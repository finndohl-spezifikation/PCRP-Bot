"""
support_voice.py \u2013 Automatischer Voice-Support f\u00FCr Paradise City Roleplay
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
\u2022 Bot betritt den Warteraum wenn ein Spieler (mit Spieler-Rolle) beitritt
\u2022 Spielt TTS-Ansage \u2192 dann Wartemusik \u2192 alle 30 Sek. TTS wiederholen
\u2022 Lobby OFFEN  \u2192 Ansage + Wartemusik in Schleife
\u2022 Lobby CLOSED \u2192 nur Ansage, keine Musik, alle 30 Sek. wiederholt
\u2022 /support-lobby open|close  \u2013 Status umschalten (Admin / Mod)
\u2022 /support-status             \u2013 Aktuellen Status anzeigen
"""

from __future__ import annotations
import asyncio
import os
import tempfile
from typing import Optional

import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer

from config import bot

# \u2500\u2500 Konfiguration \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

WARTERAUM_ID   = 1490882556269297716
SPIELER_ROLLE  = 1490855722534310003
MUSIK_URL      = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/wartemusik.mp3"
MUSIK_LOKAL    = "wartemusik_cache.mp3"
TTS_STIMME     = "de-DE-ConradNeural"
MUSIK_VOL      = 0.25
WIEDERHOL_SEK  = 30   # TTS alle X Sekunden wiederholen

ADMIN_ROLE_ID  = 1490855650081636352
MOD_ROLE_ID    = 1496147874256392202

TTS_OFFEN = (
    "Willkommen im Support! "
    "Ein Teammitglied wird sich in K\u00FCrze um dich k\u00FCmmern. "
    "Bitte hab etwas Geduld."
)
TTS_CLOSED = (
    "Der Sprach-Support ist aktuell nicht verf\u00FCgbar. "
    "Bitte erstelle ein Ticket oder versuche es sp\u00E4ter erneut."
)

# \u2500\u2500 Zustand \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_STATUS_DATEI  = "support_lobby_status.json"
_tts_cache: dict[str, str] = {}
_voice_tasks: dict[int, asyncio.Task] = {}   # guild_id \u2192 laufender Loop-Task


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
        print(f"[support_voice] \u26A0\uFE0F Status-Speicher-Fehler: {e}")


_lobby_open: bool = _load_status()


def set_lobby_status(offen: bool) -> None:
    """Wird von lobby.py aufgerufen wenn /lobby-open oder /lobby-close genutzt wird."""
    global _lobby_open
    _lobby_open = offen
    _save_status(offen)
    print(f"[support_voice] \U0001F504 Lobby-Status extern gesetzt: {'OFFEN' if offen else 'CLOSED'}")
    if _EDGE_OK:
        asyncio.get_event_loop().create_task(_refresh_tts())

# \u2500\u2500 Pakete pr\u00FCfen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

try:
    import edge_tts as _et  # noqa: F401
    _EDGE_OK = True
except ImportError:
    _EDGE_OK = False
    print("[support_voice] \u26A0\uFE0F  edge-tts fehlt \u2013 TTS deaktiviert")

try:
    import nacl as _nacl  # noqa: F401
    _NACL_OK = True
except ImportError:
    _NACL_OK = False
    print("[support_voice] \u274C PyNaCl fehlt \u2013 Voice deaktiviert!")

# \u2500\u2500 TTS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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

# \u2500\u2500 Audio-Hilfsfunktionen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
        print(f"[support_voice] \u274C TTS-Play-Fehler: {e}")
        done.set()

def _start_musik(vc: discord.VoiceClient) -> None:
    """Musik einmalig starten (kein Loop \u2014 Loop l\u00E4uft \u00FCber den Task)."""
    if not vc.is_connected() or vc.is_playing():
        return
    quelle = MUSIK_LOKAL if os.path.exists(MUSIK_LOKAL) else MUSIK_URL
    try:
        if quelle == MUSIK_URL:
            audio = FFmpegPCMAudio(quelle, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        else:
            audio = FFmpegPCMAudio(quelle)
        vc.play(PCMVolumeTransformer(audio, volume=MUSIK_VOL))
        print(f"[support_voice] \U0001F3B5 Musik gestartet")
    except Exception as e:
        print(f"[support_voice] \u274C Musik-Fehler: {e}")

# \u2500\u2500 Haupt-Loop pro Guild \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _warteraum_loop(vc: discord.VoiceClient) -> None:
    """
    L\u00E4uft solange Bot im Warteraum ist:
    1. TTS abspielen
    2. Falls offen: Wartemusik starten
    3. 30 Sekunden warten
    4. Wiederholen ab 1.
    """
    print("[support_voice] \U0001F504 Warteraum-Loop gestartet")
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
        print("[support_voice] \U0001F504 Loop abgebrochen")
    except Exception as e:
        print(f"[support_voice] \u274C Loop-Fehler: {e}")
    finally:
        if vc.is_playing():
            vc.stop()

# \u2500\u2500 Verbindung & Loop verwalten \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
        print(f"[support_voice] \u2705 Verbunden mit #{channel.name}")
    except Exception as e:
        print(f"[support_voice] \u274C Verbindungsfehler: {type(e).__name__}: {e}")
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
        print("[support_voice] \U0001F44B Bot getrennt (Warteraum leer)")

# \u2500\u2500 Musik herunterladen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _download_musik() -> None:
    if os.path.exists(MUSIK_LOKAL):
        print("[support_voice] \U0001F3B5 Wartemusik bereits gecacht")
        return
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(MUSIK_URL) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open(MUSIK_LOKAL, "wb") as f:
                        f.write(data)
                    print(f"[support_voice] \u2705 Wartemusik heruntergeladen ({len(data)//1024} KB)")
                else:
                    print(f"[support_voice] \u274C Musik-Download fehlgeschlagen: HTTP {resp.status}")
    except Exception as e:
        print(f"[support_voice] \u274C Musik-Download Fehler: {e}")

# \u2500\u2500 Listener \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.listen("on_ready")
async def support_voice_on_ready() -> None:
    print(f"[support_voice] \U0001F7E2 Bereit | PyNaCl={_NACL_OK} | edge-tts={_EDGE_OK} | Lobby={'OFFEN' if _lobby_open else 'CLOSED'}")
    await _download_musik()
    if _EDGE_OK:
        await _refresh_tts()
        print("[support_voice] \u2705 TTS vorgeneriert")

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
        print(f"[support_voice] \U0001F3A4 {member.display_name} betritt Warteraum | Lobby={'OFFEN' if _lobby_open else 'CLOSED'}")
        await _handle_join(member, after.channel)
        return

    if before.channel and before.channel.id == WARTERAUM_ID:
        humans = [m for m in before.channel.members if not m.bot]
        if not humans:
            await _disconnect(member.guild)

# \u2500\u2500 /support-lobby \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="support-lobby",
    description="Support-Lobby \u00F6ffnen oder schlie\u00DFen (Admin / Mod)"
)
@discord.app_commands.describe(status="open = Lobby \u00F6ffnen | close = Lobby schlie\u00DFen")
@discord.app_commands.choices(status=[
    discord.app_commands.Choice(name="\U0001F7E2 Offen",       value="open"),
    discord.app_commands.Choice(name="\U0001F534 Geschlossen", value="close"),
])
async def cmd_support_lobby(interaction: discord.Interaction, status: str) -> None:
    global _lobby_open

    if not any(r.id in {ADMIN_ROLE_ID, MOD_ROLE_ID} for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    _lobby_open = status == "open"
    _save_status(_lobby_open)
    if _EDGE_OK:
        await _refresh_tts()

    print(f"[support_voice] \U0001F527 Lobby-Status ge\u00E4ndert zu {'OFFEN' if _lobby_open else 'CLOSED'} von {interaction.user.display_name}")

    farbe = 0x2ECC71 if _lobby_open else 0xE74C3C
    titel = "\U0001F7E2 Support-Lobby ge\u00F6ffnet" if _lobby_open else "\U0001F534 Support-Lobby geschlossen"
    text  = "Spieler werden begr\u00FC\u00DFt und h\u00F6ren Wartemusik." if _lobby_open else "Spieler werden \u00FCber die Nicht-Verf\u00FCgbarkeit informiert."

    await interaction.response.send_message(
        embed=discord.Embed(title=titel, description=text, color=farbe),
        ephemeral=True
    )

# \u2500\u2500 /support-status \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="support-status",
    description="Aktuellen Support-Lobby Status anzeigen"
)
async def cmd_support_status(interaction: discord.Interaction) -> None:
    farbe = 0x2ECC71 if _lobby_open else 0xE74C3C
    status_text = "\U0001F7E2 **Offen** \u2014 Spieler werden begr\u00FC\u00DFt" if _lobby_open else "\U0001F534 **Geschlossen** \u2014 Spieler werden abgewiesen"
    embed = discord.Embed(
        title="\U0001F4DE Support-Lobby Status",
        description=status_text,
        color=farbe
    )
    embed.add_field(name="\u23F1\uFE0F TTS-Wiederholung", value=f"alle **{WIEDERHOL_SEK} Sekunden**", inline=True)
    embed.add_field(name="\U0001F3B5 Wartemusik", value="\u2705 Bereit" if os.path.exists(MUSIK_LOKAL) else "\u2B07\uFE0F Wird geladen...", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)
