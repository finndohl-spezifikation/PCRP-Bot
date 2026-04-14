"""
support_voice.py – Automatischer Voice-Support für Paradise City Roleplay
────────────────────────────────────────────────────────────────────────────
• Bot betritt den Support-Warteraum sobald ein Spieler beitritt
• Spielt TTS-Ansage mit männlicher deutscher Stimme (edge-tts)
    – Lobby OFFEN  → "Ein Teammitglied kümmert sich gleich um dich" + Wartemusik
    – Lobby CLOSED → "Sprach-Support nicht verfügbar"
• Bot verlässt den Kanal wenn kein Mensch mehr drin ist
• /support-lobby open|close  – Lobby-Status umschalten (Admin / Mod)

Voraussetzung:
  pip install edge-tts PyNaCl
  ffmpeg muss im PATH sein (Railway: Nixpacks/Dockerfile)
  wartemusik.mp3 im Bot-Ordner ablegen
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from typing import Optional

import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer

from config import bot

try:
    import edge_tts
    _EDGE_OK = True
except ImportError:
    _EDGE_OK = False
    print("[support_voice] ⚠️  edge-tts nicht installiert – TTS deaktiviert")

try:
    import nacl  # noqa: F401
    _NACL_OK = True
except ImportError:
    _NACL_OK = False
    print("[support_voice] ❌ PyNaCl nicht installiert – Voice komplett deaktiviert! (pip install PyNaCl)")

# ── Konfiguration ─────────────────────────────────────────────────────────

WARTERAUM_ID  = 1490882556269297716   # Support Warteraum Voice-Channel
MUSIK_URL     = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/wartemusik.mp3"
TTS_STIMME    = "de-DE-ConradNeural"  # Männliche DE-Stimme
MUSIK_VOL     = 0.25                  # 0.0 – 1.0

ADMIN_ROLE_ID = 1490855702225485936
MOD_ROLE_ID   = 1490855703370534965

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

_lobby_open: bool     = True
_tts_cache:  dict     = {}          # "offen"|"closed" → Dateipfad


# ── TTS-Hilfsfunktionen ───────────────────────────────────────────────────

async def _gen_tts(key: str, text: str) -> Optional[str]:
    """Generiert eine TTS-MP3 und gibt den Pfad zurück (gecacht)."""
    if not _EDGE_OK:
        return None
    cached = _tts_cache.get(key)
    if cached and os.path.exists(cached):
        return cached
    try:
        fd, path = tempfile.mkstemp(suffix=".mp3", prefix=f"tts_{key}_")
        os.close(fd)
        await edge_tts.Communicate(text, voice=TTS_STIMME).save(path)
        _tts_cache[key] = path
        return path
    except Exception as e:
        print(f"[support_voice] TTS-Fehler ({key}): {e}")
        return None


async def _refresh_tts() -> None:
    """Beide TTS-Dateien neu generieren (nach Status-Wechsel)."""
    for k in ("offen", "closed"):
        _tts_cache.pop(k, None)
    await _gen_tts("offen",  TTS_OFFEN)
    await _gen_tts("closed", TTS_CLOSED)


# ── Musik in Schleife ─────────────────────────────────────────────────────

def _play_musik(vc: discord.VoiceClient) -> None:
    if not vc.is_connected() or vc.is_playing():
        return
    source = PCMVolumeTransformer(
        FFmpegPCMAudio(MUSIK_URL, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
        volume=MUSIK_VOL
    )
    vc.play(source, after=lambda e: _play_musik(vc) if vc.is_connected() else None)


# ── Verbindung trennen ────────────────────────────────────────────────────

async def _disconnect(guild: discord.Guild) -> None:
    vc = guild.voice_client
    if vc and vc.is_connected():
        if vc.is_playing():
            vc.stop()
        await vc.disconnect()


# ── Spieler tritt Warteraum bei ───────────────────────────────────────────

async def _handle_join(member: discord.Member, channel: discord.VoiceChannel) -> None:
    guild = member.guild
    vc    = guild.voice_client

    try:
        if vc and vc.is_connected():
            if vc.channel.id != WARTERAUM_ID:
                await vc.move_to(channel)
        else:
            vc = await channel.connect()
        print(f"[support_voice] ✅ Verbunden mit {channel.name}")
    except Exception as e:
        print(f"[support_voice] ❌ Verbindungsfehler: {type(e).__name__}: {e}")
        return

    if vc.is_playing():
        vc.stop()

    key      = "offen" if _lobby_open else "closed"
    text     = TTS_OFFEN if _lobby_open else TTS_CLOSED
    tts_path = await _gen_tts(key, text)

    def _nach_tts(_err: Optional[Exception]) -> None:
        if _lobby_open and vc.is_connected():
            _play_musik(vc)

    if tts_path:
        vc.play(FFmpegPCMAudio(tts_path), after=_nach_tts)
    elif _lobby_open:
        _play_musik(vc)


# ── Listener ─────────────────────────────────────────────────────────────

@bot.listen("on_ready")
async def support_voice_on_ready() -> None:
    await _refresh_tts()
    print("[support_voice] ✅ TTS-Dateien vorgeneriert.")


@bot.listen("on_voice_state_update")
async def support_voice_state(
    member: discord.Member,
    before: discord.VoiceState,
    after:  discord.VoiceState,
) -> None:
    if member.bot:
        return

    if not _NACL_OK:
        return  # Voice ohne PyNaCl nicht möglich

    # Spieler betritt Warteraum
    if after.channel and after.channel.id == WARTERAUM_ID:
        print(f"[support_voice] 🎤 {member.display_name} betritt Warteraum → verbinde...")
        await _handle_join(member, after.channel)
        return

    # Spieler verlässt Warteraum → Bot trennen wenn niemand mehr da
    if before.channel and before.channel.id == WARTERAUM_ID:
        humans = [m for m in before.channel.members if not m.bot]
        if not humans:
            print(f"[support_voice] 👋 Warteraum leer → trenne Verbindung")
            await _disconnect(member.guild)


# ── Slash-Befehl ─────────────────────────────────────────────────────────

@bot.tree.command(
    name="support-lobby",
    description="Support-Lobby öffnen oder schließen (Admin / Mod)"
)
@discord.app_commands.describe(status="open = Lobby öffnen | close = Lobby schließen")
@discord.app_commands.choices(status=[
    discord.app_commands.Choice(name="🟢 Offen",       value="open"),
    discord.app_commands.Choice(name="🔴 Geschlossen", value="close"),
])
async def cmd_support_lobby(
    interaction: discord.Interaction,
    status: str,
) -> None:
    global _lobby_open

    allowed = {ADMIN_ROLE_ID, MOD_ROLE_ID}
    if not any(r.id in allowed for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    _lobby_open = status == "open"
    await _refresh_tts()

    if _lobby_open:
        embed = discord.Embed(
            title="🟢 Support-Lobby geöffnet",
            description="Spieler im Warteraum werden ab jetzt mit Ansage und Wartemusik begrüßt.",
            color=0x2ECC71
        )
    else:
        embed = discord.Embed(
            title="🔴 Support-Lobby geschlossen",
            description="Spieler werden darüber informiert, dass der Sprach-Support nicht verfügbar ist.",
            color=0xE74C3C
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)
