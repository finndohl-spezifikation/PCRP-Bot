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
import aiohttp

# Sicherheitscheck: Bot l\u00E4uft NUR auf Railway, nie doppelt in Replit
if not os.environ.get("RAILWAY_ENVIRONMENT") and not os.environ.get("FORCE_LOCAL_RUN"):
    print("=" * 60)
    print("STOPP: Bot wurde NICHT gestartet.")
    print("Dieser Bot l\u00E4uft ausschlie\u00DFlich auf Railway.")
    print("Bitte NICHT in Replit starten \u2014 nur auf Railway deployen!")
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
LOBBY_ROLE_ID     = 1490855714162475259

LOBBY_CHANNEL_ID  = 1490882583909765190

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
TICKET_RATING_CHANNEL_ID = 1491788506404491336

COUNTING_CHANNEL_ID = 1490882580487340044

# \u2500\u2500 Economy \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
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
    app_commands.Choice(name="1.000 \U0001F4B5",       value=1_000),
    app_commands.Choice(name="5.000 \U0001F4B5",       value=5_000),
    app_commands.Choice(name="10.000 \U0001F4B5",      value=10_000),
    app_commands.Choice(name="25.000 \U0001F4B5",      value=25_000),
    app_commands.Choice(name="50.000 \U0001F4B5",      value=50_000),
    app_commands.Choice(name="100.000 \U0001F4B5",     value=100_000),
    app_commands.Choice(name="250.000 \U0001F4B5",     value=250_000),
    app_commands.Choice(name="500.000 \U0001F4B5",     value=500_000),
    app_commands.Choice(name="1.000.000 \U0001F4B5",   value=1_000_000),
]

LIMIT_CHOICES = [
    app_commands.Choice(name="1.000.000 \U0001F4B5",   value=1_000_000),
    app_commands.Choice(name="2.000.000 \U0001F4B5",   value=2_000_000),
    app_commands.Choice(name="3.000.000 \U0001F4B5",   value=3_000_000),
    app_commands.Choice(name="4.000.000 \U0001F4B5",   value=4_000_000),
    app_commands.Choice(name="5.000.000 \U0001F4B5",   value=5_000_000),
    app_commands.Choice(name="6.000.000 \U0001F4B5",   value=6_000_000),
    app_commands.Choice(name="7.000.000 \U0001F4B5",   value=7_000_000),
    app_commands.Choice(name="8.000.000 \U0001F4B5",   value=8_000_000),
    app_commands.Choice(name="9.000.000 \U0001F4B5",   value=9_000_000),
    app_commands.Choice(name="10.000.000 \U0001F4B5",  value=10_000_000),
]

# Persistenter Datenspeicher
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

ECONOMY_FILE      = DATA_DIR / "economy_data.json"
SHOP_FILE         = DATA_DIR / "shop_data.json"
WARNS_FILE        = DATA_DIR / "warns_data.json"
TEAM_WARNS_FILE   = DATA_DIR / "team_warns_data.json"
HIDDEN_ITEMS_FILE = DATA_DIR / "hidden_items.json"
AUSWEIS_FILE      = DATA_DIR / "ausweis_data.json"
HANDY_FILE        = DATA_DIR / "handy_numbers.json"

# Neue Kanal- und Rollen-IDs
WARN_LOG_CHANNEL_ID      = 1491113577258684466
TEAM_WARN_LOG_CHANNEL_ID = 1490878144146833450
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

# \u2500\u2500 Handy System \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
HANDY_CHANNEL_ID      = 1490890317199708160
HANDY_ITEM_NAME       = "\U0001F4F1| Handy"  # exakter Name im Shop

DISPATCH_MD_ROLE_ID   = 1490855752712327210
DISPATCH_PD_ROLE_ID   = 1490855751797969039
DISPATCH_ADAC_ROLE_ID = 1490855754213753024
INSTAGRAM_ROLE_ID     = 1490855786698641428
PARSHIP_ROLE_ID       = 1490855783989121024

# IC-Chat Kanal-ID \u2014 bitte mit der korrekten ID des IC-Chat-Kanals ersetzen!
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
    "mistkerl", "penner", "hurenkind", "dummficker", "schei\u00DF",
]

spam_tracker     = {}
spam_warned      = set()
ticket_data      = {}
counting_state   = {"count": 0, "last_user_id": None}
counting_handled = set()

FEATURES = {
    "Discord Link Schutz":         True,
    "Link Filter (Memes)":         True,
    "Vulg\u00E4re W\u00F6rter Filter":       True,
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
    "Z\u00E4hl-Kanal":                  True,
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
                title=f"\u26A0\uFE0F Bot Fehler \u2014 {title}",
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
            emoji = "\U0001F7E2" if status else "\U0001F534"
            state = "Online" if status else "Offline"
            desc += f"{emoji} **{feature}** \u2014 {state}\n"
        embed = discord.Embed(
            title="\U0001F916 Bot Status \u2014 Alle Funktionen",
            description=desc,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await log_ch.send(embed=embed)
        except Exception:
            pass


async def apply_timeout_restrictions(member, guild, duration_h=None, duration_m=None, reason="Regelversto\u00DF"):
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
            f"M\u00F6gliche Ursachen:\n"
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


# \u2500\u2500 Economy Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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


# \u2500\u2500 Warn Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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


def load_team_warns():
    if TEAM_WARNS_FILE.exists():
        with open(TEAM_WARNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_team_warns(data):
    with open(TEAM_WARNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user_team_warns(warns, user_id):
    return warns.setdefault(str(user_id), [])


# \u2500\u2500 Hidden Items Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def load_hidden_items():
    if HIDDEN_ITEMS_FILE.exists():
        with open(HIDDEN_ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_hidden_items(data):
    with open(HIDDEN_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# \u2500\u2500 Handy Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
    """Pr\u00FCft ob der Member das Handy-Item im Inventar hat."""
    eco = load_economy()
    user_data = get_user(eco, member.id)
    inventory = user_data.get("inventory", [])
    norm_handy = normalize_item_name(HANDY_ITEM_NAME)  # z.B. "handy"
    # Permissiver Check: normalisierter Itemname muss "handy" enthalten
    return any(norm_handy in normalize_item_name(i) for i in inventory)


# \u2500\u2500 Money Log Helper \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def log_money_action(guild: discord.Guild, title: str, description: str):
    ch = guild.get_channel(MONEY_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title=f"\U0001F4B5 {title}",
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await ch.send(embed=embed)
        except Exception:
            pass


# \u2500\u2500 Betrag Autocomplete \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
        label = f"{val:,} \U0001F4B5".replace(",", ".")
        if clean == "" or clean in str(val) or clean.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=val))
    return choices[:25]


# \u2500\u2500 Shop-Item Autocomplete \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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


# \u2500\u2500 Inventar-Item Autocomplete \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
        label = f"{item_name} (\u00D7{count})"
        if current_lower == "" or current_lower in item_name.lower():
            choices.append(app_commands.Choice(name=label, value=item_name))
    return choices[:25]


# \u2500\u2500 Normalisierungsfunktion f\u00FCr Item-Namen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def normalize_item_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[\|\-\_]+', ' ', name)
    name = ''.join(c for c in name if c.isalnum() or c.isspace())
    return re.sub(r'\s+', ' ', name).strip()


# \u2500\u2500 Versteck-Button (persistent) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class VersteckRetrieveView(discord.ui.View):
    def __init__(self, item_id: str, owner_id: int):
        super().__init__(timeout=None)
        self.item_id  = item_id
        self.owner_id = owner_id
        btn = discord.ui.Button(
            label="\U0001F4E6 Aus Versteck holen",
            style=discord.ButtonStyle.green,
            custom_id=f"retrieve_{item_id}_{owner_id}"
        )
        btn.callback = self.retrieve_callback
        self.add_item(btn)

    async def retrieve_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "\u274C Nur derjenige der das Item versteckt hat kann es herausnehmen.",
                ephemeral=True
            )
            return
        hidden = load_hidden_items()
        entry  = next((h for h in hidden if h["id"] == self.item_id), None)
        if not entry:
            await interaction.response.send_message("\u274C Item wurde bereits geborgen oder existiert nicht mehr.", ephemeral=True)
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
            f"\u2705 **{entry['item']}** wurde aus dem Versteck (**{entry['location']}**) geholt.",
            ephemeral=True
        )


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# HANDY SYSTEM
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

class HandyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # \u2500\u2500 Dispatch MD \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    @discord.ui.button(
        label="\U0001F6A8 | Dispatch MD",
        style=discord.ButtonStyle.red,
        custom_id="handy_dispatch_md",
        row=0
    )
    async def dispatch_md(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_dispatch(interaction, DISPATCH_MD_ROLE_ID, "MD")

    # \u2500\u2500 Dispatch PD \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    @discord.ui.button(
        label="\U0001F6A8 | Dispatch PD",
        style=discord.ButtonStyle.red,
        custom_id="handy_dispatch_pd",
        row=0
    )
    async def dispatch_pd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_dispatch(interaction, DISPATCH_PD_ROLE_ID, "PD")

    # \u2500\u2500 Dispatch ADAC \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    @discord.ui.button(
        label="\U0001F6A8 | Dispatch ADAC",
        style=discord.ButtonStyle.red,
        custom_id="handy_dispatch_adac",
        row=0
    )
    async def dispatch_adac(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_dispatch(interaction, DISPATCH_ADAC_ROLE_ID, "ADAC")

    # \u2500\u2500 Handy Nummer Einsehen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    @discord.ui.button(
        label="\U0001F4F1 | Handy Nummer Einsehen",
        style=discord.ButtonStyle.blurple,
        custom_id="handy_nummer",
        row=1
    )
    async def handy_nummer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "\u274C Du besitzt kein Handy. Kaufe es im Shop!",
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
            title="\U0001F4F1 Deine Handynummer",
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

    # \u2500\u2500 Instagram \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    @discord.ui.button(
        label="\U0001F4F1 | Instagram",
        style=discord.ButtonStyle.blurple,
        custom_id="handy_instagram",
        row=1
    )
    async def instagram(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "\u274C Du besitzt kein Handy. Kaufe es im Shop!",
                ephemeral=True
            )
            return

        guild = interaction.guild
        role  = guild.get_role(INSTAGRAM_ROLE_ID)
        if not role:
            await interaction.response.send_message("\u274C Instagram-Rolle nicht gefunden.", ephemeral=True)
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role, reason="Handy: Instagram deinstalliert")
            embed = discord.Embed(
                description="\U0001F4F1 **App Erfolgreich Deinstalliert**\nInstagram wurde von deinem Handy entfernt.",
                color=MOD_COLOR
            )
        else:
            await member.add_roles(role, reason="Handy: Instagram installiert")
            embed = discord.Embed(
                description="\U0001F4F1 **App Erfolgreich Installiert**\nInstagram wurde auf deinem Handy installiert.",
                color=LOG_COLOR
            )
        embed.set_footer(text="Nur du siehst diese Nachricht")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # \u2500\u2500 Parship \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    @discord.ui.button(
        label="\U0001F4F1 | Parship",
        style=discord.ButtonStyle.blurple,
        custom_id="handy_parship",
        row=1
    )
    async def parship(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "\u274C Du besitzt kein Handy. Kaufe es im Shop!",
                ephemeral=True
            )
            return

        guild = interaction.guild
        role  = guild.get_role(PARSHIP_ROLE_ID)
        if not role:
            await interaction.response.send_message("\u274C Parship-Rolle nicht gefunden.", ephemeral=True)
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role, reason="Handy: Parship deinstalliert")
            embed = discord.Embed(
                description="\U0001F4F1 **App Erfolgreich Deinstalliert**\nParship wurde von deinem Handy entfernt.",
                color=MOD_COLOR
            )
        else:
            await member.add_roles(role, reason="Handy: Parship installiert")
            embed = discord.Embed(
                description="\U0001F4F1 **App Erfolgreich Installiert**\nParship wurde auf deinem Handy installiert.",
                color=LOG_COLOR
            )
        embed.set_footer(text="Nur du siehst diese Nachricht")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def handle_dispatch(interaction: discord.Interaction, role_id: int, dispatch_type: str):
    """Sendet einen Dispatch-Notruf als DM an alle Mitglieder mit der jeweiligen Rolle."""
    if not has_handy(interaction.user):
        await interaction.response.send_message(
            "\u274C Du besitzt kein Handy. Kaufe es im Shop!",
            ephemeral=True
        )
        return

    guild  = interaction.guild
    member = interaction.user
    role   = guild.get_role(role_id)

    if not role:
        await interaction.response.send_message(
            f"\u274C Dispatch-Rolle nicht gefunden.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    dispatch_embed = discord.Embed(
        title="\U0001F6A8 Dispatch \U0001F6A8",
        description=(
            f"**Ein Bewohner hat einen Dispatch abgesendet!**\n\n"
            f"\U0001F5FA\uFE0F **Standort:** {member.mention}\n"
            f"\U0001F4CB **Dispatch-Typ:** {dispatch_type}\n"
            f"\u23F0 **Zeit:** <t:{int(datetime.now(timezone.utc).timestamp())}:T>"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    dispatch_embed.set_footer(text=f"Kryptik Roleplay \u2014 Dispatch System")

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
        title="\u2705 Dispatch gesendet!",
        description=(
            f"Dein **{dispatch_type}-Dispatch** wurde erfolgreich abgesendet.\n"
            f"**Benachrichtigt:** {sent} Einheiten"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.followup.send(embed=confirm_embed, ephemeral=True)


async def auto_handy_setup():
    """Postet das Handy-Embed nur wenn noch keins im Kanal ist."""
    for guild in bot.guilds:
        channel = guild.get_channel(HANDY_CHANNEL_ID)
        if not channel:
            continue
        embed_exists = False
        try:
            async for msg in channel.history(limit=30):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Handy" in emb.title:
                            embed_exists = True
                            break
                if embed_exists:
                    break
        except Exception:
            pass
        if embed_exists:
            print(f"Handy-Embed bereits vorhanden in #{channel.name}, \u00FCberspringe.")
            continue
        embed = discord.Embed(
            title="\U0001F4F1 Handy \u2014 Einstellungen",
            description=(
                "Willkommen in deinen Handy-Einstellungen!\n\n"
                "Hier kannst du deinen Notruf absetzen, deine Handynummer einsehen "
                "und Social-Media-Apps installieren oder deinstallieren.\n\n"
                "**\U0001F6A8 Dispatch-Buttons** \u2014 Sende einen Notruf an die zust\u00E4ndige Einheit\n"
                "**\U0001F4F1 Handy Nummer** \u2014 Zeigt deine pers\u00F6nliche LA-Nummer\n"
                "**\U0001F4F1 Instagram / Parship** \u2014 Apps installieren & deinstallieren\n\n"
                "\u26A0\uFE0F *Du ben\u00F6tigst das Item* `\U0001F4F1| Handy` *aus dem Shop, um diese Funktionen zu nutzen.*"
            ),
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Kryptik Roleplay \u2014 Handy System")
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


# \u2500\u2500 Ticket System \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
    welcome_embed.set_footer(text="Nur Teammitglieder k\u00F6nnen das Ticket schlie\u00DFen")

    action_view = TicketActionView()
    await channel.send(content=team_mentions, embed=welcome_embed, view=action_view)

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
        await log_ch.send(embed=log_embed)


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support",            emoji="\U0001F39F", value="support",    description="Allgemeiner Support"),
            discord.SelectOption(label="Highteam Ticket",    emoji="\U0001F39F", value="highteam",   description="Direkter Kontakt zum Highteam"),
            discord.SelectOption(label="Fraktions Bewerbung",emoji="\U0001F39F", value="fraktion",   description="Bewerbung f\u00FCr eine Fraktion"),
            discord.SelectOption(label="Beschwerde Ticket",  emoji="\U0001F39F", value="beschwerde", description="Beschwerde einreichen"),
            discord.SelectOption(label="Bug Report",          emoji="\U0001F39F", value="bug",        description="Fehler oder Bug melden"),
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
        await channel.send(embed=assign_embed)
        await interaction.response.send_message(
            f"\u2705 {user.mention} wurde dem Ticket zugewiesen.", ephemeral=True
        )


class AssignView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
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
            await log_ch.send(embed=closed_embed, file=transcript_file)

        creator = interaction.guild.get_member(data["creator_id"])
        if creator:
            try:
                dm_embed = discord.Embed(
                    title="\U0001F39F Dein Ticket wurde geschlossen",
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



# \u2500\u2500 Events \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
            print(f"Ticket-Embed bereits vorhanden in #{channel.name} \u2014 kein erneutes Posten.")
            continue
        embed = discord.Embed(
            title="\U0001F39F Support \u2014 Ticket erstellen",
            description=(
                "Ben\u00F6tigst du Hilfe oder m\u00F6chtest ein Anliegen melden?\n\n"
                "W\u00E4hle unten im Men\u00FC die passende Ticket-Art aus.\n"
                "Unser Team wird sich schnellstm\u00F6glich um dich k\u00FCmmern.\n\n"
                "**Verf\u00FCgbare Ticket-Arten:**\n"
                "\U0001F39F **Support** \u2014 Allgemeiner Support\n"
                "\U0001F39F **Highteam Ticket** \u2014 Direkter Kontakt zum Highteam\n"
                "\U0001F39F **Fraktions Bewerbung** \u2014 Bewirb dich f\u00FCr eine Fraktion\n"
                "\U0001F39F **Beschwerde Ticket** \u2014 Beschwerde einreichen\n"
                "\U0001F39F **Bug Report** \u2014 Fehler oder Bug melden"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Cryptik Roleplay \u2014 Support System")
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
        await message.add_reaction("\u2705")
    else:
        counting_state["count"] = 0
        counting_state["last_user_id"] = None
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


async def handle_discord_invite(message):
    member = message.author
    guild  = message.guild
    try:
        await message.delete()
    except Exception as e:
        await log_bot_error("Nachricht l\u00F6schen (Discord Link)", str(e), guild)
    timeout_ok, roles_removed = await apply_timeout_restrictions(
        member, guild, duration_h=300, reason="Fremden Discord-Link gesendet"
    )
    try:
        embed = discord.Embed(
            description=(
                "> Du hast gegen unsere Server Regeln versto\u00DFen\n\n"
                "> Bitte wende dich an den Support"
            ),
            color=MOD_COLOR
        )
        await member.send(content=member.mention, embed=embed)
    except Exception:
        pass
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        timeout_status = "\u2705 Timeout erteilt (300h)" if timeout_ok else "\u274C Timeout fehlgeschlagen \u2014 Berechtigung pr\u00FCfen!"
        rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
        embed = discord.Embed(
            title="\U0001F528 Moderation \u2014 Timeout",
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
            f"{message.author.mention} Bitte sende Links ausschlie\u00DFlich im <#{MEMES_CHANNEL_ID}> Kanal",
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
                "> **Verwarnung:** Du hast einen vulg\u00E4ren Ausdruck verwendet.\n\n"
                "> Bitte beachte unsere Serverregeln. Bei weiteren Verst\u00F6\u00DFen folgen Konsequenzen."
            ),
            color=MOD_COLOR
        )
        await message.author.send(content=message.author.mention, embed=embed)
    except Exception:
        pass
    log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="\U0001F528 Moderation \u2014 Vulg\u00E4re Sprache",
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
                description="> Du wurdest aufgrund von wiederholtem Spammen f\u00FCr **10 Minuten** stummgeschaltet.",
                color=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        except Exception:
            pass
        log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            timeout_status = "\u2705 Timeout erteilt (10min)" if timeout_ok else "\u274C Timeout fehlgeschlagen \u2014 Berechtigung pr\u00FCfen!"
            rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
            embed = discord.Embed(
                title="\U0001F528 Moderation \u2014 Timeout (Spam)",
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
                    "> Bei Wiederholung erh\u00E4ltst du einen 10 Minuten Timeout."
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
        title="\U0001F5D1\uFE0F Nachricht gel\u00F6scht",
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
        title="\u270F\uFE0F Nachricht bearbeitet",
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
    title = "\U0001F462 Mitglied gekickt" if action == "gekickt" else "\U0001F6AA Mitglied hat den Server verlassen"
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
                title="\U0001F4E4 Mitglied hat den Server verlassen",
                description=(
                    f"**{member.mention}** hat uns verlassen.\n\n"
                    f"Wir w\u00FCnschen dir alles Gute!\n"
                    f"Du bist jederzeit herzlich willkommen zur\u00FCckzukehren."
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
                        description="> Bots auf diesen Server hinzuf\u00FCgen ist f\u00FCr dich leider nicht erlaubt.",
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
            title="\u2705 Mitglied beigetreten",
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
            description += f"**Einladungen von {inviter.display_name}:** {inviter_uses} \U0001F39F"
        elif inviter_uses > 0:
            description += "**Eingeladen von:** Vanity-URL (Server-Link)"
        else:
            description += "**Eingeladen von:** Unbekannt *(Bot fehlt 'Server verwalten' Berechtigung?)*"
        embed = discord.Embed(
            title="\U0001F4E5 Neues Mitglied",
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
                "> Willkommen auf Kryptik Roleplay deinem RP server mit Ultimativem Spa\u00DF und Hochwertigem RP\n\n"
                "> Wir w\u00FCnschen dir viel Spa\u00DF auf unserem Server und hoffen das du dich bei uns Gut Zurecht findest\n\n"
                "> Solltest du mal Schwierigkeiten haben melde dich gerne Jederzeit \u00FCber ein Support Ticket im channel "
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
                title="\U0001F4E5 Willkommen auf dem Server!",
                description=(
                    f"Herzlich Willkommen {member.mention} auf **Kryptik Roleplay**!\n\n"
                    f"Wir freuen uns dich hier zu haben.\n"
                    f"Bitte w\u00E4hle deine Einreiseart und erstelle deinen Ausweis."
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
            f"**Spieler:** {member.mention}\n**Bargeld:** {START_CASH:,} \U0001F4B5 (Willkommensbonus)"
        )


# \u2500\u2500 Commands \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! \U0001F44B")


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
        await ctx.send("\u274C Ticket-Kanal nicht gefunden!")
        return
    embed = discord.Embed(
        title="\U0001F39F Support \u2014 Ticket erstellen",
        description=(
            "Ben\u00F6tigst du Hilfe oder m\u00F6chtest ein Anliegen melden?\n\n"
            "W\u00E4hle unten im Men\u00FC die passende Ticket-Art aus.\n"
            "Unser Team wird sich schnellstm\u00F6glich um dich k\u00FCmmern.\n\n"
            "**Verf\u00FCgbare Ticket-Arten:**\n"
            "\U0001F39F **Support** \u2014 Allgemeiner Support\n"
            "\U0001F39F **Highteam Ticket** \u2014 Direkter Kontakt zum Highteam\n"
            "\U0001F39F **Fraktions Bewerbung** \u2014 Bewirb dich f\u00FCr eine Fraktion\n"
            "\U0001F39F **Beschwerde Ticket** \u2014 Beschwerde einreichen\n"
            "\U0001F39F **Bug Report** \u2014 Fehler oder Bug melden"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Cryptik Roleplay \u2014 Support System")
    view = TicketSelectView()
    await channel.send(embed=embed, view=view)
    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="handysetup")
async def handysetup(ctx):
    """Postet das Handy-Embed erneut im Handy-Kanal. Nur für Admins."""
    if not is_admin(ctx.author):
        return
    channel = ctx.guild.get_channel(HANDY_CHANNEL_ID)
    if not channel:
        await ctx.send("\u274C Handy-Kanal nicht gefunden!")
        return
    # Altes Embed löschen
    try:
        async for msg in channel.history(limit=20):
            if msg.author.id == ctx.bot.user.id and msg.embeds:
                for emb in msg.embeds:
                    if emb.title and "Handy" in emb.title:
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                        break
    except Exception:
        pass
    embed = discord.Embed(
        title="\U0001F4F1 Handy \u2014 Einstellungen",
        description=(
            "Willkommen in deinen Handy-Einstellungen!\n\n"
            "Hier kannst du deinen Notruf absetzen, deine Handynummer einsehen "
            "und Social-Media-Apps installieren oder deinstallieren.\n\n"
            "**\U0001F6A8 Dispatch-Buttons** \u2014 Sende einen Notruf an die zust\u00E4ndige Einheit\n"
            "**\U0001F4F1 Handy Nummer** \u2014 Zeigt deine pers\u00F6nliche LA-Nummer\n"
            "**\U0001F4F1 Instagram / Parship** \u2014 Apps installieren & deinstallieren\n\n"
            "\u26A0\uFE0F *Du ben\u00F6tigst das Item* `\U0001F4F1| Handy` *aus dem Shop, um diese Funktionen zu nutzen.*"
        ),
        color=0x00BFFF,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Kryptik Roleplay \u2014 Handy System")
    await channel.send(embed=embed, view=HandyView())
    try:
        await ctx.message.delete()
    except Exception:
        pass


# \u2500\u2500 Economy Slash Commands \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def channel_error(channel_id: int) -> str:
    return f"\u274C Du kannst diesen Command nur hier ausf\u00FChren: <#{channel_id}>"


# /lohn-abholen
@bot.tree.command(name="lohn-abholen", description="Hole deinen st\u00FCndlichen Lohn ab", guild=discord.Object(id=GUILD_ID))
async def lohn_abholen(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != LOHN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(LOHN_CHANNEL_ID), ephemeral=True)
        return

    main_wages = [WAGE_ROLES[r] for r in role_ids if r in WAGE_ROLES]
    if len(main_wages) > 1:
        await interaction.response.send_message(
            "\u274C Du hast mehrere Lohnklassen. Bitte wende dich ans Team.", ephemeral=True
        )
        return
    if not main_wages:
        await interaction.response.send_message(
            "\u274C Du hast keine Lohnklasse und kannst keinen Lohn abholen.", ephemeral=True
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
                f"\u274C Du kannst deinen Lohn erst in **{mins}m {secs}s** wieder abholen.",
                ephemeral=True
            )
            return

    user_data["bank"]      += total_wage
    user_data["last_wage"]  = now.isoformat()
    save_economy(eco)

    embed = discord.Embed(
        title="\U0001F4B5 Lohn abgeholt!",
        description=(
            f"Du hast **{total_wage:,} \U0001F4B5** auf dein Konto erhalten.\n"
            f"**Kontostand:** {user_data['bank']:,} \U0001F4B5"
        ),
        color=LOG_COLOR,
        timestamp=now
    )
    await interaction.response.send_message(embed=embed)


# /kontostand
@bot.tree.command(name="kontostand", description="Zeigt den Kontostand an (Team: auch per @Erw\u00E4hnung)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Mitglied dessen Kontostand abgerufen werden soll")
async def kontostand(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids  = [r.id for r in interaction.user.roles]
    is_team_m = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids

    if nutzer is not None:
        if not is_team_m:
            await interaction.response.send_message(
                "\u274C Du hast keine Berechtigung, den Kontostand anderer Mitglieder abzurufen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    else:
        if not is_team_m and interaction.channel.id != BANK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
            return
        if not is_team_m and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
            return
        ziel = interaction.user

    eco       = load_economy()
    user_data = get_user(eco, ziel.id)
    save_economy(eco)

    titel = "\U0001F4B3 Kontostand" if ziel.id == interaction.user.id else f"\U0001F4B3 Kontostand \u2014 {ziel.display_name}"
    embed = discord.Embed(
        title=titel,
        description=(
            f"**Bargeld:** {user_data['cash']:,} \U0001F4B5\n"
            f"**Bank:** {user_data['bank']:,} \U0001F4B5\n"
            f"**Gesamt:** {user_data['cash'] + user_data['bank']:,} \U0001F4B5"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /einzahlen
@bot.tree.command(name="einzahlen", description="Zahle Bargeld auf dein Bankkonto ein", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag w\u00E4hlen oder eingeben (1.000 \u2013 10.000.000 \U0001F4B5)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def einzahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("\u274C Betrag muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["cash"] < betrag:
        await interaction.response.send_message(
            f"\u274C Nicht genug Bargeld. Dein Bargeld: **{user_data['cash']:,} \U0001F4B5**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - user_data["daily_deposit"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"\u274C Tageslimit erreicht. Du kannst heute noch **{remaining:,} \U0001F4B5** einzahlen. "
                f"(Limit: **{user_limit:,} \U0001F4B5**)",
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
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} \U0001F4B5\n"
        f"**Bargeld danach:** {user_data['cash']:,} \U0001F4B5 | **Bank danach:** {user_data['bank']:,} \U0001F4B5"
    )

    embed = discord.Embed(
        title="\U0001F3E6 Eingezahlt",
        description=(
            f"**Eingezahlt:** {betrag:,} \U0001F4B5\n"
            f"**Bargeld:** {user_data['cash']:,} \U0001F4B5\n"
            f"**Bank:** {user_data['bank']:,} \U0001F4B5"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /auszahlen
@bot.tree.command(name="auszahlen", description="Hebe Geld von deinem Bankkonto ab", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag w\u00E4hlen oder eingeben (1.000 \u2013 10.000.000 \U0001F4B5)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def auszahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("\u274C Betrag muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["bank"] < betrag:
        await interaction.response.send_message(
            f"\u274C Nicht genug Guthaben. Dein Kontostand: **{user_data['bank']:,} \U0001F4B5**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - user_data["daily_withdraw"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"\u274C Tageslimit erreicht. Du kannst heute noch **{remaining:,} \U0001F4B5** auszahlen. "
                f"(Limit: **{user_limit:,} \U0001F4B5**)",
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
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} \U0001F4B5\n"
        f"**Bargeld danach:** {user_data['cash']:,} \U0001F4B5 | **Bank danach:** {user_data['bank']:,} \U0001F4B5"
    )

    embed = discord.Embed(
        title="\U0001F4B8 Ausgezahlt",
        description=(
            f"**Ausgezahlt:** {betrag:,} \U0001F4B5\n"
            f"**Bargeld:** {user_data['cash']:,} \U0001F4B5\n"
            f"**Bank:** {user_data['bank']:,} \U0001F4B5"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /ueberweisen
@bot.tree.command(name="ueberweisen", description="\u00DCberweise Geld an einen anderen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Empf\u00E4nger", betrag="Betrag w\u00E4hlen oder eingeben (1.000 \u2013 10.000.000 \U0001F4B5)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def ueberweisen(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("\u274C Du kannst nicht an dich selbst \u00FCberweisen.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("\u274C Betrag muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
        return

    eco        = load_economy()
    sender     = get_user(eco, interaction.user.id)
    receiver   = get_user(eco, nutzer.id)
    reset_daily_if_needed(sender)

    if sender["bank"] < betrag:
        await interaction.response.send_message(
            f"\u274C Nicht genug Guthaben. Dein Kontostand: **{sender['bank']:,} \U0001F4B5**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = sender.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - sender["daily_transfer"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"\u274C Tageslimit erreicht. Du kannst heute noch **{remaining:,} \U0001F4B5** \u00FCberweisen. "
                f"(Limit: **{user_limit:,} \U0001F4B5**)",
                ephemeral=True
            )
            return
        sender["daily_transfer"] += betrag

    sender["bank"]   -= betrag
    receiver["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "\u00DCberweisung",
        f"**Von:** {interaction.user.mention} \u2192 **An:** {nutzer.mention}\n"
        f"**Betrag:** {betrag:,} \U0001F4B5 | **Sender-Bank danach:** {sender['bank']:,} \U0001F4B5"
    )

    embed = discord.Embed(
        title="\U0001F4B3 \u00DCberweisung",
        description=(
            f"**An:** {nutzer.mention}\n"
            f"**Betrag:** {betrag:,} \U0001F4B5\n"
            f"**Dein Kontostand:** {sender['bank']:,} \U0001F4B5"
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
                title="\U0001F6D2 Shop",
                description="Der Shop ist aktuell leer.",
                color=LOG_COLOR
            ),
            ephemeral=True
        )
        return

    lines = []
    for item in items:
        line = f"**{item['name']}** \u2014 {item['price']:,} \U0001F4B5"
        ar = item.get("allowed_role")
        if ar:
            r = interaction.guild.get_role(ar)
            line += f"  \U0001F512 *{r.name if r else ar}*"
        lines.append(line)

    embed = discord.Embed(
        title="\U0001F6D2 Shop",
        description="\n".join(lines),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Kaufen mit /buy [itemname] \u2022 Nur mit Bargeld m\u00F6glich")
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
@app_commands.describe(itemname="Name des Items das du kaufen m\u00F6chtest")
async def buy(interaction: discord.Interaction, itemname: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
        return

    items = load_shop()
    item  = find_shop_item(items, itemname)

    if not item:
        await interaction.response.send_message(
            f"\u274C Item **{itemname}** wurde nicht gefunden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    allowed_role = item.get("allowed_role")
    if allowed_role and not is_adm:
        if allowed_role not in role_ids:
            rolle_obj = interaction.guild.get_role(allowed_role)
            rname     = rolle_obj.name if rolle_obj else f"<@&{allowed_role}>"
            await interaction.response.send_message(
                f"\u274C Dieses Item ist nur f\u00FCr die Rolle **{rname}** erh\u00E4ltlich.",
                ephemeral=True
            )
            return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)

    if user_data["cash"] < item["price"]:
        await interaction.response.send_message(
            f"\u274C Du hast nicht genug **Bargeld**.\n"
            f"Preis: **{item['price']:,} \U0001F4B5** | Dein Bargeld: **{user_data['cash']:,} \U0001F4B5**\n"
            f"\u2139\uFE0F K\u00E4ufe sind nur mit Bargeld m\u00F6glich. Hebe Geld mit `/auszahlen` ab.",
            ephemeral=True
        )
        return

    user_data["cash"] -= item["price"]
    if "inventory" not in user_data:
        user_data["inventory"] = []
    user_data["inventory"].append(item["name"])
    save_economy(eco)

    # \u2500\u2500 Handy-Kauf: Kanal-Berechtigung geben \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    if normalize_item_name(item["name"]) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, interaction.user)

    embed = discord.Embed(
        title="\u2705 Gekauft!",
        description=(
            f"Du hast **{item['name']}** f\u00FCr **{item['price']:,} \U0001F4B5** gekauft.\n"
            f"**Verbleibendes Bargeld:** {user_data['cash']:,} \U0001F4B5"
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
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["custom_limit"] = limit
    save_economy(eco)

    embed = discord.Embed(
        title="\u2699\uFE0F Limit gesetzt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Neues Tageslimit:** {limit:,} \U0001F4B5\n"
            f"*(gilt f\u00FCr Einzahlen, Auszahlen & \u00DCberweisen)*"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesetzt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


# /money-add (Admin only)
@bot.tree.command(name="money-add", description="[ADMIN] F\u00FCge einem Spieler Geld hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
@app_commands.default_permissions(administrator=True)
async def money_add(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("\u274C Betrag muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld hinzugef\u00FCgt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** +{betrag:,} \U0001F4B5\n"
        f"**Bargeld danach:** {user_data['cash']:,} \U0001F4B5\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="\U0001F4B0 Geld hinzugef\u00FCgt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Hinzugef\u00FCgt:** {betrag:,} \U0001F4B5\n"
            f"**Bargeld:** {user_data['cash']:,} \U0001F4B5"
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
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("\u274C Betrag muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] = max(0, user_data["cash"] - betrag)
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld entfernt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** -{betrag:,} \U0001F4B5\n"
        f"**Bargeld danach:** {user_data['cash']:,} \U0001F4B5\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="\U0001F4B8 Geld entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernt:** {betrag:,} \U0001F4B5\n"
            f"**Bargeld:** {user_data['cash']:,} \U0001F4B5"
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
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    shop_items = load_shop()
    shop_item  = find_shop_item(shop_items, itemname)
    if not shop_item:
        await interaction.response.send_message(
            f"\u274C Das Item **{itemname}** existiert nicht im Shop.\n"
            f"Es k\u00F6nnen nur vorhandene Shop-Items vergeben werden. Nutze `/shop` um alle Items zu sehen.",
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
            title="\U0001F4E6 Item hinzugef\u00FCgt",
            description=f"**{shop_item['name']}** wurde **{nutzer.mention}** hinzugef\u00FCgt.",
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
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inventory = user_data.get("inventory", [])

    match = find_inventory_item(inventory, itemname)
    if not match:
        await interaction.response.send_message(
            f"\u274C **{nutzer.display_name}** besitzt kein Item namens **{itemname}**.", ephemeral=True
        )
        return

    inventory.remove(match)
    user_data["inventory"] = inventory
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="\U0001F4E6 Item entfernt",
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

    @discord.ui.button(label="\u2705 Best\u00E4tigen", style=discord.ButtonStyle.green)
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
            rolle_info = f"\n**Nur f\u00FCr:** {r.mention if r else self.allowed_role_id}"
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="\u2705 Item hinzugef\u00FCgt",
                description=f"**{self.name}** f\u00FCr **{self.price:,} \U0001F4B5** wurde zum Shop hinzugef\u00FCgt.{rolle_info}",
                color=LOG_COLOR
            ),
            view=self
        )

    @discord.ui.button(label="\u274C Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="\u274C Abgebrochen",
                description="Das Item wurde nicht hinzugef\u00FCgt.",
                color=MOD_COLOR
            ),
            view=self
        )


@bot.tree.command(name="shop-add", description="[TEAM] F\u00FCge ein neues Item zum Shop hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    itemname="Name des Items",
    preis="Preis in $",
    rolle="(Optional) Nur diese Rolle kann das Item kaufen"
)
@app_commands.default_permissions(manage_messages=True)
async def shop_add(interaction: discord.Interaction, itemname: str, preis: int, rolle: discord.Role = None):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    if preis <= 0:
        await interaction.response.send_message("\u274C Preis muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
        return

    rolle_info = f"\n**Nur f\u00FCr:** {rolle.mention}" if rolle else "\n**Rollenbeschr\u00E4nkung:** Keine"
    embed = discord.Embed(
        title="\U0001F6D2 Neues Item hinzuf\u00FCgen?",
        description=(
            f"**Name:** {itemname}\n"
            f"**Preis:** {preis:,} \U0001F4B5"
            f"{rolle_info}\n\n"
            f"Bitte best\u00E4tige das Hinzuf\u00FCgen."
        ),
        color=LOG_COLOR
    )
    await interaction.response.send_message(
        embed=embed,
        view=ShopAddConfirmView(itemname, preis, rolle.id if rolle else None),
        ephemeral=True
    )


# /delete-item (Team only) \u2014 Item aus dem Shop entfernen
@bot.tree.command(name="delete-item", description="[TEAM] Entfernt ein Item aus dem Shop", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(itemname="Name des Items das aus dem Shop entfernt werden soll")
@app_commands.autocomplete(itemname=shop_item_autocomplete)
async def delete_item(interaction: discord.Interaction, itemname: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    items = load_shop()
    shop_item = find_shop_item(items, itemname)

    if not shop_item:
        await interaction.response.send_message(
            f"\u274C Das Item **{itemname}** wurde im Shop nicht gefunden.\n"
            f"Nutze `/shop` um alle verf\u00FCgbaren Items zu sehen.",
            ephemeral=True
        )
        return

    items.remove(shop_item)
    save_shop(items)

    # Item auch aus allen Spieler-Inventaren entfernen
    item_name = shop_item["name"]
    eco = load_economy()
    players_cleaned = 0
    total_removed   = 0
    for uid, user_data in eco.items():
        inv = user_data.get("inventory", [])
        before = len(inv)
        user_data["inventory"] = [i for i in inv if i != item_name]
        removed = before - len(user_data["inventory"])
        if removed > 0:
            players_cleaned += 1
            total_removed   += removed
    save_economy(eco)

    embed = discord.Embed(
        title="\U0001F5D1\uFE0F Item aus Shop entfernt",
        description=(
            f"**Item:** {item_name}\n"
            f"**Preis war:** {shop_item['price']:,} \U0001F4B5\n"
            f"**Entfernt von:** {interaction.user.mention}\n\n"
            f"**Inventare bereinigt:** {players_cleaned} Spieler\n"
            f"**Items entfernt:** {total_removed}x"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# WARN SYSTEM
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

@bot.tree.command(name="warn", description="[TEAM] Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
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
        title="\u26A0\uFE0F Verwarnung",
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
        f"\u2705 Verwarnung f\u00FCr {nutzer.mention} gespeichert. (Warns gesamt: **{warn_count}**)", ephemeral=True
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
                title="\U0001F507 Du wurdest getimeoutet",
                description=(
                    f"Du hast auf **{interaction.guild.name}** {WARN_AUTO_TIMEOUT_COUNT} Verwarnungen erhalten "
                    f"und wurdest daher f\u00FCr **2 Tage** getimeoutet.\n\n"
                    f"**Letzte Verwarnung:**\n"
                    f"Grund: {grund}\nKonsequenz: {konsequenz}\n\n"
                    f"Deine Rollen wurden vor\u00FCbergehend entfernt.\n"
                    f"Nach dem Timeout melde dich bitte bei einem Teammitglied."
                ),
                color=MOD_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            await nutzer.send(embed=dm_embed)
        except Exception:
            pass
        timeout_embed = discord.Embed(
            title="\U0001F507 Automatischer Timeout",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Grund:** {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht\n"
                f"**Dauer:** 2 Tage\n"
                f"**Rollen entfernt:** \u2705"
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        if log_ch:
            await log_ch.send(embed=timeout_embed)


@bot.tree.command(name="team-warn", description="[ADMIN] Team-Verwarnung an einen Spieler ausgeben (kein Timeout)", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def team_warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr Admins verf\u00FCgbar.", ephemeral=True)
        return

    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)
    warn_entry = {
        "grund":      grund,
        "konsequenz": konsequenz,
        "warned_by":  interaction.user.id,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }
    user_warns.append(warn_entry)
    save_team_warns(warns)
    warn_count = len(user_warns)

    embed = discord.Embed(
        title="\U0001F6E1\uFE0F Team-Verwarnung",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Grund:** {grund}\n"
            f"**Konsequenz:** {konsequenz}\n"
            f"**Verwarnt von:** {interaction.user.mention}\n"
            f"**Team-Warns gesamt:** {warn_count}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    log_ch = interaction.guild.get_channel(TEAM_WARN_LOG_CHANNEL_ID)
    if log_ch:
        await log_ch.send(embed=embed)

    try:
        dm_embed = discord.Embed(
            title="\U0001F6E1\uFE0F Du hast eine Team-Verwarnung erhalten",
            description=(
                f"**Server:** {interaction.guild.name}\n"
                f"**Grund:** {grund}\n"
                f"**Konsequenz:** {konsequenz}\n"
                f"**Team-Warns gesamt:** {warn_count}\n\n"
                f"Bitte halte dich an die Serverregeln."
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await nutzer.send(embed=dm_embed)
    except Exception:
        pass

    await interaction.response.send_message(
        f"\u2705 Team-Verwarnung f\u00FCr {nutzer.mention} gespeichert. (Team-Warns gesamt: **{warn_count}**)",
        ephemeral=True
    )


@bot.tree.command(name="teamwarn-list", description="[ADMIN] Team-Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler")
async def teamwarn_list(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr Admins verf\u00FCgbar.", ephemeral=True)
        return

    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"\u2705 {nutzer.mention} hat keine Team-Verwarnungen.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        ts = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** \u2014 {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"\U0001F6E1\uFE0F Team-Warns von {nutzer.display_name}",
        description="\n".join(lines),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesamt: {len(user_warns)} Team-Warn(s)")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="remove-teamwarn", description="[ADMIN] Letzte Team-Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler")
async def remove_teamwarn(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr Admins verf\u00FCgbar.", ephemeral=True)
        return

    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"\u2139\uFE0F {nutzer.mention} hat keine Team-Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_team_warns(warns)

    log_ch = interaction.guild.get_channel(TEAM_WARN_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="\U0001F5D1\uFE0F Team-Verwarnung entfernt",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Entfernte Verwarnung:** {removed['grund']}\n"
                f"**Entfernt von:** {interaction.user.mention}\n"
                f"**Verbleibende Team-Warns:** {len(user_warns)}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await log_ch.send(embed=log_embed)

    embed = discord.Embed(
        title="\u2705 Team-Verwarnung entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernte Verwarnung:** {removed['grund']}\n"
            f"**Verbleibende Team-Warns:** {len(user_warns)}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="warn-list", description="Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def warn_list(interaction: discord.Interaction, nutzer: discord.Member):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"\u2705 {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        ts  = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** \u2014 {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"\u26A0\uFE0F Warns von {nutzer.display_name}",
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
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"\u2139\uFE0F {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_warns(warns)

    embed = discord.Embed(
        title="\u2705 Verwarnung entfernt",
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
@bot.tree.command(name="rucksack", description="Zeige dein Inventar an (Team: auch per @Erw\u00E4hnung)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Spieler dessen Inventar angezeigt werden soll")
async def rucksack(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids = [r.id for r in interaction.user.roles]
    is_team_m = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids
    allowed  = is_team_m or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES)

    if nutzer is not None:
        if not is_team_m:
            await interaction.response.send_message(
                "\u274C Du hast keine Berechtigung, den Rucksack anderer Spieler einzusehen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    else:
        if not is_team_m and interaction.channel.id != RUCKSACK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
            return
        if not allowed:
            await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
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
        desc   = "\n".join(f"\u2022 **{item}** \u00D7{count}" for item, count in counts.items())

    embed = discord.Embed(
        title=f"\U0001F392 Rucksack von {ziel.display_name}",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /uebergeben
@bot.tree.command(name="uebergeben", description="Gib ein Item aus deinem Inventar an jemanden weiter", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Empf\u00E4nger", item="Item ausw\u00E4hlen", menge="Wie viele m\u00F6chtest du \u00FCbergeben? (Standard: 1)")
@app_commands.autocomplete(item=inventory_item_autocomplete)
async def uebergeben(interaction: discord.Interaction, nutzer: discord.Member, item: str, menge: int = 1):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != RUCKSACK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("\u274C Du kannst nicht an dich selbst \u00FCbergeben.", ephemeral=True)
        return

    if menge < 1:
        await interaction.response.send_message("\u274C Die Menge muss mindestens 1 sein.", ephemeral=True)
        return

    eco        = load_economy()
    giver_data = get_user(eco, interaction.user.id)
    inv        = giver_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if not match:
        await interaction.response.send_message(
            f"\u274C **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        return

    available = inv.count(match)
    if available < menge:
        await interaction.response.send_message(
            f"\u274C Du hast nur **{available}\u00D7** **{match}** im Inventar, aber m\u00F6chtest **{menge}\u00D7** \u00FCbergeben.",
            ephemeral=True
        )
        return

    for _ in range(menge):
        inv.remove(match)
    receiver_data = get_user(eco, nutzer.id)
    receiver_data.setdefault("inventory", []).extend([match] * menge)
    save_economy(eco)

    # Handy weitergeben \u2192 Kanal-Berechtigung f\u00FCr Empf\u00E4nger
    if normalize_item_name(match) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, nutzer)

    menge_text = f"\u00D7{menge}" if menge > 1 else ""
    embed = discord.Embed(
        title="\U0001F91D Item \u00FCbergeben",
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
            f"\u274C **{item}** ist nicht in deinem Inventar.", ephemeral=True
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
        title="\U0001F575\uFE0F Item versteckt",
        description=(
            f"**Item:** {match}\n"
            f"**Versteckt an:** {ort}\n\n"
            f"Nur du kannst es wieder herausnehmen."
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, view=view)


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# TEAM ITEM COMMANDS
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

@bot.tree.command(name="item-geben", description="[TEAM] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname (muss im Shop vorhanden sein)")
@app_commands.autocomplete(item=shop_item_autocomplete)
async def item_geben(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    shop_items = load_shop()
    shop_item  = find_shop_item(shop_items, item)
    if not shop_item:
        await interaction.response.send_message(
            f"\u274C Das Item **{item}** existiert nicht im Shop.\n"
            f"Es k\u00F6nnen nur vorhandene Shop-Items vergeben werden. Nutze `/shop` um alle Items zu sehen.",
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
        title="\U0001F381 Item gegeben",
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
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inv       = user_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if not match:
        await interaction.response.send_message(
            f"\u274C **{item}** ist nicht im Inventar von {nutzer.mention}.", ephemeral=True
        )
        return

    inv.remove(match)
    save_economy(eco)

    embed = discord.Embed(
        title="\U0001F5D1\uFE0F Item entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {match}\n"
            f"**Entfernt von:** {interaction.user.mention}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# KARTENKONTROLLE
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

KARTENKONTROLLE_CHANNEL_ID = 1491116234459185162


@bot.tree.command(name="kartenkontrolle", description="[TEAM] Sendet eine DM-Erinnerung zur Kartenkontrolle an alle Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def kartenkontrolle(interaction: discord.Interaction):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
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
                title="\U0001FAAA Kartenkontrolle",
                description=(
                    f"**Hallo {member.display_name}!**\n\n"
                    f"Es findet gerade eine **Kartenkontrolle** statt.\n"
                    f"Bitte begib dich in den Kanal:\n"
                    f"[\U0001F517 Zur Kartenkontrolle]({channel_link})\n\n"
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
        f"\u2705 Kartenkontrolle-DM gesendet!\n**Erfolgreich:** {sent} | **Fehlgeschlagen (DMs zu):** {failed}",
        ephemeral=True
    )


# \u2500\u2500 Ausweis Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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


# \u2500\u2500 Einreise DM Flow \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def einreise_chat_flow(channel: discord.TextChannel, member: discord.Member, guild: discord.Guild, einreise_typ: str):
    def dm_check(m):
        return m.author.id == member.id and isinstance(m.channel, discord.DMChannel)

    felder = [
        ("vorname",       "\U0001F4DD **Vorname** \u2014 Bitte gib deinen Vornamen ein:"),
        ("nachname",      "\U0001F4DD **Nachname** \u2014 Bitte gib deinen Nachnamen ein:"),
        ("geburtsdatum",  "\U0001F4DD **Geburtsdatum** \u2014 Bitte gib dein Geburtsdatum ein (Format: TT.MM.JJJJ):"),
        ("alter",         "\U0001F4DD **Alter** \u2014 Bitte gib dein Alter ein (z.B. 25):"),
        ("nationalitaet", "\U0001F4DD **Nationalit\u00E4t** \u2014 Bitte gib deine Nationalit\u00E4t ein (z.B. Deutsch):"),
        ("wohnort",       "\U0001F4DD **Wohnort** \u2014 Bitte gib deinen Wohnort ein (z.B. Los Santos):"),
    ]

    antworten = {}
    typ_label = "\U0001F935 Legale Einreise" if einreise_typ == "legal" else "\U0001F977 Illegale Einreise"

    try:
        dm = await member.create_dm()
        await dm.send(
            f"\U0001FAAA **Ausweis-Erstellung gestartet!** ({typ_label})\n"
            f"Beantworte bitte die folgenden **{len(felder)} Fragen**. "
            f"Du hast jeweils **2 Minuten** pro Antwort."
        )
    except Exception:
        await channel.send(
            f"{member.mention} \u274C Ich kann dir keine DM senden. Bitte aktiviere DMs von Servermitgliedern.",
            delete_after=15
        )
        return

    for key, frage in felder:
        await dm.send(frage)
        try:
            antwort = await bot.wait_for("message", check=dm_check, timeout=120.0)
            antworten[key] = antwort.content.strip()
        except asyncio.TimeoutError:
            await dm.send("\u274C Zeit abgelaufen! Bitte w\u00E4hle deine Einreiseart erneut.")
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
        title="\U0001FAAA Ausweis ausgestellt",
        description="Dein Ausweis wurde erfolgreich erstellt!",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Name",          value=f"{antworten['vorname']} {antworten['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum",  value=antworten["geburtsdatum"],                          inline=True)
    embed.add_field(name="Alter",         value=antworten["alter"],                                 inline=True)
    embed.add_field(name="Nationalit\u00E4t",  value=antworten["nationalitaet"],                         inline=True)
    embed.add_field(name="Wohnort",       value=antworten["wohnort"],                               inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                          inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{ausweisnummer}`",                               inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Kryptik Roleplay \u2014 Ausweis")

    await dm.send("\u2705 **Dein Ausweis wurde erfolgreich erstellt!**", embed=embed)


# \u2500\u2500 Einreise Select Menu \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class EinreiseSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Legale Einreise",
                emoji="\U0001F935",
                value="legal",
                description="Einreise als legaler Bewohner"
            ),
            discord.SelectOption(
                label="Illegale Einreise",
                emoji="\U0001F977",
                value="illegal",
                description="Einreise als illegale Person"
            ),
        ]
        super().__init__(
            placeholder="\u2708\uFE0F W\u00E4hle deine Einreiseart...",
            options=options,
            custom_id="einreise_select_main"
        )

    async def callback(self, interaction: discord.Interaction):
        member   = interaction.user
        guild    = interaction.guild
        role_ids = [r.id for r in member.roles]

        if LEGAL_ROLE_ID in role_ids or ILLEGAL_ROLE_ID in role_ids:
            await interaction.response.send_message(
                "\u274C Du hast bereits eine Einreiseart gew\u00E4hlt. Eine \u00C4nderung ist nur durch den RP-Tod m\u00F6glich.",
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
            f"\u2705 **{'Legale' if typ == 'legal' else 'Illegale'} Einreise** gew\u00E4hlt!\n"
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
            title="\u2708\uFE0F Einreise \u2014 Kryptik Roleplay",
            description=(
                "\U0001F935\u200D\u2642\uFE0F **Legale Einreise** \U0001F935\u200D\u2642\uFE0F\n"
                "Du wirst auf unserem Server als Legale Person einreisen. "
                "Du darfst als Legaler Bewohner keine Illegalen Aktivit\u00E4ten ausf\u00FChren.\n\n"
                "\U0001F977 **Illegale Einreise** \U0001F977\n"
                "Du wirst auf unserem Server als Illegale Person einreisen. "
                "Du darfst keine Staatlichen Berufe aus\u00FCben.\n\n"
                "\u26A0\uFE0F **Hinweis** \u26A0\uFE0F\n"
                "Eine \u00C4nderung der Einreiseart ist nur durch den RP-Tod deines Charakters m\u00F6glich."
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Kryptik Roleplay \u2014 Einreisesystem")
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
            f"\u274C Diesen Command kannst du nur in <#{AUSWEIS_CHANNEL_ID}> benutzen.", ephemeral=True
        )
        return

    ausweis_data = load_ausweis()
    entry = ausweis_data.get(str(interaction.user.id))

    if not entry:
        await interaction.response.send_message(
            "\u274C Du hast noch keinen Ausweis. W\u00E4hle zuerst deine Einreiseart und erstelle deinen Ausweis.",
            ephemeral=True
        )
        return

    typ_label = "\U0001F935 Legale Einreise" if entry.get("einreise_typ") == "legal" else "\U0001F977 Illegale Einreise"

    embed = discord.Embed(
        title="\U0001FAAA Personalausweis",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="Name",          value=f"{entry['vorname']} {entry['nachname']}",  inline=True)
    embed.add_field(name="Geburtsdatum",  value=entry["geburtsdatum"],                      inline=True)
    embed.add_field(name="Alter",         value=entry.get("alter", "?"),                    inline=True)
    embed.add_field(name="Nationalit\u00E4t",  value=entry["nationalitaet"],                     inline=True)
    embed.add_field(name="Wohnort",       value=entry["wohnort"],                           inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                  inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{entry['ausweisnummer']}`",              inline=False)
    embed.set_footer(text="Kryptik Roleplay \u2014 Personalausweis")

    await interaction.response.send_message(embed=embed)


# /ausweis-remove (Admin only)
@bot.tree.command(name="ausweis-remove", description="[ADMIN] Loescht den Ausweis eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler dessen Ausweis geloescht werden soll")
@app_commands.default_permissions(administrator=True)
async def ausweis_remove(interaction: discord.Interaction, nutzer: discord.Member):
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    uid = str(nutzer.id)

    if uid not in ausweis_data:
        await interaction.response.send_message(
            f"\u274C {nutzer.mention} hat keinen Ausweis.", ephemeral=True
        )
        return

    del ausweis_data[uid]
    save_ausweis(ausweis_data)

    embed = discord.Embed(
        title="\U0001F5D1\uFE0F Ausweis gel\u00F6scht",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Gel\u00F6scht von:** {interaction.user.mention}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 Admin Ausweis-Erstellen (Chat-basiert) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def ausweis_create_dm_flow(admin: discord.Member, guild: discord.Guild, target: discord.Member, original_channel: discord.TextChannel):
    def dm_check(m):
        return m.author.id == admin.id and isinstance(m.channel, discord.DMChannel)

    felder = [
        ("vorname",       "\U0001F4DD **Vorname** des Spielers:"),
        ("nachname",      "\U0001F4DD **Nachname** des Spielers:"),
        ("geburtsdatum",  "\U0001F4DD **Geburtsdatum** (Format: TT.MM.JJJJ):"),
        ("alter",         "\U0001F4DD **Alter** (z.B. 25):"),
        ("herkunft",      "\U0001F4DD **Herkunft** (z.B. Deutsch):"),
        ("wohnort",       "\U0001F4DD **Wohnort** (z.B. Los Santos):"),
        ("einreise_typ",  "\U0001F4DD **Einreiseart** \u2014 Tippe `legal` oder `illegal`:"),
    ]

    antworten = {}

    try:
        dm = await admin.create_dm()
        await dm.send(
            f"\U0001FAAA **Ausweis-Erstellung f\u00FCr {target.display_name} gestartet!**\n"
            f"Beantworte bitte die folgenden **{len(felder)} Fragen**. "
            f"Du hast jeweils **2 Minuten** pro Antwort."
        )
    except Exception:
        await original_channel.send(
            f"{admin.mention} \u274C Ich kann dir keine DM senden. Bitte aktiviere DMs von Servermitgliedern.",
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
                    await dm.send("\u274C Ung\u00FCltige Eingabe. Bitte starte den Command erneut und tippe `legal` oder `illegal`.")
                    return
                wert = wert.lower()

            antworten[key] = wert
        except asyncio.TimeoutError:
            await dm.send("\u274C Zeit abgelaufen! Bitte starte `/ausweis-create` erneut.")
            return

    ausweisnummer = generate_ausweisnummer()
    typ_label     = "\U0001F935 Legale Einreise" if antworten["einreise_typ"] == "legal" else "\U0001F977 Illegale Einreise"

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
        title="\U0001FAAA Ausweis erstellt",
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

    await dm.send("\u2705 **Ausweis erfolgreich erstellt!**", embed=embed)


# /ausweis-create (Team only)
@bot.tree.command(name="ausweis-create", description="[TEAM] Erstellt einen Ausweis fuer einen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler fuer den der Ausweis erstellt wird")
@app_commands.default_permissions(manage_messages=True)
async def ausweis_create(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    if str(nutzer.id) in ausweis_data:
        await interaction.response.send_message(
            f"\u274C {nutzer.mention} hat bereits einen Ausweis. Bitte zuerst mit /ausweis-remove l\u00F6schen.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"\u2705 Ausweis-Erstellung f\u00FCr **{nutzer.display_name}** gestartet!\n"
        f"Ich schicke dir die Fragen per **DM** \u2014 nur du siehst sie.",
        ephemeral=True
    )
    asyncio.create_task(ausweis_create_dm_flow(interaction.user, interaction.guild, nutzer, interaction.channel))


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# /delete \u2014 Nachrichten l\u00F6schen (Team only)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

@bot.tree.command(name="delete", description="[TEAM] L\u00F6scht eine bestimmte Anzahl von Nachrichten im Kanal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(anzahl="Anzahl der zu l\u00F6schenden Nachrichten (max. 100)")
@app_commands.default_permissions(manage_messages=True)
async def delete_messages(interaction: discord.Interaction, anzahl: int):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    if anzahl < 1 or anzahl > 100:
        await interaction.response.send_message("\u274C Bitte eine Zahl zwischen 1 und 100 angeben.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    geloescht = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(
        f"\u2705 **{len(geloescht)}** Nachrichten wurden gel\u00F6scht.",
        ephemeral=True
    )


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# /create-event \u2014 Event erstellen (Team only)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

EVENT_ANNOUNCEMENT_CHANNEL_ID = 1490882564561567864
EVENT_PING_ROLE_ID             = 1490855737130221598


async def create_event_channel_flow(admin: discord.Member, guild: discord.Guild, channel: discord.TextChannel):
    def check(m):
        return m.author.id == admin.id and m.channel.id == channel.id

    felder = [
        ("was",        "\U0001F4CB **Was ist das Event?** (z.B. Fahrzeugrennen, Bankraub, Stadtfest):"),
        ("startpunkt", "\U0001F4CD **Wo ist der Startpunkt?** (z.B. Pillbox Hill, Legion Square):"),
        ("erklaerung", "\U0001F4DD **Erkl\u00E4rung / Beschreibung des Events:**"),
        ("dauer",      "\u23F1\uFE0F **Dauer des Events?** (z.B. 1 Stunde, 30 Minuten):"),
        ("preis",      "\U0001F4B0 **Preis / Belohnung?** (z.B. 50.000$, Kein Preis):"),
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
        await channel.send(f"{admin.mention} \u274C Event-Channel nicht gefunden.", delete_after=10)
        return

    ping_role = guild.get_role(EVENT_PING_ROLE_ID)
    role_mention = ping_role.mention if ping_role else ""

    embed = discord.Embed(
        title="\U0001F389 Neues Event!",
        color=0x00B4D8,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F4CB Event",        value=antworten["was"],        inline=False)
    embed.add_field(name="\U0001F4CD Startpunkt",   value=antworten["startpunkt"], inline=True)
    embed.add_field(name="\u23F1\uFE0F Dauer",        value=antworten["dauer"],      inline=True)
    embed.add_field(name="\U0001F4B0 Preis",        value=antworten["preis"],      inline=True)
    embed.add_field(name="\U0001F4DD Beschreibung", value=antworten["erklaerung"], inline=False)
    embed.set_footer(text=f"Event erstellt von {admin.display_name}")

    await event_channel.send(content=role_mention, embed=embed)
    await channel.send(f"{admin.mention} \u2705 **Event wurde erfolgreich gepostet** in {event_channel.mention}!", delete_after=10)


@bot.tree.command(name="create-event", description="[TEAM] Erstellt ein neues Event", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def create_event(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.send_message(
        "\U0001F389 **Event-Erstellung gestartet!** Beantworte die Fragen hier im Channel.",
        ephemeral=True
    )
    asyncio.create_task(create_event_channel_flow(interaction.user, interaction.guild, interaction.channel))


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# /create-giveaway \u2014 Giveaway erstellen (Team only)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

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

    frage1 = await channel.send(f"{admin.mention} \U0001F381 **Was wird verlost?** (z.B. 500.000$, Fahrzeug, Item):")
    antwort1 = await bot.wait_for("message", check=check, timeout=None)
    gewinn = antwort1.content.strip()
    try:
        await frage1.delete()
        await antwort1.delete()
    except Exception:
        pass

    frage2 = await channel.send(f"{admin.mention} \u23F1\uFE0F **Wie lange l\u00E4uft das Giveaway?** (z.B. `2 Tage`, `12 Stunden`, `30 Minuten`):")
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
            f"{admin.mention} \u274C Zeitformat nicht erkannt. Bitte so eingeben: `2 Tage`, `12 Stunden`, `30 Minuten`",
            delete_after=8
        )
    try:
        await frage2.delete()
    except Exception:
        pass

    giveaway_channel = guild.get_channel(GIVEAWAY_CHANNEL_ID)
    if giveaway_channel is None:
        await channel.send(f"{admin.mention} \u274C Giveaway-Channel nicht gefunden.", delete_after=10)
        return

    end_timestamp = int((datetime.now(timezone.utc).timestamp()) + sekunden)

    embed = discord.Embed(
        title="\U0001F389 Giveaway!",
        color=0xF1C40F,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F381 Gewinn",   value=gewinn,                              inline=False)
    embed.add_field(name="\u23F1\uFE0F Endet",    value=f"<t:{end_timestamp}:R>",            inline=True)
    embed.add_field(name="\U0001F4C5 Datum",    value=f"<t:{end_timestamp}:F>",            inline=True)
    embed.set_footer(text=f"Giveaway erstellt von {admin.display_name} \u2022 Reagiere mit \U0001F389 um teilzunehmen!")

    msg = await giveaway_channel.send(embed=embed)
    await msg.add_reaction("\U0001F389")
    await channel.send(
        f"{admin.mention} \u2705 **Giveaway wurde erfolgreich gepostet** in {giveaway_channel.mention}!\n"
        f"Endet: <t:{end_timestamp}:R>",
        delete_after=10
    )

    await asyncio.sleep(sekunden)

    try:
        msg = await giveaway_channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji="\U0001F389")
        if reaction:
            users = [u async for u in reaction.users() if not u.bot]
            if users:
                winner = random.choice(users)
                win_embed = discord.Embed(
                    title="\U0001F389 Giveaway beendet!",
                    description=(
                        f"**Gewinn:** {gewinn}\n"
                        f"**Gewinner:** {winner.mention} \U0001F38A\n\n"
                        f"Herzlichen Gl\u00FCckwunsch!"
                    ),
                    color=0xF1C40F,
                    timestamp=datetime.now(timezone.utc)
                )
                await giveaway_channel.send(content=winner.mention, embed=win_embed)
            else:
                await giveaway_channel.send("\u274C Niemand hat am Giveaway teilgenommen.")
    except Exception as e:
        await log_bot_error("Giveaway-Auswertung fehlgeschlagen", str(e), guild)


@bot.tree.command(name="create-giveaway", description="[TEAM] Erstellt ein neues Giveaway", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def create_giveaway(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.send_message(
        "\U0001F381 **Giveaway-Erstellung gestartet!** Beantworte die Fragen hier im Channel.",
        ephemeral=True
    )
    asyncio.create_task(create_giveaway_channel_flow(interaction.user, interaction.guild, interaction.channel))


@bot.tree.command(name="lobby-abstimmung", description="[LOBBY] Sendet eine Lobby-Abstimmung", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def lobby_abstimmung(interaction: discord.Interaction):
    if not any(r.id == LOBBY_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr das Lobby-Team verf\u00FCgbar.", ephemeral=True)
        return

    kanal = interaction.guild.get_channel(LOBBY_CHANNEL_ID)
    if not kanal:
        await interaction.response.send_message("\u274C Lobby-Kanal nicht gefunden.", ephemeral=True)
        return

    datum = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    embed = discord.Embed(
        title="Lobby Abstimmung",
        description=(
            "\u2705 **Ich komme**\n\n"
            "\U0001F551 **Ich komme sp\u00E4ter**\n\n"
            "\u274C **Ich komme nicht**\n\n"
            f"**Datum:** {datum}\n\n"
            "**Uhrzeit:** 18:00"
        ),
        color=0x00BFFF,
        timestamp=datetime.now(timezone.utc)
    )

    GIF_URL = "https://share.creavite.co/69d7a4bca828deb1587385dd.gif"
    ping_text = "<@&1490855734517174376>"

    await interaction.response.send_message("\u2705 Abstimmung gesendet!", ephemeral=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GIF_URL) as resp:
                if resp.status == 200:
                    gif_bytes = await resp.read()
                    gif_file = discord.File(io.BytesIO(gif_bytes), filename="lobby.gif")
                    embed.set_image(url="attachment://lobby.gif")
                    msg = await kanal.send(content=ping_text, file=gif_file, embed=embed)
                else:
                    raise ValueError(f"HTTP {resp.status}")
    except Exception:
        embed.set_image(url=GIF_URL)
        msg = await kanal.send(content=ping_text, embed=embed)

    await msg.add_reaction("\u2705")
    await msg.add_reaction("\U0001F551")
    await msg.add_reaction("\u274C")


@bot.tree.command(name="lobby-open", description="[LOBBY] \u00D6ffnet die Lobby", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def lobby_open(interaction: discord.Interaction):
    if not any(r.id == LOBBY_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr das Lobby-Team verf\u00FCgbar.", ephemeral=True)
        return

    kanal = interaction.guild.get_channel(LOBBY_CHANNEL_ID)
    if not kanal:
        await interaction.response.send_message("\u274C Lobby-Kanal nicht gefunden.", ephemeral=True)
        return

    host_name = interaction.user.display_name

    embed = discord.Embed(
        title="Lobby Status",
        description=(
            "Jetzt Ge\u00F6ffnet\n\n"
            f"**Lobby Host**\n{host_name}\n\n"
            "Das Team von Cryptik Roleplay w\u00FCnscht euch Viel spa\u00DF beim RP"
        ),
        color=0x00BFFF,
        timestamp=datetime.now(timezone.utc)
    )

    GIF_URL = "https://share.creavite.co/69d7bee5a828deb1587385f2.gif"
    ping_text = "<@&1490855734517174376>"

    await interaction.response.send_message("\u2705 Lobby ge\u00F6ffnet!", ephemeral=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GIF_URL) as resp:
                if resp.status == 200:
                    gif_bytes = await resp.read()
                    gif_file = discord.File(io.BytesIO(gif_bytes), filename="lobby_open.gif")
                    embed.set_image(url="attachment://lobby_open.gif")
                    await kanal.send(content=ping_text, file=gif_file, embed=embed)
                else:
                    raise ValueError(f"HTTP {resp.status}")
    except Exception:
        embed.set_image(url=GIF_URL)
        await kanal.send(content=ping_text, embed=embed)


# \u2500\u2500 Bot starten \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    print("\u274C DISCORD_TOKEN ist nicht gesetzt!")
    exit(1)

bot.run(TOKEN)
