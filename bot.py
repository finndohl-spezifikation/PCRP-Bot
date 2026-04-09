import os
import io
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
import asyncio
import traceback
import signal
import random
import string

# Sicherheitscheck: Bot lÃ¤uft NUR auf Railway, nie doppelt in Replit
# Auf Railway ist RAILWAY_ENVIRONMENT automatisch gesetzt
if not os.environ.get("RAILWAY_ENVIRONMENT") and not os.environ.get("FORCE_LOCAL_RUN"):
    print("=" * 60)
    print("STOPP: Bot wurde NICHT gestartet.")
    print("Dieser Bot lÃ¤uft ausschlieÃlich auf Railway.")
    print("Bitte NICHT in Replit starten â nur auf Railway deployen!")
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

# ââ Economy ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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
    app_commands.Choice(name="1.000 ðµ",       value=1_000),
    app_commands.Choice(name="5.000 ðµ",       value=5_000),
    app_commands.Choice(name="10.000 ðµ",      value=10_000),
    app_commands.Choice(name="25.000 ðµ",      value=25_000),
    app_commands.Choice(name="50.000 ðµ",      value=50_000),
    app_commands.Choice(name="100.000 ðµ",     value=100_000),
    app_commands.Choice(name="250.000 ðµ",     value=250_000),
    app_commands.Choice(name="500.000 ðµ",     value=500_000),
    app_commands.Choice(name="1.000.000 ðµ",   value=1_000_000),
]

LIMIT_CHOICES = [
    app_commands.Choice(name="1.000.000 ðµ",   value=1_000_000),
    app_commands.Choice(name="2.000.000 ðµ",   value=2_000_000),
    app_commands.Choice(name="3.000.000 ðµ",   value=3_000_000),
    app_commands.Choice(name="4.000.000 ðµ",   value=4_000_000),
    app_commands.Choice(name="5.000.000 ðµ",   value=5_000_000),
    app_commands.Choice(name="6.000.000 ðµ",   value=6_000_000),
    app_commands.Choice(name="7.000.000 ðµ",   value=7_000_000),
    app_commands.Choice(name="8.000.000 ðµ",   value=8_000_000),
    app_commands.Choice(name="9.000.000 ðµ",   value=9_000_000),
    app_commands.Choice(name="10.000.000 ðµ",  value=10_000_000),
]

# ââ Persistenter Datenspeicher ââââââââââââââââââââââââââââââââââââââââââââ
# Railway: Volume unter /data mounten und DATA_DIR=/data als Umgebungsvariable setzen.
# Ohne DATA_DIR wird "data/" neben der Bot-Datei genutzt â geht verloren bei Redeploy!
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Warnung wenn kein persistentes Verzeichnis gesetzt ist
_using_persistent_volume = bool(os.environ.get("DATA_DIR"))
if not _using_persistent_volume:
    print("=" * 65)
    print("â ï¸  WARNUNG: DATA_DIR ist nicht gesetzt!")
    print("   Daten werden in ./data/ gespeichert und gehen bei Redeploy verloren.")
    print("   Auf Railway: Volume mounten und DATA_DIR=/data setzen!")
    print("=" * 65)

ECONOMY_FILE      = DATA_DIR / "economy_data.json"
SHOP_FILE         = DATA_DIR / "shop_data.json"
WARNS_FILE        = DATA_DIR / "warns_data.json"
HIDDEN_ITEMS_FILE = DATA_DIR / "hidden_items.json"
AUSWEIS_FILE      = DATA_DIR / "ausweis_data.json"


# ââ Sichere Speicher-Helfer (atomar + Backup) âââââââââââââââââââââââââââââ

import shutil

def safe_json_save(filepath: Path, data) -> None:
    """
    Speichert JSON-Daten sicher:
    1. Schreibt zuerst in eine .tmp Datei (kein Datenverlust bei Absturz)
    2. Ersetzt die Hauptdatei atomar
    3. Erstellt eine .bak Sicherungskopie
    """
    tmp_path = filepath.with_suffix(".tmp")
    bak_path = filepath.with_suffix(".bak")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(filepath)
        shutil.copy2(filepath, bak_path)
    except Exception as e:
        print(f"[FEHLER] safe_json_save({filepath.name}): {e}")
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def safe_json_load(filepath: Path, default):
    """
    LÃ¤dt JSON-Daten mit automatischem Fallback:
    1. Versucht die Hauptdatei zu lesen
    2. Bei Fehler: Fallback auf .bak Sicherungskopie
    3. Wenn beides fehlt/kaputt: gibt default zurÃ¼ck
    """
    bak_path = filepath.with_suffix(".bak")
    for path in [filepath, bak_path]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    result = json.load(f)
                if path == bak_path:
                    print(f"[WARNUNG] {filepath.name} kaputt â Backup geladen: {bak_path.name}")
                    safe_json_save(filepath, result)
                return result
            except Exception as e:
                print(f"[FEHLER] Lesen von {path.name} fehlgeschlagen: {e}")
    return default


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
ALINA_ROLE_ID       = 1490855646558556282
LEGAL_ROLE_ID       = 1490855729635135489
ILLEGAL_ROLE_ID     = 1490855730767597738

WARN_AUTO_TIMEOUT_COUNT = 3
START_CASH              = 5_000     # Startguthaben fÃ¼r neue Spieler

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
    "mistkerl", "penner", "hurenkind", "dummficker", "scheiÃ",
]

spam_tracker  = {}
spam_warned   = set()
ticket_data   = {}
counting_state    = {"count": 0, "last_user_id": None}
counting_handled  = set()  # verhindert doppelte Verarbeitung

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
                title=f"â ï¸ Bot Fehler â {title}",
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
            emoji = "ð¢" if status else "ð´"
            state = "Online" if status else "Offline"
            desc += f"{emoji} **{feature}** â {state}\n"
        embed = discord.Embed(
            title="ð¤ Bot Status â Alle Funktionen",
            description=desc,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await log_ch.send(embed=embed)
        except Exception:
            pass


async def apply_timeout_restrictions(member, guild, duration_h=None, duration_m=None, reason="RegelverstoÃ"):
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


# ââ Economy Helpers ââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def load_economy():
    return safe_json_load(ECONOMY_FILE, {})


def save_economy(data):
    safe_json_save(ECONOMY_FILE, data)


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
        # replaced_user_data["daily_reset"] = now.isoformat()
        return
    last_reset = datetime.fromisoformat(# replaced_user_data["daily_reset"])
    if (now - last_reset).total_seconds() >= 86400:
        # replaced_user_data["daily_deposit"]  = 0
        # replaced_user_data["daily_withdraw"] = 0
        # replaced_user_data["daily_transfer"] = 0
        # replaced_user_data["daily_reset"]    = now.isoformat()


def load_shop():
    return safe_json_load(SHOP_FILE, [])


def save_shop(items):
    safe_json_save(SHOP_FILE, items)


def has_citizen_or_wage(member):
    role_ids = [r.id for r in member.roles]
    return (
        CITIZEN_ROLE_ID in role_ids
        or ADMIN_ROLE_ID in role_ids
        or any(r in role_ids for r in WAGE_ROLES)
    )


def is_team(member):
    return any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in member.roles)


# ââ Warn Helpers ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def load_warns():
    return safe_json_load(WARNS_FILE, {})


def save_warns(data):
    safe_json_save(WARNS_FILE, data)


def get_user_warns(warns, user_id):
    return warns.setdefault(str(user_id), [])


# ââ Hidden Items Helpers ââââââââââââââââââââââââââââââââââââââââââââââââââ

def load_hidden_items():
    return safe_json_load(HIDDEN_ITEMS_FILE, [])


def save_hidden_items(data):
    safe_json_save(HIDDEN_ITEMS_FILE, data)


# ââ Money Log Helper ââââââââââââââââââââââââââââââââââââââââââââââââââââââ

async def log_money_action(guild: discord.Guild, title: str, description: str):
    ch = guild.get_channel(MONEY_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title=f"ðµ {title}",
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await ch.send(embed=embed)
        except Exception:
            pass


# ââ Betrag Autocomplete (1Kâ10M, Freitext erlaubt) ââââââââââââââââââââââââ

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
        label = f"{val:,} ðµ".replace(",", ".")
        if clean == "" or clean in str(val) or clean.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=val))
    return choices[:25]


# ââ Shop-Item Autocomplete ââââââââââââââââââââââââââââââââââââââââââââââââ

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


# ââ Inventar-Item Autocomplete ââââââââââââââââââââââââââââââââââââââââââââ

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
        label = f"{item_name} (Ã{count})"
        if current_lower == "" or current_lower in item_name.lower():
            choices.append(app_commands.Choice(name=label, value=item_name))
    return choices[:25]


# ââ BEHEBUNG 2: Normalisierungsfunktion fÃ¼r Item-Namen ââââââââââââââââââââ
# Entfernt Emojis, Pipe-Zeichen und normalisiert Leerzeichen,
# damit z.B. "Handy" das Item "ð±| Handy" sicher findet.

def normalize_item_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[\|\-\_]+', ' ', name)
    name = ''.join(c for c in name if c.isalnum() or c.isspace())
    return re.sub(r'\s+', ' ', name).strip()


# ââ Versteck-Button (persistent) âââââââââââââââââââââââââââââââââââââââââ

class VersteckRetrieveView(discord.ui.View):
    def __init__(self, item_id: str, owner_id: int):
        super().__init__(timeout=None)
        self.item_id  = item_id
        self.owner_id = owner_id
        btn = discord.ui.Button(
            label="ð¦ Aus Versteck holen",
            style=discord.ButtonStyle.green,
            custom_id=f"retrieve_{item_id}_{owner_id}"
        )
        btn.callback = self.retrieve_callback
        self.add_item(btn)

    async def retrieve_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "â Nur derjenige der das Item versteckt hat kann es herausnehmen.",
                ephemeral=True
            )
            return
        hidden = load_hidden_items()
        entry  = next((h for h in hidden if h["id"] == self.item_id), None)
        if not entry:
            await interaction.response.send_message("â Item wurde bereits geborgen oder existiert nicht mehr.", ephemeral=True)
            return

        # Item zurÃ¼ck ins Inventar
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

        # Ãffentliche Nachricht im Kanal fÃ¼r alle sichtbar
        public_embed = discord.Embed(
            title="ð¦ Item aus Versteck geholt",
            description=(
                f"**{interaction.user.mention}** hat ein Item aus einem Versteck geholt!\n\n"
                f"**Item:** {entry['item']}\n"
                f"**Versteck-Ort:** {entry['location']}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        public_embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=public_embed)

        # BestÃ¤tigung nur fÃ¼r den Nutzer
        await interaction.followup.send(
            f"â **{entry['item']}** ist wieder in deinem Rucksack.",
            ephemeral=True
        )


# ââ Ticket System ââââââââââââââââââââââââââââââââââââââââââââââââââââââ

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
                "â Du hast bereits ein offenes Ticket!", ephemeral=True
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
            "â Ticket konnte nicht erstellt werden.", ephemeral=True
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
        title=f"ð {type_name}",
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
    welcome_embed.set_footer(text="Nur Teammitglieder kÃ¶nnen das Ticket schlieÃen")

    action_view = TicketActionView()
    await channel.send(content=team_mentions, embed=welcome_embed, view=action_view)

    await interaction.response.send_message(
        f"â Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True
    )

    log_ch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="ð Ticket GeÃ¶ffnet",
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
                emoji="ð",
                value="support",
                description="Allgemeiner Support"
            ),
            discord.SelectOption(
                label="Highteam Ticket",
                emoji="ð",
                value="highteam",
                description="Direkter Kontakt zum Highteam"
            ),
            discord.SelectOption(
                label="Fraktions Bewerbung",
                emoji="ð",
                value="fraktion",
                description="Bewerbung fÃ¼r eine Fraktion"
            ),
            discord.SelectOption(
                label="Beschwerde Ticket",
                emoji="ð",
                value="beschwerde",
                description="Beschwerde einreichen"
            ),
            discord.SelectOption(
                label="Bug Report",
                emoji="ð",
                value="bug",
                description="Fehler oder Bug melden"
            ),
        ]
        super().__init__(
            placeholder="ð WÃ¤hle eine Ticket-Art aus...",
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
                "â Berechtigung konnte nicht gesetzt werden.", ephemeral=True
            )
            await log_bot_error("Ticket-Zuweisung fehlgeschlagen", str(e), interaction.guild)
            return

        if channel.id in ticket_data:
            ticket_data[channel.id]["handler"]    = str(user)
            ticket_data[channel.id]["handler_id"] = user.id

        assign_embed = discord.Embed(
            description=(
                f"ð¤ {user.mention} wurde dem Ticket zugewiesen.\n"
                f"**Zugewiesen von:** {interaction.user.mention}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await channel.send(embed=assign_embed)
        await interaction.response.send_message(
            f"â {user.mention} wurde dem Ticket zugewiesen.", ephemeral=True
        )


class AssignView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(AssignUserSelect())


class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ticket schlieÃen",
        style=discord.ButtonStyle.red,
        emoji="ð",
        custom_id="ticket_close_btn"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "â Nur Teammitglieder kÃ¶nnen Tickets schlieÃen.", ephemeral=True
            )
            return

        channel = interaction.channel
        data    = ticket_data.get(channel.id)
        if not data:
            await interaction.response.send_message(
                "â Ticket-Daten nicht gefunden.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        ticket_data[channel.id]["handler"]    = str(interaction.user)
        ticket_data[channel.id]["handler_id"] = interaction.user.id

        closing_embed = discord.Embed(
            title="ð Ticket wird geschlossen...",
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
                        transcript_lines.append(f"  â³ {short}")
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
                title="ð Ticket Geschlossen",
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
                    title="ð Dein Ticket wurde geschlossen",
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
        emoji="ð¤",
        custom_id="ticket_assign_btn"
    )
    async def assign_person(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_mod_or_admin(interaction.user):
            await interaction.response.send_message(
                "â Nur Teammitglieder kÃ¶nnen Personen zuweisen.", ephemeral=True
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

        star_display = "â­" * stars + "â" * (5 - stars)

        thank_embed = discord.Embed(
            title="ð Danke fÃ¼r deine Bewertung!",
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


def guild_member_bot(guild: discord.Guild):
    return guild.me


# ââ Events ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

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

    # Automatischen Backup-Task starten
    if not auto_backup_task.is_running():
        auto_backup_task.start()
        print("[BACKUP] Auto-Backup-Task gestartet (alle 30 Minuten)")

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
            print(f"Ticket-Embed bereits vorhanden in #{channel.name} â kein erneutes Posten.")
            continue
        embed = discord.Embed(
            title="ð Support â Ticket erstellen",
            description=(
                "BenÃ¶tigst du Hilfe oder mÃ¶chtest ein Anliegen melden?\n\n"
                "WÃ¤hle unten im MenÃ¼ die passende Ticket-Art aus.\n"
                "Unser Team wird sich schnellstmÃ¶glich um dich kÃ¼mmern.\n\n"
                "**VerfÃ¼gbare Ticket-Arten:**\n"
                "ð **Support** â Allgemeiner Support\n"
                "ð **Highteam Ticket** â Direkter Kontakt zum Highteam\n"
                "ð **Fraktions Bewerbung** â Bewirb dich fÃ¼r eine Fraktion\n"
                "ð **Beschwerde Ticket** â Beschwerde einreichen\n"
                "ð **Bug Report** â Fehler oder Bug melden"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Cryptik Roleplay â Support System")
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
            print(f"Lohnliste bereits vorhanden in #{channel.name} â kein erneutes Posten.")
            continue
        desc = (
            f"<@&1490855796932739093>\n**1.500 ðµ StÃ¼ndlich**\n\n"
            f"<@&1490855789844234310>\n**2.500 ðµ StÃ¼ndlich**\n\n"
            f"<@&1490855790913785886>\n**3.500 ðµ StÃ¼ndlich**\n\n"
            f"<@&1490855791953973421>\n**4.500 ðµ StÃ¼ndlich**\n\n"
            f"<@&1490855792671461478>\n**5.500 ðµ StÃ¼ndlich**\n\n"
            f"<@&1490855793694871595>\n**6.500 ðµ StÃ¼ndlich**\n\n"
            f"<@&1490855795360006246>\n**1.200 ðµ StÃ¼ndlich** *(Zusatzlohn)*"
        )
        embed = discord.Embed(
            title="ðµ Lohnliste ðµ",
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

    # Alina-Session: Nachrichten direkt an Alina weiterleiten, alle Filter Ã¼berspringen
    alina_key = (message.channel.id, message.author.id)
    if alina_key in alina_sessions:
        await handle_alina_message(message)
        await bot.process_commands(message)
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
                f"â {message.author.mention} Nur Zahlen sind hier erlaubt! Der ZÃ¤hler geht weiter bei **{counting_state['count'] + 1}**.",
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
                f"â {message.author.mention} Du kannst nicht zweimal hintereinander zÃ¤hlen! Der ZÃ¤hler steht bei **{counting_state['count']}**.",
                delete_after=5
            )
        except Exception:
            pass
        return

    if number == expected:
        counting_state["count"] = number
        counting_state["last_user_id"] = message.author.id
        await message.add_reaction("â")
    else:
        counting_state["count"] = 0
        counting_state["last_user_id"] = None
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await message.channel.send(
                f"â {message.author.mention} Falsche Zahl! Erwartet wurde **{expected}**, nicht **{number}**.\n"
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
                "> Du hast gegen unsere Server Regeln verstoÃen\n\n"
                "> Bitte wende dich an den Support"
            ),
            color=MOD_COLOR
        )
        await member.send(content=member.mention, embed=embed)
    except Exception:
        pass
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        timeout_status = "â Timeout erteilt (300h)" if timeout_ok else "â Timeout fehlgeschlagen â Berechtigung prÃ¼fen!"
        rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
        embed = discord.Embed(
            title="ð¨ Moderation â Timeout",
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
            f"{message.author.mention} Bitte sende Links ausschlieÃlich im <#{MEMES_CHANNEL_ID}> Kanal",
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
                "> Bitte beachte unsere Serverregeln. Bei weiteren VerstÃ¶Ãen folgen Konsequenzen."
            ),
            color=MOD_COLOR
        )
        await message.author.send(content=message.author.mention, embed=embed)
    except Exception:
        pass
    log_ch = message.guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="ð¨ Moderation â VulgÃ¤re Sprache",
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
            timeout_status = "â Timeout erteilt (10min)" if timeout_ok else "â Timeout fehlgeschlagen â Berechtigung prÃ¼fen!"
            rollen_status  = f"Entfernt: {', '.join(r.name for r in roles_removed)}" if roles_removed else "Keine Rollen entfernt"
            embed = discord.Embed(
                title="ð¨ Moderation â Timeout (Spam)",
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
        title="ðï¸ Nachricht gelÃ¶scht",
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
        title="âï¸ Nachricht bearbeitet",
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
        title="ð­ Rollen geÃ¤ndert",
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
        title="ð¨ Mitglied gebannt",
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
    title = "ð¢ Mitglied gekickt" if action == "gekickt" else "ðª Mitglied hat den Server verlassen"
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
                title="ð¤ Mitglied hat den Server verlassen",
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
            title="â Mitglied beigetreten",
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
            # BEHEBUNG 3: Zeige die gesammelten Einladungen des Einladers
            description += f"**Einladungen von {inviter.display_name}:** {inviter_uses} ð"
        elif inviter_uses > 0:
            description += "**Eingeladen von:** Vanity-URL (Server-Link)"
        else:
            description += "**Eingeladen von:** Unbekannt *(Bot fehlt 'Server verwalten' Berechtigung?)*"
        embed = discord.Embed(
            title="ð¥ Neues Mitglied",
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        # BEHEBUNG 3: Inviter wird direkt gepingt
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
                "> Willkommen auf Kryptik Roleplay deinem RP server mit Ultimativem SpaÃ und Hochwertigem RP\n\n"
                "> Wir wÃ¼nschen dir viel SpaÃ auf unserem Server und hoffen das du dich bei uns Gut Zurecht findest\n\n"
                "> Solltest du mal Schwierigkeiten haben melde dich gerne Jederzeit Ã¼ber ein Support Ticket im channel "
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
                title="ð¥ Willkommen auf dem Server!",
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

    # Nickname setzen
    try:
        await member.edit(nick="RP Name | PSN")
    except Exception:
        pass

    # ââ Startguthaben 5.000 ðµ ââââââââââââââââââââââââââââââââââââââââââââ
    eco       = load_economy()
    user_data = get_user(eco, member.id)
    if # replaced_user_data["cash"] == 0 and # replaced_user_data["bank"] == 0:
        # replaced_user_data["cash"] = START_CASH
        save_economy(eco)
        await log_money_action(
            guild,
            "Startguthaben vergeben",
            f"**Spieler:** {member.mention}\n**Bargeld:** {START_CASH:,} ðµ (Willkommensbonus)"
        )


# ââ Commands ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! ð")


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
    """Sendet das Ticket-Embed in den Ticket-Kanal. Nur fÃ¼r Admins."""
    if not is_admin(ctx.author):
        return
    channel = ctx.guild.get_channel(TICKET_SETUP_CHANNEL_ID)
    if not channel:
        await ctx.send("â Ticket-Kanal nicht gefunden!")
        return
    embed = discord.Embed(
        title="ð Support â Ticket erstellen",
        description=(
            "BenÃ¶tigst du Hilfe oder mÃ¶chtest ein Anliegen melden?\n\n"
            "WÃ¤hle unten im MenÃ¼ die passende Ticket-Art aus.\n"
            "Unser Team wird sich schnellstmÃ¶glich um dich kÃ¼mmern.\n\n"
            "**VerfÃ¼gbare Ticket-Arten:**\n"
            "ð **Support** â Allgemeiner Support\n"
            "ð **Highteam Ticket** â Direkter Kontakt zum Highteam\n"
            "ð **Fraktions Bewerbung** â Bewirb dich fÃ¼r eine Fraktion\n"
            "ð **Beschwerde Ticket** â Beschwerde einreichen\n"
            "ð **Bug Report** â Fehler oder Bug melden"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Cryptik Roleplay â Support System")
    view = TicketSelectView()
    await channel.send(embed=embed, view=view)
    try:
        await ctx.message.delete()
    except Exception:
        pass


# ââ Economy Slash Commands âââââââââââââââââââââââââââââââââââââââââââââââ

def channel_error(channel_id: int) -> str:
    return f"â Du kannst diesen Command nur hier ausfÃ¼hren: <#{channel_id}>"


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
            "â Du hast mehrere Lohnklassen. Bitte wende dich ans Team.", ephemeral=True
        )
        return
    if not main_wages:
        await interaction.response.send_message(
            "â Du hast keine Lohnklasse und kannst keinen Lohn abholen.", ephemeral=True
        )
        return

    total_wage = main_wages[0]
    if ADDITIONAL_WAGE_ROLE_ID in role_ids:
        total_wage += ADDITIONAL_WAGE_ROLE_WAGE

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    now       = datetime.now(timezone.utc)

    if # replaced_user_data["last_wage"]:
        last = datetime.fromisoformat(# replaced_user_data["last_wage"])
        diff = (now - last).total_seconds()
        if diff < 3600:
            remaining = int(3600 - diff)
            mins = remaining // 60
            secs = remaining % 60
            await interaction.response.send_message(
                f"â Du kannst deinen Lohn erst in **{mins}m {secs}s** wieder abholen.",
                ephemeral=True
            )
            return

    # replaced_user_data["bank"]      += total_wage
    # replaced_user_data["last_wage"]  = now.isoformat()
    save_economy(eco)

    embed = discord.Embed(
        title="ðµ Lohn abgeholt!",
        description=(
            f"Du hast **{total_wage:,} ðµ** auf dein Konto erhalten.\n"
            f"**Kontostand:** {# replaced_user_data['bank']:,} ðµ"
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
    is_team   = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids

    # @ Option: nur fÃ¼r Teamrollen
    if nutzer is not None:
        if not is_team:
            await interaction.response.send_message(
                "â Du hast keine Berechtigung, den Kontostand anderer Mitglieder abzurufen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    else:
        # Eigener Kontostand: KanalprÃ¼fung & RollenprÃ¼fung
        if not is_team and interaction.channel.id != BANK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
            return
        if not is_team and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("â Du hast keine Berechtigung.", ephemeral=True)
            return
        ziel = interaction.user

    eco       = load_economy()
    user_data = get_user(eco, ziel.id)
    save_economy(eco)

    titel = "ð³ Kontostand" if ziel.id == interaction.user.id else f"ð³ Kontostand â {ziel.display_name}"
    embed = discord.Embed(
        title=titel,
        description=(
            f"**Bargeld:** {# replaced_user_data['cash']:,} ðµ\n"
            f"**Bank:** {# replaced_user_data['bank']:,} ðµ\n"
            f"**Gesamt:** {# replaced_user_data['cash'] + # replaced_user_data['bank']:,} ðµ"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /einzahlen
@bot.tree.command(name="einzahlen", description="Zahle Bargeld auf dein Bankkonto ein", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wÃ¤hlen oder eingeben (1.000 â 10.000.000 ðµ)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def einzahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("â Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("â Betrag muss grÃ¶Ãer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if # replaced_user_data["cash"] < betrag:
        await interaction.response.send_message(
            f"â Nicht genug Bargeld. Dein Bargeld: **{# replaced_user_data['cash']:,} ðµ**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - # replaced_user_data["daily_deposit"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"â Tageslimit erreicht. Du kannst heute noch **{remaining:,} ðµ** einzahlen. "
                f"(Limit: **{user_limit:,} ðµ**)",
                ephemeral=True
            )
            return
        # replaced_user_data["daily_deposit"] += betrag

    # replaced_user_data["cash"] -= betrag
    # replaced_user_data["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Einzahlung",
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} ðµ\n"
        f"**Bargeld danach:** {# replaced_user_data['cash']:,} ðµ | **Bank danach:** {# replaced_user_data['bank']:,} ðµ"
    )

    embed = discord.Embed(
        title="ð¦ Eingezahlt",
        description=(
            f"**Eingezahlt:** {betrag:,} ðµ\n"
            f"**Bargeld:** {# replaced_user_data['cash']:,} ðµ\n"
            f"**Bank:** {# replaced_user_data['bank']:,} ðµ"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /auszahlen
@bot.tree.command(name="auszahlen", description="Hebe Geld von deinem Bankkonto ab", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wÃ¤hlen oder eingeben (1.000 â 10.000.000 ðµ)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def auszahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("â Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("â Betrag muss grÃ¶Ãer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    reset_daily_if_needed(user_data)

    if # replaced_user_data["bank"] < betrag:
        await interaction.response.send_message(
            f"â Nicht genug Guthaben. Dein Kontostand: **{# replaced_user_data['bank']:,} ðµ**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = user_data.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - # replaced_user_data["daily_withdraw"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"â Tageslimit erreicht. Du kannst heute noch **{remaining:,} ðµ** auszahlen. "
                f"(Limit: **{user_limit:,} ðµ**)",
                ephemeral=True
            )
            return
        # replaced_user_data["daily_withdraw"] += betrag

    # replaced_user_data["bank"] -= betrag
    # replaced_user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Auszahlung",
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} ðµ\n"
        f"**Bargeld danach:** {# replaced_user_data['cash']:,} ðµ | **Bank danach:** {# replaced_user_data['bank']:,} ðµ"
    )

    embed = discord.Embed(
        title="ð¸ Ausgezahlt",
        description=(
            f"**Ausgezahlt:** {betrag:,} ðµ\n"
            f"**Bargeld:** {# replaced_user_data['cash']:,} ðµ\n"
            f"**Bank:** {# replaced_user_data['bank']:,} ðµ"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /Ã¼berweisen
@bot.tree.command(name="ueberweisen", description="Ãberweise Geld an einen anderen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="EmpfÃ¤nger", betrag="Betrag wÃ¤hlen oder eingeben (1.000 â 10.000.000 ðµ)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def ueberweisen(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("â Du hast keine Berechtigung.", ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("â Du kannst nicht an dich selbst Ã¼berweisen.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("â Betrag muss grÃ¶Ãer als 0 sein.", ephemeral=True)
        return

    eco        = load_economy()
    sender     = get_user(eco, interaction.user.id)
    receiver   = get_user(eco, nutzer.id)
    reset_daily_if_needed(sender)

    if sender["bank"] < betrag:
        await interaction.response.send_message(
            f"â Nicht genug Guthaben. Dein Kontostand: **{sender['bank']:,} ðµ**", ephemeral=True
        )
        return

    if not is_adm:
        user_limit = sender.get("custom_limit") or DAILY_LIMIT
        remaining  = user_limit - sender["daily_transfer"]
        if betrag > remaining:
            await interaction.response.send_message(
                f"â Tageslimit erreicht. Du kannst heute noch **{remaining:,} ðµ** Ã¼berweisen. "
                f"(Limit: **{user_limit:,} ðµ**)",
                ephemeral=True
            )
            return
        sender["daily_transfer"] += betrag

    sender["bank"]   -= betrag
    receiver["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Ãberweisung",
        f"**Von:** {interaction.user.mention} â **An:** {nutzer.mention}\n"
        f"**Betrag:** {betrag:,} ðµ | **Sender-Bank danach:** {sender['bank']:,} ðµ"
    )

    embed = discord.Embed(
        title="ð³ Ãberweisung",
        description=(
            f"**An:** {nutzer.mention}\n"
            f"**Betrag:** {betrag:,} ðµ\n"
            f"**Dein Kontostand:** {sender['bank']:,} ðµ"
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
                title="ð Shop",
                description="Der Shop ist aktuell leer.",
                color=LOG_COLOR
            ),
            ephemeral=True
        )
        return

    lines = []
    for item in items:
        line = f"**{item['name']}** â {item['price']:,} ðµ"
        ar = item.get("allowed_role")
        if ar:
            r = interaction.guild.get_role(ar)
            line += f"  ð *{r.name if r else ar}*"
        lines.append(line)

    embed = discord.Embed(
        title="ð Shop",
        description="\n".join(lines),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Kaufen mit /buy [itemname] â¢ Nur mit Bargeld mÃ¶glich")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ââ BEHEBUNG 2: Verbesserte Item-Suche ââââââââââââââââââââââââââââââââââââ
# Hilfsfunktion: Item in Inventar-Liste suchen (exakt â Anfang â enthÃ¤lt â normalisiert)

def find_inventory_item(inventory: list, query: str):
    q = query.lower().strip()
    q_norm = normalize_item_name(query)
    # Exakter Treffer
    for i in inventory:
        if i.lower() == q:
            return i
    # Beginnt mit Suchbegriff
    for i in inventory:
        if i.lower().startswith(q):
            return i
    # EnthÃ¤lt Suchbegriff
    for i in inventory:
        if q in i.lower():
            return i
    # Normalisierter exakter Treffer (ignoriert Emojis, Pipes, Leerzeichen)
    for i in inventory:
        if normalize_item_name(i) == q_norm:
            return i
    # Normalisiert beginnt mit
    for i in inventory:
        if normalize_item_name(i).startswith(q_norm):
            return i
    # Normalisiert enthÃ¤lt
    for i in inventory:
        if q_norm in normalize_item_name(i):
            return i
    return None


# Hilfsfunktion: Item per Name suchen (exakt â Anfang â enthÃ¤lt â normalisiert)

def find_shop_item(items, query: str):
    q = query.lower().strip()
    q_norm = normalize_item_name(query)
    # Exakter Treffer
    for item in items:
        if item["name"].lower() == q:
            return item
    # Beginnt mit Suchbegriff
    for item in items:
        if item["name"].lower().startswith(q):
            return item
    # EnthÃ¤lt Suchbegriff
    for item in items:
        if q in item["name"].lower():
            return item
    # Normalisierter exakter Treffer (ignoriert Emojis, Pipes, Leerzeichen)
    for item in items:
        if normalize_item_name(item["name"]) == q_norm:
            return item
    # Normalisiert beginnt mit
    for item in items:
        if normalize_item_name(item["name"]).startswith(q_norm):
            return item
    # Normalisiert enthÃ¤lt
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
        await interaction.response.send_message("â Du hast keine Berechtigung.", ephemeral=True)
        return

    items = load_shop()
    item  = find_shop_item(items, itemname)

    if not item:
        await interaction.response.send_message(
            f"â Item **{itemname}** wurde nicht gefunden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    # RollenprÃ¼fung: Hat das Item eine RollenbeschrÃ¤nkung?
    allowed_role = item.get("allowed_role")
    if allowed_role and not is_adm:
        if allowed_role not in role_ids:
            rolle_obj = interaction.guild.get_role(allowed_role)
            rname     = rolle_obj.name if rolle_obj else f"<@&{allowed_role}>"
            await interaction.response.send_message(
                f"â Dieses Item ist nur fÃ¼r die Rolle **{rname}** erhÃ¤ltlich.",
                ephemeral=True
            )
            return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)

    if # replaced_user_data["cash"] < item["price"]:
        await interaction.response.send_message(
            f"â Du hast nicht genug **Bargeld**.\n"
            f"Preis: **{item['price']:,} ðµ** | Dein Bargeld: **{# replaced_user_data['cash']:,} ðµ**\n"
            f"â¹ï¸ KÃ¤ufe sind nur mit Bargeld mÃ¶glich. Hebe Geld mit `/auszahlen` ab.",
            ephemeral=True
        )
        return

    # replaced_user_data["cash"] -= item["price"]
    if "inventory" not in user_data:
        # replaced_user_data["inventory"] = []
    # replaced_user_data["inventory"].append(item["name"])
    save_economy(eco)

    embed = discord.Embed(
        title="â Gekauft!",
        description=(
            f"Du hast **{item['name']}** fÃ¼r **{item['price']:,} ðµ** gekauft.\n"
            f"**Verbleibendes Bargeld:** {# replaced_user_data['cash']:,} ðµ"
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
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    # replaced_user_data["custom_limit"] = limit
    save_economy(eco)

    embed = discord.Embed(
        title="âï¸ Limit gesetzt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Neues Tageslimit:** {limit:,} ðµ\n"
            f"*(gilt fÃ¼r Einzahlen, Auszahlen & Ãberweisen)*"
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
        await interaction.response.send_message("â Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("â Betrag muss grÃ¶Ãer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    # replaced_user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld hinzugefÃ¼gt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** +{betrag:,} ðµ\n"
        f"**Bargeld danach:** {# replaced_user_data['cash']:,} ðµ\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="ð° Geld hinzugefÃ¼gt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**HinzugefÃ¼gt:** {betrag:,} ðµ\n"
            f"**Bargeld:** {# replaced_user_data['cash']:,} ðµ"
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
        await interaction.response.send_message("â Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("â Betrag muss grÃ¶Ãer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    # replaced_user_data["cash"] = max(0, # replaced_user_data["cash"] - betrag)
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld entfernt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** -{betrag:,} ðµ\n"
        f"**Bargeld danach:** {# replaced_user_data['cash']:,} ðµ\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="ð¸ Geld entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernt:** {betrag:,} ðµ\n"
            f"**Bargeld:** {# replaced_user_data['cash']:,} ðµ"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /item-add (Admin only)
# BEHEBUNG 1: Nur Items aus dem Shop kÃ¶nnen vergeben werden
@bot.tree.command(name="item-add", description="[ADMIN] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", itemname="Itemname (muss im Shop vorhanden sein)")
@app_commands.autocomplete(itemname=shop_item_autocomplete)
@app_commands.default_permissions(administrator=True)
async def item_add(interaction: discord.Interaction, nutzer: discord.Member, itemname: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("â Kein Zugriff.", ephemeral=True)
        return

    # BEHEBUNG 1: PrÃ¼fen ob das Item im Shop existiert
    shop_items = load_shop()
    shop_item  = find_shop_item(shop_items, itemname)
    if not shop_item:
        await interaction.response.send_message(
            f"â Das Item **{itemname}** existiert nicht im Shop.\n"
            f"Es kÃ¶nnen nur vorhandene Shop-Items vergeben werden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    if "inventory" not in user_data:
        # replaced_user_data["inventory"] = []
    # replaced_user_data["inventory"].append(shop_item["name"])  # Offiziellen Shop-Namen verwenden
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="ð¦ Item hinzugefÃ¼gt",
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
        await interaction.response.send_message("â Kein Zugriff.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inventory = user_data.get("inventory", [])

    match = find_inventory_item(inventory, itemname)
    if not match:
        await interaction.response.send_message(
            f"â **{nutzer.display_name}** besitzt kein Item namens **{itemname}**.", ephemeral=True
        )
        return

    inventory.remove(match)
    # replaced_user_data["inventory"] = inventory
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="ð¦ Item entfernt",
            description=f"**{match}** wurde von **{nutzer.mention}** entfernt.",
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        ),
        ephemeral=True
    )


# /shop-add (Team only) with confirmation + optional role restriction
class ShopAddConfirmView(discord.ui.View):
    def __init__(self, name: str, price: int, allowed_role_id: int | None = None):
        super().__init__(timeout=60)
        self.name            = name
        self.price           = price
        self.allowed_role_id = allowed_role_id

    @discord.ui.button(label="â BestÃ¤tigen", style=discord.ButtonStyle.green)
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
                title="â Item hinzugefÃ¼gt",
                description=f"**{self.name}** fÃ¼r **{self.price:,} ðµ** wurde zum Shop hinzugefÃ¼gt.{rolle_info}",
                color=LOG_COLOR
            ),
            view=self
        )

    @discord.ui.button(label="â Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="â Abgebrochen",
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
        await interaction.response.send_message("â Kein Zugriff.", ephemeral=True)
        return

    if preis <= 0:
        await interaction.response.send_message("â Preis muss grÃ¶Ãer als 0 sein.", ephemeral=True)
        return

    rolle_info = f"\n**Nur fÃ¼r:** {rolle.mention}" if rolle else "\n**RollenbeschrÃ¤nkung:** Keine"
    embed = discord.Embed(
        title="ð Neues Item hinzufÃ¼gen?",
        description=(
            f"**Name:** {itemname}\n"
            f"**Preis:** {preis:,} ðµ"
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


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# WARN SYSTEM
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

# /warn (Team only)
@bot.tree.command(name="warn", description="[TEAM] Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
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
        title="â ï¸ Verwarnung",
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
        f"â Verwarnung fÃ¼r {nutzer.mention} gespeichert. (Warns gesamt: **{warn_count}**)", ephemeral=True
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
                title="ð Du wurdest getimeoutet",
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
            title="ð Automatischer Timeout",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Grund:** {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht\n"
                f"**Dauer:** 2 Tage\n"
                f"**Rollen entfernt:** â"
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
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"â {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        ts  = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** â {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"â ï¸ Warns von {nutzer.display_name}",
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
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"â¹ï¸ {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_warns(warns)

    embed = discord.Embed(
        title="â Verwarnung entfernt",
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
    is_team  = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids
    allowed  = is_team or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES)

    if nutzer is not None:
        if not is_team:
            await interaction.response.send_message(
                "â Du hast keine Berechtigung, den Rucksack anderer Spieler einzusehen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    else:
        if not is_team and interaction.channel.id != RUCKSACK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
            return
        if not allowed:
            await interaction.response.send_message("â Du hast keine Berechtigung.", ephemeral=True)
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
        desc   = "\n".join(f"â¢ **{item}** Ã{count}" for item, count in counts.items())

    embed = discord.Embed(
        title=f"ð Rucksack von {ziel.display_name}",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /Ã¼bergeben
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
        await interaction.response.send_message("â Du kannst nicht an dich selbst Ã¼bergeben.", ephemeral=True)
        return

    if menge < 1:
        await interaction.response.send_message("â Die Menge muss mindestens 1 sein.", ephemeral=True)
        return

    eco        = load_economy()
    giver_data = get_user(eco, interaction.user.id)
    inv        = giver_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if not match:
        await interaction.response.send_message(
            f"â **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        return

    # PrÃ¼fen ob genug vorhanden
    available = inv.count(match)
    if available < menge:
        await interaction.response.send_message(
            f"â Du hast nur **{available}Ã** **{match}** im Inventar, aber mÃ¶chtest **{menge}Ã** Ã¼bergeben.",
            ephemeral=True
        )
        return

    # Menge Ã¼bertragen
    for _ in range(menge):
        inv.remove(match)
    receiver_data = get_user(eco, nutzer.id)
    receiver_data.setdefault("inventory", []).extend([match] * menge)
    save_economy(eco)

    menge_text = f"Ã{menge}" if menge > 1 else ""
    embed = discord.Embed(
        title="ð¤ Item Ã¼bergeben",
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
            f"â **{item}** ist nicht in deinem Inventar.", ephemeral=True
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
        title="ðµï¸ Item versteckt",
        description=(
            f"**Item:** {match}\n"
            f"**Versteckt an:** {ort}\n\n"
            f"Nur du kannst es wieder herausnehmen."
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, view=view)


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# TEAM ITEM COMMANDS
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

# /item-geben (Team only)
# BEHEBUNG 1: Nur Items aus dem Shop kÃ¶nnen vergeben werden
@bot.tree.command(name="item-geben", description="[TEAM] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", item="Itemname (muss im Shop vorhanden sein)")
@app_commands.autocomplete(item=shop_item_autocomplete)
async def item_geben(interaction: discord.Interaction, nutzer: discord.Member, item: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
        return

    # BEHEBUNG 1: PrÃ¼fen ob das Item im Shop existiert
    shop_items = load_shop()
    shop_item  = find_shop_item(shop_items, item)
    if not shop_item:
        await interaction.response.send_message(
            f"â Das Item **{item}** existiert nicht im Shop.\n"
            f"Es kÃ¶nnen nur vorhandene Shop-Items vergeben werden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data.setdefault("inventory", []).append(shop_item["name"])  # Offiziellen Shop-Namen verwenden
    save_economy(eco)

    embed = discord.Embed(
        title="ð Item gegeben",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {shop_item['name']}\n"
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
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inv       = user_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if not match:
        await interaction.response.send_message(
            f"â **{item}** ist nicht im Inventar von {nutzer.mention}.", ephemeral=True
        )
        return

    inv.remove(match)
    save_economy(eco)

    embed = discord.Embed(
        title="ðï¸ Item entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {match}\n"
            f"**Entfernt von:** {interaction.user.mention}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# KARTENKONTROLLE
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

KARTENKONTROLLE_CHANNEL_ID = 1491116234459185162


@bot.tree.command(name="kartenkontrolle", description="[TEAM] Sendet eine DM-Erinnerung zur Kartenkontrolle an alle Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def kartenkontrolle(interaction: discord.Interaction):
    if not is_team(interaction.user):
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
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
                title="ðªª Kartenkontrolle",
                description=(
                    f"**Hallo {member.display_name}!**\n\n"
                    f"Es findet gerade eine **Kartenkontrolle** statt.\n"
                    f"Bitte begib dich in den Kanal:\n"
                    f"[ð Zur Kartenkontrolle]({channel_link})\n\n"
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
        f"â Kartenkontrolle-DM gesendet!\n**Erfolgreich:** {sent} | **Fehlgeschlagen (DMs zu):** {failed}",
        ephemeral=True
    )


# ââ Ausweis Helpers ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def load_ausweis():
    return safe_json_load(AUSWEIS_FILE, {})


def save_ausweis(data):
    safe_json_save(AUSWEIS_FILE, data)


def generate_ausweisnummer():
    letters = random.choices(string.ascii_uppercase, k=2)
    digits  = random.choices(string.digits, k=6)
    return "".join(letters) + "-" + "".join(digits)


# ââ Ausweis Chat-Eingabe ââââââââââââââââââââââââââââââââââââââââââââââââââââââ

async def collect_ausweis_via_chat(interaction: discord.Interaction, einreise_typ: str):
    """Sammelt alle Ausweisdaten Schritt fÃ¼r Schritt Ã¼ber den Chat."""
    channel = interaction.channel
    user    = interaction.user

    felder = [
        ("Vorname",      "z.B. `Max`"),
        ("Nachname",     "z.B. `Mustermann`"),
        ("Geburtsdatum", "z.B. `01.01.2000`"),
        ("Alter",        "z.B. `25`"),
        ("NationalitÃ¤t", "z.B. `Deutsch`"),
        ("Wohnort",      "z.B. `Los Santos`"),
    ]

    antworten   = {}
    zu_loeschen = []

    def check(m):
        return m.author.id == user.id and m.channel.id == channel.id

    for i, (feld, beispiel) in enumerate(felder, start=1):
        frage = await channel.send(
            f"{user.mention} ð **[{i}/{len(felder)}] {feld}** ({beispiel}):"
        )
        zu_loeschen.append(frage)

        try:
            antwort = await bot.wait_for("message", check=check, timeout=90.0)
            antworten[feld] = antwort.content.strip()
            zu_loeschen.append(antwort)
        except asyncio.TimeoutError:
            for m in zu_loeschen:
                try:
                    await m.delete()
                except Exception:
                    pass
            await channel.send(
                f"{user.mention} â Zeit abgelaufen. Bitte erneut versuchen.",
                delete_after=8
            )
            return

    # Alle Fragen & Antworten aufrÃ¤umen
    for m in zu_loeschen:
        try:
            await m.delete()
        except Exception:
            pass

    # Ausweis speichern
    ausweisnummer = generate_ausweisnummer()
    typ_label     = "ð¤µ Legale Einreise" if einreise_typ == "legal" else "ð¥· Illegale Einreise"

    ausweis_data = load_ausweis()
    ausweis_data[str(user.id)] = {
        "vorname":       antworten["Vorname"],
        "nachname":      antworten["Nachname"],
        "geburtsdatum":  antworten["Geburtsdatum"],
        "alter":         antworten["Alter"],
        "nationalitaet": antworten["NationalitÃ¤t"],
        "wohnort":       antworten["Wohnort"],
        "einreise_typ":  einreise_typ,
        "ausweisnummer": ausweisnummer,
        "discord_name":  str(user),
        "discord_id":    user.id,
    }
    save_ausweis(ausweis_data)

    # Rollen vergeben
    member = interaction.guild.get_member(user.id)
    if member:
        einreise_role = interaction.guild.get_role(
            LEGAL_ROLE_ID if einreise_typ == "legal" else ILLEGAL_ROLE_ID
        )
        if einreise_role:
            try:
                await member.add_roles(einreise_role, reason=f"Einreise: {einreise_typ}")
            except Exception:
                pass

        rollen_zu_vergeben = [
            interaction.guild.get_role(rid)
            for rid in CHARAKTER_ROLLEN
            if interaction.guild.get_role(rid) is not None
        ]
        if rollen_zu_vergeben:
            try:
                await member.add_roles(*rollen_zu_vergeben, reason="Charakter erstellt")
            except Exception:
                pass

    # BestÃ¤tigungs-Embed senden
    embed = discord.Embed(
        title="ðªª Ausweis ausgestellt",
        description="Dein Ausweis wurde erfolgreich erstellt!",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Name",          value=f"{antworten['Vorname']} {antworten['Nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum",  value=antworten["Geburtsdatum"],                          inline=True)
    embed.add_field(name="Alter",         value=antworten["Alter"],                                 inline=True)
    embed.add_field(name="NationalitÃ¤t",  value=antworten["NationalitÃ¤t"],                          inline=True)
    embed.add_field(name="Wohnort",       value=antworten["Wohnort"],                               inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                          inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{ausweisnummer}`",                               inline=False)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text="Kryptik Roleplay â Ausweis")
    try:
        await channel.send(user.mention, embed=embed)
    except Exception as e:
        await log_bot_error("collect_ausweis_via_chat BestÃ¤tigung Fehler", str(e), interaction.guild)


# ââ Einreise Select Menu ââââââââââââââââââââââââââââââââââââââââââââââââââââââ

class EinreiseSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Legale Einreise",
                emoji="ð¤µ",
                value="legal",
                description="Einreise als legaler Bewohner"
            ),
            discord.SelectOption(
                label="Illegale Einreise",
                emoji="ð¥·",
                value="illegal",
                description="Einreise als illegale Person"
            ),
        ]
        super().__init__(
            placeholder="âï¸ WÃ¤hle deine Einreiseart...",
            options=options,
            custom_id="einreise_select_main"
        )

    async def callback(self, interaction: discord.Interaction):
        member   = interaction.user
        role_ids = [r.id for r in member.roles]

        # PrÃ¼fen ob bereits eingereist
        if LEGAL_ROLE_ID in role_ids or ILLEGAL_ROLE_ID in role_ids:
            await interaction.response.send_message(
                "â Du hast bereits eine Einreiseart gewÃ¤hlt. Eine Ãnderung ist nur durch den RP-Tod mÃ¶glich.",
                ephemeral=True
            )
            return

        typ       = self.values[0]
        typ_label = "ð¤µ Legale Einreise" if typ == "legal" else "ð¥· Illegale Einreise"

        # Sofort antworten (Discord 3-Sekunden-Limit einhalten)
        await interaction.response.send_message(
            f"â Du hast **{typ_label}** gewÃ¤hlt!\n"
            "ð Ich stelle dir jetzt im Chat Fragen â beantworte jede mit einer Nachricht.\n"
            "Du hast jeweils **90 Sekunden** Zeit pro Frage.",
            ephemeral=True
        )

        # Chat-Eingabe als Hintergrund-Task starten
        asyncio.create_task(collect_ausweis_via_chat(interaction, typ))


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
            title="âï¸ Einreise â Kryptik Roleplay",
            description=(
                "ð¤µââï¸ **Legale Einreise** ð¤µââï¸\n"
                "Du wirst auf unserem Server als Legale Person einreisen. "
                "Du darfst als Legaler Bewohner keine Illegalen AktivitÃ¤ten ausfÃ¼hren.\n\n"
                "ð¥· **Illegale Einreise** ð¥·\n"
                "Du wirst auf unserem Server als Illegale Person einreisen. "
                "Du darfst keine Staatlichen Berufe ausÃ¼ben.\n\n"
                "â ï¸ **Hinweis** â ï¸\n"
                "Eine Ãnderung der Einreiseart ist nur durch den RP-Tod deines Charakters mÃ¶glich."
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Kryptik Roleplay â Einreisesystem")
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
            f"â Diesen Command kannst du nur in <#{AUSWEIS_CHANNEL_ID}> benutzen.", ephemeral=True
        )
        return

    ausweis_data = load_ausweis()
    entry = ausweis_data.get(str(interaction.user.id))

    if not entry:
        await interaction.response.send_message(
            "â Du hast noch keinen Ausweis. WÃ¤hle zuerst deine Einreiseart und erstelle deinen Ausweis.",
            ephemeral=True
        )
        return

    typ_label = "ð¤µ Legale Einreise" if entry.get("einreise_typ") == "legal" else "ð¥· Illegale Einreise"

    embed = discord.Embed(
        title="ðªª Personalausweis",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="Name",          value=f"{entry['vorname']} {entry['nachname']}",  inline=True)
    embed.add_field(name="Geburtsdatum",  value=entry["geburtsdatum"],                      inline=True)
    # BEHEBUNG 4: Alter wird korrekt angezeigt, auch bei alten Ausweisen ohne Alter-Feld
    embed.add_field(name="Alter",         value=entry.get("alter", "?"),                    inline=True)
    embed.add_field(name="NationalitÃ¤t",  value=entry["nationalitaet"],                     inline=True)
    embed.add_field(name="Wohnort",       value=entry["wohnort"],                           inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                  inline=True)
    embed.add_field(name="Ausweisnummer", value=f"``{entry['ausweisnummer']}``",        inline=False)
    embed.set_footer(text="Kryptik Roleplay â Personalausweis")

    await interaction.response.send_message(embed=embed)


# /ausweis-remove (Admin only)
@bot.tree.command(name="ausweis-remove", description="[ADMIN] Loescht den Ausweis eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler dessen Ausweis geloescht werden soll")
@app_commands.default_permissions(administrator=True)
async def ausweis_remove(interaction: discord.Interaction, nutzer: discord.Member):
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    uid = str(nutzer.id)

    if uid not in ausweis_data:
        await interaction.response.send_message(
            f"â {nutzer.mention} hat keinen Ausweis.", ephemeral=True
        )
        return

    del ausweis_data[uid]
    save_ausweis(ausweis_data)

    embed = discord.Embed(
        title="ðï¸ Ausweis gelÃ¶scht",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**GelÃ¶scht von:** {interaction.user.mention}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ââ Admin Ausweis-Erstellen Modal âââââââââââââââââââââââââââââââââââââââââââââ

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
        try:
            teile        = self.gebdatum_alter.value.split("/")
            geburtsdatum = teile[0].strip() if len(teile) >= 1 else self.gebdatum_alter.value.strip()
            alter        = teile[1].strip() if len(teile) >= 2 else "?"

            ausweisnummer = generate_ausweisnummer()
            typ_label     = "ð¤µ Legale Einreise" if self.einreise_typ == "legal" else "ð¥· Illegale Einreise"

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
                    except Exception:
                        pass

            embed = discord.Embed(
                title="ðªª Ausweis erstellt",
                color=0x000000,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Spieler",       value=target_mention,                                inline=False)
            embed.add_field(name="Name",          value=f"{self.vorname.value} {self.nachname.value}", inline=True)
            embed.add_field(name="Geburtsdatum",  value=geburtsdatum,                                  inline=True)
            # BEHEBUNG 4: Alter wird korrekt angezeigt
            embed.add_field(name="Alter",         value=alter,                                         inline=True)
            embed.add_field(name="Nationalitaet", value=self.nationalitaet.value,                      inline=True)
            embed.add_field(name="Wohnort",       value=self.wohnort.value,                            inline=True)
            embed.add_field(name="Einreiseart",   value=typ_label,                                     inline=True)
            embed.add_field(name="Ausweisnummer", value=f"`{ausweisnummer}`",                          inline=False)
            embed.set_footer(text=f"Erstellt von {interaction.user.display_name}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            err = traceback.format_exc()
            await log_bot_error("AusweisCreateModal on_submit Fehler", err, interaction.guild)
            try:
                await interaction.response.send_message(
                    "â Beim Erstellen des Ausweises ist ein Fehler aufgetreten. Bitte versuche es erneut.",
                    ephemeral=True
                )
            except Exception:
                pass

    # BEHEBUNG 4: on_error Handler verhindert den Discord "Anwendung antwortet nicht" Fehler
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        err = traceback.format_exc()
        await log_bot_error("AusweisCreateModal Fehler", err, interaction.guild)
        try:
            await interaction.response.send_message(
                "â Beim Erstellen des Ausweises ist ein Fehler aufgetreten. Bitte versuche es erneut.",
                ephemeral=True
            )
        except Exception:
            pass


class AusweisCreateEinreiseSelect(discord.ui.Select):
    def __init__(self, target_id: int):
        self.target_id = target_id
        options = [
            discord.SelectOption(label="Legale Einreise",   emoji="ð¤µ", value="legal"),
            discord.SelectOption(label="Illegale Einreise", emoji="ð¥·", value="illegal"),
        ]
        super().__init__(placeholder="Einreiseart wÃ¤hlen...", options=options)

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
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    if str(nutzer.id) in ausweis_data:
        await interaction.response.send_message(
            f"â {nutzer.mention} hat bereits einen Ausweis. Bitte zuerst mit /ausweis-remove loeschen.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"WÃ¤hle die Einreiseart fÃ¼r {nutzer.mention}:",
        view=AusweisCreateSelectView(nutzer.id),
        ephemeral=True
    )


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# !alina â Alina-Konversation (nur fÃ¼r bestimmte Rolle)
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

alina_sessions: dict = {}  # {(channel_id, user_id): True}

ALINA_ANTWORTEN = [
    "*leckt sich die Lippen und schaut dich gierig an* Oh ja, **\"{msg}\"** â genau das wollte ich hÃ¶ren, komm her du Kleiner ðð¥",
    "*schlÃ¤gt sich auf den Oberschenkel und lacht dreckig* **\"{msg}\"** fragst du?! Schatz, ich mach das und noch viel mehr~ ðð",
    "*beugt sich langsam vor, das Haar fÃ¤llt ihr ins Gesicht* Mmmh... **\"{msg}\"**... das klingt nach SpaÃ. Ich bin dabei. Wann fangen wir an? ð",
    "*wischt sich den Mund ab und grinst* Du willst wissen: **\"{msg}\"**? Alter, ich lebe dafÃ¼r. Komm einfach nÃ¤her~ ð¥µ",
    "*rollt genÃ¼sslich mit den Augen* **\"{msg}\"** â das Beste was mir heute jemand gefragt hat. Ja. Tausendmal ja. ð¦ð",
    "*lacht so laut dass die WÃ¤nde wackeln* **\"{msg}\"**?! Haha, Schatz, ich kenn da keine Grenzen â frag ruhig weiter ðð",
    "*tippt sich an die Lippe und denkt kurz nach* **\"{msg}\"**... weiÃt du was, ich zeig dir das lieber als es zu erklÃ¤ren~ ð¥",
    "*steht auf, streckt sich und zwinkert dir zu* **\"{msg}\"** â das ist genau mein Ding. Wir kÃ¶nnen sofort anfangen ð",
    "*flÃ¼stert* **\"{msg}\"**... ohhh das hÃ¶rt Alina gerne. Weiter so, SÃ¼Ãer~ ðð¥",
    "*kratzt sich am Bauch und grinst breit* **\"{msg}\"**? Alter, ich bin Alina â ich mach alles. ALLES. Vertrau mir ð",
]

ALINA_BELEIDIGUNGEN = [
    " Du bist zwar ein Vollidiot aber wenigstens stellst du die richtigen Fragen ð",
    " Ehrlich gesagt bist du so dumm wie Brot â aber niedlich ð",
    " Alter was bist du fÃ¼r ein Freak lmao~ aber ich mag das ð",
    " Du hast echt einen an der Waffel, oder? Passt zu mir ðð",
    " Manchmal frag ich mich wie du noch atmen kannst â aber hey, mehr fÃ¼r mich ð",
    " Du bist das Seltsamste was mir heute passiert ist. Und das ist ein Kompliment~ ð¤·",
]


class AlinaEndView(discord.ui.View):
    def __init__(self, user_id: int, channel_id: int):
        super().__init__(timeout=600)
        self.user_id    = user_id
        self.channel_id = channel_id

    @discord.ui.button(label="ð Chat beenden", style=discord.ButtonStyle.danger)
    async def end_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("â Das ist nicht dein Chat.", ephemeral=True)
            return
        alina_sessions.pop((self.channel_id, self.user_id), None)
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(
            "*Alina schnalzt mit der Zunge, dreht sich um und verschwindet hinter dem Vorhang* "
            "TschÃ¼ss SÃ¼Ãer~ War schÃ¶n mit dir ð"
        )
        self.stop()


async def handle_alina_message(message: discord.Message):
    if message.content.strip().lower().startswith("!alina"):
        return
    msg = message.content[:300]
    antwort = random.choice(ALINA_ANTWORTEN).format(msg=msg)
    if random.random() < 0.3:
        antwort += random.choice(ALINA_BELEIDIGUNGEN)
    embed = discord.Embed(description=antwort, color=0xff1493)
    embed.set_author(name="Alina ð")
    await message.channel.send(embed=embed, view=AlinaEndView(message.author.id, message.channel.id))


@bot.command(name="alina")
async def alina_cmd(ctx):
    if ALINA_ROLE_ID not in [r.id for r in ctx.author.roles]:
        try:
            await ctx.message.delete()
        except Exception:
            pass
        return

    key = (ctx.channel.id, ctx.author.id)
    if key in alina_sessions:
        await ctx.send(
            f"{ctx.author.mention} Du hast bereits eine aktive Alina-Session. Beende sie zuerst mit dem Button.",
            delete_after=6
        )
        return

    alina_sessions[key] = True
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        description=(
            "*Alina betritt den Raum, wischt sich SchweiÃ von der Stirn und grinst dich frech an*\n"
            "Na Schatz~ Ich bin Alina. Dick, haarig und fÃ¼r **alles** offen. Was willst du wissen? ðð"
        ),
        color=0xff1493
    )
    embed.set_author(name="Alina ð")
    embed.set_footer(text="Schreib einfach in den Chat â Alina antwortet. Button zum Beenden:")
    await ctx.send(embed=embed, view=AlinaEndView(ctx.author.id, ctx.channel.id))


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# /delete â Nachrichten lÃ¶schen (Team only)
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@bot.tree.command(name="delete", description="[TEAM] LÃ¶scht eine bestimmte Anzahl von Nachrichten im Kanal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(anzahl="Anzahl der zu lÃ¶schenden Nachrichten (max. 100)")
@app_commands.default_permissions(manage_messages=True)
async def delete_messages(interaction: discord.Interaction, anzahl: int):
    if not is_team(interaction.user):
        await interaction.response.send_message("â Keine Berechtigung.", ephemeral=True)
        return

    if anzahl < 1 or anzahl > 100:
        await interaction.response.send_message("â Bitte eine Zahl zwischen 1 und 100 angeben.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    geloescht = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(
        f"â **{len(geloescht)}** Nachrichten wurden gelÃ¶scht.",
        ephemeral=True
    )


# ââ Datensicherung ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

ALL_DATA_FILES = [
    ECONOMY_FILE,
    SHOP_FILE,
    WARNS_FILE,
    HIDDEN_ITEMS_FILE,
    AUSWEIS_FILE,
]


def backup_all_data():
    """Erstellt einen Snapshot aller Datendateien im backups/-Ordner."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = []
    for src in ALL_DATA_FILES:
        if src.exists():
            dst = BACKUP_DIR / f"{src.stem}_{ts}.json"
            try:
                shutil.copy2(src, dst)
                saved.append(src.name)
            except Exception as e:
                print(f"[BACKUP] Fehler beim Sichern von {src.name}: {e}")
    # Alte Backups aufrÃ¤umen: nur die letzten 10 je Datei behalten
    for src in ALL_DATA_FILES:
        old_backups = sorted(BACKUP_DIR.glob(f"{src.stem}_*.json"))
        for old in old_backups[:-10]:
            try:
                old.unlink()
            except Exception:
                pass
    if saved:
        print(f"[BACKUP] Gesichert: {', '.join(saved)}")


@tasks.loop(minutes=30)
async def auto_backup_task():
    """Automatischer Backup alle 30 Minuten."""
    try:
        backup_all_data()
    except Exception as e:
        print(f"[BACKUP] Auto-Backup Fehler: {e}")


def _shutdown_handler(signum, frame):
    """Beim Herunterfahren (SIGTERM/SIGINT) alle Daten nochmal sichern."""
    print("[SHUTDOWN] Signal empfangen â erstelle finalen Backup...")
    try:
        backup_all_data()
    except Exception as e:
        print(f"[SHUTDOWN] Backup-Fehler: {e}")
    print("[SHUTDOWN] Backup abgeschlossen. Bot wird beendet.")


signal.signal(signal.SIGTERM, _shutdown_handler)
signal.signal(signal.SIGINT,  _shutdown_handler)


token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
