# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# moderation.py — Auto-Moderation (Spam, Links, Vulgäre Sprache)
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import is_admin, is_mod_or_admin, log_bot_error, apply_timeout_restrictions


async def handle_discord_invite(message):
    member = message.author
    guild  = message.guild
    grund  = "Fremden Discord-Link gesendet"
    try:
        await message.delete()
    except Exception as e:
        await log_bot_error("Nachricht löschen (Discord Link)", str(e), guild)
    try:
        dm_embed = discord.Embed(
            title="🚫 Du wurdest permanent gebannt",
            description=(
                f"**Server:** {guild.name}\n"
                f"**Grund:** {grund}\n\n"
                "Du hast einen fremden Discord-Einladungslink gesendet, was gegen unsere Serverregeln verstößt.\n"
                "Bei Fragen wende dich an den Support."
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await member.send(embed=dm_embed)
    except Exception:
        pass
    ban_status = "⏳ Ban wird ausgeführt..."
    try:
        await guild.ban(member, reason=grund, delete_message_days=1)
        ban_status = "✅ Gebannt"
    except Exception as e:
        ban_status = f"❌ Ban fehlgeschlagen: {e}"
        await log_bot_error("Ban fehlgeschlagen (Discord Link)", str(e), guild)
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="🔨 Moderation — Discord Link Ban",
            description=(
                f"**Benutzer:** {member.mention} (`{member}`)\n"
                f"**Status:** {ban_status}\n"
                f"**Grund:** {grund}\n"
                f"**Kanal:** {message.channel.mention}\n"
                f"**Nachricht:** {message.content[:300]}"
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await log_ch.send(embed=embed)


async def handle_link_outside_memes(message):
    try:
        await message.delete()
    except Exception:
        pass
    try:
        await message.channel.send(
            f"{message.author.mention} Bitte sende Links ausschließlich im <#{MEMES_CHANNEL_ID}> Kanal",
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
                "> **Verwarnung:** Du hast einen vulgären Ausdruck verwendet.\n\n"
                "> Bitte beachte unsere Serverregeln. Bei weiteren Verstößen folgen Konsequenzen."
            ),
            color=MOD_COLOR
        )
        await message.author.send(content=message.author.mention, embed=embed)
    except Exception:
        pass
    log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="🔨 Moderation — Vulgäre Sprache",
            description=(
                f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
                f"**Kanal:** {message.channel.mention}\n"
                f"**Nachricht:** {message.content[:300]}"
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
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
                description="> Du wurdest aufgrund von wiederholtem Spammen für **10 Minuten** stummgeschaltet.",
                color=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        except Exception:
            pass
        log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            timeout_status = "✅ Timeout erteilt (10min)" if timeout_ok else "❌ Timeout fehlgeschlagen — Berechtigung prüfen!"
            rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
            embed = discord.Embed(
                title="🔨 Moderation — Timeout (Spam)",
                description=(
                    f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
                    f"**Timeout:** {timeout_status}\n"
                    f"**Rollen:** {rollen_status}\n"
                    f"**Grund:** Wiederholtes Spammen"
                ),
                color=MOD_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
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
                    "> Bei Wiederholung erhältst du einen 10 Minuten Timeout."
                ),
                color=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        except Exception:
            pass
