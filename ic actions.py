# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# ic_actions.py — IC Aktionen (/erste-hilfe, /ortung, /fesseln)
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from economy_helpers import has_item, consume_item

IC_ACTIONS_CHANNEL_ID = 1490882589014364250

ERSTE_HILFE_ITEM = "Erste Hilfe Koffer"
ORTUNG_ITEM      = "Ortungsgerät"
FESSELN_ITEM     = "Handfesseln"


def _hat_buerger_rolle(member) -> bool:
    return any(r.id == CITIZEN_ROLE_ID for r in member.roles)


def _in_ic_channel(interaction: discord.Interaction) -> bool:
    return interaction.channel_id == IC_ACTIONS_CHANNEL_ID


# ── /erste-hilfe ─────────────────────────────────────────────

@bot.tree.command(
    name="erste-hilfe",
    description="Erste Hilfe leisten — benötigt ⚕️| Erste Hilfe Koffer im Inventar"
)
@app_commands.describe(
    ziel="Spieler dem du erste Hilfe leistest"
)
async def erste_hilfe(interaction: discord.Interaction, ziel: discord.Member):
    if not _in_ic_channel(interaction):
        await interaction.response.send_message(
            f"❌ Dieser Command ist nur in <#{IC_ACTIONS_CHANNEL_ID}> nutzbar.", ephemeral=True
        )
        return
    if not _hat_buerger_rolle(interaction.user):
        await interaction.response.send_message(
            "❌ Du benötigst die Bürger-Rolle um diesen Command zu nutzen.", ephemeral=True
        )
        return
    if not has_item(interaction.user, ERSTE_HILFE_ITEM):
        await interaction.response.send_message(
            "❌ Du benötigst einen **⚕️| Erste Hilfe Koffer** aus dem Shop!", ephemeral=True
        )
        return

    consume_item(interaction.user, ERSTE_HILFE_ITEM)

    embed = discord.Embed(
        title="⚕️ Erste Hilfe",
        description=(
            f"{interaction.user.mention} leistet **{ziel.mention}** erste Hilfe!\n\n"
            f"⏰ **{ziel.display_name}** muss sich innerhalb der nächsten **15 Minuten** "
            f"von einem **Medic behandeln** lassen!"
        ),
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    embed.set_footer(text="Kryptik Roleplay — IC Aktion")
    await interaction.response.send_message(embed=embed)


# ── /ortung ──────────────────────────────────────────────────

@bot.tree.command(
    name="ortung",
    description="Spieler orten — benötigt 💻| Ortungsgerät im Inventar"
)
@app_commands.describe(
    ziel="Spieler den du ortest"
)
async def ortung(interaction: discord.Interaction, ziel: discord.Member):
    if not _in_ic_channel(interaction):
        await interaction.response.send_message(
            f"❌ Dieser Command ist nur in <#{IC_ACTIONS_CHANNEL_ID}> nutzbar.", ephemeral=True
        )
        return
    if not _hat_buerger_rolle(interaction.user):
        await interaction.response.send_message(
            "❌ Du benötigst die Bürger-Rolle um diesen Command zu nutzen.", ephemeral=True
        )
        return
    if not has_item(interaction.user, ORTUNG_ITEM):
        await interaction.response.send_message(
            "❌ Du benötigst ein **💻| Ortungsgerät** aus dem Shop!", ephemeral=True
        )
        return

    consume_item(interaction.user, ORTUNG_ITEM)

    embed = discord.Embed(
        title="💻 Ortung aktiv",
        description=(
            f"{interaction.user.mention} hat **{ziel.mention}** geortet!\n\n"
            f"📍 Der Standort von **{ziel.display_name}** ist bekannt."
        ),
        color=0x3498DB,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    embed.set_footer(text="Kryptik Roleplay — IC Aktion")
    await interaction.response.send_message(embed=embed)


# ── /fesseln ─────────────────────────────────────────────────

@bot.tree.command(
    name="fesseln",
    description="Spieler fesseln — benötigt ⛓️| Handfesseln im Inventar"
)
@app_commands.describe(
    ziel="Spieler den du fesselst"
)
async def fesseln(interaction: discord.Interaction, ziel: discord.Member):
    if not _in_ic_channel(interaction):
        await interaction.response.send_message(
            f"❌ Dieser Command ist nur in <#{IC_ACTIONS_CHANNEL_ID}> nutzbar.", ephemeral=True
        )
        return
    if not _hat_buerger_rolle(interaction.user):
        await interaction.response.send_message(
            "❌ Du benötigst die Bürger-Rolle um diesen Command zu nutzen.", ephemeral=True
        )
        return
    if not has_item(interaction.user, FESSELN_ITEM):
        await interaction.response.send_message(
            "❌ Du benötigst **⛓️| Handfesseln** aus dem Shop!", ephemeral=True
        )
        return

    consume_item(interaction.user, FESSELN_ITEM)

    embed = discord.Embed(
        title="⛓️ Gefesselt",
        description=(
            f"{interaction.user.mention} hat **{ziel.mention}** gefesselt!\n\n"
            f"🔒 **{ziel.display_name}** ist jetzt gefesselt und kann sich nicht bewegen."
        ),
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    embed.set_footer(text="Kryptik Roleplay — IC Aktion")
    await interaction.response.send_message(embed=embed)
