# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# ticket.py — Ticket System (Support, Highteam, Fraktion, etc.)
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import is_mod_or_admin, log_bot_error


TICKET_TYPE_NAMES = {
    "support":    "Support",
    "highteam":   "Highteam Ticket",
    "fraktion":   "Fraktions Bewerbung",
    "beschwerde": "Beschwerde Ticket",
    "bug":        "Bug Report",
    "crew":       "Crew Anfrage",
}

TICKET_TYPE_CATEGORIES = {
    "support":    TICKET_CATEGORY_DEFAULT,
    "highteam":   TICKET_CATEGORY_HIGHTEAM,
    "fraktion":   TICKET_CATEGORY_FRAKTION,
    "beschwerde": TICKET_CATEGORY_DEFAULT,
    "bug":        TICKET_CATEGORY_DEFAULT,
    "crew":       TICKET_CATEGORY_FRAKTION,
}


async def create_ticket(interaction: discord.Interaction, ticket_type: str):
    guild  = interaction.guild
    member = interaction.user

    for ch in guild.text_channels:
        data = ticket_data.get(ch.id)
        if data and data["creator_id"] == member.id:
            await interaction.response.send_message(
                "❌ Du hast bereits ein offenes Ticket!", ephemeral=True
            )
            return

    type_name   = TICKET_TYPE_NAMES.get(ticket_type, ticket_type)
    category_id = TICKET_TYPE_CATEGORIES.get(ticket_type, TICKET_CATEGORY_DEFAULT)
    category    = guild.get_channel(category_id)
    admin_role  = guild.get_role(ADMIN_ROLE_ID)
    mod_role    = guild.get_role(MOD_ROLE_ID)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            manage_channels=True, manage_messages=True
        ),
    }
    if admin_role:
        overwrites[admin_role] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            manage_channels=True, manage_messages=True
        )
    if mod_role:
        overwrites[mod_role] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            manage_channels=True, manage_messages=True
        )

    safe_name    = member.name[:15].lower().replace(" ", "-")
    channel_name = f"ticket-{ticket_type}-{safe_name}"

    try:
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket von {member} ({member.id}) | Typ: {type_name}"
        )
    except Exception as e:
        await interaction.response.send_message(
            "❌ Ticket konnte nicht erstellt werden.", ephemeral=True
        )
        await log_bot_error("Ticket erstellen fehlgeschlagen", str(e), guild)
        return

    ticket_data[channel.id] = {
        "creator_id":   member.id,
        "creator_name": str(member),
        "type":         ticket_type,
        "type_name":    type_name,
        "handler":      None,
        "handler_id":   None,
        "opened_at":    datetime.now(timezone.utc).isoformat(),
    }

    team_mentions = ""
    if admin_role:
        team_mentions += admin_role.mention + " "
    if mod_role:
        team_mentions += mod_role.mention

    welcome_embed = discord.Embed(
        title=f"🎟 {type_name}",
        description=(
            f"Willkommen {member.mention}!\n\n"
            f"Dein Ticket wurde erfolgreich erstellt. Das Team wird sich schnellstmöglich um dein Anliegen kümmern.\n\n"
            f"**Ticket-Typ:** {type_name}\n"
            f"**Erstellt von:** {member.mention}\n"
            f"**Erstellt am:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    welcome_embed.set_footer(text="Nur Teammitglieder können das Ticket schließen")

    action_view = TicketActionView()
    await channel.send(content=team_mentions, embed=welcome_embed, view=action_view)

    # ── Crew Anfrage: Vorlage automatisch ins Ticket senden ───
    if ticket_type == "crew":
        crew_embed = discord.Embed(
            title="📋 Crew Anfrage — Vorlage",
            description=(
                "Bitte gib Folgendes an:\n\n"
                "**PSN Name:**\n\n"
                "**Social Club Name:**"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        crew_embed.set_footer(text="Bitte fülle alle Felder aus, damit wir deine Anfrage bearbeiten können.")
        await channel.send(embed=crew_embed)

    await interaction.response.send_message(
        f"✅ Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True
    )

    log_ch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="📂 Ticket Geöffnet",
            description=(
                f"**Benutzer:** {member.mention} (`{member}`)\n"
                f"**Typ:** {type_name}\n"
                f"**Channel:** {channel.mention}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await log_ch.send(embed=log_embed)


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support",            emoji="🎟", value="support",    description="Allgemeiner Support"),
            discord.SelectOption(label="Highteam Ticket",    emoji="🎟", value="highteam",   description="Direkter Kontakt zum Highteam"),
            discord.SelectOption(label="Fraktions Bewerbung",emoji="🎟", value="fraktion",   description="Bewerbung für eine Fraktion"),
            discord.SelectOption(label="Beschwerde Ticket",  emoji="🎟", value="beschwerde", description="Beschwerde einreichen"),
            discord.SelectOption(label="Bug Report",          emoji="🎟", value="bug",        description="Fehler oder Bug melden"),
            discord.SelectOption(label="Crew Anfrage",        emoji="🎮", value="crew",       description="Crew-Anfrage über Rockstar Social Club"),
        ]
        super().__init__(
            placeholder="🎟 Wähle eine Ticket-Art aus...",
            options=options,
            custom_id="ticket_select_main"
        )

    async def callback(self, interaction: discord.Interaction):
        await create_ticket(interaction, self.values[0])


class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class AssignUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(
            placeholder="Person auswählen...",
            custom_id="ticket_assign_user_select",
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        user    = self.values[0]
        channel = interaction.channel
        try:
            await channel.set_permissions(
                user,
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        except Exception as e:
            await interaction.response.send_message(
                "❌ Berechtigung konnte nicht gesetzt werden.", ephemeral=True
            )
            await log_bot_error("Ticket-Zuweisung fehlgeschlagen", str(e), interaction.guild)
            return

        if channel.id in ticket_data:
            ticket_data[channel.id]["handler"]    = str(user)
            ticket_data[channel.id]["handler_id"] = user.id

        assign_embed = discord.Embed(
            description=(
                f"👤 {user.mention} wurde dem Ticket zugewiesen.\n"
                f"**Zugewiesen von:** {interaction.user.mention}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await channel.send(embed=assign_embed)
        await interaction.response.send_message(
            f"✅ {user.mention} wurde dem Ticket zugewiesen.", ephemeral=True
        )


class AssignView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(AssignUserSelect())


class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ticket schließen",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="ticket_close_btn"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Nur Teammitglieder können Tickets schließen.", ephemeral=True
            )
            return

        channel = interaction.channel
        data    = ticket_data.get(channel.id)
        if not data:
            await interaction.response.send_message(
                "❌ Ticket-Daten nicht gefunden.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        ticket_data[channel.id]["handler"]    = str(interaction.user)
        ticket_data[channel.id]["handler_id"] = interaction.user.id

        closing_embed = discord.Embed(
            title="🔒 Ticket wird geschlossen...",
            description="Das Ticket wird in wenigen Sekunden geschlossen.",
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await channel.send(embed=closing_embed)

        transcript_lines = [
            f"=== Ticket Transkript: {data['type_name']} ===",
            f"Erstellt von  : {data['creator_name']}",
            f"Bearbeitet von: {str(interaction.user)}",
            f"Datum         : {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')} UTC",
            "=" * 55,
            ""
        ]
        try:
            async for msg in channel.history(limit=500, oldest_first=True):
                if msg.author == interaction.guild.me:
                    continue
                ts = msg.created_at.strftime("%d.%m.%Y %H:%M")
                if msg.content:
                    transcript_lines.append(f"[{ts}] {msg.author}: {msg.content}")
                for emb in msg.embeds:
                    if emb.title:
                        transcript_lines.append(f"[{ts}] {msg.author} [Embed-Titel]: {emb.title}")
                    if emb.description:
                        short = emb.description[:300].replace("\n", " ")
                        transcript_lines.append(f"  ↳ {short}")
        except Exception:
            transcript_lines.append("(Transkript konnte nicht vollständig geladen werden)")

        transcript_text = "\n".join(transcript_lines)
        transcript_file = discord.File(
            fp=io.BytesIO(transcript_text.encode("utf-8")),
            filename=f"transkript-{channel.name}.txt"
        )

        log_ch = interaction.guild.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            closed_embed = discord.Embed(
                title="📁 Ticket Geschlossen",
                description=(
                    f"**Benutzer:** <@{data['creator_id']}> (`{data['creator_name']}`)\n"
                    f"**Typ:** {data['type_name']}\n"
                    f"**Geschlossen von:** {interaction.user.mention} (`{interaction.user}`)\n"
                    f"**Channel:** #{channel.name}"
                ),
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            await log_ch.send(embed=closed_embed, file=transcript_file)

        creator = interaction.guild.get_member(data["creator_id"])
        if creator:
            try:
                dm_embed = discord.Embed(
                    title="🎟 Dein Ticket wurde geschlossen",
                    description=(
                        f"Dein **{data['type_name']}** auf **Cryptik Roleplay** wurde geschlossen.\n\n"
                        f"**Bearbeitet von:** {interaction.user.display_name}\n\n"
                        f"Wie zufrieden warst du mit der Bearbeitung?\n"
                        f"Bitte bewerte unseren Support:"
                    ),
                    color=LOG_COLOR,
                    timestamp=datetime.now(timezone.utc)
                )
                rating_view = RatingView(
                    channel_name=channel.name,
                    handler_name=interaction.user.display_name,
                    handler_id=interaction.user.id,
                    ticket_type=data["type_name"],
                    creator_name=data["creator_name"],
                    guild=interaction.guild
                )
                await creator.send(embed=dm_embed, view=rating_view)
            except Exception:
                pass

        ticket_data.pop(channel.id, None)
        await asyncio.sleep(3)
        try:
            await channel.delete(reason="Ticket geschlossen")
        except Exception as e:
            await log_bot_error("Ticket löschen fehlgeschlagen", str(e), interaction.guild)

    @discord.ui.button(
        label="Person zuweisen",
        style=discord.ButtonStyle.blurple,
        emoji="👤",
        custom_id="ticket_assign_btn"
    )
    async def assign_person(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Nur Teammitglieder können Personen zuweisen.", ephemeral=True
            )
            return
        assign_view = AssignView()
        await interaction.response.send_message(
            "Wähle eine Person aus die dem Ticket zugewiesen werden soll:",
            view=assign_view,
            ephemeral=True
        )


class CommentModal(discord.ui.Modal, title="⭐ Ticket Bewertung"):
    kommentar = discord.ui.TextInput(
        label="Wie war deine Erfahrung? (optional)",
        style=discord.TextStyle.long,
        placeholder="Schreibe hier dein Feedback zur Ticket-Bearbeitung...",
        required=False,
        max_length=1000
    )

    def __init__(self, stars: int, rating_view: "RatingView"):
        super().__init__()
        self.stars       = stars
        self.rating_view = rating_view

    async def on_submit(self, interaction: discord.Interaction):
        if self.rating_view.rated:
            await interaction.response.send_message(
                "Du hast dieses Ticket bereits bewertet.", ephemeral=True
            )
            return
        self.rating_view.rated = True

        stars        = self.stars
        star_display = "⭐" * stars + "☆" * (5 - stars)
        comment_text = self.kommentar.value.strip() if self.kommentar.value else ""

        thank_desc = (
            f"Du hast **{star_display}** ({stars}/5) gegeben.\n\n"
            + (f"**Dein Kommentar:**\n{comment_text}\n\n" if comment_text else "")
            + "Vielen Dank für dein Feedback! Wir arbeiten stets daran unseren Support zu verbessern. "
            "Wir hoffen dein Anliegen wurde zu deiner Zufriedenheit gelöst."
        )
        thank_embed = discord.Embed(
            title="💙 Danke für deine Bewertung!",
            description=thank_desc,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.response.send_message(embed=thank_embed)

        log_ch = self.rating_view.guild_ref.get_channel(TICKET_RATING_CHANNEL_ID)
        if log_ch:
            rating_desc = (
                f"**Ticket:** {self.rating_view.channel_name}\n"
                f"**Typ:** {self.rating_view.ticket_type}\n"
                f"**Erstellt von:** {self.rating_view.creator_name}\n"
                f"**Bearbeitet von:** {self.rating_view.handler_name}\n"
                f"**Bewertung:** {star_display} ({stars}/5)"
                + (f"\n**Kommentar:** {comment_text}" if comment_text else "")
            )
            rating_embed = discord.Embed(
                title="⭐ Ticket Bewertung",
                description=rating_desc,
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            await log_ch.send(embed=rating_embed)

        for item in self.rating_view.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self.rating_view)
        except Exception:
            pass


class RatingView(discord.ui.View):
    def __init__(self, channel_name, handler_name, handler_id, ticket_type, creator_name, guild):
        super().__init__(timeout=604800)
        self.channel_name = channel_name
        self.handler_name = handler_name
        self.handler_id   = handler_id
        self.ticket_type  = ticket_type
        self.creator_name = creator_name
        self.guild_ref    = guild
        self.rated        = False

    @discord.ui.button(label="⭐ 1", style=discord.ButtonStyle.grey, custom_id="rating_1")
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=1, rating_view=self))

    @discord.ui.button(label="⭐ 2", style=discord.ButtonStyle.grey, custom_id="rating_2")
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=2, rating_view=self))

    @discord.ui.button(label="⭐ 3", style=discord.ButtonStyle.grey, custom_id="rating_3")
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=3, rating_view=self))

    @discord.ui.button(label="⭐ 4", style=discord.ButtonStyle.grey, custom_id="rating_4")
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=4, rating_view=self))

    @discord.ui.button(label="⭐ 5", style=discord.ButtonStyle.green, custom_id="rating_5")
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=5, rating_view=self))


async def auto_ticket_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(TICKET_SETUP_CHANNEL_ID)
        if not channel:
            continue
        old_msg = None
        already_up_to_date = False
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Ticket erstellen" in emb.title:
                            if emb.description and "Crew Anfrage" in emb.description:
                                already_up_to_date = True
                            else:
                                old_msg = msg
                            break
                if already_up_to_date or old_msg:
                    break
        except Exception:
            pass
        if already_up_to_date:
            print(f"Ticket-Embed bereits aktuell in #{channel.name} — kein erneutes Posten.")
            continue
        if old_msg:
            try:
                await old_msg.delete()
                print(f"Altes Ticket-Embed gelöscht in #{channel.name} — wird neu gepostet.")
            except Exception:
                pass
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
                "🎟 **Bug Report** — Fehler oder Bug melden\n"
                "🎮 **Crew Anfrage** — Crew-Anfrage über Rockstar Social Club"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_image(url="https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/ticket_banner.jpg")
        embed.set_footer(text="Cryptik Roleplay — Support System")
        try:
            await channel.send(embed=embed, view=TicketSelectView())
            print(f"Ticket-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_ticket_setup fehlgeschlagen", str(e), guild)


async def auto_lohnliste_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(LOHNLISTE_CHANNEL_ID)
        if not channel:
            continue
        already_posted = False
        try:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Lohnliste" in emb.title:
                            already_posted = True
                            break
                if already_posted:
                    break
        except Exception:
            pass
        if already_posted:
            print(f"Lohnliste bereits vorhanden in #{channel.name} — kein erneutes Posten.")
            continue
        desc = (
            f"<@&1490855796932739093>\n**1.500 💵 Stündlich**\n\n"
            f"<@&1490855789844234310>\n**2.500 💵 Stündlich**\n\n"
            f"<@&1490855790913785886>\n**3.500 💵 Stündlich**\n\n"
            f"<@&1490855791953973421>\n**4.500 💵 Stündlich**\n\n"
            f"<@&1490855792671461478>\n**5.500 💵 Stündlich**\n\n"
            f"<@&1490855793694871595>\n**6.500 💵 Stündlich**\n\n"
            f"<@&1490855795360006246>\n**1.200 💵 Stündlich** *(Zusatzlohn)*"
        )
        embed = discord.Embed(
            title="💵 Lohnliste 💵",
            description=desc,
            color=LOG_COLOR
        )
        try:
            await channel.send(embed=embed)
            print(f"Lohnliste automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_lohnliste_setup fehlgeschlagen", str(e), guild)
