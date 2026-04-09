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

# Sicherheitscheck: Bot lÃ¤uft NUR auf Railway, nie doppelt in Replit
# Auf Railway wird RAILWAY_ENVIRONMENT automatisch gesetzt
if not os.environ.get("RAILWAY_ENVIRONMENT") and not os.environ.get("FORCE_LOCAL_RUN"):
    print("=" * 60)
    print("STOPP: Bot wurde NICHT gestartet.")
    print("Dieser Bot lÃ¤uft ausschlieÃŸlich auf Eisenbahn.")
    print("Bitte NICHT in Replit starten â€” nur auf Railway eingesetzt!")
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

# Rollen werden automatisch vergeben, sobald ein Charakter erstellt wurde
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

TICKET_SETUP_CHANNEL_ID = 1490882553559650355
TICKET_CATEGORY_DEFAULT = 1490882554570608751
TICKET_CATEGORY_HIGHTEAM = 1491069210389119016
TICKET_CATEGORY_FRAKTION = 1491069425384685750
TICKET_LOG_CHANNEL_ID = 1490878139306606743

COUNTING_CHANNEL_ID = 1490882580487340044

# \u2500\u2500 Wirtschaft \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
LOHNLISTE_CHANNEL_ID = 1490890346668888194
LOHN_CHANNEL_ID = 1490890348254200049
BANK_CHANNEL_ID = 1490890349382734044
SHOP_CHANNEL_ID = 1490890311755628584
HANDY_CHANNEL_ID         = 1490890317199708160
  DISPATCH_MD_ROLE_ID      = 1490855752712327210
  DISPATCH_PD_ROLE_ID      = 1490855751797969039
  DISPATCH_ADAC_ROLE_ID    = 1490855754213753024
  INSTAGRAM_ROLE_ID        = 1490855786698641428
  PARSHIP_ROLE_ID          = 1490855783989121024
  IC_CHAT_CHANNEL_ID       = 0  # <- IC-Chat Kanal-ID hier eintragen!
  PHONE_FILE               = DATA_DIR / "phone_data.json"


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
ZUSÃ„TZLICHER_LOHNROLL_LOHN = 1200

TÃ„GLICHES_LIMIT = 1_000_000

BETRAG_CHOICES = [
    app_commands.Choice(name="1.000 \U0001f4b5", value=1_000),
    app_commands.Choice(name="5.000 \U0001f4b5", value=5_000),
    app_commands.Choice(name="10.000 \U0001f4b5", value=10_000),
    app_commands.Choice(name="25.000 \U0001f4b5", value=25_000),
    app_commands.Choice(name="50.000 \U0001f4b5", value=50_000),
    app_commands.Choice(name="100.000 \U0001f4b5", value=100_000),
    app_commands.Choice(name="250.000 \U0001f4b5", value=250_000),
    app_commands.Choice(name="500.000 \U0001f4b5", value=500_000),
    app_commands.Choice(name="1.000.000 \U0001f4b5", value=1_000_000),
]

LIMIT_CHOICES = [
    app_commands.Choice(name="1.000.000 \U0001f4b5", value=1_000_000),
    app_commands.Choice(name="2.000.000 \U0001f4b5", value=2_000_000),
    app_commands.Choice(name="3.000.000 \U0001f4b5", value=3_000_000),
    app_commands.Choice(name="4.000.000 \U0001f4b5", value=4_000_000),
    app_commands.Choice(name="5.000.000 \U0001f4b5", value=5_000_000),
    app_commands.Choice(name="6.000.000 \U0001f4b5", value=6_000_000),
    app_commands.Choice(name="7.000.000 \U0001f4b5", value=7_000_000),
    app_commands.Choice(name="8.000.000 \U0001f4b5", value=8_000_000),
    app_commands.Choice(name="9.000.000 \U0001f4b5", value=9_000_000),
    app_commands.Choice(name="10.000.000 \U0001f4b5", value=10_000_000),
]

# Persistenter Datenspeicher â€“ auf Railway: Volume unter /data mounten und DATA_DIR=/data setzen
# Ohne DATA_DIR wird der Ordner "data" neben der Bot-Datei genutzt (lokal ok, Railway: verloren bei Redeploy!)
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

ECONOMY_FILE = DATA_DIR / "economy_data.json"
SHOP_FILE = DATA_DIR / "shop_data.json"
WARNS_FILE = DATA_DIR / "warns_data.json"
HIDDEN_ITEMS_FILE = DATA_DIR / "hidden_items.json"
AUSWEIS_FILE = DATA_DIR / "ausweis_data.json"

# Neue Kanal- und Rollen-IDs
WARN_LOG_CHANNEL_ID = 1491113577258684466
MONEY_LOG_CHANNEL_ID = 1490878138429997087
RUCKSACK_CHANNEL_ID = 1490882592445304972
UEBERGEBEN_CHANNEL_ID = 1490882589014364250
VERSTECKEN_CHANNEL_ID = 1490882591023173682
TEAM_CITIZEN_CHANNEL_ID = 1490882591023173682

WELCOME_CHANNEL_ID = 1490878151897911557
GOODBYE_CHANNEL_ID = 1490878154733260951
EINREISE_CHANNEL_ID = 1490878156582686853
AUSWEIS_CHANNEL_ID = 1490882590012604538
LEGAL_ROLE_ID = 1490855729635135489
ILLEGAL_ROLE_ID = 1490855730767597738

WARN_AUTO_TIMEOUT_COUNT = 3
START_CASH = 5_000 # Startguthaben fÃ¼r neue Spieler

LOG_COLOR = 0x00BFFF
MOD_COLOR = 0xFF0000

DISCORD_INVITE_RE = re.compile(
    r'(https?://)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com/invite|discord\.com/invite)/\S+',
    re.IGNORECASE
)
URL_RE = re.compile(r'https?://\S+', re.IGNORECASE)

VULGÃ„RE_WÃ–RTER = [
    "fotze", "wichser", "hurensohn", "arschloch", "fick", "ficken",
    "neger", "nigger", "wichsen", "schlampe", "nutte", "hure",
    "wixer", "drecksau", "scheisskopf", "pisser", "dreckssack",
    "mongo", "spast", "vollidiot", "schwachkopf", "dreckskerl",
    "mistkerl", "penner", "hurenkind", "dummficker", "scheiÃŸ",
]

spam_tracker = {}
spam_warned = set()
ticket_data = {}
counting_state = {"count": 0, "last_user_id": None}
counting_handled = set() # verhindert doppelte Verarbeitung

FUNKTIONEN = {
    "Discord Link Schutz": Wahr,
    "Linkfilter (Memes)": Wahr,
    "VulgÃ¤re WÃ¶rter Filter": True,
    "Spamschutz": Stimmt,
    "Nachrichtenlog": Wahr,
    "Bearbeitungslog": True,
    "Rollenlog": Wahr,
    "Mitgliederprotokoll": Wahr,
    "Mitgliedslogbuch + Einladungen": Wahr,
    "Bot Kick": Wahr,
    "Fehlerprotokollierung": Ja,
    "Rollen-Entfernung (Timeout)": True,
    "Ticketsystem": Wahr,
    "ZÃ¤hl-Kanal": Wahr,
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
    for g in guilds_to_check:
        if not g:
            continue
        log_ch = g.get_channel(BOT_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title=f"\u26a0ï¸ Bot Fehler â€” {title}",
                description=f"```{error_text[:1900]}```",
                Farbe=MOD_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            try:
                await log_ch.send(embed=embed)
            except:
                pass
            brechen

async def send_bot_status():
    for Gilde in bot.guilds:
        log_ch = guild.get_channel(BOT_LOG_CHANNEL_ID)
        if not log_ch:
            continue
        desc = ""
        for Feature, Status in FEATURES.items():
            Emoji = "\U0001f7e2" wenn Status, sonst "\U0001f534"
            Status = "Online", falls Status "Online", ansonsten "Offline"
            desc += f"{emoji} **{feature}** â€” {state}\n"
        embed = discord.Embed(
            title="\U0001f916 Bot Status â€” Alle Funktionen",
            Beschreibung=desc,
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        try:
            await log_ch.send(embed=embed)
        except:
            pass

async def apply_timeout_restrictions(member, guild, duration_h=None, duration_m=None, reason="RegelverstoÃŸ"):
    timeout_ok = False
    if duration_h:
        timeout_until = datetime.now(timezone.utc) + timedelta(hours=duration_h)
    anders:
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
            Gilde
        )
    roles_removed = []
    try:
        zu entfernende Rollen = [
            r for r in member.roles
            if r != guild.default_role and not r.managed
        ]
        if Rollen_zu_entfernen:
            await member.remove_roles(*roles_to_remove, reason=f"Timeout: {reason}")
            roles_removed = roles_to_remove
    except Exception as e:
        wait log_bot_error("Rollen entfernen fehlgeschlagen", str(e), guild)
    return timeout_ok, roles_removed

# \u2500\u2500 Wirtschaftshelfer \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
    if user_id not in Daten:
        data[uid] = {
            "Bargeld": 0,
            "Bank": 0,
            "last_wage": Keine,
            "tÃ¤gliche Einzahlung": 0,
            "daily_withdraw": 0,
            "tÃ¤gliche_Ãœberweisungen": 0,
            "daily_reset": Keine,
            "Inventar": [],
            "custom_limit": Keine,
        }
    return data[uid]

def reset_daily_if_needed(user_data):
    jetzt = datetime.now(timezone.utc)
    if user_data.get("daily_reset") is None:
        user_data["daily_reset"] = now.isoformat()
        return
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
    return []

def save_shop(items):
    with open(SHOP_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def has_citizen_or_wage(member):
    role_ids = [r.id for r in member.roles]
    return (
        CITIZEN_ROLE_ID in role_ids
        oder ADMIN_ROLE_ID in role_ids
        oder any(r in role_ids for r in WAGE_ROLES)
    )

def is_team(member):
    return any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in member.roles)

# \u2500\u2500 Warnhelfer \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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

# \u2500\u2500 Helfer fÃ¼r versteckte GegenstÃ¤nde \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def load_hidden_items():
    if HIDDEN_ITEMS_FILE.exists():
        with open(HIDDEN_ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_hidden_items(data):
    with open(HIDDEN_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# \u2500\u2500 Money Log Helper \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def log_money_action(guild: discord.Guild, title: str, description: str):
    ch = guild.get_channel(MONEY_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title=f"\U0001f4b5 {title}",
            Beschreibung=Beschreibung,
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        try:
            await ch.send(embed=embed)
        except:
            pass

# \u2500\u2500 Betrag Autocomplete (1Kâ€“10M, Freitext erlaubt) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

BETRAG_SUGGESTIONS = [
    1.000, 5.000, 10.000, 25.000, 50.000
    100.000, 250.000, 500.000, 1.000.000
    2_000_000, 5_000_000, 10_000_000
]

async def betrag_autocomplete(
    Interaktion: discord.Interaktion,
    aktuell: str
) -> list[app_commands.Choice[int]]:
    AuswahlmÃ¶glichkeiten = []
    clean = current.replace(".", "").replace(",", "").strip()
    for val in BETRAG_SUGGESTIONS:
        label = f"{val:,} \U0001f4b5".replace(",", ".")
        if clean == "" or clean in str(val) or clean.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=val))
    return choices[:25]

# \u2500\u2500 Shop-Artikel-AutovervollstÃ¤ndigung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def shop_item_autocomplete(
    Interaktion: discord.Interaktion,
    aktuell: str
) -> list[app_commands.Choice[str]]:
    items = load_shop()
    current_lower = current.lower()
    AuswahlmÃ¶glichkeiten = []
    for Artikel in Artikeln:
        Name = Artikel["Name"]
        if current_lower == "" or current_lower in name.lower():
            choices.append(app_commands.Choice(name=name, value=name))
    return choices[:25]

# \u2500\u2500 Inventar-Item Autocomplete \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def inventory_item_autocomplete(
    Interaktion: discord.Interaktion,
    aktuell: str
) -> list[app_commands.Choice[str]]:
    from collections import Counter
    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    inventory = user_data.get("inventory", [])
    Anzahl = ZÃ¤hler(Inventar)
    current_lower = current.lower()
    AuswahlmÃ¶glichkeiten = []
    for item_name, count in counts.items():
        label = f"{item_name} (Ã—{count})"
        if current_lower == "" or current_lower in item_name.lower():
            choices.append(app_commands.Choice(name=label, value=item_name))
    return choices[:25]

# \u2500\u2500 BEHEBUNG 2: Normalisierungsfunktion fÃ¼r Item-Namen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Entfernt Emojis, Pipe-Zeichen und normalisierte Leerzeichen,
# Damit zB "Handy" das Item "\U0001f4f1| Handy" sicher findet.

def normalize_item_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[\|\-\_]+', ' ', name)
    name = ''.join(c for c in name if c.isalnum() or c.isspace())
    return re.sub(r'\s+', ' ', name).strip()

# \u2500\u2500 Versteck-Button (persistent) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class VersteckRetrieveView(discord.ui.View):
    def __init__(self, item_id: str, owner_id: int):
        super().__init__(timeout=None)
        self.item_id = item_id
        self.owner_id = owner_id
        btn = discord.ui.Button(
            label="\U0001f4e6 Aus Versteck holen",
            style=discord.ButtonStyle.green,
            custom_id=f"retrieve_{item_id}_{owner_id}"
        )
        btn.callback = self.retrieve_callback
        self.add_item(btn)

    async def retrieve_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "\u274c Nur derjenige, der das Item versteckt hat, kann es herausnehmen.",
                ephemeral=True
            )
            return
        versteckt = load_hidden_items()
        Eintrag = next((h for h in versteckt, falls h["id"] == self.item_id), None)
        if kein Eintrag:
            wait interaction.response.send_message("\u274c Item wurde bereits geborgen or existiert not mehr.", ephemeral=True)
            return

        # Artikel zurÃ¼ckgesendet Inventar
        eco = load_economy()
        user_data = get_user(eco, interaction.user.id)
        user_data.setdefault("inventory", []).append(entry["item"])
        save_economy(eco)

        # Verstecktes Element entfernen
        hidden = [h for h in hidden if h["id"] != self.item_id]
        save_hidden_items(hidden)

        # SchaltflÃ¤che deaktivieren
        for Kind in Selbst.Kinder:
            Kind.deaktiviert = Wahr
        try:
            await interaction.message.edit(view=self)
        except:
            pass

        await interaction.response.send_message(
            f"\u2705 **{entry['item']}** wurde aus dem Versteck (**{entry['location']}**) geholt.",
            ephemeral=True
        )

# \u2500\u2500 Ticketsystem \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

TICKET_TYPE_NAMES = {
    "Support": "Support",
    "highteam": "Highteam Ticket",
    "fraktion": "Fraktionsbewerbung",
    "beschwerde": "Beschwerde-Ticket",
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
    Gilde = interaction.guild
    Mitglied = interaction.Benutzer

    for ch in guild.text_channels:
        data = ticket_data.get(ch.id)
        if data and data["creator_id"] == member.id:
            await interaction.response.send_message(
                "\u274c Du hast bereits ein offenes Ticket!", ephemeral=True
            )
            return

    type_name = TICKET_TYPE_NAMES.get(ticket_type, ticket_type)
    category_id = TICKET_TYPE_CATEGORIES.get(ticket_type, TICKET_CATEGORY_DEFAULT)
    Kategorie = Gilde.get_channel(Kategorie_ID)
    admin_role = guild.get_role(ADMIN_ROLE_ID)
    mod_role = guild.get_role(MOD_ROLE_ID)

    Ãœberschreibt = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        Mitglied: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            manage_channels=True, manage_messages=True
        ),
    }
    if Administratorrolle:
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

    try:
        Kanal = await guild.create_text_channel(
            Name=Kanalname,
            Kategorie=Kategorie,
            Ã¼berschreibt=Ã¼berschreibt,
            topic=f"Ticket von {member} ({member.id}) | Typ: {type_name}"
        )
    except Exception as e:
        await interaction.response.send_message(
            "\u274c Ticket konnte not erstellt werden.", ephemeral=True
        )
        wait log_bot_error("Ticket erstellen fehlgeschlagen", str(e), guild)
        return

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
    if Administratorrolle:
        team_mentions += admin_role.mention + " "
    if mod_role:
        team_mentions += mod_role.mention

    welcome_embed = discord.Embed(
        title=f"\U0001f39f {type_name}",
        Beschreibung=(
            f"Willkommen {member.mention}!\n\n"
            f"Dein Ticket wurde erfolgreich erstellt. Das Team wird sich schnellstmÃ¶glich um dein Anliegen kÃ¼mmern.\n\n"
            f"**Ticket-Typ:** {type_name}\n"
            f"**Erstellt von:** {member.mention}\n"
            f"**Erstellt am:** <t:{int(datetime.now(timezone.utc).timestamp())}:F>"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    Welcome_embed.set_footer(text="Nur Teammitglieder kÃ¶nnen das Ticket schlieÃŸen")

    action_view = TicketActionView()
    await channel.send(content=team_mentions, embed=welcome_embed, view=action_view)

    await interaction.response.send_message(
        f"\u2705 Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True
    )

    log_ch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="\U0001f4c2 Ticket GeÃ¶ffnet",
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
                emoji="\U0001f39f",
                Wert="UnterstÃ¼tzung",
                description="Allgemeiner Support"
            ),
            discord.SelectOption(
                label="Highteam-Ticket",
                emoji="\U0001f39f",
                Wert="highteam",
                description="Direktor Kontakt zum Highteam"
            ),
            discord.SelectOption(
                label="Fraktionen Bewerbung",
                emoji="\U0001f39f",
                Wert="Fraktion",
                description="Bewerbung fÃ¼r eine Fraktion"
            ),
            discord.SelectOption(
                label="Beschwerde Ticket",
                emoji="\U0001f39f",
                Wert="beschwerde",
                description="Beschwerde einreichen"
            ),
            discord.SelectOption(
                label="Fehlerbericht",
                emoji="\U0001f39f",
                Wert="Bug",
                description="Fehler or Bug melden"
            ),
        ]
        super().__init__(
            placeholder="\U0001f39f WÃ¤hle eine Ticket-Art aus...",
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
            placeholder="Person auswÃ¤hlen...",
            custom_id="ticket_assign_user_select",
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        Benutzer = self.values[0]
        Kanal = interaction.channel
        try:
            await channel.set_permissions(
                Benutzer,
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        except Exception as e:
            await interaction.response.send_message(
                "\u274c Berechtigung konnte not gesetzt werden.", ephemeral=True
            )
            wait log_bot_error("Ticket-Zuweisung fehlgeschlagen", str(e), interaction.guild)
            return

        if channel.id in ticket_data:
            ticket_data[channel.id]["handler"] = str(user)
            ticket_data[channel.id]["handler_id"] = user.id

        assign_embed = discord.Embed(
            Beschreibung=(
                f"\U0001f464 {user.mention} wurde dem Ticket zugewiesen.\n"
                f"**Zugewiesen von:** {interaction.user.mention}"
            ),
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
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
        label="Ticket schlieÃŸen",
        style=discord.ButtonStyle.red,
        emoji="\U0001f512",
        custom_id="ticket_close_btn"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "\u274c Nur Teammitglieder kÃ¶nnen Tickets schlieÃŸen.", ephemeral=True
            )
            return

        Kanal = interaction.channel
        data = ticket_data.get(channel.id)
        if not data:
            await interaction.response.send_message(
                "\u274c Ticket-Daten not gefunden.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        ticket_data[channel.id]["handler"] = str(interaction.user)
        ticket_data[channel.id]["handler_id"] = interaction.user.id

        closing_embed = discord.Embed(
            title="\U0001f512 Ticket wird geschlossen...",
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
                        transcript_lines.append(f" â†³ {short}")
        except:
            transcript_lines.append("(Transkript konnte not vollstÃ¤ndig geladen werden)")

        transcript_text = "\n".join(transcript_lines)
        transcript_file = discord.File(
            fp=io.BytesIO(transcript_text.encode("utf-8")),
            filename=f"transkript-{channel.name}.txt"
        )

        log_ch = interaction.guild.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            closed_embed = discord.Embed(
                title="\U0001f4c1 Ticket geschlossen",
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
        if Ersteller:
            try:
                dm_embed = discord.Embed(
                    title="\U0001f39f Dein Ticket wurde geschlossen",
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
            except:
                pass

        ticket_data.pop(channel.id, None)
        await asyncio.sleep(3)
        try:
            Warten Sie aufchannel.delete(reason="Ticket geschlossen")
        except Exception as e:
            wait log_bot_error("Ticket lÃ¶schen fehlgeschlagen", str(e), interaction.guild)

    @discord.ui.button(
        label="Person empf",
        style=discord.ButtonStyle.blurple,
        emoji="\U0001f464",
        custom_id="ticket_assign_btn"
    )
    async def assign_person(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "\u274c Nur Teammitglieder kÃ¶nnen Personen zuweisen.", ephemeral=True
            )
            return
        assign_view = AssignView()
        await interaction.response.send_message(
            "WÃ¤hlen Sie eine Person aus die dem Ticket zugewiesen werden soll:",
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
        if selbstbewertet:
            await interaction.response.send_message(
                "Du hast dieses Ticket bereits bewertet.", ephemeral=True
            )
            return
        Selbstbewertung = Wahr

        star_display = "â­" * Sterne + "\u2606" * (5 - Sterne)

        thank_embed = discord.Embed(
            title="\U0001f499 Danke fÃ¼r deine Bewertung!",
            Beschreibung=(
                f"Du hast **{star_display}** ({stars}/5) gegeben.\n\n"
                f"Vielen Dank fÃ¼r dein Feedback! Wir arbeiten stets daran, unseren Support zu verbessern. "
                f"Wir hoffen, dass dein Anliegen zu deiner Zufriedenheit gelÃ¶st wurde."
            ),
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await interaction.response.send_message(embed=thank_embed)

        log_ch = self.guild_ref.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            rating_embed = discord.Embed(
                title="â­ Ticketbewertung",
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

        for Element in self.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self)
        except:
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

def guild_member_bot(guild: discord.Guild):
    return guild.me

# \u2500\u2500 Veranstaltungen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.event

  # ==============================================================================
  # HANDY SYSTEM
  # ==============================================================================
  import random as _random

  _LA_AREA_CODES = ["213", "310", "323", "424", "562", "626", "747", "818"]

  def _load_phone_data():
      if PHONE_FILE.exists():
          with open(PHONE_FILE, "r", encoding="utf-8") as f:
              return json.load(f)
      return {}

  def _save_phone_data(data):
      with open(PHONE_FILE, "w", encoding="utf-8") as f:
          json.dump(data, f, indent=2, ensure_ascii=False)

  def _get_or_create_phone(user_id: int) -> str:
      data = _load_phone_data()
      uid = str(user_id)
      if uid not in data:
          area = _random.choice(_LA_AREA_CODES)
          data[uid] = f"({area}) {_random.randint(200,999)}-{_random.randint(1000,9999)}"
          _save_phone_data(data)
      return data[uid]

  def _has_handy(member: discord.Member) -> bool:
      eco = load_economy()
      ud = get_user(eco, member.id)
      return any("handy" in item.lower() for item in ud.get("inventory", []))

  async def grant_handy_channel_access(guild: discord.Guild, member: discord.Member):
      channel = guild.get_channel(HANDY_CHANNEL_ID)
      if not channel:
          return
      try:
          await channel.set_permissions(member, view_channel=True, read_message_history=True, send_messages=False)
      except Exception:
          pass

  async def _send_dispatch(interaction: discord.Interaction, dienst: str, role_id: int):
      guild = interaction.guild
      role = guild.get_role(role_id)
      if not role:
          await interaction.response.send_message("\u274c Rolle not gefunden.", ephemeral=True)
          return
      sender = interaction.user
      dm_embed = discord.Embed(
          title="U0001f6a8 Dispatch U0001f6a8",
          description=(
              f"Ein Bewohner hat einen Notruf abgesendet!\n\n"
              f"**Dienst:** {dienst}\n"
              f"**Gesendet von:** {sender.display_name} ({sender.mention})"
          ),
          color=0xFF0000,
          timestamp=datetime.now(timezone.utc)
      )
      dm_embed.set_footer(text=f"Cryptik Roleplay â€” {dienst} Dispatch")
      sent = 0
      failed = 0
      for m in role.members:
          try:
              await m.send(embed=dm_embed)
              sent += 1
          except Exception:
              failed += 1
      if IC_CHAT_CHANNEL_ID:
          ic_ch = guild.get_channel(IC_CHAT_CHANNEL_ID)
          if ic_ch:
              try:
                  await ic_ch.send(
                      content=role.mention,
                      embed=discord.Embed(
                          description=f"U0001f6a8 **{dienst} Dispatch** | {sender.mention} benÃ¶tigt Hilfe!",
                          color=0xFF0000
                      )
                  )
              except Exception:
                  pass
      confirm = discord.Embed(
          title="\u2705 Dispatch abgesendet",
          description=(
              f"Dein **{dienst}**-Dispatch wurde versendet.\n"
              f"**{sent}** Mitglieder benachrichtigt."
              + (f"\n*({failed} per DM not erreichbar)*" if failed else "")
          ),
          color=0xFF0000
      )
      await interaction.response.send_message(embed=confirm, ephemeral=True)

  class HandyView(discord.ui.View):
      def __init__(self):
          super().__init__(timeout=None)

      @discord.ui.button(label="U0001f6a8 | Dispatch MD", style=discord.ButtonStyle.red, custom_id="handy_dispatch_md", row=0)
      async def dispatch_md(self, interaction: discord.Interaction, button: discord.ui.Button):
          if not _has_handy(interaction.user):
              await interaction.response.send_message("\u274c Du besitzt kein Handy.", ephemeral=True)
              return
          await _send_dispatch(interaction, "MD", DISPATCH_MD_ROLE_ID)

      @discord.ui.button(label="U0001f6a8 | Dispatch PD", style=discord.ButtonStyle.red, custom_id="handy_dispatch_pd", row=1)
      async def dispatch_pd(self, interaction: discord.Interaction, button: discord.ui.Button):
          if not _has_handy(interaction.user):
              await interaction.response.send_message("\u274c Du besitzt kein Handy.", ephemeral=True)
              return
          await _send_dispatch(interaction, "PD", DISPATCH_PD_ROLE_ID)

      @discord.ui.button(label="U0001f6a8 | Dispatch ADAC", style=discord.ButtonStyle.red, custom_id="handy_dispatch_adac", row=2)
      async def dispatch_adac(self, interaction: discord.Interaction, button: discord.ui.Button):
          if not _has_handy(interaction.user):
              await interaction.response.send_message("\u274c Du besitzt kein Handy.", ephemeral=True)
              return
          await _send_dispatch(interaction, "ADAC", DISPATCH_ADAC_ROLE_ID)

      @discord.ui.button(label="U0001f4f1 | Handy Nummer Einsehen", style=discord.ButtonStyle.blurple, custom_id="handy_nummer", row=3)
      async def handy_nummer(self, interaction: discord.Interaction, button: discord.ui.Button):
          if not _has_handy(interaction.user):
              await interaction.response.send_message("\u274c Du besitzt kein Handy.", ephemeral=True)
              return
          nummer = _get_or_create_phone(interaction.user.id)
          embed = discord.Embed(
              title="U0001f4f1 Deine Handy-Nummer",
              description=f"**{nummer}**\n\nU0001f4cd *Los Angeles, Kalifornien, USA*\n\nDiese Nummer bleibt immer gleich.",
              color=0x5865F2
          )
          await interaction.response.send_message(embed=embed, ephemeral=True)

      @discord.ui.button(label="U0001f4f1 | Instagram", style=discord.ButtonStyle.blurple, custom_id="handy_instagram", row=4)
      async def instagram(self, interaction: discord.Interaction, button: discord.ui.Button):
          if not _has_handy(interaction.user):
              await interaction.response.send_message("\u274c Du besitzt kein Handy.", ephemeral=True)
              return
          role = interaction.guild.get_role(INSTAGRAM_ROLE_ID)
          if not role:
              await interaction.response.send_message("\u274c Rolle not gefunden.", ephemeral=True)
              return
          if role in interaction.user.roles:
              await interaction.user.remove_roles(role)
              await interaction.response.send_message("U0001f4f1 App Erfolgreich Deinstalliert", ephemeral=True)
          else:
              await interaction.user.add_roles(role)
              await interaction.response.send_message("U0001f4f1 App Erfolgreich Installiert", ephemeral=True)

      @discord.ui.button(label="U0001f4f1 | Parship", style=discord.ButtonStyle.blurple, custom_id="handy_parship", row=4)
      async def parship(self, interaction: discord.Interaction, button: discord.ui.Button):
          if not _has_handy(interaction.user):
              await interaction.response.send_message("\u274c Du besitzt kein Handy.", ephemeral=True)
              return
          role = interaction.guild.get_role(PARSHIP_ROLE_ID)
          if not role:
              await interaction.response.send_message("\u274c Rolle not gefunden.", ephemeral=True)
              return
          if role in interaction.user.roles:
              await interaction.user.remove_roles(role)
              await interaction.response.send_message("U0001f4f1 App Erfolgreich Deinstalliert", ephemeral=True)
          else:
              await interaction.user.add_roles(role)
              await interaction.response.send_message("U0001f4f1 App Erfolgreich Installiert", ephemeral=True)

  async def auto_handy_setup():
      for guild in bot.guilds:
          channel = guild.get_channel(HANDY_CHANNEL_ID)
          if not channel:
              continue
          already_posted = False
          try:
              async for msg in channel.history(limit=30):
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
              continue
          embed = discord.Embed(
              title="U0001f4f1 Handy Einstellungen",
              description=(
                  "Willkommen in deinen **Handy-Einstellungen**!\n\n"
                  "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
                  "U0001f6a8 **Dispatch MD** â€” Notruf an den Medizinischen Dienst\n"
                  "U0001f6a8 **Dispatch PD** â€” Notruf an die Polizei\n"
                  "U0001f6a8 **Dispatch ADAC** â€” Pannenhilfe anfordern\n"
                  "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
                  "U0001f4f1 **Handy Nummer** â€” Deine persÃ¶nliche LA-Nummer\n"
                  "U0001f4f1 **Instagram** â€” App installieren / deinstallieren\n"
                  "U0001f4f1 **Parship** â€” App installieren / deinstallieren"
              ),
              color=0x00BFFF,
              timestamp=datetime.now(timezone.utc)
          )
          embed.set_footer(text="Cryptik Roleplay â€” Handy System")
          try:
              await channel.send(embed=embed, view=HandyView())
          except Exception as e:
              print(f"auto_handy_setup fehlgeschlagen: {e}")

  
async def on_ready():
    global bot_start_time, invite_cache
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")

    bot.add_view(TicketSelectView())
    bot.add_view(TicketActionView())

    # Versteck-Buttons nach Neustart wieder registrieren
    for jeden Eintrag in load_hidden_items():
        bot.add_view(VersteckRetrieveView(entry["id"], entry["owner_id"]))

    for Gilde in bot.guilds:
        try:
            Einladungen = await guild.fetch_invites()
            invite_cache[guild.id] = {inv.code: inv for inv in invites}
        except:
            pass

    await auto_ticket_setup()
    await auto_lohnliste_setup()
    await auto_einreise_setup()
    await auto_handy_setup()
    bot.add_view(HandyView())
    bot.add_view(EinreiseView())
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        # Guild-Commands registrieren (sofort aktiv, keine globale Duplikate)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Slash-Befehle synchronisiert (Gilde): {len(synced)}")
        # Alle globalen Befehle von Discord entfernen
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("Globale Befehle gelÃ¶scht")
    except Exception as e:
        print(f"Slash Command sync fehlgeschlagen: {e}")

async def auto_ticket_setup():
    for Gilde in bot.guilds:
        Kanal = guild.get_channel(TICKET_SETUP_CHANNEL_ID)
        if not Kanal:
            continue
        bereits_gepostet = False
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Ticket erstellen" in emb.title:
                            bereits_gepostet = Wahr
                            brechen
                if bereits gepostet:
                    brechen
        except:
            pass
        if bereits gepostet:
            print(f"Ticket-Embed bereits vorhanden in #{channel.name} â€” kein erneutes Posten.")
            continue
        embed = discord.Embed(
            title="\U0001f39f Support â€” Ticket erstellen",
            Beschreibung=(
                "BenÃ¶tigst du Hilfe or mÃ¶chtest einen Betroffenen melden?\n\n"
                "WÃ¤hlen Sie unten im MenÃ¼ die passende Ticket-Art aus.\n"
                "Unser Team wird sich schnellstmÃ¶glich um dich kÃ¼mmern.\n\n"
                "**VerfÃ¼gbare Ticket-Arten:**\n"
                "\U0001f39f **Support** â€” Allgemeiner Support\n"
                "\U0001f39f **Highteam Ticket** â€” Direkter Kontakt zum Highteam\n"
                "\U0001f39f **Fraktions Bewerbung** â€” Bewirb dich fÃ¼r eine Fraktion\n"
                "\U0001f39f **Beschwerde Ticket** â€” Beschwerde einreichen\n"
                "\U0001f39f **Bug Report** â€“ Fehler or Bug melden"
            ),
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Cryptik Roleplay â€” Support System")
        try:
            await channel.send(embed=embed, view=TicketSelectView())
            print(f"Ticket-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            wait log_bot_error("auto_ticket_setup fehlgeschlagen", str(e), guild)

async def auto_lohnliste_setup():
    for Gilde in bot.guilds:
        Kanal = guild.get_channel(LOHNLISTE_CHANNEL_ID)
        if not Kanal:
            continue
        bereits_gepostet = False
        try:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Lohnliste" in emb.title:
                            bereits_gepostet = Wahr
                            brechen
                if bereits gepostet:
                    brechen
        except:
            pass
        if bereits gepostet:
            print(f"Lohnliste bereits vorhanden in #{channel.name} â€” kein erneutes Posten.")
            continue
        desc = (
            f"<@&1490855796932739093>\n**1.500 \U0001f4b5 StÃ¼ndlich**\n\n"
            f"<@&1490855789844234310>\n**2.500 \U0001f4b5 StÃ¼ndlich**\n\n"
            f"<@&1490855790913785886>\n**3.500 \U0001f4b5 StÃ¼ndlich**\n\n"
            f"<@&1490855791953973421>\n**4.500 \U0001f4b5 StÃ¼ndlich**\n\n"
            f"<@&1490855792671461478>\n**5.500 \U0001f4b5 StÃ¼ndlich**\n\n"
            f"<@&1490855793694871595>\n**6.500 \U0001f4b5 StÃ¼ndlich**\n\n"
            f"<@&1490855795360006246>\n**1.200 \U0001f4b5 StÃ¼ndlich** *(Zusatzlohn)*"
        )
        embed = discord.Embed(
            title="\U0001f4b5 Lohnliste \U0001f4b5",
            Beschreibung=desc,
            Farbe=LOG_COLOR
        )
        try:
            await channel.send(embed=embed)
            print(f"Lohnliste automatisch gepostet in #{channel.name}")
        except Exception as e:
            wait log_bot_error("auto_lohnliste_setup fehlgeschlagen", str(e), guild)

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
    Mitglied = message.author

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
    if not is_mod_or_admin(member) and contains_vulg(message.content):
        await handle_vulgar_message(message)
        return

    await check_spam(message)
    await bot.process_commands(message)

async def handle_counting(message):
    if message.id in counting_handled:
        return
    counting_handled.add(message.id)
    if len(counting_handled) > 200:
        Ã¤lteste = Liste(counting_handled)[:100]
        for Mitte in Ã¤lteste:
            counting_handled.discard(mid)

    content = message.content.strip()
    try:
        Zahl = int(Inhalt)
    except ValueError:
        try:
            await message.delete()
        except:
            pass
        try:
            await message.channel.send(
                f"\u274c {message.author.mention} Nur Zahlen sind hier erlaubt! Der ZÃ¤hler geht weiter bei **{counting_state['count'] + 1}**.",
                delete_after=5
            )
        except:
            pass
        return

    erwartet = ZÃ¤hlzustand["Anzahl"] + 1

    if counting_state["last_user_id"] == message.author.id:
        try:
            await message.delete()
        except:
            pass
        try:
            await message.channel.send(
                f"\u274c {message.author.mention} Du kannst not zweimal hintereinander zÃ¤hlen! Der ZÃ¤hler steht bei **{counting_state['count']}**.",
                delete_after=5
            )
        except:
            pass
        return

    if die Zahl dem Erwartungswert entspricht:
        counting_state["count"] = Zahl
        counting_state["last_user_id"] = message.author.id
        await message.add_reaction("\u2705")
    anders:
        counting_state["count"] = 0
        counting_state["last_user_id"] = None
        try:
            await message.delete()
        except:
            pass
        try:
            await message.channel.send(
                f"\u274c {message.author.mention} Falsche Zahl! Erwartet wurde **{expected}**, nicht **{number}**.\n"
                f"Der ZÃ¤hler wurde zurÃ¼ckgesetzt. Fangt wieder bei **1** an!",
                delete_after=8
            )
        except:
            pass

async def handle_discord_invite(message):
    Mitglied = message.author
    Gilde = message.guild
    try:
        await message.delete()
    except Exception as e:
        wait log_bot_error("Nachricht lÃ¶schen (Discord Link)", str(e), guild)
    timeout_ok, roles_removed = await apply_timeout_restrictions(
        Mitglied, Gilde, Dauer_h=300, Grund="Fremden Discord-Link gesendet"
    )
    try:
        embed = discord.Embed(
            Beschreibung=(
                "> Du hast gegen unsere Server Regeln verstoÃŸen\n\n"
                "> Bitte wende dich an den Support"
            ),
            Farbe=MOD_COLOR
        )
        await member.send(content=member.mention, embed=embed)
    except:
        pass
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        timeout_status = "\u2705 Timeout erteilt (300h)" if timeout_ok else "\u274c Timeout fehlgeschlagen â€” Berechtigung prÃ¼fen!"
        rollen_status = f"Entfernt: {', '.join(r.name for r in Roles_removed)}" if Roles_removed else "Keine Rollen entfernt"
        embed = discord.Embed(
            title="\U0001f528 Moderation â€” Timeout",
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
    try:
        await message.delete()
    except:
        pass
    try:
        await message.channel.send(
            f"{message.author.mention} Bitte senden Sie Links ausschlieÃŸlich im <#{MEMES_CHANNEL_ID}> Kanal",
            delete_after=6
        )
    except:
        pass

async def handle_vulgar_message(message):
    try:
        await message.delete()
    except:
        pass
    try:
        embed = discord.Embed(
            Beschreibung=(
                "> **Verwarnung:** Du hast einen vulgÃ¤ren Ausdruck verwendet.\n\n"
                "> Bitte beachte unsere Serverregeln. Bei weiteren VerstÃ¶ÃŸen folgen Konsequenzen."
            ),
            Farbe=MOD_COLOR
        )
        await message.author.send(content=message.author.mention, embed=embed)
    except:
        pass
    log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="\U0001f528 Moderation â€” VulgÃ¤re Sprache",
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
    user_id = message.author.id
    jetzt = datetime.now(timezone.utc)
    if user_id not in spam_tracker:
        spam_tracker[user_id] = []
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if (now - t).total_seconds() < 5]
    spam_tracker[user_id].append(now)
    Anzahl = len(spam_tracker[user_id])
    if count >= 5 and user_id in spam_warned:
        spam_tracker[user_id] = []
        spam_warned.discard(user_id)
        try:
            await message.channel.purge(limit=50, check=lambda m: m.author.id == user_id)
        except:
            pass
        timeout_ok, roles_removed = await apply_timeout_restrictions(
            message.author, message.guild, duration_m=10, reason="Wiederholtes Spammen"
        )
        try:
            embed = discord.Embed(
                description="> Du wurdest aufgrund von wiederholtem Spammen fÃ¼r **10 Minuten** stummgeschaltet.",
                Farbe=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        except:
            pass
        log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            timeout_status = "\u2705 Timeout erteilt (10min)" if timeout_ok else "\u274c Timeout fehlgeschlagen â€” Berechtigung prÃ¼fen!"
            rollen_status = f"Entfernt: {', '.join(r.name for r in Roles_removed)}" if Roles_removed else "Keine Rollen entfernt"
            embed = discord.Embed(
                title="\U0001f528 Moderation â€” Timeout (Spam)",
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
        try:
            await message.channel.purge(limit=50, check=lambda m: m.author.id == user_id)
        except:
            pass
        try:
            embed = discord.Embed(
                Beschreibung=(
                    "> **Verwarnung:** Bitte vermeide es zu spammen.\n\n"
                    "> Bei Wiederholung erhÃ¤ltst du einen 10 Minuten Timeout."
                ),
                Farbe=MOD_COLOR
            )
            await message.author.send(content=message.author.mention, embed=embed)
        except:
            pass

@bot.event
async def on_message_delete(message):
    if not message.guild or message.author.bot:
        return
    log_ch = message.guild.get_channel(MESSAGE_LOG_CHANNEL_ID)
    if not log_ch:
        return
    embed = discord.Embed(
        title="\U0001f5d1ï¸Nachricht gelÃ¶scht",
        Beschreibung=(
            f"**Benutzer:** {message.author.mention} (`{message.author}`)\n"
            f"**Kanal:** {message.channel.me ntion}\n"
            f"**Inhalt:** {message.content[:500] if message.content else '*Kein Text*'}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
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
        title="\u270fï¸ Nachricht bearbeitet",
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
        return
    Gilde = after.guild
    log_ch = guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if not log_ch:
        return
    hinzugefÃ¼gt = [r for r in after.roles falls r not in before.roles]
    entfernt = [r for r in vorher.Rollen falls r not in nachher.Rollen]
    if not hinzugefÃ¼gt and not entfernt:
        return
    description = f"**Benutzer:** {after.mention} (`{after}`)\n"
    if hinzugefÃ¼gt:
        description += f"**HinzugefÃ¼gt:** {', '.join(r.mention for r in added)}\n"
    if entfernt:
        description += f"**Entfernt:** {', '.join(r.mention for r in removed)}\n"
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == after.id:
                Beschreibung += f"**GeÃ¤ndert von:** {entry.user.mention} (`{entry.user}`)"
                brechen
    except:
        pass
    embed = discord.Embed(
        title="\U0001f3ad Rollen geÃ¤ndert",
        Beschreibung=Beschreibung,
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if not log_ch:
        return
    reason = "Kein Grund angegeben"
    Banner = Keine
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                Grund = Eintrag.Grund or Grund
                Banner = Eintrag.Benutzer
                brechen
    except:
        pass
    description = f"**Benutzer:** {user.mention} (`{user}`)\n**Grund:** {reason}"
    Banner:
        description += f"\n**Gebannt von:** {banner.mention} (`{banner}`)"
    embed = discord.Embed(
        title="\U0001f528 Mitglied gegeben",
        Beschreibung=Beschreibung,
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)

@bot.event
async def on_member_remove(member):
    Gilde = member.guild
    log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if not log_ch:
        return
    await asyncio.sleep(1)
    Aktion = "verlassen"
    mod = None
    Grund = Keiner
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                Aktion = "gekickt"
                mod = entry.user
                reason = enter.reason oder "Kein Grund angegeben"
                brechen
    except:
        pass
    try:
        async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.ban):
            if entry.target.id == member.id:
                return
    except:
        pass
    description = f"**Benutzer:** {member.mention} (`{member}`)\n**Aktion:** {action}"
    if Mod:
        description += f"\n**Von:** {mod.mention} (`{mod}`)"
    Grund:
        Beschreibung += f"\n**Grund:** {Grund}"
    title = "\U0001f462 Mitglied gekickt" if action == "gekickt" else "\U0001f6aa Mitglied hat den Server verlassen"
    embed = discord.Embed(
        Titel=Titel,
        Beschreibung=Beschreibung,
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await log_ch.send(embed=embed)

    goodbye_ch = guild.get_channel(GOODBYE_CHANNEL_ID)
    if goodbye_ch:
        try:
            g_embed = discord.Embed(
                title="\U0001f4e4 Mitglied hat den Server verlassen",
                Beschreibung=(
                    f"**{member.mention}** hat uns verlassen.\n\n"
                    f"Wir wÃ¼nschen dir alles Gute!\n"
                    f"Du bist jederzeit herzlich willkommen zurÃ¼ck."
                ),
                Farbe=LOG_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            g_embed.set_thumbnail(url=member.display_avatar.url)
            g_embed.add_field(name="Mitglied", value=str(member), inline=True)
            g_embed.add_field(name="ID", value=str(member.id), inline=True)
            g_embed.set_footer(text=f"Noch {guild.member_count} Mitglieder")
            await goodbye_ch.send(embed=g_embed)
        except:
            pass

@bot.event
async def on_invite_create(invite):
    Gilde = invite.guild
    if guild.id not in invite_cache:
        invite_cache[guild.id] = {}
    invite_cache[guild.id][invite.code] = invite

@bot.event
async def on_invite_delete(invite):
    Gilde = invite.guild
    if guild.id in invite_cache and invite.code in invite_cache[guild.id]:
        del invite_cache[guild.id][invite.code]

@bot.event
async def on_member_join(member):
    Gilde = member.guild

    if member.bot:
        try:
            wait member.kick(reason="Bots sind auf diesem Server not erlaubt")
        except:
            pass
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    embed = discord.Embed(
                        description="> Bots auf diesem Server hinzufÃ¼gen ist fÃ¼r dich leider not erlaubt.",
                        Farbe=MOD_COLOR
                    )
                    try:
                        await entry.user.send(content=entry.user.mention, embed=embed)
                    except:
                        pass
                    brechen
        except:
            pass
        return

    member_log_ch = guild.get_channel(MEMBER_LOG_CHANNEL_ID)
    if member_log_ch:
        embed = discord.Embed(
            title="\u2705 Mitglied beigetreten",
            description=f"**Benutzer:** {member.mention} (`{member}`)",
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        await member_log_ch.send(embed=embed)

    Einladender = Keine
    inviter_uses = 0
    try:
        new_invites = await guild.fetch_invites()
        new_invites_map = {inv.code: inv for inv in new_invites}
        old_invite_map = invite_cache.get(guild.id, {})
        for code, new_inv in new_invite_map.items():
            old_inv = old_invite_map.get(code)
            if old_inv and new_inv.uses > old_inv.uses:
                Einladender = new_inv.inviter
                inviter_uses = new_inv.uses
                brechen
        if not der Einladende:
            for code, old_inv in old_invite_map.items():
                if Code not in new_invite_map:
                    Einladender = alte_Einladung.Einladender
                    inviter_uses = (old_inv.uses or 0) + 1
                    brechen
        if not der Einladende:
            try:
                vanity = await guild.vanity_invite()
                if vanity and old_invite_map.get("vanity"):
                    old_vanity = old_invite_map["vanity"]
                    if vanity.uses > getattr(old_vanity, "uses", 0):
                        inviter_uses = vanity.uses
                new_invite_map["vanity"] = vanity
            except:
                pass
        invite_cache[guild.id] = new_invite_map
    except Exception as e:
        wait log_bot_error("Invite-Tracking fehlgeschlagen", str(e), Gilde)

    join_log_ch = guild.get_channel(JOIN_LOG_CHANNEL_ID)
    if join_log_ch:
        description = f"**Spieler:** {member.mention} (`{member}`)\n"
        if der Einladende:
            description += f"**Eingeladen von:** {inviter.mention} (`{inviter}`)\n"
            # BEHEBUNG 3: Zeige die gesammelten Einladungen des Einladers
            Beschreibung += f"**Einladungen von {inviter.display_name}:** {inviter_uses} \U0001f39f"
        elif inviter_uses > 0:
            Beschreibung += "**Eingeladen von:** Vanity-URL (Server-Link)"
        anders:
            Beschreibung += "**Eingeladen von:** Unbekannt *(Bot fehlt 'Server verwalten' Berechtigung?)*"
        embed = discord.Embed(
            title="\U0001f4e5 Neues Mitglied",
            Beschreibung=Beschreibung,
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        # BEHEBUNG 3: Inviter wird direkt gepingt
        ping_content = inviter.mention if inviter else None
        await join_log_ch.send(content=ping_content, embed=embed)

    Rolle = guild.get_role(WHITELIST_ROLE_ID)
    if WÃ¼rfelwurf:
        try:
            await member.add_roles(rolle)
        except:
            pass

    try:
        embed = discord.Embed(
            Beschreibung=(
                "> Willkommen auf Kryptik Roleplay deinem RP Server mit Ultimativem SpaÃŸ und Hochwertigem RP\n\n"
                "> Wir wÃ¼nschen dir viel SpaÃŸ auf unserem Server and hoffen, dass du dich bei uns Gut Zurecht findest\n\n"
                "> Solltest du mal Schwierigkeiten haben melde dich gerne jederzeit Ã¼ber ein Support Ticket im Kanal"
                f"[#ticket-erstellen](https://discord.com/channels/{GUILD_ID}/{TICKET_CHANNEL_ID})"
            ),
            Farbe=LOG_COLOR
        )
        await member.send(content=member.mention, embed=embed)
    except:
        pass

    # Willkommens-Embed im Welcome-Kanal
    welcome_ch = guild.get_channel(WELCOME_CHANNEL_ID)
    if welcome_ch:
        try:
            w_embed = discord.Embed(
                title="\U0001f4e5 Willkommen auf dem Server!",
                Beschreibung=(
                    f"Herzlich Willkommen {member.mention} auf **Kryptik Roleplay**!\n\n"
                    f"Wir freuen uns, dich hier zu haben.\n"
                    f "Bitte wÃ¤hle deine Einreiseart and erstelle dein Ausweis."
                ),
                Farbe=LOG_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            w_embed.set_thumbnail(url=member.display_avatar.url)
            w_embed.add_field(name="Mitglied", value=str(member), inline=True)
            w_embed.add_field(name="ID", value=str(member.id), inline=True)
            w_embed.set_footer(text=f"Mitglied #{guild.member_count}")
            await welcome_ch.send(embed=w_embed)
        except:
            pass

    # Nickname setzen
    try:
        await member.edit(nick="RP Name | PSN")
    except:
        pass

    # \u2500\u2500 Startguthaben 5.000 \U0001f4b5 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    eco = load_economy()
    user_data = get_user(eco, member.id)
    if user_data["cash"] == 0 and user_data["bank"] == 0:
        user_data["cash"] = START_CASH
        save_economy(eco)
        await log_money_action(
            Gilde,
            "Startguthaben vergeben",
            f"**Spieler:** {member.mention}\n**Bargeld:** {START_CASH:,} \U0001f4b5 (Willkommensbonus)"
        )

# \u2500\u2500 Befehle \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! \U0001f44b")

@bot.command(name="testping")
async def testing(ctx):
    if not is_admin(ctx.author):
        return
    kanal = ctx.guild.get_channel(JOIN_LOG_CHANNEL_ID)
    Rolle = ctx.guild.get_role(MOD_ROLE_ID)
    if kanal and rolle:
        wait kanal.send(f"{rolle.mention} Dies ist ein Test-Ping vom Bot!")
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name="botstatus")
async def botstatus(ctx):
    if not is_admin(ctx.author):
        return
    await send_bot_status()
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name="ticketsetup")
async def ticketsetup(ctx):
    "Sendet das Ticket-Embed in den Ticket-Kanal. Nur fÃ¼r Admins."
    if not is_admin(ctx.author):
        return
    Kanal = ctx.guild.get_channel(TICKET_SETUP_CHANNEL_ID)
    if not Kanal:
        wait ctx.send("\u274c Ticket-Kanal not gefunden!")
        return
    embed = discord.Embed(
        title="\U0001f39f Support â€” Ticket erstellen",
        Beschreibung=(
            "BenÃ¶tigst du Hilfe or mÃ¶chtest einen Betroffenen melden?\n\n"
            "WÃ¤hlen Sie unten im MenÃ¼ die passende Ticket-Art aus.\n"
            "Unser Team wird sich schnellstmÃ¶glich um dich kÃ¼mmern.\n\n"
            "**VerfÃ¼gbare Ticket-Arten:**\n"
            "\U0001f39f **Support** â€” Allgemeiner Support\n"
            "\U0001f39f **Highteam Ticket** â€” Direkter Kontakt zum Highteam\n"
            "\U0001f39f **Fraktions Bewerbung** â€” Bewirb dich fÃ¼r eine Fraktion\n"
            "\U0001f39f **Beschwerde Ticket** â€” Beschwerde einreichen\n"
            "\U0001f39f **Bug Report** â€“ Fehler or Bug melden"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Cryptik Roleplay â€” Support System")
    Ansicht = TicketSelectView()
    await channel.send(embed=embed, view=view)
    try:
        await ctx.message.delete()
    except:
        pass

# \u2500\u2500 Wirtschafts-Slash-Befehle \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def channel_error(channel_id: int) -> str:
    return f"\u274c Du kannst diesen Befehl nur hier ausfÃ¼hren: <#{channel_id}>"

# /lohn-abholen
@bot.tree.command(name="lohn-abholen", description="Hole deinen sÃ¼dlÃ¤ndischen Lohn ab", guild=discord.Object(id=GUILD_ID))
async def lohn_abholen(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != LOHN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(LOHN_CHANNEL_ID), ephemeral=True)
        return

    main_wages = [WAGE_ROLES[r] for r in role_ids if r in WAGE_ROLES]
    if len(main_wages) > 1:
        await interaction.response.send_message(
            "\u274c Du hast mehrere Lohnklassen. Bitte wende dich ans Team.", ephemeral=True
        )
        return
    if not Hauptlohn:
        await interaction.response.send_message(
            "\u274c Du hast keine Lohnklasse and kannst keinen Lohn abholen.", ephemeral=True
        )
        return

    Gesamtlohn = Hauptlohn[0]
    if ADDITIONAL_WAGE_ROLE_ID in role_ids:
        Gesamtlohn += ZUSÃ„TZLICHER_LOHN_ROLLENLOHN

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
                f"\u274c Du kannst deinen Lohn erst in **{mins}m {secs}s** wieder abholen.",
                ephemeral=True
            )
            return

    user_data["bank"] += total_wage
    user_data["last_wage"] = now.isoformat()
    save_economy(eco)

    embed = discord.Embed(
        title="\U0001f4b5 Lohn abgeholt!",
        Beschreibung=(
            f"Du hast **{total_wage:,} \U0001f4b5** auf dein Konto erhalten.\n"
            f"**Kontostand:** {user_data['bank']:,} \U0001f4b5"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=jetzt
    )
    await interaction.response.send_message(embed=embed)

# /kontostand
@bot.tree.command(name="kontostand", description="Zeigt den Kontostand an (Team: auch per @ErwÃ¤hnung)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Mitglied von dessen Kontostand abgerufen werden soll")
async def kontostand(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids = [r.id for r in interaction.user.roles]
    is_team = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids

    # @ Option: nur fÃ¼r Teamrollen
    if nutzer not None ist:
        if not is_team:
            await interaction.response.send_message(
                "\u274c Du hast keine Berechtigung, den Kontostand anderer Mitglieder abzurufen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    anders:
        # Eigener Kontostand: KanalprÃ¼fung & RollenprÃ¼fung
        if not is_team and interaction.channel.id != BANK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
            return
        if not is_team and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("\u274c Du hast keine Berechtigung.", ephemeral=True)
            return
        Ziel = interaction.Benutzer

    eco = load_economy()
    user_data = get_user(eco, ziel.id)
    save_economy(eco)

    titel = "\U0001f4b3 Kontostand" if ziel.id == interaction.user.id else f"\U0001f4b3 Kontostand â€” {ziel.display_name}"
    embed = discord.Embed(
        title=titel,
        Beschreibung=(
            f"**Bargeld:** {user_data['cash']:,} \U0001f4b5\n"
            f"**Bank:** {user_data['bank']:,} \U0001f4b5\n"
            f"**Gesamt:** {user_data['cash'] + user_data['bank']:,} \U0001f4b5"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /einzahlen
@bot.tree.command(name="einzahlen", description="Zahle Bargeld auf dein Bankkonto ein", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wÃ¤hlen or eingeben (1.000 â€“ 10.000.000 \U0001f4b5)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def einzahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("\u274c Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        wait interaction.response.send_message("\u274c Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["cash"] < Betrag:
        await interaction.response.send_message(
            f"\u274c Nicht genug Bargeld. Dein Bargeld: **{user_data['cash']:,} \U0001f4b5**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        verbleibend = Benutzerlimit - Benutzerdaten["tÃ¤gliche Einzahlung"]
        if Betrag > Restbetrag:
            await interaction.response.send_message(
                f"\u274c Tageslimit erreicht. Du kannst heute noch **{remaining:,} \U0001f4b5** einzahlen. "
                f"(Limit: **{user_limit:,} \U0001f4b5**)",
                ephemeral=True
            )
            return
        user_data["daily_deposit"] += Betrag

    user_data["cash"] -= betrag
    user_data["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Einzahlung",
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} \U0001f4b5\n"
        f"**Bargeld danach:** {user_data['cash']:,} \U0001f4b5 | **Bank danach:** {user_data['bank']:,} \U0001f4b5"
    )

    embed = discord.Embed(
        title="\U0001f3e6 Eingezahlt",
        Beschreibung=(
            f"**Eingezahlt:** {betrag:,} \U0001f4b5\n"
            f"**Bargeld:** {user_data['cash']:,} \U0001f4b5\n"
            f"**Bank:** {user_data['bank']:,} \U0001f4b5"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)

# /auszahlen
@bot.tree.command(name="auszahlen", description="Hebe Geld von deinem Bankkonto ab", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wÃ¤hlen or eingeben (1.000 â€“ 10.000.000 \U0001f4b5)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def auszahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("\u274c Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        wait interaction.response.send_message("\u274c Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if user_data["bank"] < Betrag:
        await interaction.response.send_message(
            f"\u274c Nicht genug Guthaben. Dein Kontostand: **{user_data['bank']:,} \U0001f4b5**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        verbleibend = Benutzerlimit - Benutzerdaten["tÃ¤gliche_Abhebung"]
        if Betrag > Restbetrag:
            await interaction.response.send_message(
                f"\u274c Tageslimit erreicht. Du kannst heute noch **{remaining:,} \U0001f4b5** auszahlen. "
                f"(Limit: **{user_limit:,} \U0001f4b5**)",
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
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} \U0001f4b5\n"
        f"**Bargeld danach:** {user_data['cash']:,} \U0001f4b5 | **Bank danach:** {user_data['bank']:,} \U0001f4b5"
    )

    embed = discord.Embed(
        title="\U0001f4b8 Ausgezahlt",
        Beschreibung=(
            f"**Ausgezahlt:** {betrag:,} \U0001f4b5\n"
            f"**Bargeld:** {user_data['cash']:,} \U0001f4b5\n"
            f"**Bank:** {user_data['bank']:,} \U0001f4b5"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)

# /Ã¼berweisungen
@bot.tree.command(name="ueberweisen", description="Ãœberweise Geld an einen anderen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="EmpfÃ¤nger", betrag="Betrag wÃ¤hlen or eingeben (1.000 â€“ 10.000.000 \U0001f4b5)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def ueberweisen(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("\u274c Du hast keine Berechtigung.", ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        wait interaction.response.send_message("\u274c Du kannst not an dich selbst Ã¼berweisen.", ephemeral=True)
        return

    if betrag <= 0:
        wait interaction.response.send_message("\u274c Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco = load_economy()
    sender = get_user(eco, interaction.user.id)
    EmpfÃ¤nger = get_user(eco, nutzer.id)
    reset_daily_if_needed(sender)

    if sender["bank"] < betrag:
        await interaction.response.send_message(
            f"\u274c Nicht genug Guthaben. Dein Kontostand: **{sender['bank']:,} \U0001f4b5**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = sender.get("custom_limit") or DAILY_LIMIT
        verbleibend = Benutzerlimit - Absender["tÃ¤gliche Ãœberweisung"]
        if Betrag > Restbetrag:
            await interaction.response.send_message(
                f"\u274c Tageslimit erreicht. Du kannst heute noch **{remaining:,} \U0001f4b5** Ã¼berweisen. "
                f"(Limit: **{user_limit:,} \U0001f4b5**)",
                ephemeral=True
            )
            return
        sender["daily_transfer"] += Betrag

    Absender["Bank"] -= Betrag
    EmpfÃ¤nger["Bank"] += Betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Ãœberweisung",
        f"**Von:** {interaction.user.mention} â†’ **An:** {nutzer.mention}\n"
        f"**Betrag:** {betrag:,} \U0001f4b5 | **Sender-Bank danach:** {sender['bank']:,} \U0001f4b5"
    )

    embed = discord.Embed(
        title="\U0001f4b3 Ãœberweisung",
        Beschreibung=(
            f"**An:** {nutzer.mention}\n"
            f"**Betrag:** {betrag:,} \U0001f4b5\n"
            f"**Dein Kontostand:** {sender['bank']:,} \U0001f4b5"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)

# /GeschÃ¤ft
@bot.tree.command(name="shop", description="Zeigt den Shop an", guild=discord.Object(id=GUILD_ID))
async def shop(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        return

    items = load_shop()
    if keine Artikel:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="\U0001f6d2 Shop",
                description="Der Shop ist aktuell leer.",
                Farbe=LOG_COLOR
            ),
            ephemeral=True
        )
        return

    Zeilen = []
    for Artikel in Artikeln:
        Zeile = f"**{item['name']}** â€” {item['price']:,} \U0001f4b5"
        ar = item.get("allowed_role")
        if ar:
            r = interaction.guild.get_role(ar)
            line += f" \U0001f512 *{r.name if r else ar}*"
        lines.append(line)

    embed = discord.Embed(
        title="\U0001f6d2 Shop",
        description="\n".join(lines),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Kaufen mit /buy [itemname] â€¢ Nur mit Bargeld mÃ¶glich")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# \u2500\u2500 BEHEBUNG 2: Verbesserte Item-Suche \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Hilfsfunktion: Item in Inventar-Liste suchen (exakt â†’ Anfang â†’ enthÃ¤lt â†’ normalisiert)

def find_inventory_item(inventory: list, query: str):
    q = query.lower().strip()
    q_norm = normalize_item_name(query)
    # Exakter Treffer
    fÃ¼r i im Inventar:
        if i.lower() == q:
            return i
    # Beginnt mit Input
    fÃ¼r i im Inventar:
        if i.lower().startswith(q):
            return i
    # EnthÃ¤lt Suchbegriff
    fÃ¼r i im Inventar:
        if q in i.lower():
            return i
    # Normalisierter exakter Treffer (ignoriert Emojis, Pipes, Leerzeichen)
    fÃ¼r i im Inventar:
        if normalize_item_name(i) == q_norm:
            return i
    # Normalisiert beginnt mit
    fÃ¼r i im Inventar:
        if normalize_item_name(i).startswith(q_norm):
            return i
    # Normalisiert enthÃ¤lt
    fÃ¼r i im Inventar:
        if q_norm in normalize_item_name(i):
            return i
    return None

# Hilfsfunktion: Item per Name suchen (exakt â†’ Anfang â†’ enthÃ¤lt â†’ normalisiert)

def find_shop_item(items, query: str):
    q = query.lower().strip()
    q_norm = normalize_item_name(query)
    # Exakter Treffer
    for Artikel in Artikeln:
        if item["name"].lower() == q:
            Artikel zurÃ¼cksenden
    # Beginnt mit Input
    for Artikel in Artikeln:
        if item["name"].lower().startswith(q):
            Artikel zurÃ¼cksenden
    # EnthÃ¤lt Suchbegriff
    for Artikel in Artikeln:
        if q in item["name"].lower():
            Artikel zurÃ¼cksenden
    # Normalisierter exakter Treffer (ignoriert Emojis, Pipes, Leerzeichen)
    for Artikel in Artikeln:
        if normalize_item_name(item["name"]) == q_norm:
            Artikel zurÃ¼cksenden
    # Normalisiert beginnt mit
    for Artikel in Artikeln:
        if normalize_item_name(item["name"]).startswith(q_norm):
            Artikel zurÃ¼cksenden
    # Normalisiert enthÃ¤lt
    for Artikel in Artikeln:
        if q_norm in normalize_item_name(item["name"]):
            Artikel zurÃ¼cksenden
    return None

# /kaufen
@bot.tree.command(name="buy", description="Einen Artikel aus dem Shop kaufen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(itemname="Name des Artikels, den du kaufen mÃ¶chtest")
async def buy(interaction: discord.Interaction, itemname: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("\u274c Du hast keine Berechtigung.", ephemeral=True)
        return

    items = load_shop()
    item = find_shop_item(items, itemname)

    if not Artikel:
        await interaction.response.send_message(
            f"\u274c Artikel **{itemname}** wurde nicht. Nutze `/shop gefunden` um alle Artikel zu sehen.",
            ephemeral=True
        )
        return

    # RollenprÃ¼fung: Hat das Item eine RollenbeschrÃ¤nkung?
    allowed_role = item.get("allowed_role")
    if allowed_role and not is_adm:
        if allowed_role not in role_ids:
            rolle_obj = interaction.guild.get_role(allowed_role)
            rname = rolle_obj.name if rolle_obj else f"<@&{allowed_role}>"
            await interaction.response.send_message(
                f"\u274c Dieser Artikel ist nur fÃ¼r die Rolle **{rname}** erhÃ¤ltlich.",
                ephemeral=True
            )
            return

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)

    if user_data["cash"] < item["price"]:
        await interaction.response.send_message(
            f"\u274c Du hast not genug **Bargeld**.\n"
            f"Preis: **{item['price']:,} \U0001f4b5** | Dein Bargeld: **{user_data['cash']:,} \U0001f4b5**\n"
            f"â„¹ï¸ KÃ¤ufe sind nur mit Bargeld mÃ¶glich. Hebe Geld mit `/auszahlen` ab.",
            ephemeral=True
        )
        return

    user_data["cash"] -= item["price"]
    if "inventory" not in user_data:
        user_data["inventory"] = []
    user_data["inventory"].append(item["name"])
    if "handy" in item["name"].lower():
        await grant_handy_channel_access(interaction.guild, interaction.user)
    save_economy(eco)

    embed = discord.Embed(
        title="\u2705 Gekauft!",
        Beschreibung=(
            f"Du hast **{item['name']}** fÃ¼r **{item['price']:,} \U0001f4b5** gekauft.\n"
            f"**Verbleibendes Bargeld:** {user_data['cash']:,} \U0001f4b5"
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
    if ADMIN_ROLE_ID and MOD_ROLE_ID not in role_ids:
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["custom_limit"] = limit
    save_economy(eco)

    embed = discord.Embed(
        title="\u2699ï¸ Limit gesetzt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Neues Tageslimit:** {limit:,} \U0001f4b5\n"
            f"*(gilt fÃ¼r Einzahlen, Auszahlen & Ãœberweisen)*"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesetzt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

# /money-add (Nur fÃ¼r Administratoren)
@bot.tree.command(name="money-add", description="[ADMIN] FÃ¼ge einem Spieler Geld hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
@app_commands.default_permissions(administrator=True)
async def money_add(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("\u274c Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        wait interaction.response.send_message("\u274c Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld hinzugefÃ¼gt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** +{betrag:,} \U0001f4b5\n"
        f"**Bargeld danach:** {user_data['cash']:,} \U0001f4b5\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="\U0001f4b0 Geld hinzugefÃ¼gt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**HinzugefÃ¼gt:** {betrag:,} \U0001f4b5\n"
            f"**Bargeld:** {user_data['cash']:,} \U0001f4b5"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /remove-money (Nur fÃ¼r Administratoren)
@bot.tree.command(name="remove-money", description="[ADMIN] Entferne Geld von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
@app_commands.default_permissions(administrator=True)
async def remove_money(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("\u274c Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        wait interaction.response.send_message("\u274c Betrag muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] = max(0, user_data["cash"] - betrag)
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld entfernt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** -{betrag:,} \U0001f4b5\n"
        f"**Bargeld danach:** {user_data['cash']:,} \U0001f4b5\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="\U0001f4b8 Geld entfernt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernt:** {betrag:,} \U0001f4b5\n"
            f"**Bargeld:** {user_data['cash']:,} \U0001f4b5"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /item-add (Nur fÃ¼r Administratoren)
# BEHEBUNG 1: Nur Artikel aus dem Shop kÃ¶nnen vergeben werden
@bot.tree.command(name="item-add", description="[ADMIN] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", itemname="Itemname (muss im Shop vorhanden sein)")
@app_commands.autocomplete(itemname=shop_item_autocomplete)
@app_commands.default_permissions(administrator=True)
async def item_add(interaction: discord.Interaction, nutzer: discord.Member, itemname: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("\u274c Kein Zugriff.", ephemeral=True)
        return

    # BEHEBUNG 1: PrÃ¼fen Sie, ob das Item im Shop existiert
    shop_items = load_shop()
    shop_item = find_shop_item(shop_items, itemname)
    if not shop_item:
        await interaction.response.send_message(
            f"\u274c Das Item **{itemname}** existiert not im Shop.\n"
            f"Es kÃ¶nnen nur Shop-Items vergeben werden. Verwenden Sie `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    if "inventory" not in user_data:
        user_data["inventory"] = []
    user_data["inventory"].append(shop_item["name"]) # Offizielle Shop-Namen verwenden
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="\U0001f4e6 Element hinzugefÃ¼gt",
            description=f"**{shop_item['name']}** wurde **{nutzer.mention}** hinzugefÃ¼gt.",
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        ),
        ephemeral=True
    )

# /remove-item (Nur fÃ¼r Administratoren)
@bot.tree.command(name="remove-item", description="[ADMIN] Entferne ein Item von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", itemname="Itemname")
@app_commands.default_permissions(administrator=True)
async def remove_item(interaction: discord.Interaction, nutzer: discord.Member, itemname: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("\u274c Kein Zugriff.", ephemeral=True)
        return

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    inventory = user_data.get("inventory", [])

    match = find_inventory_item(inventory, itemname)
    if keine Ãœbereinstimmung:
        await interaction.response.send_message(
            f"\u274c **{nutzer.display_name}** besitzt kein Item namens **{itemname}**.", ephemeral=True
        )
        return

    inventory.remove(match)
    user_data["inventory"] = inventory
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            Titel="\U0001f4e6 Artikel entfernt",
            description=f"**{match}** wurde von **{nutzer.mention}** entfernt.",
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        ),
        ephemeral=True
    )

# /shop-add (nur Team) mit BestÃ¤tigung + optionaler RollenbeschrÃ¤nkung
class ShopAddConfirmView(discord.ui.View):
    def __init__(self, name: str, price: int, allowed_role_id: int | None = None):
        super().__init__(timeout=60)
        self.name = Name
        self.price = price
        self.allowed_role_id = allowed_role_id

    @discord.ui.button(label="\u2705 BestÃ¤tigen", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = load_shop()
        Eintrag = {"Name": self.Name, "Preis": self.Preis}
        if self.allowed_role_id:
            entry["allowed_role"] = self.allowed_role_id
        items.append(entry)
        save_shop(items)
        for Element in self.children:
            item.disabled = True
        rolle_info = ""
        if self.allowed_role_id:
            r = interaction.guild.get_role(self.allowed_role_id)
            rolle_info = f"\n**Nur fÃ¼r:** {r.mention if r else self.allowed_role_id}"
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="\u2705 Element hinzugefÃ¼gt",
                description=f"**{self.name}** fÃ¼r **{self.price:,} \U0001f4b5** wurde zum Shop hinzugefÃ¼gt.{rolle_info}",
                Farbe=LOG_COLOR
            ),
            Ansicht=Selbst
        )

    @discord.ui.button(label="\u274c Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for Element in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="\u274c Abgebrochen",
                description="Das Item wurde not hinzugefÃ¼gt.",
                Farbe=MOD_COLOR
            ),
            Ansicht=Selbst
        )

@bot.tree.command(name="shop-add", description="[TEAM] FÃ¼ge ein neues Item zum Shop hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    itemname="Name des Artikels",
    preis="Preis in $",
    rolle="(Optional) Nur diese Rolle kann das Item kaufen"
)
@app_commands.default_permissions(manage_messages=True)
async def shop_add(interaction: discord.Interaction, itemname: str, preis: int, rolle: discord.Role = None):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274c Kein Zugriff.", ephemeral=True)
        return

    if Preis <= 0:
        wait interaction.response.send_message("\u274c Preis muss grÃ¶ÃŸer als 0 sein.", ephemeral=True)
        return

    rolle_info = f"\n**Nur fÃ¼r:** {rolle.mention}" if rolle else "\n**RollenbeschrÃ¤nkung:** Keine"
    embed = discord.Embed(
        title="\U0001f6d2 Neues Element hinzufÃ¼gen?",
        Beschreibung=(
            f"**Name:** {itemname}\n"
            f"**Preis:** {preis:,} \U0001f4b5"
            f"{rolle_info}\n\n"
            f"Bitte bestÃ¤tige das HinzufÃ¼gen."
        ),
        Farbe=LOG_COLOR
    )
    await interaction.response.send_message(
        embed=embed,
        view=ShopAddConfirmView(itemname, preis, rolle.id if rolle else None),
        ephemeral=True
    )

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# WARNUNG SYSTEM
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

# /warn (Nur fÃ¼r Teams)
@bot.tree.command(name="warn", description="[TEAM] Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

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
        title="\u26a0ï¸ Verwarnung",
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
        f"\u2705 Verwarnung fÃ¼r {nutzer.mention} gespeichert. (Warns gesamt: **{warn_count}**)", ephemeral=True
    )

    # Automatischer Timeout bei 3 Warnungen
    if warn_count >= WARN_AUTO_TIMEOUT_COUNT:
        timeout_dur = timedelta(days=2)
        try:
            wait nutzer.timeout(timeout_dur, reason=f"Automatischer Timeout: {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht")
        except:
            pass
        # Alle Rollen entfernen
        try:
            roles_to_remove = [r for r in nutzer.roles if r != interaction.guild.default_role and not r.managed]
            if Rollen_zu_entfernen:
                wait nutzer.remove_roles(*roles_to_remove, reason="Automatischer Timeout: 3 Warns")
        except:
            pass
        # DM senden
        try:
            dm_embed = discord.Embed(
                title="\U0001f507 Du wurdest getimeoutet",
                Beschreibung=(
                    f"Du hast auf **{interaction.guild.name}** {WARN_AUTO_TIMEOUT_COUNT} Verwarnungen erhalten "
                    f"und wurde daher fÃ¼r **2 Tage** getimeoutet.\n\n"
                    f"**Letzte Verwarnung:**\n"
                    f"Grund: {grund}\nKonsequenz: {konsequenz}\n\n"
                    f"Deine Rollen wurden vorÃ¼bergehend entfernt.\n"
                    f"Nach dem Timeout melde dich bitte bei einem Teammitglied."
                ),
                Farbe=MOD_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            await nutzer.send(embed=dm_embed)
        except:
            pass
        timeout_embed = discord.Embed(
            title="\U0001f507 Automatischer Timeout",
            Beschreibung=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Grund:** {WARN_AUTO_TIMEOUT_COUNT} Warnt erreicht\n"
                f"**Dauer:** 2 Tage\n"
                f"**Rollen entfernt:** \u2705"
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
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    warns = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"\u2705 {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    Zeilen = []
    for i, w in enumerate(user_warns, 1):
        ts = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** â€” {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"\u26a0ï¸ Warnt von {nutzer.display_name}",
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
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    warns = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"â„¹ï¸ {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    entfernt = user_warns.pop()
    save_warns(warns)

    embed = discord.Embed(
        title="\u2705 Verwarnung entfernt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernte Verwarnung:** {removed['grund']}\n"
            f"**Verbleibende Warns:** {len(user_warns)}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /Rucksack
@bot.tree.command(name="rucksack", description="Zeige dein Inventar an (Team: auch per @ErwÃ¤hnung)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Spieler dessen Inventar angezeigt werden soll")
async def rucksack(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids = [r.id for r in interaction.user.roles]
    is_team = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids
    erlaubt = is_team or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES)

    if nutzer not None ist:
        if not is_team:
            await interaction.response.send_message(
                "\u274c Du hast keine Berechtigung, den Rucksack anderer Spieler einzusehen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    anders:
        if not is_team and interaction.channel.id != RUCKSACK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
            return
        if not erlaubt:
            await interaction.response.send_message("\u274c Du hast keine Berechtigung.", ephemeral=True)
            return
        Ziel = interaction.Benutzer

    eco = load_economy()
    user_data = get_user(eco, ziel.id)
    inventory = user_data.get("inventory", [])

    if not im Lagerbestand:
        desc = f"*{'Dein' if ziel.id == interaction.user.id else ziel.display_name + 's'} Rucksack ist leer.*"
    anders:
        from collections import Counter
        Anzahl = ZÃ¤hler(Inventar)
        desc = "\n".join(f"â€¢ **{item}** Ã—{count}" for item, count in counts.items())

    embed = discord.Embed(
        title=f"\U0001f392 Rucksack von {ziel.display_name}",
        Beschreibung=desc,
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /Ã¼bergeben
@bot.tree.command(name="uebergeben", description="Gib ein Item aus deinem Inventar an jemanden weiter", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="EmpfÃ¤nger", item="Item auswÃ¤hlen", menge="Wie viele mÃ¶chten du Ã¼bergeben? (Standard: 1)")
@app_commands.autocomplete(item=inventory_item_autocomplete)
async def uebergeben(interaction: discord.Interaction, nutzer: discord.Member, item: str, menge: int = 1):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != RUCKSACK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        wait interaction.response.send_message("\u274c Du kannst not an dich selbst Ã¼bergeben.", ephemeral=True)
        return

    if Menge < 1:
        wait interaction.response.send_message("\u274c Die Menge muss mindestens 1 sein.", ephemeral=True)
        return

    eco = load_economy()
    giver_data = get_user(eco, interaction.user.id)
    inv = giver_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if keine Ãœbereinstimmung:
        await interaction.response.send_message(
            f"\u274c **{item}** ist not in deinem Inventar.", ephemeral=True
        )
        return

    # PrÃ¼fen ob ausreichend vorhanden
    verfÃ¼gbar = inv.count(match)
    if verfÃ¼gbar < Menge:
        await interaction.response.send_message(
            f"\u274c Du hast nur **{available}Ã—** **{match}** im Inventar, mÃ¶chtest aber **{menge}Ã—** Ã¼bergeben.",
            ephemeral=True
        )
        return

    # Menge Ã¼bertragen
    for _ in range(menge):
        inv.remove(match)
    receiver_data = get_user(eco, nutzer.id)
    receiver_data.setdefault("inventory", []).extend([match] * menge)
    save_economy(eco)

    menge_text = f"Ã—{menge}" wenn menge > 1 sonst ""
    embed = discord.Embed(
        title="\U0001f91d Artikel geliefert",
        Beschreibung=(
            f"**Von:** {interaction.user.mention}\n"
            f"**An:** {nutzer.mention}\n"
            f"**Item:** {match} {menge_text}"
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
        return

    eco = load_economy()
    user_data = get_user(eco, interaction.user.id)
    inv = user_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if keine Ãœbereinstimmung:
        await interaction.response.send_message(
            f"\u274c **{item}** ist not in deinem Inventar.", ephemeral=True
        )
        return

    inv.remove(match)
    save_economy(eco)

    import uuid
    item_id = str(uuid.uuid4())[:8]
    versteckt = load_hidden_items()
    hidden.append({
        "id": item_id,
        "owner_id": interaction.user.id,
        "item": Ãœbereinstimmung,
        "Standort": Ort,
    })
    save_hidden_items(hidden)

    view = VersteckRetrieveView(item_id, interaction.user.id)
    bot.add_view(view)

    embed = discord.Embed(
        title="\U0001f575ï¸ Artikel versteckt",
        Beschreibung=(
            f"**Item:** {match}\n"
            f"**Versteckt an:** {ort}\n\n"
            f"Nur du kannst es wieder herausnehmen."
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, view=view)

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# TEAM-GEGENSTANDSBEFEHLE
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

# /item-geben (Nur fÃ¼r Teams)
# BEHEBUNG 1: Nur Artikel aus dem Shop kÃ¶nnen vergeben werden
@bot.tree.command(name="item-geben", description="[TEAM] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname (muss im Shop vorhanden sein)")
@app_commands.autocomplete(item=shop_item_autocomplete)
async def item_geben(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    # BEHEBUNG 1: PrÃ¼fen Sie, ob das Item im Shop existiert
    shop_items = load_shop()
    shop_item = find_shop_item(shop_items, item)
    if not shop_item:
        await interaction.response.send_message(
            f"\u274c Das Item **{item}** existiert not im Shop.\n"
            f"Es kÃ¶nnen nur Shop-Items vergeben werden. Verwenden Sie `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data.setdefault("inventory", []).append(shop_item["name"]) # Offizielle Shop-Namen verwenden
    save_economy(eco)

    embed = discord.Embed(
        Titel="\U0001f381 Artikel gegeben",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Artikel:** {shop_item['name']}\n"
            f"**Vergeben von:** {interaction.user.mention}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /item-entfernen (Nur fÃ¼r Teams)
@bot.tree.command(name="item-entfernen", description="[TEAM] Entferne ein Item von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname")
async def item_entfernen(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    eco = load_economy()
    user_data = get_user(eco, nutzer.id)
    inv = user_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if keine Ãœbereinstimmung:
        await interaction.response.send_message(
            f"\u274c **{item}** ist not im Inventar von {nutzer.mention}.", ephemeral=True
        )
        return

    inv.remove(match)
    save_economy(eco)

    embed = discord.Embed(
        title="\U0001f5d1ï¸ Artikel entfernt",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {match}\n"
            f"**Entfernt von:** {interaction.user.mention}"
        ),
        Farbe=LOG_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
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
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    Gilde = interaction.guild
    channel_link = f"https://discord.com/channels/{guild.id}/{KARTENKONTROLLE_CHANNEL_ID}"

    gesendet = 0
    fehlgeschlagen = 0
    for Mitglieder in guild.members:
        if member.bot:
            continue
        role_ids = [r.id for r in member.roles]
        is_member_role = (
            CITIZEN_ROLE_ID in role_ids
            oder any(r in role_ids for r in WAGE_ROLES)
        )
        if not is_member_role:
            continue
        try:
            dm_embed = discord.Embed(
                title="\U0001faaa Kartenkontrolle",
                Beschreibung=(
                    f"**Hallo {member.display_name}!**\n\n"
                    f"Es findet gerade eine **Kartenkontrolle** statt.\n"
                    f"Bitte begib dich in den Kanal:\n"
                    f"[\U0001f517 Zur Kartenkontrolle]({channel_link})\n\n"
                    f"*Diese Nachricht wurde automatisch durch das Team gesendet.*"
                ),
                Farbe=LOG_COLOR,
                Zeitstempel=datetime.now(timezone.utc)
            )
            await member.send(embed=dm_embed)
            gesendet += 1
        except:
            fehlgeschlagen += 1

    await interaction.followup.send(
        f"\u2705 Kartenkontrolle-DM gesendet!\n**Erfolgreich:** {sent} | **Fehlgeschlagen (DMs zu):** {failed}",
        ephemeral=True
    )

# \u2500\u2500 Ausweis Helfer \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def load_ausweis():
    if AUSWEIS_FILE.exists():
        with open(AUSWEIS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_ausweis(data):
    with open(AUSWEIS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

import random
Importieren Sie die Zeichenkette

def generate_ausweisnummer():
    letters = random.choices(string.ascii_uppercase, k=2)
    digits = random.choices(string.digits, k=6)
    return "".join(letters) + "-" + "".join(digits)

# \u2500\u2500 Einreise DM Flow \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def einreise_chat_flow(channel: discord.TextChannel, Mitglied: discord.Member, Gilde: discord.Guild, einreise_typ: str):
    def dm_check(m):
        return m.author.id == member.id and isinstance(m.channel, discord.DMChannel)

    Felder = [
        ("vorname", "\U0001f4dd **Vorname** â€“ Bitte gib deinen Vornamen ein:"),
        ("nachname", "\U0001f4dd **Nachname** â€“ Bitte gib deinen Nachnamen ein:"),
        ("geburtsdatum", "\U0001f4dd **Geburtsdatum** â€” Bitte gib dein Geburtsdatum ein (Format: TT.MM.JJJJ):"),
        ("alter", "\U0001f4dd **Alter** â€” Bitte gib dein Alter ein (zB 25):"),
        ("nationalitaet", "\U0001f4dd **NationalitÃ¤t** â€“ Bitte gib deine NationalitÃ¤t ein (zB Deutsch):"),
        ("wohnort", "\U0001f4dd **Wohnort** â€“ Bitte gib deinen Wohnort ein (zB Los Santos):"),
    ]

    antworten = {}
    typ_label = "\U0001f935 Legale Einreise" if einreise_typ == "legal" else "\U0001f977 Illegale Einreise"

    try:
        dm = await member.create_dm()
        await dm.send(
            f"\U0001faaa **Ausweis-Erstellung gestartet!** ({typ_label})\n"
            f"Beantworte bitte die folgenden **{len(felder)} Fragen**. "
            f"Du hast jeweils **2 Minuten** pro Antwort."
        )
    except:
        await channel.send(
            f"{member.mention} \u274c Ich kann dir keine DM senden. "
            f"Bitte aktiviere DMs von Servermitgliedern and wÃ¤hle deine Einreiseart erneut.",
            delete_after=20
        )
        return

    fÃ¼r SchlÃ¼ssel, Frage in Felder:
        await dm.send(frage)
        try:
            antwort = await bot.wait_for("message", check=dm_check, timeout=120.0)
            antworten[key] = antwort.content.strip()
        except asyncio.TimeoutError:
            wait dm.send("\u274c Zeit abgelaufen! Bitte wÃ¤hlen Sie Ihre Einreiseart erneut.")
            return

    ausweisnummer = generic_ausweisnummer()

    ausweis_data = load_ausweis()
    ausweis_data[str(member.id)] = {
        "vorname": antworten["vorname"],
        "nachname": antworten["nachname"],
        "geburtsdatum": antworten["geburtsdatum"],
        "alter": antworten["alter"],
        "nationalitaet": antworten["nationalitaet"],
        "wohnort": antworten["wohnort"],
        "einreise_typ": einreise_typ,
        "ausweisnummer": ausweisnummer,
        "discord_name": str(member),
        "discord_id": Mitglieds-ID,
    }
    save_ausweis(ausweis_data)

    rollen_zu_vergeben = [
        guild.get_role(rid)
        for rid in CHARAKTER_ROLLEN
        if guild.get_role(rid) is not None
    ]
    if rolling_zu_vergeben:
        try:
            wait member.add_roles(*rollen_zu_vergeben, reason="Charakter erstellt")
        except:
            pass

    embed = discord.Embed(
        title="\U0001faaa Ausweis ausgestellt",
        description="Dein Ausweis wurde erfolgreich erstellt!",
        Farbe=0x000000,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.add_field(name="Name", value=f"{antworten['vorname']} {antworten['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum", value=antworten["geburtsdatum"], inline=True)
    embed.add_field(name="Alter", value=antworten["alter"], inline=True)
    embed.add_field(name="NationalitÃ¤t", value=antworten["nationalitaet"], inline=True)
    embed.add_field(name="Wohnort", value=antworten["wohnort"], inline=True)
    embed.add_field(name="Einreiseart", value=typ_label, inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{ausweisnummer}`, inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Kryptik Roleplay â€” Ausweis")

    wait dm.send("\u2705 **Dein Ausweis wurde erfolgreich erstellt!**", embed=embed)

# \u2500\u2500 Einreise MenÃ¼ auswÃ¤hlen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class EinreiseSelect(discord.ui.Select):
    def __init__(self):
        Optionen = [
            discord.SelectOption(
                label="Legale Einreise",
                emoji="\U0001f935",
                Wert="legal",
                description="Einreise als legaler Bewohner"
            ),
            discord.SelectOption(
                label="Illegale Einfuhr",
                emoji="\U0001f977",
                Wert="illegal",
                description="Einreise als illegale Person"
            ),
        ]
        super().__init__(
            placeholder="\u2708ï¸ WÃ¤hle deine Einreiseart...",
            Optionen=Optionen,
            custom_id="einreise_select_main"
        )

    async def callback(self, interaction: discord.Interaction):
        Mitglied = interaction.Benutzer
        Gilde = interaction.guild
        role_ids = [r.id for r in member.roles]

        # PrÃ¼fen Sie, ob bereits eingereist ist
        if LEGAL_ROLE_ID in role_ids or ILLEGAL_ROLE_ID in role_ids:
            await interaction.response.send_message(
                "\u274c Du hast bereits eine Einreiseart gewÃ¤hlt. Eine Ã„nderung ist nur durch den RP-Tod mÃ¶glich.",
                ephemeral=True
            )
            return

        typ = self.values[0]
        role_id = LEGAL_ROLE_ID if typ == "legal" else ILLEGAL_ROLE_ID
        Rolle = guild.get_role(role_id)

        if Rolle:
            try:
                wait member.add_roles(role, reason=f"Einreise: {typ}")
            except Exception as e:
                wait log_bot_error("Einreise-Rolle vergeben fehlgeschlagen", str(e), guild)

        await interaction.response.send_message(
            f"\u2705 **{'Legale' if typ == 'legal' else 'Illegale'} Einreise** gewÃ¤hlt!\n"
            f"Die Ausweis-Erstellung beginnt gleich hier im Chat. Bitte beachte die Fragen.",
            ephemeral=True
        )
        asyncio.create_task(einreise_chat_flow(interaction.channel, member, guild, typ))

Klasse EinreiseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EinreiseSelect())

async def auto_einreise_setup():
    for Gilde in bot.guilds:
        Kanal = guild.get_channel(EINREISE_CHANNEL_ID)
        if not Kanal:
            continue
        bereits_gepostet = False
        try:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Einreise" in emb.title:
                            bereits_gepostet = Wahr
                            brechen
                if bereits gepostet:
                    brechen
        except:
            pass
        if bereits gepostet:
            print(f"Einreise-Embed bereits vorhanden in #{channel.name}")
            continue
        embed = discord.Embed(
            title="\u2708ï¸ Einreise â€” Kryptik Roleplay",
            Beschreibung=(
                "\U0001f935â€\u2642ï¸ â€‹â€‹**Legale Einreise** \U0001f935â€\u2642ï¸\n"
                "Du wirst auf unserem Server als legale Person einreisen."
                "Du darfst als legaler Bewohner keine illegalen AktivitÃ¤ten ausfÃ¼hren.\n\n"
                "\U0001f977 **Illegale Einreise** \U0001f977\n"
                "Du wirst auf unserem Server als illegale Person einreisen."
                "Du darfst keine staatlichen Berufe ausÃ¼ben.\n\n"
                "\u26a0ï¸ **Hinweis** \u26a0ï¸\n"
                "Eine Ã„nderung der Einreiseart ist nur durch den RP-Tod deines Charakters mÃ¶glich."
            ),
            Farbe=LOG_COLOR,
            Zeitstempel=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Kryptik Roleplay â€” Einreisesystem")
        try:
            await channel.send(embed=embed, view=EinreiseView())
            print(f"Einreise-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            wait log_bot_error("auto_einreise_setup fehlgeschlagen", str(e), guild)

# /ausweisen
@bot.tree.command(name="ausweisen", description="Zeige deinen Ausweis vor", guild=discord.Object(id=GUILD_ID))
async def ausweisen(interaction: discord.Interaction):
    if interaction.channel.id != AUSWEIS_CHANNEL_ID and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message(
            f"\u274c Diesen Befehl kannst du nur in <#{AUSWEIS_CHANNEL_ID}> benutzen.", ephemeral=True
        )
        return

    ausweis_data = load_ausweis()
    entry = ausweis_data.get(str(interaction.user.id))

    if kein Eintrag:
        await interaction.response.send_message(
            "\u274c Du hast noch kein Ausweis. WÃ¤hle zuerst deine Einreiseart and erstelle dein Ausweis.",
            ephemeral=True
        )
        return

    typ_label = "\U0001f935 Legale Einreise" if enter.get("einreise_typ") == "legal" else "\U0001f977 Illegale Einreise"

    embed = discord.Embed(
        title="\U0001faaa Personalausweis",
        Farbe=0x000000,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="Name", value=f"{entry['vorname']} {entry['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum", value=entry["geburtsdatum"], inline=True)
    # BEHEBUNG 4: Alter wird korrekt angezeigt, auch bei alten Ausweisen ohne Alter-Feld
    embed.add_field(name="Alter", value=entry.get("alter", "?"), inline=True)
    embed.add_field(name="NationalitÃ¤t", value=entry["nationalitaet"], inline=True)
    embed.add_field(name="Wohnort", value=entry["wohnort"], inline=True)
    embed.add_field(name="Einreiseart", value=typ_label, inline=True)
    embed.add_field(name="Ausweisnummer", value=f"``{entry['ausweisnummer']}``, inline=False)
    embed.set_footer(text="Kryptik Roleplay â€” Personalausweis")

    await interaction.response.send_message(embed=embed)

# /ausweis-remove (nur Admin)
@bot.tree.command(name="ausweis-remove", description="[ADMIN] Loescht den Ausweis eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler dessen Ausweis geloescht werden soll")
@app_commands.default_permissions(administrator=True)
async def ausweis_remove(interaction: discord.Interaction, nutzer: discord.Member):
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    uid = str(nutzer.id)

    if die UID not in ausweis_data:
        await interaction.response.send_message(
            f"\u274c {nutzer.mention} hat keine Ausweis.", ephemeral=True
        )
        return

    del ausweis_data[uid]
    save_ausweis(ausweis_data)

    embed = discord.Embed(
        title="\U0001f5d1ï¸ Ausweis gelÃ¶scht",
        Beschreibung=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**GelÃ¶scht von:** {interaction.user.mention}"
        ),
        Farbe=MOD_COLOR,
        Zeitstempel=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# \u2500\u2500 Admin Ausweis-Erstellen (Chat-basiert per DM) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def ausweis_create_dm_flow(admin: discord.Member, guild: discord.Guild, target: discord.Member, original_channel: discord.TextChannel):
    def dm_check(m):
        return m.author.id == admin.id and isinstance(m.channel, discord.DMChannel)

    Felder = [
        ("vorname", "\U0001f4dd **Vorname** des Spielers:"),
        ("nachname", "\U0001f4dd **Nachname** des Spielers:"),
        ("geburtsdatum", "\U0001f4dd **Geburtsdatum** (Format: TT.MM.JJJJ):"),
        ("alter", "\U0001f4dd **Alter** (zB 25):"),
        ("herkunft", "\U0001f4dd **Herkunft** (zB Deutsch):"),
        ("wohnort", "\U0001f4dd **Wohnort** (zB Los Santos):"),
        ("einreise_typ", "\U0001f4dd **Einreiseart** â€” Tippe `legal` oder `illegal`:"),
    ]

    antworten = {}

    try:
        dm = await admin.create_dm()
        await dm.send(
            f"\U0001faaa **Ausweis-Erstellung fÃ¼r {target.display_name} gestartet!**\n"
            f"Beantworte bitte die folgenden **{len(felder)} Fragen**. "
            f"Du hast jeweils **2 Minuten** pro Antwort."
        )
    except:
        await original_channel.send(
            f"{admin.mention} \u274c Ich kann dir keine DM senden. Bitte aktiviere DMs von Servermitgliedern.",
            delete_after=15
        )
        return

    fÃ¼r SchlÃ¼ssel, Frage in Felder:
        await dm.send(frage)
        try:
            antwort = await bot.wait_for("message", check=dm_check, timeout=120.0)
            wert = antwort.content.strip()

            if key == "einreise_typ":
                if wert.lower() not in ("legal", "illegal"):
                    wait dm.send("\u274c UngÃ¼ltige Eingabe. Bitte starten Sie den Befehl erneut and geben Sie `legal` oder `illegal` ein.")
                    return
                wert = wert.lower()

            antworten[key] = wert
        except asyncio.TimeoutError:
            wait dm.send("\u274c Zeit abgelaufen! Bitte starten Sie `/ausweis-create` erneut.")
            return

    ausweisnummer = generic_ausweisnummer()
    typ_label = "\U0001f935 Legale Einreise" if antworten["einreise_typ"] == "legal" else "\U0001f977 Illegale Einreise"

    ausweis_data = load_ausweis()
    ausweis_data[str(target.id)] = {
        "vorname": antworten["vorname"],
        "nachname": antworten["nachname"],
        "geburtsdatum": antworten["geburtsdatum"],
        "alter": antworten["alter"],
        "nationalitaet": antworten["herkunft"],
        "wohnort": antworten["wohnort"],
        "einreise_typ": antworten["einreise_typ"],
        "ausweisnummer": ausweisnummer,
        "erstellt_von": str(admin),
    }
    save_ausweis(ausweis_data)

    rollen_zu_vergeben = [
        guild.get_role(rid)
        for rid in CHARAKTER_ROLLEN
        if guild.get_role(rid) is not None
    ]
    if rolling_zu_vergeben:
        try:
            wait target.add_roles(*rollen_zu_vergeben, reason="Charakter erstellt (Team)")
        except:
            pass

    embed = discord.Embed(
        title="\U0001faaa Ausweis erstellt",
        Farbe=0x000000,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.add_field(name="Spieler", value=target.mention, inline=False)
    embed.add_field(name="Name", value=f"{antworten['vorname']} {antworten['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum", value=antworten["geburtsdatum"], inline=True)
    embed.add_field(name="Alter", value=antworten["alter"], inline=True)
    embed.add_field(name="Herkunft", value=antworten["herkunft"], inline=True)
    embed.add_field(name="Wohnort", value=antworten["wohnort"], inline=True)
    embed.add_field(name="Einreiseart", value=typ_label, inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{ausweisnummer}`, inline=False)
    embed.set_footer(text=f"Erstellt von {admin.display_name}")

    wait dm.send("\u2705 **Ausweis erfolgreich erstellt!**", embed=embed)

# /ausweis-create (Nur fÃ¼r Teams)
@bot.tree.command(name="ausweis-create", description="[TEAM] Erstellt einen Ausweis fÃ¼r einen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler fÃ¼r den Ausweis erstellt wird")
@app_commands.default_permissions(manage_messages=True)
async def ausweis_create(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    if str(nutzer.id) in ausweis_data:
        await interaction.response.send_message(
            f"\u274c {nutzer.mention} hat bereits einen Ausweis. Bitte zuerst mit /ausweis-remove lÃ¶schen.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"\u2705 Ausweis-Erstellung fÃ¼r **{nutzer.display_name}** gestartet!\n"
        f"Ich schicke dir die Fragen per **DM** â€” nur du siehst sie.",
        ephemeral=True
    )
    asyncio.create_task(ausweis_create_dm_flow(interaction.user, interaction.guild, nutzer, interaction.channel))

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# /delete â€“ Nachrichten lÃ¶schen (nur Team)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

@bot.tree.command(name="delete", description="[TEAM] LÃ¶scht eine bestimmte Anzahl von Nachrichten im Kanal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(anzahl="Anzahl der zu lÃ¶schenden Nachrichten (max. 100)")
@app_commands.default_permissions(manage_messages=True)
async def delete_messages(interaction: discord.Interaction, anzahl: int):
    if not is_team(interaction.user):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    if Anzahl < 1 or Anzahl > 100:
        wait interaction.response.send_message("\u274c Bitte eine Zahl zwischen 1 and 100 angeben.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    geloescht = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(
        f"\u2705 **{len(geloescht)}** Nachrichten wurden gelÃ¶scht.",
        ephemeral=True
    )

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# /create-event â€” Event erstellen (nur fÃ¼r Teams)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

EVENT_ANNOUNCEMENT_CHANNEL_ID = 1490882564561567864
EVENT_PING_ROLE_ID = 1490855737130221598

async def create_event_channel_flow(admin: discord.Member, guild: discord.Guild, channel: discord.TextChannel):
    def check(m):
        return m.author.id == admin.id and m.channel.id == channel.id

    Felder = [
        ("was", "\U0001f4cb **Was ist das Event?** (zB Fahrzeugrennen, Bankraub, Stadtfest):"),
        ("startpunkt", "\U0001f4cd **Wo ist der Startpunkt?** (zB Pillbox Hill, Legion Square):"),
        ("erklaerung", "\U0001f4dd **ErklÃ¤rung / Beschreibung des Events:**"),
        ("dauer", "â±ï¸ **Dauer des Events?** (zB 1 Stunde, 30 Minuten):"),
        ("preis", "\U0001f4b0 **Preis / Belohnung?** (zB 50.000$, Kein Preis):"),
    ]

    antworten = {}

    fÃ¼r SchlÃ¼ssel, Frage in Felder:
        frage_msg = waitingchannel.send(f"{admin.mention} {frage}")
        Antwort = await bot.wait_for("message", check=check, timeout=None)
        antworten[key] = antwort.content.strip()
        try:
            await frage_msg.delete()
            await antwort.delete()
        except:
            pass

    event_channel = guild.get_channel(EVENT_ANNOUNCEMENT_CHANNEL_ID)
    if event_channel is None:
        wait channel.send(f"{admin.mention} \u274c Event-Channel not gefunden.", delete_after=10)
        return

    ping_role = guild.get_role(EVENT_PING_ROLE_ID)
    role_mention = ping_role.mention if ping_role else ""

    embed = discord.Embed(
        title="\U0001f389 Neues Event!",
        Farbe=0x00B4D8,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001f4cb Event", value=antworten["was"], inline=False)
    embed.add_field(name="\U0001f4cdStartpunkt", value=antworten["startpunkt"], inline=True)
    embed.add_field(name="â±ï¸ Dauer", value=antworten["dauer"], inline=True)
    embed.add_field(name="\U0001f4b0 Preis", value=antworten["preis"], inline=True)
    embed.add_field(name="\U0001f4dd Beschreibung", value=antworten["erklaerung"], inline=False)
    embed.set_footer(text=f"Ereignis erstellt von {admin.display_name}")

    await event_channel.send(content=role_mention, embed=embed)
    waitchannel.send(f"{admin.mention} \u2705 **Event wurde erfolgreich gepostet** in {event_channel.mention}!", delete_after=10)

@bot.tree.command(name="create-event", description="[TEAM] Erstellt ein neues Event", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def create_event(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.send_message(
        "\U0001f389 **Event-Erstellung gestartet!** Beantworte die Fragen hier im Channel.",
        ephemeral=True
    )
    asyncio.create_task(create_event_channel_flow(interaction.user, interaction.guild, interaction.channel))

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# /create-giveaway â€” Gewinnspiel erstellen (Nur fÃ¼r Teams)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

GIVEAWAY_CHANNEL_ID = 1490882565618536551

def parse_dauer_zu_sekunden(text: str):
    "Parst eine Zeitangabe wie â€š2 Tage', â€š3 Stunden', â€š30 Minuten' in Sekunden."
    text = text.lower().strip()
    Einheiten = {
        "tag": 86400, "tage": 86400,
        "stunde": 3600, "stunden": 3600,
        "Minute": 60, "Minuten": 60,
        "Sekunde": 1, "Sekunden": 1,
    }
    insgesamt = 0
    gefunden = Falsch
    teile = text.split()
    i = 0
    while i < len(teile):
        try:
            zahl = float(teile[i].replace(",", "."))
            if i + 1 < len(teile):
                einheit = teile[i + 1].rstrip(".")
                if einheit in einheiten:
                    gesamt += int(zahl * einheiten[einheit])
                    gefunden = Wahr
                    i += 2
                    continue
        except ValueError:
            pass
        i += 1
    gib gesamt zurÃ¼ck, wenn gefunden, sonst Keine

async def create_giveaway_channel_flow(admin: discord.Member, guild: discord.Guild, channel: discord.TextChannel):
    def check(m):
        return m.author.id == admin.id and m.channel.id == channel.id

    # Frage 1: Was wird verlost?
    frage1 =awaitchannel.send(f"{admin.mention} \U0001f381 **Was wird verloren?** (zB 500.000$, Fahrzeug, Item):")
    antwort1 = await bot.wait_for("message", check=check, timeout=None)
    gewinn = antwort1.content.strip()
    try:
        await frage1.delete()
        await antwort1.delete()
    except:
        pass

    # Frage 2: Laufzeit
    frage2 =awaitchannel.send(f"{admin.mention} â±ï¸ **Wie lange lÃ¤uft das Giveaway?** (zB `2 Tage`, `12 Stunden`, `30 Minuten`):")
    solange wahr:
        antwort2 = await bot.wait_for("message", check=check, timeout=None)
        laufzeit_text = antwort2.content.strip()
        Sekunden = parse_dauer_zu_sekunden(laufzeit_text)
        try:
            await antwort2.delete()
        except:
            pass
        if sekunden and sekunden > 0:
            brechen
        Fehler = await channel.send(
            f"{admin.mention} \u274c Zeitformat not erkannt. Bitte so eingeben: `2 Tage`, `12 Stunden`, `30 Minuten`",
            delete_after=8
        )
    try:
        await frage2.delete()
    except:
        pass

    giveaway_channel = guild.get_channel(GIVEAWAY_CHANNEL_ID)
    if giveaway_channel None ist:
        waitchannel.send(f"{admin.mention} \u274c Giveaway-Channel not gefunden.", delete_after=10)
        return

    end_timestamp = int((datetime.now(timezone.utc).timestamp()) + sekunden)

    embed = discord.Embed(
        Titel="\U0001f389 Gewinnspiel!",
        Farbe=0xF1C40F,
        Zeitstempel=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001f381 Gewinn", value=gewinn, inline=False)
    embed.add_field(name="â±ï¸ Endet", value=f"<t:{end_timestamp}:R>", inline=False)
    embed.set_footer(text=f"Giveaway erstellt von {admin.display_name}")

    await giveaway_channel.send(embed=embed)
    await channel.send(
        f"{admin.mention} \u2705 **Gewinnspiel gepostet** in {giveaway_channel.mention}! Endet <t:{end_timestamp}:R>.",
        delete_after=15
    )

    # Warten bis Giveaway endet
    await asyncio.sleep(sekunden)

    # ZufÃ¤lliger Gewinner auswÃ¤hlen (kein Bot)
    mitglieder = [m for m in guild.members, wenn not m.bot]
    if not Mitglieder:
        wait giveaway_channel.send("\u274c Kein Gewinner â€” keine Mitglieder auf dem Server gefunden.")
        return

    gewinner = random.choice(mitglieder)
    ticket_channel = guild.get_channel(TICKET_CHANNEL_ID)
    ticket_mention = ticket_channel.mention if ticket_channel else "#tickets"

    end_embed = discord.Embed(
        title="\U0001f38aGewinnspiel beendet!",
        Farbe=0xF1C40F,
        Zeitstempel=datetime.now(timezone.utc)
    )
    end_embed.add_field(name="\U0001f381 Gewinn", value=gewinn, inline=False)
    end_embed.add_field(name="\U0001f3c6Gewinner", value=gewinner.mention, inline=False)
    end_embed.set_footer(text="Herzlichen GlÃ¼ckwunsch!")

    await giveaway_channel.send(
        Inhalt=(
            f"\U0001f38a {gewinner.mention} du hast das Giveaway gewonnen!\n"
            f"Bitte melde dich in {ticket_mention} um deinen Gewinn abzuholen!"
        ),
        Einbettung=Ende_Einbettung
    )

@bot.tree.command(name="create-giveaway", description="[TEAM] Erstellt ein neues Giveaway", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def create_giveaway(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.send_message(
        "\U0001f389 **Giveaway-Erstellung gestartet!** Beantworte die Fragen hier im Channel.",
        ephemeral=True
    )
    asyncio.create_task(create_giveaway_channel_flow(interaction.user, interaction.guild, interaction.channel))

token = os.environ.get("DISCORD_TOKEN")
if not Token:
    raise RuntimeError("DISCORD_TOKEN ist not gesetzt.")

bot.run(token)
