# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# moderation.py \u2014 Auto-Moderation (Spam, Links, Vulg\xe4re Sprache)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from helpers import is_admin, is_mod_or_admin, log_bot_error, apply_timeout_restrictions
import dashboard_hooks as _dh


async def handle_discord_invite(message):
    member  = message.author
    guild   = message.guild
    inhalt  = message.content[:300]

    # 1) Nachricht sofort l\u00f6schen
    try:
        await message.delete()
    except Exception as e:
        await log_bot_error("Nachricht l\u00f6schen (Discord Link)", str(e), guild)

    _dh.log_warning(
        '\U0001F517 Fremder Discord-Link',
        f'{member} (`{member.id}`) hat in #{message.channel.name} einen fremden Server-Link gesendet: {inhalt}',
    )
    _dh.log_activity(
        'LINK',
        f'{member} sendete fremden Link in #{message.channel.name}: {inhalt[:100]}',
        member.id,
    )
    # 2) DM an den T\u00e4ter
    try:
        dm_embed = discord.Embed(
            title="\U0001F6AB Link gel\u00f6scht",
            description=(
                f"**Server:** {guild.name}\n\n"
                "Du hast einen Einladungslink zu einem **fremden Discord-Server** gesendet.\n"
                "Das ist auf diesem Server nicht erlaubt \u2014 deine Nachricht wurde sofort gel\u00f6scht."
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        dm_embed.set_footer(text="Paradise City Roleplay \u2022 Moderation")
        await member.send(embed=dm_embed)
    except Exception:
        pass

    # 3) Aktivit\u00e4tswarnung per DM an den Inhaber
    try:
        owner = await guild.fetch_member(OWNER_ID)
    except Exception:
        owner = None
    if owner:
        try:
            warn_embed = discord.Embed(
                title="\u26A0\uFE0F Aktivit\u00e4tswarnung \u2014 Fremder Discord-Link",
                description=(
                    f"\U0001F464 **Benutzer:** {member.mention} (`{member}` | `{member.id}`)\n"
                    f"\U0001F4E2 **Kanal:** {message.channel.mention}\n"
                    f"\U0001F4DD **Nachricht:** {inhalt}\n"
                    f"\U0001F552 **Zeitpunkt:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>\n\n"
                    "\U0001F5D1\uFE0F Die Nachricht wurde automatisch gel\u00f6scht."
                ),
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc),
            )
            warn_embed.set_footer(text="Paradise City Roleplay \u2022 Server-Schutz")
            await owner.send(embed=warn_embed)
        except Exception:
            pass


async def handle_link_outside_memes(message):
    try:
        await message.delete()
    except Exception:
        pass
    try:
        await message.channel.send(
            f"{message.author.mention} Bitte sende Links ausschlie\xdflich im <#{MEMES_CHANNEL_ID}> Kanal",
            delete_after=6
        )
    except Exception:
        pass


async def handle_vulgar_message(message):
    try:
        await message.delete()
    except Exception:
        pass
    try:
        embed = discord.Embed(
            description=(
                "> **Verwarnung:** Du hast einen vulg\xe4ren Ausdruck verwendet.\n\n"
                "> Bitte beachte unsere Serverregeln. Bei weiteren Verst\xf6\xdfen folgen Konsequenzen."
            ),
            color=MOD_COLOR
        )
        await message.author.send(content=message.author.mention, embed=embed)
    except Exception:
        pass
    log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="\U0001f528 Moderation \u2014 Vulg\xe4re Sprache",
            description=(
                f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
                f"**Kanal:** {message.channel.mention}\n"
                f"**Nachricht:** {message.content[:300]}"
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Paradise City Roleplay \u2022 Moderation")
        await log_ch.send(embed=embed)


async def check_spam(message):
    user_id = message.author.id
    now = datetime.now(timezone.utc)
    if user_id not in spam_tracker:
        spam_tracker[user_id] = []
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if (now - t).total_seconds() < 5]
    spam_tracker[user_id].append(now)
    count = len(spam_tracker[user_id])
    if count >= 5 and user_id in spam_warned:
        spam_tracker[user_id] = []
        spam_warned.discard(user_id)
        try:
            await message.channel.purge(limit=50, check=lambda m: m.author.id == user_id)
        except Exception:
            pass
        timeout_ok, roles_removed = await apply_timeout_restrictions(
            message.author, message.guild, duration_m=10, reason="Wiederholtes Spammen"
        )
        try:
            embed = discord.Embed(
                description="> Du wurdest aufgrund von wiederholtem Spammen f\xfcr **10 Minuten** stummgeschaltet.",
                color=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        except Exception:
            pass
        log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            timeout_status = "\u2705 Timeout erteilt (10min)" if timeout_ok else "\u274c Timeout fehlgeschlagen \u2014 Berechtigung pr\xfcfen!"
            rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
            embed = discord.Embed(
                title="\U0001f528 Moderation \u2014 Timeout (Spam)",
                description=(
                    f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
                    f"**Timeout:** {timeout_status}\n"
                    f"**Rollen:** {rollen_status}\n"
                    f"**Grund:** Wiederholtes Spammen"
                ),
                color=MOD_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="Paradise City Roleplay \u2022 Moderation")
            await log_ch.send(embed=embed)
    elif count >= 5 and user_id not in spam_warned:
        spam_tracker[user_id] = []
        spam_warned.add(user_id)
        try:
            await message.channel.purge(limit=50, check=lambda m: m.author.id == user_id)
        except Exception:
            pass
        try:
            embed = discord.Embed(
                description=(
                    "> **Verwarnung:** Bitte vermeide es zu spammen.\n\n"
                    "> Bei Wiederholung erh\xe4ltst du einen 10 Minuten Timeout."
                ),
                color=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        except Exception:
            pass
