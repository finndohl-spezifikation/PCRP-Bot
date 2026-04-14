"""
support_voice.py – Automatischer Voice-Support für Paradise City Roleplay
────────────────────────────────────────────────────────────────────────────
• Bot betritt den Warteraum wenn ein Spieler (mit Spieler-Rolle) beitritt
• Spielt TTS-Ansage → dann Wartemusik → alle 30 Sek. TTS wiederholen
• Lobby OFFEN  → Ansage + Wartemusik in Schleife
• Lobby CLOSED → nur Ansage, keine Musik, alle 30 Sek. wiederholt
• /support-lobby open|close  – Status umschalten (Admin / Mod)
• /support-status             – Aktuellen Status anzeigen
"""

from __future__ import annotations
import asyncio
import os
import tempfile
from typing import Optional

import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer

from config import bot

# ── Konfiguration ─────────────────────────────────────────────────────────

WARTERAUM_ID   = 1490882556269297716
SPIELER_ROLLE  = 1490855722534310003
MUSIK_URL      = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/wartemusik.mp3"
MUSIK_LOKAL    = "wartemusik_cache.mp3"
TTS_STIMME     = "de-DE-ConradNeural"
MUSIK_VOL      = 0.25
WIEDERHOL_SEK  = 30   # TTS alle X Sekunden wiederholen

ADMIN_ROLE_ID  = 1490855702225485936
MOD_ROLE_ID    = 1490855703370534965

TTS_OFFEN = (
    "Willkommen im Support! "
    "Ein Teammitglied wird sich in Kürze um dich kümmern. "
    "Bitte hab etwas Geduld."
)
TTS_CLOSED = (
    "Der Sprach-Support ist aktuell nicht verfügbar. "
    "Bitte erstelle ein Ticket oder versuche es später erneut."
)

# ── Zustand ───────────────────────────────────────────────────────────────

_STATUS_DATEI  = "support_lobby_status.json"
_tts_cache: dict[str, str] = {}
_voice_tasks: dict[int, asyncio.Task] = {}   # guild_id → laufender Loop-Task


def _load_status() -> bool:
    try:
        import json
        with open(_STATUS_DATEI, "r") as f:
            return json.load(f).get("open", True)
    except Exception:
        return True


def _save_status(open: bool) -> None:
    try:
        import json
        with open(_STATUS_DATEI, "w") as f:
            json.dump({"open": open}, f)
    except Exception as e:
        print(f"[support_voice] ⚠️ Status-Speicher-Fehler: {e}")


_lobby_open: bool = _load_status()

# ── Pakete prüfen ─────────────────────────────────────────────────────────

try:
    import edge_tts as _et  # noqa: F401
    _EDGE_OK = True
except ImportError:
    _EDGE_OK = False
    print("[support_voice] ⚠️  edge-tts fehlt – TTS deaktiviert")

try:
    import nacl as _nacl  # noqa: F401
    _NACL_OK = True
except ImportError:
    _NACL_OK = False
    print("[support_voice] ❌ PyNaCl fehlt – Voice deaktiviert!")

# ── TTS ───────────────────────────────────────────────────────────────────

async def _gen_tts(key: str, text: str) -> Optional[str]:
    if not _EDGE_OK:
        return None
    cached = _tts_cache.get(key)
    if cached and os.path.exists(cached):
        return cached
    try:
        import edge_tts
        fd, path = tempfile.mkstemp(suffix=".mp3", prefix=f"tts_{key}_")
        os.close(fd)
        await edge_tts.Communicate(text, voice=TTS_STIMME).save(path)
        _tts_cache[key] = path
        return path
    except Exception as e:
        print(f"[support_voice] TTS-Fehler: {e}")
        return None

async def _refresh_tts() -> None:
    _tts_cache.clear()
    await _gen_tts("offen",  TTS_OFFEN)
    await _gen_tts("closed", TTS_CLOSED)

# ── Audio-Hilfsfunktionen ─────────────────────────────────────────────────

async def _play_tts_async(vc: discord.VoiceClient) -> None:
    """TTS abspielen und warten bis sie fertig ist."""
    key  = "offen" if _lobby_open else "closed"
    text = TTS_OFFEN if _lobby_open else TTS_CLOSED
    path = await _gen_tts(key, text)
    if not path or not vc.is_connected():
        return

    done = asyncio.Event()
    try:
        if vc.is_playing():
            vc.stop()
            await asyncio.sleep(0.2)
        vc.play(FFmpegPCMAudio(path), after=lambda e: done.set())
        await done.wait()
    except Exception as e:
        print(f"[support_voice] ❌ TTS-Play-Fehler: {e}")
        done.set()

def _start_musik(vc: discord.VoiceClient) -> None:
    """Musik einmalig starten (kein Loop — Loop läuft über den Task)."""
    if not vc.is_connected() or vc.is_playing():
        return
    quelle = MUSIK_LOKAL if os.path.exists(MUSIK_LOKAL) else MUSIK_URL
    try:
        if quelle == MUSIK_URL:
            audio = FFmpegPCMAudio(quelle, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        else:
            audio = FFmpegPCMAudio(quelle)
        vc.play(PCMVolumeTransformer(audio, volume=MUSIK_VOL))
        print(f"[support_voice] 🎵 Musik gestartet")
    except Exception as e:
        print(f"[support_voice] ❌ Musik-Fehler: {e}")

# ── Haupt-Loop pro Guild ──────────────────────────────────────────────────

async def _warteraum_loop(vc: discord.VoiceClient) -> None:
    """
    Läuft solange Bot im Warteraum ist:
    1. TTS abspielen
    2. Falls offen: Wartemusik starten
    3. 30 Sekunden warten
    4. Wiederholen ab 1.
    """
    print("[support_voice] 🔄 Warteraum-Loop gestartet")
    try:
        while vc.is_connected():
            # TTS abspielen
            await _play_tts_async(vc)

            if not vc.is_connected():
                break

            # Musik starten (nur wenn Lobby offen)
            if _lobby_open:
                _start_musik(vc)

            # 30 Sekunden warten
            await asyncio.sleep(WIEDERHOL_SEK)

            # Musik stoppen bevor TTS wiederholt wird
            if vc.is_playing():
                vc.stop()
                await asyncio.sleep(0.3)

    except asyncio.CancelledError:
        print("[support_voice] 🔄 Loop abgebrochen")
    except Exception as e:
        print(f"[support_voice] ❌ Loop-Fehler: {e}")
    finally:
        if vc.is_playing():
            vc.stop()

# ── Verbindung & Loop verwalten ───────────────────────────────────────────

async def _handle_join(member: discord.Member, channel: discord.VoiceChannel) -> None:
    guild = member.guild

    # Laufenden Loop abbrechen falls vorhanden
    _cancel_loop(guild.id)

    vc = guild.voice_client
    try:
        if vc and vc.is_connected():
            if vc.channel.id != channel.id:
                await vc.move_to(channel)
        else:
            vc = await channel.connect()
        print(f"[support_voice] ✅ Verbunden mit #{channel.name}")
    except Exception as e:
        print(f"[support_voice] ❌ Verbindungsfehler: {type(e).__name__}: {e}")
        return

    # Loop starten
    task = asyncio.create_task(_warteraum_loop(vc))
    _voice_tasks[guild.id] = task

def _cancel_loop(guild_id: int) -> None:
    task = _voice_tasks.pop(guild_id, None)
    if task and not task.done():
        task.cancel()

async def _disconnect(guild: discord.Guild) -> None:
    _cancel_loop(guild.id)
    vc = guild.voice_client
    if vc and vc.is_connected():
        if vc.is_playing():
            vc.stop()
        await vc.disconnect()
        print("[support_voice] 👋 Bot getrennt (Warteraum leer)")

# ── Musik herunterladen ───────────────────────────────────────────────────

async def _download_musik() -> None:
    if os.path.exists(MUSIK_LOKAL):
        print("[support_voice] 🎵 Wartemusik bereits gecacht")
        return
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(MUSIK_URL) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open(MUSIK_LOKAL, "wb") as f:
                        f.write(data)
                    print(f"[support_voice] ✅ Wartemusik heruntergeladen ({len(data)//1024} KB)")
                else:
                    print(f"[support_voice] ❌ Musik-Download fehlgeschlagen: HTTP {resp.status}")
    except Exception as e:
        print(f"[support_voice] ❌ Musik-Download Fehler: {e}")

# ── Listener ─────────────────────────────────────────────────────────────

@bot.listen("on_ready")
async def support_voice_on_ready() -> None:
    print(f"[support_voice] 🟢 Bereit | PyNaCl={_NACL_OK} | edge-tts={_EDGE_OK} | Lobby={'OFFEN' if _lobby_open else 'CLOSED'}")
    await _download_musik()
    if _EDGE_OK:
        await _refresh_tts()
        print("[support_voice] ✅ TTS vorgeneriert")

@bot.listen("on_voice_state_update")
async def support_voice_state(
    member: discord.Member,
    before: discord.VoiceState,
    after:  discord.VoiceState,
) -> None:
    if member.bot or not _NACL_OK:
        return

    rolle_ids = {r.id for r in member.roles}
    hat_rolle = SPIELER_ROLLE in rolle_ids

    if after.channel and after.channel.id == WARTERAUM_ID and hat_rolle:
        print(f"[support_voice] 🎤 {member.display_name} betritt Warteraum | Lobby={'OFFEN' if _lobby_open else 'CLOSED'}")
        await _handle_join(member, after.channel)
        return

    if before.channel and before.channel.id == WARTERAUM_ID:
        humans = [m for m in before.channel.members if not m.bot]
        if not humans:
            await _disconnect(member.guild)

# ── /support-lobby ────────────────────────────────────────────────────────

@bot.tree.command(
    name="support-lobby",
    description="Support-Lobby öffnen oder schließen (Admin / Mod)"
)
@discord.app_commands.describe(status="open = Lobby öffnen | close = Lobby schließen")
@discord.app_commands.choices(status=[
    discord.app_commands.Choice(name="🟢 Offen",       value="open"),
    discord.app_commands.Choice(name="🔴 Geschlossen", value="close"),
])
async def cmd_support_lobby(interaction: discord.Interaction, status: str) -> None:
    global _lobby_open

    if not any(r.id in {ADMIN_ROLE_ID, MOD_ROLE_ID} for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    _lobby_open = status == "open"
    _save_status(_lobby_open)
    if _EDGE_OK:
        await _refresh_tts()

    print(f"[support_voice] 🔧 Lobby-Status geändert zu {'OFFEN' if _lobby_open else 'CLOSED'} von {interaction.user.display_name}")

    farbe = 0x2ECC71 if _lobby_open else 0xE74C3C
    titel = "🟢 Support-Lobby geöffnet" if _lobby_open else "🔴 Support-Lobby geschlossen"
    text  = "Spieler werden begrüßt und hören Wartemusik." if _lobby_open else "Spieler werden über die Nicht-Verfügbarkeit informiert."

    await interaction.response.send_message(
        embed=discord.Embed(title=titel, description=text, color=farbe),
        ephemeral=True
    )

# ── /support-status ───────────────────────────────────────────────────────

@bot.tree.command(
    name="support-status",
    description="Aktuellen Support-Lobby Status anzeigen"
)
async def cmd_support_status(interaction: discord.Interaction) -> None:
    farbe = 0x2ECC71 if _lobby_open else 0xE74C3C
    status_text = "🟢 **Offen** — Spieler werden begrüßt" if _lobby_open else "🔴 **Geschlossen** — Spieler werden abgewiesen"
    embed = discord.Embed(
        title="📞 Support-Lobby Status",
        description=status_text,
        color=farbe
    )
    embed.add_field(name="⏱️ TTS-Wiederholung", value=f"alle **{WIEDERHOL_SEK} Sekunden**", inline=True)
    embed.add_field(name="🎵 Wartemusik", value="✅ Bereit" if os.path.exists(MUSIK_LOKAL) else "⬇️ Wird geladen...", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)
