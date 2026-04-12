# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# vorschlag.py — Vorschlag-System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

import discord
from discord import app_commands
from datetime import datetime, timezone

from config import bot, GUILD_ID, LOG_COLOR, ADMIN_ROLE_ID, MOD_ROLE_ID

# ── Konstanten ────────────────────────────────────────────────

VORSCHLAG_CHANNEL_ID = 1490882579765661837

# ── Abstimmungs-View ──────────────────────────────────────────

class VorschlagView(discord.ui.View):
    def __init__(self, ja: int = 0, nein: int = 0):
        super().__init__(timeout=None)
        self.ja   = ja
        self.nein = nein
        self._update_labels()

    def _update_labels(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "vorschlag_ja":
                    child.label = f"👍 {self.ja}"
                elif child.custom_id == "vorschlag_nein":
                    child.label = f"👎 {self.nein}"

    @discord.ui.button(label="👍 0", style=discord.ButtonStyle.green,
                       custom_id="vorschlag_ja")
    async def vote_ja(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        self.ja += 1
        self._update_labels()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            "✅ Du hast für diesen Vorschlag gestimmt!", ephemeral=True
        )

    @discord.ui.button(label="👎 0", style=discord.ButtonStyle.red,
                       custom_id="vorschlag_nein")
    async def vote_nein(self, interaction: discord.Interaction,
                        button: discord.ui.Button):
        self.nein += 1
        self._update_labels()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            "❌ Du hast gegen diesen Vorschlag gestimmt!", ephemeral=True
        )


# ── /vorschlag ────────────────────────────────────────────────

@bot.tree.command(
    name="vorschlag",
    description="Reiche einen Vorschlag für den Server ein.",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(vorschlag="Dein Vorschlag für den Server")
async def cmd_vorschlag(interaction: discord.Interaction, vorschlag: str):
    channel = interaction.guild.get_channel(VORSCHLAG_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message(
            "❌ Vorschlag-Kanal nicht gefunden.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="💡 Neuer Vorschlag",
        description=vorschlag,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url
    )
    embed.set_footer(text=f"Vorschlag von {interaction.user} · Paradise City Roleplay")
    embed.set_image(
        url="https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/paradise_city.jpg"
    )

    view = VorschlagView()
    msg = await channel.send(embed=embed, view=view)

    await interaction.response.send_message(
        "✅ Dein Vorschlag wurde eingereicht!", ephemeral=True
    )


# ── /vorschlag-annehmen ───────────────────────────────────────

@bot.tree.command(
    name="vorschlag-annehmen",
    description="Nimm einen Vorschlag an. (Admin/Mod)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    message_id="ID der Vorschlags-Nachricht",
    grund="Begründung (optional)"
)
async def cmd_vorschlag_annehmen(
    interaction: discord.Interaction,
    message_id: str,
    grund: str = "Kein Grund angegeben"
):
    admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
    mod_role   = interaction.guild.get_role(MOD_ROLE_ID)
    if not any(r in interaction.user.roles for r in [admin_role, mod_role] if r):
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung.", ephemeral=True
        )
        return

    channel = interaction.guild.get_channel(VORSCHLAG_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message(
            "❌ Vorschlag-Kanal nicht gefunden.", ephemeral=True
        )
        return

    try:
        msg = await channel.fetch_message(int(message_id))
    except Exception:
        await interaction.response.send_message(
            "❌ Nachricht nicht gefunden. Bitte prüfe die Message-ID.", ephemeral=True
        )
        return

    if not msg.embeds:
        await interaction.response.send_message(
            "❌ Diese Nachricht enthält kein Vorschlags-Embed.", ephemeral=True
        )
        return

    old_embed = msg.embeds[0]

    new_embed = discord.Embed(
        title="✅ Vorschlag angenommen",
        description=old_embed.description,
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc)
    )
    if old_embed.author:
        new_embed.set_author(name=old_embed.author.name, icon_url=old_embed.author.icon_url)
    new_embed.add_field(name="Entscheidung", value="✅ Angenommen", inline=True)
    new_embed.add_field(name="Bearbeitet von", value=interaction.user.mention, inline=True)
    new_embed.add_field(name="Begründung", value=grund, inline=False)
    new_embed.set_footer(text="Paradise City Roleplay — Vorschläge")
    new_embed.set_image(
        url="https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/paradise_city.jpg"
    )

    await msg.edit(embed=new_embed, view=None)
    await interaction.response.send_message(
        "✅ Vorschlag wurde als **angenommen** markiert.", ephemeral=True
    )


# ── /vorschlag-ablehnen ───────────────────────────────────────

@bot.tree.command(
    name="vorschlag-ablehnen",
    description="Lehne einen Vorschlag ab. (Admin/Mod)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    message_id="ID der Vorschlags-Nachricht",
    grund="Begründung (optional)"
)
async def cmd_vorschlag_ablehnen(
    interaction: discord.Interaction,
    message_id: str,
    grund: str = "Kein Grund angegeben"
):
    admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
    mod_role   = interaction.guild.get_role(MOD_ROLE_ID)
    if not any(r in interaction.user.roles for r in [admin_role, mod_role] if r):
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung.", ephemeral=True
        )
        return

    channel = interaction.guild.get_channel(VORSCHLAG_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message(
            "❌ Vorschlag-Kanal nicht gefunden.", ephemeral=True
        )
        return

    try:
        msg = await channel.fetch_message(int(message_id))
    except Exception:
        await interaction.response.send_message(
            "❌ Nachricht nicht gefunden. Bitte prüfe die Message-ID.", ephemeral=True
        )
        return

    if not msg.embeds:
        await interaction.response.send_message(
            "❌ Diese Nachricht enthält kein Vorschlags-Embed.", ephemeral=True
        )
        return

    old_embed = msg.embeds[0]

    new_embed = discord.Embed(
        title="❌ Vorschlag abgelehnt",
        description=old_embed.description,
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc)
    )
    if old_embed.author:
        new_embed.set_author(name=old_embed.author.name, icon_url=old_embed.author.icon_url)
    new_embed.add_field(name="Entscheidung", value="❌ Abgelehnt", inline=True)
    new_embed.add_field(name="Bearbeitet von", value=interaction.user.mention, inline=True)
    new_embed.add_field(name="Begründung", value=grund, inline=False)
    new_embed.set_footer(text="Paradise City Roleplay — Vorschläge")
    new_embed.set_image(
        url="https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/paradise_city.jpg"
    )

    await msg.edit(embed=new_embed, view=None)
    await interaction.response.send_message(
        "✅ Vorschlag wurde als **abgelehnt** markiert.", ephemeral=True
    )
