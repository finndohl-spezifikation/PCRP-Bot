# -*- coding: utf-8 -*-
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# vorschlag.py â€” Vorschlag-System
# Paradise City Roleplay Discord Bot
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

import discord
from discord import app_commands
from datetime import datetime, timezone

from config import bot, GUILD_ID, LOG_COLOR, ADMIN_ROLE_ID, MOD_ROLE_ID

# â”€â”€ Konstanten â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

VORSCHLAG_CHANNEL_ID = 1490882579765661837

# â”€â”€ Abstimmungs-View â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
                    child.label = f"ðŸ‘ {self.ja}"
                elif child.custom_id == "vorschlag_nein":
                    child.label = f"ðŸ‘Ž {self.nein}"

    @discord.ui.button(label="ðŸ‘ 0", style=discord.ButtonStyle.green,
                       custom_id="vorschlag_ja")
    async def vote_ja(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        self.ja += 1
        self._update_labels()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            "âœ… Du hast fÃ¼r diesen Vorschlag gestimmt!", ephemeral=True
        )

    @discord.ui.button(label="ðŸ‘Ž 0", style=discord.ButtonStyle.red,
                       custom_id="vorschlag_nein")
    async def vote_nein(self, interaction: discord.Interaction,
                        button: discord.ui.Button):
        self.nein += 1
        self._update_labels()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            "âŒ Du hast gegen diesen Vorschlag gestimmt!", ephemeral=True
        )


# â”€â”€ /vorschlag â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@bot.tree.command(
    name="vorschlag",
    description="Reiche einen Vorschlag fÃ¼r den Server ein.",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(vorschlag="Dein Vorschlag fÃ¼r den Server")
async def cmd_vorschlag(interaction: discord.Interaction, vorschlag: str):
    channel = interaction.guild.get_channel(VORSCHLAG_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message(
            "âŒ Vorschlag-Kanal nicht gefunden.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="ðŸ’¡ Neuer Vorschlag",
        description=vorschlag,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url
    )
    embed.set_footer(text=f"Vorschlag von {interaction.user} Â· Paradise City Roleplay")
    embed.set_thumbnail(
        url="https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/paradise_city.jpg"
    )

    view = VorschlagView()
    msg = await channel.send(embed=embed, view=view)

    await interaction.response.send_message(
        "âœ… Dein Vorschlag wurde eingereicht!", ephemeral=True
    )


# â”€â”€ Autocomplete: offene VorschlÃ¤ge laden â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def vorschlag_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    channel = interaction.guild.get_channel(VORSCHLAG_CHANNEL_ID)
    if not channel:
        return []
    choices = []
    try:
        async for msg in channel.history(limit=50):
            if not msg.author.bot or not msg.embeds:
                continue
            emb = msg.embeds[0]
            if not emb.title or "Vorschlag" not in emb.title:
                continue
            if emb.title in ("âœ… Vorschlag angenommen", "âŒ Vorschlag abgelehnt"):
                continue
            text = (emb.description or "")[:80]
            if current.lower() in text.lower():
                choices.append(app_commands.Choice(name=text, value=str(msg.id)))
            if len(choices) >= 25:
                break
    except Exception:
        pass
    return choices


# â”€â”€ /vorschlag-annehmen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@bot.tree.command(
    name="vorschlag-annehmen",
    description="Nimm einen Vorschlag an. (Admin/Mod)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(
    vorschlag="WÃ¤hle den Vorschlag aus",
    grund="BegrÃ¼ndung (optional)"
)
@app_commands.autocomplete(vorschlag=vorschlag_autocomplete)
async def cmd_vorschlag_annehmen(
    interaction: discord.Interaction,
    vorschlag: str,
    grund: str = "Kein Grund angegeben"
):
    admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
    mod_role   = interaction.guild.get_role(MOD_ROLE_ID)
    if not any(r in interaction.user.roles for r in [admin_role, mod_role] if r):
        await interaction.response.send_message(
            "âŒ Du hast keine Berechtigung.", ephemeral=True
        )
        return

    channel = interaction.guild.get_channel(VORSCHLAG_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message(
            "âŒ Vorschlag-Kanal nicht gefunden.", ephemeral=True
        )
        return

    try:
        msg = await channel.fetch_message(int(vorschlag))
    except Exception:
        await interaction.response.send_message(
            "âŒ Vorschlag nicht gefunden.", ephemeral=True
        )
        return

    if not msg.embeds:
        await interaction.response.send_message(
            "âŒ Diese Nachricht enthÃ¤lt kein Vorschlags-Embed.", ephemeral=True
        )
        return

    old_embed = msg.embeds[0]

    new_embed = discord.Embed(
        title="âœ… Vorschlag angenommen",
        description=old_embed.description,
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc)
    )
    if old_embed.author:
        new_embed.set_author(name=old_embed.author.name, icon_url=old_embed.author.icon_url)
    new_embed.add_field(name="Entscheidung", value="âœ… Angenommen", inline=True)
    new_embed.add_field(name="Bearbeitet von", value=interaction.user.mention, inline=True)
    new_embed.add_field(name="BegrÃ¼ndung", value=grund, inline=False)
    new_embed.set_footer(text="Paradise City Roleplay â€” VorschlÃ¤ge")
    new_embed.set_thumbnail(
        url="https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/paradise_city.jpg"
    )

    await msg.edit(embed=new_embed, view=None)
    await interaction.response.send_message(
        "âœ… Vorschlag wurde als **angenommen** markiert.", ephemeral=True
    )


# â”€â”€ /vorschlag-ablehnen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@bot.tree.command(
    name="vorschlag-ablehnen",
    description="Lehne einen Vorschlag ab. (Admin/Mod)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(
    vorschlag="WÃ¤hle den Vorschlag aus",
    grund="BegrÃ¼ndung (optional)"
)
@app_commands.autocomplete(vorschlag=vorschlag_autocomplete)
async def cmd_vorschlag_ablehnen(
    interaction: discord.Interaction,
    vorschlag: str,
    grund: str = "Kein Grund angegeben"
):
    admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
    mod_role   = interaction.guild.get_role(MOD_ROLE_ID)
    if not any(r in interaction.user.roles for r in [admin_role, mod_role] if r):
        await interaction.response.send_message(
            "âŒ Du hast keine Berechtigung.", ephemeral=True
        )
        return

    channel = interaction.guild.get_channel(VORSCHLAG_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message(
            "âŒ Vorschlag-Kanal nicht gefunden.", ephemeral=True
        )
        return

    try:
        msg = await channel.fetch_message(int(vorschlag))
    except Exception:
        await interaction.response.send_message(
            "âŒ Vorschlag nicht gefunden.", ephemeral=True
        )
        return

    if not msg.embeds:
        await interaction.response.send_message(
            "âŒ Diese Nachricht enthÃ¤lt kein Vorschlags-Embed.", ephemeral=True
        )
        return

    old_embed = msg.embeds[0]

    new_embed = discord.Embed(
        title="âŒ Vorschlag abgelehnt",
        description=old_embed.description,
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc)
    )
    if old_embed.author:
        new_embed.set_author(name=old_embed.author.name, icon_url=old_embed.author.icon_url)
    new_embed.add_field(name="Entscheidung", value="âŒ Abgelehnt", inline=True)
    new_embed.add_field(name="Bearbeitet von", value=interaction.user.mention, inline=True)
    new_embed.add_field(name="BegrÃ¼ndung", value=grund, inline=False)
    new_embed.set_footer(text="Paradise City Roleplay â€” VorschlÃ¤ge")
    new_embed.set_thumbnail(
        url="https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/paradise_city.jpg"
    )

    await msg.edit(embed=new_embed, view=None)
    await interaction.response.send_message(
        "âœ… Vorschlag wurde als **abgelehnt** markiert.", ephemeral=True
    )
