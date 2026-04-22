# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# ticket.py \u2014 Ticket System (Support, Highteam, Fraktion, etc.)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

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
                "\u274C Du hast bereits ein offenes Ticket!", ephemeral=True
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
            "\u274C Ticket konnte nicht erstellt werden.", ephemeral=True
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
        title=f"\U0001F39F {type_name}",
        description=(
            f"Willkommen {member.mention}!\n\n"
            f"Dein Ticket wurde erfolgreich erstellt. Das Team wird sich schnellstm\u00F6glich um dein Anliegen k\u00FCmmern.\n\n"
            f"**Ticket-Typ:** {type_name}\n"
            f"**Erstellt von:** {member.mention}\n"
            f"**Erstellt am:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    welcome_embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")

    action_view = TicketActionView()
    await channel.send(content=team_mentions, embed=welcome_embed, view=action_view)

    # \u2500\u2500 Crew Anfrage: Vorlage automatisch ins Ticket senden \u2500\u2500\u2500
    if ticket_type == "crew":
        crew_embed = discord.Embed(
            title="\U0001F4CB Crew Anfrage \u2014 Vorlage",
            description=(
                "Bitte gib Folgendes an:\n\n"
                "**PSN Name:**\n\n"
                "**Social Club Name:**"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        crew_embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")
        await channel.send(embed=crew_embed)

    await interaction.response.send_message(
        f"\u2705 Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True
    )

    log_ch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="\U0001F4C2 Ticket Ge\u00F6ffnet",
            description=(
                f"**Benutzer:** {member.mention} (`{member}`)\n"
                f"**Typ:** {type_name}\n"
                f"**Channel:** {channel.mention}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        log_embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")
        await log_ch.send(embed=log_embed)


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support",            emoji="\U0001F39F", value="support",    description="Allgemeiner Support"),
            discord.SelectOption(label="Highteam Ticket",    emoji="\U0001F39F", value="highteam",   description="Direkter Kontakt zum Highteam"),
            discord.SelectOption(label="Fraktions Bewerbung",emoji="\U0001F39F", value="fraktion",   description="Bewerbung f\u00FCr eine Fraktion"),
            discord.SelectOption(label="Beschwerde Ticket",  emoji="\U0001F39F", value="beschwerde", description="Beschwerde einreichen"),
            discord.SelectOption(label="Bug Report",          emoji="\U0001F39F", value="bug",        description="Fehler oder Bug melden"),
            discord.SelectOption(label="Crew Anfrage",        emoji="\U0001F3AE", value="crew",       description="Crew-Anfrage \u00FCber Rockstar Social Club"),
        ]
        super().__init__(
            placeholder="\U0001F39F W\u00E4hle eine Ticket-Art aus...",
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
            placeholder="Person ausw\u00E4hlen...",
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
                "\u274C Berechtigung konnte nicht gesetzt werden.", ephemeral=True
            )
            await log_bot_error("Ticket-Zuweisung fehlgeschlagen", str(e), interaction.guild)
            return

        if channel.id in ticket_data:
            ticket_data[channel.id]["handler"]    = str(user)
            ticket_data[channel.id]["handler_id"] = user.id

        assign_embed = discord.Embed(
            description=(
                f"\U0001F464 {user.mention} wurde dem Ticket zugewiesen.\n"
                f"**Zugewiesen von:** {interaction.user.mention}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        assign_embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")
        await channel.send(embed=assign_embed)
        await interaction.response.send_message(
            f"\u2705 {user.mention} wurde dem Ticket zugewiesen.", ephemeral=True
        )


class AssignView(TimedDisableView):
    def __init__(self):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.add_item(AssignUserSelect())


class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ticket schlie\u00DFen",
        style=discord.ButtonStyle.red,
        emoji="\U0001F512",
        custom_id="ticket_close_btn"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "\u274C Nur Teammitglieder k\u00F6nnen Tickets schlie\u00DFen.", ephemeral=True
            )
            return

        channel = interaction.channel
        data    = ticket_data.get(channel.id)
        if not data:
            await interaction.response.send_message(
                "\u274C Ticket-Daten nicht gefunden.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        ticket_data[channel.id]["handler"]    = str(interaction.user)
        ticket_data[channel.id]["handler_id"] = interaction.user.id

        closing_embed = discord.Embed(
            title="\U0001F512 Ticket wird geschlossen...",
            description="Das Ticket wird in wenigen Sekunden geschlossen.",
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        closing_embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")
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
                        transcript_lines.append(f"  \u21B3 {short}")
        except Exception:
            transcript_lines.append("(Transkript konnte nicht vollst\u00E4ndig geladen werden)")

        transcript_text = "\n".join(transcript_lines)
        transcript_file = discord.File(
            fp=io.BytesIO(transcript_text.encode("utf-8")),
            filename=f"transkript-{channel.name}.txt"
        )

        log_ch = interaction.guild.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            closed_embed = discord.Embed(
                title="\U0001F4C1 Ticket Geschlossen",
                description=(
                    f"**Benutzer:** <@{data['creator_id']}> (`{data['creator_name']}`)\n"
                    f"**Typ:** {data['type_name']}\n"
                    f"**Geschlossen von:** {interaction.user.mention} (`{interaction.user}`)\n"
                    f"**Channel:** #{channel.name}"
                ),
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            closed_embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")
            await log_ch.send(embed=closed_embed, file=transcript_file)

        creator = interaction.guild.get_member(data["creator_id"])
        if creator:
            try:
                dm_embed = discord.Embed(
                    title="\U0001F39F Dein Ticket wurde geschlossen",
                    description=(
                        f"Dein **{data['type_name']}** auf **Paradise City Roleplay** wurde geschlossen.\n\n"
                        f"**Bearbeitet von:** {interaction.user.display_name}\n\n"
                        f"Wie zufrieden warst du mit der Bearbeitung?\n"
                        f"Bitte bewerte unseren Support:"
                    ),
                    color=LOG_COLOR,
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")
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
            await log_bot_error("Ticket l\u00F6schen fehlgeschlagen", str(e), interaction.guild)

    @discord.ui.button(
        label="Person zuweisen",
        style=discord.ButtonStyle.blurple,
        emoji="\U0001F464",
        custom_id="ticket_assign_btn"
    )
    async def assign_person(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "\u274C Nur Teammitglieder k\u00F6nnen Personen zuweisen.", ephemeral=True
            )
            return
        assign_view = AssignView()
        await interaction.response.send_message(
            "W\u00E4hle eine Person aus die dem Ticket zugewiesen werden soll:",
            view=assign_view,
            ephemeral=True
        )


class CommentModal(discord.ui.Modal, title="\u2B50 Ticket Bewertung"):
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
        star_display = "\u2B50" * stars + "\u2606" * (5 - stars)
        comment_text = self.kommentar.value.strip() if self.kommentar.value else ""

        thank_desc = (
            f"Du hast **{star_display}** ({stars}/5) gegeben.\n\n"
            + (f"**Dein Kommentar:**\n{comment_text}\n\n" if comment_text else "")
            + "Vielen Dank f\u00FCr dein Feedback! Wir arbeiten stets daran unseren Support zu verbessern. "
            "Wir hoffen dein Anliegen wurde zu deiner Zufriedenheit gel\u00F6st."
        )
        thank_embed = discord.Embed(
            title="\U0001F499 Danke f\u00FCr deine Bewertung!",
            description=thank_desc,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        thank_embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")
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
                title="\u2B50 Ticket Bewertung",
                description=rating_desc,
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            rating_embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")
            await log_ch.send(embed=rating_embed)

        for item in self.rating_view.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self.rating_view)
        except Exception:
            pass


class RatingView(TimedDisableView):
    def __init__(self, channel_name, handler_name, handler_id, ticket_type, creator_name, guild):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.channel_name = channel_name
        self.handler_name = handler_name
        self.handler_id   = handler_id
        self.ticket_type  = ticket_type
        self.creator_name = creator_name
        self.guild_ref    = guild
        self.rated        = False

    @discord.ui.button(label="\u2B50 1", style=discord.ButtonStyle.grey, custom_id="rating_1")
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=1, rating_view=self))

    @discord.ui.button(label="\u2B50 2", style=discord.ButtonStyle.grey, custom_id="rating_2")
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=2, rating_view=self))

    @discord.ui.button(label="\u2B50 3", style=discord.ButtonStyle.grey, custom_id="rating_3")
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=3, rating_view=self))

    @discord.ui.button(label="\u2B50 4", style=discord.ButtonStyle.grey, custom_id="rating_4")
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=4, rating_view=self))

    @discord.ui.button(label="\u2B50 5", style=discord.ButtonStyle.green, custom_id="rating_5")
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(stars=5, rating_view=self))


TICKET_IMG_URL = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/ticket.png"

def _build_ticket_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\U0001F39F\uFE0F Paradise City \u2014 Support System",
        description=(
            "Ben\u00F6tigst du Hilfe oder hast ein Anliegen?\n"
            "W\u00E4hle unten die passende Ticket-Art aus \u2014 unser Team meldet sich schnellstm\u00F6glich.\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(
        name="\U0001F39F\uFE0F Support",
        value="> Allgemeiner Support bei Fragen & Problemen",
        inline=False,
    )
    embed.add_field(
        name="\U0001F451 Highteam Ticket",
        value="> Direkter Kontakt zum Highteam",
        inline=False,
    )
    embed.add_field(
        name="\U0001F3DB\uFE0F Fraktions Bewerbung",
        value="> Bewirb dich f\u00FCr eine Fraktion auf dem Server",
        inline=False,
    )
    embed.add_field(
        name="\U0001F4E2 Beschwerde Ticket",
        value="> Melde eine Beschwerde gegen einen Spieler oder Mitarbeiter",
        inline=False,
    )
    embed.add_field(
        name="\U0001F41B Bug Report",
        value="> Melde einen Fehler oder Bug im Roleplay",
        inline=False,
    )
    embed.add_field(
        name="\U0001F3AE Crew Anfrage",
        value="> Crew-Anfrage \u00FCber den Rockstar Social Club",
        inline=False,
    )

    embed.set_thumbnail(url=TICKET_IMG_URL)
    embed.set_footer(text="Paradise City Roleplay \u2022 Support-System | Nur ein Ticket gleichzeitig m\u00F6glich")
    return embed


TICKET_INFO_CHANNEL_ID = 1490885002030874775


@bot.tree.command(
    name="setup-ticket",
    description="[Admin] Ticket-Embed neu posten (l\u00F6scht altes und postet aktuelles)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
async def cmd_setup_ticket(interaction: discord.Interaction):
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild    = interaction.guild
    posted   = 0
    channels = []

    for ch_id in [TICKET_SETUP_CHANNEL_ID, TICKET_INFO_CHANNEL_ID]:
        ch = guild.get_channel(ch_id)
        if ch:
            channels.append(ch)

    if not channels:
        await interaction.followup.send("\u274C Kein Ticket-Channel gefunden.", ephemeral=True)
        return

    for ch in channels:
        try:
            async for msg in ch.history(limit=100):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Ticket erstellen" in emb.title:
                            await msg.delete()
                            break
        except Exception as e:
            await log_bot_error("setup-ticket: L\u00F6schen fehlgeschlagen", str(e), guild)

        try:
            await ch.send(embed=_build_ticket_embed(), view=TicketSelectView())
            posted += 1
        except Exception as e:
            await log_bot_error("setup-ticket: Senden fehlgeschlagen", str(e), guild)

    if posted == 0:
        await interaction.followup.send("\u274C Embed konnte nicht gesendet werden.", ephemeral=True)
        return

    await interaction.followup.send(
        f"\u2705 Ticket-Embed in {posted} Kanal{'\u00E4' if posted != 1 else 'a'}len neu gepostet.",
        ephemeral=True
    )


async def _post_ticket_to_channel(guild: discord.Guild, channel_id: int, with_view: bool = True):
    channel = guild.get_channel(channel_id)
    if not channel:
        return
    existing = None
    try:
        async for msg in channel.history(limit=100):
            if msg.author.id == bot.user.id and msg.embeds:
                for emb in msg.embeds:
                    if emb.title and "Ticket erstellen" in emb.title:
                        existing = msg
                        break
            if existing:
                break
    except Exception:
        pass
    try:
        if existing:
            if with_view:
                await existing.edit(embed=_build_ticket_embed(), view=TicketSelectView())
            else:
                await existing.edit(embed=_build_ticket_embed())
        else:
            if with_view:
                await channel.send(embed=_build_ticket_embed(), view=TicketSelectView())
            else:
                await channel.send(embed=_build_ticket_embed())
    except Exception as e:
        await log_bot_error(f"Ticket-Embed in #{channel.name} fehlgeschlagen", str(e), guild)


async def auto_ticket_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(TICKET_SETUP_CHANNEL_ID)
        if not channel:
            continue
        already_up_to_date = False
        try:
            async for msg in channel.history(limit=100):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Ticket erstellen" in emb.title:
                            if emb.description and "Crew Anfrage" in emb.description:
                                already_up_to_date = True
                            break
                if already_up_to_date:
                    break
        except Exception:
            pass
        if already_up_to_date:
            print(f"Ticket-Embed bereits aktuell in #{channel.name} \u2014 kein erneutes Posten.")
        else:
            try:
                async for msg in channel.history(limit=100):
                    if msg.author.id == bot.user.id and msg.embeds:
                        for emb in msg.embeds:
                            if emb.title and "Ticket erstellen" in emb.title:
                                await msg.delete()
                                break
            except Exception:
                pass
            try:
                await channel.send(embed=_build_ticket_embed(), view=TicketSelectView())
                print(f"Ticket-Embed gepostet in #{channel.name}")
            except Exception as e:
                await log_bot_error("auto_ticket_setup fehlgeschlagen", str(e), guild)

        await _post_ticket_to_channel(guild, TICKET_INFO_CHANNEL_ID, with_view=True)



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
            print(f"Lohnliste bereits vorhanden in #{channel.name} \u2014 kein erneutes Posten.")
            continue
        desc = (
            f"<@&1490855796932739093>\n**1.500 \U0001F4B5 St\u00FCndlich**\n\n"
            f"<@&1490855789844234310>\n**2.500 \U0001F4B5 St\u00FCndlich**\n\n"
            f"<@&1490855790913785886>\n**3.500 \U0001F4B5 St\u00FCndlich**\n\n"
            f"<@&1490855791953973421>\n**4.500 \U0001F4B5 St\u00FCndlich**\n\n"
            f"<@&1490855792671461478>\n**5.500 \U0001F4B5 St\u00FCndlich**\n\n"
            f"<@&1490855793694871595>\n**6.500 \U0001F4B5 St\u00FCndlich**\n\n"
            f"<@&1490855795360006246>\n**1.200 \U0001F4B5 St\u00FCndlich** *(Zusatzlohn)*"
        )
        embed = discord.Embed(
            title="\U0001F4B5 Lohnliste \U0001F4B5",
            description=desc,
            color=LOG_COLOR
        )
        embed.set_footer(text="Paradise City Roleplay \u2022 Support-System")
        try:
            await channel.send(embed=embed)
            print(f"Lohnliste automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_lohnliste_setup fehlgeschlagen", str(e), guild)
