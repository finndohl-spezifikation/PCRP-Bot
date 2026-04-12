# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# inventory.py — Inventar Commands (Rucksack, Übergeben, Verstecken, Use)
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import is_admin
from economy_helpers import (
    load_economy, save_economy, get_user, load_shop,
    find_shop_item, find_inventory_item, normalize_item_name,
    has_citizen_or_wage, shop_item_autocomplete, inventory_item_autocomplete,
    load_hidden_items, save_hidden_items, VersteckRetrieveView, channel_error
)
from handy import give_handy_channel_access


# /rucksack
@bot.tree.command(name="rucksack", description="[Inventar] Zeige dein Inventar an", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Spieler dessen Inventar angezeigt werden soll")
async def rucksack(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids = [r.id for r in interaction.user.roles]
    is_team_m = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids
    allowed  = is_team_m or CITIZEN_ROLE_ID in role_ids or any(r in role_ids for r in WAGE_ROLES)

    if nutzer is not None:
        if not is_team_m:
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, den Rucksack anderer Spieler einzusehen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    else:
        if not is_team_m and interaction.channel.id != RUCKSACK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
            return
        if not allowed:
            await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
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
        desc   = "\n".join(f"• **{item}** ×{count}" for item, count in counts.items())

    embed = discord.Embed(
        title=f"🎒 Rucksack von {ziel.display_name}",
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /uebergeben
@bot.tree.command(name="uebergeben", description="[Inventar] Gib ein Item an jemanden weiter", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Empfänger", item="Item auswählen", menge="Wie viele möchtest du übergeben? (Standard: 1)")
@app_commands.autocomplete(item=inventory_item_autocomplete)
async def uebergeben(interaction: discord.Interaction, nutzer: discord.Member, item: str, menge: int = 1):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != UEBERGEBEN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(UEBERGEBEN_CHANNEL_ID), ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("❌ Du kannst nicht an dich selbst übergeben.", ephemeral=True)
        return

    if menge < 1:
        await interaction.response.send_message("❌ Die Menge muss mindestens 1 sein.", ephemeral=True)
        return

    eco        = load_economy()
    giver_data = get_user(eco, interaction.user.id)
    inv        = giver_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if not match:
        await interaction.response.send_message(
            f"❌ **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        return

    available = inv.count(match)
    if available < menge:
        await interaction.response.send_message(
            f"❌ Du hast nur **{available}×** **{match}** im Inventar, aber möchtest **{menge}×** übergeben.",
            ephemeral=True
        )
        return

    for _ in range(menge):
        inv.remove(match)
    receiver_data = get_user(eco, nutzer.id)
    receiver_data.setdefault("inventory", []).extend([match] * menge)
    save_economy(eco)

    if normalize_item_name(match) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, nutzer)

    menge_text = f"×{menge}" if menge > 1 else ""
    embed = discord.Embed(
        title="🤝 Item übergeben",
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
@bot.tree.command(name="verstecken", description="[Inventar] Verstecke ein Item an einem Ort", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(item="Item auswählen", ort="Wo soll das Item versteckt werden?")
@app_commands.autocomplete(item=inventory_item_autocomplete)
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
            f"❌ **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        return

    inv.remove(match)
    save_economy(eco)

    item_id = str(uuid.uuid4())[:8]
    hidden  = load_hidden_items()
    hidden.append({
        "id":       item_id,
        "item":     match,
        "location": ort,
        "owner_id": interaction.user.id,
        "hidden_at": datetime.now(timezone.utc).isoformat(),
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


# /use-item
@bot.tree.command(name="use-item", description="[Inventar] Benutze und entferne ein Item aus deinem Inventar", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    item="Name des Items das du benutzen möchtest",
    menge="Wie viele möchtest du benutzen? (Standard: 1)"
)
async def use_item(interaction: discord.Interaction, item: str, menge: int = 1):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != RUCKSACK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(RUCKSACK_CHANNEL_ID), ephemeral=True)
        return

    if menge < 1:
        await interaction.response.send_message("❌ Die Menge muss mindestens **1** sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    inv       = user_data.get("inventory", [])

    match = find_inventory_item(inv, item)
    if not match:
        await interaction.response.send_message(
            f"❌ **{item}** ist nicht in deinem Inventar.", ephemeral=True
        )
        return

    verfuegbar = inv.count(match)
    if menge > verfuegbar:
        await interaction.response.send_message(
            f"❌ Du hast nur **{verfuegbar}x {match}** im Inventar, aber möchtest **{menge}** benutzen.",
            ephemeral=True
        )
        return

    for _ in range(menge):
        inv.remove(match)
    save_economy(eco)

    menge_text = f" × {menge}" if menge > 1 else ""
    embed = discord.Embed(
        title="✅ Item benutzt",
        description=(
            f"**{interaction.user.mention}** hat **{match}**{menge_text} benutzt.\n"
            f"Das Item wurde aus dem Inventar entfernt."
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /item-add (Admin only)
@bot.tree.command(name="item-add", description="[Admin] Gib einem Spieler ein Item", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    nutzer="Spieler",
    itemname="Itemname (muss im Shop vorhanden sein)",
    menge="Anzahl (Standard: 1)",
)
@app_commands.autocomplete(itemname=shop_item_autocomplete)
async def item_add(interaction: discord.Interaction, nutzer: discord.Member, itemname: str, menge: int = 1):
    if not any(r.id in (ITEM_MANAGE_ROLE_ID, ADMIN_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    if menge < 1:
        await interaction.response.send_message("❌ Menge muss mindestens 1 sein.", ephemeral=True)
        return

    shop_items = load_shop()
    shop_item  = find_shop_item(shop_items, itemname)
    if not shop_item:
        await interaction.response.send_message(
            f"❌ Das Item **{itemname}** existiert nicht im Shop.\n"
            f"Es können nur vorhandene Shop-Items vergeben werden. Nutze `/shop` um alle Items zu sehen.",
            ephemeral=True
        )
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    if "inventory" not in user_data:
        user_data["inventory"] = []
    user_data["inventory"].extend([shop_item["name"]] * menge)
    save_economy(eco)

    if normalize_item_name(shop_item["name"]) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, nutzer)

    embed = discord.Embed(
        title="📦 Item vergeben",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Item:** {shop_item['name']}\n"
            f"**Menge:** {menge}×\n"
            f"**Vergeben von:** {interaction.user.mention}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /remove-item (Admin only)
@bot.tree.command(name="remove-item", description="[Admin] Entferne ein Item aus dem Inventar eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler", itemname="Itemname")
async def remove_item(interaction: discord.Interaction, nutzer: discord.Member, itemname: str):
    if not any(r.id in (ITEM_MANAGE_ROLE_ID, ADMIN_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inventory = user_data.get("inventory", [])

    match = find_inventory_item(inventory, itemname)
    if not match:
        await interaction.response.send_message(
            f"❌ **{nutzer.display_name}** besitzt kein Item namens **{itemname}**.", ephemeral=True
        )
        return

    inventory.remove(match)
    user_data["inventory"] = inventory
    save_economy(eco)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="📦 Item entfernt",
            description=f"**{match}** wurde von **{nutzer.mention}** entfernt.",
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        ),
        ephemeral=True
    )
