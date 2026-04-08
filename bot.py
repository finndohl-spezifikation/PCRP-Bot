import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import uuid
from datetime import datetime, timezone, timedelta
from collections import Counter

# ═══════════════════════════════════════════════════════════════════════
# KONFIGURATION – IDs hier eintragen
# ═══════════════════════════════════════════════════════════════════════

GUILD_ID                = 0      # TODO: Server-ID
ADMIN_ROLE_ID           = 0      # TODO: Admin-Rolle
MOD_ROLE_ID             = 0      # TODO: Moderator-Rolle
CITIZEN_ROLE_ID         = 0      # TODO: Bürger-Rolle
WAGE_ROLES              = []     # TODO: Liste der Lohn-Rollen-IDs

LOG_COLOR               = discord.Color.from_rgb(88, 101, 242)
MOD_COLOR               = discord.Color.from_rgb(237, 66, 69)

MONEY_LOG_CHANNEL_ID    = 0      # TODO: Kanal für Geld-Logs
WARN_LOG_CHANNEL_ID     = 0      # TODO: Kanal für Warn-Logs
SHOP_CHANNEL_ID         = 0      # TODO: Kanal für den Shop
EINZAHLEN_CHANNEL_ID    = 0      # TODO: Kanal für /einzahlen
AUSZAHLEN_CHANNEL_ID    = 0      # TODO: Kanal für /auszahlen
UEBERWEISEN_CHANNEL_ID  = 0      # TODO: Kanal für /ueberweisen
RUCKSACK_CHANNEL_ID     = 0      # TODO: Kanal für /rucksack
UEBERGEBEN_CHANNEL_ID   = 0      # TODO: Kanal für /uebergeben
VERSTECKEN_CHANNEL_ID   = 0      # TODO: Kanal für /verstecken

WARN_AUTO_TIMEOUT_COUNT = 3
DEFAULT_DAILY_LIMIT     = 5000   # Standard-Tageslimit für Überweisungen

LIMIT_CHOICES = [
    app_commands.Choice(name="500 $",    value=500),
    app_commands.Choice(name="1.000 $",  value=1000),
    app_commands.Choice(name="2.000 $",  value=2000),
    app_commands.Choice(name="5.000 $",  value=5000),
    app_commands.Choice(name="10.000 $", value=10000),
]

# ═══════════════════════════════════════════════════════════════════════
# DATENHALTUNG
# ═══════════════════════════════════════════════════════════════════════

ECONOMY_FILE = "economy.json"
WARNS_FILE   = "warns.json"
SHOP_FILE    = "shop.json"
HIDDEN_FILE  = "hidden_items.json"


def _load_json(path: str, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_economy() -> dict:
    return _load_json(ECONOMY_FILE, {})


def save_economy(data: dict) -> None:
    _save_json(ECONOMY_FILE, data)


def get_user(eco: dict, user_id: int) -> dict:
    key = str(user_id)
    if key not in eco:
        eco[key] = {
            "cash": 0,
            "bank": 0,
            "inventory": [],
            "custom_limit": None,
            "today_transferred": 0,
            "transfer_date": "",
        }
    return eco[key]


def load_warns() -> dict:
    return _load_json(WARNS_FILE, {})


def save_warns(data: dict) -> None:
    _save_json(WARNS_FILE, data)


def get_user_warns(warns: dict, user_id: int) -> list:
    key = str(user_id)
    if key not in warns:
        warns[key] = []
    return warns[key]


def load_shop() -> list:
    return _load_json(SHOP_FILE, [])


def save_shop(data: list) -> None:
    _save_json(SHOP_FILE, data)


def load_hidden_items() -> list:
    return _load_json(HIDDEN_FILE, [])


def save_hidden_items(data: list) -> None:
    _save_json(HIDDEN_FILE, data)


# ═══════════════════════════════════════════════════════════════════════
# BOT SETUP
# ═══════════════════════════════════════════════════════════════════════

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ═══════════════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════

def is_admin(user: discord.Member) -> bool:
    return ADMIN_ROLE_ID in [r.id for r in user.roles]


def is_team(user: discord.Member) -> bool:
    role_ids = [r.id for r in user.roles]
    return ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids


def channel_error(channel_id: int) -> str:
    return f"❌ Dieser Befehl kann nur in <#{channel_id}> verwendet werden."


async def log_money_action(guild: discord.Guild, title: str, description: str) -> None:
    ch = guild.get_channel(MONEY_LOG_CHANNEL_ID)
    if ch:
        await ch.send(embed=discord.Embed(
            title=title,
            description=description,
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        ))


# ═══════════════════════════════════════════════════════════════════════
# VIEWS (persistent)
# ═══════════════════════════════════════════════════════════════════════

class VersteckRetrieveView(discord.ui.View):
    def __init__(self, item_id: str, owner_id: int):
        super().__init__(timeout=None)
        self.item_id  = item_id
        self.owner_id = owner_id
        btn = discord.ui.Button(
            label="📦 Item herausnehmen",
            style=discord.ButtonStyle.green,
            custom_id=f"versteck_{item_id}",
        )
        btn.callback = self._retrieve_callback
        self.add_item(btn)

    async def _retrieve_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Das ist nicht dein verstecktes Item.", ephemeral=True
            )
            return

        hidden = load_hidden_items()
        entry  = next((h for h in hidden if h["id"] == self.item_id), None)
        if not entry:
            await interaction.response.send_message(
                "❌ Dieses Item existiert nicht mehr.", ephemeral=True
            )
            return

        hidden.remove(entry)
        save_hidden_items(hidden)

        eco       = load_economy()
        user_data = get_user(eco, interaction.user.id)
        user_data.setdefault("inventory", []).append(entry["item"])
        save_economy(eco)

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="📦 Item zurückgeholt",
                description=f"**{entry['item']}** ist wieder in deinem Rucksack.",
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            ),
            view=self
        )


# ═══════════════════════════════════════════════════════════════════════
# ON READY
# ═══════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    hidden = load_hidden_items()
    for entry in hidden:
        bot.add_view(VersteckRetrieveView(entry["id"], entry["owner_id"]))
    print(f"✅ Bot eingeloggt als {bot.user}")


# ═══════════════════════════════════════════════════════════════════════
# WIRTSCHAFT – EINZAHLEN / AUSZAHLEN / UEBERWEISEN
# ═══════════════════════════════════════════════════════════════════════

# /einzahlen
@bot.tree.command(name="einzahlen", description="Zahle Bargeld auf dein Bankkonto ein", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag in $")
async def einzahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids
    allowed  = is_adm or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES) or MOD_ROLE_ID in role_ids

    if not allowed:
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if not is_adm and interaction.channel.id != EINZAHLEN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(EINZAHLEN_CHANNEL_ID), ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)

    if user_data["cash"] < betrag:
        await interaction.response.send_message(
            f"❌ Du hast nicht genug Bargeld. Dein Bargeld: **{user_data['cash']:,} 💵**",
            ephemeral=True
        )
        return

    user_data["cash"] -= betrag
    user_data["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Einzahlung",
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** +{betrag:,} 💵\n"
        f"**Guthaben danach:** {user_data['bank']:,} 💵"
    )

    embed = discord.Embed(
        title="🏦 Einzahlung erfolgreich",
        description=(
            f"**Eingezahlt:** {betrag:,} 💵\n"
            f"**Neues Bargeld:** {user_data['cash']:,} 💵\n"
            f"**Neues Guthaben:** {user_data['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /auszahlen
@bot.tree.command(name="auszahlen", description="Hebe Geld von deinem Bankkonto ab", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag in $")
async def auszahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids
    allowed  = is_adm or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES) or MOD_ROLE_ID in role_ids

    if not allowed:
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if not is_adm and interaction.channel.id != AUSZAHLEN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(AUSZAHLEN_CHANNEL_ID), ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)

    if user_data["bank"] < betrag:
        await interaction.response.send_message(
            f"❌ Dein Guthaben reicht nicht aus. Dein Guthaben: **{user_data['bank']:,} 💵**",
            ephemeral=True
        )
        return

    user_data["bank"] -= betrag
    user_data["cash"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Auszahlung",
        f"**Spieler:** {interaction.user.mention}\n**Betrag:** -{betrag:,} 💵\n"
        f"**Bargeld danach:** {user_data['cash']:,} 💵"
    )

    embed = discord.Embed(
        title="💵 Auszahlung erfolgreich",
        description=(
            f"**Ausgezahlt:** {betrag:,} 💵\n"
            f"**Neues Bargeld:** {user_data['cash']:,} 💵\n"
            f"**Neues Guthaben:** {user_data['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /ueberweisen
@bot.tree.command(name="ueberweisen", description="Überweise Bargeld an einen anderen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Empfänger", betrag="Betrag in $")
async def ueberweisen(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids
    allowed  = is_adm or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES) or MOD_ROLE_ID in role_ids

    if not allowed:
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if not is_adm and interaction.channel.id != UEBERWEISEN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(UEBERWEISEN_CHANNEL_ID), ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("❌ Du kannst nicht an dich selbst überweisen.", ephemeral=True)
        return

    eco       = load_economy()
    sender    = get_user(eco, interaction.user.id)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if sender.get("transfer_date", "") != today_str:
        sender["today_transferred"] = 0
        sender["transfer_date"]     = today_str

    daily_limit = sender.get("custom_limit") or DEFAULT_DAILY_LIMIT
    remaining   = daily_limit - sender.get("today_transferred", 0)

    if betrag > remaining:
        await interaction.response.send_message(
            f"❌ Tageslimit überschritten.\n"
            f"**Tageslimit:** {daily_limit:,} 💵 | **Noch verfügbar:** {remaining:,} 💵",
            ephemeral=True
        )
        return

    if sender["cash"] < betrag:
        await interaction.response.send_message(
            f"❌ Du hast nicht genug Bargeld. Dein Bargeld: **{sender['cash']:,} 💵**",
            ephemeral=True
        )
        return

    receiver                    = get_user(eco, nutzer.id)
    sender["cash"]             -= betrag
    sender["today_transferred"] = sender.get("today_transferred", 0) + betrag
    receiver["cash"]           += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Überweisung",
        f"**Von:** {interaction.user.mention}\n**An:** {nutzer.mention}\n"
        f"**Betrag:** {betrag:,} 💵\n"
        f"**Verbleibend heute:** {daily_limit - sender['today_transferred']:,} 💵"
    )

    embed = discord.Embed(
        title="💸 Überweisung erfolgreich",
        description=(
            f"**An:** {nutzer.mention}\n"
            f"**Betrag:** {betrag:,} 💵\n"
            f"**Dein Bargeld:** {sender['cash']:,} 💵\n"
            f"**Noch heute übertragbar:** {daily_limit - sender['today_transferred']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════
# SHOP
# ═══════════════════════════════════════════════════════════════════════

# /kaufen
@bot.tree.command(name="kaufen", description="Kaufe ein Item aus dem Shop", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(itemname="Name des Items")
async def kaufen(interaction: discord.Interaction, itemname: str):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids
    allowed  = is_adm or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES) or MOD_ROLE_ID in role_ids

    if not allowed:
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        return

    items      = load_shop()
    item_lower = itemname.lower()
    item       = next((i for i in items if i["name"].lower() == item_lower), None)

    if not item:
        await interaction.response.send_message(
            f"❌ **{itemname}** ist nicht im Shop.", ephemeral=True
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
        counts = Counter(inventory)
        desc   = "\n".join(f"• **{item}** ×{count}" for item, count in counts.items())

    embed = discord.Embed(
        title=f"🎒 Rucksack von {interaction.user.display_name}",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /uebergeben
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


token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
