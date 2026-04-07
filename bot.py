import os
import io
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

TICKET_SETUP_CHANNEL_ID  = 1490885002030874775
TICKET_CATEGORY_DEFAULT  = 1490882554570608751
TICKET_CATEGORY_HIGHTEAM = 1491069210389119016
TICKET_CATEGORY_FRAKTION = 1491069425384685750
TICKET_LOG_CHANNEL_ID    = 1490878139306606743

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
ticket_data   = {}

FEATURES = {
    "Discord Link Schutz":         True,
    "Link Filter (Memes)":         True,
    "Vulgäre Wörter Filter":       True,
    "Spam Schutz":                 True,
    "Nachrichten Log":             True,
    "Bearbeitungs Log":            True,
    "Rollen Log":                  True,
    "Member Log":                  True,
    "Join Log + Invites":          True,
    "Bot Kick":                    True,
    "Fehler Logging":              True,
    "Rollen-Entfernung (Timeout)": True,
    "Ticket System":               True,
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

async def apply_timeout_restrictions(member, guild, duration_h=None, duration_m=None, reason="Regelverstoß"):
    timeout_ok = False
    if duration_h:
        timeout_until = datetime.now(timezone.utc) + timedelta(hours=duration_h)
    else:
        timeout_until = datetime.now(timezone.utc) + timedelta(minutes=duration_m)
    try:
        await member.timeout(timeout_until, reason=reason)
        timeout_ok = True
    except Exception as e:
        await log_bot_error(
            f"Timeout fehlgeschlagen ({reason})",
            f"Benutzer: {member} ({member.id})\nFehler: {e}\n\nMögliche Ursachen:\n- Bot hat keine 'Mitglieder moderieren' Berechtigung\n- Bot-Rolle ist niedriger als die Ziel-Rolle",
            guild
        )
    roles_removed = []
    try:
        roles_to_remove = [r for r in member.roles if r != guild.default_role and not r.managed]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"Timeout: {reason}")
            roles_removed = roles_to_remove
    except Exception as e:
        await log_bot_error("Rollen entfernen fehlgeschlagen", str(e), guild)
    return timeout_ok, roles_removed


TICKET_TYPE_NAMES = {
    "support":    "Support",
    "highteam":   "Highteam Ticket",
    "fraktion":   "Fraktions Bewerbung",
    "beschwerde": "Beschwerde Ticket",
    "bug":        "Bug Report",
}
TICKET_TYPE_CATEGORIES = {
    "support":    TICKET_CATEGORY_DEFAULT,
    "highteam":   TICKET_CATEGORY_HIGHTEAM,
    "fraktion":   TICKET_CATEGORY_FRAKTION,
    "beschwerde": TICKET_CATEGORY_DEFAULT,
    "bug":        TICKET_CATEGORY_DEFAULT,
}


async def create_ticket(interaction: discord.Interaction, ticket_type: str):
    guild  = interaction.guild
    member = interaction.user
    for ch in guild.text_channels:
        data = ticket_data.get(ch.id)
        if data and data["creator_id"] == member.id:
            await interaction.response.send_message("❌ Du hast bereits ein offenes Ticket!", ephemeral=True)
            return
    type_name   = TICKET_TYPE_NAMES.get(ticket_type, ticket_type)
    category_id = TICKET_TYPE_CATEGORIES.get(ticket_type, TICKET_CATEGORY_DEFAULT)
    category    = guild.get_channel(category_id)
    admin_role  = guild.get_role(ADMIN_ROLE_ID)
    mod_role    = guild.get_role(MOD_ROLE_ID)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True, manage_messages=True),
    }
    if admin_role:
        overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True, manage_messages=True)
    if mod_role:
        overwrites[mod_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True, manage_messages=True)
    safe_name    = member.name[:15].lower().replace(" ", "-")
    channel_name = f"ticket-{ticket_type}-{safe_name}"
    try:
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites, topic=f"Ticket von {member} ({member.id}) | Typ: {type_name}")
    except Exception as e:
        await interaction.response.send_message("❌ Ticket konnte nicht erstellt werden.", ephemeral=True)
        await log_bot_error("Ticket erstellen fehlgeschlagen", str(e), guild)
        return
    ticket_data[channel.id] = {
        "creator_id": member.id, "creator_name": str(member),
        "type": ticket_type, "type_name": type_name,
        "handler": None, "handler_id": None,
        "opened_at": datetime.now(timezone.utc).isoformat(),
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
            f"**Ticket-Typ:** {type_name}\n**Erstellt von:** {member.mention}\n"
            f"**Erstellt am:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>"
        ),
        color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
    )
    welcome_embed.set_footer(text="Nur Teammitglieder können das Ticket schließen")
    await channel.send(content=team_mentions, embed=welcome_embed, view=TicketActionView())
    await interaction.response.send_message(f"✅ Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True)
    log_ch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if log_ch:
        await log_ch.send(embed=discord.Embed(
            title="📂 Ticket Geöffnet",
            description=f"**Benutzer:** {member.mention} (`{member}`)\n**Typ:** {type_name}\n**Channel:** {channel.mention}",
            color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
        ))


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", emoji="🎟", value="support", description="Allgemeiner Support"),
            discord.SelectOption(label="Highteam Ticket", emoji="🎟", value="highteam", description="Direkter Kontakt zum Highteam"),
            discord.SelectOption(label="Fraktions Bewerbung", emoji="🎟", value="fraktion", description="Bewerbung für eine Fraktion"),
            discord.SelectOption(label="Beschwerde Ticket", emoji="🎟", value="beschwerde", description="Beschwerde einreichen"),
            discord.SelectOption(label="Bug Report", emoji="🎟", value="bug", description="Fehler oder Bug melden"),
        ]
        super().__init__(placeholder="🎟 Wähle eine Ticket-Art aus...", options=options, custom_id="ticket_select_main")
    async def callback(self, interaction: discord.Interaction):
        await create_ticket(interaction, self.values[0])

class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class AssignUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="Person auswählen...", custom_id="ticket_assign_user_select", min_values=1, max_values=1)
    async def callback(self, interaction: discord.Interaction):
        user = self.values[0]
        channel = interaction.channel
        try:
            await channel.set_permissions(user, view_channel=True, send_messages=True, read_message_history=True)
        except Exception as e:
            await interaction.response.send_message("❌ Berechtigung konnte nicht gesetzt werden.", ephemeral=True)
            await log_bot_error("Ticket-Zuweisung fehlgeschlagen", str(e), interaction.guild)
            return
        if channel.id in ticket_data:
            ticket_data[channel.id]["handler"]    = str(user)
            ticket_data[channel.id]["handler_id"] = user.id
        await channel.send(embed=discord.Embed(
            description=f"👤 {user.mention} wurde dem Ticket zugewiesen.\n**Zugewiesen von:** {interaction.user.mention}",
            color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
        ))
        await interaction.response.send_message(f"✅ {user.mention} wurde dem Ticket zugewiesen.", ephemeral=True)

class AssignView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(AssignUserSelect())

class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket schließen", style=discord.ButtonStyle.red, emoji="🔒", custom_id="ticket_close_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message("❌ Nur Teammitglieder können Tickets schließen.", ephemeral=True)
            return
        channel = interaction.channel
        data = ticket_data.get(channel.id)
        if not data:
            await interaction.response.send_message("❌ Ticket-Daten nicht gefunden.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        ticket_data[channel.id]["handler"]    = str(interaction.user)
        ticket_data[channel.id]["handler_id"] = interaction.user.id
        await channel.send(embed=discord.Embed(title="🔒 Ticket wird geschlossen...", description="Das Ticket wird in wenigen Sekunden geschlossen.", color=MOD_COLOR, timestamp=datetime.now(timezone.utc)))
        transcript_lines = [
            f"=== Ticket Transkript: {data['type_name']} ===",
            f"Erstellt von  : {data['creator_name']}",
            f"Bearbeitet von: {str(interaction.user)}",
            f"Datum         : {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')} UTC",
            "=" * 55, ""
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
                        transcript_lines.append(f"[{ts}] {msg.author} [Embed]: {emb.title}")
                    if emb.description:
                        transcript_lines.append(f"  ↳ {emb.description[:200].replace(chr(10), ' ')}")
        except Exception:
            transcript_lines.append("(Transkript konnte nicht vollständig geladen werden)")
        transcript_file = discord.File(fp=io.BytesIO("\n".join(transcript_lines).encode("utf-8")), filename=f"transkript-{channel.name}.txt")
        log_ch = interaction.guild.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(embed=discord.Embed(
                title="📁 Ticket Geschlossen",
                description=(
                    f"**Benutzer:** <@{data['creator_id']}> (`{data['creator_name']}`)\n"
                    f"**Typ:** {data['type_name']}\n"
                    f"**Geschlossen von:** {interaction.user.mention} (`{interaction.user}`)\n"
                    f"**Channel:** #{channel.name}"
                ),
                color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
            ), file=transcript_file)
        creator = interaction.guild.get_member(data["creator_id"])
        if creator:
            try:
                rating_view = RatingView(
                    channel_name=channel.name, handler_name=interaction.user.display_name,
                    handler_id=interaction.user.id, ticket_type=data["type_name"],
                    creator_name=data["creator_name"], guild=interaction.guild
                )
                await creator.send(embed=discord.Embed(
                    title="🎟 Dein Ticket wurde geschlossen",
                    description=(
                        f"Dein **{data['type_name']}** auf **Cryptik Roleplay** wurde geschlossen.\n\n"
                        f"**Bearbeitet von:** {interaction.user.display_name}\n\n"
                        f"Wie zufrieden warst du mit der Bearbeitung?\nBitte bewerte unseren Support:"
                    ),
                    color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
                ), view=rating_view)
            except Exception:
                pass
        ticket_data.pop(channel.id, None)
        await asyncio.sleep(3)
        try:
            await channel.delete(reason="Ticket geschlossen")
        except Exception as e:
            await log_bot_error("Ticket löschen fehlgeschlagen", str(e), interaction.guild)

    @discord.ui.button(label="Person zuweisen", style=discord.ButtonStyle.blurple, emoji="👤", custom_id="ticket_assign_btn")
    async def assign_person(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message("❌ Nur Teammitglieder können Personen zuweisen.", ephemeral=True)
            return
        await interaction.response.send_message("Wähle eine Person aus:", view=AssignView(), ephemeral=True)


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

    async def submit_rating(self, interaction: discord.Interaction, stars: int):
        if self.rated:
            await interaction.response.send_message("Du hast dieses Ticket bereits bewertet.", ephemeral=True)
            return
        self.rated = True
        star_display = "⭐" * stars + "☆" * (5 - stars)
        await interaction.response.send_message(embed=discord.Embed(
            title="💙 Danke für deine Bewertung!",
            description=(
                f"Du hast **{star_display}** ({stars}/5) gegeben.\n\n"
                f"Vielen Dank für dein Feedback! Wir arbeiten stets daran unseren Support zu verbessern."
            ),
            color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
        ))
        log_ch = self.guild_ref.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(embed=discord.Embed(
                title="⭐ Ticket Bewertung",
                description=(
                    f"**Ticket:** {self.channel_name}\n**Typ:** {self.ticket_type}\n"
                    f"**Erstellt von:** {self.creator_name}\n**Bearbeitet von:** {self.handler_name}\n"
                    f"**Bewertung:** {star_display} ({stars}/5)"
                ),
                color=LOG_COLOR, timestamp=datetime.now(timezone.utc)
            ))
        for item in self.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="⭐ 1", style=discord.ButtonStyle.grey, custom_id="rating_1")
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 1)
    @discord.ui.button(label="⭐ 2", style=discord.ButtonStyle.grey, custom_id="rating_2")
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 2)
    @discord.ui.button(label="⭐ 3", style=discord.ButtonStyle.grey, custom_id="rating_3")
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 3)
    @discord.ui.button(label="⭐ 4", style=discord.ButtonStyle.grey, custom_id="rating_4")
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 4)
    @discord.ui.button(label="⭐ 5", style=discord.ButtonStyle.green, custom_id="rating_5")
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 5)
