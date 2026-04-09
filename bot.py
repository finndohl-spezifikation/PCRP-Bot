import os
import io
import json
import random
import string
import uuid
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
import asyncio
import traceback

# Sicherheitscheck: Bot lÃ¤uft NUR auf Railway, nie doppelt in Replit
if not os.environ.get("RAILWAY_ENVIRONMENT") and not os.environ.get("FORCE_LOCAL_RUN"):
    print("=" * 60)
    print("STOPP: Bot wurde NICHT gestartet.")
    print("Dieser Bot lÃ¤uft ausschlieÃŸlich auf Railway.")
    print("Bitte NICHT in Replit starten â€” nur auf Railway deployen!")
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

# â”€â”€ Economy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
    app_commands.Choice(name="1.000 ðŸ’µ",       value=1_000),
    app_commands.Choice(name="5.000 ðŸ’µ",       value=5_000),
    app_commands.Choice(name="10.000 ðŸ’µ",      value=10_000),
    app_commands.Choice(name="25.000 ðŸ’µ",      value=25_000),
    app_commands.Choice(name="50.000 ðŸ’µ",      value=50_000),
    app_commands.Choice(name="100.000 ðŸ’µ",     value=100_000),
    app_commands.Choice(name="250.000 ðŸ’µ",     value=250_000),
    app_commands.Choice(name="500.000 ðŸ’µ",     value=500_000),
    app_commands.Choice(name="1.000.000 ðŸ’µ",   value=1_000_000),
]

LIMIT_CHOICES = [
    app_commands.Choice(name="1.000.000 ðŸ’µ",   value=1_000_000),
    app_commands.Choice(name="2.000.000 ðŸ’µ",   value=2_000_000),
    app_commands.Choice(name="3.000.000 ðŸ’µ",   value=3_000_000),
    app_commands.Choice(name="4.000.000 ðŸ’µ",   value=4_000_000),
    app_commands.Choice(name="5.000.000 ðŸ’µ",   value=5_000_000),
    app_commands.Choice(name="6.000.000 ðŸ’µ",   value=6_000_000),
    app_commands.Choice(name="7.000.000 ðŸ’µ",   value=7_000_000),
    app_commands.Choice(name="8.000.000 ðŸ’µ",   value=8_000_000),
    app_commands.Choice(name="9.000.000 ðŸ’µ",   value=9_000_000),
    app_commands.Choice(name="10.000.000 ðŸ’µ",  value=10_000_000),
]

# Persistenter Datenspeicher
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

ECONOMY_FILE      = DATA_DIR / "economy_data.json"
SHOP_FILE         = DATA_DIR / "shop_data.json"
WARNS_FILE        = DATA_DIR / "warns_data.json"
HIDDEN_ITEMS_FILE = DATA_DIR / "hidden_items.json"
AUSWEIS_FILE      = DATA_DIR / "ausweis_data.json"
HANDY_FILE        = DATA_DIR / "handy_numbers.json"

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

# â”€â”€ Handy System â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
HANDY_CHANNEL_ID      = 1490890317199708160
HANDY_ITEM_NAME       = "ðŸ“±| Handy"  # exakter Name im Shop

DISPATCH_MD_ROLE_ID   = 1490855752712327210
DISPATCH_PD_ROLE_ID   = 1490855751797969039
DISPATCH_ADAC_ROLE_ID = 1490855754213753024
INSTAGRAM_ROLE_ID     = 1490855786698641428
PARSHIP_ROLE_ID       = 1490855783989121024

# IC-Chat Kanal-ID â€” bitte mit der korrekten ID des IC-Chat-Kanals ersetzen!
IC_CHAT_CHANNEL_ID    = 0

WARN_AUTO_TIMEOUT_COUNT = 3
START_CASH              = 5_000

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
    "mistkerl", "penner", "hurenkind", "dummficker", "scheiÃŸ",
]

spam_tracker     = {}
spam_warned      = set()
ticket_data      = {}
counting_state   = {"count": 0, "last_user_id": None}
counting_handled = set()

FEATURES = {
    "Discord Link Schutz":         True,
    "Link Filter (Memes)":         True,
    "VulgÃ¤re WÃ¶rter Filter":       True,
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
    "ZÃ¤hl-Kanal":                  True,
    "Economy System":              True,
    "Handy System":                True,
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
                title=f"âš ï¸ Bot Fehler â€” {title}",
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
            emoji = "ðŸŸ¢" if status else "ðŸ”´"
            state = "Online" if status else "Offline"
            desc += f"{emoji} **{feature}** â€” {state}\n"
        embed = discord.Embed(
            title="ðŸ¤– Bot Status â€” Alle Funktionen",
            description=desc,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await log_ch.send(embed=embed)
        except Exception:
            pass


async def apply_timeout_restrictions(member, guild, duration_h=None, duration_m=None, reason="RegelverstoÃŸ"):
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
            f"MÃ¶gliche Ursachen:\n"
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


# â”€â”€ Economy Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Warn Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Hidden Items Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_hidden_items():
    if HIDDEN_ITEMS_FILE.exists():
        with open(HIDDEN_ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_hidden_items(data):
    with open(HIDDEN_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# â”€â”€ Handy Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_handy_numbers():
    if HANDY_FILE.exists():
        with open(HANDY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_handy_numbers(data):
    with open(HANDY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_la_phone_number():
    # LA-Vorwahlen: 213, 310, 323, 424, 562, 626, 747, 818
    area_codes = ["213", "310", "323", "424", "562", "626", "747", "818"]
    area = random.choice(area_codes)
    num1 = random.randint(200, 999)
    num2 = random.randint(1000, 9999)
    return f"+1 ({area}) {num1}-{num2}"


def has_handy(member):
    """PrÃ¼ft ob der Member das Handy-Item im Inventar hat."""
    eco = load_economy()
    user_data = get_user(eco, member.id)
    inventory = user_data.get("inventory", [])
    return any(normalize_item_name(i) == normalize_item_name(HANDY_ITEM_NAME) for i in inventory)


# â”€â”€ Money Log Helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def log_money_action(guild: discord.Guild, title: str, description: str):
    ch = guild.get_channel(MONEY_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title=f"ðŸ’µ {title}",
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await ch.send(embed=embed)
        except Exception:
            pass


# â”€â”€ Betrag Autocomplete â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
        label = f"{val:,} ðŸ’µ".replace(",", ".")
        if clean == "" or clean in str(val) or clean.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=val))
    return choices[:25]


# â”€â”€ Shop-Item Autocomplete â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def shop_item_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    items = load_shop()
    current_lower = current.lower()
    choices = []
    for item in items:
        name = item["name"]
        if current_lower == "" or current_lower in name.lower():
            choices.append(app_commands.Choice(name=name, value=name))
    return choices[:25]


# â”€â”€ Inventar-Item Autocomplete â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def inventory_item_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    from collections import Counter
    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    inventory = user_data.get("inventory", [])
    counts    = Counter(inventory)
    current_lower = current.lower()
    choices = []
    for item_name, count in counts.items():
        label = f"{item_name} (Ã—{count})"
        if current_lower == "" or current_lower in item_name.lower():
            choices.append(app_commands.Choice(name=label, value=item_name))
    return choices[:25]


# â”€â”€ Normalisierungsfunktion fÃ¼r Item-Namen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def normalize_item_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[\|\-\_]+', ' ', name)
    name = ''.join(c for c in name if c.isalnum() or c.isspace())
    return re.sub(r'\s+', ' ', name).strip()


# â”€â”€ Versteck-Button (persistent) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class VersteckRetrieveView(discord.ui.View):
    def __init__(self, item_id: str, owner_id: int):
        super().__init__(timeout=None)
        self.item_id  = item_id
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
                "âŒ Nur derjenige der das Item versteckt hat kann es herausnehmen.",
                ephemeral=True
            )
            return
        hidden = load_hidden_items()
        entry  = next((h for h in hidden if h["id"] == self.item_id), None)
        if not entry:
            await interaction.response.send_message("âŒ Item wurde bereits geborgen oder existiert nicht mehr.", ephemeral=True)
            return

        eco       = load_economy()
        user_data = get_user(eco, interaction.user.id)
        user_data.setdefault("inventory", []).append(entry["item"])
        save_economy(eco)

        hidden = [h for h in hidden if h["id"] != self.item_id]
        save_hidden_items(hidden)

        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.response.send_message(
            f"âœ… **{entry['item']}** wurde aus dem Versteck (**{entry['location']}**) geholt.",
            ephemeral=True
        )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# HANDY SYSTEM
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class HandyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # â”€â”€ Dispatch MD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @discord.ui.button(
        label="ðŸš¨ | Dispatch MD",
        style=discord.ButtonStyle.red,
        custom_id="handy_dispatch_md",
        row=0
    )
    async def dispatch_md(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_dispatch(interaction, DISPATCH_MD_ROLE_ID, "MD")

    # â”€â”€ Dispatch PD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @discord.ui.button(
        label="ðŸš¨ | Dispatch PD",
        style=discord.ButtonStyle.red,
        custom_id="handy_dispatch_pd",
        row=0
    )
    async def dispatch_pd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_dispatch(interaction, DISPATCH_PD_ROLE_ID, "PD")

    # â”€â”€ Dispatch ADAC â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @discord.ui.button(
        label="ðŸš¨ | Dispatch ADAC",
        style=discord.ButtonStyle.red,
        custom_id="handy_dispatch_adac",
        row=0
    )
    async def dispatch_adac(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_dispatch(interaction, DISPATCH_ADAC_ROLE_ID, "ADAC")

    # â”€â”€ Handy Nummer Einsehen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @discord.ui.button(
        label="ðŸ“± | Handy Nummer Einsehen",
        style=discord.ButtonStyle.blurple,
        custom_id="handy_nummer",
        row=1
    )
    async def handy_nummer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "âŒ Du besitzt kein Handy. Kaufe es im Shop!",
                ephemeral=True
            )
            return

        numbers = load_handy_numbers()
        uid = str(interaction.user.id)

        if uid not in numbers:
            numbers[uid] = generate_la_phone_number()
            save_handy_numbers(numbers)

        phone = numbers[uid]
        embed = discord.Embed(
            title="ðŸ“± Deine Handynummer",
            description=(
                f"**Nummer:** `{phone}`\n"
                f"**Vorwahl:** Los Angeles (LA)\n\n"
                f"*Diese Nummer bleibt dauerhaft dieselbe.*"
            ),
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Nur du siehst diese Nachricht")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # â”€â”€ Instagram â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @discord.ui.button(
        label="ðŸ“± | Instagram",
        style=discord.ButtonStyle.blurple,
        custom_id="handy_instagram",
        row=1
    )
    async def instagram(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "âŒ Du besitzt kein Handy. Kaufe es im Shop!",
                ephemeral=True
            )
            return

        guild = interaction.guild
        role  = guild.get_role(INSTAGRAM_ROLE_ID)
        if not role:
            await interaction.response.send_message("âŒ Instagram-Rolle nicht gefunden.", ephemeral=True)
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role, reason="Handy: Instagram deinstalliert")
            embed = discord.Embed(
                description="ðŸ“± **App Erfolgreich Deinstalliert**\nInstagram wurde von deinem Handy entfernt.",
                color=MOD_COLOR
            )
        else:
            await member.add_roles(role, reason="Handy: Instagram installiert")
            embed = discord.Embed(
                description="ðŸ“± **App Erfolgreich Installiert**\nInstagram wurde auf deinem Handy installiert.",
                color=LOG_COLOR
            )
        embed.set_footer(text="Nur du siehst diese Nachricht")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # â”€â”€ Parship â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @discord.ui.button(
        label="ðŸ“± | Parship",
        style=discord.ButtonStyle.blurple,
        custom_id="handy_parship",
        row=1
    )
    async def parship(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "âŒ Du besitzt kein Handy. Kaufe es im Shop!",
                ephemeral=True
            )
            return

        guild = interaction.guild
        role  = guild.get_role(PARSHIP_ROLE_ID)
        if not role:
            await interaction.response.send_message("âŒ Parship-Rolle nicht gefunden.", ephemeral=True)
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role, reason="Handy: Parship deinstalliert")
            embed = discord.Embed(
                description="ðŸ“± **App Erfolgreich Deinstalliert**\nParship wurde von deinem Handy entfernt.",
                color=MOD_COLOR
            )
        else:
            await member.add_roles(role, reason="Handy: Parship installiert")
            embed = discord.Embed(
                description="ðŸ“± **App Erfolgreich Installiert**\nParship wurde auf deinem Handy installiert.",
                color=LOG_COLOR
            )
        embed.set_footer(text="Nur du siehst diese Nachricht")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def handle_dispatch(interaction: discord.Interaction, role_id: int, dispatch_type: str):
    """Sendet einen Dispatch-Notruf als DM an alle Mitglieder mit der jeweiligen Rolle."""
    if not has_handy(interaction.user):
        await interaction.response.send_message(
            "âŒ Du besitzt kein Handy. Kaufe es im Shop!",
            ephemeral=True
        )
        return

    guild  = interaction.guild
    member = interaction.user
    role   = guild.get_role(role_id)

    if not role:
        await interaction.response.send_message(
            f"âŒ Dispatch-Rolle nicht gefunden.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    dispatch_embed = discord.Embed(
        title="ðŸš¨ Dispatch ðŸš¨",
        description=(
            f"**Ein Bewohner hat einen Dispatch abgesendet!**\n\n"
            f"ðŸ—ºï¸ **Standort:** {member.mention}\n"
            f"ðŸ“‹ **Dispatch-Typ:** {dispatch_type}\n"
            f"â° **Zeit:** <t:{int(datetime.now(timezone.utc).timestamp())}:T>"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    dispatch_embed.set_footer(text=f"Kryptik Roleplay â€” Dispatch System")

    sent   = 0
    failed = 0
    for target in guild.members:
        if target.bot:
            continue
        if role not in target.roles:
            continue
        try:
            await target.send(embed=dispatch_embed)
            sent += 1
        except Exception:
            failed += 1

    confirm_embed = discord.Embed(
        title="âœ… Dispatch gesendet!",
        description=(
            f"Dein **{dispatch_type}-Dispatch** wurde erfolgreich abgesendet.\n"
            f"**Benachrichtigt:** {sent} Einheiten\n\n"
            f"Falls niemand reagiert, kannst du unten im IC-Chat pingen."
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )

    nobody_view = DispatchNobodyView(dispatch_type, member)
    await interaction.followup.send(embed=confirm_embed, view=nobody_view, ephemeral=True)


class DispatchNobodyView(discord.ui.View):
    """Kurzlebige View, die dem Dispatcher erlaubt, den IC-Chat zu pingen wenn niemand kommt."""
    def __init__(self, dispatch_type: str, requester: discord.Member):
        super().__init__(timeout=600)  # 10 Minuten verfÃ¼gbar
        self.dispatch_type = dispatch_type
        self.requester     = requester

    @discord.ui.button(
        label="ðŸ“¢ Niemand kommt â€” IC-Chat pingen",
        style=discord.ButtonStyle.red,
        emoji="ðŸ“¢"
    )
    async def ping_ic_chat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester.id:
            await interaction.response.send_message("âŒ Nur der Absender kann diese Aktion ausfÃ¼hren.", ephemeral=True)
            return

        guild = interaction.guild
        ic_ch = guild.get_channel(IC_CHAT_CHANNEL_ID) if IC_CHAT_CHANNEL_ID else None

        if not ic_ch:
            await interaction.response.send_message(
                "âŒ IC-Chat-Kanal nicht konfiguriert. Bitte wende dich ans Team.",
                ephemeral=True
            )
            return

        try:
            await ic_ch.send(
                f"ðŸ“¢ {self.requester.mention} hat einen **{self.dispatch_type}-Dispatch** abgesendet "
                f"und wartet noch auf eine Einheit! ðŸš¨"
            )
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("âœ… IC-Chat wurde gepingt!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"âŒ Fehler beim Pingen: {e}", ephemeral=True)


async def auto_handy_setup():
    """Postet das Handy-Embed mit den Buttons im Handy-Kanal, falls noch nicht vorhanden."""
    for guild in bot.guilds:
        channel = guild.get_channel(HANDY_CHANNEL_ID)
        if not channel:
            continue
        already_posted = False
        try:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Handy" in emb.title:
                            already_posted = True
                            break
                if already_posted:
                    break
        except Exception:
            pass
        if already_posted:
            print(f"Handy-Embed bereits vorhanden in #{channel.name} â€” kein erneutes Posten.")
            continue
        embed = discord.Embed(
            title="ðŸ“± Handy â€” Einstellungen",
            description=(
                "Willkommen in deinen Handy-Einstellungen!\n\n"
                "Hier kannst du deinen Notruf absetzen, deine Handynummer einsehen "
                "und Social-Media-Apps installieren oder deinstallieren.\n\n"
                "**ðŸš¨ Dispatch-Buttons** â€” Sende einen Notruf an die zustÃ¤ndige Einheit\n"
                "**ðŸ“± Handy Nummer** â€” Zeigt deine persÃ¶nliche LA-Nummer\n"
                "**ðŸ“± Instagram / Parship** â€” Apps installieren & deinstallieren\n\n"
                "âš ï¸ *Du benÃ¶tigst das Item* `ðŸ“±| Handy` *aus dem Shop, um diese Funktionen zu nutzen.*"
            ),
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Kryptik Roleplay â€” Handy System")
        try:
            await channel.send(embed=embed, view=HandyView())
            print(f"Handy-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_handy_setup fehlgeschlagen", str(e), guild)


async def give_handy_channel_access(guild: discord.Guild, member: discord.Member):
    """Gibt einem Member Lesezugriff auf den Handy-Kanal nach Handy-Kauf."""
    channel = guild.get_channel(HANDY_CHANNEL_ID)
    if not channel:
        return
    try:
        await channel.set_permissions(
            member,
            view_channel=True,
            send_messages=False,
            read_message_history=True
        )
    except Exception as e:
        await log_bot_error("Handy-Kanal Berechtigung fehlgeschlagen", str(e), guild)


# â”€â”€ Ticket System â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
                "âŒ Du hast bereits ein offenes Ticket!", ephemeral=True
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
            "âŒ Ticket konnte nicht erstellt werden.", ephemeral=True
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
        title=f"ðŸŽŸ {type_name}",
        description=(
            f"Willkommen {member.mention}!\n\n"
            f"Dein Ticket wurde erfolgreich erstellt. Das Team wird sich schnellstmÃ¶glich um dein Anliegen kÃ¼mmern.\n\n"
            f"**Ticket-Typ:** {type_name}\n"
            f"**Erstellt von:** {member.mention}\n"
            f"**Erstellt am:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    welcome_embed.set_footer(text="Nur Teammitglieder kÃ¶nnen das Ticket schlieÃŸen")

    action_view = TicketActionView()
    await channel.send(content=team_mentions, embed=welcome_embed, view=action_view)

    await interaction.response.send_message(
        f"âœ… Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True
    )

    log_ch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="ðŸ“‚ Ticket GeÃ¶ffnet",
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
            discord.SelectOption(label="Support",            emoji="ðŸŽŸ", value="support",    description="Allgemeiner Support"),
            discord.SelectOption(label="Highteam Ticket",    emoji="ðŸŽŸ", value="highteam",   description="Direkter Kontakt zum Highteam"),
            discord.SelectOption(label="Fraktions Bewerbung",emoji="ðŸŽŸ", value="fraktion",   description="Bewerbung fÃ¼r eine Fraktion"),
            discord.SelectOption(label="Beschwerde Ticket",  emoji="ðŸŽŸ", value="beschwerde", description="Beschwerde einreichen"),
            discord.SelectOption(label="Bug Report",          emoji="ðŸŽŸ", value="bug",        description="Fehler oder Bug melden"),
        ]
        super().__init__(
            placeholder="ðŸŽŸ WÃ¤hle eine Ticket-Art aus...",
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
            placeholder="Person auswÃ¤hlen...",
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
                "âŒ Berechtigung konnte nicht gesetzt werden.", ephemeral=True
            )
            await log_bot_error("Ticket-Zuweisung fehlgeschlagen", str(e), interaction.guild)
            return

        if channel.id in ticket_data:
            ticket_data[channel.id]["handler"]    = str(user)
            ticket_data[channel.id]["handler_id"] = user.id

        assign_embed = discord.Embed(
            description=(
                f"ðŸ‘¤ {user.mention} wurde dem Ticket zugewiesen.\n"
                f"**Zugewiesen von:** {interaction.user.mention}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
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
        emoji="ðŸ”’",
        custom_id="ticket_close_btn"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "âŒ Nur Teammitglieder kÃ¶nnen Tickets schlieÃŸen.", ephemeral=True
            )
            return

        channel = interaction.channel
        data    = ticket_data.get(channel.id)
        if not data:
            await interaction.response.send_message(
                "âŒ Ticket-Daten nicht gefunden.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        ticket_data[channel.id]["handler"]    = str(interaction.user)
        ticket_data[channel.id]["handler_id"] = interaction.user.id

        closing_embed = discord.Embed(
            title="ðŸ”’ Ticket wird geschlossen...",
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
                        transcript_lines.append(f"  â†³ {short}")
        except Exception:
            transcript_lines.append("(Transkript konnte nicht vollstÃ¤ndig geladen werden)")

        transcript_text = "\n".join(transcript_lines)
        transcript_file = discord.File(
            fp=io.BytesIO(transcript_text.encode("utf-8")),
            filename=f"transkript-{channel.name}.txt"
        )

        log_ch = interaction.guild.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            closed_embed = discord.Embed(
                title="ðŸ“ Ticket Geschlossen",
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
                    title="ðŸŽŸ Dein Ticket wurde geschlossen",
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
            await log_bot_error("Ticket lÃ¶schen fehlgeschlagen", str(e), interaction.guild)

    @discord.ui.button(
        label="Person zuweisen",
        style=discord.ButtonStyle.blurple,
        emoji="ðŸ‘¤",
        custom_id="ticket_assign_btn"
    )
    async def assign_person(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "âŒ Nur Teammitglieder kÃ¶nnen Personen zuweisen.", ephemeral=True
            )
            return
        assign_view = AssignView()
        await interaction.response.send_message(
            "WÃ¤hle eine Person aus die dem Ticket zugewiesen werden soll:",
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

        star_display = "â­" * stars + "â˜†" * (5 - stars)

        thank_embed = discord.Embed(
            title="ðŸ’™ Danke fÃ¼r deine Bewertung!",
            description=(
                f"Du hast **{star_display}** ({stars}/5) gegeben.\n\n"
                f"Vielen Dank fÃ¼r dein Feedback! Wir arbeiten stets daran unseren Support zu verbessern. "
                f"Wir hoffen dein Anliegen wurde zu deiner Zufriedenheit gelÃ¶st."
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.response.send_message(embed=thank_embed)

        log_ch = self.guild_ref.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            rating_embed = discord.Embed(
                title="â­ Ticket Bewertung",
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

    @discord.ui.button(label="â­ 1", style=discord.ButtonStyle.grey, custom_id="rating_1")
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 1)

    @discord.ui.button(label="â­ 2", style=discord.ButtonStyle.grey, custom_id="rating_2")
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 2)

    @discord.ui.button(label="â­ 3", style=discord.ButtonStyle.grey, custom_id="rating_3")
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 3)

    @discord.ui.button(label="â­ 4", style=discord.ButtonStyle.grey, custom_id="rating_4")
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 4)

    @discord.ui.button(label="â­ 5", style=discord.ButtonStyle.green, custom_id="rating_5")
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 5)


# â”€â”€ Events â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@bot.event
async def on_ready():
    global bot_start_time, invite_cache
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")

    bot.add_view(TicketSelectView())
    bot.add_view(TicketActionView())
    bot.add_view(HandyView())
    bot.add_view(EinreiseView())

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

    try:
        guild_obj = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Slash Commands synced (Guild): {len(synced)}")
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
            print(f"Ticket-Embed bereits vorhanden in #{channel.name} â€” kein erneutes Posten.")
            continue
        embed = discord.Embed(
            title="ðŸŽŸ Support â€” Ticket erstellen",
            description=(
                "BenÃ¶tigst du Hilfe oder mÃ¶chtest ein Anliegen melden?\n\n"
                "WÃ¤hle unten im MenÃ¼ die passende Ticket-Art aus.\n"
                "Unser Team wird sich schnellstmÃ¶glich um dich kÃ¼mmern.\n\n"
                "**VerfÃ¼gbare Ticket-Arten:**\n"
                "ðŸŽŸ **Support** â€” Allgemeiner Support\n"
                "ðŸŽŸ **Highteam Ticket** â€” Direkter Kontakt zum Highteam\n"
                "ðŸŽŸ **Fraktions Bewerbung** â€” Bewirb dich fÃ¼r eine Fraktion\n"
                "ðŸŽŸ **Beschwerde Ticket** â€” Beschwerde einreichen\n"
                "ðŸŽŸ **Bug Report** â€” Fehler oder Bug melden"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Cryptik Roleplay â€” Support System")
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
            print(f"Lohnliste bereits vorhanden in #{channel.name} â€” kein erneutes Posten.")
            continue
        desc = (
            f"<@&1490855796932739093>\n**1.500 ðŸ’µ StÃ¼ndlich**\n\n"
            f"<@&1490855789844234310>\n**2.500 ðŸ’µ StÃ¼ndlich**\n\n"
            f"<@&1490855790913785886>\n**3.500 ðŸ’µ StÃ¼ndlich**\n\n"
            f"<@&1490855791953973421>\n**4.500 ðŸ’µ StÃ¼ndlich**\n\n"
            f"<@&1490855792671461478>\n**5.500 ðŸ’µ StÃ¼ndlich**\n\n"
            f"<@&1490855793694871595>\n**6.500 ðŸ’µ StÃ¼ndlich**\n\n"
            f"<@&1490855795360006246>\n**1.200 ðŸ’µ StÃ¼ndlich** *(Zusatzlohn)*"
        )
        embed = discord.Embed(
            title="ðŸ’µ Lohnliste ðŸ’µ",
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
                f"âŒ {message.author.mention} Nur Zahlen sind hier erlaubt! Der ZÃ¤hler geht weiter bei **{counting_state['count'] + 1}**.",
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
                f"âŒ {message.author.mention} Du kannst nicht zweimal hintereinander zÃ¤hlen! Der ZÃ¤hler steht bei **{counting_state['count']}**.",
                delete_after=5
            )
        except Exception:
            pass
        return

    if number == expected:
        counting_state["count"] = number
        counting_state["last_user_id"] = message.author.id
        await message.add_reaction("âœ…")
    else:
        counting_state["count"] = 0
        counting_state["last_user_id"] = None
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await message.channel.send(
                f"âŒ {message.author.mention} Falsche Zahl! Erwartet wurde **{expected}**, nicht **{number}**.\n"
                f"Der ZÃ¤hler wurde zurÃ¼ckgesetzt. Fangt wieder bei **1** an!",
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
        await log_bot_error("Nachricht lÃ¶schen (Discord Link)", str(e), guild)
    timeout_ok, roles_removed = await apply_timeout_restrictions(
        member, guild, duration_h=300, reason="Fremden Discord-Link gesendet"
    )
    try:
        embed = discord.Embed(
            description=(
                "> Du hast gegen unsere Server Regeln verstoÃŸen\n\n"
                "> Bitte wende dich an den Support"
            ),
            color=MOD_COLOR
        )
        await member.send(content=member.mention, embed=embed)
    except Exception:
        pass
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        timeout_status = "âœ… Timeout erteilt (300h)" if timeout_ok else "âŒ Timeout fehlgeschlagen â€” Berechtigung prÃ¼fen!"
        rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
        embed = discord.Embed(
            title="ðŸ”¨ Moderation â€” Timeout",
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
            f"{message.author.mention} Bitte sende Links ausschlieÃŸlich im <#{MEMES_CHANNEL_ID}> Kanal",
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
                "> **Verwarnung:** Du hast einen vulgÃ¤ren Ausdruck verwendet.\n\n"
                "> Bitte beachte unsere Serverregeln. Bei weiteren VerstÃ¶ÃŸen folgen Konsequenzen."
            ),
            color=MOD_COLOR
        )
        await message.author.send(content=message.author.mention, embed=embed)
    except Exception:
        pass
    log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="ðŸ”¨ Moderation â€” VulgÃ¤re Sprache",
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
                description="> Du wurdest aufgrund von wiederholtem Spammen fÃ¼r **10 Minuten** stummgeschaltet.",
                color=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        except Exception:
            pass
        log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            timeout_status = "âœ… Timeout erteilt (10min)" if timeout_ok else "âŒ Timeout fehlgeschlagen â€” Berechtigung prÃ¼fen!"
            rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
            embed = discord.Embed(
                title="ðŸ”¨ Moderation â€” Timeout (Spam)",
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
                    "> Bei Wiederholung erhÃ¤ltst du einen 10 Minuten Timeout."
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
        title="ðŸ—‘ï¸ Nachricht gelÃ¶scht",
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
        title="âœï¸ Nachricht bearbeitet",
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
        description += f"**HinzugefÃ¼gt:** {', '.join(r.mention for r in added)}\n"
    if removed:
        description += f"**Entfernt:** {', '.join(r.mention for r in removed)}\n"
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == after.id:
                description += f"**GeÃ¤ndert von:** {entry.user.mention} (`{entry.user}`)"
                break
    except Exception:
        pass
    embed = discord.Embed(
        title="ðŸŽ­ Rollen geÃ¤ndert",
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
        title="ðŸ”¨ Mitglied gebannt",
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
    title = "ðŸ‘¢ Mitglied gekickt" if action == "gekickt" else "ðŸšª Mitglied hat den Server verlassen"
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
                title="ðŸ“¤ Mitglied hat den Server verlassen",
                description=(
                    f"**{member.mention}** hat uns verlassen.\n\n"
                    f"Wir wÃ¼nschen dir alles Gute!\n"
                    f"Du bist jederzeit herzlich willkommen zurÃ¼ckzukehren."
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
                        description="> Bots auf diesen Server hinzufÃ¼gen ist fÃ¼r dich leider nicht erlaubt.",
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
            title="âœ… Mitglied beigetreten",
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
            description += f"**Einladungen von {inviter.display_name}:** {inviter_uses} ðŸŽŸ"
        elif inviter_uses > 0:
            description += "**Eingeladen von:** Vanity-URL (Server-Link)"
        else:
            description += "**Eingeladen von:** Unbekannt *(Bot fehlt 'Server verwalten' Berechtigung?)*"
        embed = discord.Embed(
            title="ðŸ“¥ Neues Mitglied",
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        ping_content = inviter.mention if inviter else None
        await join_log_ch.send(content=ping_content, embed=embed)

    rolle = guild.get_role(WHITELIST_ROLE_ID)
    if rolle:
        try:
            await member.add_roles(rolle)
        except Exception:
            pass

    try:
        embed = discord.Embed(
            description=(
                "> Willkommen auf Kryptik Roleplay deinem RP server mit Ultimativem SpaÃŸ und Hochwertigem RP\n\n"
                "> Wir wÃ¼nschen dir viel SpaÃŸ auf unserem Server und hoffen das du dich bei uns Gut Zurecht findest\n\n"
                "> Solltest du mal Schwierigkeiten haben melde dich gerne Jederzeit Ã¼ber ein Support Ticket im channel "
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
                title="ðŸ“¥ Willkommen auf dem Server!",
                description=(
                    f"Herzlich Willkommen {member.mention} auf **Kryptik Roleplay**!\n\n"
                    f"Wir freuen uns dich hier zu haben.\n"
                    f"Bitte wÃ¤hle deine Einreiseart und erstelle deinen Ausweis."
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
            f"**Spieler:** {member.mention}\n**Bargeld:** {START_CASH:,} ðŸ’µ (Willkommensbonus)"
        )


# â”€â”€ Commands â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! ðŸ‘‹")


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
        await ctx.send("âŒ Ticket-Kanal nicht gefunden!")
        return
    embed = discord.Embed(
        title="ðŸŽŸ Support â€” Ticket erstellen",
        description=(
            "BenÃ¶tigst du Hilfe oder mÃ¶chtest ein Anliegen melden?\n\n"
            "WÃ¤hle unten im MenÃ¼ die passende Ticket-Art aus.\n"
            "Unser Team wird sich schnellstmÃ¶glich um dich kÃ¼mmern.\n\n"
            "**VerfÃ¼gbare Ticket-Arten:**\n"
            "ðŸŽŸ **Support** â€” Allgemeiner Support\n"
            "ðŸŽŸ **Highteam Ticket** â€” Direkter Kontakt zum Highteam\n"
            "ðŸŽŸ **Fraktions Bewerbung** â€” Bewirb dich fÃ¼r eine Fraktion\n"
            "ðŸŽŸ **Beschwerde Ticket** â€” Beschwerde einreichen\n"
            "ðŸŽŸ **Bug Report** â€” Fehler oder Bug melden"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Cryptik Roleplay â€” Support System")
    view = TicketSelectView()
    await channel.send(embed=embed, view=view)
    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="handysetup")
async def handysetup(ctx):
    """Postet das Handy-Embed erneut im Handy-Kanal. Nur fÃ¼r Admins."""
    if not is_admin(ctx.author):
        return
    channel = ctx.guild.get_channel(HANDY_CHANNEL_ID)
    if not channel:
        await ctx.send("âŒ Handy-Kanal nicht gefunden!")
        return
    embed = discord.Embed(
        title="ðŸ“± Handy â€” Einstellungen",
        description=(
            "Willkommen in deinen Handy-Einstellungen!\n\n"
            "Hier kannst du deinen Notruf absetzen, deine Handynummer einsehen "
            "und Social-Media-Apps installieren oder deinstallieren.\n\n"
            "**ðŸš¨ Dispatch-Buttons** â€” Sende einen Notruf an die zustÃ¤ndige Einheit\n"
            "**ðŸ“± Handy Nummer** â€” Zeigt deine persÃ¶nliche LA-Nummer\n"
            "**ðŸ“± Instagram / Parship** â€” Apps installieren & deinstallieren\n\n"
            "âš ï¸ *Du benÃ¶tigst das Item* `ðŸ“±| Handy` *aus dem Shop, um diese Funktionen zu nutzen.*"
        ),
        color=0x00BFFF,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Kryptik Roleplay â€” Handy System")
    await channel.send(embed=embed, view=HandyView())
    try:
        await ctx.message.delete()
    except Exception:
        pass


# â”€â”€ Economy Slash Commands â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def channel_error(channel_id: int) -> str:
    return f"âŒ Du kannst diesen Command nur hier ausfÃ¼hren: <#{channel_id}>"


# /lohn-abholen
@bot.tree.command(name="lohn-abholen", description="Hole deinen stÃ¼ndlichen Lohn ab", guild=discord.Object(id=GUILD_ID))
async def lohn_abholen(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != LOHN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(LOHN_CHANNEL_ID), ephemeral=True)
        return

    main_wages = [WAGE_ROLES[r] for r in role_ids if r in WAGE_ROLES]
    if len(main_wages) > 1:
        await interaction.response.send_message(
            "âŒ Du hast mehrere Lohnklassen. Bitte wende dich ans Team.", ephemeral=True
        )
        return
    if not main_wages:
        await interaction.response.send_message(
            "âŒ Du hast keine Lohnklasse und kannst keinen Lohn abholen.", ephemeral=True
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
                f"âŒ Du kannst deinen Lohn erst in **{mins}m {secs}s** wieder abholen.",
                ephemeral=True
            )
            return

    user_data["bank"]      += total_wage
    user_data["last_wage"]  = now.isoformat()
    save_economy(eco)

    embed = discord.Embed(
        title="ðŸ’µ Lohn abgeholt!",
        description=(
            f"Du hast **{total_wage:,} ðŸ’µ** auf dein Konto erhalten.\n"
            f"**Kontostand:** {user_data['bank']:,} ðŸ’µ"
        ),
        color=LOG_COLOR,
        timestamp=now
    )
    await interaction.response.send_message(embed=embed)


# /kontostand
@bot.tree.command(name="kontostand", description="Zeigt den Kontostand an (Team: auch per @ErwÃ¤hnung)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Mitglied dessen Kontostand abgerufen werden soll")
async def kontostand(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids  = [r.id for r in interaction.user.roles]
    is_team_m = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids

    if nutzer is not None:
        if not is_team_m:
            await interaction.response.send_message(
                "âŒ Du hast keine Berechtigung, den Kontostand anderer Mitglieder abzurufen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    else:
        if not is_team_m and interaction.channel.id != BANK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
            return
        if not is_team_m and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("âŒ Du hast keine Berechtigung.", ephemeral=True)
            return
        ziel = interaction.user

    eco       = load_economy()
    user_data = get_user(eco, ziel.id)
    save_economy(eco)

    titel = "ðŸ’³ Kontostand" if ziel.id == interaction.user.id else f"ðŸ’³ Kontostand â€” {ziel.display_name}"
    embed = discord.Embed(
        title=titel,
        description=(
            f"**Bargeld:** {user_data['cash']:,} ðŸ’µ\n"
            f"**Bank:** {user_data['bank']:,} ðŸ’µ\n"
            f"**Gesamt:** {user_data['cash'] + user_data['bank']:,} ðŸ’µ"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /einzahlen
@bot.tree.command(name="einzahlen", description="Zahle Bargeld auf dein Bankkonto ein", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wÃ¤hlen oder eingeben (1.000 â€“ 10.000.000 ðŸ’µ)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def einzahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("âŒ Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("âŒ Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["cash"] < betrag:
        await interaction.response.send_message(
            f"âŒ Nicht genug Bargeld. Dein Bargeld: **{user_data['cash']:,} ðŸ’µ**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - user_data["daily_deposit"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"âŒ Tageslimit erreicht. Du kannst heute noch **{remaining:,} ðŸ’µ** einzahlen. "
                f"(Limit: **{user_limit:,} ðŸ’µ**)",
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
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} ðŸ’µ\n"
        f"**Bargeld danach:** {user_data['cash']:,} ðŸ’µ | **Bank danach:** {user_data['bank']:,} ðŸ’µ"
    )

    embed = discord.Embed(
        title="ðŸ¦ Eingezahlt",
        description=(
            f"**Eingezahlt:** {betrag:,} ðŸ’µ\n"
            f"**Bargeld:** {user_data['cash']:,} ðŸ’µ\n"
            f"**Bank:** {user_data['bank']:,} ðŸ’µ"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /auszahlen
@bot.tree.command(name="auszahlen", description="Hebe Geld von deinem Bankkonto ab", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wÃ¤hlen oder eingeben (1.000 â€“ 10.000.000 ðŸ’µ)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def auszahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("âŒ Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("âŒ Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["bank"] < betrag:
        await interaction.response.send_message(
            f"âŒ Nicht genug Guthaben. Dein Kontostand: **{user_data['bank']:,} ðŸ’µ**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - user_data["daily_withdraw"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"âŒ Tageslimit erreicht. Du kannst heute noch **{remaining:,} ðŸ’µ** auszahlen. "
                f"(Limit: **{user_limit:,} ðŸ’µ**)",
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
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} ðŸ’µ\n"
        f"**Bargeld danach:** {user_data['cash']:,} ðŸ’µ | **Bank danach:** {user_data['bank']:,} ðŸ’µ"
    )

    embed = discord.Embed(
        title="ðŸ’¸ Ausgezahlt",
        description=(
            f"**Ausgezahlt:** {betrag:,} ðŸ’µ\n"
            f"**Bargeld:** {user_data['cash']:,} ðŸ’µ\n"
            f"**Bank:** {user_data['bank']:,} ðŸ’µ"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /ueberweisen
@bot.tree.command(name="ueberweisen", description="Ãœberweise Geld an einen anderen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="EmpfÃ¤nger", betrag="Betrag wÃ¤hlen oder eingeben (1.000 â€“ 10.000.000 ðŸ’µ)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def ueberweisen(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("âŒ Du hast keine Berechtigung.", ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("âŒ Du kannst nicht an dich selbst Ã¼berweisen.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("âŒ Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco        = load_economy()
    sender     = get_user(eco, interaction.user.id)
    receiver   = get_user(eco, nutzer.id)
    reset_daily_if_needed(sender)

    if sender["bank"] < betrag:
        await interaction.response.send_message(
            f"âŒ Nicht genug Guthaben. Dein Kontostand: **{sender['bank']:,} ðŸ’µ**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = sender.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - sender["daily_transfer"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"âŒ Tageslimit erreicht. Du kannst heute noch **{remaining:,} ðŸ’µ** Ã¼berweisen. "
                f"(Limit: **{user_limit:,} ðŸ’µ**)",
                ephemeral=True
            )
            return
        sender["daily_transfer"] += betrag

    sender["bank"]   -= betrag
    receiver["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Ãœberweisung",
        f"**Von:** {interaction.user.mention} â†’ **An:** {nutzer.mention}\n"
        f"**Betrag:** {betrag:,} ðŸ’µ | **Sender-Bank danach:** {sender['bank']:,} ðŸ’µ"
    )

    embed = discord.Embed(
        title="ðŸ’³ Ãœberweisung",
        description=(
            f"**An:** {nutzer.mention}\n"
            f"**Betrag:** {betrag:,} ðŸ’µ\n"
            f"**Dein Kontostand:** {sender['bank']:,} ðŸ’µ"
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
                title="ðŸ›’ Shop",
                description="Der Shop ist aktuell leer.",
                color=LOG_COLOR
            ),
            ephemeral=True
        )
        return

    lines = []
    for item in items:
        line = f"**{item['name']}** â€” {item['price']:,} ðŸ’µ"
        ar = item.get("allowed_role")
        if ar:
            r = interaction.guild.get_role(ar)
            line += f"  ðŸ”’ *{r.name if r else ar}*"
        lines.append(line)

    embed = discord.Embed(
        title="ðŸ›’ Shop",
        description="\n".join(lines),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Kaufen mit /buy [itemname] â€¢ Nur mit Bargeld mÃ¶glich")
    await interaction.response.send_message(embed=embed, ephemeral=True)


def find_inventory_item(inventory: list, query: str):
    q = query.lower().strip()
    q_norm = normalize_item_name(query)
    for i in inventory:
        if i.lower() == q:
            return i
    for i in inventory:
        if i.lower().startswith(q):
            return i
    for i in inventory:
        if q in i.lower():
            return i
    for i in inventory:
        if normalize_item_name(i) == q_norm:
            return i
    for i in inventory:
        if normalize_item_name(i).startswith(q_norm):
            return i
    for i in inventory:
        if q_norm in normalize_item_name(i):
            return i
    return None


def find_shop_item(items, query: str):
    q = query.lower().strip()
    q_norm = normalize_item_name(query)
    for item in items:
        if item["name"].lower() == q:
            return item
    for item in items:
        if item["name"].lower().startswith(q):
            return item
    for item in items:
        if q in item["name"].lower():
            return item
    for item in items:
        if normalize_item_name(item["name"]) == q_norm:
            return item
    for item in items:
        if normalize_item_name(item["name"]).startswith(q_norm):
            return item
    for item in items:
        if q_norm in normalize_item_name(item["name"]):
            return item
    return None


# /buy
@bot.tree.command(name="buy", description="Kaufe ein Item aus dem Shop", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(itemname="Name des Items das du kaufen mÃ¶chtest")
async def buy(interaction: discord.Interaction, itemname: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("âŒ Du hast keine Berechtigung.", ephemeral=True)
        return

    items = load_shop()
    item  = find_shop_item(items, itemname)

    if not item:
        await interaction.response.send_message(
            f"âŒ Item **{itemname}** wurde nicht gefunden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    allowed_role = item.get("allowed_role")
    if allowed_role and not is_adm:
        if allowed_role not in role_ids:
            rolle_obj = interaction.guild.get_role(allowed_role)
            rname     = rolle_obj.name if rolle_obj else f"<@&{allowed_role}>"
            await interaction.response.send_message(
                f"âŒ Dieses Item ist nur fÃ¼r die Rolle **{rname}** erhÃ¤ltlich.",
                ephemeral=True
            )
            return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)

    if user_data["cash"] < item["price"]:
        await interaction.response.send_message(
            f"âŒ Du hast nicht genug **Bargeld**.\n"
            f"Preis: **{item['price']:,} ðŸ’µ** | Dein Bargeld: **{user_data['cash']:,} ðŸ’µ**\n"
            f"â„¹ï¸ KÃ¤ufe sind nur mit Bargeld mÃ¶glich. Hebe Geld mit `/auszahlen` ab.",
            ephemeral=True
        )
        return

    user_data["cash"] -= item["price"]
    if "inventory" not in user_data:
        user_data["inventory"] = []
    user_data["inventory"].append(item["name"])
    save_economy(eco)

    # â”€â”€ Handy-Kauf: Kanal-Berechtigung geben â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if normalize_item_name(item["name"]) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, interaction.user)

    embed = discord.Embed(
        title="âœ… Gekauft!",
        description=(
            f"Du hast **{item['name']}** fÃ¼r **{item['price']:,} ðŸ’µ** gekauft.\n"
            f"**Verbleibendes Bargeld:** {user_data['cash']:,} ðŸ’µ"
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
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["custom_limit"] = limit
    save_economy(eco)

    embed = discord.Embed(
        title="âš™ï¸ Limit gesetzt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Neues Tageslimit:** {limit:,} ðŸ’µ\n"
            f"*(gilt fÃ¼r Einzahlen, Auszahlen & Ãœberweisen)*"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesetzt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


# /money-add (Admin only)
@bot.tree.command(name="money-add", description="[ADMIN] FÃ¼ge einem Spieler Geld hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
@app_commands.default_permissions(administrator=True)
async def money_add(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("âŒ Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("âŒ Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld hinzugefÃ¼gt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** +{betrag:,} ðŸ’µ\n"
        f"**Bargeld danach:** {user_data['cash']:,} ðŸ’µ\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="ðŸ’° Geld hinzugefÃ¼gt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**HinzugefÃ¼gt:** {betrag:,} ðŸ’µ\n"
            f"**Bargeld:** {user_data['cash']:,} ðŸ’µ"
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
        await interaction.response.send_message("âŒ Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("âŒ Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] = max(0, user_data["cash"] - betrag)
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld entfernt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** -{betrag:,} ðŸ’µ\n"
        f"**Bargeld danach:** {user_data['cash']:,} ðŸ’µ\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="ðŸ’¸ Geld entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernt:** {betrag:,} ðŸ’µ\n"
            f"**Bargeld:** {user_data['cash']:,} ðŸ’µ"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /item-add (Admin only)
@bot.tree.command(name="item-add", description="[ADMIN] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", itemname="Itemname (muss im Shop vorhanden sein)")
@app_commands.autocomplete(itemname=shop_item_autocomplete)
@app_commands.default_permissions(administrator=True)
async def item_add(interaction: discord.Interaction, nutzer: discord.Member, itemname: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("âŒ Kein Zugriff.", ephemeral=True)
        return

    shop_items = load_shop()
    shop_item  = find_shop_item(shop_items, itemname)
    if not shop_item:
        await interaction.response.send_message(
            f"âŒ Das Item **{itemname}** existiert nicht im Shop.\n"
            f"Es kÃ¶nnen nur vorhandene Shop-Items vergeben werden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    if "inventory" not in user_data:
        user_data["inventory"] = []
    user_data["inventory"].append(shop_item["name"])
    save_economy(eco)

    # Handy-Kanal-Berechtigung geben wenn Handy vergeben wird
    if normalize_item_name(shop_item["name"]) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, nutzer)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="ðŸ“¦ Item hinzugefÃ¼gt",
            description=f"**{shop_item['name']}** wurde **{nutzer.mention}** hinzugefÃ¼gt.",
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
        await interaction.response.send_message("âŒ Kein Zugriff.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inventory = user_data.get("inventory", [])

    match = find_inventory_item(inventory, itemname)
    if not match:
        await interaction.response.send_message(
            f"âŒ **{nutzer.display_name}** besitzt kein Item namens **{itemname}**.", ephemeral=True
        )
        return

    inventory.remove(match)
    user_data["inventory"] = inventory
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="ðŸ“¦ Item entfernt",
            description=f"**{match}** wurde von **{nutzer.mention}** entfernt.",
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        ),
        ephemeral=True
    )


# /shop-add (Team only)
class ShopAddConfirmView(discord.ui.View):
    def __init__(self, name: str, price: int, allowed_role_id: int | None = None):
        super().__init__(timeout=60)
        self.name            = name
        self.price           = price
        self.allowed_role_id = allowed_role_id

    @discord.ui.button(label="âœ… BestÃ¤tigen", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = load_shop()
        entry = {"name": self.name, "price": self.price}
        if self.allowed_role_id:
            entry["allowed_role"] = self.allowed_role_id
        items.append(entry)
        save_shop(items)
        for item in self.children:
            item.disabled = True
        rolle_info = ""
        if self.allowed_role_id:
            r = interaction.guild.get_role(self.allowed_role_id)
            rolle_info = f"\n**Nur fÃ¼r:** {r.mention if r else self.allowed_role_id}"
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="âœ… Item hinzugefÃ¼gt",
                description=f"**{self.name}** fÃ¼r **{self.price:,} ðŸ’µ** wurde zum Shop hinzugefÃ¼gt.{rolle_info}",
                color=LOG_COLOR
            ),
            view=self
        )

    @discord.ui.button(label="âŒ Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="âŒ Abgebrochen",
                description="Das Item wurde nicht hinzugefÃ¼gt.",
                color=MOD_COLOR
            ),
            view=self
        )


@bot.tree.command(name="shop-add", description="[TEAM] FÃ¼ge ein neues Item zum Shop hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    itemname="Name des Items",
    preis="Preis in $",
    rolle="(Optional) Nur diese Rolle kann das Item kaufen"
)
@app_commands.default_permissions(manage_messages=True)
async def shop_add(interaction: discord.Interaction, itemname: str, preis: int, rolle: discord.Role = None):
    if not is_team(interaction.user):
        await interaction.response.send_message("âŒ Kein Zugriff.", ephemeral=True)
        return

    if preis <= 0:
        await interaction.response.send_message("âŒ Preis muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    rolle_info = f"\n**Nur fÃ¼r:** {rolle.mention}" if rolle else "\n**RollenbeschrÃ¤nkung:** Keine"
    embed = discord.Embed(
        title="ðŸ›’ Neues Item hinzufÃ¼gen?",
        description=(
            f"**Name:** {itemname}\n"
            f"**Preis:** {preis:,} ðŸ’µ"
            f"{rolle_info}\n\n"
            f"Bitte bestÃ¤tige das HinzufÃ¼gen."
        ),
        color=LOG_COLOR
    )
    await interaction.response.send_message(
        embed=embed,
        view=ShopAddConfirmView(itemname, preis, rolle.id if rolle else None),
        ephemeral=True
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# WARN SYSTEM
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@bot.tree.command(name="warn", description="[TEAM] Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
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
        title="âš ï¸ Verwarnung",
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
        f"âœ… Verwarnung fÃ¼r {nutzer.mention} gespeichert. (Warns gesamt: **{warn_count}**)", ephemeral=True
    )

    if warn_count >= WARN_AUTO_TIMEOUT_COUNT:
        timeout_dur = timedelta(days=2)
        try:
            await nutzer.timeout(timeout_dur, reason=f"Automatischer Timeout: {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht")
        except Exception:
            pass
        try:
            roles_to_remove = [r for r in nutzer.roles if r != interaction.guild.default_role and not r.managed]
            if roles_to_remove:
                await nutzer.remove_roles(*roles_to_remove, reason="Automatischer Timeout: 3 Warns")
        except Exception:
            pass
        try:
            dm_embed = discord.Embed(
                title="ðŸ”‡ Du wurdest getimeoutet",
                description=(
                    f"Du hast auf **{interaction.guild.name}** {WARN_AUTO_TIMEOUT_COUNT} Verwarnungen erhalten "
                    f"und wurdest daher fÃ¼r **2 Tage** getimeoutet.\n\n"
                    f"**Letzte Verwarnung:**\n"
                    f"Grund: {grund}\nKonsequenz: {konsequenz}\n\n"
                    f"Deine Rollen wurden vorÃ¼bergehend entfernt.\n"
                    f"Nach dem Timeout melde dich bitte bei einem Teammitglied."
                ),
                color=MOD_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            await nutzer.send(embed=dm_embed)
        except Exception:
            pass
        timeout_embed = discord.Embed(
            title="ðŸ”‡ Automatischer Timeout",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Grund:** {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht\n"
                f"**Dauer:** 2 Tage\n"
                f"**Rollen entfernt:** âœ…"
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        if log_ch:
            await log_ch.send(embed=timeout_embed)


@bot.tree.command(name="warn-list", description="Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def warn_list(interaction: discord.Interaction, nutzer: discord.Member):
    if not is_team(interaction.user):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"âœ… {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        ts  = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** â€” {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"âš ï¸ Warns von {nutzer.display_name}",
        description="\n".join(lines),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesamt: {len(user_warns)} Warn(s)")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="remove-warn", description="[TEAM] Letzte Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler")
async def remove_warn(interaction: discord.Interaction, nutzer: discord.Member):
    if not is_team(interaction.user):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"â„¹ï¸ {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_warns(warns)

    embed = discord.Embed(
        title="âœ… Verwarnung entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernte Verwarnung:** {removed['grund']}\n"
            f"**Verbleibende Warns:** {len(user_warns)}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /rucksack
@bot.tree.command(name="rucksack", description="Zeige dein Inventar an (Team: auch per @ErwÃ¤hnung)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Spieler dessen Inventar angezeigt werden soll")
async def rucksack(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids = [r.id for r in interaction.user.roles]
    is_team_m = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids
    allowed  = is_team_m or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES)

    if nutzer is not None:
        if not is_team_m:
            await interaction.response.send_message(
                "âŒ Du hast keine Berechtigung, den Rucksack anderer Spieler einzusehen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    else:
        if not is_team_m and interaction.channel.id != RUCKSACK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
            return
        if not allowed:
            await interaction.response.send_message("âŒ Du hast keine Berechtigung.", ephemeral=True)
            return
        ziel = interaction.user

    eco       = load_economy()
    user_data = get_user(eco, ziel.id)
    inventory = user_data.get("inventory", [])

    if not inventory:
        desc = f"*{'Dein' if ziel.id == interaction.user.id else ziel.display_name + 's'} Rucksack ist leer.*"
    else:
        from collections import Counter
        counts = Counter(inventory)
        desc   = "\n".join(f"â€¢ **{item}** Ã—{count}" for item, count in counts.items())

    embed = discord.Embed(
        title=f"ðŸŽ’ Rucksack von {ziel.display_name}",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /uebergeben
@bot.tree.command(name="uebergeben", description="Gib ein Item aus deinem Inventar an jemanden weiter", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="EmpfÃ¤nger", item="Item auswÃ¤hlen", menge="Wie viele mÃ¶chtest du Ã¼bergeben? (Standard: 1)")
@app_commands.autocomplete(item=inventory_item_autocomplete)
async def uebergeben(interaction: discord.Interaction, nutzer: discord.Member, item: str, menge: int = 1):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != RUCKSACK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("âŒ Du kannst nicht an dich selbst Ã¼bergeben.", ephemeral=True)
        return

    if menge < 1:
        await interaction.response.send_message("âŒ Die Menge muss mindestens 1 sein.", ephemeral=True)
        return

    eco        = load_economy()
    giver_data = get_user(eco, interaction.user.id)
    inv        = giver_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if not match:
        await interaction.response.send_message(
            f"âŒ **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        return

    available = inv.count(match)
    if available < menge:
        await interaction.response.send_message(
            f"âŒ Du hast nur **{available}Ã—** **{match}** im Inventar, aber mÃ¶chtest **{menge}Ã—** Ã¼bergeben.",
            ephemeral=True
        )
        return

    for _ in range(menge):
        inv.remove(match)
    receiver_data = get_user(eco, nutzer.id)
    receiver_data.setdefault("inventory", []).extend([match] * menge)
    save_economy(eco)

    # Handy weitergeben â†’ Kanal-Berechtigung fÃ¼r EmpfÃ¤nger
    if normalize_item_name(match) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, nutzer)

    menge_text = f"Ã—{menge}" if menge > 1 else ""
    embed = discord.Embed(
        title="ðŸ¤ Item Ã¼bergeben",
        description=(
            f"**Von:** {interaction.user.mention}\n"
            f"**An:** {nutzer.mention}\n"
            f"**Item:** {match} {menge_text}"
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

    match = find_inventory_item(inv, item)
    if not match:
        await interaction.response.send_message(
            f"âŒ **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        return

    inv.remove(match)
    save_economy(eco)

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
        title="ðŸ•µï¸ Item versteckt",
        description=(
            f"**Item:** {match}\n"
            f"**Versteckt an:** {ort}\n\n"
            f"Nur du kannst es wieder herausnehmen."
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, view=view)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TEAM ITEM COMMANDS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@bot.tree.command(name="item-geben", description="[TEAM] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname (muss im Shop vorhanden sein)")
@app_commands.autocomplete(item=shop_item_autocomplete)
async def item_geben(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    shop_items = load_shop()
    shop_item  = find_shop_item(shop_items, item)
    if not shop_item:
        await interaction.response.send_message(
            f"âŒ Das Item **{item}** existiert nicht im Shop.\n"
            f"Es kÃ¶nnen nur vorhandene Shop-Items vergeben werden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data.setdefault("inventory", []).append(shop_item["name"])
    save_economy(eco)

    if normalize_item_name(shop_item["name"]) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, nutzer)

    embed = discord.Embed(
        title="ðŸŽ Item gegeben",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {shop_item['name']}\n"
            f"**Vergeben von:** {interaction.user.mention}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="item-entfernen", description="[TEAM] Entferne ein Item von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname")
async def item_entfernen(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inv       = user_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if not match:
        await interaction.response.send_message(
            f"âŒ **{item}** ist nicht im Inventar von {nutzer.mention}.", ephemeral=True
        )
        return

    inv.remove(match)
    save_economy(eco)

    embed = discord.Embed(
        title="ðŸ—‘ï¸ Item entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {match}\n"
            f"**Entfernt von:** {interaction.user.mention}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# KARTENKONTROLLE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

KARTENKONTROLLE_CHANNEL_ID = 1491116234459185162


@bot.tree.command(name="kartenkontrolle", description="[TEAM] Sendet eine DM-Erinnerung zur Kartenkontrolle an alle Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def kartenkontrolle(interaction: discord.Interaction):
    if not is_team(interaction.user):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
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
                title="ðŸªª Kartenkontrolle",
                description=(
                    f"**Hallo {member.display_name}!**\n\n"
                    f"Es findet gerade eine **Kartenkontrolle** statt.\n"
                    f"Bitte begib dich in den Kanal:\n"
                    f"[ðŸ”— Zur Kartenkontrolle]({channel_link})\n\n"
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
        f"âœ… Kartenkontrolle-DM gesendet!\n**Erfolgreich:** {sent} | **Fehlgeschlagen (DMs zu):** {failed}",
        ephemeral=True
    )


# â”€â”€ Ausweis Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_ausweis():
    if AUSWEIS_FILE.exists():
        with open(AUSWEIS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_ausweis(data):
    with open(AUSWEIS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_ausweisnummer():
    letters = random.choices(string.ascii_uppercase, k=2)
    digits  = random.choices(string.digits, k=6)
    return "".join(letters) + "-" + "".join(digits)


# â”€â”€ Einreise DM Flow â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def einreise_chat_flow(channel: discord.TextChannel, member: discord.Member, guild: discord.Guild, einreise_typ: str):
    def dm_check(m):
        return m.author.id == member.id and isinstance(m.channel, discord.DMChannel)

    felder = [
        ("vorname",       "ðŸ“ **Vorname** â€” Bitte gib deinen Vornamen ein:"),
        ("nachname",      "ðŸ“ **Nachname** â€” Bitte gib deinen Nachnamen ein:"),
        ("geburtsdatum",  "ðŸ“ **Geburtsdatum** â€” Bitte gib dein Geburtsdatum ein (Format: TT.MM.JJJJ):"),
        ("alter",         "ðŸ“ **Alter** â€” Bitte gib dein Alter ein (z.B. 25):"),
        ("nationalitaet", "ðŸ“ **NationalitÃ¤t** â€” Bitte gib deine NationalitÃ¤t ein (z.B. Deutsch):"),
        ("wohnort",       "ðŸ“ **Wohnort** â€” Bitte gib deinen Wohnort ein (z.B. Los Santos):"),
    ]

    antworten = {}
    typ_label = "ðŸ¤µ Legale Einreise" if einreise_typ == "legal" else "ðŸ¥· Illegale Einreise"

    try:
        dm = await member.create_dm()
        await dm.send(
            f"ðŸªª **Ausweis-Erstellung gestartet!** ({typ_label})\n"
            f"Beantworte bitte die folgenden **{len(felder)} Fragen**. "
            f"Du hast jeweils **2 Minuten** pro Antwort."
        )
    except Exception:
        await channel.send(
            f"{member.mention} âŒ Ich kann dir keine DM senden. Bitte aktiviere DMs von Servermitgliedern.",
            delete_after=15
        )
        return

    for key, frage in felder:
        await dm.send(frage)
        try:
            antwort = await bot.wait_for("message", check=dm_check, timeout=120.0)
            antworten[key] = antwort.content.strip()
        except asyncio.TimeoutError:
            await dm.send("âŒ Zeit abgelaufen! Bitte wÃ¤hle deine Einreiseart erneut.")
            return

    ausweisnummer = generate_ausweisnummer()

    ausweis_data = load_ausweis()
    ausweis_data[str(member.id)] = {
        "vorname":       antworten["vorname"],
        "nachname":      antworten["nachname"],
        "geburtsdatum":  antworten["geburtsdatum"],
        "alter":         antworten["alter"],
        "nationalitaet": antworten["nationalitaet"],
        "wohnort":       antworten["wohnort"],
        "einreise_typ":  einreise_typ,
        "ausweisnummer": ausweisnummer,
        "discord_name":  str(member),
        "discord_id":    member.id,
    }
    save_ausweis(ausweis_data)

    rollen_zu_vergeben = [
        guild.get_role(rid)
        for rid in CHARAKTER_ROLLEN
        if guild.get_role(rid) is not None
    ]
    if rollen_zu_vergeben:
        try:
            await member.add_roles(*rollen_zu_vergeben, reason="Charakter erstellt")
        except Exception:
            pass

    embed = discord.Embed(
        title="ðŸªª Ausweis ausgestellt",
        description="Dein Ausweis wurde erfolgreich erstellt!",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Name",          value=f"{antworten['vorname']} {antworten['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum",  value=antworten["geburtsdatum"],                          inline=True)
    embed.add_field(name="Alter",         value=antworten["alter"],                                 inline=True)
    embed.add_field(name="NationalitÃ¤t",  value=antworten["nationalitaet"],                         inline=True)
    embed.add_field(name="Wohnort",       value=antworten["wohnort"],                               inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                          inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{ausweisnummer}`",                               inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Kryptik Roleplay â€” Ausweis")

    await dm.send("âœ… **Dein Ausweis wurde erfolgreich erstellt!**", embed=embed)


# â”€â”€ Einreise Select Menu â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class EinreiseSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Legale Einreise",
                emoji="ðŸ¤µ",
                value="legal",
                description="Einreise als legaler Bewohner"
            ),
            discord.SelectOption(
                label="Illegale Einreise",
                emoji="ðŸ¥·",
                value="illegal",
                description="Einreise als illegale Person"
            ),
        ]
        super().__init__(
            placeholder="âœˆï¸ WÃ¤hle deine Einreiseart...",
            options=options,
            custom_id="einreise_select_main"
        )

    async def callback(self, interaction: discord.Interaction):
        member   = interaction.user
        guild    = interaction.guild
        role_ids = [r.id for r in member.roles]

        if LEGAL_ROLE_ID in role_ids or ILLEGAL_ROLE_ID in role_ids:
            await interaction.response.send_message(
                "âŒ Du hast bereits eine Einreiseart gewÃ¤hlt. Eine Ã„nderung ist nur durch den RP-Tod mÃ¶glich.",
                ephemeral=True
            )
            return

        typ     = self.values[0]
        role_id = LEGAL_ROLE_ID if typ == "legal" else ILLEGAL_ROLE_ID
        role    = guild.get_role(role_id)

        if role:
            try:
                await member.add_roles(role, reason=f"Einreise: {typ}")
            except Exception as e:
                await log_bot_error("Einreise-Rolle vergeben fehlgeschlagen", str(e), guild)

        await interaction.response.send_message(
            f"âœ… **{'Legale' if typ == 'legal' else 'Illegale'} Einreise** gewÃ¤hlt!\n"
            f"Die Ausweis-Erstellung startet gleich hier im Chat. Bitte beachte die Fragen.",
            ephemeral=True
        )
        asyncio.create_task(einreise_chat_flow(interaction.channel, member, guild, typ))


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
            title="âœˆï¸ Einreise â€” Kryptik Roleplay",
            description=(
                "ðŸ¤µâ€â™‚ï¸ **Legale Einreise** ðŸ¤µâ€â™‚ï¸\n"
                "Du wirst auf unserem Server als Legale Person einreisen. "
                "Du darfst als Legaler Bewohner keine Illegalen AktivitÃ¤ten ausfÃ¼hren.\n\n"
                "ðŸ¥· **Illegale Einreise** ðŸ¥·\n"
                "Du wirst auf unserem Server als Illegale Person einreisen. "
                "Du darfst keine Staatlichen Berufe ausÃ¼ben.\n\n"
                "âš ï¸ **Hinweis** âš ï¸\n"
                "Eine Ã„nderung der Einreiseart ist nur durch den RP-Tod deines Charakters mÃ¶glich."
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Kryptik Roleplay â€” Einreisesystem")
        try:
            await channel.send(embed=embed, view=EinreiseView())
            print(f"Einreise-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_einreise_setup fehlgeschlagen", str(e), guild)


# /ausweisen
@bot.tree.command(name="ausweisen", description="Zeige deinen Ausweis vor", guild=discord.Object(id=GUILD_ID))
async def ausweisen(interaction: discord.Interaction):
    if interaction.channel.id != AUSWEIS_CHANNEL_ID and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message(
            f"âŒ Diesen Command kannst du nur in <#{AUSWEIS_CHANNEL_ID}> benutzen.", ephemeral=True
        )
        return

    ausweis_data = load_ausweis()
    entry = ausweis_data.get(str(interaction.user.id))

    if not entry:
        await interaction.response.send_message(
            "âŒ Du hast noch keinen Ausweis. WÃ¤hle zuerst deine Einreiseart und erstelle deinen Ausweis.",
            ephemeral=True
        )
        return

    typ_label = "ðŸ¤µ Legale Einreise" if entry.get("einreise_typ") == "legal" else "ðŸ¥· Illegale Einreise"

    embed = discord.Embed(
        title="ðŸªª Personalausweis",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="Name",          value=f"{entry['vorname']} {entry['nachname']}",  inline=True)
    embed.add_field(name="Geburtsdatum",  value=entry["geburtsdatum"],                      inline=True)
    embed.add_field(name="Alter",         value=entry.get("alter", "?"),                    inline=True)
    embed.add_field(name="NationalitÃ¤t",  value=entry["nationalitaet"],                     inline=True)
    embed.add_field(name="Wohnort",       value=entry["wohnort"],                           inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                  inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{entry['ausweisnummer']}`",              inline=False)
    embed.set_footer(text="Kryptik Roleplay â€” Personalausweis")

    await interaction.response.send_message(embed=embed)


# /ausweis-remove (Admin only)
@bot.tree.command(name="ausweis-remove", description="[ADMIN] Loescht den Ausweis eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler dessen Ausweis geloescht werden soll")
@app_commands.default_permissions(administrator=True)
async def ausweis_remove(interaction: discord.Interaction, nutzer: discord.Member):
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    uid = str(nutzer.id)

    if uid not in ausweis_data:
        await interaction.response.send_message(
            f"âŒ {nutzer.mention} hat keinen Ausweis.", ephemeral=True
        )
        return

    del ausweis_data[uid]
    save_ausweis(ausweis_data)

    embed = discord.Embed(
        title="ðŸ—‘ï¸ Ausweis gelÃ¶scht",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**GelÃ¶scht von:** {interaction.user.mention}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# â”€â”€ Admin Ausweis-Erstellen (Chat-basiert) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def ausweis_create_dm_flow(admin: discord.Member, guild: discord.Guild, target: discord.Member, original_channel: discord.TextChannel):
    def dm_check(m):
        return m.author.id == admin.id and isinstance(m.channel, discord.DMChannel)

    felder = [
        ("vorname",       "ðŸ“ **Vorname** des Spielers:"),
        ("nachname",      "ðŸ“ **Nachname** des Spielers:"),
        ("geburtsdatum",  "ðŸ“ **Geburtsdatum** (Format: TT.MM.JJJJ):"),
        ("alter",         "ðŸ“ **Alter** (z.B. 25):"),
        ("herkunft",      "ðŸ“ **Herkunft** (z.B. Deutsch):"),
        ("wohnort",       "ðŸ“ **Wohnort** (z.B. Los Santos):"),
        ("einreise_typ",  "ðŸ“ **Einreiseart** â€” Tippe `legal` oder `illegal`:"),
    ]

    antworten = {}

    try:
        dm = await admin.create_dm()
        await dm.send(
            f"ðŸªª **Ausweis-Erstellung fÃ¼r {target.display_name} gestartet!**\n"
            f"Beantworte bitte die folgenden **{len(felder)} Fragen**. "
            f"Du hast jeweils **2 Minuten** pro Antwort."
        )
    except Exception:
        await original_channel.send(
            f"{admin.mention} âŒ Ich kann dir keine DM senden. Bitte aktiviere DMs von Servermitgliedern.",
            delete_after=15
        )
        return

    for key, frage in felder:
        await dm.send(frage)
        try:
            antwort = await bot.wait_for("message", check=dm_check, timeout=120.0)
            wert = antwort.content.strip()

            if key == "einreise_typ":
                if wert.lower() not in ("legal", "illegal"):
                    await dm.send("âŒ UngÃ¼ltige Eingabe. Bitte starte den Command erneut und tippe `legal` oder `illegal`.")
                    return
                wert = wert.lower()

            antworten[key] = wert
        except asyncio.TimeoutError:
            await dm.send("âŒ Zeit abgelaufen! Bitte starte `/ausweis-create` erneut.")
            return

    ausweisnummer = generate_ausweisnummer()
    typ_label     = "ðŸ¤µ Legale Einreise" if antworten["einreise_typ"] == "legal" else "ðŸ¥· Illegale Einreise"

    ausweis_data = load_ausweis()
    ausweis_data[str(target.id)] = {
        "vorname":       antworten["vorname"],
        "nachname":      antworten["nachname"],
        "geburtsdatum":  antworten["geburtsdatum"],
        "alter":         antworten["alter"],
        "nationalitaet": antworten["herkunft"],
        "wohnort":       antworten["wohnort"],
        "einreise_typ":  antworten["einreise_typ"],
        "ausweisnummer": ausweisnummer,
        "erstellt_von":  str(admin),
    }
    save_ausweis(ausweis_data)

    rollen_zu_vergeben = [
        guild.get_role(rid)
        for rid in CHARAKTER_ROLLEN
        if guild.get_role(rid) is not None
    ]
    if rollen_zu_vergeben:
        try:
            await target.add_roles(*rollen_zu_vergeben, reason="Charakter erstellt (Team)")
        except Exception:
            pass

    embed = discord.Embed(
        title="ðŸªª Ausweis erstellt",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Spieler",       value=target.mention,                                        inline=False)
    embed.add_field(name="Name",          value=f"{antworten['vorname']} {antworten['nachname']}",     inline=True)
    embed.add_field(name="Geburtsdatum",  value=antworten["geburtsdatum"],                             inline=True)
    embed.add_field(name="Alter",         value=antworten["alter"],                                    inline=True)
    embed.add_field(name="Herkunft",      value=antworten["herkunft"],                                 inline=True)
    embed.add_field(name="Wohnort",       value=antworten["wohnort"],                                  inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                             inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{ausweisnummer}`",                                  inline=False)
    embed.set_footer(text=f"Erstellt von {admin.display_name}")

    await dm.send("âœ… **Ausweis erfolgreich erstellt!**", embed=embed)


# /ausweis-create (Team only)
@bot.tree.command(name="ausweis-create", description="[TEAM] Erstellt einen Ausweis fuer einen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler fuer den der Ausweis erstellt wird")
@app_commands.default_permissions(manage_messages=True)
async def ausweis_create(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    if str(nutzer.id) in ausweis_data:
        await interaction.response.send_message(
            f"âŒ {nutzer.mention} hat bereits einen Ausweis. Bitte zuerst mit /ausweis-remove lÃ¶schen.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"âœ… Ausweis-Erstellung fÃ¼r **{nutzer.display_name}** gestartet!\n"
        f"Ich schicke dir die Fragen per **DM** â€” nur du siehst sie.",
        ephemeral=True
    )
    asyncio.create_task(ausweis_create_dm_flow(interaction.user, interaction.guild, nutzer, interaction.channel))


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# /delete â€” Nachrichten lÃ¶schen (Team only)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@bot.tree.command(name="delete", description="[TEAM] LÃ¶scht eine bestimmte Anzahl von Nachrichten im Kanal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(anzahl="Anzahl der zu lÃ¶schenden Nachrichten (max. 100)")
@app_commands.default_permissions(manage_messages=True)
async def delete_messages(interaction: discord.Interaction, anzahl: int):
    if not is_team(interaction.user):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    if anzahl < 1 or anzahl > 100:
        await interaction.response.send_message("âŒ Bitte eine Zahl zwischen 1 und 100 angeben.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    geloescht = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(
        f"âœ… **{len(geloescht)}** Nachrichten wurden gelÃ¶scht.",
        ephemeral=True
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# /create-event â€” Event erstellen (Team only)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

EVENT_ANNOUNCEMENT_CHANNEL_ID = 1490882564561567864
EVENT_PING_ROLE_ID             = 1490855737130221598


async def create_event_channel_flow(admin: discord.Member, guild: discord.Guild, channel: discord.TextChannel):
    def check(m):
        return m.author.id == admin.id and m.channel.id == channel.id

    felder = [
        ("was",        "ðŸ“‹ **Was ist das Event?** (z.B. Fahrzeugrennen, Bankraub, Stadtfest):"),
        ("startpunkt", "ðŸ“ **Wo ist der Startpunkt?** (z.B. Pillbox Hill, Legion Square):"),
        ("erklaerung", "ðŸ“ **ErklÃ¤rung / Beschreibung des Events:**"),
        ("dauer",      "â±ï¸ **Dauer des Events?** (z.B. 1 Stunde, 30 Minuten):"),
        ("preis",      "ðŸ’° **Preis / Belohnung?** (z.B. 50.000$, Kein Preis):"),
    ]

    antworten = {}

    for key, frage in felder:
        frage_msg = await channel.send(f"{admin.mention} {frage}")
        antwort = await bot.wait_for("message", check=check, timeout=None)
        antworten[key] = antwort.content.strip()
        try:
            await frage_msg.delete()
            await antwort.delete()
        except Exception:
            pass

    event_channel = guild.get_channel(EVENT_ANNOUNCEMENT_CHANNEL_ID)
    if event_channel is None:
        await channel.send(f"{admin.mention} âŒ Event-Channel nicht gefunden.", delete_after=10)
        return

    ping_role = guild.get_role(EVENT_PING_ROLE_ID)
    role_mention = ping_role.mention if ping_role else ""

    embed = discord.Embed(
        title="ðŸŽ‰ Neues Event!",
        color=0x00B4D8,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="ðŸ“‹ Event",        value=antworten["was"],        inline=False)
    embed.add_field(name="ðŸ“ Startpunkt",   value=antworten["startpunkt"], inline=True)
    embed.add_field(name="â±ï¸ Dauer",        value=antworten["dauer"],      inline=True)
    embed.add_field(name="ðŸ’° Preis",        value=antworten["preis"],      inline=True)
    embed.add_field(name="ðŸ“ Beschreibung", value=antworten["erklaerung"], inline=False)
    embed.set_footer(text=f"Event erstellt von {admin.display_name}")

    await event_channel.send(content=role_mention, embed=embed)
    await channel.send(f"{admin.mention} âœ… **Event wurde erfolgreich gepostet** in {event_channel.mention}!", delete_after=10)


@bot.tree.command(name="create-event", description="[TEAM] Erstellt ein neues Event", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def create_event(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.send_message(
        "ðŸŽ‰ **Event-Erstellung gestartet!** Beantworte die Fragen hier im Channel.",
        ephemeral=True
    )
    asyncio.create_task(create_event_channel_flow(interaction.user, interaction.guild, interaction.channel))


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# /create-giveaway â€” Giveaway erstellen (Team only)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

GIVEAWAY_CHANNEL_ID = 1490882565618536551


def parse_dauer_zu_sekunden(text: str):
    text = text.lower().strip()
    einheiten = {
        "tag": 86400, "tage": 86400,
        "stunde": 3600, "stunden": 3600,
        "minute": 60, "minuten": 60,
        "sekunde": 1, "sekunden": 1,
    }
    gesamt = 0
    gefunden = False
    teile = text.split()
    i = 0
    while i < len(teile):
        try:
            zahl = float(teile[i].replace(",", "."))
            if i + 1 < len(teile):
                einheit = teile[i + 1].rstrip(".")
                if einheit in einheiten:
                    gesamt += int(zahl * einheiten[einheit])
                    gefunden = True
                    i += 2
                    continue
        except ValueError:
            pass
        i += 1
    return gesamt if gefunden else None


async def create_giveaway_channel_flow(admin: discord.Member, guild: discord.Guild, channel: discord.TextChannel):
    def check(m):
        return m.author.id == admin.id and m.channel.id == channel.id

    frage1 = await channel.send(f"{admin.mention} ðŸŽ **Was wird verlost?** (z.B. 500.000$, Fahrzeug, Item):")
    antwort1 = await bot.wait_for("message", check=check, timeout=None)
    gewinn = antwort1.content.strip()
    try:
        await frage1.delete()
        await antwort1.delete()
    except Exception:
        pass

    frage2 = await channel.send(f"{admin.mention} â±ï¸ **Wie lange lÃ¤uft das Giveaway?** (z.B. `2 Tage`, `12 Stunden`, `30 Minuten`):")
    while True:
        antwort2 = await bot.wait_for("message", check=check, timeout=None)
        laufzeit_text = antwort2.content.strip()
        sekunden = parse_dauer_zu_sekunden(laufzeit_text)
        try:
            await antwort2.delete()
        except Exception:
            pass
        if sekunden and sekunden > 0:
            break
        await channel.send(
            f"{admin.mention} âŒ Zeitformat nicht erkannt. Bitte so eingeben: `2 Tage`, `12 Stunden`, `30 Minuten`",
            delete_after=8
        )
    try:
        await frage2.delete()
    except Exception:
        pass

    giveaway_channel = guild.get_channel(GIVEAWAY_CHANNEL_ID)
    if giveaway_channel is None:
        await channel.send(f"{admin.mention} âŒ Giveaway-Channel nicht gefunden.", delete_after=10)
        return

    end_timestamp = int((datetime.now(timezone.utc).timestamp()) + sekunden)

    embed = discord.Embed(
        title="ðŸŽ‰ Giveaway!",
        color=0xF1C40F,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="ðŸŽ Gewinn",   value=gewinn,                              inline=False)
    embed.add_field(name="â±ï¸ Endet",    value=f"<t:{end_timestamp}:R>",            inline=True)
    embed.add_field(name="ðŸ“… Datum",    value=f"<t:{end_timestamp}:F>",            inline=True)
    embed.set_footer(text=f"Giveaway erstellt von {admin.display_name} â€¢ Reagiere mit ðŸŽ‰ um teilzunehmen!")

    msg = await giveaway_channel.send(embed=embed)
    await msg.add_reaction("ðŸŽ‰")
    await channel.send(
        f"{admin.mention} âœ… **Giveaway wurde erfolgreich gepostet** in {giveaway_channel.mention}!\n"
        f"Endet: <t:{end_timestamp}:R>",
        delete_after=10
    )

    await asyncio.sleep(sekunden)

    try:
        msg = await giveaway_channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji="ðŸŽ‰")
        if reaction:
            users = [u async for u in reaction.users() if not u.bot]
            if users:
                winner = random.choice(users)
                win_embed = discord.Embed(
                    title="ðŸŽ‰ Giveaway beendet!",
                    description=(
                        f"**Gewinn:** {gewinn}\n"
                        f"**Gewinner:** {winner.mention} ðŸŽŠ\n\n"
                        f"Herzlichen GlÃ¼ckwunsch!"
                    ),
                    color=0xF1C40F,
                    timestamp=datetime.now(timezone.utc)
                )
                await giveaway_channel.send(content=winner.mention, embed=win_embed)
            else:
                await giveaway_channel.send("âŒ Niemand hat am Giveaway teilgenommen.")
    except Exception as e:
        await log_bot_error("Giveaway-Auswertung fehlgeschlagen", str(e), guild)


@bot.tree.command(name="create-giveaway", description="[TEAM] Erstellt ein neues Giveaway", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def create_giveaway(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("âŒ Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.send_message(
        "ðŸŽ **Giveaway-Erstellung gestartet!** Beantworte die Fragen hier im Channel.",
        ephemeral=True
    )
    asyncio.create_task(create_giveaway_channel_flow(interaction.user, interaction.guild, interaction.channel))


# â”€â”€ Bot starten â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    print("âŒ DISCORD_TOKEN ist nicht gesetzt!")
    exit(1)

bot.run(TOKEN)
