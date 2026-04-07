import os
import io
import json
Discord importieren
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
import asyncio
Import-Traceback

# Sicherheitscheck: Bot läuft NUR auf Railway, nie doppelt in Replit
# Auf Railway wird RAILWAY_ENVIRONMENT automatisch gesetzt
if not os.environ.get("RAILWAY_ENVIRONMENT") and not os.environ.get("FORCE_LOCAL_RUN"):
    print("=" * 60)
    print("STOPP: Bot wurde NICHT gestartet.")
    print("Dieser Bot läuft ausschließlich auf Railway.")
    print("Bitte NICHT in Replit starten – nur auf Railway eingesetzt!")
    print("=" * 60)
    exit(0)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot_start_time = None
invite_cache = {}

ADMIN_ROLE_ID = 1490855702225485936
MOD_ROLE_ID = 1490855703370534965
WHITELIST_ROLE_ID = 1490855725516460234

MOD_LOG_CHANNEL_ID = 1490878132230819840
MESSAGE_LOG_CHANNEL_ID = 1490878135837917234
ROLE_LOG_CHANNEL_ID = 1490878137385619598
MEMBER_LOG_CHANNEL_ID = 1490878134847930368
JOIN_LOG_CHANNEL_ID = 1490878153391083683
BOT_LOG_CHANNEL_ID = 1490878133279264842
MEMES_CHANNEL_ID = 1490882578276810924
GUILD_ID = 1490839259907887239
TICKET_CHANNEL_ID = 1490855943230066818

TICKET_SETUP_CHANNEL_ID = 1490882553559650355
TICKET_CATEGORY_DEFAULT = 1490882554570608751
TICKET_CATEGORY_HIGHTEAM = 1491069210389119016
TICKET_CATEGORY_FRAKTION = 1491069425384685750
TICKET_LOG_CHANNEL_ID = 1490878139306606743

COUNTING_CHANNEL_ID = 1490882580487340044

# — Wirtschaft â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€
LOHNLISTE_CHANNEL_ID = 1490890346668888194
LOHN_CHANNEL_ID = 1490890348254200049
BANK_CHANNEL_ID = 1490890349382734044
SHOP_CHANNEL_ID = 1490890311755628584

CITIZEN_ROLE_ID = 1490855722534310003

Lohnrollen = {
    1490855796932739093: 1500,
    1490855789844234310: 2500,
    1490855790913785886: 3500,
    1490855791953973421: 4500,
    1490855792671461478: 5500,
    1490855793694871595: 6500,
}
ADDITIONAL_WAGE_ROLE_ID = 1490855795360006246
ZUSÄTZLICHER_LOHNROLL-LOHN = 1200

TÄGLICHES_LIMIT = 1_000_000

BETRAG_CHOICES = [
    app_commands.Choice(name="1.000 ðŸ'µ", value=1_000),
    app_commands.Choice(name="5.000 ðŸ'µ", value=5_000),
    app_commands.Choice(name="10.000 ðŸ'µ", value=10_000),
    app_commands.Choice(name="25.000 ðŸ'µ", value=25_000),
    app_commands.Choice(name="50.000 ðŸ'µ", value=50_000),
    app_commands.Choice(name="100.000 ðŸ'µ", value=100_000),
    app_commands.Choice(name="250.000 ðŸ'µ", value=250_000),
    app_commands.Choice(name="500.000 ðŸ'µ", value=500_000),
    app_commands.Choice(name="1.000.000 ðŸ'µ", value=1_000_000),
]

LIMIT_CHOICES = [
    app_commands.Choice(name="1.000.000 ðŸ'µ", value=1_000_000),
    app_commands.Choice(name="2.000.000 ðŸ'µ", value=2_000_000),
    app_commands.Choice(name="3.000.000 ðŸ'µ", value=3_000_000),
    app_commands.Choice(name="4.000.000 ðŸ'µ", value=4_000_000),
    app_commands.Choice(name="5.000.000 ðŸ'µ", value=5_000_000),
    app_commands.Choice(name="6.000.000 ðŸ'µ", value=6_000_000),
    app_commands.Choice(name="7.000.000 ðŸ'µ", value=7_000_000),
    app_commands.Choice(name="8.000.000 ðŸ'µ", value=8_000_000),
    app_commands.Choice(name="9.000.000 ðŸ'µ", value=9_000_000),
    app_commands.Choice(name="10.000.000 ðŸ'µ", value=10_000_000),
]

ECONOMY_FILE = Path(__file__).parent / "economy_data.json"
SHOP_FILE = Path(__file__).parent / "shop_data.json"
WARNS_FILE = Path(__file__).parent / "warns_data.json"
HIDDEN_ITEMS_FILE = Path(__file__).parent / "hidden_items.json"

# Neue Kanal- und Rollen-IDs
WARN_LOG_CHANNEL_ID = 1491113577258684466
MONEY_LOG_CHANNEL_ID = 1490878138429997087
RUCKSACK_CHANNEL_ID = 1490882592445304972
UEBERGEBEN_CHANNEL_ID = 1490882589014364250
VERSTECKEN_CHANNEL_ID = 1490882591023173682
TEAM_CITIZEN_CHANNEL_ID = 1490882591023173682

WARN_AUTO_TIMEOUT_COUNT = 3
START_CASH = 5_000 # Startguthaben für neue Spieler

LOG_COLOR = 0x00BFFF
MOD_COLOR = 0xFF0000

DISCORD_INVITE_RE = re.compile(
    r'(https?://)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com/invite|discord\.com/invite)/\S+',
    re.IGNORECASE
)
URL_RE = re.compile(r'https?://\S+', re.IGNORECASE)

VULGÄRE_WÖRTER = [
    „fotze“, „wichser“, „hurensohn“, „arschloch“, „fick“, „ficken“,
    „neger“, „nigger“, „wichsen“, „schlampe“, „nutte“, „hure“,
    „wixer“, „drecksau“, „scheisskopf“, „pisser“, „dreckssack“,
    „mongo“, „spast“, „vollidiot“, „schwachkopf“, „dreckskerl“,
    „mistkerl“, „penner“, „hurenkind“, „dummficker“, „scheiß“,
]

spam_tracker = {}
spam_warned = set()
ticket_data = {}
counting_state = {"count": 0, "last_user_id": None}
counting_handled = set() # verhindert doppelte Verarbeitung

FUNKTIONEN = {
    "Discord Link Schutz": Wahr,
    "Linkfilter (Memes)": Wahr,
    "Vulgärer Wasserfilter": Wahr,
    "Spamschutz": Stimmt,
    "Nachrichtenlog": Wahr,
    "Bearbeitungslog": True,
    "Rollenlog": Wahr,
    "Mitgliederprotokoll": Wahr,
    "Mitgliedslogbuch + Einladungen": Wahr,
    "Bot Kick": Wahr,
    "Fehlerprotokollierung": Ja,
    „Rollen-Entfernung (Timeout)“: Richtig,
    "Ticketsystem": Wahr,
    "Zähl-Kanal": Wahr,
    "Wirtschaftssystem": Wahr,
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
    für g in guilds_to_check:
        falls nicht g:
            weitermachen
        log_ch = g.get_channel(BOT_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title=f"âš ï¸ Bot Fehler – {title}",
                description=f"```{error_text[:1900]}```",
                Farbe=MOD_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            versuchen:
                await log_ch.send(embed=embed)
            Ausnahme:
                passieren
            brechen

async def send_bot_status():
    für Gilde in bot.guilds:
        log_ch = guild.get_channel(BOT_LOG_CHANNEL_ID)
        falls nicht log_ch:
            weitermachen
        desc = ""
        für Feature, Status in FEATURES.items():
            Emoji = "ðŸŸ¢" wenn Status, sonst "ðŸ”´"
            Status = "Online", falls Status "Online", ansonsten "Offline"
            desc += f"{emoji} **{feature}** — {state}\n"
        embed = discord.Embed(
            title="ðŸ¤– Bot Status – Alle Funktionen",
            Beschreibung=desc,
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        versuchen:
            await log_ch.send(embed=embed)
        Ausnahme:
            passieren

async def apply_timeout_restrictions(member, guild, duration_h=None, duration_m=None, reason="RegelverstoÃŸ"):
    timeout_ok = False
    falls duration_h:
        timeout_until = datetime.now(timezone.utc) + timedelta(hours=duration_h)
    anders:
        timeout_until = datetime.now(timezone.utc) + timedelta(minutes=duration_m)
    versuchen:
        await member.timeout(timeout_until, reason=reason)
        timeout_ok = True
    außer Ausnahme als e:
        await log_bot_error(
            f"Timeout fehlgeschlagen ({reason})",
            f"Benutzer: {member} ({member.id})\nFehler: {e}\n\n"
            f"Mögliche Ursachen:\n"
            f"- Bot hat keine 'Mitglieder moderieren' Berechtigung\n"
            f"- Bot-Rolle ist niedriger als die Ziel-Rolle",
            Gilde
        )
    roles_removed = []
    versuchen:
        zu entfernende Rollen = [
            r für r in member.roles
            if r != guild.default_role and not r.managed
        ]
        falls Rollen_zu_entfernen:
            await member.remove_roles(*roles_to_remove, reason=f"Timeout: {reason}")
            roles_removed = roles_to_remove
    außer Ausnahme als e:
        wait log_bot_error("Rollen entfernen fehlgeschlagen", str(e), guild)
    return timeout_ok, roles_removed


# – Wirtschaftshelfer â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€ â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€

def load_economy():
    if ECONOMY_FILE.exists():
        with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    zurückkehren {}

def save_economy(data):
    with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(data, user_id):
    uid = str(user_id)
    Falls die Benutzer-ID nicht in den Daten enthalten ist:
        data[uid] = {
            "Bargeld": 0,
            "Bank": 0,
            "last_wage": Keine,
            "tägliche Einzahlung": 0,
            "daily_withdraw": 0,
            "tägliche_Überweisungen": 0,
            "daily_reset": Keine,
            "Inventar": [],
            "custom_limit": Keine,
        }
    return data[uid]

def reset_daily_if_needed(user_data):
    jetzt = datetime.now(timezone.utc)
    if user_data.get("daily_reset") is None:
        user_data["daily_reset"] = now.isoformat()
        zurückkehren
    last_reset = datetime.fromisoformat(user_data["daily_reset"])
    if (now - last_reset).total_seconds() >= 86400:
        user_data["daily_deposit"] = 0
        user_data["daily_withdraw"] = 0
        user_data["daily_transfer"] = 0
        user_data["daily_reset"] = now.isoformat()

def load_shop():
    if SHOP_FILE.exists():
        with open(SHOP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    zurückkehren []

def save_shop(items):
    with open(SHOP_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def has_citizen_or_wage(member):
    role_ids = [r.id for r in member.roles]
    zurückkehren (
        CITIZEN_ROLE_ID in role_ids
        oder ADMIN_ROLE_ID in role_ids
        oder any(r in role_ids for r in WAGE_ROLES)
    )

def is_team(member):
    return any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in member.roles)


# – Helfer warnen â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€ â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€

def load_warns():
    if WARNS_FILE.exists():
        with open(WARNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    zurückkehren {}

def save_warns(data):
    with open(WARNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user_warns(warns, user_id):
    return warns.setdefault(str(user_id), [])


# – Helfer für versteckte Gegenstände â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€ â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€

def load_hidden_items():
    if HIDDEN_ITEMS_FILE.exists():
        with open(HIDDEN_ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    zurückkehren []

def save_hidden_items(data):
    with open(HIDDEN_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# — Geldtagebuch-Helfer — ...

async def log_money_action(guild: discord.Guild, title: str, description: str):
    ch = guild.get_channel(MONEY_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title=f"ðŸ'µ {title}",
            Beschreibung=Beschreibung,
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        versuchen:
            await ch.send(embed=embed)
        Ausnahme:
            passieren


# â“€â“€ Betrag Autocomplete (1K–10M, Freitext erlaubt) â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€

BETRAG_SUGGESTIONS = [
    1.000, 5.000, 10.000, 25.000, 50.000
    100.000, 250.000, 500.000, 1.000.000
    2_000_000, 5_000_000, 10_000_000
]

async def betrag_autocomplete(
    Interaktion: discord.Interaktion,
    aktuell: str
) -> list[app_commands.Choice[int]]:
    Auswahlmöglichkeiten = []
    clean = current.replace(".", "").replace(",", "").strip()
    für val in BETRAG_SUGGESTIONS:
        label = f"{val:,} ðŸ'µ".replace(",", ".")
        if clean == "" or clean in str(val) or clean.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=val))
    return choices[:25]


# â“€â“€ Versteck-Button (persistent) â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â ”€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€

class VersteckRetrieveView(discord.ui.View):
    def __init__(self, item_id: str, owner_id: int):
        super().__init__(timeout=None)
        self.item_id = item_id
        self.owner_id = owner_id
        btn = discord.ui.Button(
            label="ðŸ“¦ Aus Versteck holen",
            style=discord.ButtonStyle.green,
            custom_id=f"retrieve_{item_id}_{owner_id}"
        )
        btn.callback = self.retrieve_callback
        self.add_item(btn)

    async def retrieve_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                „â Œ Nur derjenige, der das Item versteckt hat, kann es herausnehmen.“,
                ephemeral=True
            )
            zurückkehren
        versteckt = load_hidden_items()
        Eintrag = nächste((h für h in versteckt, falls h["id"] == self.item_id), None)
        falls kein Eintrag:
            wait interaction.response.send_message("â Œ Item wurde bereits geborgen oder existierte nicht mehr.", ephemeral=True)
            zurückkehren

        # Artikel zurück ins Inventar
        eco = load_economy()
        user_data = get_user(eco, interaction.user.id)
        user_data.setdefault("inventory", []).append(entry["item"])
        save_economy(eco)

        # Verstecktes Element entfernen
        hidden = [h for h in hidden if h["id"] != self.item_id]
        save_hidden_items(hidden)

        # Schaltfläche deaktivieren
        für Kind in Selbst.Kinder:
            Kind.deaktiviert = Wahr
        versuchen:
            await interaction.message.edit(view=self)
        Ausnahme:
            passieren

        await interaction.response.send_message(
            f"âœ… **{entry['item']}** wurde aus dem Versteck (**{entry['location']}**) geholt.",
            ephemeral=True
        )


# — Ticketsystem

TICKET_TYPE_NAMES = {
    "Support": "Support",
    "highteam": "Highteam Ticket",
    "fraktion": "Fraktionsbewerbung",
    „beschwerde“: „Beschwerde-Ticket“,
    "bug": "Fehlerbericht",
}

TICKET_TYPE_CATEGORIES = {
    "support": TICKET_CATEGORY_DEFAULT,
    "highteam": TICKET_CATEGORY_HIGHTEAM,
    "fraktion": TICKET_CATEGORY_FRAKTION,
    "beschwerde": TICKET_CATEGORY_DEFAULT,
    "Bug": TICKET_CATEGORY_DEFAULT,
}


async def create_ticket(interaction: discord.Interaction, ticket_type: str):
    Gilde = Interaktion.Gilde
    Mitglied = Interaktion.Benutzer

    für ch in guild.text_channels:
        data = ticket_data.get(ch.id)
        if data and data["creator_id"] == member.id:
            await interaction.response.send_message(
                „â Œ Du hast bereits ein offenes Ticket!“, ephemeral=True
            )
            zurückkehren

    type_name = TICKET_TYPE_NAMES.get(ticket_type, ticket_type)
    category_id = TICKET_TYPE_CATEGORIES.get(ticket_type, TICKET_CATEGORY_DEFAULT)
    Kategorie = Gilde.get_channel(Kategorie_ID)
    admin_role = guild.get_role(ADMIN_ROLE_ID)
    mod_role = guild.get_role(MOD_ROLE_ID)

    Überschreibt = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        Mitglied: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            manage_channels=True, manage_messages=True
        ),
    }
    falls Administratorrolle:
        overwrites[admin_role] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            manage_channels=True, manage_messages=True
        )
    if mod_role:
        overwrites[mod_role] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            manage_channels=True, manage_messages=True
        )

    safe_name = member.name[:15].lower().replace(" ", "-")
    channel_name = f"ticket-{ticket_type}-{safe_name}"

    versuchen:
        Kanal = await guild.create_text_channel(
            Name=Kanalname,
            Kategorie=Kategorie,
            überschreibt=überschreibt,
            topic=f"Ticket von {member} ({member.id}) | Typ: {type_name}"
        )
    außer Ausnahme als e:
        await interaction.response.send_message(
            „â Œ Ticket konnte nicht erstellt werden.“, ephemeral=True
        )
        wait log_bot_error("Ticket erstellen fehlgeschlagen", str(e), guild)
        zurückkehren

    ticket_data[channel.id] = {
        "creator_id": member.id,
        "creator_name": str(member),
        "type": ticket_type,
        "type_name": type_name,
        "Handler": Keine,
        "handler_id": None,
        "opened_at": datetime.now(timezone.utc).isoformat(),
    }

    team_mentions = ""
    falls Administratorrolle:
        team_mentions += admin_role.mention + " "
    if mod_role:
        team_mentions += mod_role.mention

    welcome_embed = discord.Embed(
        title=f"ðŸŽŸ {type_name}",
        Beschreibung=(
            f"Willkommen {member.mention}!\n\n"
            f"Dein Ticket wurde erfolgreich erstellt. Das Team wird sich schnellstmöglich um dein Anliegen kümmern.\n\n"
            f"**Ticket-Typ:** {type_name}\n"
            f"**Erstellt von:** {member.mention}\n"
            f"**Erstellt am:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    Welcome_embed.set_footer(text="Nur Teammitglieder können das Ticket gewinnen")

    action_view = TicketActionView()
    await channel.send(content=team_mentions, embed=welcome_embed, view=action_view)

    await interaction.response.send_message(
        f"âœ… Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True
    )

    log_ch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="ðŸ“‚ Ticket GeÃ¶ffnet",
            Beschreibung=(
                f"**Benutzer:** {member.mention} (`{member}`)\n"
                f"**Typ:** {type_name}\n"
                f"**Kanal:** {channel.mention}"
            ),
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await log_ch.send(embed=log_embed)


class TicketSelect(discord.ui.Select):
    def __init__(self):
        Optionen = [
            discord.SelectOption(
                label="Support",
                emoji="ðŸŽŸ",
                Wert="Unterstützung",
                description="Allgemeiner Support"
            ),
            discord.SelectOption(
                label="Highteam-Ticket",
                emoji="ðŸŽŸ",
                Wert="highteam",
                description="Direktor Kontakt zum Highteam"
            ),
            discord.SelectOption(
                label="Fraktionen Bewerbung",
                emoji="ðŸŽŸ",
                Wert="Fraktion",
                description="Bewerbung für eine Fraktion"
            ),
            discord.SelectOption(
                label="Beschwerde Ticket",
                emoji="ðŸŽŸ",
                Wert="beschwerde",
                description="Beschwerde einreichen"
            ),
            discord.SelectOption(
                label="Fehlerbericht",
                emoji="ðŸŽŸ",
                Wert="Bug",
                description="Fehler oder Bug melden"
            ),
        ]
        super().__init__(
            placeholder="ðŸŽŸ Wähle eine Ticket-Art aus...",
            Optionen=Optionen,
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
        Benutzer = self.values[0]
        Kanal = Interaktion.Kanal
        versuchen:
            await channel.set_permissions(
                Benutzer,
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        außer Ausnahme als e:
            await interaction.response.send_message(
                „â Œ Berechtigung konnte nicht gesetzt werden.“, ephemeral=True
            )
            wait log_bot_error("Ticket-Zuweisung fehlgeschlagen", str(e), interaction.guild)
            zurückkehren

        if channel.id in ticket_data:
            ticket_data[channel.id]["handler"] = str(user)
            ticket_data[channel.id]["handler_id"] = user.id

        assign_embed = discord.Embed(
            Beschreibung=(
                f"ðŸ'¤ {user.mention} wurde dem Ticket zugewiesen.\n"
                f"**Zugewiesen von:** {interaction.user.mention}"
            ),
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await channel.send(embed=assign_embed)
        await interaction.response.send_message(
            f"âœ… {user.mention} wurde dem Ticket zugewiesen.", ephemeral=True
        )


class AssignView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(AssignUserSelect())


class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ticket schlieÃŸen",
        style=discord.ButtonStyle.red,
        emoji="ðŸ”'",
        custom_id="ticket_close_btn"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                „â Œ Nur Teammitglieder können Tickets gewinnen.“, ephemeral=True
            )
            zurückkehren

        Kanal = Interaktion.Kanal
        data = ticket_data.get(channel.id)
        Falls keine Daten vorliegen:
            await interaction.response.send_message(
                „â Œ Ticket-Daten nicht gefunden.“, ephemeral=True
            )
            zurückkehren

        await interaction.response.defer(ephemeral=True)

        ticket_data[channel.id]["handler"] = str(interaction.user)
        ticket_data[channel.id]["handler_id"] = interaction.user.id

        closing_embed = discord.Embed(
            title="ðŸ"' Ticket wird geschlossen...“,
            description="Das Ticket wird in wenigen Sekunden geschlossen.",
            Farbe=MOD_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await channel.send(embed=closing_embed)

        Transkriptzeilen = [
            f"=== Ticket Transkript: {data['type_name']} ===",
            f"Erstellt von: {data['creator_name']}",
            f"Bearbeitet von: {str(interaction.user)}",
            f"Datum : {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')} UTC",
            "=" * 55,
            ""
        ]
        versuchen:
            async for msg in channel.history(limit=500, oldest_first=True):
                if msg.author == interaction.guild.me:
                    weitermachen
                ts = msg.created_at.strftime("%d.%m.%Y %H:%M")
                if msg.content:
                    transcript_lines.append(f"[{ts}] {msg.author}: {msg.content}")
                für emb in msg.embeds:
                    if emb.title:
                        transcript_lines.append(f"[{ts}] {msg.author} [Embed-Titel]: {emb.title}")
                    if emb.description:
                        short = emb.description[:300].replace("\n", " ")
                        transcript_lines.append(f" → {short}")
        Ausnahme:
            transcript_lines.append("(Transkript konnte nicht vollständig geladen werden)")

        transcript_text = "\n".join(transcript_lines)
        transcript_file = discord.File(
            fp=io.BytesIO(transcript_text.encode("utf-8")),
            filename=f"transkript-{channel.name}.txt"
        )

        log_ch = interaction.guild.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            closed_embed = discord.Embed(
                title="ðŸ“ Ticket geschlossen",
                Beschreibung=(
                    f"**Benutzer:** <@{data['creator_id']}> (`{data['creator_name']}`)\n"
                    f"**Typ:** {data['type_name']}\n"
                    f"**Geschlossen von:** {interaction.user.mention} (`{interaction.user}`)\n"
                    f"**Kanal:** #{channel.name}"
                ),
                Farbe=LOG_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            await log_ch.send(embed=closed_embed, file=transcript_file)

        creator = interaction.guild.get_member(data["creator_id"])
        wenn Ersteller:
            versuchen:
                dm_embed = discord.Embed(
                    title="ðŸŽŸ Dein Ticket wurde geschlossen",
                    Beschreibung=(
                        f"Dein **{data['type_name']}** auf **Cryptik Roleplay** wurde geschlossen.\n\n"
                        f"**Bearbeitet von:** {interaction.user.display_name}\n\n"
                        f"Wie zufrieden warst du mit der Bearbeitung?\n"
                        f"Bitte bewerte unseren Support:"
                    ),
                    Farbe=LOG_COLOR,
                    Zeitstempel=datetime.now(timezone.utc)
                )
                Bewertungsansicht = Bewertungsansicht(
                    Kanalname=Kanal.name,
                    handler_name=interaction.user.display_name,
                    handler_id=interaction.user.id,
                    ticket_type=data["type_name"],
                    creator_name=data["creator_name"],
                    guild=interaction.guild
                )
                await creator.send(embed=dm_embed, view=rating_view)
            Ausnahme:
                passieren

        ticket_data.pop(channel.id, None)
        await asyncio.sleep(3)
        versuchen:
            Warten Sie aufchannel.delete(reason="Ticket geschlossen")
        außer Ausnahme als e:
            wait log_bot_error("Ticket löschen fehlgeschlagen", str(e), interaction.guild)

    @discord.ui.button(
        label="Person empf",
        style=discord.ButtonStyle.blurple,
        emoji="ðŸ'¤",
        custom_id="ticket_assign_btn"
    )
    async def assign_person(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                „â Œ Nur Teammitglieder können Personen zuweisen.“, ephemeral=True
            )
            zurückkehren
        assign_view = AssignView()
        await interaction.response.send_message(
            „Wähle eine Person aus dem Ticket zugewiesen werden soll:“,
            view=assign_view,
            ephemeral=True
        )


class RatingView(discord.ui.View):
    def __init__(self, channel_name, handler_name, handler_id, ticket_type, creator_name, guild):
        super().__init__(timeout=604800)
        self.channel_name = channel_name
        self.handler_name = handler_name
        self.handler_id = handler_id
        self.ticket_type = ticket_type
        self.creator_name = creator_name
        self.guild_ref = guild
        selbst.bewertet = Falsch

    async def submit_rating(self, interaction: discord.Interaction, stars: int):
        falls selbstbewertet:
            await interaction.response.send_message(
                „Du hast dieses Ticket bereits bewertet.“, ephemeral=True
            )
            zurückkehren
        Selbstbewertung = Wahr

        star_display = "â " * Sterne + "★" * (5 - Sterne)

        thank_embed = discord.Embed(
            title="ðŸ'™ Danke für deine Bewertung!",
            Beschreibung=(
                f"Du hast **{star_display}** ({stars}/5) gegeben.\n\n"
                „Vielen Dank für Ihr Feedback! Wir arbeiten stets daran, unseren Support zu verbessern.“
                f „Wir hoffen, dass dein Anliegen zu deiner Zufriedenheit gelösst.“
            ),
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await interaction.response.send_message(embed=thank_embed)

        log_ch = self.guild_ref.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            rating_embed = discord.Embed(
                title="â Ticketbewertung",
                Beschreibung=(
                    f"**Ticket:** {self.channel_name}\n"
                    f"**Typ:** {self.ticket_type}\n"
                    f"**Erstellt von:** {self.creator_name}\n"
                    f"**Bearbeitet von:** {self.handler_name}\n"
                    f"**Bewertung:** {star_display} ({stars}/5)"
                ),
                Farbe=LOG_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            await log_ch.send(embed=rating_embed)

        für Element in self.children:
            item.disabled = True
        versuchen:
            await interaction.message.edit(view=self)
        Ausnahme:
            passieren

    @discord.ui.button(label="â 1", style=discord.ButtonStyle.grey, custom_id="rating_1")
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 1)

    @discord.ui.button(label="â 2", style=discord.ButtonStyle.grey, custom_id="rating_2")
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 2)

    @discord.ui.button(label="â 3", style=discord.ButtonStyle.grey, custom_id="rating_3")
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 3)

    @discord.ui.button(label="â 4", style=discord.ButtonStyle.grey, custom_id="rating_4")
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 4)

    @discord.ui.button(label="â 5", style=discord.ButtonStyle.green, custom_id="rating_5")
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 5)


def guild_member_bot(guild: discord.Guild):
    return guild.me


# — Veranstaltungen â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€

@bot.event
async def on_ready():
    global bot_start_time, invite_cache
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")

    bot.add_view(TicketSelectView())
    bot.add_view(TicketActionView())

    # Versteck-Buttons nach Neustart wieder registrieren
    für jeden Eintrag in load_hidden_items():
        bot.add_view(VersteckRetrieveView(entry["id"], entry["owner_id"]))

    für Gilde in bot.guilds:
        versuchen:
            Einladungen = await guild.fetch_invites()
            invite_cache[guild.id] = {inv.code: inv for inv in invites}
        Ausnahme:
            passieren

    await auto_ticket_setup()
    await auto_lohnliste_setup()
    await send_bot_status()
    versuchen:
        guild_obj = discord.Object(id=GUILD_ID)
        # Guild-Commands registrieren (sofort aktiv, keine globale Duplikate)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Slash-Befehle synchronisiert (Gilde): {len(synced)}")
        # Alle globalen Befehle von Discord entfernen
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("Globale Befehle gelöscht")
    außer Ausnahme als e:
        print(f"Slash Command sync fehlgeschlagen: {e}")


async def auto_ticket_setup():
    für Gilde in bot.guilds:
        Kanal = guild.get_channel(TICKET_SETUP_CHANNEL_ID)
        falls nicht Kanal:
            weitermachen
        bereits_gepostet = False
        versuchen:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    für emb in msg.embeds:
                        if emb.title and "Ticket erstellen" in emb.title:
                            bereits_gepostet = Wahr
                            brechen
                falls bereits gepostet:
                    brechen
        Ausnahme:
            passieren
        falls bereits gepostet:
            print(f"Ticket-Embed bereits vorhanden in #{channel.name} – kein erneutes Posten.")
            weitermachen
        embed = discord.Embed(
            title="ðŸŽŸ Support – Ticket erstellen",
            Beschreibung=(
                „Benötigt du Hilfe oder möchtest du einen Betroffenen melden?\n\n“
                „Wähle unten im Menü die passende Ticket-Art aus.\n“
                „Unser Team wird sich schnellstmöglich um dich kümmern.\n\n“
                „**Verfügbare Ticket-Arten:**\n“
                „ðŸŽŸ **Support** – Allgemeiner Support\n“
                „ðŸŽŸ **Highteam Ticket** – Direkter Kontakt zum Highteam\n“
                „ðŸŽŸ **Fraktions Bewerbung** – Bewirb dich für eine Fraktion\n“
                „ðŸŽŸ **Beschwerde Ticket** – Beschwerde einreichen\n“
                „ðŸŽŸ **Bug Report** – Fehler oder Bug melden“
            ),
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Cryptik Roleplay — Supportsystem")
        versuchen:
            await channel.send(embed=embed, view=TicketSelectView())
            print(f"Ticket-Embed automatisch gepostet in #{channel.name}")
        außer Ausnahme als e:
            wait log_bot_error("auto_ticket_setup fehlgeschlagen", str(e), guild)


async def auto_lohnliste_setup():
    für Gilde in bot.guilds:
        Kanal = guild.get_channel(LOHNLISTE_CHANNEL_ID)
        falls nicht Kanal:
            weitermachen
        bereits_gepostet = False
        versuchen:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    für emb in msg.embeds:
                        if emb.title and "Lohnliste" in emb.title:
                            bereits_gepostet = Wahr
                            brechen
                falls bereits gepostet:
                    brechen
        Ausnahme:
            passieren
        falls bereits gepostet:
            print(f"Lohnliste bereits vorhanden in #{channel.name}")
            weitermachen
        desc = (
            f"<@&1490855796932739093>\n**1.500 ðŸ'µ Stü¼ndlich**\n\n"
            f"<@&1490855789844234310>\n**2.500 ðŸ'µ Stü¼ndlich**\n\n"
            f"<@&1490855790913785886>\n**3.500 ðŸ'µ Stü¼ndlich**\n\n"
            f"<@&1490855791953973421>\n**4.500 ðŸ'µ Stü¼ndlich**\n\n"
            f"<@&1490855792671461478>\n**5.500 ðŸ'µ Stü¼ndlich**\n\n"
            f"<@&1490855793694871595>\n**6.500 ðŸ'µ Stü¼ndlich**\n\n"
            f"<@&1490855795360006246>\n**1.200 ðŸ'µ Stündlich** *(Zusatzlohn)*"
        )
        embed = discord.Embed(
            title="ðŸ'µ Lohnliste ðŸ'µ",
            Beschreibung=desc,
            Farbe=LOG_COLOR
        )
        versuchen:
            await channel.send(embed=embed)
            print(f"Lohnliste automatisch gepostet in #{channel.name}")
        außer Ausnahme als e:
            wait log_bot_error("auto_lohnliste_setup fehlgeschlagen", str(e), guild)


@bot.event
async def on_error(event, *args, **kwargs):
    err = traceback.format_exc()
    await log_bot_error(f"Event: {event}", err)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        zurückkehren
    if isinstance(error, (commands.MissingRole, commands.CheckFailure)):
        zurückkehren
    err = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    await log_bot_error(f"Command: {ctx.command}", err, ctx.guild)


@bot.event
async def on_message(message):
    if message.author.bot:
        zurückkehren
    if bot_start_time and message.created_at < bot_start_time:
        zurückkehren
    Mitglied = Nachricht.Autor

    if message.channel.id == COUNTING_CHANNEL_ID:
        await handle_counting(message)
        zurückkehren

    if not is_admin(member) and DISCORD_INVITE_RE.search(message.content):
        await handle_discord_invite(message)
        zurückkehren
    if not is_mod_or_admin(member) and message.channel.id != MEMES_CHANNEL_ID:
        if URL_RE.search(message.content):
            await handle_link_outside_memes(message)
            zurückkehren
    if not is_mod_or_admin(member) and contains_vulg(message.content):
        await handle_vulgar_message(message)
        zurückkehren
    await check_spam(message)
    await bot.process_commands(message)


async def handle_counting(message):
    if message.id in counting_handled:
        zurückkehren
    counting_handled.add(message.id)
    if len(counting_handled) > 200:
        älteste = Liste(counting_handled)[:100]
        für Mitte in älteste:
            counting_handled.discard(mid)

    content = message.content.strip()
    versuchen:
        Zahl = int(Inhalt)
    außer ValueError:
        versuchen:
            await message.delete()
        Ausnahme:
            passieren
        versuchen:
            await message.channel.send(
                f"â Œ {message.author.mention} Nur Zahlen sind hier erlaubt! Der Zähler geht weiter bei **{counting_state['count'] + 1}**.",
                delete_after=5
            )
        Ausnahme:
            passieren
        zurückkehren

    erwartet = Zählzustand["Anzahl"] + 1

    if counting_state["last_user_id"] == message.author.id:
        versuchen:
            await message.delete()
        Ausnahme:
            passieren
        versuchen:
            await message.channel.send(
                f"â Œ {message.author.mention} Du kannst nicht zweimal hintereinander zählen! Der Zähler steht bei **{counting_state['count']}**.",
                delete_after=5
            )
        Ausnahme:
            passieren
        zurückkehren

    Wenn die Zahl dem Erwartungswert entspricht:
        counting_state["count"] = Zahl
        counting_state["last_user_id"] = message.author.id
        await message.add_reaction("✓…")
    anders:
        counting_state["count"] = 0
        counting_state["last_user_id"] = None
        versuchen:
            await message.delete()
        Ausnahme:
            passieren
        versuchen:
            await message.channel.send(
                f"â Œ {message.author.mention} Falsche Zahl! Erwartet wurde **{expected}**, nicht **{number}**.\n"
                f"Der Zähler wurde zurückgesetzt. Fangt wieder bei **1** an!",
                delete_after=8
            )
        Ausnahme:
            passieren


async def handle_discord_invite(message):
    Mitglied = Nachricht.Autor
    Gilde = Nachricht.Gilde
    versuchen:
        await message.delete()
    außer Ausnahme als e:
        wait log_bot_error("Nachricht löschen (Discord Link)", str(e), guild)
    timeout_ok, roles_removed = await apply_timeout_restrictions(
        Mitglied, Gilde, Dauer_h=300, Grund="Fremden Discord-Link gesendet"
    )
    versuchen:
        embed = discord.Embed(
            Beschreibung=(
                "> Du hast gegen unsere Server Regeln verstoßen\n\n"
                „> Bitte wende dich an den Support“
            ),
            Farbe=MOD_COLOR
        )
        await member.send(content=member.mention, embed=embed)
    Ausnahme:
        passieren
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        timeout_status = "âœ… Timeout erteilt (300h)" if timeout_ok else "â Œ Timeout fehlgeschlagen – Berechtigung prüfen!"
        rollen_status = f"Entfernt: {', '.join(r.name for r in Roles_removed)}" if Roles_removed else "Keine Rollen entfernt"
        embed = discord.Embed(
            title="ðŸ”¨ Moderation — Timeout",
            Beschreibung=(
                f"**Benutzer:** {member.mention} (`{member}`)\n"
                f"**Timeout:** {timeout_status}\n"
                f"**Rollen:** {rollen_status}\n"
                f"**Grund:** Fremden Discord-Link gesendet\n"
                f"**Kanal:** {message.channel.mention}\n"
                f"**Nachricht:** {message.content[:300]}"
            ),
            Farbe=MOD_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await log_ch.send(embed=embed)


async def handle_link_outside_memes(message):
    versuchen:
        await message.delete()
    Ausnahme:
        passieren
    versuchen:
        await message.channel.send(
            f"{message.author.mention} Bitte senden Sie Links ausschließlich im <#{MEMES_CHANNEL_ID}> Kanal",
            delete_after=6
        )
    Ausnahme:
        passieren


async def handle_vulgar_message(message):
    versuchen:
        await message.delete()
    Ausnahme:
        passieren
    versuchen:
        embed = discord.Embed(
            Beschreibung=(
                "> **Verwarnung:** Du hast einen vulgären Ausdruck verwendet.\n\n"
                "> Bitte beachte unsere Serverregeln. Bei weiteren Verstößen folgen Konsequenzen."
            ),
            Farbe=MOD_COLOR
        )
        await message.author.send(content=message.author.mention, embed=embed)
    Ausnahme:
        passieren
    log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="ðŸ"¨ Moderation – Vulgäre Sprache",
            Beschreibung=(
                f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
                f"**Kanal:** {message.channel.mention}\n"
                f"**Nachricht:** {message.content[:300]}"
            ),
            Farbe=MOD_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await log_ch.send(embed=embed)


async def check_spam(message):
    Benutzer-ID = Nachricht.Autor-ID
    jetzt = datetime.now(timezone.utc)
    Falls die Benutzer-ID nicht im Spam-Tracker enthalten ist:
        spam_tracker[user_id] = []
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if (now - t).total_seconds() < 5]
    spam_tracker[user_id].append(now)
    Anzahl = Länge(spam_tracker[user_id])
    Wenn count >= 5 und user_id in spam_warned enthalten ist:
        spam_tracker[user_id] = []
        spam_warned.discard(user_id)
        versuchen:
            await message.channel.purge(limit=50, check=lambda m: m.author.id == user_id)
        Ausnahme:
            passieren
        timeout_ok, roles_removed = await apply_timeout_restrictions(
            message.author, message.guild, duration_m=10, reason="Wiederholtes Spammen"
        )
        versuchen:
            embed = discord.Embed(
                description="> Du wurdest aufgrund von wiederholtem Spammen für **10 Minuten** stummgeschaltet.",
                Farbe=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        Ausnahme:
            passieren
        log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            timeout_status = "âœ… Timeout erteilt (10min)" if timeout_ok else "â Œ Timeout fehlgeschlagen – Berechtigung prüfen!"
            rollen_status = f"Entfernt: {', '.join(r.name for r in Roles_removed)}" if Roles_removed else "Keine Rollen entfernt"
            embed = discord.Embed(
                title="ðŸ”¨ Moderation — Timeout (Spam)",
                Beschreibung=(
                    f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
                    f"**Timeout:** {timeout_status}\n"
                    f"**Rollen:** {rollen_status}\n"
                    f"**Grund:** Wiederholtes Spammen"
                ),
                Farbe=MOD_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            await log_ch.send(embed=embed)
    elif count >= 5 and user_id not in spam_warned:
        spam_tracker[user_id] = []
        spam_warned.add(user_id)
        versuchen:
            await message.channel.purge(limit=50, check=lambda m: m.author.id == user_id)
        Ausnahme:
            passieren
        versuchen:
            embed = discord.Embed(
                Beschreibung=(
                    „> **Verwarnung:** Bitte vermeide es zu spammen.\n\n“
                    "> Bei Wiederholung erhältst du einen 10 Minuten Timeout."
                ),
                Farbe=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        Ausnahme:
            passieren


@bot.event
async def on_message_delete(message):
    if not message.guild or message.author.bot:
        zurückkehren
    log_ch = message.guild.get_channel(MESSAGE_LOG_CHANNEL_ID)
    falls nicht log_ch:
        zurückkehren
    embed = discord.Embed(
        title="ðŸ—'ï¸ Nachricht gelöscht",
        Beschreibung=(
            f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
            f"**Kanal:** {message.channel.mention}\n"
            f"**Inhalt:** {message.content[:500] if message.content else '*Kein Text*'}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)


@bot.event
async def on_message_edit(before, after):
    if not before.guild or before.author.bot:
        zurückkehren
    Wenn before.content == after.content:
        zurückkehren
    log_ch = before.guild.get_channel(MESSAGE_LOG_CHANNEL_ID)
    falls nicht log_ch:
        zurückkehren
    embed = discord.Embed(
        title="âœ ï¸ Nachricht bearbeitet",
        Beschreibung=(
            f"**Benutzer:** {before.author.mention} (`{before.author}`)\n"
            f"**Kanal:** {before.channel.mention}\n"
            f"**Vorher:** {before.content[:250] if before.content else '*Kein Text*'}\n"
            f"**Nachher:** {after.content[:250] if after.content else '*Kein Text*'}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)


@bot.event
async def on_member_update(before, after):
    if before.roles == after.roles:
        zurückkehren
    Gilde = nach.Gilde
    log_ch = guild.get_channel(ROLE_LOG_CHANNEL_ID)
    falls nicht log_ch:
        zurückkehren
    hinzugefügt = [r für r in nach.Rollen falls r nicht in vor.Rollen]
    entfernt = [r für r in vorher.Rollen falls r nicht in nachher.Rollen]
    falls nicht hinzugefügt und nicht entfernt:
        zurückkehren
    description = f"**Benutzer:** {after.mention} (`{after}`)\n"
    falls hinzugefügt:
        description += f"**HinzugefÃ¼gt:** {', '.join(r.mention for r in added)}\n"
    falls entfernt:
        description += f"**Entfernt:** {', '.join(r.mention for r in removed)}\n"
    versuchen:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == after.id:
                description += f"**Geändert von:** {entry.user.mention} (`{entry.user}`)"
                brechen
    Ausnahme:
        passieren
    embed = discord.Embed(
        title="ðŸŽ Rollen geändert",
        Beschreibung=Beschreibung,
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)


@bot.event
async def on_member_ban(guild, user):
    log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    falls nicht log_ch:
        zurückkehren
    reason = "Kein Grund angegeben"
    Banner = Keine
    versuchen:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                Grund = Eintrag.Grund oder Grund
                Banner = Eintrag.Benutzer
                brechen
    Ausnahme:
        passieren
    description = f"**Benutzer:** {user.mention} (`{user}`)\n**Grund:** {reason}"
    Banner:
        description += f"\n**Gebannt von:** {banner.mention} (`{banner}`)"
    embed = discord.Embed(
        title="ðŸ"¨ Mitglied gegeben",
        Beschreibung=Beschreibung,
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)


@bot.event
async def on_member_remove(member):
    Gilde = Mitglied.Gilde
    log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    falls nicht log_ch:
        zurückkehren
    await asyncio.sleep(1)
    Aktion = "verlassen"
    mod = None
    Grund = Keiner
    versuchen:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                Aktion = "gekickt"
                mod = entry.user
                reason = enter.reason oder „Kein Grund angegeben“
                brechen
    Ausnahme:
        passieren
    versuchen:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.ban):
            if entry.target.id == member.id:
                zurückkehren
    Ausnahme:
        passieren
    description = f"**Benutzer:** {member.mention} (`{member}`)\n**Aktion:** {action}"
    falls Mod:
        description += f"\n**Von:** {mod.mention} (`{mod}`)"
    Grund:
        Beschreibung += f"\n**Grund:** {Grund}"
    title = "ðŸ'¢ Mitglied gekickt" if action == "gekickt" else "ðŸšª Mitglied hat den Server verlassen"
    embed = discord.Embed(
        Titel=Titel,
        Beschreibung=Beschreibung,
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)


@bot.event
async def on_invite_create(invite):
    Gilde = invite.guild
    Falls guild.id nicht im invite_cache enthalten ist:
        invite_cache[guild.id] = {}
    invite_cache[guild.id][invite.code] = invite


@bot.event
async def on_invite_delete(invite):
    Gilde = invite.guild
    if guild.id in invite_cache and invite.code in invite_cache[guild.id]:
        del invite_cache[guild.id][invite.code]


@bot.event
async def on_member_join(member):
    Gilde = Mitglied.Gilde
    if member.bot:
        versuchen:
            wait member.kick(reason="Bots sind auf diesem Server nicht erlaubt")
        Ausnahme:
            passieren
        versuchen:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    embed = discord.Embed(
                        description="> Bots auf diesen Server hinzufügen ist für dich leider nicht erlaubt.",
                        Farbe=MOD_COLOR
                    )
                    versuchen:
                        await entry.user.send(content=entry.user.mention, embed=embed)
                    Ausnahme:
                        passieren
                    brechen
        Ausnahme:
            passieren
        zurückkehren

    member_log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if member_log_ch:
        embed = discord.Embed(
            title="âœ… Mitglied beigetreten",
            description=f"**Benutzer:** {member.mention} (`{member}`)",
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await member_log_ch.send(embed=embed)

    Einladender = Keine
    inviter_uses = 0
    versuchen:
        new_invites = await guild.fetch_invites()
        new_invites_map = {inv.code: inv for inv in new_invites}
        old_invite_map = invite_cache.get(guild.id, {})
        for code, new_inv in new_invite_map.items():
            old_inv = old_invite_map.get(code)
            if old_inv and new_inv.uses > old_inv.uses:
                Einladender = new_inv.inviter
                inviter_uses = new_inv.uses
                brechen
        falls nicht der Einladende:
            for code, old_inv in old_invite_map.items():
                Falls der Code nicht in new_invite_map enthalten ist:
                    Einladender = alte_Einladung.Einladender
                    inviter_uses = (old_inv.uses or 0) + 1
                    brechen
        falls nicht der Einladende:
            versuchen:
                vanity = await guild.vanity_invite()
                if vanity and old_invite_map.get("vanity"):
                    old_vanity = old_invite_map["vanity"]
                    if vanity.uses > getattr(old_vanity, "uses", 0):
                        inviter_uses = vanity.uses
                new_invite_map["vanity"] = vanity
            Ausnahme:
                passieren
        invite_cache[guild.id] = new_invite_map
    außer Ausnahme als e:
        wait log_bot_error("Invite-Tracking fehlgeschlagen", str(e), Gilde)

    join_log_ch = guild.get_channel(JOIN_LOG_CHANNEL_ID)
    if join_log_ch:
        description = f"**Spieler:** {member.mention} (`{member}`)\n"
        falls der Einladende:
            description += f"**Eingeladen von:** {inviter.mention} (`{inviter}`)\n"
            description += f"**Einladungen von {inviter.display_name}:** {inviter_uses}"
        elif inviter_uses > 0:
            Beschreibung += "**Eingeladen von:** Vanity-URL (Server-Link)"
        anders:
            Beschreibung += "**Eingeladen von:** Unbekannt *(Bot fehlt 'Server verwalten' Berechtigung?)*"
        embed = discord.Embed(
            title="ðŸ“¥ Neues Mitglied",
            Beschreibung=Beschreibung,
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await join_log_ch.send(embed=embed)

    Rolle = guild.get_role(WHITELIST_ROLE_ID)
    falls Würfelwurf:
        versuchen:
            await member.add_roles(rolle)
        Ausnahme:
            passieren

    versuchen:
        embed = discord.Embed(
            Beschreibung=(
                "> Willkommen auf Kryptik Roleplay deinem RP Server mit Ultimativem Spaß und Hochwertigem RP\n\n"
                "> Wir wünschen dir viel Spaß auf unserem Server und hoffen, dass du dich bei uns gut zurecht findest\n\n"
                "> Solltest du mal Schwierigkeiten haben melde dich gerne jederzeit über ein Support Ticket im Kanal "
                f"[#ticket-erstellen](https://discord.com/channels/{GUILD_ID}/{TICKET_CHANNEL_ID})"
            ),
            Farbe=LOG_COLOR
        )
        await member.send(content=member.mention, embed=embed)
    Ausnahme:
        passieren

    # â“€â“€ Startguthaben 5.000 ðŸ'µ â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€ â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€
    eco = load_economy()
    user_data = get_user(eco, member.id)
    if user_data["cash"] == 0 and user_data["bank"] == 0:
        user_data["cash"] = START_CASH
        save_economy(eco)
        await log_money_action(
            Gilde,
            "Startguthaben vergeben",
            f"**Spieler:** {member.mention}\n**Bargeld:** {START_CASH:,} ðŸ'µ (Willkommensbonus)"
        )


# â“€â“€ Befehle â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€ â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€â“€

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! ðŸ'‹")


@bot.command(name="testping")
async def testing(ctx):
    if not is_admin(ctx.author):
        zurückkehren
    kanal = ctx.guild.get_channel(JOIN_LOG_CHANNEL_ID)
    Rolle = ctx.guild.get_role(MOD_ROLE_ID)
    if kanal and rolle:
        wait kanal.send(f"{rolle.mention} Dies ist ein Test-Ping vom Bot!")
    versuchen:
        await ctx.message.delete()
    Ausnahme:
        passieren


@bot.command(name="botstatus")
async def botstatus(ctx):
    if not is_admin(ctx.author):
        zurückkehren
    await send_bot_status()
    versuchen:
        await ctx.message.delete()
    Ausnahme:
        passieren


@bot.command(name="ticketsetup")
async def ticketsetup(ctx):
    „Sendet das Ticket-Embed in den Ticket-Kanal. Nur für Admins.“
    if not is_admin(ctx.author):
        zurückkehren
    Kanal = ctx.guild.get_channel(TICKET_SETUP_CHANNEL_ID)
    falls nicht Kanal:
        wait ctx.send("â Œ Ticket-Kanal nicht gefunden!")
        zurückkehren
    embed = discord.Embed(
        title="ðŸŽŸ Support – Ticket erstellen",
        Beschreibung=(
            „Benötigt du Hilfe oder möchtest du einen Betroffenen melden?\n\n“
            „Wähle unten im Menü die passende Ticket-Art aus.\n“
            „Unser Team wird sich schnellstmöglich um dich kümmern.\n\n“
            „**Verfügbare Ticket-Arten:**\n“
            „ðŸŽŸ **Support** – Allgemeiner Support\n“
            „ðŸŽŸ **Highteam Ticket** – Direkter Kontakt zum Highteam\n“
            „ðŸŽŸ **Fraktions Bewerbung** – Bewirb dich für eine Fraktion\n“
            „ðŸŽŸ **Beschwerde Ticket** – Beschwerde einreichen\n“
            „ðŸŽŸ **Bug Report** – Fehler oder Bug melden“
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Cryptik Roleplay — Supportsystem")
    Ansicht = TicketSelectView()
    await channel.send(embed=embed, view=view)
    versuchen:
        await ctx.message.delete()
    Ausnahme:
        passieren


# — Economy Slash Commands —

def channel_error(channel_id: int) -> str:
    return f"â Œ Du kannst diesen Befehl nur hier ausführen: <#{channel_id}>"


# /lohn-abholen
@bot.tree.command(name="lohn-abholen", description="Hole deinen wertvollen Lohn ab", guild=discord.Object(id=GUILD_ID))
async def lohn_abholen(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != LOHN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(LOHN_CHANNEL_ID), ephemeral=True)
        zurückkehren

    main_wages = [WAGE_ROLES[r] for r in role_ids if r in WAGE_ROLES]
    if len(main_wages) > 1:
        await interaction.response.send_message(
            „â Œ Du hast mehrere Lohnklassen. Bitte wende dich ans Team.“, ephemeral=True
        )
        zurückkehren
    falls nicht Hauptlohn:
        await interaction.response.send_message(
            „â Œ Du hast keine Lohnklasse und kannst keinen Lohn abholen.“, ephemeral=True
        )
        zurückkehren

    Gesamtlohn = Hauptlohn[0]
    if ADDITIONAL_WAGE_ROLE_ID in role_ids:
        Gesamtlohn += ZUSÄTZLICHER_LOHN_ROLLENLOHN

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    jetzt = datetime.now(timezone.utc)

    if user_data["last_wage"]:
        last = datetime.fromisoformat(user_data["last_wage"])
        diff = (jetzt - letzte).total_seconds()
        if diff < 3600:
            Rest = int(3600 - Differenz)
            Minuten = verbleibend // 60
            Sekunden = verbleibende % 60
            await interaction.response.send_message(
                f"â Œ Du kannst deinen Lohn erst in **{mins}m {secs}s** wieder abholen.",
                ephemeral=True
            )
            zurückkehren

    user_data["bank"] += total_wage
    user_data["last_wage"] = now.isoformat()
    save_economy(eco)

    embed = discord.Embed(
        title="ðŸ'µ Lohn abgeholt!",
        Beschreibung=(
            f"Du hast **{total_wage:,} ðŸ'µ** auf dein Konto erhalten.\n"
            f"**Kontostand:** {user_data['bank']:,} ðŸ'µ"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=jetzt
    )
    await interaction.response.send_message(embed=embed)


# /kontostand
@bot.tree.command(name="kontostand", description="Zeigt deinen Kontostand an", guild=discord.Object(id=GUILD_ID))
async def kontostand(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        zurückkehren

    if not is_adm and not has_citizen_or_wage(interaction.user):
        wait interaction.response.send_message("â Œ Du hast keine Berechtigung.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    save_economy(eco)

    embed = discord.Embed(
        title="ðŸ'³ Kontostand",
        Beschreibung=(
            f"**Bargeld:** {user_data['cash']:,} ðŸ'µ\n"
            f"**Bank:** {user_data['bank']:,} ðŸ'µ\n"
            f"**Gesamt:** {user_data['cash'] + user_data['bank']:,} ðŸ'µ"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /einzahlen
@bot.tree.command(name="einzahlen", description="Zahle Bargeld auf dein Bankkonto ein", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wählen oder eingeben (1.000 – 10.000.000 ðŸ'µ)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def einzahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        zurückkehren

    if not is_adm and not has_citizen_or_wage(interaction.user):
        wait interaction.response.send_message("â Œ Du hast keine Berechtigung.", ephemeral=True)
        zurückkehren

    if betrag <= 0:
        wait interaction.response.send_message("â Œ Betrag muss größer als 0 sein.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["cash"] < Betrag:
        await interaction.response.send_message(
            f"â Œ Nicht genug Bargeld. Dein Bargeld: **{user_data['cash']:,} ðŸ'µ**", ephemeral=True
        )
        zurückkehren

    falls nicht is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        verbleibend = Benutzerlimit - Benutzerdaten["tägliche Einzahlung"]
        falls Betrag > Restbetrag:
            await interaction.response.send_message(
                f"â Œ Tageslimit erreicht. Du kannst heute noch **{remaining:,} ðŸ'µ** einzahlen. "
                f"(Limit: **{user_limit:,} ðŸ'µ**)",
                ephemeral=True
            )
            zurückkehren
        user_data["daily_deposit"] += Betrag

    user_data["cash"] -= betrag
    user_data["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        Interaktion.Gilde,
        "Einzahlung",
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} ðŸ'µ\n"
        f"**Bargeld danach:** {user_data['cash']:,} ðŸ'µ | **Bank danach:** {user_data['bank']:,} ðŸ'µ"
    )

    embed = discord.Embed(
        title="ðŸ ¦ Eingezahlt",
        Beschreibung=(
            f"**Eingezahlt:** {betrag:,} ðŸ'µ\n"
            f"**Bargeld:** {user_data['cash']:,} ðŸ'µ\n"
            f"**Bank:** {user_data['bank']:,} ðŸ'µ"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /auszahlen
@bot.tree.command(name="auszahlen", description="Hebe Geld von deinem Bankkonto ab", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wählen oder eingeben (1.000 – 10.000.000 ðŸ'µ)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def auszahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        zurückkehren

    if not is_adm and not has_citizen_or_wage(interaction.user):
        wait interaction.response.send_message("â Œ Du hast keine Berechtigung.", ephemeral=True)
        zurückkehren

    if betrag <= 0:
        wait interaction.response.send_message("â Œ Betrag muss größer als 0 sein.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["bank"] < Betrag:
        await interaction.response.send_message (
            f"â Œ Nicht genug Guthaben. Dein Kontostand: **{user_data['bank']:,} ðŸ'µ**", ephemeral=True
        )
        zurückkehren

    falls nicht is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        verbleibend = Benutzerlimit - Benutzerdaten["tägliche_Abhebung"]
        falls Betrag > Restbetrag:
            await interaction.response.send_message(
                f"â Œ Tageslimit erreicht. Du kannst heute noch **{remaining:,} ðŸ'µ** auszahlen. "
                f"(Limit: **{user_limit:,} ðŸ'µ**)",
                ephemeral=True
            )
            zurückkehren
        user_data["daily_withdraw"] += betrag

    user_data["bank"] -= betrag
    user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        Interaktion.Gilde,
        "Auszahlung",
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} ðŸ'µ\n"
        f"**Bargeld danach:** {user_data['cash']:,} ðŸ'µ | **Bank danach:** {user_data['bank']:,} ðŸ'µ"
    )

    embed = discord.Embed(
        title="ðŸ'¸ Ausgezahlt",
        Beschreibung=(
            f"**Ausgezahlt:** {betrag:,} ðŸ'µ\n"
            f"**Bargeld:** {user_data['cash']:,} ðŸ'µ\n"
            f"**Bank:** {user_data['bank']:,} ðŸ'µ"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /äberweisen
@bot.tree.command(name="überweisen", description="überweise Geld an einen anderen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Empfanger", betrag="Betrag wählen oder eingeben (1.000 – 10.000.000 ðŸ'µ)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def ueberweisen(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        zurückkehren

    if not is_adm and not has_citizen_or_wage(interaction.user):
        wait interaction.response.send_message("â Œ Du hast keine Berechtigung.", ephemeral=True)
        zurückkehren

    if nutzer.id == interaction.user.id:
        wait interaction.response.send_message("â Œ Du kannst dich nicht selbst überweisen.", ephemeral=True)
        zurückkehren

    if betrag <= 0:
        wait interaction.response.send_message("â Œ Betrag muss größer als 0 sein.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    sender = get_user(eco, interaction.user.id)
    Empfänger = get_user(eco, nutzer.id)
    reset_daily_if_needed(sender)

    if sender["bank"] < betrag:
        await interaction.response.send_message(
            f"â Œ Nicht genug Guthaben. Dein Kontostand: **{sender['bank']:,} ðŸ'µ**", ephemeral=True
        )
        zurückkehren

    falls nicht is_adm:
        user_limit = sender.get("custom_limit") or DAILY_LIMIT
        verbleibend = Benutzerlimit - Absender["tägliche Überweisung"]
        falls Betrag > Restbetrag:
            await interaction.response.send_message(
                f"â Œ Tageslimit erreicht. Du kannst heute noch **{remaining:,} ðŸ'µ** überweisen. "
                f"(Limit: **{user_limit:,} ðŸ'µ**)",
                ephemeral=True
            )
            zurückkehren
        sender["daily_transfer"] += Betrag

    Absender["Bank"] -= Betrag
    Empfänger["Bank"] += Betrag
    save_economy(eco)
    await log_money_action(
        Interaktion.Gilde,
        "Berweisung",
        f"**Von:** {interaction.user.mention} â†' **An:** {nutzer.mention}\n"
        f"**Betrag:** {betrag:,} ðŸ'µ | **Sender-Bank danach:** {sender['bank']:,} ðŸ'µ"
    )

    embed = discord.Embed(
        title="ðŸ'³ Überweisung",
        Beschreibung=(
            f"**An:** {nutzer.mention}\n"
            f"**Betrag:** {betrag:,} ðŸ'µ\n"
            f"**Dein Kontostand:** {sender['bank']:,} ðŸ'µ"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /Geschäft
@bot.tree.command(name="shop", description="Zeigt den Shop an", guild=discord.Object(id=GUILD_ID))
async def shop(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        zurückkehren

    items = load_shop()
    falls keine Artikel:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ðŸ›' Shop",
                description="Der Shop ist aktuell leer.",
                Farbe=LOG_COLOR
            ),
            ephemeral=True
        )
        zurückkehren

    desc = "\n".join(f"**{item['name']}** â€— {item['price']:,} ðŸ'µ" for item in items)
    embed = discord.Embed(
        title="ðŸ›' Shop",
        Beschreibung=desc,
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Kaufen mit /buy [itemname] â€¢ Nur mit Bargeld mÃ¶glich")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /kaufen
@bot.tree.command(name="buy", description="Einen Artikel aus dem Shop kaufen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(itemname="Name des Artikels, den du kaufen möchtest")
async def buy(interaction: discord.Interaction, itemname: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        zurückkehren

    if not is_adm and not has_citizen_or_wage(interaction.user):
        wait interaction.response.send_message("â Œ Du hast keine Berechtigung.", ephemeral=True)
        zurückkehren

    items = load_shop()
    item = next((i for i in items if i["name"].lower() == itemname.lower()), None)

    falls nicht Artikel:
        await interaction.response.send_message(
            f"â Œ Artikel **{itemname}** wurde nicht. Nutze `/shop` um alle Artikel zu sehen.",
            ephemeral=True
        )
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)

    if user_data["cash"] < item["price"]:
        await interaction.response.send_message(
            f"â Œ Du hast nicht genug **Bargeld**.\n"
            f"Preis: **{item['price']:,} ðŸ'µ** | Dein Bargeld: **{user_data['cash']:,} ðŸ'µ**\n"
            f"â„¹ï¸ Käufe sind nur mit Bargeld möglich. Hebe Geld mit `/auszahlen` ab.",
            ephemeral=True
        )
        zurückkehren

    user_data["cash"] -= item["price"]
    Falls "inventory" nicht in user_data enthalten ist:
        user_data["inventory"] = []
    user_data["inventory"].append(item["name"])
    save_economy(eco)

    embed = discord.Embed(
        title="✓ Gekauft!",
        Beschreibung=(
            f"Du hast **{item['name']}** für **{item['price']:,} ðŸ'µ** gekauft.\n"
            f"**Verbleibendes Bargeld:** {user_data['cash']:,} ðŸ'µ"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /set-limit (Nur Team)
@bot.tree.command(name="set-limit", description="[TEAM] Setzt das individuelle Tageslimit eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", limit="Neues Tageslimit")
@app_commands.choices(limit=LIMIT_CHOICES)
async def set_limit(interaction: discord.Interaction, nutzer: discord.Member, limit: int):
    role_ids = [r.id for r in interaction.user.roles]
    Falls ADMIN_ROLE_ID und MOD_ROLE_ID nicht in role_ids enthalten sind:
        Warten auf Interaktion.response.send_message("â Œ Keine Berechtigung.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["custom_limit"] = limit
    save_economy(eco)

    embed = discord.Embed(
        title="âš™ï¸ Limit gesetzt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Neues Tageslimit:** {limit:,} ðŸ'µ\n"
            f"*(gilt für Einzahlen, Auszahlen & Überweisen)*"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesetzt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


# /money-add (Nur für Administratoren)
@bot.tree.command(name="money-add", description="[ADMIN] Füge einem Spieler Geld hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
@app_commands.default_permissions(administrator=True)
async def money_add(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not is_admin(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Kein Zugriff.", ephemeral=True)
        zurückkehren

    if betrag <= 0:
        wait interaction.response.send_message("â Œ Betrag muss größer als 0 sein.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        Interaktion.Gilde,
        "Admin: Geld zugefÃ¼gt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** +{betrag:,} ðŸ'µ\n"
        f"**Bargeld danach:** {user_data['cash']:,} ðŸ'µ\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="ðŸ'° Geld hinzugefügt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**HinzugefÃ¼gt:** {betrag:,} ðŸ'µ\n"
            f"**Bargeld:** {user_data['cash']:,} ðŸ'µ"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /remove-money (Nur für Administratoren)
@bot.tree.command(name="remove-money", description="[ADMIN] Entferne Geld von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
@app_commands.default_permissions(administrator=True)
async def remove_money(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not is_admin(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Kein Zugriff.", ephemeral=True)
        zurückkehren

    if betrag <= 0:
        wait interaction.response.send_message("â Œ Betrag muss größer als 0 sein.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] = max(0, user_data["cash"] - betrag)
    save_economy(eco)
    await log_money_action(
        Interaktion.Gilde,
        "Admin: Geld entfernt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** -{betrag:,} ðŸ'µ\n"
        f"**Bargeld danach:** {user_data['cash']:,} ðŸ'µ\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="ðŸ'¸ Geld entfernt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernt:** {betrag:,} ðŸ'µ\n"
            f"**Bargeld:** {user_data['cash']:,} ðŸ'µ"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /item-add (Nur für Administratoren)
@bot.tree.command(name="item-add", description="[ADMIN] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", itemname="Itemname")
@app_commands.default_permissions(administrator=True)
async def item_add(interaction: discord.Interaction, nutzer: discord.Member, itemname: str):
    if not is_admin(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Kein Zugriff.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    Falls "inventory" nicht in user_data enthalten ist:
        user_data["inventory"] = []
    user_data["inventory"].append(itemname)
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="ðŸ“¦ Item hinzugefügt",
            description=f"**{itemname}** wurde **{nutzer.mention}** hinzugefügt.",
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        ),
        ephemeral=True
    )


# /remove-item (Nur für Administratoren)
@bot.tree.command(name="remove-item", description="[ADMIN] Entferne ein Item von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", itemname="Itemname")
@app_commands.default_permissions(administrator=True)
async def remove_item(interaction: discord.Interaction, nutzer: discord.Member, itemname: str):
    if not is_admin(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Kein Zugriff.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    inventory = user_data.get("inventory", [])

    Falls der Artikelname nicht im Inventar vorhanden ist:
        await interaction.response.send_message(
            f"â Œ **{nutzer.display_name}** besitzt kein Item namens **{itemname}**.", ephemeral=True
        )
        zurückkehren

    inventory.remove(itemname)
    user_data["inventory"] = inventory
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="ðŸ“¦ Item entfernt",
            description=f"**{itemname}** wurde von **{nutzer.mention}** entfernt.",
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        ),
        ephemeral=True
    )


# /shop-add (Nur für Administratoren) mit Bestätigung
class ShopAddConfirmView(discord.ui.View):
    def __init__(self, name: str, price: int):
        super().__init__(timeout=60)
        self.name = Name
        self.price = price

    @discord.ui.button(label="âœ… BestÃ¤tigen", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = load_shop()
        items.append({"name": self.name, "price": self.price})
        save_shop(items)
        für Element in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✓ Artikel hinzugefügt",
                description=f"**{self.name}** für **{self.price:,} ðŸ'µ** wurde zum Shop hinzugefügt.",
                Farbe=LOG_COLOR
            ),
            Ansicht=Selbst
        )

    @discord.ui.button(label="☐ Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        für Element in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="â Œ Abgebrochen",
                description="Das Item wurde nicht hinzugefügt.",
                Farbe=MOD_COLOR
            ),
            Ansicht=Selbst
        )


@bot.tree.command(name="shop-add", description="[ADMIN] Füge einen neuen Artikel zum Shop hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(itemname="Name des Artikels", preis="Preis in $")
@app_commands.default_permissions(administrator=True)
async def shop_add(interaction: discord.Interaction, itemname: str, preis: int):
    if not is_admin(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Kein Zugriff.", ephemeral=True)
        zurückkehren

    falls Preis <= 0:
        wait interaction.response.send_message("â Œ Preis muss größer als 0 sein.", ephemeral=True)
        zurückkehren

    embed = discord.Embed(
        title="ðŸ›' Neues Item hinzufügen?",
        Beschreibung=(
            f"**Name:** {itemname}\n"
            f"**Preis:** {preis:,} ðŸ'µ\n\n"
            f"Bitte bestätige das Hinzufügen."
        ),
        Farbe=LOG_COLOR
    )
    await interaction.response.send_message(embed=embed, view=ShopAddConfirmView(itemname, preis), ephemeral=True)


# â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â•
# WARNUNG SYSTEM
# â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â•

# /warn (Nur für Teams)
@bot.tree.command(name="warn", description="[TEAM] Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if not is_team(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Keine Berechtigung.", ephemeral=True)
        zurückkehren

    warns = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)
    warn_entry = {
        "grund": grund,
        "Konsequenz": Konsequenz,
        "warned_by": interaction.user.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    user_warns.append(warn_entry)
    save_warns(warns)
    warn_count = len(user_warns)

    embed = discord.Embed(
        title="✓ Verwarnung",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Grund:** {grund}\n"
            f"**Konsequenz:** {konsequenz}\n"
            f"**Verwarnt von:** {interaction.user.mention}\n"
            f"**Warnungen insgesamt:** {warn_count}"
        ),
        Farbe=MOD_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    log_ch = interaction.guild.get_channel(WARN_LOG_CHANNEL_ID)
    if log_ch:
        await log_ch.send(embed=embed)

    await interaction.response.send_message(
        f"âœ… Verwarnung für {nutzer.mention} gespeichert. (Warns gesamt: **{warn_count}**)", ephemeral=True
    )

    # Automatischer Timeout bei 3 Warnungen
    if warn_count >= WARN_AUTO_TIMEOUT_COUNT:
        timeout_dur = timedelta(days=2)
        versuchen:
            wait nutzer.timeout(timeout_dur, reason=f"Automatischer Timeout: {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht")
        Ausnahme:
            passieren
        # Alle Rollen entfernen
        versuchen:
            roles_to_remove = [r for r in nutzer.roles if r != interaction.guild.default_role and not r.managed]
            falls Rollen_zu_entfernen:
                wait nutzer.remove_roles(*roles_to_remove, reason="Automatischer Timeout: 3 Warns")
        Ausnahme:
            passieren
        # DM senden
        versuchen:
            dm_embed = discord.Embed(
                title="ðŸ”‡ Du wurdest getimoutet",
                Beschreibung=(
                    f"Du hast auf **{interaction.guild.name}** {WARN_AUTO_TIMEOUT_COUNT} Verwarnungen erhalten "
                    f"und wurde daher für **2 Tage** getimeoutet.\n\n"
                    f"**Letzte Verwarnung:**\n"
                    f"Grund: {grund}\nKonsequenz: {konsequenz}\n\n"
                    f"Deine Rollen wurden vorübergehend entfernt.\n"
                    f"Nach dem Timeout melde dich bitte bei einem Teammitglied."
                ),
                Farbe=MOD_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            await nutzer.send(embed=dm_embed)
        Ausnahme:
            passieren
        timeout_embed = discord.Embed(
            title="ðŸ"‡ Automatischer Timeout",
            Beschreibung=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Grund:** {WARN_AUTO_TIMEOUT_COUNT} Warnt erreicht\n"
                f"**Dauer:** 2 Tage\n"
                f"**Rollen entfernt:** âœ…"
            ),
            Farbe=MOD_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        if log_ch:
            await log_ch.send(embed=timeout_embed)


# /warn-list
@bot.tree.command(name="warn-list", description="Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def warn_list(interaction: discord.Interaction, nutzer: discord.Member):
    if not is_team(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Keine Berechtigung.", ephemeral=True)
        zurückkehren

    warns = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"âœ… {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        zurückkehren

    Zeilen = []
    for i, w in enumerate(user_warns, 1):
        ts = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** – {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"âš ï¸ Warnt von {nutzer.display_name}",
        description="\n".join(lines),
        Farbe=MOD_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesamt: {len(user_warns)} Warnung(en)")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /remove-warn
@bot.tree.command(name="remove-warn", description="[TEAM] Letzte Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler")
async def remove_warn(interaction: discord.Interaction, nutzer: discord.Member):
    if not is_team(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Keine Berechtigung.", ephemeral=True)
        zurückkehren

    warns = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"â„¹ï¸ {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        zurückkehren

    entfernt = user_warns.pop()
    save_warns(warns)

    embed = discord.Embed(
        title="âœ… Verwarnung entfernt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernter Warn:** {removed['grund']}\n"
            f"**Verbleibende Warns:** {len(user_warns)}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â•
# INVENTAR-SYSTEM
# â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â•

# /Rucksack
@bot.tree.command(name="Rucksack", Beschreibung="Zeige dein Inventar an", guild=discord.Object(id=GUILD_ID))
async def rucksack(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids
    erlaubt = is_adm oder CITIZEN_ROLE_ID in role_ids oder any(r in role_ids für r in WAGE_ROLES) oder MOD_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != RUCKSACK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
        zurückkehren

    falls nicht erlaubt:
        wait interaction.response.send_message("â Œ Du hast keine Berechtigung.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    inventory = user_data.get("inventory", [])

    falls nicht im Lagerbestand:
        desc = "*Dein Rucksack ist leer.*"
    anders:
        from collections import Counter
        Anzahl = Zähler(Inventar)
        desc = "\n".join(f"â€¢ **{item}** Ã—{count}" for item, count in counts.items())

    embed = discord.Embed(
        title=f"ðŸŽ' Rucksack von {interaction.user.display_name}",
        Beschreibung=desc,
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /Ã¼bergeben
@bot.tree.command(name="übergeben", description="Gib ein Item aus deinem Inventar an jemanden weiter", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Empfanger", item="Name des Items")
async def uebergeben(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    wenn nicht is_adm und interaction.channel.id != UEBERGEBEN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(UEBERGEBEN_CHANNEL_ID), ephemeral=True)
        zurückkehren

    if nutzer.id == interaction.user.id:
        wait interaction.response.send_message("â Œ Du kannst dich nicht selbst übergeben.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    giver_data = get_user(eco, interaction.user.id)
    inv = giver_data.get("inventory", [])

    item_lower = item.lower()
    match = next((i for i in inv if i.lower() == item_lower), None)
    falls keine Übereinstimmung:
        await interaction.response.send_message(
            f"â Œ **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        zurückkehren

    inv.remove(match)
    receiver_data = get_user(eco, nutzer.id)
    receiver_data.setdefault("inventory", []).append(match)
    save_economy(eco)

    embed = discord.Embed(
        title="ðŸ¤ Item Ã¼bergeben",
        Beschreibung=(
            f"**Von:** {interaction.user.mention}\n"
            f"**An:** {nutzer.mention}\n"
            f"**Artikel:** {match}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /verstecken
@bot.tree.command(name="verstecken", description="Verstecke ein Item aus deinem Inventar", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(item="Name des Items", ort="Wo versteckst du es?")
async def Verstecken(interaction: discord.Interaction, item: str, ort: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != VERSTECKEN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(VERSTECKEN_CHANNEL_ID), ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    inv = user_data.get("inventory", [])

    item_lower = item.lower()
    match = next((i for i in inv if i.lower() == item_lower), None)
    falls keine Übereinstimmung:
        await interaction.response.send_message(
            f"â Œ **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        zurückkehren

    inv.remove(match)
    save_economy(eco)

    import uuid
    item_id = str(uuid.uuid4())[:8]
    versteckt = load_hidden_items()
    hidden.append({
        "id": item_id,
        "owner_id": interaction.user.id,
        "item": Übereinstimmung,
        "Standort": Ort,
    })
    save_hidden_items(hidden)

    view = VersteckRetrieveView(item_id, interaction.user.id)
    bot.add_view(view)

    embed = discord.Embed(
        title="ðŸ•µï¸ Item versteckt",
        Beschreibung=(
            f"**Item:** {match}\n"
            f"**Versteckt an:** {ort}\n\n"
            f"Nur du kannst es wieder herausnehmen."
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, view=view)


# â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â•
# TEAM-GEGENSTANDSBEFEHLE
# â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â•

# /item-geben (Nur für Teams)
@bot.tree.command(name="item-geben", description="[TEAM] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname")
async def item_geben(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Keine Berechtigung.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data.setdefault("inventory", []).append(item)
    save_economy(eco)

    embed = discord.Embed(
        title="ðŸŽ Item gegeben",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Artikel:** {item}\n"
            f"**Vergeben von:** {interaction.user.mention}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /item-entfernen (Nur für Teams)
@bot.tree.command(name="item-entfernen", description="[TEAM] Entferne ein Item von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname")
async def item_entfernen(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Keine Berechtigung.", ephemeral=True)
        zurückkehren

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    inv = user_data.get("inventory", [])

    item_lower = item.lower()
    match = next((i for i in inv if i.lower() == item_lower), None)
    falls keine Übereinstimmung:
        await interaction.response.send_message(
            f"â Œ **{item}** ist nicht im Inventar von {nutzer.mention}.", ephemeral=True
        )
        zurückkehren

    inv.remove(match)
    save_economy(eco)

    embed = discord.Embed(
        title="ðŸ—'ï¸ Item entfernt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {match}\n"
            f"**Entfernt von:** {interaction.user.mention}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â•
# KARTENKONTROLLE
# â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â•

KARTENKONTROLLE_CHANNEL_ID = 1491116234459185162

@bot.tree.command(name="kartenkontrolle", description="[TEAM] Sendet eine DM-Erinnerung zur Kartenkontrolle an alle Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def kartenkontrolle(interaction: discord.Interaction):
    if not is_team(interaction.user):
        Warten auf Interaktion.response.send_message("â Œ Keine Berechtigung.", ephemeral=True)
        zurückkehren

    await interaction.response.defer(ephemeral=True)

    Gilde = Interaktion.Gilde
    channel_link = f"https://discord.com/channels/{guild.id}/{KARTENKONTROLLE_CHANNEL_ID}"

    gesendet = 0
    fehlgeschlagen = 0
    für Mitglieder in guild.members:
        if member.bot:
            weitermachen
        role_ids = [r.id for r in member.roles]
        is_member_role = (
            CITIZEN_ROLE_ID in role_ids
            oder any(r in role_ids for r in WAGE_ROLES)
        )
        falls nicht is_member_role:
            weitermachen
        versuchen:
            dm_embed = discord.Embed(
                title="ðŸªª Kartenkontrolle",
                Beschreibung=(
                    f"**Hallo {member.display_name}!**\n\n"
                    f"Es findet gerade eine **Kartenkontrolle** statt.\n"
                    f"Bitte begib dich in den Kanal:\n"
                    f"[ðŸ”— Zur Kartenkontrolle]({channel_link})\n\n"
                    f"*Diese Nachricht wurde automatisch durch das Team gesendet.*"
                ),
                Farbe=LOG_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            await member.send(embed=dm_embed)
            gesendet += 1
        Ausnahme:
            fehlgeschlagen += 1

    await interaction.followup.send(
        f"âœ… Kartenkontrolle-DM gesendet!\n**Erfolgreich:** {sent} | **Fehlgeschlagen (DMs zu):** {failed}",
        ephemeral=True
    )


token = os.environ.get("DISCORD_TOKEN")
Falls kein Token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
