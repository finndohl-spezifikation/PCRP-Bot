# -*- coding: utf-8 -*-
# logs.py — Zentrales Logging-System (Paradise City Roleplay)
#
# Importieren mit:  from logs import log_server, log_mod, log_bot_error, ...
# Alle Funktionen sind async und fangen Fehler intern ab.

import discord
from datetime import datetime, timezone
from config import (
    bot,
    SERVER_LOG_CHANNEL_ID,
    MOD_LOG_CHANNEL_ID,
    BOT_LOG_CHANNEL_ID,
    MEMBER_LOG_CHANNEL_ID,
    MESSAGE_LOG_CHANNEL_ID,
    ROLE_LOG_CHANNEL_ID,
    MONEY_LOG_CHANNEL_ID,
    TICKET_LOG_CHANNEL_ID,
)

_FOOTER = "Paradise City Roleplay"

# ── Interne Hilfsfunktion ─────────────────────────────────────────────────────

def _make_embed(
    title: str,
    desc: str,
    color: int,
    fields: list[tuple[str, str, bool]] | None = None,
    thumbnail: str | None = None,
) -> discord.Embed:
    emb = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_footer(text=_FOOTER)
    if thumbnail:
        emb.set_thumbnail(url=thumbnail)
    for (name, value, inline) in (fields or []):
        emb.add_field(name=name, value=value, inline=inline)
    return emb


async def _send(channel_id: int, embed: discord.Embed, files: list | None = None) -> None:
    """Sendet ein Embed in den angegebenen Kanal — fängt alle Fehler ab."""
    try:
        ch = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        if ch:
            await ch.send(embed=embed, files=files or [])
    except Exception as e:
        print(f"[logs] Fehler beim Senden in Kanal {channel_id}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1 · SERVER-LOG  (Kanal-/Rollenstruktur-Änderungen)
#     Channel: SERVER_LOG_CHANNEL_ID
# ═══════════════════════════════════════════════════════════════════════════════

async def log_server(
    title: str,
    desc: str,
    color: int = 0x3498DB,
    fields: list[tuple[str, str, bool]] | None = None,
) -> None:
    """Kanal erstellt/gelöscht/bearbeitet, Rolle erstellt/gelöscht/bearbeitet."""
    emb = _make_embed(f"\U0001F3DB\uFE0F {title}", desc, color, fields)
    await _send(SERVER_LOG_CHANNEL_ID, emb)


# ═══════════════════════════════════════════════════════════════════════════════
# 2 · MOD-LOG  (Bans, Timeouts, Warns, Bot-Versuche, Spam, Vulguläre Wörter)
#     Channel: MOD_LOG_CHANNEL_ID
# ═══════════════════════════════════════════════════════════════════════════════

async def log_mod(
    title: str,
    desc: str,
    color: int = 0xE74C3C,
    fields: list[tuple[str, str, bool]] | None = None,
    thumbnail: str | None = None,
) -> None:
    """Moderations-Aktion loggen (Bann, Entbann, Timeout, Warn, Spam, ...)."""
    emb = _make_embed(f"\U0001F528 {title}", desc, color, fields, thumbnail)
    await _send(MOD_LOG_CHANNEL_ID, emb)


# ═══════════════════════════════════════════════════════════════════════════════
# 3 · BOT-LOG  (Fehler, Neustarts)
#     Channel: BOT_LOG_CHANNEL_ID
# ═══════════════════════════════════════════════════════════════════════════════

async def log_bot_error(
    title: str,
    desc: str,
    guild=None,   # für Kompatibilität mit helpers.log_bot_error-Aufrufen
) -> None:
    """Bot-Fehler oder Neustart loggen."""
    emb = _make_embed(
        f"\u26A0\uFE0F {title}",
        desc,
        0xE74C3C,
    )
    await _send(BOT_LOG_CHANNEL_ID, emb)


async def log_bot_restart(info: str = "") -> None:
    """Wird beim Bot-Start aufgerufen um Neustarts zu protokollieren."""
    desc = f"Der Bot wurde **neugestartet**."
    if info:
        desc += f"\n\n{info}"
    emb = _make_embed(
        "\U0001F504 Bot neugestartet",
        desc,
        0x2ECC71,
    )
    await _send(BOT_LOG_CHANNEL_ID, emb)


# ═══════════════════════════════════════════════════════════════════════════════
# 4 · MEMBER-LOG  (Beitritt, Verlassen, Angelbeweise)
#     Channel: MEMBER_LOG_CHANNEL_ID
# ═══════════════════════════════════════════════════════════════════════════════

async def log_member(
    title: str,
    desc: str,
    color: int = 0x2ECC71,
    fields: list[tuple[str, str, bool]] | None = None,
    thumbnail: str | None = None,
    files: list | None = None,
) -> None:
    """Mitglied beigetreten/verlassen oder Angelbeweis."""
    emb = _make_embed(f"\U0001F465 {title}", desc, color, fields, thumbnail)
    await _send(MEMBER_LOG_CHANNEL_ID, emb, files)


# ═══════════════════════════════════════════════════════════════════════════════
# 5 · NACHRICHTEN-LOG  (gelöscht, bearbeitet)
#     Channel: MESSAGE_LOG_CHANNEL_ID
# ═══════════════════════════════════════════════════════════════════════════════

async def log_message(
    title: str,
    desc: str,
    color: int = 0x95A5A6,
    fields: list[tuple[str, str, bool]] | None = None,
    thumbnail: str | None = None,
) -> None:
    """Nachricht gelöscht oder bearbeitet."""
    emb = _make_embed(f"\U0001F4AC {title}", desc, color, fields, thumbnail)
    await _send(MESSAGE_LOG_CHANNEL_ID, emb)


# ═══════════════════════════════════════════════════════════════════════════════
# 6 · ROLLEN-LOG  (Rollen an Mitglied zugewiesen / entfernt)
#     Channel: ROLE_LOG_CHANNEL_ID
# ═══════════════════════════════════════════════════════════════════════════════

async def log_role(
    title: str,
    desc: str,
    color: int = 0x9B59B6,
    fields: list[tuple[str, str, bool]] | None = None,
    thumbnail: str | None = None,
) -> None:
    """Rolle einem Mitglied hinzugefügt oder weggenommen."""
    emb = _make_embed(f"\U0001F3F7\uFE0F {title}", desc, color, fields, thumbnail)
    await _send(ROLE_LOG_CHANNEL_ID, emb)


# ═══════════════════════════════════════════════════════════════════════════════
# 7 · GELD-LOG  (alle Geldinteraktionen)
#     Channel: MONEY_LOG_CHANNEL_ID
# ═══════════════════════════════════════════════════════════════════════════════

async def log_money_action(
    guild,          # für Kompatibilität mit helpers.log_money_action-Aufrufen
    title: str,
    desc: str,
    fields: list[tuple[str, str, bool]] | None = None,
    thumbnail: str | None = None,
) -> None:
    """Geld-Transaktion loggen (Einzahlung, Auszahlung, Überweisung, Kauf, ...)."""
    emb = _make_embed(f"\U0001F4B0 {title}", desc, 0xF1C40F, fields, thumbnail)
    await _send(MONEY_LOG_CHANNEL_ID, emb)


# ═══════════════════════════════════════════════════════════════════════════════
# 8 · TICKET-LOG  (erstellt, geschlossen, zugewiesen, Transkript)
#     Channel: TICKET_LOG_CHANNEL_ID
# ═══════════════════════════════════════════════════════════════════════════════

async def log_ticket(
    guild,
    embed: discord.Embed,
    file: discord.File | None = None,
) -> None:
    """Ticket-Event loggen. Nimmt ein fertiges Embed + optional Transkript-Datei."""
    files = [file] if file else []
    await _send(TICKET_LOG_CHANNEL_ID, embed, files)
