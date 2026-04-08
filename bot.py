import os
import io
import json
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
import asyncio
import traceback

# Sicherheitscheck: Bot läuft NUR auf Railway, nie doppelt in Replit
# Auf Railway ist RAILWAY_ENVIRONMENT automatisch gesetzt
if not os.environ.get("RAILWAY_ENVIRONMENT") and not os.environ.get("FORCE_LOCAL_RUN"):
    print("=" * 60)
    print("STOPP: Bot wurde NICHT gestartet.")
    print("Dieser Bot läuft ausschließlich auf Railway.")
    print("Bitte NICHT in Replit starten — nur auf Railway deployen!")
    print("=" * 60)
    exit(0)

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

# Rollen die automatisch vergeben werden, sobald ein Charakter erstellt wurde
CHARAKTER_ROLLEN = [
    1490855719853887569,
    1490855722534310003,
    1490855728473178282,
    1490855731950256128,
    1490855741647618251,
    1490855750329696446,
    1490855759674740849,
    1490855768532975687,
    1490855768948211905,
    1490855779694280876,
    1490855796932739093,
    1490855788829216940,
]

TICKET_SETUP_CHANNEL_ID  = 1490882553559650355
TICKET_CATEGORY_DEFAULT  = 1490882554570608751
TICKET_CATEGORY_HIGHTEAM = 1491069210389119016
TICKET_CATEGORY_FRAKTION = 1491069425384685750
TICKET_LOG_CHANNEL_ID    = 1490878139306606743

COUNTING_CHANNEL_ID = 1490882580487340044

# ── Economy ──────────────────────────────────────────────────────────────
LOHNLISTE_CHANNEL_ID = 1490890346668888194
LOHN_CHANNEL_ID      = 1490890348254200049
BANK_CHANNEL_ID      = 1490890349382734044
SHOP_CHANNEL_ID      = 1490890311755628584

CITIZEN_ROLE_ID = 1490855722534310003

WAGE_ROLES = {
    1490855796932739093: 1500,
    1490855789844234310: 2500,
    1490855790913785886: 3500,
    1490855791953973421: 4500,
    1490855792671461478: 5500,
    1490855793694871595: 6500,
}
ADDITIONAL_WAGE_ROLE_ID   = 1490855795360006246
ADDITIONAL_WAGE_ROLE_WAGE = 1200

DAILY_LIMIT = 1_000_000

BETRAG_CHOICES = [
    app_commands.Choice(name="1.000 💵",       value=1_000),
    app_commands.Choice(name="5.000 💵",       value=5_000),
    app_commands.Choice(name="10.000 💵",      value=10_000),
    app_commands.Choice(name="25.000 💵",      value=25_000),
    app_commands.Choice(name="50.000 💵",      value=50_000),
    app_commands.Choice(name="100.000 💵",     value=100_000),
    app_commands.Choice(name="250.000 💵",     value=250_000),
    app_commands.Choice(name="500.000 💵",     value=500_000),
    app_commands.Choice(name="1.000.000 💵",   value=1_000_000),
]

LIMIT_CHOICES = [
    app_commands.Choice(name="1.000.000 💵",   value=1_000_000),
    app_commands.Choice(name="2.000.000 💵",   value=2_000_000),
    app_commands.Choice(name="3.000.000 💵",   value=3_000_000),
    app_commands.Choice(name="4.000.000 💵",   value=4_000_000),
    app_commands.Choice(name="5.000.000 💵",   value=5_000_000),
    app_commands.Choice(name="6.000.000 💵",   value=6_000_000),
    app_commands.Choice(name="7.000.000 💵",   value=7_000_000),
    app_commands.Choice(name="8.000.000 💵",   value=8_000_000),
    app_commands.Choice(name="9.000.000 💵",   value=9_000_000),
    app_commands.Choice(name="10.000.000 💵",  value=10_000_000),
]

ECONOMY_FILE      = Path(__file__).parent / "economy_data.json"
SHOP_FILE         = Path(__file__).parent / "shop_data.json"
WARNS_FILE        = Path(__file__).parent / "warns_data.json"
HIDDEN_ITEMS_FILE = Path(__file__).parent / "hidden_items.json"
AUSWEIS_FILE      = Path(__file__).parent / "ausweis_data.json"

# Neue Kanal- und Rollen-IDs
WARN_LOG_CHANNEL_ID     = 1491113577258684466
MONEY_LOG_CHANNEL_ID    = 1490878138429997087
RUCKSACK_CHANNEL_ID     = 1490882592445304972
UEBERGEBEN_CHANNEL_ID   = 1490882589014364250
VERSTECKEN_CHANNEL_ID   = 1490882591023173682
TEAM_CITIZEN_CHANNEL_ID = 1490882591023173682

WELCOME_CHANNEL_ID  = 1490878151897911557
GOODBYE_CHANNEL_ID  = 1490878154733260951
EINREISE_CHANNEL_ID = 1490878156582686853
AUSWEIS_CHANNEL_ID  = 1490882590012604538
LEGAL_ROLE_ID       = 1490855729635135489
ILLEGAL_ROLE_ID     = 1490855730767597738

WARN_AUTO_TIMEOUT_COUNT = 3
START_CASH              = 5_000     # Startguthaben für neue Spieler

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

spam_tracker  = {}
spam_warned   = set()
ticket_data   = {}
counting_state    = {"count": 0, "last_user_id": None}
counting_handled  = set()  # verhindert doppelte Verarbeitung

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
    "Zähl-Kanal":                  True,
    "Economy System":              True,
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
            f"Benutzer: {member} ({member.id})\nFehler: {e}\n\n"
            f"Mögliche Ursachen:\n"
            f"- Bot hat keine 'Mitglieder moderieren' Berechtigung\n"
            f"- Bot-Rolle ist niedriger als die Ziel-Rolle",
            guild
        )
    roles_removed = []
    try:
        roles_to_remove = [
            r for r in member.roles
            if r != guild.default_role and not r.managed
        ]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"Timeout: {reason}")
            roles_removed = roles_to_remove
    except Exception as e:
        await log_bot_error("Rollen entfernen fehlgeschlagen", str(e), guild)
    return timeout_ok, roles_removed


# ── Economy Helpers ──────────────────────────────────────────────────────

def load_economy():
    if ECONOMY_FILE.exists():
        with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_economy(data):
    with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "cash": 0,
            "bank": 0,
            "last_wage": None,
            "daily_deposit": 0,
            "daily_withdraw": 0,
            "daily_transfer": 0,
            "daily_reset": None,
            "inventory": [],
            "custom_limit": None,
        }
    return data[uid]

def reset_daily_if_needed(user_data):
    now = datetime.now(timezone.utc)
    if user_data.get("daily_reset") is None:
        user_data["daily_reset"] = now.isoformat()
        return
    last_reset = datetime.fromisoformat(user_data["daily_reset"])
    if (now - last_reset).total_seconds() >= 86400:
        user_data["daily_deposit"]  = 0
        user_data["daily_withdraw"] = 0
        user_data["daily_transfer"] = 0
        user_data["daily_reset"]    = now.isoformat()

def load_shop():
    if SHOP_FILE.exists():
        with open(SHOP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_shop(items):
    with open(SHOP_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def has_citizen_or_wage(member):
    role_ids = [r.id for r in member.roles]
    return (
        CITIZEN_ROLE_ID in role_ids
        or ADMIN_ROLE_ID in role_ids
        or any(r in role_ids for r in WAGE_ROLES)
    )

def is_team(member):
    return any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in member.roles)


# ── Warn Helpers ──────────────────────────────────────────────────────────

def load_warns():
    if WARNS_FILE.exists():
        with open(WARNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_warns(data):
    with open(WARNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user_warns(warns, user_id):
    return warns.setdefault(str(user_id), [])


# ── Hidden Items Helpers ──────────────────────────────────────────────────

def load_hidden_items():
    if HIDDEN_ITEMS_FILE.exists():
        with open(HIDDEN_ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_hidden_items(data):
    with open(HIDDEN_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Money Log Helper ──────────────────────────────────────────────────────

async def log_money_action(guild: discord.Guild, title: str, description: str):
    ch = guild.get_channel(MONEY_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title=f"💵 {title}",
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await ch.send(embed=embed)
        except Exception:
            pass


# ── Betrag Autocomplete (1K–10M, Freitext erlaubt) ────────────────────────

BETRAG_SUGGESTIONS = [
    1_000, 5_000, 10_000, 25_000, 50_000,
    100_000, 250_000, 500_000, 1_000_000,
    2_000_000, 5_000_000, 10_000_000
]

async def betrag_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[int]]:
    choices = []
    clean = current.replace(".", "").replace(",", "").strip()
    for val in BETRAG_SUGGESTIONS:
        label = f"{val:,} 💵".replace(",", ".")
        if clean == "" or clean in str(val) or clean.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=val))
    return choices[:25]


# ── Versteck-Button (persistent) ─────────────────────────────────────────

class VersteckRetrieveView(discord.ui.View):
    def __init__(self, item_id: str, owner_id: int):
        super().__init__(timeout=None)
        self.item_id  = item_id
        self.owner_id = owner_id
        btn = discord.ui.Button(
            label="📦 Aus Versteck holen",
            style=discord.ButtonStyle.green,
            custom_id=f"retrieve_{item_id}_{owner_id}"
        )
        btn.callback = self.retrieve_callback
        self.add_item(btn)

    async def retrieve_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Nur derjenige der das Item versteckt hat kann es herausnehmen.",
                ephemeral=True
            )
            return
        hidden = load_hidden_items()
        entry  = next((h for h in hidden if h["id"] == self.item_id), None)
        if not entry:
            await interaction.response.send_message("❌ Item wurde bereits geborgen oder existiert nicht mehr.", ephemeral=True)
            return

        # Item zurück ins Inventar
        eco       = load_economy()
        user_data = get_user(eco, interaction.user.id)
        user_data.setdefault("inventory", []).append(entry["item"])
        save_economy(eco)

        # Hidden item entfernen
        hidden = [h for h in hidden if h["id"] != self.item_id]
        save_hidden_items(hidden)

        # Button deaktivieren
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.response.send_message(
            f"✅ **{entry['item']}** wurde aus dem Versteck (**{entry['location']}**) geholt.",
            ephemeral=True
        )


# ── Ticket System ──────────────────────────────────────────────────────

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
            discord.SelectOption(
                label="Support",
                emoji="🎟",
                value="support",
                description="Allgemeiner Support"
            ),
            discord.SelectOption(
                label="Highteam Ticket",
                emoji="🎟",
                value="highteam",
                description="Direkter Kontakt zum Highteam"
            ),
            discord.SelectOption(
                label="Fraktions Bewerbung",
                emoji="🎟",
                value="fraktion",
                description="Bewerbung für eine Fraktion"
            ),
            discord.SelectOption(
                label="Beschwerde Ticket",
                emoji="🎟",
                value="beschwerde",
                description="Beschwerde einreichen"
            ),
            discord.SelectOption(
                label="Bug Report",
                emoji="🎟",
                value="bug",
                description="Fehler oder Bug melden"
            ),
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
            await interaction.response.send_message(
                "Du hast dieses Ticket bereits bewertet.", ephemeral=True
            )
            return
        self.rated = True

        star_display = "⭐" * stars + "☆" * (5 - stars)

        thank_embed = discord.Embed(
            title="💙 Danke für deine Bewertung!",
            description=(
                f"Du hast **{star_display}** ({stars}/5) gegeben.\n\n"
                f"Vielen Dank für dein Feedback! Wir arbeiten stets daran unseren Support zu verbessern. "
                f"Wir hoffen dein Anliegen wurde zu deiner Zufriedenheit gelöst."
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.response.send_message(embed=thank_embed)

        log_ch = self.guild_ref.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            rating_embed = discord.Embed(
                title="⭐ Ticket Bewertung",
                description=(
                    f"**Ticket:** {self.channel_name}\n"
                    f"**Typ:** {self.ticket_type}\n"
                    f"**Erstellt von:** {self.creator_name}\n"
                    f"**Bearbeitet von:** {self.handler_name}\n"
                    f"**Bewertung:** {star_display} ({stars}/5)"
                ),
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            await log_ch.send(embed=rating_embed)

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


def guild_member_bot(guild: discord.Guild):
    return guild.me


# ── Events ──────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    global bot_start_time, invite_cache
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")

    bot.add_view(TicketSelectView())
    bot.add_view(TicketActionView())

    # Versteck-Buttons nach Neustart wieder registrieren
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
    bot.add_view(EinreiseView())
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        # Guild-Commands registrieren (sofort aktiv, keine globalen Duplikate)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Slash Commands synced (Guild): {len(synced)}")
        # Alle globalen Commands von Discord entfernen
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("Globale Commands bereinigt")
    except Exception as e:
        print(f"Slash Command sync fehlgeschlagen: {e}")


async def auto_ticket_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(TICKET_SETUP_CHANNEL_ID)
        if not channel:
            continue
        already_posted = False
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
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
            print(f"Lohnliste bereits vorhanden in #{channel.name}")
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
        await message.add_reaction("✅")
    else:
        counting_state["count"] = 0
        counting_state["last_user_id"] = None
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


async def handle_discord_invite(message):
    member = message.author
    guild  = message.guild
    try:
        await message.delete()
    except Exception as e:
        await log_bot_error("Nachricht löschen (Discord Link)", str(e), guild)
    timeout_ok, roles_removed = await apply_timeout_restrictions(
        member, guild, duration_h=300, reason="Fremden Discord-Link gesendet"
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
        timeout_status = "✅ Timeout erteilt (300h)" if timeout_ok else "❌ Timeout fehlgeschlagen — Berechtigung prüfen!"
        rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
        embed = discord.Embed(
            title="🔨 Moderation — Timeout",
            description=(
                f"**Benutzer:** {member.mention} (`{member}`)\n"
                f"**Timeout:** {timeout_status}\n"
                f"**Rollen:** {rollen_status}\n"
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
            description += f"**Invites von {inviter.display_name}:** {inviter_uses}"
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

    # Willkommens-Embed im Welcome-Kanal
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
            await welcome_ch.send(embed=w_embed)
        except Exception:
            pass

    # Nickname setzen
    try:
        await member.edit(nick="RP Name | PSN")
    except Exception:
        pass

    # ── Startguthaben 5.000 💵 ────────────────────────────────────────────
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


# ── Commands ──────────────────────────────────────────────────────────────

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
    """Sendet das Ticket-Embed in den Ticket-Kanal. Nur für Admins."""
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
    view = TicketSelectView()
    await channel.send(embed=embed, view=view)
    try:
        await ctx.message.delete()
    except Exception:
        pass


# ── Economy Slash Commands ───────────────────────────────────────────────

def channel_error(channel_id: int) -> str:
    return f"❌ Du kannst diesen Command nur hier ausführen: <#{channel_id}>"


# /lohn-abholen
@bot.tree.command(name="lohn-abholen", description="Hole deinen stündlichen Lohn ab", guild=discord.Object(id=GUILD_ID))
async def lohn_abholen(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != LOHN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(LOHN_CHANNEL_ID), ephemeral=True)
        return

    main_wages = [WAGE_ROLES[r] for r in role_ids if r in WAGE_ROLES]
    if len(main_wages) > 1:
        await interaction.response.send_message(
            "❌ Du hast mehrere Lohnklassen. Bitte wende dich ans Team.", ephemeral=True
        )
        return
    if not main_wages:
        await interaction.response.send_message(
            "❌ Du hast keine Lohnklasse und kannst keinen Lohn abholen.", ephemeral=True
        )
        return

    total_wage = main_wages[0]
    if ADDITIONAL_WAGE_ROLE_ID in role_ids:
        total_wage += ADDITIONAL_WAGE_ROLE_WAGE

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    now       = datetime.now(timezone.utc)

    if user_data["last_wage"]:
        last = datetime.fromisoformat(user_data["last_wage"])
        diff = (now - last).total_seconds()
        if diff < 3600:
            remaining = int(3600 - diff)
            mins = remaining // 60
            secs = remaining % 60
            await interaction.response.send_message(
                f"❌ Du kannst deinen Lohn erst in **{mins}m {secs}s** wieder abholen.",
                ephemeral=True
            )
            return

    user_data["bank"]      += total_wage
    user_data["last_wage"]  = now.isoformat()
    save_economy(eco)

    embed = discord.Embed(
        title="💵 Lohn abgeholt!",
        description=(
            f"Du hast **{total_wage:,} 💵** auf dein Konto erhalten.\n"
            f"**Kontostand:** {user_data['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=now
    )
    await interaction.response.send_message(embed=embed)


# /kontostand
@bot.tree.command(name="kontostand", description="Zeigt den Kontostand an (Team: auch per @Erwähnung)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Mitglied dessen Kontostand abgerufen werden soll")
async def kontostand(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids  = [r.id for r in interaction.user.roles]
    is_team   = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids

    # @ Option: nur für Teamrollen
    if nutzer is not None:
        if not is_team:
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, den Kontostand anderer Mitglieder abzurufen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    else:
        # Eigener Kontostand: Kanalprüfung & Rollenprüfung
        if not is_team and interaction.channel.id != BANK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
            return
        if not is_team and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
            return
        ziel = interaction.user

    eco       = load_economy()
    user_data = get_user(eco, ziel.id)
    save_economy(eco)

    titel = "💳 Kontostand" if ziel.id == interaction.user.id else f"💳 Kontostand — {ziel.display_name}"
    embed = discord.Embed(
        title=titel,
        description=(
            f"**Bargeld:** {user_data['cash']:,} 💵\n"
            f"**Bank:** {user_data['bank']:,} 💵\n"
            f"**Gesamt:** {user_data['cash'] + user_data['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /einzahlen
@bot.tree.command(name="einzahlen", description="Zahle Bargeld auf dein Bankkonto ein", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wählen oder eingeben (1.000 – 10.000.000 💵)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def einzahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["cash"] < betrag:
        await interaction.response.send_message(
            f"❌ Nicht genug Bargeld. Dein Bargeld: **{user_data['cash']:,} 💵**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - user_data["daily_deposit"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"❌ Tageslimit erreicht. Du kannst heute noch **{remaining:,} 💵** einzahlen. "
                f"(Limit: **{user_limit:,} 💵**)",
                ephemeral=True
            )
            return
        user_data["daily_deposit"] += betrag

    user_data["cash"] -= betrag
    user_data["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Einzahlung",
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} 💵\n"
        f"**Bargeld danach:** {user_data['cash']:,} 💵 | **Bank danach:** {user_data['bank']:,} 💵"
    )

    embed = discord.Embed(
        title="🏦 Eingezahlt",
        description=(
            f"**Eingezahlt:** {betrag:,} 💵\n"
            f"**Bargeld:** {user_data['cash']:,} 💵\n"
            f"**Bank:** {user_data['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /auszahlen
@bot.tree.command(name="auszahlen", description="Hebe Geld von deinem Bankkonto ab", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wählen oder eingeben (1.000 – 10.000.000 💵)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def auszahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["bank"] < betrag:
        await interaction.response.send_message(
            f"❌ Nicht genug Guthaben. Dein Kontostand: **{user_data['bank']:,} 💵**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - user_data["daily_withdraw"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"❌ Tageslimit erreicht. Du kannst heute noch **{remaining:,} 💵** auszahlen. "
                f"(Limit: **{user_limit:,} 💵**)",
                ephemeral=True
            )
            return
        user_data["daily_withdraw"] += betrag

    user_data["bank"] -= betrag
    user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Auszahlung",
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} 💵\n"
        f"**Bargeld danach:** {user_data['cash']:,} 💵 | **Bank danach:** {user_data['bank']:,} 💵"
    )

    embed = discord.Embed(
        title="💸 Ausgezahlt",
        description=(
            f"**Ausgezahlt:** {betrag:,} 💵\n"
            f"**Bargeld:** {user_data['cash']:,} 💵\n"
            f"**Bank:** {user_data['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /überweisen
@bot.tree.command(name="ueberweisen", description="Überweise Geld an einen anderen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Empfänger", betrag="Betrag wählen oder eingeben (1.000 – 10.000.000 💵)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def ueberweisen(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("❌ Du kannst nicht an dich selbst überweisen.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco        = load_economy()
    sender     = get_user(eco, interaction.user.id)
    receiver   = get_user(eco, nutzer.id)
    reset_daily_if_needed(sender)

    if sender["bank"] < betrag:
        await interaction.response.send_message(
            f"❌ Nicht genug Guthaben. Dein Kontostand: **{sender['bank']:,} 💵**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = sender.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - sender["daily_transfer"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"❌ Tageslimit erreicht. Du kannst heute noch **{remaining:,} 💵** überweisen. "
                f"(Limit: **{user_limit:,} 💵**)",
                ephemeral=True
            )
            return
        sender["daily_transfer"] += betrag

    sender["bank"]   -= betrag
    receiver["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Überweisung",
        f"**Von:** {interaction.user.mention} → **An:** {nutzer.mention}\n"
        f"**Betrag:** {betrag:,} 💵 | **Sender-Bank danach:** {sender['bank']:,} 💵"
    )

    embed = discord.Embed(
        title="💳 Überweisung",
        description=(
            f"**An:** {nutzer.mention}\n"
            f"**Betrag:** {betrag:,} 💵\n"
            f"**Dein Kontostand:** {sender['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /shop
@bot.tree.command(name="shop", description="Zeigt den Shop an", guild=discord.Object(id=GUILD_ID))
async def shop(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        return

    items = load_shop()
    if not items:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🛒 Shop",
                description="Der Shop ist aktuell leer.",
                color=LOG_COLOR
            ),
            ephemeral=True
        )
        return

    desc = "\n".join(f"**{item['name']}** — {item['price']:,} 💵" for item in items)
    embed = discord.Embed(
        title="🛒 Shop",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Kaufen mit /buy [itemname] • Nur mit Bargeld möglich")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /buy
@bot.tree.command(name="buy", description="Kaufe ein Item aus dem Shop", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(itemname="Name des Items das du kaufen möchtest")
async def buy(interaction: discord.Interaction, itemname: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    items = load_shop()
    item  = next((i for i in items if i["name"].lower() == itemname.lower()), None)

    if not item:
        await interaction.response.send_message(
            f"❌ Item **{itemname}** wurde nicht gefunden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)

    if user_data["cash"] < item["price"]:
        await interaction.response.send_message(
            f"❌ Du hast nicht genug **Bargeld**.\n"
            f"Preis: **{item['price']:,} 💵** | Dein Bargeld: **{user_data['cash']:,} 💵**\n"
            f"ℹ️ Käufe sind nur mit Bargeld möglich. Hebe Geld mit `/auszahlen` ab.",
            ephemeral=True
        )
        return

    user_data["cash"] -= item["price"]
    if "inventory" not in user_data:
        user_data["inventory"] = []
    user_data["inventory"].append(item["name"])
    save_economy(eco)

    embed = discord.Embed(
        title="✅ Gekauft!",
        description=(
            f"Du hast **{item['name']}** für **{item['price']:,} 💵** gekauft.\n"
            f"**Verbleibendes Bargeld:** {user_data['cash']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /set-limit (Team only)
@bot.tree.command(name="set-limit", description="[TEAM] Setzt das individuelle Tageslimit eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", limit="Neues Tageslimit")
@app_commands.choices(limit=LIMIT_CHOICES)
async def set_limit(interaction: discord.Interaction, nutzer: discord.Member, limit: int):
    role_ids = [r.id for r in interaction.user.roles]
    if ADMIN_ROLE_ID not in role_ids and MOD_ROLE_ID not in role_ids:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["custom_limit"] = limit
    save_economy(eco)

    embed = discord.Embed(
        title="⚙️ Limit gesetzt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Neues Tageslimit:** {limit:,} 💵\n"
            f"*(gilt für Einzahlen, Auszahlen & Überweisen)*"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesetzt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


# /money-add (Admin only)
@bot.tree.command(name="money-add", description="[ADMIN] Füge einem Spieler Geld hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
@app_commands.default_permissions(administrator=True)
async def money_add(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld hinzugefügt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** +{betrag:,} 💵\n"
        f"**Bargeld danach:** {user_data['cash']:,} 💵\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="💰 Geld hinzugefügt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Hinzugefügt:** {betrag:,} 💵\n"
            f"**Bargeld:** {user_data['cash']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /remove-money (Admin only)
@bot.tree.command(name="remove-money", description="[ADMIN] Entferne Geld von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
@app_commands.default_permissions(administrator=True)
async def remove_money(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] = max(0, user_data["cash"] - betrag)
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld entfernt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** -{betrag:,} 💵\n"
        f"**Bargeld danach:** {user_data['cash']:,} 💵\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="💸 Geld entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernt:** {betrag:,} 💵\n"
            f"**Bargeld:** {user_data['cash']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /item-add (Admin only)
@bot.tree.command(name="item-add", description="[ADMIN] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", itemname="Itemname")
@app_commands.default_permissions(administrator=True)
async def item_add(interaction: discord.Interaction, nutzer: discord.Member, itemname: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    if "inventory" not in user_data:
        user_data["inventory"] = []
    user_data["inventory"].append(itemname)
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="📦 Item hinzugefügt",
            description=f"**{itemname}** wurde **{nutzer.mention}** hinzugefügt.",
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        ),
        ephemeral=True
    )


# /remove-item (Admin only)
@bot.tree.command(name="remove-item", description="[ADMIN] Entferne ein Item von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", itemname="Itemname")
@app_commands.default_permissions(administrator=True)
async def remove_item(interaction: discord.Interaction, nutzer: discord.Member, itemname: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inventory = user_data.get("inventory", [])

    if itemname not in inventory:
        await interaction.response.send_message(
            f"❌ **{nutzer.display_name}** besitzt kein Item namens **{itemname}**.", ephemeral=True
        )
        return

    inventory.remove(itemname)
    user_data["inventory"] = inventory
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="📦 Item entfernt",
            description=f"**{itemname}** wurde von **{nutzer.mention}** entfernt.",
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        ),
        ephemeral=True
    )


# /shop-add (Admin only) with confirmation
class ShopAddConfirmView(discord.ui.View):
    def __init__(self, name: str, price: int):
        super().__init__(timeout=60)
        self.name  = name
        self.price = price

    @discord.ui.button(label="✅ Bestätigen", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = load_shop()
        items.append({"name": self.name, "price": self.price})
        save_shop(items)
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Item hinzugefügt",
                description=f"**{self.name}** für **{self.price:,} 💵** wurde zum Shop hinzugefügt.",
                color=LOG_COLOR
            ),
            view=self
        )

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="❌ Abgebrochen",
                description="Das Item wurde nicht hinzugefügt.",
                color=MOD_COLOR
            ),
            view=self
        )


@bot.tree.command(name="shop-add", description="[ADMIN] Füge ein neues Item zum Shop hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(itemname="Name des Items", preis="Preis in $")
@app_commands.default_permissions(administrator=True)
async def shop_add(interaction: discord.Interaction, itemname: str, preis: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    if preis <= 0:
        await interaction.response.send_message("❌ Preis muss größer als 0 sein.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🛒 Neues Item hinzufügen?",
        description=(
            f"**Name:** {itemname}\n"
            f"**Preis:** {preis:,} 💵\n\n"
            f"Bitte bestätige das Hinzufügen."
        ),
        color=LOG_COLOR
    )
    await interaction.response.send_message(embed=embed, view=ShopAddConfirmView(itemname, preis), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════
# WARN SYSTEM
# ═══════════════════════════════════════════════════════════════════════

# /warn (Team only)
@bot.tree.command(name="warn", description="[TEAM] Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)
    warn_entry = {
        "grund":       grund,
        "konsequenz":  konsequenz,
        "warned_by":   interaction.user.id,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }
    user_warns.append(warn_entry)
    save_warns(warns)
    warn_count = len(user_warns)

    embed = discord.Embed(
        title="⚠️ Verwarnung",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Grund:** {grund}\n"
            f"**Konsequenz:** {konsequenz}\n"
            f"**Verwarnt von:** {interaction.user.mention}\n"
            f"**Warns gesamt:** {warn_count}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    log_ch = interaction.guild.get_channel(WARN_LOG_CHANNEL_ID)
    if log_ch:
        await log_ch.send(embed=embed)

    await interaction.response.send_message(
        f"✅ Verwarnung für {nutzer.mention} gespeichert. (Warns gesamt: **{warn_count}**)", ephemeral=True
    )

    # Automatischer Timeout bei 3 Warns
    if warn_count >= WARN_AUTO_TIMEOUT_COUNT:
        timeout_dur = timedelta(days=2)
        try:
            await nutzer.timeout(timeout_dur, reason=f"Automatischer Timeout: {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht")
        except Exception:
            pass
        # Alle Rollen entfernen
        try:
            roles_to_remove = [r for r in nutzer.roles if r != interaction.guild.default_role and not r.managed]
            if roles_to_remove:
                await nutzer.remove_roles(*roles_to_remove, reason="Automatischer Timeout: 3 Warns")
        except Exception:
            pass
        # DM senden
        try:
            dm_embed = discord.Embed(
                title="🔇 Du wurdest getimeoutet",
                description=(
                    f"Du hast auf **{interaction.guild.name}** {WARN_AUTO_TIMEOUT_COUNT} Verwarnungen erhalten "
                    f"und wurdest daher für **2 Tage** getimeoutet.\n\n"
                    f"**Letzte Verwarnung:**\n"
                    f"Grund: {grund}\nKonsequenz: {konsequenz}\n\n"
                    f"Deine Rollen wurden vorübergehend entfernt.\n"
                    f"Nach dem Timeout melde dich bitte bei einem Teammitglied."
                ),
                color=MOD_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            await nutzer.send(embed=dm_embed)
        except Exception:
            pass
        timeout_embed = discord.Embed(
            title="🔇 Automatischer Timeout",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Grund:** {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht\n"
                f"**Dauer:** 2 Tage\n"
                f"**Rollen entfernt:** ✅"
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        if log_ch:
            await log_ch.send(embed=timeout_embed)


# /warn-list
@bot.tree.command(name="warn-list", description="Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def warn_list(interaction: discord.Interaction, nutzer: discord.Member):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"✅ {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        ts  = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** — {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"⚠️ Warns von {nutzer.display_name}",
        description="\n".join(lines),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesamt: {len(user_warns)} Warn(s)")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /remove-warn
@bot.tree.command(name="remove-warn", description="[TEAM] Letzte Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler")
async def remove_warn(interaction: discord.Interaction, nutzer: discord.Member):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"ℹ️ {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_warns(warns)

    embed = discord.Embed(
        title="✅ Verwarnung entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernter Warn:** {removed['grund']}\n"
            f"**Verbleibende Warns:** {len(user_warns)}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════
# INVENTAR SYSTEM
# ═══════════════════════════════════════════════════════════════════════

# /rucksack
@bot.tree.command(name="rucksack", description="Zeige dein Inventar an", guild=discord.Object(id=GUILD_ID))
async def rucksack(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids
    allowed  = is_adm or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES) or MOD_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != RUCKSACK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
        return

    if not allowed:
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    inventory = user_data.get("inventory", [])

    if not inventory:
        desc = "*Dein Rucksack ist leer.*"
    else:
        from collections import Counter
        counts = Counter(inventory)
        desc   = "\n".join(f"• **{item}** ×{count}" for item, count in counts.items())

    embed = discord.Embed(
        title=f"🎒 Rucksack von {interaction.user.display_name}",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /übergeben
@bot.tree.command(name="uebergeben", description="Gib ein Item aus deinem Inventar an jemanden weiter", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Empfänger", item="Name des Items")
async def uebergeben(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != UEBERGEBEN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(UEBERGEBEN_CHANNEL_ID), ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("❌ Du kannst nicht an dich selbst übergeben.", ephemeral=True)
        return

    eco        = load_economy()
    giver_data = get_user(eco, interaction.user.id)
    inv        = giver_data.get("inventory", [])

    item_lower = item.lower()
    match      = next((i for i in inv if i.lower() == item_lower), None)
    if not match:
        await interaction.response.send_message(
            f"❌ **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        return

    inv.remove(match)
    receiver_data = get_user(eco, nutzer.id)
    receiver_data.setdefault("inventory", []).append(match)
    save_economy(eco)

    embed = discord.Embed(
        title="🤝 Item übergeben",
        description=(
            f"**Von:** {interaction.user.mention}\n"
            f"**An:** {nutzer.mention}\n"
            f"**Item:** {match}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /verstecken
@bot.tree.command(name="verstecken", description="Verstecke ein Item aus deinem Inventar", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(item="Name des Items", ort="Wo versteckst du es?")
async def verstecken(interaction: discord.Interaction, item: str, ort: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != VERSTECKEN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(VERSTECKEN_CHANNEL_ID), ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    inv       = user_data.get("inventory", [])

    item_lower = item.lower()
    match      = next((i for i in inv if i.lower() == item_lower), None)
    if not match:
        await interaction.response.send_message(
            f"❌ **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        return

    inv.remove(match)
    save_economy(eco)

    import uuid
    item_id = str(uuid.uuid4())[:8]
    hidden  = load_hidden_items()
    hidden.append({
        "id":       item_id,
        "owner_id": interaction.user.id,
        "item":     match,
        "location": ort,
    })
    save_hidden_items(hidden)

    view = VersteckRetrieveView(item_id, interaction.user.id)
    bot.add_view(view)

    embed = discord.Embed(
        title="🕵️ Item versteckt",
        description=(
            f"**Item:** {match}\n"
            f"**Versteckt an:** {ort}\n\n"
            f"Nur du kannst es wieder herausnehmen."
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, view=view)


# ═══════════════════════════════════════════════════════════════════════
# TEAM ITEM COMMANDS
# ═══════════════════════════════════════════════════════════════════════

# /item-geben (Team only)
@bot.tree.command(name="item-geben", description="[TEAM] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname")
async def item_geben(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data.setdefault("inventory", []).append(item)
    save_economy(eco)

    embed = discord.Embed(
        title="🎁 Item gegeben",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {item}\n"
            f"**Vergeben von:** {interaction.user.mention}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /item-entfernen (Team only)
@bot.tree.command(name="item-entfernen", description="[TEAM] Entferne ein Item von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname")
async def item_entfernen(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inv       = user_data.get("inventory", [])

    item_lower = item.lower()
    match      = next((i for i in inv if i.lower() == item_lower), None)
    if not match:
        await interaction.response.send_message(
            f"❌ **{item}** ist nicht im Inventar von {nutzer.mention}.", ephemeral=True
        )
        return

    inv.remove(match)
    save_economy(eco)

    embed = discord.Embed(
        title="🗑️ Item entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {match}\n"
            f"**Entfernt von:** {interaction.user.mention}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════
# KARTENKONTROLLE
# ═══════════════════════════════════════════════════════════════════════

KARTENKONTROLLE_CHANNEL_ID = 1491116234459185162

@bot.tree.command(name="kartenkontrolle", description="[TEAM] Sendet eine DM-Erinnerung zur Kartenkontrolle an alle Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def kartenkontrolle(interaction: discord.Interaction):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild        = interaction.guild
    channel_link = f"https://discord.com/channels/{guild.id}/{KARTENKONTROLLE_CHANNEL_ID}"

    sent     = 0
    failed   = 0
    for member in guild.members:
        if member.bot:
            continue
        role_ids = [r.id for r in member.roles]
        is_member_role = (
            CITIZEN_ROLE_ID in role_ids
            or any(r in role_ids for r in WAGE_ROLES)
        )
        if not is_member_role:
            continue
        try:
            dm_embed = discord.Embed(
                title="🪪 Kartenkontrolle",
                description=(
                    f"**Hallo {member.display_name}!**\n\n"
                    f"Es findet gerade eine **Kartenkontrolle** statt.\n"
                    f"Bitte begib dich in den Kanal:\n"
                    f"[🔗 Zur Kartenkontrolle]({channel_link})\n\n"
                    f"*Diese Nachricht wurde automatisch durch das Team gesendet.*"
                ),
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            await member.send(embed=dm_embed)
            sent += 1
        except Exception:
            failed += 1

    await interaction.followup.send(
        f"✅ Kartenkontrolle-DM gesendet!\n**Erfolgreich:** {sent} | **Fehlgeschlagen (DMs zu):** {failed}",
        ephemeral=True
    )




# ── Ausweis Helpers ──────────────────────────────────────────────────────────

def load_ausweis():
    if AUSWEIS_FILE.exists():
        with open(AUSWEIS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_ausweis(data):
    with open(AUSWEIS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

import random
import string

def generate_ausweisnummer():
    letters = random.choices(string.ascii_uppercase, k=2)
    digits  = random.choices(string.digits, k=6)
    return "".join(letters) + "-" + "".join(digits)


# ── Einreise Modal 1 ──────────────────────────────────────────────────────────

class EinreiseModal(discord.ui.Modal, title="Ausweis erstellen"):
    vorname       = discord.ui.TextInput(label="Vorname",              placeholder="Max",                  max_length=50)
    nachname      = discord.ui.TextInput(label="Nachname",             placeholder="Mustermann",           max_length=50)
    gebdatum_alter = discord.ui.TextInput(label="Geburtsdatum / Alter", placeholder="TT.MM.JJJJ / 25",   max_length=30)
    nationalitaet = discord.ui.TextInput(label="Nationalitaet",        placeholder="Deutsch",             max_length=50)
    wohnort       = discord.ui.TextInput(label="Wohnort",              placeholder="Los Santos",          max_length=100)

    def __init__(self, einreise_typ: str):
        super().__init__()
        self.einreise_typ = einreise_typ

    async def on_submit(self, interaction: discord.Interaction):
        teile = self.gebdatum_alter.value.split("/")
        geburtsdatum = teile[0].strip() if len(teile) >= 1 else self.gebdatum_alter.value.strip()
        alter        = teile[1].strip() if len(teile) >= 2 else "?"

        ausweisnummer = generate_ausweisnummer()
        typ_label     = "🤵 Legale Einreise" if self.einreise_typ == "legal" else "🥷 Illegale Einreise"
        ausweis_data  = load_ausweis()
        ausweis_data[str(interaction.user.id)] = {
            "vorname":       self.vorname.value,
            "nachname":      self.nachname.value,
            "geburtsdatum":  geburtsdatum,
            "alter":         alter,
            "nationalitaet": self.nationalitaet.value,
            "wohnort":       self.wohnort.value,
            "einreise_typ":  self.einreise_typ,
            "ausweisnummer": ausweisnummer,
            "discord_name":  str(interaction.user),
            "discord_id":    interaction.user.id,
        }
        save_ausweis(ausweis_data)

        # Charakter-Rollen automatisch zuweisen
        member = interaction.guild.get_member(interaction.user.id)
        if member:
            rollen_zu_vergeben = [
                interaction.guild.get_role(rid)
                for rid in CHARAKTER_ROLLEN
                if interaction.guild.get_role(rid) is not None
            ]
            if rollen_zu_vergeben:
                try:
                    await member.add_roles(*rollen_zu_vergeben, reason="Charakter erstellt")
                except discord.Forbidden:
                    pass

        embed = discord.Embed(
            title="🪪 Ausweis ausgestellt",
            description="Dein Ausweis wurde erfolgreich erstellt!",
            color=0x000000,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Name",          value=f"{self.vorname.value} {self.nachname.value}", inline=True)
        embed.add_field(name="Geburtsdatum",  value=geburtsdatum,                                  inline=True)
        embed.add_field(name="Alter",         value=alter,                                         inline=True)
        embed.add_field(name="Nationalitaet", value=self.nationalitaet.value,                      inline=True)
        embed.add_field(name="Wohnort",       value=self.wohnort.value,                            inline=True)
        embed.add_field(name="Einreiseart",   value=typ_label,                                     inline=True)
        embed.add_field(name="Ausweisnummer", value=f"`{ausweisnummer}`",                          inline=False)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Kryptik Roleplay — Ausweis")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Einreise Select Menu ──────────────────────────────────────────────────────

class EinreiseSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Legale Einreise",
                emoji="🤵",
                value="legal",
                description="Einreise als legaler Bewohner"
            ),
            discord.SelectOption(
                label="Illegale Einreise",
                emoji="🥷",
                value="illegal",
                description="Einreise als illegale Person"
            ),
        ]
        super().__init__(
            placeholder="✈️ Wähle deine Einreiseart...",
            options=options,
            custom_id="einreise_select_main"
        )

    async def callback(self, interaction: discord.Interaction):
        member  = interaction.user
        guild   = interaction.guild
        role_ids = [r.id for r in member.roles]

        # Prüfen ob bereits eingereist
        if LEGAL_ROLE_ID in role_ids or ILLEGAL_ROLE_ID in role_ids:
            await interaction.response.send_message(
                "❌ Du hast bereits eine Einreiseart gewählt. Eine Änderung ist nur durch den RP-Tod möglich.",
                ephemeral=True
            )
            return

        typ = self.values[0]
        role_id = LEGAL_ROLE_ID if typ == "legal" else ILLEGAL_ROLE_ID
        role    = guild.get_role(role_id)

        if role:
            try:
                await member.add_roles(role, reason=f"Einreise: {typ}")
            except Exception as e:
                await log_bot_error("Einreise-Rolle vergeben fehlgeschlagen", str(e), guild)

        await interaction.response.send_modal(EinreiseModal(typ))


class EinreiseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EinreiseSelect())


async def auto_einreise_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(EINREISE_CHANNEL_ID)
        if not channel:
            continue
        already_posted = False
        try:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Einreise" in emb.title:
                            already_posted = True
                            break
                if already_posted:
                    break
        except Exception:
            pass
        if already_posted:
            print(f"Einreise-Embed bereits vorhanden in #{channel.name}")
            continue
        embed = discord.Embed(
            title="✈️ Einreise — Kryptik Roleplay",
            description=(
                "🤵‍♂️ **Legale Einreise** 🤵‍♂️\n"
                "Du wirst auf unserem Server als Legale Person einreisen. "
                "Du darfst als Legaler Bewohner keine Illegalen Aktivitäten ausführen.\n\n"
                "🥷 **Illegale Einreise** 🥷\n"
                "Du wirst auf unserem Server als Illegale Person einreisen. "
                "Du darfst keine Staatlichen Berufe ausüben.\n\n"
                "⚠️ **Hinweis** ⚠️\n"
                "Eine Änderung der Einreiseart ist nur durch den RP-Tod deines Charakters möglich."
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Kryptik Roleplay — Einreisesystem")
        try:
            await channel.send(embed=embed, view=EinreiseView())
            print(f"Einreise-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_einreise_setup fehlgeschlagen", str(e), guild)


# ── Abschied Event ────────────────────────────────────────────────────────────

@bot.event
async def on_member_remove(member):
    guild    = member.guild
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
            await goodbye_ch.send(embed=g_embed)
        except Exception:
            pass


# /ausweisen
@bot.tree.command(name="ausweisen", description="Zeige deinen Ausweis vor", guild=discord.Object(id=GUILD_ID))
async def ausweisen(interaction: discord.Interaction):
    if interaction.channel.id != AUSWEIS_CHANNEL_ID and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message(
            f"❌ Diesen Command kannst du nur in <#{AUSWEIS_CHANNEL_ID}> benutzen.", ephemeral=True
        )
        return

    ausweis_data = load_ausweis()
    entry = ausweis_data.get(str(interaction.user.id))

    if not entry:
        await interaction.response.send_message(
            "❌ Du hast noch keinen Ausweis. Wähle zuerst deine Einreiseart und erstelle deinen Ausweis.",
            ephemeral=True
        )
        return

    typ_label = "🤵 Legale Einreise" if entry.get("einreise_typ") == "legal" else "🥷 Illegale Einreise"

    embed = discord.Embed(
        title="🪪 Personalausweis",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="Name",          value=f"{entry['vorname']} {entry['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum",  value=entry["geburtsdatum"],                     inline=True)
    embed.add_field(name="Alter",         value=entry["alter"],                            inline=True)
    embed.add_field(name="Nationalität",  value=entry["nationalitaet"],                    inline=True)
    embed.add_field(name="Wohnort",       value=entry["wohnort"],                          inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                 inline=True)
    embed.add_field(name="Ausweisnummer", value=f"``{entry['ausweisnummer']}``",       inline=False)
    embed.set_footer(text="Kryptik Roleplay — Personalausweis")

    await interaction.response.send_message(embed=embed)



# /ausweis-remove (Admin only)
@bot.tree.command(name="ausweis-remove", description="[ADMIN] Loescht den Ausweis eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler dessen Ausweis geloescht werden soll")
@app_commands.default_permissions(administrator=True)
async def ausweis_remove(interaction: discord.Interaction, nutzer: discord.Member):
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    uid = str(nutzer.id)

    if uid not in ausweis_data:
        await interaction.response.send_message(
            f"❌ {nutzer.mention} hat keinen Ausweis.", ephemeral=True
        )
        return

    del ausweis_data[uid]
    save_ausweis(ausweis_data)

    embed = discord.Embed(
        title="🗑️ Ausweis gelöscht",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Gelöscht von:** {interaction.user.mention}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Admin Ausweis-Erstellen Modal (einzelnes Modal) ───────────────────────────

class AusweisCreateModal(discord.ui.Modal, title="Ausweis erstellen (Admin)"):
    vorname        = discord.ui.TextInput(label="Vorname",              placeholder="Max",               max_length=50)
    nachname       = discord.ui.TextInput(label="Nachname",             placeholder="Mustermann",        max_length=50)
    gebdatum_alter = discord.ui.TextInput(label="Geburtsdatum / Alter", placeholder="TT.MM.JJJJ / 25", max_length=30)
    nationalitaet  = discord.ui.TextInput(label="Nationalitaet",        placeholder="Deutsch",          max_length=50)
    wohnort        = discord.ui.TextInput(label="Wohnort",              placeholder="Los Santos",       max_length=100)

    def __init__(self, target_id: int, einreise_typ: str):
        super().__init__()
        self.target_id    = target_id
        self.einreise_typ = einreise_typ

    async def on_submit(self, interaction: discord.Interaction):
        teile        = self.gebdatum_alter.value.split("/")
        geburtsdatum = teile[0].strip() if len(teile) >= 1 else self.gebdatum_alter.value.strip()
        alter        = teile[1].strip() if len(teile) >= 2 else "?"

        ausweisnummer = generate_ausweisnummer()
        typ_label     = "🤵 Legale Einreise" if self.einreise_typ == "legal" else "🥷 Illegale Einreise"

        ausweis_data = load_ausweis()
        ausweis_data[str(self.target_id)] = {
            "vorname":       self.vorname.value,
            "nachname":      self.nachname.value,
            "geburtsdatum":  geburtsdatum,
            "alter":         alter,
            "nationalitaet": self.nationalitaet.value,
            "wohnort":       self.wohnort.value,
            "einreise_typ":  self.einreise_typ,
            "ausweisnummer": ausweisnummer,
            "erstellt_von":  str(interaction.user),
        }
        save_ausweis(ausweis_data)

        target         = interaction.guild.get_member(self.target_id)
        target_mention = target.mention if target else f"<@{self.target_id}>"

        # Charakter-Rollen automatisch vergeben
        if target:
            rollen_zu_vergeben = [
                interaction.guild.get_role(rid)
                for rid in CHARAKTER_ROLLEN
                if interaction.guild.get_role(rid) is not None
            ]
            if rollen_zu_vergeben:
                try:
                    await target.add_roles(*rollen_zu_vergeben, reason="Charakter erstellt (Admin)")
                except discord.Forbidden:
                    pass

        embed = discord.Embed(
            title="🪪 Ausweis erstellt",
            color=0x000000,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Spieler",       value=target_mention,                                inline=False)
        embed.add_field(name="Name",          value=f"{self.vorname.value} {self.nachname.value}", inline=True)
        embed.add_field(name="Geburtsdatum",  value=geburtsdatum,                                  inline=True)
        embed.add_field(name="Alter",         value=alter,                                         inline=True)
        embed.add_field(name="Nationalitaet", value=self.nationalitaet.value,                      inline=True)
        embed.add_field(name="Wohnort",       value=self.wohnort.value,                            inline=True)
        embed.add_field(name="Einreiseart",   value=typ_label,                                     inline=True)
        embed.add_field(name="Ausweisnummer", value=f"`{ausweisnummer}`",                          inline=False)
        embed.set_footer(text=f"Erstellt von {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class AusweisCreateEinreiseSelect(discord.ui.Select):
    def __init__(self, target_id: int):
        self.target_id = target_id
        options = [
            discord.SelectOption(label="Legale Einreise",   emoji="🤵", value="legal"),
            discord.SelectOption(label="Illegale Einreise", emoji="🥷", value="illegal"),
        ]
        super().__init__(placeholder="Einreiseart wählen...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            AusweisCreateModal(self.target_id, self.values[0])
        )

class AusweisCreateSelectView(discord.ui.View):
    def __init__(self, target_id: int):
        super().__init__(timeout=120)
        self.add_item(AusweisCreateEinreiseSelect(target_id))


# /ausweis-create (Admin only)
@bot.tree.command(name="ausweis-create", description="[ADMIN] Erstellt einen Ausweis fuer einen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler fuer den der Ausweis erstellt wird")
@app_commands.default_permissions(administrator=True)
async def ausweis_create(interaction: discord.Interaction, nutzer: discord.Member):
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    if str(nutzer.id) in ausweis_data:
        await interaction.response.send_message(
            f"❌ {nutzer.mention} hat bereits einen Ausweis. Bitte zuerst mit /ausweis-remove loeschen.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Wähle die Einreiseart für {nutzer.mention}:",
        view=AusweisCreateSelectView(nutzer.id),
        ephemeral=True
    )


token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
