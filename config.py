# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# config.py \u2014 Imports, Konstanten, IDs, Regex, Feature-Flags
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

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
intents.invites = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot_start_time = None
invite_cache = {}

INTERACTION_VIEW_TIMEOUT = int(os.environ.get("INTERACTION_VIEW_TIMEOUT", "300"))


class TimedDisableView(discord.ui.View):
    def __init__(self, timeout: int = INTERACTION_VIEW_TIMEOUT):
        super().__init__(timeout=timeout)
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        self.message = interaction.message
        return True

    async def on_timeout(self):
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True

        message = getattr(self, "message", None)
        if message is not None:
            try:
                await message.edit(view=self)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

OWNER_ID          = 1411796740243456092   # Server-Inhaber â€” immer alle Rechte
ADMIN_ROLE_ID     = 1490855650081636352
MOD_ROLE_ID       = 1496147874256392202
INHABER_ROLE_ID   = 1490855647259136053
DASH_ROLE_ID      = 1490855702225485936   # Highteam / Dashboard-Zugang
TICKET_MOD_ROLE_ID = 1490855703370534965  # Rolle mit Ticket-Zugriff

# Alle Rollen die Tickets sehen, schlieÃŸen und zuweisen dÃ¼rfen
TICKET_STAFF_ROLE_IDS = {
    INHABER_ROLE_ID,
    ADMIN_ROLE_ID,
    MOD_ROLE_ID,
    DASH_ROLE_ID,
    TICKET_MOD_ROLE_ID,
}
WHITELIST_ROLE_ID  = 1490855725516460234   # Bewerber-Rolle (Autorole beim Beitritt)
BEWERBER_ROLE_ID   = 1490855725516460234   # identisch, f\u00FCr lesbareren Code
LOBBY_ROLE_ID     = 1490855714162475259

LOBBY_CHANNEL_ID  = 1490882583909765190

SERVER_LOG_CHANNEL_ID  = 1490878131240829028  # Kanal-/Rollenstruktur-Änderungen
MOD_LOG_CHANNEL_ID     = 1490878132230819840  # Moderation
BOT_LOG_CHANNEL_ID     = 1490878133279264842  # Bot-Fehler & Neustarts
MEMBER_LOG_CHANNEL_ID  = 1490878134847930368  # Beitritt/Verlassen + Angelbeweise
MESSAGE_LOG_CHANNEL_ID = 1490878135837917234  # Nachrichten gelöscht/bearbeitet
ROLE_LOG_CHANNEL_ID    = 1490878137385619598  # Rollenzuweisungen an Mitglieder
AKTIVITAET_WARN_CHANNEL_ID = 1497385121324732567
JOIN_LOG_CHANNEL_ID    = 1490878153391083683
MEMES_CHANNEL_ID       = 1490882578276810924
GUILD_ID               = 1490839259907887239
TICKET_CHANNEL_ID      = 1490855943230066818

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

# \u2500\u2500 Economy \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
LOHNLISTE_CHANNEL_ID = 1490890346668888194
LOHN_CHANNEL_ID      = 1490890348254200049
BANK_CHANNEL_ID      = 1490890349382734044
SHOP_CHANNEL_ID      = 1490890311755628584

CITIZEN_ROLE_ID = 1490855722534310003

WAGE_ROLES = {
    1490855796932739093: 1000,   # Arbeitslosenkasse
    1490855789844234310: 3000,   # Niedrige Lohnklasse
    1490855790913785886: 3600,   # Mittlere Lohnklasse
    1490855791953973421: 4500,   # Hohe Lohnklasse
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
HIDDEN_ITEMS_FILE  = DATA_DIR / "hidden_items.json"
COUNTING_FILE      = DATA_DIR / "counting_state.json"
ABSTIMMUNG_FILE    = DATA_DIR / "abstimmung_data.json"
AUSWEIS_FILE         = DATA_DIR / "ausweis_data.json"
FUEHRERSCHEIN_FILE      = DATA_DIR / "fuehrerschein_data.json"
FAHRLEHRER_LIZENZ_FILE  = DATA_DIR / "fahrlehrer_lizenz_data.json"
HANDY_FILE           = DATA_DIR / "handy_numbers.json"
CASINO_COOLDOWN_FILE = DATA_DIR / "casino_cooldown.json"
SAVED_ROLES_FILE     = DATA_DIR / "saved_roles.json"

# \u2500\u2500 Casino Kanal-IDs \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
CASINO_CHANNEL_ID     = 1490889784753782784
CASINO_LOG_CHANNEL_ID = 1490878131240829028  # gleicher Kanal wie SERVER_LOG

# Neue Kanal- und Rollen-IDs
WARN_LOG_CHANNEL_ID      = 1491113577258684466
TEAM_WARN_LOG_CHANNEL_ID = 1490878144146833450
MONEY_LOG_CHANNEL_ID    = 1490878138429997087
RUCKSACK_CHANNEL_ID     = 1490882591023173682
UEBERGEBEN_CHANNEL_ID   = 1490882592445304972
VERSTECKEN_CHANNEL_ID   = 1490882589014364250
TEAM_CITIZEN_CHANNEL_ID = 1490882591023173682

WELCOME_CHANNEL_ID  = 1490878151897911557
GOODBYE_CHANNEL_ID  = 1490878154733260951
EINREISE_CHANNEL_ID = 1490878156582686853
AUSWEIS_CHANNEL_ID  = 1490882590012604538
LEGAL_ROLE_ID       = 1490855729635135489
ILLEGAL_ROLE_ID     = 1490855730767597738

# \u2500\u2500 F\u00FChrerschein System \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
FUEHRERSCHEIN_ERSTELLEN_ROLE_ID = 1490855755296014446
FUEHRERSCHEIN_ENTZIEHEN_ROLE_ID = 1490855751797969039

# \u2500\u2500 Rechnungs-System \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
LAMD_ROLE_ID        = 1490855752712327210
LAPD_ROLE_ID        = 1490855751797969039  # identisch mit FUEHRERSCHEIN_ENTZIEHEN_ROLE_ID
LACS_ROLE_ID        = 1490855754213753024
RECHNUNGEN_CHANNEL_ID = 1492314171373649983
LSPD_ROLE_ID          = 1490855749008621659
RECHNUNGEN_FILE     = DATA_DIR / "rechnungen_data.json"

# \u2500\u2500 Command-Berechtigungs-Rollen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
WARN_ROLE_ID        = 1490855711674994688  # /warn, /warn-list, /remove-warn
SHOP_ADMIN_ROLE_ID  = 1490855717354213388  # /shop-add, /delete-item
ITEM_MANAGE_ROLE_ID = 1490855718658510908  # /item-add, /remove-item
MONEY_ADD_ROLE_1_ID = 1490855647259136053  # /money-add
MONEY_ADD_ROLE_2_ID = 1490855648978669599  # /money-add

# \u2500\u2500 Handy System \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
HANDY_CHANNEL_ID      = 1490890317199708160
HANDY_ITEM_NAME       = "\U0001F4F1| Handy"

DISPATCH_MD_ROLE_ID   = 1490855752712327210
DISPATCH_PD_ROLE_ID   = 1490855751797969039
DISPATCH_ADAC_ROLE_ID = 1490855754213753024
INSTAGRAM_ROLE_ID     = 1490855786698641428
PARSHIP_ROLE_ID       = 1490855783989121024
EBAY_ROLE_ID          = 1490855785159331850
HANDY_AN_ROLE_ID      = 1490855780797251744
HANDY_AUS_ROLE_ID     = 1490855781778722976
SIM_WECHSEL_CHANNEL_ID = 1490882589014364250

IC_CHAT_CHANNEL_ID    = 0

WARN_AUTO_TIMEOUT_COUNT = 3
WARN_AUTO_BAN_COUNT     = 6
START_CASH              = 5_000

LOG_COLOR = 0xE67E22
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

# \u2500\u2500 Event System \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
EVENT_ANNOUNCEMENT_CHANNEL_ID = 1490882564561567864
EVENT_PING_ROLE_ID             = 1490855737130221598

# \u2500\u2500 Giveaway \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
GIVEAWAY_CHANNEL_ID = 1490882565618536551

# \u2500\u2500 Kartenkontrolle \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
KARTENKONTROLLE_CHANNEL_ID = 1491116234459185162

# \u2500\u2500 Team \u00DCbersicht \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
TEAM_OVERVIEW_CHANNEL_ID = 1490882570899030136
DUTY_FILE = DATA_DIR / "duty_status.json"

# Rollen die im Team-Embed angezeigt werden (nur IDs \u2014 Name kommt vom Server)
TEAM_ROLES = [
    1490855647259136053,
    1490855648978669599,
    1490855654347505706,
    1490855657543303239,
    1490855655408664577,
    1490855656352251987,
    1490855659506372743,
    1490855661137956879,
    1490855664854106225,
    1490855679282516100,
    1490855680708579389,
    1490855688208126095,
    1490855689424212110,
    1490855690183381087,
    1492678578071146536,
    1492678644277969048,
    1490855692477923520,
    1490855693786550404,
    1490855695363342358,
    1490855695912931329,
    1498395437206601828,
    1498395500137807932,
]

# Set f\u00FCr schnelle Zugriffspr\u00FCfung (Button-Berechtigung)
TEAM_ROLE_IDS = set(TEAM_ROLES)
