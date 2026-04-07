# ── Events ──────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    global bot_start_time, invite_cache
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")
    bot.add_view(TicketSelectView())
    bot.add_view(TicketActionView())
    for guild in bot.guilds:
        try:
            invites = await guild.fetch_invites()
            invite_cache[guild.id] = {inv.code: inv for inv in invites}
        except Exception:
            pass
    await auto_ticket_setup()
    await send_bot_status()


async def auto_ticket_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(TICKET_SETUP_CHANNEL_ID)
        if not channel:
            continue
        already_posted = False
        try:
            async for msg in channel.history(limit=50):
                if msg.author == guild.me and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Ticket erstellen" in emb.title:
                            already_posted = True
                            break
                if already_posted:
                    break
        except Exception:
            pass
        if already_posted:
            print(f"Ticket-Embed bereits vorhanden in #{channel.name} — kein erneutes Posten.")
            continue
        embed = discord.Embed(
            title="🎟 Support — Ticket erstellen",
            description=(
                "Benötigst du Hilfe oder möchtest ein Anliegen melden?\n\n"
                "Wähle unten im Menü die passende Ticket-Art aus.\n"
                "Unser Team wird sich schnellstmöglich um dich kümmern.\n\n"
                "**Verfügbare Ticket-Arten:**\n"
                "🎟 **Support** — Allgemeiner Support\n"
                "🎟 **Highteam Ticket** — Direkter Kontakt zum Highteam\n"
                "🎟 **Fraktions Bewerbung** — Bewirb dich für eine Fraktion\n"
                "🎟 **Beschwerde Ticket** — Beschwerde einreichen\n"
                "🎟 **Bug Report** — Fehler oder Bug melden"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Cryptik Roleplay — Support System")
        try:
            await channel.send(embed=embed, view=TicketSelectView())
            print(f"Ticket-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_ticket_setup fehlgeschlagen", str(e), guild)


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
    timeout_ok, roles_removed = await apply_timeout_restrictions(member, guild, duration_h=300, reason="Fremden Discord-Link gesendet")
    try:
        await member.send(content=member.mention, embed=discord.Embed(
            description="> Du hast gegen unsere Server Regeln verstoßen\n\n> Bitte wende dich an den Support",
            color=MOD_COLOR
        ))
    except Exception:
        pass
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        timeout_status = "✅ Timeout erteilt (300h)" if timeout_ok else "❌ Timeout fehlgeschlagen — Berechtigung prüfen!"
        rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
        await log_ch.send(embed=discord.Embed(
            title="🔨 Moderation — Timeout",
            description=(
                f"**Benutzer:** {member.mention} (`{member}`)\n**Timeout:** {timeout_status}\n"
                f"**Rollen:** {rollen_status}\n**Grund:** Fremden Discord-Link gesendet\n"
                f"**Kanal:** {message.channel.mention}\n**Nachricht:** {message.content[:300]}"
            ),
            color=MOD_COLOR, timestamp=datetime.now(timezone.utc)
        ))


async def handle_link_outside_memes(message):
    try:
        await message.delete()
    except Exception:
        pass
    try:
        await message.channel.send(f"{message.author.mention} Bitte sende Links ausschließlich im <#{MEMES_CHANNEL_ID}> Kanal", delete_after=6)
    except Exception:
        pass


async def handle_vulgar_message(message):
    try:
        await message.delete()
    except Exception:
        pass
    try:
        await message.author.send(content=message.author.mention, embed=discord.Embed(
            description="> **Verwarnung:** Du hast einen vulgären Ausdruck verwendet.\n\n> Bitte beachte unsere Serverregeln. Bei weiteren Verstößen folgen Konsequenzen.",
            color=MOD_COLOR
        ))
    except Exception:
        pass
    log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        await log_ch.send(embed=discord.Embed(
            title="🔨 Moderation — Vulgäre Sprache",
            description=f"**Benutzer:** {message.author.mention} (`{message.author}`)\n**Kanal:** {message.channel.mention}\n**Nachricht:** {message.content[:300]}",
            color=MOD_COLOR, timestamp=datetime.now(timezone.utc)
        ))


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
        timeout_ok, roles_removed = await apply_timeout_restrictions(message.author, message.guild, duration_m=10, reason="Wiederholtes Spammen")
        try:
            await message.author.send(content=message.author.mention, embed=discord.Embed(
                description="> Du wurdest aufgrund von wiederholtem Spammen für **10 Minuten** stummgeschaltet.",
                color=MOD_COLOR
            ))
        except Exception:
            pass
        log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            timeout_status = "✅ Timeout erteilt (10min)" if timeout_ok else "❌ Timeout fehlgeschlagen — Berechtigung prüfen!"
            rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
            await log_ch.send(embed=discord.Embed(
                title="🔨 Moderation — Timeout (Spam)",
                description=f"**Benutzer:** {message.author.mention} (`{message.author}`)\n**Timeout:** {timeout_status}\n**Rollen:** {rollen_status}\n**Grund:** Wiederholtes Spammen",
                color=MOD_COLOR, timestamp=datetime.now(timezone.utc)
            ))
    elif count >= 5 and user_id not in spam_warned:
        spam_tracker[user_id] = []
        spam_warned.add(user_id)
        try:
            await message.channel.purge(limit=50, check=lambda m: m.author.id == user_id)
        except Exception:
            pass
        try:
            await message.author.send(content=message.author.mention, embed=discord.Embed(
                description="> **Verwarnung:** Bitte vermeide es zu spammen.\n\n> Bei Wiederholung erhältst du einen 10 Minuten Timeout.",
                color=MOD_COLOR
            ))
        except Exception:
            pass


@bot.event
async def on_message_delete(message):
    if not message.guild or message.author.bot:
        return
    log_ch = message.guild.get_channel(MESSAGE_LOG_CHANNEL_ID)
    if not log_ch:
        return
    await log_ch.send(embed=discord.Embed(
        title="🗑️ Nachricht gelöscht",
        description=f"**Benutzer:** {message.author.mention} (`{message.author}`)\n**Kanal:** {message.channel.mention}\n**Inhalt:** {message.content[:500] if message.content else '*Kein Text*'}",
        color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
    ))


@bot.event
async def on_message_edit(before, after):
    if not before.guild or before.author.bot:
        return
    if before.content == after.content:
        return
    log_ch = before.guild.get_channel(MESSAGE_LOG_CHANNEL_ID)
    if not log_ch:
        return
    await log_ch.send(embed=discord.Embed(
        title="✏️ Nachricht bearbeitet",
        description=(
            f"**Benutzer:** {before.author.mention} (`{before.author}`)\n**Kanal:** {before.channel.mention}\n"
            f"**Vorher:** {before.content[:250] if before.content else '*Kein Text*'}\n"
            f"**Nachher:** {after.content[:250] if after.content else '*Kein Text*'}"
        ),
        color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
    ))


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
    await log_ch.send(embed=discord.Embed(title="🎭 Rollen geändert", description=description, color=LOG_COLOR, timestamp=datetime.now(timezone.utc)))


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
    await log_ch.send(embed=discord.Embed(title="🔨 Mitglied gebannt", description=description, color=LOG_COLOR, timestamp=datetime.now(timezone.utc)))


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
    await log_ch.send(embed=discord.Embed(title=title, description=description, color=LOG_COLOR, timestamp=datetime.now(timezone.utc)))


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
        try:
            await member.kick(reason="Bots sind auf diesem Server nicht erlaubt")
        except Exception:
            pass
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    try:
                        await entry.user.send(content=entry.user.mention, embed=discord.Embed(
                            description="> Bots auf diesen Server hinzufügen ist für dich leider nicht erlaubt.",
                            color=MOD_COLOR
                        ))
                    except Exception:
                        pass
                    break
        except Exception:
            pass
        return

    member_log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if member_log_ch:
        await member_log_ch.send(embed=discord.Embed(
            title="✅ Mitglied beigetreten",
            description=f"**Benutzer:** {member.mention} (`{member}`)",
            color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
        ))

    inviter = None
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
                    if vanity.uses > getattr(old_invite_map["vanity"], "uses", 0):
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
            description += f"**Eingeladen von:** {inviter.mention} (`{inviter}`)\n**Invites von {inviter.display_name}:** {inviter_uses}"
        elif inviter_uses > 0:
            description += "**Eingeladen von:** Vanity-URL (Server-Link)"
        else:
            description += "**Eingeladen von:** Unbekannt *(Bot fehlt 'Server verwalten' Berechtigung?)*"
        await join_log_ch.send(embed=discord.Embed(title="📥 Neues Mitglied", description=description, color=LOG_COLOR, timestamp=datetime.now(timezone.utc)))

    rolle = guild.get_role(WHITELIST_ROLE_ID)
    if rolle:
        try:
            await member.add_roles(rolle)
        except Exception:
            pass

    try:
        await member.send(content=member.mention, embed=discord.Embed(
            description=(
                "> Willkommen auf Kryptik Roleplay deinem RP server mit Ultimativem Spaß und Hochwertigem RP\n\n"
                "> Wir wünschen dir viel Spaß auf unserem Server und hoffen das du dich bei uns Gut Zurecht findest\n\n"
                f"> Solltest du mal Schwierigkeiten haben melde dich gerne Jederzeit über ein Support Ticket im channel "
                f"[#ticket-erstellen](https://discord.com/channels/{GUILD_ID}/{TICKET_CHANNEL_ID})"
            ),
            color=LOG_COLOR
        ))
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


@bot.command(name="ticketsetup")
async def ticketsetup(ctx):
    if not is_admin(ctx.author):
        return
    channel = ctx.guild.get_channel(TICKET_SETUP_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Ticket-Kanal nicht gefunden!")
        return
    embed = discord.Embed(
        title="🎟 Support — Ticket erstellen",
        description=(
            "Benötigst du Hilfe oder möchtest ein Anliegen melden?\n\n"
            "Wähle unten im Menü die passende Ticket-Art aus.\n"
            "Unser Team wird sich schnellstmöglich um dich kümmern.\n\n"
            "**Verfügbare Ticket-Arten:**\n"
            "🎟 **Support** — Allgemeiner Support\n"
            "🎟 **Highteam Ticket** — Direkter Kontakt zum Highteam\n"
            "🎟 **Fraktions Bewerbung** — Bewirb dich für eine Fraktion\n"
            "🎟 **Beschwerde Ticket** — Beschwerde einreichen\n"
            "🎟 **Bug Report** — Fehler oder Bug melden"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Cryptik Roleplay — Support System")
    await channel.send(embed=embed, view=TicketSelectView())
    try:
        await ctx.message.delete()
    except Exception:
        pass


token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
