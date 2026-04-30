# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# events.py \u2014 Discord Events (on_ready, on_message, Logs, etc.)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

import base64
from config import *
from helpers import is_admin, is_mod_or_admin, contains_vulgar, log_bot_error
import dashboard_hooks as _dh
from economy_helpers import (
    load_economy, save_economy, get_user, load_hidden_items,
    counting_state, save_counting_state, VersteckRetrieveView, log_money_action
)
from moderation import (
    handle_discord_invite, handle_link_outside_memes,
    handle_vulgar_message, check_spam
)
from ticket       import TicketSelectView, TicketActionView
from handy        import HandyView
from einreise     import EinreiseView, load_ausweis, save_ausweis
from shop         import ShopKwikChannelView, ShopBaumarktChannelView, ShopSchwarzmarktChannelView
from casino       import CasinoView
from dienst       import DienstUnifiedView
from team_overview import TeamOverviewView
from lotto        import LottoView, lotto_draw_loop
from embed_manager import setup_all_embeds
from logs import log_bot_restart
from rechnungen   import RechnungenPanelView
from economy_commands import LohnPanelView, KontoPanelView

try:
    from kokain import KokaInfoView as _KokaInfoView
except Exception:
    _KokaInfoView = None
try:
    from weed import WeedInfoView as _WeedInfoView
except Exception:
    _WeedInfoView = None
try:
    from angeln import (
        auto_angeln_setup as _auto_angeln_setup,
        AnglernInfoView as _AnglernInfoView,
        AnglershopView  as _AnglershopView,
    )
except Exception:
    _auto_angeln_setup = None
    _AnglernInfoView   = None
    _AnglershopView    = None



@bot.event
async def on_ready():
    global bot_start_time, invite_cache
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")

    bot.add_view(TicketSelectView())
    bot.add_view(TicketActionView())
    bot.add_view(HandyView())
    bot.add_view(EinreiseView())

    bot.add_view(ShopKwikChannelView())
    bot.add_view(ShopBaumarktChannelView())
    bot.add_view(ShopSchwarzmarktChannelView())
    bot.add_view(CasinoView())
    bot.add_view(TeamOverviewView())
    bot.add_view(LottoView())
    bot.add_view(DienstUnifiedView())
    bot.add_view(RechnungenPanelView())
    bot.add_view(LohnPanelView())
    bot.add_view(KontoPanelView())
    if _KokaInfoView:
        bot.add_view(_KokaInfoView())
    if _WeedInfoView:
        bot.add_view(_WeedInfoView())
    if _AnglernInfoView:
        bot.add_view(_AnglernInfoView())
    if _AnglershopView:
        bot.add_view(_AnglershopView())

    for entry in load_hidden_items():
        bot.add_view(VersteckRetrieveView(entry["id"], entry["owner_id"]))

    for guild in bot.guilds:
        try:
            if hasattr(guild, "fetch_invites"):
                invites = await guild.fetch_invites()
                invite_cache[guild.id] = {inv.code: inv for inv in invites}
                try:
                    vanity = await guild.vanity_invite()
                    if vanity:
                        invite_cache[guild.id]["vanity"] = vanity
                except Exception:
                    pass
        except Exception:
            pass

    # Dashboard: Mitglieder-Cache bef\u00fcllen
    for guild in bot.guilds:
        for m in guild.members:
            if not m.bot:
                _dh.update_member(m)
        inv_map = invite_cache.get(guild.id, {})
        _dh.update_invites({
            code: {
                "inviter_name": str(inv.inviter) if inv.inviter else "?",
                "inviter_id":   str(inv.inviter.id) if inv.inviter else None,
                "uses":         inv.uses,
            }
            for code, inv in inv_map.items() if hasattr(inv, 'inviter')
        })

    GALAXY_BOT_ID = 270904126974590976
    for guild in bot.guilds:
        galaxy = guild.get_member(GALAXY_BOT_ID)
        if galaxy:
            try:
                await guild.ban(galaxy, reason="Galaxy Bot ist auf diesem Server nicht erlaubt", delete_message_days=0)
                log_ch = guild.get_channel(BOT_LOG_CHANNEL_ID)
                if log_ch:
                    embed = discord.Embed(
                        title="\U0001F528 Galaxy Bot gebannt",
                        description="Galaxy Bot wurde beim Start automatisch vom Server gebannt.",
                        color=MOD_COLOR,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await log_ch.send(embed=embed)
            except Exception as e:
                await log_bot_error("Galaxy Bot Ban fehlgeschlagen", str(e), guild)

    app_id = bot.user.id
    invite = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={app_id}&permissions=8&scope=bot%20applications.commands"
    )
    print(f"Bot-ID / Invite-Link: {invite}")

    try:
        guild_obj = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Slash Commands synced (Guild): {len(synced)}")
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("Globale Commands bereinigt")
    except Exception as e:
        print(f"Slash Command sync fehlgeschlagen: {e}")

    await setup_all_embeds()
    bot.loop.create_task(lotto_draw_loop())

    try:
        _g = len(bot.guilds)
        _m = sum(g.member_count or 0 for g in bot.guilds)
        _t = int(bot_start_time.timestamp())
        _info = (
            "🤖 **Bot:** " + str(bot.user) + " (`" + str(bot.user.id) + "`)" + "\n"
            + "📡 **Server:** " + str(_g) + "\n"
            + "👥 **Mitglieder:** " + str(_m) + "\n"
            + f"⏰ **Gestartet um:** <t:{int(bot_start_time.timestamp())}:F>"
        )
        await log_bot_restart(_info)
    except Exception as _rle:
        print(f"[on_ready] log_bot_restart fehlgeschlagen: {_rle}")


@bot.event
async def on_error(event, *args, **kwargs):
    import traceback
    err = traceback.format_exc()
    try:
        await log_bot_error(f"Event: {event}", err)
    except Exception:
        traceback.print_exc()


@bot.event
async def on_command_error(ctx, error):
    import traceback
    from discord.ext import commands
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, (commands.MissingRole, commands.CheckFailure)):
        return
    err = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    try:
        await log_bot_error(f"Command: {ctx.command}", err, ctx.guild)
    except Exception:
        pass


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if bot_start_time and message.created_at < bot_start_time:
        return
    member = message.author

    # DMs haben kein Guild-Objekt \u2014 Server-Filter \u00FCberspringen
    if not message.guild:
        await bot.process_commands(message)
        return

    if message.channel.id == COUNTING_CHANNEL_ID:
        await handle_counting(message)
        return

    # Echtzeit-Log: jede Nachricht erfassen
    _preview = (message.content or '[kein Text]')[:120]
    _dh.log_activity(
        'NACHRICHT',
        f'#{message.channel.name} | {message.author}: {_preview}',
        message.author.id,
    )

    # Server-Inhaber hat volle Rechte \u2014 kein Mod-Filter
    if message.guild and member.id == message.guild.owner_id:
        await bot.process_commands(message)
        return

    _ist_inhaber = (
        member.id == OWNER_ID
        or member.id == message.guild.owner_id
        or any(r.id == INHABER_ROLE_ID for r in getattr(member, 'roles', []))
    )
    if not _ist_inhaber and DISCORD_INVITE_RE.search(message.content):
        await handle_discord_invite(message)
        return
    if not is_mod_or_admin(member) and message.channel.id != MEMES_CHANNEL_ID:
        if URL_RE.search(message.content):
            await handle_link_outside_memes(message)
            return
    _VULGAR_EXEMPT_ROLES = {1490855648978669599}
    _hat_vulgar_exempt = any(r.id in _VULGAR_EXEMPT_ROLES for r in getattr(member, 'roles', []))
    if not is_mod_or_admin(member) and not _hat_vulgar_exempt and contains_vulgar(message.content):
        await handle_vulgar_message(message)
        return

    # Mods und Admins sind vom Spamschutz ausgenommen
    if not is_mod_or_admin(member):
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
                f"\u274C {message.author.mention} Nur Zahlen sind hier erlaubt! Der Z\u00E4hler geht weiter bei **{counting_state['count'] + 1}**.",
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
                f"\u274C {message.author.mention} Du kannst nicht zweimal hintereinander z\u00E4hlen! Der Z\u00E4hler steht bei **{counting_state['count']}**.",
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
            await message.add_reaction("\U0001F3C6")
            try:
                await message.channel.send(
                    f"\U0001F389 **1000 erreicht!** Unglaublich! {message.author.mention} hat die **1000** geschafft!\n"
                    f"Der Z\u00E4hler wird zur\u00FCckgesetzt. Fangt wieder bei **1** an!"
                )
            except Exception:
                pass
            counting_state["count"] = 0
            counting_state["last_user_id"] = None
            save_counting_state(counting_state)
        else:
            await message.add_reaction("\u2705")
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
                f"\u274C {message.author.mention} Falsche Zahl! Erwartet wurde **{expected}**, nicht **{number}**.\n"
                f"Der Z\u00E4hler wurde zur\u00FCckgesetzt. Fangt wieder bei **1** an!",
                delete_after=8
            )
        except Exception:
            pass


@bot.event
async def on_message_delete(message):
    if not message.guild or message.author.bot:
        return
    _dh.log_activity(
        'GELÃ–SCHT',
        f'#{message.channel.name} | {message.author}: {(message.content or "[kein Text]")[:120]}',
        message.author.id,
    )
    # Embed-Log wird von logs_events.py übernommen (kein Duplikat)


@bot.event
async def on_message_edit(before, after):
    if not before.guild or before.author.bot:
        return
    if before.content == after.content:
        return
    _dh.log_activity(
        'BEARBEITET',
        f'#{before.channel.name} | {before.author}: {(before.content or "[]")[:80]} â†’ {(after.content or "[]")[:80]}',
        before.author.id,
    )
    # Embed-Log wird von logs_events.py übernommen (kein Duplikat)


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
    # Dashboard: Member-Cache + Rollen-Log
    _dh.update_member(after)
    # Warnung: Highteam-/Team-Rolle vergeben
    for _r in added:
        if _r.id in TEAM_ROLE_IDS:
            _dh.log_warning(
                '\u26a0\ufe0f Highteam-Rolle vergeben',
                f'{after} ({after.id}) hat die Rolle **{_r.name}** erhalten.',
            )
            _ht_embed = discord.Embed(
                title="\u26a0\ufe0f Aktivit\u00e4tswarnung \u2014 Highteam-Rolle vergeben",
                description=(
                    f"\U0001f464 **Benutzer:** {after.mention} (`{after}` | `{after.id}`)\n"
                    f"\U0001f3ad **Rolle:** {_r.mention} (`{_r.name}`)"
                ),
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc),
            )
            _ht_embed.set_footer(text="Paradise City Roleplay \u2022 Server-Schutz")
            await _warn_channel_send(guild, _ht_embed)
    _dh.log_activity("ROLLE",
        f"{after} â€” Rollen geÃ¤ndert: +[{', '.join(r.name for r in added)}] -[{', '.join(r.name for r in removed)}]",
        after.id)
    description = f"**Benutzer:** {after.mention} (`{after}`)\n"
    if added:
        description += f"**Hinzugef\u00FCgt:** {', '.join(r.mention for r in added)}\n"
    if removed:
        description += f"**Entfernt:** {', '.join(r.mention for r in removed)}\n"
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == after.id:
                description += f"**Ge\u00E4ndert von:** {entry.user.mention} (`{entry.user}`)"
                break
    except Exception:
        pass
    embed = discord.Embed(
        title="\U0001F3AD Rollen ge\u00E4ndert",
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
    _dh.log_activity(
        'BAN',
        f'{user} ({user.id}) gebannt â€” Grund: {reason}' + (f' | Von: {banner}' if banner else ''),
        user.id,
    )
    embed = discord.Embed(
        title="\U0001F528 Mitglied gebannt",
        description=description,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)


@bot.event
async def on_member_remove(member):
    guild  = member.guild
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
    _dh.log_activity(
        'KICK' if action == 'gekickt' else 'VERLASSEN',
        f'{member} ({member.id}) {action}' + (f' | Von: {mod}' if mod else ''),
        member.id,
    )
    # Embed-Log wird von logs_events.py übernommen (kein Duplikat)

    goodbye_ch = guild.get_channel(GOODBYE_CHANNEL_ID)
    if goodbye_ch:
        try:
            g_embed = discord.Embed(
                title="\U0001F4E4 Auf Wiedersehen!",
                description=(
                    f"**{member.display_name}** hat **Paradise City Roleplay** verlassen.\n\n"
                    f"Wir w\u00FCnschen dir alles Gute \u2014 du bist jederzeit willkommen zur\u00FCckzukehren! \U0001F44B"
                ),
                color=0xE67E22,
                timestamp=datetime.now(timezone.utc)
            )
            g_embed.set_thumbnail(url=member.display_avatar.url)
            g_embed.add_field(name="\U0001F464 Mitglied", value=str(member), inline=True)
            g_embed.add_field(name="\U0001F194 ID",       value=str(member.id), inline=True)
            g_embed.set_footer(text=f"Paradise City Roleplay \u2022 Noch {guild.member_count} Mitglieder")
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
        # Wer hat den Bot hinzugef\u00FCgt? (Audit-Log)
        adder = None
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    adder = entry.user
                    break
        except Exception:
            pass

        # Nur der Inhaber (Rolle oder OWNER_ID) darf Bots hinzuf\u00FCgen
        if adder:
            if adder.id == OWNER_ID or adder.id == guild.owner_id:
                return
            adder_member = guild.get_member(adder.id)
            if adder_member and any(r.id == INHABER_ROLE_ID for r in adder_member.roles):
                return

        # Jeder andere Bot wird sofort gebannt
        try:
            await guild.ban(member, reason="\U0001F6AB Nicht autorisierter Bot \u2014 automatisch gebannt", delete_message_days=0)
        except Exception:
            pass

        # DM an den T\u00E4ter (falls bekannt)
        if adder:
            try:
                embed = discord.Embed(
                    title="\u26A0\uFE0F Nicht erlaubt",
                    description=(
                        f"Du hast versucht den Bot **{member}** auf den Server hinzuzuf\u00FCgen.\n"
                        "Das ist auf diesem Server **nicht erlaubt** \u2014 nur der Inhaber darf Bots hinzuf\u00FCgen.\n"
                        f"Der Bot wurde automatisch **gebannt**."
                    ),
                    color=0xFF0000,
                )
                await adder.send(embed=embed)
            except Exception:
                pass

        # DM-Warnung an den Inhaber
        warn_embed = discord.Embed(
            title="\u26A0\uFE0F Bot-Einladung erkannt",
            description=(
                f"\U0001F916 **Bot:** `{member}` (`{member.id}`)\n"
                f"\U0001F464 **Hinzugef\u00FCgt von:** {adder.mention + ' (`' + str(adder.id) + '`)' if adder else 'Unbekannt'}\n"
                f"\U0001F552 **Zeitpunkt:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>\n\n"
                "\U0001F6AB Der Bot wurde automatisch **gebannt**."
            ),
            color=0xFF0000,
            timestamp=datetime.now(timezone.utc),
        )
        await _dm_inhaber(guild, warn_embed)
        return

    # Dashboard: Mitglied-Cache aktualisieren
    _dh.update_member(member)
    _dh.log_activity("MITGLIED", f"{member} ({member.id}) ist dem Server beigetreten", member.id)

    # Embed-Log wird von logs_events.py übernommen (kein Duplikat)

    inviter      = None
    inviter_uses = 0
    via_vanity   = False
    try:
        if not hasattr(guild, "fetch_invites"):
            raise AttributeError("fetch_invites nicht verf\u00FCgbar \u2014 Invites-Intent pr\u00FCfen")
        new_invites    = await guild.fetch_invites()
        new_invite_map = {inv.code: inv for inv in new_invites}
        old_invite_map = invite_cache.get(guild.id, {})

        # Falls Cache leer war (z.B. nach Neustart): Cache bef\u00FCllen, Zuordnung nicht m\u00F6glich
        if old_invite_map:
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

        # Vanity-URL pr\u00FCfen
        if not inviter:
            try:
                vanity = await guild.vanity_invite()
                if vanity:
                    old_vanity_uses = getattr(old_invite_map.get("vanity"), "uses", 0) or 0
                    if vanity.uses > old_vanity_uses:
                        via_vanity   = True
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
            description += f"**Gesamte Einladungen von {inviter.display_name}:** {inviter_uses} \U0001F39F"
        elif via_vanity:
            description += "**Eingeladen von:** Vanity-URL (Server-Link)"
        else:
            description += "**Eingeladen von:** Unbekannt"
        embed = discord.Embed(
            title="\U0001F4E5 Neues Mitglied",
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        ping_content = inviter.mention if inviter else None
        await join_log_ch.send(content=ping_content, embed=embed)

    try:
        ausweis_data = load_ausweis()
        hat_ausweis  = str(member.id) in ausweis_data
    except Exception:
        ausweis_data = {}
        hat_ausweis  = False

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
                await member.add_roles(*wiederherstellen, reason="Wiederbeitritt \u2014 Rollen wiederhergestellt")
            except Exception:
                pass
    else:
        rolle = guild.get_role(WHITELIST_ROLE_ID)
        if rolle:
            try:
                await member.add_roles(rolle, reason="Autorole \u2014 Bewerber")
            except Exception:
                pass

    try:
        embed = discord.Embed(
            title="\U0001F44B Willkommen auf Paradise City Roleplay!",
            description=(
                "> Willkommen auf **Paradise City Roleplay** \u2014 deinem PS4 GTA RP Server mit Ultimativem Spa\u00DF und Hochwertigem RP!\n\n"
                "> Wir freuen uns dich bei uns zu haben und w\u00FCnschen dir viel Spa\u00DF auf unserem Server.\n\n"
                "> Solltest du Hilfe ben\u00F6tigen, melde dich jederzeit \u00FCber ein Support-Ticket in "
                f"<#{TICKET_CHANNEL_ID}>."
            ),
            color=0xE67E22
        )
        embed.set_footer(text="Paradise City Roleplay \u2022 Willkommen!")
        await member.send(content=member.mention, embed=embed)
    except Exception:
        pass

    welcome_ch = guild.get_channel(WELCOME_CHANNEL_ID)
    if welcome_ch:
        try:
            w_embed = discord.Embed(
                title="\U0001F44B Willkommen auf Paradise City Roleplay!",
                description=(
                    f"Hey {member.mention}, herzlich willkommen auf **Paradise City Roleplay**!\n\n"
                    f"W\u00E4hle deine Einreiseart und erstelle deinen Ausweis um loszulegen."
                ),
                color=0xE67E22,
                timestamp=datetime.now(timezone.utc)
            )
            w_embed.set_thumbnail(url=member.display_avatar.url)
            w_embed.add_field(name="\U0001F464 Mitglied", value=str(member), inline=True)
            w_embed.add_field(name="\U0001F194 ID", value=str(member.id), inline=True)
            w_embed.set_footer(text=f"Paradise City Roleplay \u2022 Mitglied #{guild.member_count}")
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
        user_data["bank"] = START_CASH
        save_economy(eco)
        await log_money_action(
            guild,
            "Startguthaben vergeben",
            f"**Spieler:** {member.mention}\n**Bank:** {START_CASH:,} \U0001F4B5 (Willkommensbonus)"
    )


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# SERVER-SCHUTZ \u2014 Anti-Create / Anti-Delete / Anti-Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

# IDs die der Bot selbst gel\u00F6scht hat \u2014 verhindert doppelte Inhaber-Warnung
_NANANA_GIF_B64 = (
    "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"
)

_bot_deleted_ids: set = set()


async def _warn_channel_send(guild: discord.Guild, embed: discord.Embed):
    """\u0041ktivit\u00e4tswarnung auch in den dedizierten Warn-Kanal schicken."""
    try:
        ch = guild.get_channel(AKTIVITAET_WARN_CHANNEL_ID)
        if ch:
            await ch.send(embed=embed)
    except Exception:
        pass


async def _dm_inhaber(guild: discord.Guild, embed: discord.Embed):
    """DM an alle Mitglieder mit Inhaber-Rolle."""
    # Dashboard: Aktivit\u00e4tswarnung aufzeichnen
    try:
        _dh.log_warning(
            embed.title or "Warnung",
            embed.description or "",
        )
    except Exception:
        pass
    # Zus\u00e4tzlich in den Aktivit\u00e4tswarnung-Kanal posten
    await _warn_channel_send(guild, embed)
    inhaber_role = guild.get_role(INHABER_ROLE_ID)
    if not inhaber_role:
        return
    for member in inhaber_role.members:
        try:
            await member.send(embed=embed)
        except Exception:
            pass


async def _get_audit_user(guild: discord.Guild, action: discord.AuditLogAction, target_id: int):
    """Letzten Audit-Log-Eintrag f\u00FCr Ziel-ID suchen."""
    try:
        async for entry in guild.audit_logs(limit=10, action=action):
            if entry.target.id == target_id:
                return entry.user
    except Exception:
        pass
    return None


@bot.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel):
    if channel.guild.id != GUILD_ID:
        return
    creator = await _get_audit_user(channel.guild, discord.AuditLogAction.channel_create, channel.id)
    if creator and creator.id == bot.user.id:
        return
    if creator and (creator.id == OWNER_ID or creator.id == channel.guild.owner_id):
        return
    if creator and any(r.id == INHABER_ROLE_ID for r in getattr(creator, 'roles', [])):
        return
    _bot_deleted_ids.add(channel.id)
    try:
        await channel.delete(reason="\U0001F6AB Server-Schutz: Kanal-Erstellung nicht erlaubt")
    except Exception:
        _bot_deleted_ids.discard(channel.id)
        return
    if creator:
        try:
            gif  = discord.File(io.BytesIO(base64.b64decode(_NANANA_GIF_B64)), filename="nanana.gif")
            embed = discord.Embed(
                title="NaNaNa",
                description=f"Der Kanal **{channel.name}** wurde sofort wieder gel\u00F6scht.",
                color=0xE74C3C,
            )
            embed.set_image(url="attachment://nanana.gif")
            embed.set_footer(text="Sowas macht nur mein Entwickler \U0001F60E")
            await creator.send(file=gif, embed=embed)
        except Exception:
            pass


@bot.event
async def on_guild_role_create(role: discord.Role):
    if role.guild.id != GUILD_ID:
        return
    creator = await _get_audit_user(role.guild, discord.AuditLogAction.role_create, role.id)
    if creator and creator.id == bot.user.id:
        return
    if creator and (creator.id == OWNER_ID or creator.id == role.guild.owner_id):
        return
    if creator and any(r.id == INHABER_ROLE_ID for r in getattr(creator, 'roles', [])):
        return
    _bot_deleted_ids.add(role.id)
    try:
        await role.delete(reason="\U0001F6AB Server-Schutz: Rollen-Erstellung nicht erlaubt")
    except Exception:
        _bot_deleted_ids.discard(role.id)
        return
    if creator:
        try:
            embed = discord.Embed(
                description=(
                    "**NaNaNa \U0001F60E**\n"
                    "Sowas macht nur mein Entwickler!\n\n"
                    f"Die Rolle **{role.name}** wurde sofort wieder gel\u00F6scht."
                ),
                color=0xE74C3C,
            )
            await creator.send(embed=embed)
        except Exception:
            pass


async def _strip_alle_rollen(guild: discord.Guild, member: discord.Member, grund: str):
    """Entfernt alle Rollen eines Mitglieds sofort und benachrichtigt den Inhaber."""
    if member is None or member.bot:
        return
    rollen_vorher = [r for r in member.roles if r != guild.default_role]
    try:
        await member.edit(roles=[], reason=f"\U0001F6AB Server-Schutz: {grund}")
    except Exception:
        return
    warn_embed = discord.Embed(
        title="\U0001F6A8 Sanktion \u2014 Alle Rollen entzogen",
        description=(
            f"\U0001F464 **Mitglied:** {member.mention} (`{member}` | `{member.id}`)\n"
            f"\U0001F4CB **Grund:** {grund}\n"
            f"\U0001F4E6 **Entzogene Rollen:** {', '.join(r.name for r in rollen_vorher) or '\u2014'}\n"
            f"\U0001F552 **Zeitpunkt:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>"
        ),
        color=0xFF0000,
        timestamp=datetime.now(timezone.utc),
    )
    await _dm_inhaber(guild, warn_embed)
    try:
        dm_embed = discord.Embed(
            title="\u26A0\uFE0F Sanktion",
            description=(
                f"Deine Aktion **\u201E{grund}\u201C** auf dem Server "
                f"**{guild.name}** ist nicht erlaubt.\n"
                "Dir wurden sofort **alle Rollen entzogen**."
            ),
            color=0xFF0000,
        )
        await member.send(embed=dm_embed)
    except Exception:
        pass


@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
    if channel.guild.id != GUILD_ID:
        return
    if channel.id in _bot_deleted_ids:
        _bot_deleted_ids.discard(channel.id)
        return
    deleter = await _get_audit_user(channel.guild, discord.AuditLogAction.channel_delete, channel.id)
    if deleter:
        if deleter.id == bot.user.id:
            return
        if deleter.id == OWNER_ID or deleter.id == channel.guild.owner_id:
            return
        deleter_member = channel.guild.get_member(deleter.id)
        if deleter_member and any(r.id == INHABER_ROLE_ID for r in deleter_member.roles):
            return
        await _strip_alle_rollen(
            channel.guild,
            deleter_member or channel.guild.get_member(deleter.id),
            f"Kanal #{channel.name} gel\u00F6scht"
        )
    else:
        embed = discord.Embed(
            title="\u26A0\uFE0F Kanal gel\u00F6scht \u2014 T\u00E4ter unbekannt",
            description=(
                f"\U0001F4E2 Der Kanal **#{channel.name}** wurde gel\u00F6scht.\n"
                f"\U0001F464 **Von:** Unbekannt\n"
                f"\U0001F552 **Zeitpunkt:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>"
            ),
            color=0xFF0000,
            timestamp=datetime.now(timezone.utc),
        )
        await _dm_inhaber(channel.guild, embed)


@bot.event
async def on_guild_role_delete(role: discord.Role):
    if role.guild.id != GUILD_ID:
        return
    if role.id in _bot_deleted_ids:
        _bot_deleted_ids.discard(role.id)
        return
    deleter = await _get_audit_user(role.guild, discord.AuditLogAction.role_delete, role.id)
    if deleter:
        if deleter.id == bot.user.id:
            return
        if deleter.id == OWNER_ID or deleter.id == role.guild.owner_id:
            return
        deleter_member = role.guild.get_member(deleter.id)
        if deleter_member and any(r.id == INHABER_ROLE_ID for r in deleter_member.roles):
            return
        await _strip_alle_rollen(
            role.guild,
            deleter_member or role.guild.get_member(deleter.id),
            f"Rolle \u201E{role.name}\u201C gel\u00F6scht"
        )
    else:
        embed = discord.Embed(
            title="\u26A0\uFE0F Rolle gel\u00F6scht \u2014 T\u00E4ter unbekannt",
            description=(
                f"\U0001F4E2 Die Rolle **{role.name}** wurde gel\u00F6scht.\n"
                f"\U0001F464 **Von:** Unbekannt\n"
                f"\U0001F552 **Zeitpunkt:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>"
            ),
            color=0xFF0000,
            timestamp=datetime.now(timezone.utc),
        )
        await _dm_inhaber(role.guild, embed)
