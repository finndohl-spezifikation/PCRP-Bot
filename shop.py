# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# shop.py — 3-Shop-System (Kwik-E-Markt / Baumarkt / Schwarzmarkt)
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import is_admin
from economy_helpers import (
    load_economy, save_economy, get_user, load_shop, save_shop,
    find_shop_item, find_inventory_item, normalize_item_name,
    has_citizen_or_wage, shop_item_autocomplete, channel_error
)
from handy import give_handy_channel_access

# ── Konstanten ────────────────────────────────────────────────

_RUBBELLOS_NAME       = "🎟️| Rubbellos"
_RUBBELLOS_TAGESLIMIT = 3

SCHWARZMARKT_ROLE_ID = 1490855730767597738

SHOPS = {
    "kwik": {
        "label":   "🏪 Kwik-E-Markt",
        "emoji":   "🏪",
        "channel": 1490890311755628584,
    },
    "baumarkt": {
        "label":   "🔨 Baumarkt",
        "emoji":   "🔨",
        "channel": 1492976742497783818,
    },
    "schwarzmarkt": {
        "label":   "🕵️ Schwarzmarkt",
        "emoji":   "🕵️",
        "channel": 1492977067665526804,
    },
}

CHANNEL_TO_SHOP = {v["channel"]: k for k, v in SHOPS.items()}


# ── Hilfsfunktionen ───────────────────────────────────────────

def _has_schwarzmarkt_access(member: discord.Member) -> bool:
    role_ids = {r.id for r in member.roles}
    return bool(role_ids & {ADMIN_ROLE_ID, MOD_ROLE_ID, SCHWARZMARKT_ROLE_ID})


def _is_shop_admin(member: discord.Member) -> bool:
    role_ids = {r.id for r in member.roles}
    return bool(role_ids & {ADMIN_ROLE_ID, SHOP_ADMIN_ROLE_ID})


def _item_shop(item: dict) -> str:
    """Gibt den Shop-Key eines Items zurück; default: 'kwik' für alte Items."""
    return item.get("shop", "kwik")


def _build_shop_embed(shop_key: str, member: discord.Member) -> discord.Embed:
    shop    = SHOPS[shop_key]
    items   = load_shop()
    role_ids = {r.id for r in member.roles}
    is_adm  = ADMIN_ROLE_ID in role_ids

    filtered = [
        i for i in items
        if _item_shop(i) == shop_key
        and (is_adm or not i.get("allowed_role") or i.get("allowed_role") in role_ids)
    ]

    embed = discord.Embed(
        title=shop["label"],
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )

    if filtered:
        lines = []
        for item in filtered:
            line = f"**{item['name']}** — {item['price']:,} 💵"
            if item.get("allowed_role"):
                r = member.guild.get_role(item["allowed_role"])
                line += f" *(nur {r.mention if r else 'bestimmte Rolle'})*"
            lines.append(line)
        embed.description = "\n".join(lines)
    else:
        embed.description = "*Dieser Shop ist aktuell leer.*"

    embed.set_footer(text="Kaufen mit /buy [itemname] • Nur mit Bargeld möglich")
    return embed


# ── Shop-Auswahl Select ───────────────────────────────────────

class ShopSelectView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=60)

        options = []
        for key, cfg in SHOPS.items():
            if key == "schwarzmarkt" and not _has_schwarzmarkt_access(member):
                continue
            options.append(discord.SelectOption(
                label=cfg["label"],
                value=key,
                emoji=cfg["emoji"],
            ))

        select = discord.ui.Select(
            placeholder="Welchen Shop möchtest du öffnen?",
            options=options,
            custom_id="shop_select",
        )
        select.callback = self.on_select
        self.add_item(select)
        self.member = member

    async def on_select(self, interaction: discord.Interaction):
        shop_key = interaction.data["values"][0]
        shop_cfg = SHOPS[shop_key]
        is_adm   = ADMIN_ROLE_ID in {r.id for r in interaction.user.roles}

        # Schwarzmarkt-Berechtigungsprüfung
        if shop_key == "schwarzmarkt" and not _has_schwarzmarkt_access(interaction.user):
            await interaction.response.edit_message(
                embed=discord.Embed(
                    description="❌ Du hast keinen Zugang zum Schwarzmarkt.",
                    color=0xE74C3C
                ),
                view=None
            )
            return

        # Kanal-Check
        if not is_adm and interaction.channel.id != shop_cfg["channel"]:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=f"❌ Der **{shop_cfg['label']}** ist nur in <#{shop_cfg['channel']}> zugänglich.",
                    color=0xE74C3C
                ),
                view=None
            )
            return

        embed = _build_shop_embed(shop_key, interaction.user)
        await interaction.response.edit_message(embed=embed, view=None)


# ── /shop ─────────────────────────────────────────────────────

@bot.tree.command(
    name="shop",
    description="Öffne einen der Shops",
    guild=discord.Object(id=GUILD_ID)
)
async def shop(interaction: discord.Interaction):
    # Prüfen ob User überhaupt irgendeinen Shop öffnen darf
    is_adm = ADMIN_ROLE_ID in {r.id for r in interaction.user.roles}
    if not is_adm:
        shop_key = CHANNEL_TO_SHOP.get(interaction.channel.id)
        if not shop_key:
            channels = ", ".join(f"<#{v['channel']}>" for v in SHOPS.values())
            await interaction.response.send_message(
                f"❌ Der Shop ist nur in den Shop-Kanälen nutzbar: {channels}",
                ephemeral=True
            )
            return

    view = ShopSelectView(interaction.user)
    await interaction.response.send_message(
        embed=discord.Embed(
            title="🛒 Shop auswählen",
            description="Wähle unten aus, welchen Shop du öffnen möchtest.",
            color=LOG_COLOR
        ),
        view=view,
        ephemeral=True
    )


# ── /buy ──────────────────────────────────────────────────────

@bot.tree.command(
    name="buy",
    description="Kaufe ein Item aus dem Shop",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    itemname="Name des Items das du kaufen möchtest",
    menge="Wie viele möchtest du kaufen? (Standard: 1)"
)
async def buy(interaction: discord.Interaction, itemname: str, menge: int = 1):
    role_ids = {r.id for r in interaction.user.roles}
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if menge < 1:
        await interaction.response.send_message("❌ Die Menge muss mindestens **1** sein.", ephemeral=True)
        return
    if menge > 100:
        await interaction.response.send_message("❌ Du kannst maximal **100** Items auf einmal kaufen.", ephemeral=True)
        return

    items = load_shop()
    item  = find_shop_item(items, itemname)

    if not item:
        await interaction.response.send_message(
            f"❌ Item **{itemname}** wurde nicht gefunden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    # Kanal-Check: User muss im korrekten Shop-Kanal sein
    shop_key = _item_shop(item)
    shop_cfg = SHOPS.get(shop_key, SHOPS["kwik"])
    if not is_adm and interaction.channel.id != shop_cfg["channel"]:
        await interaction.response.send_message(
            f"❌ Dieses Item kann nur in <#{shop_cfg['channel']}> gekauft werden.",
            ephemeral=True
        )
        return

    # Schwarzmarkt-Zugang
    if shop_key == "schwarzmarkt" and not is_adm and not _has_schwarzmarkt_access(interaction.user):
        await interaction.response.send_message(
            "❌ Du hast keinen Zugang zum Schwarzmarkt.", ephemeral=True
        )
        return

    # Rollen-Check für Item
    allowed_role = item.get("allowed_role")
    if allowed_role and not is_adm and allowed_role not in role_ids:
        rolle_obj = interaction.guild.get_role(allowed_role)
        rname     = rolle_obj.name if rolle_obj else f"<@&{allowed_role}>"
        await interaction.response.send_message(
            f"❌ Dieses Item ist nur für die Rolle **{rname}** erhältlich.", ephemeral=True
        )
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)

    # Rubbellos-Tageslimit
    if normalize_item_name(item["name"]) == normalize_item_name(_RUBBELLOS_NAME) and not is_adm:
        today    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        rb_daily = user_data.get("rubbellos_daily", {"date": "", "count": 0})
        rb_count = rb_daily["count"] if rb_daily.get("date") == today else 0
        if rb_count + menge > _RUBBELLOS_TAGESLIMIT:
            verbleibend = max(0, _RUBBELLOS_TAGESLIMIT - rb_count)
            await interaction.response.send_message(
                f"❌ Du kannst nur **{_RUBBELLOS_TAGESLIMIT} Rubbellose pro Tag** kaufen.\n"
                f"Heute bereits gekauft: **{rb_count}** — noch kaufbar: **{verbleibend}**.",
                ephemeral=True
            )
            return

    gesamtpreis = item["price"] * menge
    if user_data["cash"] < gesamtpreis:
        await interaction.response.send_message(
            f"❌ Du hast nicht genug **Bargeld**.\n"
            f"Preis: **{item['price']:,} 💵** × {menge} = **{gesamtpreis:,} 💵** | "
            f"Dein Bargeld: **{user_data['cash']:,} 💵**\n"
            f"ℹ️ Käufe sind nur mit Bargeld möglich. Hebe Geld mit `/auszahlen` ab.",
            ephemeral=True
        )
        return

    user_data["cash"] -= gesamtpreis
    if "inventory" not in user_data:
        user_data["inventory"] = []
    for _ in range(menge):
        user_data["inventory"].append(item["name"])

    if normalize_item_name(item["name"]) == normalize_item_name(_RUBBELLOS_NAME):
        today    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        rb_daily = user_data.get("rubbellos_daily", {"date": "", "count": 0})
        rb_count = rb_daily["count"] if rb_daily.get("date") == today else 0
        user_data["rubbellos_daily"] = {"date": today, "count": rb_count + menge}

    save_economy(eco)

    if normalize_item_name(item["name"]) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, interaction.user)

    menge_text = f" × {menge}" if menge > 1 else ""
    embed = discord.Embed(
        title="✅ Gekauft!",
        description=(
            f"Du hast **{item['name']}**{menge_text} für **{gesamtpreis:,} 💵** gekauft.\n"
            f"**Verbleibendes Bargeld:** {user_data['cash']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# ── /shop-add ─────────────────────────────────────────────────

class ShopAddConfirmView(discord.ui.View):
    def __init__(self, name: str, price: int, shop_key: str, allowed_role_id=None):
        super().__init__(timeout=60)
        self.name            = name
        self.price           = price
        self.shop_key        = shop_key
        self.allowed_role_id = allowed_role_id

    @discord.ui.button(label="✅ Bestätigen", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = load_shop()
        entry = {"name": self.name, "price": self.price, "shop": self.shop_key}
        if self.allowed_role_id:
            entry["allowed_role"] = self.allowed_role_id
        items.append(entry)
        save_shop(items)
        for child in self.children:
            child.disabled = True
        rolle_info = ""
        if self.allowed_role_id:
            r = interaction.guild.get_role(self.allowed_role_id)
            rolle_info = f"\n**Nur für:** {r.mention if r else self.allowed_role_id}"
        shop_label = SHOPS[self.shop_key]["label"]
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Item hinzugefügt",
                description=(
                    f"**{self.name}** für **{self.price:,} 💵** wurde zum "
                    f"**{shop_label}** hinzugefügt.{rolle_info}"
                ),
                color=LOG_COLOR
            ),
            view=self
        )

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="❌ Abgebrochen",
                description="Das Item wurde nicht hinzugefügt.",
                color=MOD_COLOR
            ),
            view=self
        )


@bot.tree.command(
    name="shop-add",
    description="[Shop] Füge ein neues Item zu einem Shop hinzu (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    itemname="Name des Items",
    preis="Preis in $",
    shop="Welcher Shop: kwik / baumarkt / schwarzmarkt",
    rolle="(Optional) Nur diese Rolle kann das Item kaufen"
)
@app_commands.choices(shop=[
    app_commands.Choice(name="🏪 Kwik-E-Markt",  value="kwik"),
    app_commands.Choice(name="🔨 Baumarkt",       value="baumarkt"),
    app_commands.Choice(name="🕵️ Schwarzmarkt",  value="schwarzmarkt"),
])
async def shop_add(
    interaction: discord.Interaction,
    itemname: str,
    preis: int,
    shop: str,
    rolle: discord.Role = None
):
    if not _is_shop_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    if preis <= 0:
        await interaction.response.send_message("❌ Preis muss größer als 0 sein.", ephemeral=True)
        return

    shop_label = SHOPS[shop]["label"]
    rolle_info = f"\n**Nur für:** {rolle.mention}" if rolle else "\n**Rollenbeschränkung:** Keine"
    embed = discord.Embed(
        title="🛒 Neues Item hinzufügen?",
        description=(
            f"**Name:** {itemname}\n"
            f"**Preis:** {preis:,} 💵\n"
            f"**Shop:** {shop_label}"
            f"{rolle_info}\n\n"
            "Bitte bestätige das Hinzufügen."
        ),
        color=LOG_COLOR
    )
    await interaction.response.send_message(
        embed=embed,
        view=ShopAddConfirmView(itemname, preis, shop, rolle.id if rolle else None),
        ephemeral=True
    )


# ── /shop-edit ────────────────────────────────────────────────

@bot.tree.command(
    name="shop-edit",
    description="[Shop] Bearbeite ein bestehendes Item (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    itemname="Name des Items das bearbeitet werden soll",
    neuer_preis="Neuer Preis in $ (leer lassen um nicht zu ändern)",
    neuer_name="Neuer Name des Items (leer lassen um nicht zu ändern)"
)
@app_commands.autocomplete(itemname=shop_item_autocomplete)
async def shop_edit(
    interaction: discord.Interaction,
    itemname: str,
    neuer_preis: int = None,
    neuer_name: str = None
):
    if not _is_shop_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    if neuer_preis is None and neuer_name is None:
        await interaction.response.send_message(
            "❌ Bitte gib einen neuen Preis oder einen neuen Namen an.", ephemeral=True
        )
        return

    items     = load_shop()
    shop_item = find_shop_item(items, itemname)

    if not shop_item:
        await interaction.response.send_message(
            f"❌ Item **{itemname}** wurde nicht gefunden.", ephemeral=True
        )
        return

    changes = []
    if neuer_preis is not None:
        if neuer_preis <= 0:
            await interaction.response.send_message("❌ Preis muss größer als 0 sein.", ephemeral=True)
            return
        old_price           = shop_item["price"]
        shop_item["price"]  = neuer_preis
        changes.append(f"**Preis:** {old_price:,} 💵 → {neuer_preis:,} 💵")

    if neuer_name:
        old_name           = shop_item["name"]
        shop_item["name"]  = neuer_name
        # Auch in Inventaren aktualisieren
        eco = load_economy()
        for uid, udata in eco.items():
            udata["inventory"] = [
                neuer_name if i == old_name else i
                for i in udata.get("inventory", [])
            ]
        save_economy(eco)
        changes.append(f"**Name:** {old_name} → {neuer_name}")

    save_shop(items)

    embed = discord.Embed(
        title="✏️ Item bearbeitet",
        description="\n".join(changes),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Bearbeitet von {interaction.user}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /delete-item ──────────────────────────────────────────────

@bot.tree.command(
    name="delete-item",
    description="[Shop] Entfernt ein Item aus dem Shop (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
@app_commands.describe(itemname="Name des Items das entfernt werden soll")
@app_commands.autocomplete(itemname=shop_item_autocomplete)
async def delete_item(interaction: discord.Interaction, itemname: str):
    if not _is_shop_admin(interaction.user):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    items     = load_shop()
    shop_item = find_shop_item(items, itemname)

    if not shop_item:
        await interaction.response.send_message(
            f"❌ Das Item **{itemname}** wurde nicht gefunden.", ephemeral=True
        )
        return

    items.remove(shop_item)
    save_shop(items)

    item_name       = shop_item["name"]
    eco             = load_economy()
    players_cleaned = 0
    total_removed   = 0
    for uid, user_data in eco.items():
        inv    = user_data.get("inventory", [])
        before = len(inv)
        user_data["inventory"] = [i for i in inv if i != item_name]
        removed = before - len(user_data["inventory"])
        if removed > 0:
            players_cleaned += 1
            total_removed   += removed
    save_economy(eco)

    embed = discord.Embed(
        title="🗑️ Item aus Shop entfernt",
        description=(
            f"**Item:** {item_name}\n"
            f"**Shop:** {SHOPS.get(_item_shop(shop_item), SHOPS['kwik'])['label']}\n"
            f"**Preis war:** {shop_item['price']:,} 💵\n"
            f"**Entfernt von:** {interaction.user.mention}\n\n"
            f"**Inventare bereinigt:** {players_cleaned} Spieler\n"
            f"**Items entfernt:** {total_removed}x"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
