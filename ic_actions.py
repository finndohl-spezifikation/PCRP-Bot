# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# ic_actions.py \u2014 IC Aktionen (/erste-hilfe, /ortung, /fesseln)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from economy_helpers import has_item, consume_item, load_economy, save_economy, get_user

IC_ACTIONS_CHANNEL_ID = 1490882589014364250

ERSTE_HILFE_ITEM = "Erste Hilfe Koffer"
ORTUNG_ITEM      = "Ortungsger\u00E4t"
FESSELN_ITEM     = "Handfesseln"


def _hat_buerger_rolle(member) -> bool:
    return any(r.id == CITIZEN_ROLE_ID for r in member.roles)


def _in_ic_channel(interaction: discord.Interaction) -> bool:
    if any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID, INHABER_ROLE_ID) for r in interaction.user.roles):
        return True
    return interaction.channel_id == IC_ACTIONS_CHANNEL_ID


# \u2500\u2500 /erste-hilfe \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="erste-hilfe",
    description="Erste Hilfe leisten \u2014 ben\u00F6tigt \u2695\uFE0F| Erste Hilfe Koffer im Inventar",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    ziel="Spieler dem du erste Hilfe leistest"
)
async def erste_hilfe(interaction: discord.Interaction, ziel: discord.Member):
    if not _in_ic_channel(interaction):
        await interaction.response.send_message(
            f"\u274C Dieser Command ist nur in <#{IC_ACTIONS_CHANNEL_ID}> nutzbar.", ephemeral=True
        )
        return
    if not _hat_buerger_rolle(interaction.user):
        await interaction.response.send_message(
            "\u274C Du ben\u00F6tigst die B\u00FCrger-Rolle um diesen Command zu nutzen.", ephemeral=True
        )
        return
    if not has_item(interaction.user, ERSTE_HILFE_ITEM):
        await interaction.response.send_message(
            "\u274C Du ben\u00F6tigst einen **\u2695\uFE0F| Erste Hilfe Koffer** aus dem Shop!", ephemeral=True
        )
        return

    consume_item(interaction.user, ERSTE_HILFE_ITEM)

    embed = discord.Embed(
        title="\u2695\uFE0F Erste Hilfe",
        description=(
            f"{interaction.user.mention} leistet **{ziel.mention}** erste Hilfe!\n\n"
            f"\u23F0 **{ziel.display_name}** muss sich innerhalb der n\u00E4chsten **15 Minuten** "
            f"von einem **Medic behandeln** lassen!"
        ),
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    embed.set_footer(text="Paradise City Roleplay \u2014 IC Aktion")
    await interaction.response.send_message(embed=embed)


# \u2500\u2500 /ortung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="ortung",
    description="Spieler orten \u2014 ben\u00F6tigt \U0001F4BB| Ortungsger\u00E4t im Inventar",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    ziel="Spieler den du ortest"
)
async def ortung(interaction: discord.Interaction, ziel: discord.Member):
    if not _in_ic_channel(interaction):
        await interaction.response.send_message(
            f"\u274C Dieser Command ist nur in <#{IC_ACTIONS_CHANNEL_ID}> nutzbar.", ephemeral=True
        )
        return
    if not _hat_buerger_rolle(interaction.user):
        await interaction.response.send_message(
            "\u274C Du ben\u00F6tigst die B\u00FCrger-Rolle um diesen Command zu nutzen.", ephemeral=True
        )
        return
    if not has_item(interaction.user, ORTUNG_ITEM):
        await interaction.response.send_message(
            "\u274C Du ben\u00F6tigst ein **\U0001F4BB| Ortungsger\u00E4t** aus dem Shop!", ephemeral=True
        )
        return

    consume_item(interaction.user, ORTUNG_ITEM)

    embed = discord.Embed(
        title="\U0001F4BB Ortung aktiv",
        description=(
            f"{interaction.user.mention} hat **{ziel.mention}** geortet!\n\n"
            f"\U0001F4CD Der Standort von **{ziel.display_name}** ist bekannt."
        ),
        color=0xE67E22,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    embed.set_footer(text="Paradise City Roleplay \u2014 IC Aktion")
    await interaction.response.send_message(embed=embed)


# \u2500\u2500 Entfesseln View \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class EntfesselnView(TimedDisableView):
    def __init__(self, fesseler_id: int, target_id: int):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.fesseler_id = fesseler_id
        self.target_id   = target_id

    @discord.ui.button(label="\U0001F513 Entfesseln", style=discord.ButtonStyle.green)
    async def entfesseln(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.fesseler_id:
            await interaction.response.send_message(
                "\u274C Nur derjenige der gefesselt hat kann auch entfesseln!", ephemeral=True
            )
            return

        eco       = load_economy()
        user_data = get_user(eco, self.fesseler_id)
        user_data.setdefault("inventory", []).append("\u26D3\uFE0F| Handfesseln")
        eco[str(self.fesseler_id)] = user_data
        save_economy(eco)

        button.disabled = True
        button.label    = "\U0001F513 Entfesselt"

        target  = interaction.guild.get_member(self.target_id)
        fesseler = interaction.guild.get_member(self.fesseler_id)
        embed = discord.Embed(
            title="\U0001F513 Entfesselt",
            description=(
                f"{interaction.user.mention} hat "
                f"**{target.mention if target else 'den Spieler'}** entfesselt!\n\n"
                f"Die Handfesseln wurden zur\u00FCck ins Inventar von "
                f"{fesseler.mention if fesseler else 'dem Fesseler'} gelegt."
            ),
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc)
        )
        if target:
            embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Paradise City Roleplay \u2014 IC Aktion")
        await interaction.response.edit_message(embed=embed, view=self)


# \u2500\u2500 /fesseln \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="fesseln",
    description="Spieler fesseln \u2014 ben\u00F6tigt \u26D3\uFE0F| Handfesseln im Inventar",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    ziel="Spieler den du fesselst"
)
async def fesseln(interaction: discord.Interaction, ziel: discord.Member):
    if not _in_ic_channel(interaction):
        await interaction.response.send_message(
            f"\u274C Dieser Command ist nur in <#{IC_ACTIONS_CHANNEL_ID}> nutzbar.", ephemeral=True
        )
        return
    if not _hat_buerger_rolle(interaction.user):
        await interaction.response.send_message(
            "\u274C Du ben\u00F6tigst die B\u00FCrger-Rolle um diesen Command zu nutzen.", ephemeral=True
        )
        return
    if not has_item(interaction.user, FESSELN_ITEM):
        await interaction.response.send_message(
            "\u274C Du ben\u00F6tigst **\u26D3\uFE0F| Handfesseln** aus dem Shop!", ephemeral=True
        )
        return

    consume_item(interaction.user, FESSELN_ITEM)

    embed = discord.Embed(
        title="\u26D3\uFE0F Gefesselt",
        description=(
            f"{interaction.user.mention} hat **{ziel.mention}** gefesselt!\n\n"
            f"\U0001F512 **{ziel.display_name}** ist jetzt gefesselt und kann sich nicht bewegen."
        ),
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    embed.set_footer(text="Paradise City Roleplay \u2014 IC Aktion")
    view = EntfesselnView(fesseler_id=interaction.user.id, target_id=ziel.id)
    await interaction.response.send_message(embed=embed, view=view)
