# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# economy_helpers.py — Economy, Shop, Inventar Hilfsfunktionen
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import log_bot_error


# ── Economy Helpers ──────────────────────────────────────────

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


# ── Shop Helpers ─────────────────────────────────────────────

def load_shop():
    if SHOP_FILE.exists():
        with open(SHOP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_shop(items):
    with open(SHOP_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


# ── Hidden Items Helpers ─────────────────────────────────────

def load_hidden_items():
    if HIDDEN_ITEMS_FILE.exists():
        with open(HIDDEN_ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_hidden_items(data):
    with open(HIDDEN_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Counting Helpers ─────────────────────────────────────────

def load_counting_state():
    if COUNTING_FILE.exists():
        with open(COUNTING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    return {"count": 0, "last_user_id": None}


def save_counting_state(state):
    with open(COUNTING_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


counting_state = load_counting_state()


# ── Abstimmung Helpers ───────────────────────────────────────

def load_abstimmung():
    if ABSTIMMUNG_FILE.exists():
        with open(ABSTIMMUNG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_abstimmung(data):
    with open(ABSTIMMUNG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


abstimmung_polls = load_abstimmung()


def make_progress_bar(count: int, total: int, width: int = 20) -> str:
    if total == 0:
        filled = 0
    else:
        filled = round(count / total * width)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def build_abstimmung_embed(poll: dict) -> discord.Embed:
    g_count = len(poll["green_voters"])
    r_count = len(poll["red_voters"])
    total   = g_count + r_count

    g_pct    = round(g_count / total * 100) if total > 0 else 0
    r_pct    = round(r_count / total * 100) if total > 0 else 0
    g_bar    = make_progress_bar(g_count, total)
    r_bar    = make_progress_bar(r_count, total)

    description = (
        f"✅ **{poll['option_ja']}** — {g_count} Stimme(n)\n"
        f"`{g_bar}` **{g_pct}%**\n\n"
        f"❌ **{poll['option_nein']}** — {r_count} Stimme(n)\n"
        f"`{r_bar}` **{r_pct}%**\n\n"
        f"👥 **Gesamt:** {total} Abstimmung(en)"
    )
    embed = discord.Embed(
        title=f"🗳️ Abstimmung — {poll['question']}",
        description=description,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay • Abstimmungs-System")
    return embed


# ── Normalisierungsfunktion für Item-Namen ───────────────────

def normalize_item_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[\|\-\_]+', ' ', name)
    name = ''.join(c for c in name if c.isalnum() or c.isspace())
    return re.sub(r'\s+', ' ', name).strip()


# ── Handy Helpers ────────────────────────────────────────────

def load_handy_numbers():
    if HANDY_FILE.exists():
        with open(HANDY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_handy_numbers(data):
    with open(HANDY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_la_phone_number():
    area_codes = ["213", "310", "323", "424", "562", "626", "747", "818"]
    area = random.choice(area_codes)
    num1 = random.randint(200, 999)
    num2 = random.randint(1000, 9999)
    return f"+1 ({area}) {num1}-{num2}"


def has_citizen_or_wage(member: discord.Member) -> bool:
    role_ids = [r.id for r in member.roles]
    return CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES)


def has_handy(member):
    eco = load_economy()
    user_data = get_user(eco, member.id)
    inventory = user_data.get("inventory", [])
    norm_handy = normalize_item_name(HANDY_ITEM_NAME)
    return any(norm_handy in normalize_item_name(i) for i in inventory)


def has_sim_karte(member):
    eco = load_economy()
    user_data = get_user(eco, member.id)
    inventory = user_data.get("inventory", [])
    norm_sim = normalize_item_name("Sim Karte")
    return any(norm_sim in normalize_item_name(i) for i in inventory)


def consume_sim_karte(member) -> bool:
    """Entfernt genau eine SIM-Karte aus dem Inventar. Gibt True zurück wenn erfolgreich."""
    eco = load_economy()
    user_data = get_user(eco, member.id)
    inventory = user_data.get("inventory", [])
    norm_sim  = normalize_item_name("Sim Karte")
    for idx, item in enumerate(inventory):
        if norm_sim in normalize_item_name(item):
            inventory.pop(idx)
            user_data["inventory"] = inventory
            eco[str(member.id)] = user_data
            save_economy(eco)
            return True
    return False


def has_item(member, item_query: str) -> bool:
    """Prüft ob member ein Item mit dem Namen item_query im Inventar hat."""
    eco = load_economy()
    user_data = get_user(eco, member.id)
    inventory = user_data.get("inventory", [])
    norm_q = normalize_item_name(item_query)
    return any(norm_q in normalize_item_name(i) for i in inventory)


def consume_item(member, item_query: str) -> bool:
    """Entfernt genau eine Kopie von item_query aus dem Inventar. True = erfolgreich."""
    eco = load_economy()
    user_data = get_user(eco, member.id)
    inventory = user_data.get("inventory", [])
    norm_q = normalize_item_name(item_query)
    for idx, item in enumerate(inventory):
        if norm_q in normalize_item_name(item):
            inventory.pop(idx)
            user_data["inventory"] = inventory
            eco[str(member.id)] = user_data
            save_economy(eco)
            return True
    return False


# ── Money Log Helper ─────────────────────────────────────────

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


# ── Betrag Autocomplete ─────────────────────────────────────

BETRAG_SUGGESTIONS = [
    1_000, 5_000, 10_000, 25_000, 50_000,
    100_000, 250_000, 500_000, 1_000_000,
    2_000_000, 5_000_000, 10_000_000
]


async def betrag_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    choices = []
    clean = current.replace(".", "").replace(",", "").strip()
    for val in BETRAG_SUGGESTIONS:
        label = f"{val:,} 💵".replace(",", ".")
        if clean == "" or clean in str(val) or clean.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=val))
    return choices[:25]


# ── Shop-Item Autocomplete ──────────────────────────────────

async def shop_item_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    items = load_shop()
    current_lower = current.lower()
    choices = []
    for item in items:
        name = item["name"]
        if current_lower == "" or current_lower in name.lower():
            choices.append(app_commands.Choice(name=name, value=name))
    return choices[:25]


# ── Inventar-Item Autocomplete ───────────────────────────────

async def inventory_item_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    from collections import Counter
    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    inventory = user_data.get("inventory", [])
    counts    = Counter(inventory)
    current_lower = current.lower()
    choices = []
    for item_name, count in counts.items():
        label = f"{item_name} (×{count})"
        if current_lower == "" or current_lower in item_name.lower():
            choices.append(app_commands.Choice(name=label, value=item_name))
    return choices[:25]


# ── Versteck-Button (persistent) ─────────────────────────────

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
            f"✅ **{entry['item']}** wurde aus dem Versteck (**{entry['location']}**) geholt.",
            ephemeral=True
        )

        embed_public = discord.Embed(
            title="📦 Item aus Versteck geholt",
            description=(
                f"{interaction.user.mention} hat **{entry['item']}** "
                f"aus dem Versteck an **{entry['location']}** geholt."
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await interaction.channel.send(embed=embed_public)
        except Exception:
            pass

        if IC_CHAT_CHANNEL_ID:
            ic_channel = interaction.guild.get_channel(IC_CHAT_CHANNEL_ID)
            if ic_channel:
                embed = discord.Embed(
                    title="🕵️ IC — Item aus Versteck geholt",
                    description=(
                        f"**{interaction.user.display_name}** hat **{entry['item']}** "
                        f"aus dem Versteck an **{entry['location']}** geholt."
                    ),
                    color=0xFFA500,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text=f"Nutzer: {interaction.user} • ID: {interaction.user.id}")
                try:
                    await ic_channel.send(embed=embed)
                except Exception:
                    pass


# ── Warn Helpers ─────────────────────────────────────────────

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


# ── Shop/Inventar Suchfunktionen ────────────────────────────

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


def channel_error(channel_id: int) -> str:
    return f"❌ Du kannst diesen Command nur hier ausführen: <#{channel_id}>"
