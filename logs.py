# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# logs.py \u2014 Erweiterte Server-Logs
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#
# Erg\u00E4nzt events.py um:
#   \u2022 Voice-Channel Beitritt / Verlassen / Wechsel  \u2192 MEMBER_LOG
#   \u2022 Namens- / Nickname-\u00C4nderungen                 \u2192 MEMBER_LOG
#   \u2022 Rollen erstellt / gel\u00F6scht                    \u2192 ROLE_LOG
#   \u2022 Timeout verh\u00E4ngt / aufgehoben                 \u2192 MOD_LOG
#   \u2022 Server-\u00C4nderungen (Shop-Items, etc.)          \u2192 SERVER_LOG
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

import discord
import dashboard_hooks as _dh
from config import (
    bot,
    MEMBER_LOG_CHANNEL_ID,
    ROLE_LOG_CHANNEL_ID,
    MOD_LOG_CHANNEL_ID,
    LOG_COLOR, MOD_COLOR,
    GUILD_ID,
    AKTIVITAET_WARN_CHANNEL_ID,
)
from datetime import datetime, timezone

SERVER_LOG_CHANNEL_ID = 1490878131240829028


# \u2500\u2500 Voice-Channel Log \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
        _dh.log_activity('VOICE', f'{member} ist "{after.channel.name}" beigetreten', member.id)
    elif before.channel is not None and after.channel is None:
        _dh.log_activity('VOICE', f'{member} hat "{before.channel.name}" verlassen', member.id)
    else:
        _dh.log_activity('VOICE', f'{member} wechselte von "{before.channel.name}" zu "{after.channel.name}"', member.id)

    if before.channel is None and after.channel is not None:
        title = "\U0001F50A Voice beigetreten"
        desc  = (
            f"**Mitglied:** {member.mention} (`{member}`)\n"
            f"**Kanal:** {after.channel.mention}"
        )
        color = LOG_COLOR
    elif before.channel is not None and after.channel is None:
        title = "\U0001F507 Voice verlassen"
        desc  = (
            f"**Mitglied:** {member.mention} (`{member}`)\n"
            f"**Kanal:** {before.channel.mention}"
        )
        color = LOG_COLOR
    else:
        title = "\U0001F500 Voice gewechselt"
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


# \u2500\u2500 Namens- / Nickname-\u00C4nderung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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

    _dh.log_activity('NAME', f'{after}: Name/Nick ge\u00E4ndert', after.id)

    desc = f"**Mitglied:** {after.mention} (`{after}`)\n"
    if name_changed:
        desc += f"**Username:** `{before.name}` \u2192 `{after.name}`\n"
    if nick_changed:
        desc += (
            f"**Nickname:** `{before.nick or '\u2014'}` \u2192 `{after.nick or '\u2014'}`\n"
        )

    embed = discord.Embed(
        title="\u270F\uFE0F Name ge\u00E4ndert",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass


# \u2500\u2500 Timeout Log \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
        _dh.log_activity('TIMEOUT', f'{after} wurde getimeouted bis {after_to.strftime("%d.%m.%Y %H:%M UTC")}', after.id)
    else:
        _dh.log_activity('TIMEOUT', f'Timeout von {after} aufgehoben', after.id)

    if after_to is not None:
        title = "\U0001F507 Timeout verh\u00E4ngt"
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
        title = "\u2705 Timeout aufgehoben"
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


# \u2500\u2500 Rollen erstellt / gel\u00F6scht \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
        title="\u2705 Rolle erstellt",
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
    _dh.log_warning(
        '\U0001F5D1\uFE0F Rolle gel\u00F6scht',
        f'Die Rolle **{role.name}** wurde vom Server gel\u00F6scht.',
    )
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
        desc += f"\n**Gel\u00F6scht von:** {deleter.mention} (`{deleter}`)"

    embed = discord.Embed(
        title="\U0001f5d1\ufe0f Rolle gel\u00f6scht",
        description=desc,
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass
    try:
        _wc = guild.get_channel(AKTIVITAET_WARN_CHANNEL_ID)
        if _wc:
            await _wc.send(embed=embed)
    except Exception:
        pass


# \u2500\u2500 Unban Log \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
        title="\u2705 Mitglied entbannt",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass


# \u2500\u2500 Kanal gel\u00F6scht \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.listen("on_guild_channel_delete")
async def log_channel_delete(channel):
    guild = channel.guild
    deleter = None
    try:
        import discord as _discord
        async for entry in guild.audit_logs(limit=3, action=_discord.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                deleter = entry.user
                break
    except Exception:
        pass
    _dh.log_warning(
        '\U0001f4e2 Kanal gel\u00f6scht',
        f'Kanal **#{channel.name}** wurde gel\u00f6scht.'
        + (f' | Von: {deleter}' if deleter else ''),
    )
    _dh.log_activity(
        'KANAL',
        f'Kanal #{channel.name} gel\u00f6scht' + (f' von {deleter}' if deleter else ''),
    )
    try:
        _wc = guild.get_channel(AKTIVITAET_WARN_CHANNEL_ID)
        if _wc:
            _kd_desc = f"**Kanal:** `#{channel.name}`"
            if deleter:
                _kd_desc += f"\n**Gel\u00f6scht von:** {deleter.mention} (`{deleter}`)"
            _kd_embed = discord.Embed(
                title="\u26a0\ufe0f Aktivit\u00e4tswarnung \u2014 Kanal gel\u00f6scht",
                description=_kd_desc,
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc),
            )
            _kd_embed.set_footer(text="Paradise City Roleplay \u2022 Server-Schutz")
            await _wc.send(embed=_kd_embed)
    except Exception:
        pass


# \u2500\u2500 Helfer: Server-\u00C4nderungen loggen (Items, Shop, etc.) \u2500\u2500\u2500\u2500\u2500\u2500

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
    embed.set_footer(text="Paradise City Roleplay \u2014 Server-Log")
    try:
        await log_ch.send(embed=embed)
    except Exception:
        pass
