# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# logs.py — Erweiterte Server-Logs
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════
#
# Ergänzt events.py um:
#   • Voice-Channel Beitritt / Verlassen / Wechsel  → MEMBER_LOG
#   • Namens- / Nickname-Änderungen                 → MEMBER_LOG
#   • Rollen erstellt / gelöscht                    → ROLE_LOG
#   • Timeout verhängt / aufgehoben                 → MOD_LOG
#   • Server-Änderungen (Shop-Items, etc.)          → SERVER_LOG
# ══════════════════════════════════════════════════════════════

import discord
from config import (
    bot,
    MEMBER_LOG_CHANNEL_ID,
    ROLE_LOG_CHANNEL_ID,
    MOD_LOG_CHANNEL_ID,
    LOG_COLOR, MOD_COLOR,
)
from datetime import datetime, timezone

SERVER_LOG_CHANNEL_ID = 1490878131240829028


# ── Voice-Channel Log ─────────────────────────────────────────

@bot.listen("on_voice_state_update")
async def log_voice_state(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return
    guild  = member.guild
    log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if not log_ch:
        return

    if before.channel == after.channel:
        return

    if before.channel is None and after.channel is not None:
        title = "🔊 Voice beigetreten"
        desc  = (
            f"**Mitglied:** {member.mention} (`{member}`)\n"
            f"**Kanal:** {after.channel.mention}"
        )
        color = LOG_COLOR
    elif before.channel is not None and after.channel is None:
        title = "🔇 Voice verlassen"
        desc  = (
            f"**Mitglied:** {member.mention} (`{member}`)\n"
            f"**Kanal:** {before.channel.mention}"
        )
        color = LOG_COLOR
    else:
        title = "🔀 Voice gewechselt"
        desc  = (
            f"**Mitglied:** {member.mention} (`{member}`)\n"
            f"**Von:** {before.channel.mention}\n"
            f"**Nach:** {after.channel.mention}"
        )
        color = LOG_COLOR

    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass


# ── Namens- / Nickname-Änderung ───────────────────────────────

@bot.listen("on_member_update")
async def log_name_change(before: discord.Member, after: discord.Member):
    guild  = after.guild
    log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if not log_ch:
        return

    nick_changed = before.nick != after.nick
    name_changed = before.name != after.name

    if not nick_changed and not name_changed:
        return

    if before.roles != after.roles:
        return

    desc = f"**Mitglied:** {after.mention} (`{after}`)\n"
    if name_changed:
        desc += f"**Username:** `{before.name}` → `{after.name}`\n"
    if nick_changed:
        desc += (
            f"**Nickname:** `{before.nick or '—'}` → `{after.nick or '—'}`\n"
        )

    embed = discord.Embed(
        title="✏️ Name geändert",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass


# ── Timeout Log ───────────────────────────────────────────────

@bot.listen("on_member_update")
async def log_timeout(before: discord.Member, after: discord.Member):
    guild  = after.guild
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return

    before_to = before.timed_out_until
    after_to  = after.timed_out_until

    if before_to == after_to:
        return

    if after_to is not None:
        title = "🔇 Timeout verhängt"
        ts    = int(after_to.timestamp())
        desc  = (
            f"**Mitglied:** {after.mention} (`{after}`)\n"
            f"**Bis:** <t:{ts}:F> (<t:{ts}:R>)"
        )
        try:
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id:
                    desc += f"\n**Von:** {entry.user.mention} (`{entry.user}`)"
                    if entry.reason:
                        desc += f"\n**Grund:** {entry.reason}"
                    break
        except Exception:
            pass
        color = MOD_COLOR
    else:
        title = "✅ Timeout aufgehoben"
        desc  = f"**Mitglied:** {after.mention} (`{after}`)"
        color = LOG_COLOR

    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass


# ── Rollen erstellt / gelöscht ────────────────────────────────

@bot.listen("on_guild_role_create")
async def log_role_create(role: discord.Role):
    guild  = role.guild
    log_ch = guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if not log_ch:
        return

    creator = None
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.role_create):
            if entry.target.id == role.id:
                creator = entry.user
                break
    except Exception:
        pass

    desc = f"**Rolle:** {role.mention} (`{role.name}`)\n**Farbe:** `{role.color}`"
    if creator:
        desc += f"\n**Erstellt von:** {creator.mention} (`{creator}`)"

    embed = discord.Embed(
        title="✅ Rolle erstellt",
        description=desc,
        color=role.color.value or LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass


@bot.listen("on_guild_role_delete")
async def log_role_delete(role: discord.Role):
    guild  = role.guild
    log_ch = guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if not log_ch:
        return

    deleter = None
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.role_delete):
            if entry.target.id == role.id:
                deleter = entry.user
                break
    except Exception:
        pass

    desc = f"**Rolle:** `{role.name}`"
    if deleter:
        desc += f"\n**Gelöscht von:** {deleter.mention} (`{deleter}`)"

    embed = discord.Embed(
        title="🗑️ Rolle gelöscht",
        description=desc,
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass


# ── Unban Log ─────────────────────────────────────────────────

@bot.listen("on_member_unban")
async def log_unban(guild: discord.Guild, user: discord.User):
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return

    unbanner = None
    reason   = "Kein Grund angegeben"
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.unban):
            if entry.target.id == user.id:
                unbanner = entry.user
                reason   = entry.reason or reason
                break
    except Exception:
        pass

    desc = f"**Benutzer:** {user.mention} (`{user}`)\n**Grund:** {reason}"
    if unbanner:
        desc += f"\n**Entbannt von:** {unbanner.mention} (`{unbanner}`)"

    embed = discord.Embed(
        title="✅ Mitglied entbannt",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass


# ── Helfer: Server-Änderungen loggen (Items, Shop, etc.) ──────

async def log_server_change(guild: discord.Guild, title: str, description: str):
    log_ch = guild.get_channel(SERVER_LOG_CHANNEL_ID)
    if not log_ch:
        return
    embed = discord.Embed(
        title=title,
        description=description,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay — Server-Log")
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass
