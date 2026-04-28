# -*- coding: utf-8 -*-
# log_events.py — Automatische Discord-Event-Logs (Paradise City Roleplay)
#
# Wird von bot.py mit  import log_events  geladen.
# Registriert alle Listener mit @bot.listen, um bestehende Listener nicht zu überschreiben.

import discord
import asyncio
import re
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from config import bot
from logs import (
    log_server,
    log_mod,
    log_bot_error,
    log_member,
    log_message,
    log_role,
)

# ── Audit-Log-Helfer ──────────────────────────────────────────────────────────

async def _audit_executor(
    guild: discord.Guild,
    action: discord.AuditLogAction,
    target_id: int | None = None,
    timeout: float = 1.5,
) -> discord.Member | discord.User | None:
    """Sucht den Ausführenden einer Aktion im Audit-Log."""
    await asyncio.sleep(timeout)
    try:
        async for entry in guild.audit_logs(limit=10, action=action):
            if target_id is None:
                return entry.user
            if entry.target and getattr(entry.target, "id", None) == target_id:
                return entry.user
    except (discord.Forbidden, Exception):
        pass
    return None


def _ts(dt: datetime | None = None) -> str:
    """Discord-Zeitstempel-Format."""
    d = dt or datetime.now(timezone.utc)
    return discord.utils.format_dt(d, "F")


def _short(text: str, limit: int = 1024) -> str:
    if not text:
        return "*— leer —*"
    return text[:limit - 3] + "…" if len(text) > limit else text


# ═══════════════════════════════════════════════════════════════════════════════
# 1 · SERVER-LOG — Kanal-Ereignisse
# ═══════════════════════════════════════════════════════════════════════════════

@bot.listen("on_guild_channel_create")
async def _log_channel_create(channel: discord.abc.GuildChannel):
    executor = await _audit_executor(
        channel.guild, discord.AuditLogAction.channel_create, channel.id
    )
    ch_type = {
        discord.ChannelType.text:     "Text-Kanal",
        discord.ChannelType.voice:    "Voice-Kanal",
        discord.ChannelType.category: "Kategorie",
        discord.ChannelType.news:     "Ankündigungs-Kanal",
        discord.ChannelType.stage_voice: "Stage-Kanal",
        discord.ChannelType.forum:    "Forum-Kanal",
    }.get(channel.type, "Kanal")

    cat = getattr(channel, "category", None)
    desc = (
        f"**{ch_type}:** {channel.mention}\n"
        f"**Name:** `{channel.name}`\n"
        f"**Kategorie:** {cat.name if cat else '—'}\n"
        f"**Erstellt von:** {executor.mention if executor else '—'}"
    )
    await log_server("Kanal erstellt", desc, color=0x2ECC71)


@bot.listen("on_guild_channel_delete")
async def _log_channel_delete(channel: discord.abc.GuildChannel):
    executor = await _audit_executor(
        channel.guild, discord.AuditLogAction.channel_delete, channel.id
    )
    cat = getattr(channel, "category", None)
    desc = (
        f"**Name:** `{channel.name}`\n"
        f"**Kategorie:** {cat.name if cat else '—'}\n"
        f"**Gelöscht von:** {executor.mention if executor else '—'}"
    )
    await log_server("Kanal gelöscht", desc, color=0xE74C3C)


@bot.listen("on_guild_channel_update")
async def _log_channel_update(before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
    changes: list[str] = []

    if before.name != after.name:
        changes.append(f"**Name:** `{before.name}` → `{after.name}`")

    # Textkanal: Topic
    b_topic = getattr(before, "topic", None)
    a_topic = getattr(after,  "topic", None)
    if b_topic != a_topic:
        changes.append(
            f"**Thema:** `{b_topic or '—'}` → `{a_topic or '—'}`"
        )

    # NSFW
    b_nsfw = getattr(before, "nsfw", None)
    a_nsfw = getattr(after,  "nsfw", None)
    if b_nsfw is not None and b_nsfw != a_nsfw:
        changes.append(f"**NSFW:** `{b_nsfw}` → `{a_nsfw}`")

    # Kategorie
    b_cat = getattr(before, "category", None)
    a_cat = getattr(after,  "category", None)
    if getattr(b_cat, "id", None) != getattr(a_cat, "id", None):
        changes.append(
            f"**Kategorie:** `{b_cat.name if b_cat else '—'}` → `{a_cat.name if a_cat else '—'}`"
        )

    if not changes:
        return

    executor = await _audit_executor(
        after.guild, discord.AuditLogAction.channel_update, after.id
    )
    desc = (
        f"**Kanal:** {after.mention}\n"
        f"**Bearbeitet von:** {executor.mention if executor else '—'}\n\n"
        + "\n".join(changes)
    )
    await log_server("Kanal bearbeitet", desc, color=0xF39C12)


# ── Rollen-Ereignisse (Struktur) ──────────────────────────────────────────────

@bot.listen("on_guild_role_create")
async def _log_role_create(role: discord.Role):
    executor = await _audit_executor(
        role.guild, discord.AuditLogAction.role_create, role.id
    )
    desc = (
        f"**Rolle:** {role.mention} (`{role.name}`)\n"
        f"**Farbe:** `{role.color}`\n"
        f"**Erwähnbar:** `{role.mentionable}`\n"
        f"**Erstellt von:** {executor.mention if executor else '—'}"
    )
    await log_server("Rolle erstellt", desc, color=0x2ECC71)


@bot.listen("on_guild_role_delete")
async def _log_role_delete(role: discord.Role):
    executor = await _audit_executor(
        role.guild, discord.AuditLogAction.role_delete, role.id
    )
    desc = (
        f"**Name:** `{role.name}`\n"
        f"**Farbe:** `{role.color}`\n"
        f"**Gelöscht von:** {executor.mention if executor else '—'}"
    )
    await log_server("Rolle gelöscht", desc, color=0xE74C3C)


@bot.listen("on_guild_role_update")
async def _log_role_update(before: discord.Role, after: discord.Role):
    changes: list[str] = []

    if before.name != after.name:
        changes.append(f"**Name:** `{before.name}` → `{after.name}`")
    if before.color != after.color:
        changes.append(f"**Farbe:** `{before.color}` → `{after.color}`")
    if before.hoist != after.hoist:
        changes.append(f"**Separat anzeigen:** `{before.hoist}` → `{after.hoist}`")
    if before.mentionable != after.mentionable:
        changes.append(f"**Erwähnbar:** `{before.mentionable}` → `{after.mentionable}`")
    if before.permissions != after.permissions:
        changes.append("**Berechtigungen wurden geändert**")

    if not changes:
        return

    executor = await _audit_executor(
        after.guild, discord.AuditLogAction.role_update, after.id
    )
    desc = (
        f"**Rolle:** {after.mention}\n"
        f"**Bearbeitet von:** {executor.mention if executor else '—'}\n\n"
        + "\n".join(changes)
    )
    await log_server("Rolle bearbeitet", desc, color=0xF39C12)


# ═══════════════════════════════════════════════════════════════════════════════
# 2 · MOD-LOG — Bans, Timeouts, Bot-Hinzufügungen
# ═══════════════════════════════════════════════════════════════════════════════

@bot.listen("on_member_ban")
async def _log_member_ban(guild: discord.Guild, user: discord.User):
    executor = await _audit_executor(
        guild, discord.AuditLogAction.ban, user.id
    )
    # Grund aus Audit-Log lesen
    reason = "—"
    try:
        await asyncio.sleep(1.5)
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if entry.target and entry.target.id == user.id:
                reason = entry.reason or "—"
                break
    except Exception:
        pass

    desc = (
        f"**Mitglied:** {user.mention} (`{user}` · ID: `{user.id}`)\n"
        f"**Gebannt von:** {executor.mention if executor else '—'}\n"
        f"**Grund:** {reason}"
    )
    await log_mod(
        "Mitglied gebannt",
        desc,
        color=0xE74C3C,
        thumbnail=str(user.display_avatar.url),
    )


@bot.listen("on_member_unban")
async def _log_member_unban(guild: discord.Guild, user: discord.User):
    executor = await _audit_executor(
        guild, discord.AuditLogAction.unban, user.id
    )
    desc = (
        f"**Mitglied:** {user.mention} (`{user}` · ID: `{user.id}`)\n"
        f"**Entbannt von:** {executor.mention if executor else '—'}"
    )
    await log_mod(
        "Mitglied entbannt",
        desc,
        color=0x2ECC71,
        thumbnail=str(user.display_avatar.url),
    )


@bot.listen("on_member_update")
async def _log_member_update(before: discord.Member, after: discord.Member):
    guild = after.guild

    # ── Timeout-Änderung ─────────────────────────────────────────────────────
    b_to = before.timed_out_until
    a_to = after.timed_out_until

    if b_to != a_to:
        if a_to and a_to > datetime.now(timezone.utc):
            # Timeout gesetzt
            executor = await _audit_executor(
                guild, discord.AuditLogAction.member_update, after.id
            )
            reason = "—"
            try:
                async for entry in guild.audit_logs(
                    limit=5, action=discord.AuditLogAction.member_update
                ):
                    if entry.target and entry.target.id == after.id:
                        reason = entry.reason or "—"
                        break
            except Exception:
                pass
            desc = (
                f"**Mitglied:** {after.mention} (`{after}`)\n"
                f"**Von:** {executor.mention if executor else '—'}\n"
                f"**Bis:** {_ts(a_to)}\n"
                f"**Grund:** {reason}"
            )
            await log_mod(
                "\u23F1\uFE0F Timeout erteilt",
                desc,
                color=0xF39C12,
                thumbnail=str(after.display_avatar.url),
            )
        else:
            # Timeout aufgehoben
            executor = await _audit_executor(
                guild, discord.AuditLogAction.member_update, after.id
            )
            desc = (
                f"**Mitglied:** {after.mention} (`{after}`)\n"
                f"**Aufgehoben von:** {executor.mention if executor else '—'}"
            )
            await log_mod(
                "\u23F1\uFE0F Timeout aufgehoben",
                desc,
                color=0x2ECC71,
                thumbnail=str(after.display_avatar.url),
            )

    # ── Rollen-Änderung (Zuweisung / Entzug an Mitglied) ─────────────────────
    b_roles = set(before.roles)
    a_roles = set(after.roles)

    added   = a_roles - b_roles
    removed = b_roles - a_roles

    if added or removed:
        executor = await _audit_executor(
            guild, discord.AuditLogAction.member_role_update, after.id
        )
        parts: list[str] = []
        if added:
            parts.append(
                "**Hinzugefügt:** " + ", ".join(r.mention for r in added)
            )
        if removed:
            parts.append(
                "**Entfernt:** " + ", ".join(r.mention for r in removed)
            )
        desc = (
            f"**Mitglied:** {after.mention} (`{after}`)\n"
            f"**Von:** {executor.mention if executor else '—'}\n\n"
            + "\n".join(parts)
        )
        from logs import log_role as _log_role
        await _log_role(
            "Rollen geändert",
            desc,
            color=0x9B59B6 if added else 0xE74C3C,
            thumbnail=str(after.display_avatar.url),
        )


# ── Bot-Hinzufüge-Versuche ────────────────────────────────────────────────────

@bot.listen("on_guild_integrations_update")
async def _log_bot_add_attempt(guild: discord.Guild):
    """Prüft ob ein Bot zum Server hinzugefügt wurde."""
    await asyncio.sleep(2.0)
    try:
        async for entry in guild.audit_logs(
            limit=5, action=discord.AuditLogAction.bot_add
        ):
            # Nur sehr neue Einträge (< 10 Sekunden alt)
            age = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
            if age > 10:
                break
            bot_user = entry.target
            executor  = entry.user
            desc = (
                f"**Bot:** {bot_user.mention if bot_user else '—'} "
                f"(`{bot_user}` · ID: `{getattr(bot_user, 'id', '—')}`)\n"
                f"**Hinzugefügt von:** {executor.mention if executor else '—'}\n\n"
                f"\u26A0\uFE0F Ein neuer Bot wurde dem Server hinzugefügt!"
            )
            await log_mod(
                "\U0001F916 Bot hinzugefügt",
                desc,
                color=0xE67E22,
            )
    except (discord.Forbidden, Exception):
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# 3 · MEMBER-LOG — Beitritt / Verlassen
# ═══════════════════════════════════════════════════════════════════════════════

@bot.listen("on_member_join")
async def _log_member_join(member: discord.Member):
    account_age = datetime.now(timezone.utc) - member.created_at
    age_str = f"{account_age.days} Tage"
    warn = ""
    if account_age.days < 7:
        warn = "\n\u26A0\uFE0F **Neues Konto** (weniger als 7 Tage alt)!"

    desc = (
        f"**Mitglied:** {member.mention} (`{member}` · ID: `{member.id}`)\n"
        f"**Account-Alter:** {age_str}\n"
        f"**Beigetreten:** {_ts()}"
        f"{warn}"
    )
    await log_member(
        "Mitglied beigetreten",
        desc,
        color=0x2ECC71,
        thumbnail=str(member.display_avatar.url),
    )


@bot.listen("on_member_remove")
async def _log_member_remove(member: discord.Member):
    roles = [r for r in member.roles if r.name != "@everyone"]
    roles_str = ", ".join(r.mention for r in roles) if roles else "—"

    # War es ein Kick?
    kicked_by = None
    try:
        await asyncio.sleep(1.5)
        async for entry in member.guild.audit_logs(
            limit=5, action=discord.AuditLogAction.kick
        ):
            if entry.target and entry.target.id == member.id:
                age = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                if age < 10:
                    kicked_by = entry.user
                break
    except Exception:
        pass

    if kicked_by:
        title = "\U0001F462 Mitglied gekickt"
        extra = f"\n**Gekickt von:** {kicked_by.mention}"
        color = 0xE67E22
    else:
        title = "\U0001F6AA Mitglied verlassen"
        extra = ""
        color = 0xE74C3C

    desc = (
        f"**Mitglied:** `{member}` · ID: `{member.id}`\n"
        f"**Rollen:** {roles_str}"
        f"{extra}"
    )
    await log_member(title, desc, color=color, thumbnail=str(member.display_avatar.url))


# ═══════════════════════════════════════════════════════════════════════════════
# 4 · NACHRICHTEN-LOG — Gelöscht / Bearbeitet / Bulk-Löschung
# ═══════════════════════════════════════════════════════════════════════════════

# Kanal-IDs die NICHT geloggt werden (Bot-Kanäle, Log-Kanäle usw.)
_MSG_LOG_IGNORE_CHANNELS: set[int] = {
    # Log-Kanäle selbst (verhindert Schleifen)
    1490878131240829028,
    1490878132230819840,
    1490878133279264842,
    1490878134847930368,
    1490878135837917234,
    1490878137385619598,
    1490878138429997087,
    1490878139306606743,
}


@bot.listen("on_message_delete")
async def _log_message_delete(message: discord.Message):
    if message.author.bot:
        return
    if not message.guild:
        return
    if message.channel.id in _MSG_LOG_IGNORE_CHANNELS:
        return

    # Wer hat gelöscht?
    deleted_by = None
    try:
        await asyncio.sleep(1.0)
        async for entry in message.guild.audit_logs(
            limit=5, action=discord.AuditLogAction.message_delete
        ):
            if (
                entry.target
                and entry.target.id == message.author.id
                and entry.extra.channel.id == message.channel.id
            ):
                age = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                if age < 8:
                    deleted_by = entry.user
                break
    except Exception:
        pass

    content = _short(message.content or "*— kein Text —*", 1000)
    attachments = ", ".join(a.filename for a in message.attachments) if message.attachments else None

    fields = [
        ("Inhalt", content, False),
        ("Kanal", message.channel.mention, True),
        ("Verfasser", message.author.mention, True),
    ]
    if deleted_by and deleted_by.id != message.author.id:
        fields.append(("Gelöscht von", deleted_by.mention, True))
    if attachments:
        fields.append(("Anhänge", attachments, False))

    await log_message(
        "Nachricht gelöscht",
        f"Erstellt: {_ts(message.created_at)}",
        color=0xE74C3C,
        fields=fields,
        thumbnail=str(message.author.display_avatar.url),
    )


@bot.listen("on_message_edit")
async def _log_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot:
        return
    if not before.guild:
        return
    if before.channel.id in _MSG_LOG_IGNORE_CHANNELS:
        return
    if before.content == after.content:
        return  # Nur Embed-Update, kein echter Edit

    b_text = _short(before.content or "*— leer —*", 512)
    a_text = _short(after.content  or "*— leer —*", 512)

    await log_message(
        "Nachricht bearbeitet",
        f"**Kanal:** {after.channel.mention} · {after.author.mention}\n"
        f"[Zur Nachricht]({after.jump_url})",
        color=0xF39C12,
        fields=[
            ("Vorher", b_text, False),
            ("Nachher", a_text, False),
        ],
        thumbnail=str(after.author.display_avatar.url),
    )


@bot.listen("on_bulk_message_delete")
async def _log_bulk_delete(messages: list[discord.Message]):
    if not messages:
        return
    guild = messages[0].guild
    if not guild:
        return
    channel = messages[0].channel

    executor = await _audit_executor(
        guild, discord.AuditLogAction.message_bulk_delete, channel.id
    )
    count = len(messages)
    desc = (
        f"**{count} Nachrichten** wurden auf einmal gelöscht.\n"
        f"**Kanal:** {channel.mention}\n"
        f"**Gelöscht von:** {executor.mention if executor else '—'}"
    )
    await log_message("Bulk-Löschung", desc, color=0xC0392B)


# ═══════════════════════════════════════════════════════════════════════════════
# 5 · MOD-LOG — Spam-Erkennung & Vulgäre Wörter
# ═══════════════════════════════════════════════════════════════════════════════

# Spam-Tracker: user_id → Liste von Zeitstempeln
_spam_tracker: dict[int, list[datetime]] = defaultdict(list)
_SPAM_THRESHOLD   = 6    # Nachrichten
_SPAM_WINDOW_SECS = 5    # innerhalb von X Sekunden
_spam_warned: set[int] = set()   # user_ids die kürzlich als Spam gemeldet wurden

# Vulgäre Wörter (Deutsch + häufige Englische)
_VULGAR_WORDS = re.compile(
    r"\b("
    r"fick|ficker|gefickt|fickst|fotze|hurensohn|hurenkind|nutte|wichser|wichse|"
    r"arschloch|scheiß|scheiße|scheiße|scheis|scheiss|kacke|kacken|"
    r"motherfuck|motherfucker|nigger|nigga|faggot|bastard|bitch|asshole|"
    r"anal|penis|vagina|schwanz|titten|"
    r"nazi|heil.{0,5}hitler|judensau"
    r")\b",
    re.IGNORECASE | re.UNICODE,
)

# Kanäle in denen Spam/Vulgär-Check NICHT greift
_CONTENT_CHECK_IGNORE: set[int] = set(_MSG_LOG_IGNORE_CHANNELS)


@bot.listen("on_message")
async def _log_spam_and_vulgar(message: discord.Message):
    if message.author.bot:
        return
    if not message.guild:
        return
    if message.channel.id in _CONTENT_CHECK_IGNORE:
        return

    now = datetime.now(timezone.utc)
    uid = message.author.id

    # ── Spam ──────────────────────────────────────────────────────────────────
    times = _spam_tracker[uid]
    times.append(now)
    # Alte Einträge entfernen
    cutoff = now - timedelta(seconds=_SPAM_WINDOW_SECS)
    _spam_tracker[uid] = [t for t in times if t >= cutoff]

    if len(_spam_tracker[uid]) >= _SPAM_THRESHOLD and uid not in _spam_warned:
        _spam_warned.add(uid)
        asyncio.get_event_loop().call_later(30, lambda: _spam_warned.discard(uid))

        desc = (
            f"**Mitglied:** {message.author.mention} (`{message.author}`)\n"
            f"**Kanal:** {message.channel.mention}\n"
            f"**Nachrichten:** {len(_spam_tracker[uid])} in {_SPAM_WINDOW_SECS} Sekunden"
        )
        await log_mod(
            "\U0001F4E8 Spam erkannt",
            desc,
            color=0xE67E22,
            thumbnail=str(message.author.display_avatar.url),
        )

    # ── Vulgäre Wörter ────────────────────────────────────────────────────────
    if message.content and _VULGAR_WORDS.search(message.content):
        matches = list(set(_VULGAR_WORDS.findall(message.content)))
        desc = (
            f"**Mitglied:** {message.author.mention} (`{message.author}`)\n"
            f"**Kanal:** {message.channel.mention}\n"
            f"**Erkannte Wörter:** `{'`, `'.join(matches)}`\n"
            f"**Nachricht:** {_short(message.content, 400)}"
        )
        await log_mod(
            "\U0001F4A2 Vulgäre Sprache",
            desc,
            color=0x992D22,
            thumbnail=str(message.author.display_avatar.url),
        )
