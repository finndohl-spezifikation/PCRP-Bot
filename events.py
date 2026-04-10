# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# events.py — Discord Events (on_ready, on_message, Logs, etc.)
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import is_admin, is_mod_or_admin, contains_vulgar, log_bot_error
from economy_helpers import (
    load_economy, save_economy, get_user, load_hidden_items,
    counting_state, save_counting_state, VersteckRetrieveView, log_money_action
)
from moderation import (
    handle_discord_invite, handle_link_outside_memes,
    handle_vulgar_message, check_spam
)
from ticket import (
    TicketSelectView, TicketActionView, auto_ticket_setup, auto_lohnliste_setup
)
from handy import HandyView, auto_handy_setup
from einreise import EinreiseView, auto_einreise_setup, load_ausweis, save_ausweis
from casino import CasinoView, auto_casino_setup



@bot.event
async def on_ready():
    global bot_start_time, invite_cache
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")

    bot.add_view(TicketSelectView())
    bot.add_view(TicketActionView())
    bot.add_view(HandyView())
    bot.add_view(EinreiseView())
    bot.add_view(CasinoView())

    for entry in load_hidden_items():
        bot.add_view(VersteckRetrieveView(entry["id"], entry["owner_id"]))

    for guild in bot.guilds:
        try:
            invites = await guild.fetch_invites()
            invite_cache[guild.id] = {inv.code: inv for inv in invites}
        except Exception:
            pass

    await auto_ticket_setup()
    await auto_lohnliste_setup()
    await auto_einreise_setup()
    await auto_handy_setup()
    await auto_casino_setup()

    GALAXY_BOT_ID = 270904126974590976
    for guild in bot.guilds:
        galaxy = guild.get_member(GALAXY_BOT_ID)
        if galaxy:
            try:
                await guild.ban(galaxy, reason="Galaxy Bot ist auf diesem Server nicht erlaubt", delete_message_days=0)
                log_ch = guild.get_channel(BOT_LOG_CHANNEL_ID)
                if log_ch:
                    embed = discord.Embed(
                        title="🔨 Galaxy Bot gebannt",
                        description="Galaxy Bot wurde beim Start automatisch vom Server gebannt.",
                        color=MOD_COLOR,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await log_ch.send(embed=embed)
            except Exception as e:
                await log_bot_error("Galaxy Bot Ban fehlgeschlagen", str(e), guild)

    try:
        guild_obj = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Slash Commands synced (Guild): {len(synced)}")
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("Globale Commands bereinigt")
    except Exception as e:
        print(f"Slash Command sync fehlgeschlagen: {e}")

    try:
        from help_embed import update_help_embed
        await update_help_embed()
    except Exception as e:
        print(f"[help_embed] Fehler beim Aktualisieren: {e}")



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

    if message.channel.id == COUNTING_CHANNEL_ID:
        await handle_counting(message)
        return

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


async def handle_counting(message):
    if message.id in counting_handled:
        return
    counting_handled.add(message.id)
    if len(counting_handled) > 200:
        oldest = list(counting_handled)[:100]
        for mid in oldest:
            counting_handled.discard(mid)

    content = message.content.strip()
    try:
        number = int(content)
    except ValueError:
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await message.channel.send(
                f"❌ {message.author.mention} Nur Zahlen sind hier erlaubt! Der Zähler geht weiter bei **{counting_state['count'] + 1}**.",
                delete_after=5
            )
        except Exception:
            pass
        return

    expected = counting_state["count"] + 1

    if counting_state["last_user_id"] == message.author.id:
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await message.channel.send(
                f"❌ {message.author.mention} Du kannst nicht zweimal hintereinander zählen! Der Zähler steht bei **{counting_state['count']}**.",
                delete_after=5
            )
        except Exception:
            pass
        return

    if number == expected:
        counting_state["count"] = number
        counting_state["last_user_id"] = message.author.id
        save_counting_state(counting_state)
        if number == 1000:
            await message.add_reaction("🏆")
            try:
                await message.channel.send(
                    f"🎉 **1000 erreicht!** Unglaublich! {message.author.mention} hat die **1000** geschafft!\n"
                    f"Der Zähler wird zurückgesetzt. Fangt wieder bei **1** an!"
                )
            except Exception:
                pass
            counting_state["count"] = 0
            counting_state["last_user_id"] = None
            save_counting_state(counting_state)
        else:
            await message.add_reaction("✅")
    else:
        counting_state["count"] = 0
        counting_state["last_user_id"] = None
        save_counting_state(counting_state)
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await message.channel.send(
                f"❌ {message.author.mention} Falsche Zahl! Erwartet wurde **{expected}**, nicht **{number}**.\n"
                f"Der Zähler wurde zurückgesetzt. Fangt wieder bei **1** an!",
                delete_after=8
            )
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

    goodbye_ch = guild.get_channel(GOODBYE_CHANNEL_ID)
    if goodbye_ch:
        try:
            g_embed = discord.Embed(
                title="📤 Mitglied hat den Server verlassen",
                description=(
                    f"**{member.mention}** hat uns verlassen.\n\n"
                    f"Wir wünschen dir alles Gute!\n"
                    f"Du bist jederzeit herzlich willkommen zurückzukehren."
                ),
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            g_embed.set_thumbnail(url=member.display_avatar.url)
            g_embed.add_field(name="Mitglied", value=str(member), inline=True)
            g_embed.add_field(name="ID",       value=str(member.id), inline=True)
            g_embed.set_footer(text=f"Noch {guild.member_count} Mitglieder")
            g_embed.set_image(url="https://a457f842-f550-4b03-850d-68292f4acbb5-00-1syh7hg70wqb4.picard.replit.dev/api/files/banner.png")
            await goodbye_ch.send(embed=g_embed)
        except Exception:
            pass


@bot.event
async def on_invite_create(invite):
    guild = invite.guild
    if guild.id not in invite_cache:
        invite_cache[guild.id] = {}
    invite_cache[guild.id][invite.code] = invite


@bot.event
async def on_invite_delete(invite):
    guild = invite.guild
    if guild.id in invite_cache and invite.code in invite_cache[guild.id]:
        del invite_cache[guild.id][invite.code]


@bot.event
async def on_member_join(member):
    guild = member.guild

    if member.bot:
        GALAXY_BOT_ID = 270904126974590976
        if member.id == GALAXY_BOT_ID:
            try:
                await guild.ban(member, reason="Galaxy Bot ist auf diesem Server nicht erlaubt", delete_message_days=0)
                log_ch = guild.get_channel(BOT_LOG_CHANNEL_ID)
                if log_ch:
                    embed = discord.Embed(
                        title="🔨 Galaxy Bot gebannt",
                        description="Galaxy Bot hat versucht dem Server beizutreten und wurde automatisch gebannt.",
                        color=MOD_COLOR,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await log_ch.send(embed=embed)
            except Exception:
                pass
            return
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
        if not inviter:
            for code, old_inv in old_invite_map.items():
                if code not in new_invite_map:
                    inviter      = old_inv.inviter
                    inviter_uses = (old_inv.uses or 0) + 1
                    break
        if not inviter:
            try:
                vanity = await guild.vanity_invite()
                if vanity and old_invite_map.get("vanity"):
                    old_vanity = old_invite_map["vanity"]
                    if vanity.uses > getattr(old_vanity, "uses", 0):
                        inviter_uses = vanity.uses
                new_invite_map["vanity"] = vanity
            except Exception:
                pass
        invite_cache[guild.id] = new_invite_map
    except Exception as e:
        await log_bot_error("Invite-Tracking fehlgeschlagen", str(e), guild)

    join_log_ch = guild.get_channel(JOIN_LOG_CHANNEL_ID)
    if join_log_ch:
        description = f"**Spieler:** {member.mention} (`{member}`)\n"
        if inviter:
            description += f"**Eingeladen von:** {inviter.mention} (`{inviter}`)\n"
            description += f"**Einladungen von {inviter.display_name}:** {inviter_uses} 🎟"
        elif inviter_uses > 0:
            description += "**Eingeladen von:** Vanity-URL (Server-Link)"
        else:
            description += "**Eingeladen von:** Unbekannt *(Bot fehlt 'Server verwalten' Berechtigung?)*"
        embed = discord.Embed(
            title="📥 Neues Mitglied",
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        ping_content = inviter.mention if inviter else None
        await join_log_ch.send(content=ping_content, embed=embed)

    ausweis_data = load_ausweis()
    hat_ausweis  = str(member.id) in ausweis_data

    if hat_ausweis:
        eintrag      = ausweis_data[str(member.id)]
        einreise_typ = eintrag.get("einreise_typ", "legal")
        wiederherstellen = []
        for rid in CHARAKTER_ROLLEN:
            r = guild.get_role(rid)
            if r:
                wiederherstellen.append(r)
        einreise_role_id = LEGAL_ROLE_ID if einreise_typ == "legal" else ILLEGAL_ROLE_ID
        einreise_role    = guild.get_role(einreise_role_id)
        if einreise_role:
            wiederherstellen.append(einreise_role)
        if wiederherstellen:
            try:
                await member.add_roles(*wiederherstellen, reason="Wiederbeitritt — Rollen wiederhergestellt")
            except Exception:
                pass
    else:
        rolle = guild.get_role(WHITELIST_ROLE_ID)
        if rolle:
            try:
                await member.add_roles(rolle, reason="Autorole — Bewerber")
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

    welcome_ch = guild.get_channel(WELCOME_CHANNEL_ID)
    if welcome_ch:
        try:
            w_embed = discord.Embed(
                title="📥 Willkommen auf dem Server!",
                description=(
                    f"Herzlich Willkommen {member.mention} auf **Kryptik Roleplay**!\n\n"
                    f"Wir freuen uns dich hier zu haben.\n"
                    f"Bitte wähle deine Einreiseart und erstelle deinen Ausweis."
                ),
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            w_embed.set_thumbnail(url=member.display_avatar.url)
            w_embed.add_field(name="Mitglied", value=str(member), inline=True)
            w_embed.add_field(name="ID", value=str(member.id), inline=True)
            w_embed.set_footer(text=f"Mitglied #{guild.member_count}")
            w_embed.set_image(url="https://a457f842-f550-4b03-850d-68292f4acbb5-00-1syh7hg70wqb4.picard.replit.dev/api/files/banner.png")
            await welcome_ch.send(embed=w_embed)
        except Exception:
            pass

    try:
        await member.edit(nick="RP Name | PSN")
    except Exception:
        pass

    eco       = load_economy()
    user_data = get_user(eco, member.id)
    if user_data["cash"] == 0 and user_data["bank"] == 0:
        user_data["cash"] = START_CASH
        save_economy(eco)
        await log_money_action(
            guild,
            "Startguthaben vergeben",
            f"**Spieler:** {member.mention}\n**Bargeld:** {START_CASH:,} 💵 (Willkommensbonus)"
    )
