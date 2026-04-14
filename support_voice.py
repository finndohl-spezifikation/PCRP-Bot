"""
support_voice.py – Automatischer Voice-Support für Paradise City Roleplay
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

WARTERAUM_ID    = 1490882556269297716   # Support Warteraum Voice-Channel
SPIELER_ROLLE   = 1490855722534310003   # Nur Spieler mit dieser Rolle triggern den Bot
MUSIK_URL       = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/wartemusik.mp3"
TTS_STIMME      = "de-DE-ConradNeural"
MUSIK_VOL       = 0.25

ADMIN_ROLE_ID   = 1490855702225485936
MOD_ROLE_ID     = 1490855703370534965

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

_lobby_open: bool = True
_tts_cache: dict[str, str] = {}

# ── Prüfungen beim Import ─────────────────────────────────────────────────

try:
    import edge_tts as _edge_tts_mod
    _EDGE_OK = True
except ImportError:
    _EDGE_OK = False
    print("[support_voice] ⚠️  edge-tts fehlt – TTS deaktiviert")

try:
    import nacl as _nacl_mod  # noqa: F401
    _NACL_OK = True
except ImportError:
    _NACL_OK = False
    print("[support_voice] ❌ PyNaCl fehlt – Voice deaktiviert! → pip install PyNaCl")

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

# ── Audio ─────────────────────────────────────────────────────────────────

def _play_musik(vc: discord.VoiceClient) -> None:
    if not vc.is_connected() or vc.is_playing():
        return
    try:
        source = PCMVolumeTransformer(
            FFmpegPCMAudio(
                MUSIK_URL,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
            ),
            volume=MUSIK_VOL
        )
        vc.play(source, after=lambda e: _play_musik(vc) if vc.is_connected() else None)
    except Exception as e:
        print(f"[support_voice] Musik-Fehler: {e}")

async def _disconnect(guild: discord.Guild) -> None:
    vc = guild.voice_client
    if vc and vc.is_connected():
        if vc.is_playing():
            vc.stop()
        await vc.disconnect()
        print("[support_voice] 👋 Bot getrennt (Warteraum leer)")

# ── Beitritt-Handler ──────────────────────────────────────────────────────

async def _handle_join(member: discord.Member, channel: discord.VoiceChannel) -> None:
    guild = member.guild
    vc    = guild.voice_client

    # Verbinden
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

    # Laufendes Audio stoppen
    if vc.is_playing():
        vc.stop()
    await asyncio.sleep(0.3)

    # TTS abspielen
    key      = "offen" if _lobby_open else "closed"
    text     = TTS_OFFEN if _lobby_open else TTS_CLOSED
    tts_path = await _gen_tts(key, text)

    def _nach_tts(_err: Optional[Exception]) -> None:
        if _err:
            print(f"[support_voice] TTS-Abspiel-Fehler: {_err}")
        if _lobby_open and vc.is_connected():
            _play_musik(vc)

    if tts_path:
        try:
            vc.play(FFmpegPCMAudio(tts_path), after=_nach_tts)
        except Exception as e:
            print(f"[support_voice] TTS-Play-Fehler: {e}")
            if _lobby_open:
                _play_musik(vc)
    elif _lobby_open:
        _play_musik(vc)

# ── Listener ─────────────────────────────────────────────────────────────

@bot.listen("on_ready")
async def support_voice_on_ready() -> None:
    print(f"[support_voice] 🟢 Bereit | PyNaCl={_NACL_OK} | edge-tts={_EDGE_OK}")
    if _EDGE_OK:
        await _refresh_tts()
        print("[support_voice] ✅ TTS vorgeneriert")

@bot.listen("on_voice_state_update")
async def support_voice_state(
    member: discord.Member,
    before: discord.VoiceState,
    after:  discord.VoiceState,
) -> None:
    if member.bot:
        return
    if not _NACL_OK:
        return

    # Nur Spieler mit der Spieler-Rolle
    rolle_ids = {r.id for r in member.roles}
    hat_rolle = SPIELER_ROLLE in rolle_ids

    # Spieler betritt Warteraum
    if after.channel and after.channel.id == WARTERAUM_ID and hat_rolle:
        print(f"[support_voice] 🎤 {member.display_name} betritt Warteraum")
        await _handle_join(member, after.channel)
        return

    # Warteraum verlassen → prüfen ob noch Menschen drin
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
    if _EDGE_OK:
        await _refresh_tts()

    if _lobby_open:
        embed = discord.Embed(
            title="🟢 Support-Lobby geöffnet",
            description="Spieler werden ab jetzt begrüßt und hören Wartemusik.",
            color=0x2ECC71
        )
    else:
        embed = discord.Embed(
            title="🔴 Support-Lobby geschlossen",
            description="Spieler werden über die Nicht-Verfügbarkeit informiert.",
            color=0xE74C3C
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)
