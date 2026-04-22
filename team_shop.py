# -*- coding: utf-8 -*-
# \\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550
# team_shop.py \\u2014 Team-Shop (nur Mod / Admin)
# Paradise City Roleplay Discord Bot
# \\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550

import re
from config import *
from economy_helpers import load_economy, save_economy, get_user, load_team_shop, save_team_shop

# \\u2500\\u2500 Hilfsfunktionen \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

_PAGE_SIZE = 15


def _is_team(member: discord.Member) -> bool:
    role_ids = {r.id for r in member.roles}
    return bool(role_ids & {ADMIN_ROLE_ID, MOD_ROLE_ID, SHOP_ADMIN_ROLE_ID})


def _find_team_item(items: list, query: str) -> dict | None:
    q = query.strip().lower()
    for item in items:
        if item["name"].strip().lower() == q:
            return item
    return None


# \\u2500\\u2500 Embed-Builder \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

def _build_team_embed(page: int = 0) -> tuple[discord.Embed, int]:
    items       = load_team_shop()
    total_pages = max(1, -(-len(items) // _PAGE_SIZE))
    page        = max(0, min(page, total_pages - 1))
    page_items  = items[page * _PAGE_SIZE : (page + 1) * _PAGE_SIZE]

    embed = discord.Embed(
        title="\\U0001F6E1\\uFE0F Team-Shop",
        description=(
            "\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\u2015\\n"
            + (
                "\\n".join(f"\\u27A4 **{i['name']}**" for i in page_items)
                if page_items else "*Keine Items vorhanden.*"
            )
        ),
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc),
    )

    footer = "\\U0001F6E1\\uFE0F Nur f\\u00FCr Team-Mitglieder \\u2022 Kostenlos"
    if total_pages > 1:
        footer += f"  |  Seite {page + 1}/{total_pages}"
    embed.set_footer(text=footer)
    return embed, total_pages


# \\u2500\\u2500 Item-Select \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

class TeamItemSelect(discord.ui.Select):
    def __init__(self, page_items: list):
        options = []
        for item in page_items[:25]:
            name   = item["name"]
            custom = re.search(r'<(a?):([^:]+):(\\d+)>', name)
            label  = re.sub(r'<a?:[^:]+:\\d+>\\s*\\|?\\s*', '', name).strip() or name
            emoji  = None
            if custom:
                emoji = discord.PartialEmoji(
                    animated=bool(custom.group(1)),
                    name=custom.group(2),
                    id=int(custom.group(3))
                )
            options.append(discord.SelectOption(
                label=label[:100],
                value=name[:100],
                description="Kostenlos \\u2014 nur f\\u00FCr Team",
                emoji=emoji
            ))
        super().__init__(
            placeholder="\\U0001F4E6 Item ausw\\u00E4hlen \\u2014 wird direkt ins Inventar gelegt",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="team_item_select",
        )

    async def callback(self, interaction: discord.Interaction):
        if not _is_team(interaction.user):
            await interaction.response.send_message("\\u274C Kein Zugriff.", ephemeral=True)
            return

        item_name = self.values[0]
        items     = load_team_shop()
        item      = _find_team_item(items, item_name)
        if not item:
            await interaction.response.send_message(
                "\\u274C Item nicht mehr verf\\u00FCgbar.", ephemeral=True
            )
            return

        eco       = load_economy()
        user_data = get_user(eco, interaction.user.id)
        user_data.setdefault("inventory", []).append(item["name"])
        save_economy(eco)

        embed = discord.Embed(
            title="\\u2705 Item erhalten",
            description=(
                f"\\u27A4 **{item['name']}** wurde deinem Inventar hinzugef\\u00FCgt."
            ),
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text=f"Team-Shop \\u2022 {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# \\u2500\\u2500 Team-Shop-View (Seiten bl\\u00e4ttern) \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

class TeamShopView(TimedDisableView):
    def __init__(self, page: int = 0, total_pages: int = 1):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.page        = page
        self.total_pages = total_pages
        self._rebuild()

    def _rebuild(self):
        self.clear_items()
        items      = load_team_shop()
        page_items = items[self.page * _PAGE_SIZE : (self.page + 1) * _PAGE_SIZE]

        if page_items:
            self.add_item(TeamItemSelect(page_items))

        if self.total_pages > 1:
            prev = discord.ui.Button(
                label="\\u25C0 Zur\\u00FCck",
                style=discord.ButtonStyle.secondary,
                disabled=self.page <= 0,
                row=2,
            )
            next_ = discord.ui.Button(
                label="Weiter \\u25B6",
                style=discord.ButtonStyle.secondary,
                disabled=self.page >= self.total_pages - 1,
                row=2,
            )

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


# \\u2500\\u2500 /items \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

@bot.tree.command(
    name="items",
    description="[Team] \\u00D6ffne den Team-Shop",
    guild=discord.Object(id=GUILD_ID)
)
async def items_cmd(interaction: discord.Interaction):
    if not _is_team(interaction.user):
        await interaction.response.send_message("\\u274C Kein Zugriff.", ephemeral=True)
        return

    embed, total_pages = _build_team_embed(page=0)
    view = TeamShopView(page=0, total_pages=total_pages)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# \\u2500\\u2500 /items-add \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

@bot.tree.command(
    name="items-add",
    description="[Team] F\\u00FCge ein Item zum Team-Shop hinzu",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
@app_commands.describe(itemname="Name des Items")
async def items_add(interaction: discord.Interaction, itemname: str):
    if not _is_team(interaction.user):
        await interaction.response.send_message("\\u274C Kein Zugriff.", ephemeral=True)
        return

    itemname = itemname.strip()
    if not itemname:
        await interaction.response.send_message("\\u274C Bitte einen g\\u00FCltigen Namen angeben.", ephemeral=True)
        return

    items = load_team_shop()
    if _find_team_item(items, itemname):
        await interaction.response.send_message(
            f"\\u274C **{itemname}** existiert bereits im Team-Shop.", ephemeral=True
        )
        return

    items.append({"name": itemname})
    save_team_shop(items)

    embed = discord.Embed(
        title="\\u2705 Item hinzugef\\u00FCgt",
        description=f"\\u27A4 **{itemname}** wurde zum Team-Shop hinzugef\\u00FCgt.",
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=f"Hinzugef\\u00FCgt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \\u2500\\u2500 /items-delete \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

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
        await interaction.response.send_message("\\u274C Kein Zugriff.", ephemeral=True)
        return

    items = load_team_shop()
    item  = _find_team_item(items, itemname)
    if not item:
        await interaction.response.send_message(
            f"\\u274C **{itemname}** nicht im Team-Shop gefunden.", ephemeral=True
        )
        return

    items.remove(item)
    save_team_shop(items)

    embed = discord.Embed(
        title="\\U0001F5D1\\uFE0F Item entfernt",
        description=f"\\u27A4 **{itemname}** wurde aus dem Team-Shop entfernt.",
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=f"Entfernt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)
