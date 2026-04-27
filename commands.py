@bot.tree.command(
    name="shop-edit",
    description="[Shop] Bearbeite ein bestehendes Item (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    itemname="Name des Items das bearbeitet werden soll",
    neuer_preis="Neuer Preis in $ (leer lassen um nicht zu ändern)",
    neuer_name="Neuer Name des Items (leer lassen um nicht zu ändern)"
)
@app_commands.autocomplete(itemname=all_shops_item_autocomplete)
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

    items      = load_shop()
    shop_item  = find_shop_item(items, itemname)
    _save_fn   = save_shop

    if not shop_item:
        team_items = load_team_shop()
        shop_item  = find_shop_item(team_items, itemname)
        if shop_item:
            items    = team_items
            _save_fn = save_team_shop

    if not shop_item:
        angler_items = load_angler_shop()
        shop_item    = find_shop_item(angler_items, itemname)
        if shop_item:
            items    = angler_items
            _save_fn = save_angler_shop

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
        old_price          = shop_item["price"]
        shop_item["price"] = neuer_preis
        changes.append(f"**Preis:** {old_price:,} 💵 → {neuer_preis:,} 💵")

    if neuer_name:
        old_name          = shop_item["name"]
        shop_item["name"] = neuer_name
        eco = load_economy()
        for uid, udata in eco.items():
            udata["inventory"] = [
                neuer_name if i == old_name else i
                for i in udata.get("inventory", [])
            ]
        save_economy(eco)
        changes.append(f"**Name:** {old_name} → {neuer_name}")

    _save_fn(items)

    embed = discord.Embed(
        title="✏️ Item bearbeitet",
        description="\n".join(changes),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Bearbeitet von {interaction.user}")
    await interaction.response.send_message(embed=embed, ephemeral=True)
