import os
import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import re
import asyncio
import traceback

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot_start_time = None
invite_cache = {}

ADMIN_ROLE_ID     = 1490855702225485936
MOD_ROLE_ID       = 1490855703370534965
WHITELIST_ROLE_ID = 1490855725516460234

MOD_LOG_CHANNEL_ID     = 1490878132230819840
MESSAGE_LOG_CHANNEL_ID = 1490878135837917234
ROLE_LOG_CHANNEL_ID    = 1490878137385619598
MEMBER_LOG_CHANNEL_ID  = 1490878134847930368
JOIN_LOG_CHANNEL_ID    = 1490878153391083683
BOT_LOG_CHANNEL_ID     = 1490878133279264842
MEMES_CHANNEL_ID       = 1490882578276810924
GUILD_ID               = 1490839259907887239
TICKET_CHANNEL_ID      = 1490855943230066818

LOG_COLOR = 0x00BFFF
MOD_COLOR = 0xFF0000

DISCORD_INVITE_RE = re.compile(
    r'(https?://)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com/invite|discord\.com/invite)/\S+',
    re.IGNORECASE
)
URL_RE = re.compile(r'https?://\S+', re.IGNORECASE)

VULGAR_WORDS = [
    "fotze", "wichser", "hurensohn", "arschloch", "fick", "ficken",
    "neger", "nigger", "wichsen", "schlampe", "nutte", "hure",
    "wixer", "drecksau", "scheisskopf", "pisser", "dreckssack",
    "mongo", "spast", "vollidiot", "schwachkopf", "dreckskerl",
    "mistkerl", "penner", "hurenkind", "dummficker", "scheiß",
]

spam_tracker = {}
spam_warned   = set()

FEATURES = {
    "Discord Link Schutz":    True,
    "Link Filter (Memes)":   True,
    "Vulgäre Wörter Filter": True,
    "Spam Schutz":           True,
    "Nachrichten Log":       True,
    "Bearbeitungs Log":      True,
    "Rollen Log":            True,
    "Member Log":            True,
    "Join Log + Invites":    True,
    "Bot Kick":              True,
    "Fehler Logging":        True,
}

def is_admin(member):
    return any(r.id == ADMIN_ROLE_ID for r in member.roles)

def is_mod_or_admin(member):
    return any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in member.roles)

def contains_vulgar(text: str) -> bool:
    text_lower = text.lower()
    return any(word in text_lower for word in VULGAR_WORDS)

async def log_bot_error(title: str, error_text: str, guild=None):
    guilds_to_check = [guild] if guild else bot.guilds
    for g in guilds_to_check:
        if not g:
            continue
        log_ch = g.get_channel(BOT_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title=f"⚠️ Bot Fehler — {title}",
                description=f"```{error_text[:1900]}```",
                color=MOD_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            try:
                await log_ch.send(embed=embed)
            except Exception:
                pass
            break

async def send_bot_status():
    for guild in bot.guilds:
        log_ch = guild.get_channel(BOT_LOG_CHANNEL_ID)
        if not log_ch:
            continue
        desc = ""
        for feature, status in FEATURES.items():
            emoji = "🟢" if status else "🔴"
            state = "Online" if status else "Offline"
            desc += f"{emoji} **{feature}** — {state}\n"
        embed = discord.Embed(
            title="🤖 Bot Status — Alle Funktionen",
            description=desc,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await log_ch.send(embed=embed)
        except Exception:
            pass

@bot.event
async def on_ready():
    global bot_start_time, invite_cache
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")
    for guild in bot.guilds:
        try:
            invites = await guild.fetch_invites()
            invite_cache[guild.id] = {inv.code: inv for inv in invites}
        except Exception:
            pass
    await send_bot_status()

@bot.event
async def on_error(event, *args, **kwargs):
    err = traceback.format_exc()
    await log_bot_error(f"Event: {event}", err)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, (commands.MissingRole, commands.CheckFailure)):
        return
    err = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    await log_bot_error(f"Command: {ctx.command}", err, ctx.guild)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if bot_start_time and message.created_at < bot_start_time:
        return
    member = message.author
    if not is_admin(member) and DISCORD_INVITE_RE.search(message.content):
        await handle_discord_invite(message)
        return
    if not is_mod_or_admin(member) and message.channel.id != MEMES_CHANNEL_ID:
        if URL_RE.search(message.content):
            await handle_link_outside_memes(message)
            return
    if not is_mod_or_admin(member) and contains_vulgar(message.content):
        await handle_vulgar_message(message)
        return
    await check_spam(message)
    await bot.process_commands(message)

async def handle_discord_invite(message):
    member = message.author
    guild  = message.guild

    try:
        await message.delete()
    except Exception as e:
        await log_bot_error("Nachricht löschen (Discord Link)", str(e), guild)

    timeout_until = datetime.now(timezone.utc) + timedelta(hours=300)
    timeout_ok = False
    try:
        await member.timeout(timeout_until, reason="Fremden Discord-Link gesendet")
        timeout_ok = True
    except Exception as e:
        await log_bot_error(
            "Timeout fehlgeschlagen (Discord Link)",
            f"Benutzer: {member} ({member.id})\nFehler: {e}\n\n"
            f"Mögliche Ursachen:\n"
            f"- Bot hat keine 'Mitglieder moderieren' Berechtigung\n"
            f"- Bot-Rolle ist niedriger als die Ziel-Rolle",
            guild
        )

    try:
        embed = discord.Embed(
            description=(
                "> Du hast gegen unsere Server Regeln verstoßen\n\n"
                "> Bitte wende dich an den Support"
            ),
            color=MOD_COLOR
        )
        await member.send(content=member.mention, embed=embed)
    except Exception:
        pass

    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        status = "✅ Timeout erteilt (300h)" if timeout_ok else "❌ Timeout fehlgeschlagen — Bot-Berechtigung prüfen!"
        embed = discord.Embed(
            title="🔨 Moderation — Timeout",
            description=(
                f"**Benutzer:** {member.mention} (`{member}`)\n"
                f"**Aktion:** {status}\n"
                f"**Grund:** Fremden Discord-Link gesendet\n"
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
        timeout_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        try:
            await message.author.timeout(timeout_until, reason="Wiederholtes Spammen")
        except Exception as e:
            await log_bot_error(
                "Timeout fehlgeschlagen (Spam)",
                f"Benutzer: {message.author} ({message.author.id})\nFehler: {e}\n\n"
                f"Mögliche Ursachen:\n"
                f"- Bot hat keine 'Mitglieder moderieren' Berechtigung\n"
                f"- Bot-Rolle ist niedriger als die Ziel-Rolle",
                message.guild
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
            embed = discord.Embed(
                title="🔨 Moderation — Timeout (Spam)",
                description=(
                    f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
                    f"**Aktion:** 10 Minuten Timeout\n"
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

@bot.event
async def on_message_delete(message):
    if not message.guild or message.author.bot:
        return
    log_ch = message.guild.get_channel(MESSAGE_LOG_CHANNEL_ID)
    if not log_ch:
        return
    embed = discord.Embed(
        title="🗑️ Nachricht gelöscht",
        description=(
            f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
            f"**Kanal:** {message.channel.mention}\n"
            f"**Inhalt:** {message.content[:500] if message.content else '*Kein Text*'}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if not before.guild or before.author.bot:
        return
    if before.content == after.content:
        return
    log_ch = before.guild.get_channel(MESSAGE_LOG_CHANNEL_ID)
    if not log_ch:
        return
    embed = discord.Embed(
        title="✏️ Nachricht bearbeitet",
        description=(
            f"**Benutzer:** {before.author.mention} (`{before.author}`)\n"
            f"**Kanal:** {before.channel.mention}\n"
            f"**Vorher:** {before.content[:250] if before.content else '*Kein Text*'}\n"
            f"**Nachher:** {after.content[:250] if after.content else '*Kein Text*'}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    if before.roles == after.roles:
        return
    guild  = after.guild
    log_ch = guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if not log_ch:
        return
    added   = [r for r in after.roles if r not in before.roles]
    removed = [r for r in before.roles if r not in after.roles]
    if not added and not removed:
        return
    description = f"**Benutzer:** {after.mention} (`{after}`)\n"
    if added:
        description += f"**Hinzugefügt:** {', '.join(r.mention for r in added)}\n"
    if removed:
        description += f"**Entfernt:** {', '.join(r.mention for r in removed)}\n"
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == after.id:
                description += f"**Geändert von:** {entry.user.mention} (`{entry.user}`)"
                break
    except Exception:
        pass
    embed = discord.Embed(
        title="🎭 Rollen geändert",
        description=description,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if not log_ch:
        return
    reason = "Kein Grund angegeben"
    banner = None
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                reason = entry.reason or reason
                banner = entry.user
                break
    except Exception:
        pass
    description = f"**Benutzer:** {user.mention} (`{user}`)\n**Grund:** {reason}"
    if banner:
        description += f"\n**Gebannt von:** {banner.mention} (`{banner}`)"
    embed = discord.Embed(
        title="🔨 Mitglied gebannt",
        description=description,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)

@bot.event
async def on_member_remove(member):
    guild  = member.guild
    log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if not log_ch:
        return
    await asyncio.sleep(1)
    action = "verlassen"
    mod    = None
    reason = None
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                action = "gekickt"
                mod    = entry.user
                reason = entry.reason or "Kein Grund angegeben"
                break
    except Exception:
        pass
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.ban):
            if entry.target.id == member.id:
                return
    except Exception:
        pass
    description = f"**Benutzer:** {member.mention} (`{member}`)\n**Aktion:** {action}"
    if mod:
        description += f"\n**Von:** {mod.mention} (`{mod}`)"
    if reason:
        description += f"\n**Grund:** {reason}"
    title = "👢 Mitglied gekickt" if action == "gekickt" else "🚪 Mitglied hat den Server verlassen"
    embed = discord.Embed(
        title=title,
        description=description,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)

@bot.event
async def on_invite_create(invite):
    guild = invite.guild
    if guild.id not in invite_cache:
        invite_cache[guild.id] = {}
    invite_cache[guild.id][invite.code] = invite

@bot.event
async def on_member_join(member):
    guild = member.guild
    if member.bot:
        try:
            await member.kick(reason="Bots sind auf diesem Server nicht erlaubt")
        except Exception:
            pass
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    embed = discord.Embed(
                        description="> Bots auf diesen Server hinzufügen ist für dich leider nicht erlaubt.",
                        color=MOD_COLOR
                    )
                    try:
                        await entry.user.send(content=entry.user.mention, embed=embed)
                    except Exception:
                        pass
                    break
        except Exception:
            pass
        return
    member_log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if member_log_ch:
        embed = discord.Embed(
            title="✅ Mitglied beigetreten",
            description=f"**Benutzer:** {member.mention} (`{member}`)",
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await member_log_ch.send(embed=embed)
    inviter      = None
    inviter_uses = 0
    try:
        new_invites    = await guild.fetch_invites()
        new_invite_map = {inv.code: inv for inv in new_invites}
        old_invite_map = invite_cache.get(guild.id, {})
        for code, new_inv in new_invite_map.items():
            old_inv = old_invite_map.get(code)
            if old_inv and new_inv.uses > old_inv.uses:
                inviter      = new_inv.inviter
                inviter_uses = new_inv.uses
                break
        invite_cache[guild.id] = new_invite_map
    except Exception:
        pass
    join_log_ch = guild.get_channel(JOIN_LOG_CHANNEL_ID)
    if join_log_ch:
        description = f"**Spieler:** {member.mention} (`{member}`)\n"
        if inviter:
            description += f"**Eingeladen von:** {inviter.mention} (`{inviter}`)\n"
            description += f"**Invites von {inviter.display_name}:** {inviter_uses}"
        else:
            description += "**Eingeladen von:** Unbekannt"
        embed = discord.Embed(
            title="📥 Neues Mitglied",
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await join_log_ch.send(embed=embed)
    rolle = guild.get_role(WHITELIST_ROLE_ID)
    if rolle:
        try:
            await member.add_roles(rolle)
        except Exception:
            pass
    try:
        embed = discord.Embed(
            description=(
                "> Willkommen auf Kryptik Roleplay deinem RP server mit Ultimativem Spaß und Hochwertigem RP\n\n"
                "> Wir wünschen dir viel Spaß auf unserem Server und hoffen das du dich bei uns Gut Zurecht findest\n\n"
                "> Solltest du mal Schwierigkeiten haben melde dich gerne Jederzeit über ein Support Ticket im channel "
                f"[#ticket-erstellen](https://discord.com/channels/{GUILD_ID}/{TICKET_CHANNEL_ID})"
            ),
            color=LOG_COLOR
        )
        await member.send(content=member.mention, embed=embed)
    except Exception:
        pass

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! 👋")

@bot.command(name="testping")
async def testping(ctx):
    if not is_admin(ctx.author):
        return
    kanal = ctx.guild.get_channel(JOIN_LOG_CHANNEL_ID)
    rolle = ctx.guild.get_role(MOD_ROLE_ID)
    if kanal and rolle:
        await kanal.send(f"{rolle.mention} Dies ist ein Test-Ping vom Bot!")
    try:
        await ctx.message.delete()
    except Exception:
        pass

@bot.command(name="botstatus")
async def botstatus(ctx):
    if not is_admin(ctx.author):
        return
    await send_bot_status()
    try:
        await ctx.message.delete()
    except Exception:
        pass

token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
