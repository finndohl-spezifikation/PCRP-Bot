# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# shop.py — Shop System (Anzeigen, Kaufen, Hinzufügen, Löschen)
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import is_admin
from economy_helpers import (
    load_economy, save_economy, get_user, load_shop, save_shop,
    find_shop_item, find_inventory_item, normalize_item_name,
    has_citizen_or_wage, shop_item_autocomplete, channel_error
)
from handy import give_handy_channel_access


# /shop
@bot.tree.command(name="shop", description="[Shop] Zeigt den Shop an", guild=discord.Object(id=GUILD_ID))
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

    lines = []
    for item in items:
        line = f"**{item['name']}** — {item['price']:,} 💵"
        ar = item.get("allowed_role")
        if ar:
            r = interaction.guild.get_role(ar)
            line += f"  🔒 *{r.name if r else ar}*"
        lines.append(line)

    embed = discord.Embed(
        title="🛒 Shop",
        description="\n".join(lines),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Kaufen mit /buy [itemname] • Nur mit Bargeld möglich")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /buy
@bot.tree.command(name="buy", description="[Shop] Kaufe ein Item aus dem Shop", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    itemname="Name des Items das du kaufen möchtest",
    menge="Wie viele möchtest du kaufen? (Standard: 1)"
)
async def buy(interaction: discord.Interaction, itemname: str, menge: int = 1):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(channel_error(SHOP_CHANNEL_ID), ephemeral=True)
        return

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

    allowed_role = item.get("allowed_role")
    if allowed_role and not is_adm:
        if allowed_role not in role_ids:
            rolle_obj = interaction.guild.get_role(allowed_role)
            rname     = rolle_obj.name if rolle_obj else f"<@&{allowed_role}>"
            await interaction.response.send_message(
                f"❌ Dieses Item ist nur für die Rolle **{rname}** erhältlich.",
                ephemeral=True
            )
            return

    eco        = load_economy()
    user_data  = get_user(eco, interaction.user.id)
    gesamtpreis = item["price"] * menge

    if user_data["cash"] < gesamtpreis:
        await interaction.response.send_message(
            f"❌ Du hast nicht genug **Bargeld**.\n"
            f"Preis: **{item['price']:,} 💵** × {menge} = **{gesamtpreis:,} 💵** | Dein Bargeld: **{user_data['cash']:,} 💵**\n"
            f"ℹ️ Käufe sind nur mit Bargeld möglich. Hebe Geld mit `/auszahlen` ab.",
            ephemeral=True
        )
        return

    user_data["cash"] -= gesamtpreis
    if "inventory" not in user_data:
        user_data["inventory"] = []
    for _ in range(menge):
        user_data["inventory"].append(item["name"])
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


# /shop-add (Team only)
class ShopAddConfirmView(discord.ui.View):
    def __init__(self, name: str, price: int, allowed_role_id: int | None = None):
        super().__init__(timeout=60)
        self.name            = name
        self.price           = price
        self.allowed_role_id = allowed_role_id

    @discord.ui.button(label="✅ Bestätigen", style=discord.ButtonStyle.green)
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
            rolle_info = f"\n**Nur für:** {r.mention if r else self.allowed_role_id}"
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Item hinzugefügt",
                description=f"**{self.name}** für **{self.price:,} 💵** wurde zum Shop hinzugefügt.{rolle_info}",
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


@bot.tree.command(name="shop-add", description="[Shop] Füge ein neues Item zum Shop hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    itemname="Name des Items",
    preis="Preis in $",
    rolle="(Optional) Nur diese Rolle kann das Item kaufen"
)
async def shop_add(interaction: discord.Interaction, itemname: str, preis: int, rolle: discord.Role = None):
    if not any(r.id in (SHOP_ADMIN_ROLE_ID, ADMIN_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    if preis <= 0:
        await interaction.response.send_message("❌ Preis muss größer als 0 sein.", ephemeral=True)
        return

    rolle_info = f"\n**Nur für:** {rolle.mention}" if rolle else "\n**Rollenbeschränkung:** Keine"
    embed = discord.Embed(
        title="🛒 Neues Item hinzufügen?",
        description=(
            f"**Name:** {itemname}\n"
            f"**Preis:** {preis:,} 💵"
            f"{rolle_info}\n\n"
            f"Bitte bestätige das Hinzufügen."
        ),
        color=LOG_COLOR
    )
    await interaction.response.send_message(
        embed=embed,
        view=ShopAddConfirmView(itemname, preis, rolle.id if rolle else None),
        ephemeral=True
    )


# /delete-item (Team only)
@bot.tree.command(name="delete-item", description="[Shop] Entfernt ein Item aus dem Shop", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(itemname="Name des Items das aus dem Shop entfernt werden soll")
@app_commands.autocomplete(itemname=shop_item_autocomplete)
async def delete_item(interaction: discord.Interaction, itemname: str):
    if not any(r.id in (SHOP_ADMIN_ROLE_ID, ADMIN_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    items = load_shop()
    shop_item = find_shop_item(items, itemname)

    if not shop_item:
        await interaction.response.send_message(
            f"❌ Das Item **{itemname}** wurde im Shop nicht gefunden.\n"
            f"Nutze `/shop` um alle verfügbaren Items zu sehen.",
            ephemeral=True
        )
        return

    items.remove(shop_item)
    save_shop(items)

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
        title="🗑️ Item aus Shop entfernt",
        description=(
            f"**Item:** {item_name}\n"
            f"**Preis war:** {shop_item['price']:,} 💵\n"
            f"**Entfernt von:** {interaction.user.mention}\n\n"
            f"**Inventare bereinigt:** {players_cleaned} Spieler\n"
            f"**Items entfernt:** {total_removed}x"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
