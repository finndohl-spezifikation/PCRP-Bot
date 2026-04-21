            async def prev_cb(interaction: discord.Interaction):
                self.page -= 1
                embed, self.total_pages = _build_team_embed(self.page)
                self._rebuild()
                await interaction.response.edit_message(embed=embed, view=self)

            async def next_cb(interaction: discord.Interaction):
                self.page += 1
                embed, self.total_pages = _build_team_embed(self.page)
                self._rebuild()
                await interaction.response.edit_message(embed=embed, view=self)

            prev.callback  = prev_cb
            next_.callback = next_cb
            self.add_item(prev)
            self.add_item(next_)


# \u2500\u2500 /items \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="items",
    description="[Team] \u00D6ffne den Team-Shop",
    guild=discord.Object(id=GUILD_ID)
)
async def items_cmd(interaction: discord.Interaction):
    if not _is_team(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    embed, total_pages = _build_team_embed(page=0)
    view = TeamShopView(page=0, total_pages=total_pages)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# \u2500\u2500 /items-add \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="items-add",
    description="[Team] F\u00FCge ein Item zum Team-Shop hinzu",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
@app_commands.describe(itemname="Name des Items")
async def items_add(interaction: discord.Interaction, itemname: str):
    if not _is_team(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    itemname = itemname.strip()
    if not itemname:
        await interaction.response.send_message("\u274C Bitte einen g\u00FCltigen Namen angeben.", ephemeral=True)
        return

    items = load_team_shop()
    if _find_team_item(items, itemname):
        await interaction.response.send_message(
            f"\u274C **{itemname}** existiert bereits im Team-Shop.", ephemeral=True
        )
        return

    items.append({"name": itemname})
    save_team_shop(items)

    embed = discord.Embed(
        title="\u2705 Item hinzugef\u00FCgt",
        description=f"\u27A4 **{itemname}** wurde zum Team-Shop hinzugef\u00FCgt.",
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=f"Hinzugef\u00FCgt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 /items-delete \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _team_item_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    items = load_team_shop()
    return [
        app_commands.Choice(name=i["name"][:100], value=i["name"][:100])
        for i in items
        if current.lower() in i["name"].lower()
    ][:25]


@bot.tree.command(
    name="items-delete",
    description="[Team] Entferne ein Item aus dem Team-Shop",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
@app_commands.describe(itemname="Name des Items")
@app_commands.autocomplete(itemname=_team_item_autocomplete)
async def items_delete(interaction: discord.Interaction, itemname: str):
    if not _is_team(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    items = load_team_shop()
    item  = _find_team_item(items, itemname)
    if not item:
        await interaction.response.send_message(
            f"\u274C **{itemname}** nicht im Team-Shop gefunden.", ephemeral=True
        )
        return

    items.remove(item)
    save_team_shop(items)

    embed = discord.Embed(
        title="\U0001F5D1\uFE0F Item entfernt",
        description=f"\u27A4 **{itemname}** wurde aus dem Team-Shop entfernt.",
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=f"Entfernt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)
