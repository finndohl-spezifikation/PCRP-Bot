# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# misc_commands.py — Verschiedene Slash Commands
#   /kartenkontrolle, /delete, /commands
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import is_admin, is_team

# ── /kartenkontrolle ─────────────────────────────────────────

@bot.tree.command(name="kartenkontrolle", description="[Team] Kartenkontrolle-Erinnerung per DM senden", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def kartenkontrolle(interaction: discord.Interaction):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild        = interaction.guild
    channel_link = f"https://discord.com/channels/{guild.id}/{KARTENKONTROLLE_CHANNEL_ID}"

    sent   = 0
    failed = 0
    for member in guild.members:
        if member.bot:
            continue
        role_ids = [r.id for r in member.roles]
        is_member_role = (
            CITIZEN_ROLE_ID in role_ids
            or any(r in role_ids for r in WAGE_ROLES)
        )
        if not is_member_role:
            continue
        try:
            dm_embed = discord.Embed(
                title="🪪 Kartenkontrolle",
                description=(
                    f"**Hallo {member.display_name}!**\n\n"
                    f"Es findet gerade eine **Kartenkontrolle** statt.\n"
                    f"Bitte begib dich in den Kanal:\n"
                    f"[🔗 Zur Kartenkontrolle]({channel_link})\n\n"
                    f"*Diese Nachricht wurde automatisch durch das Team gesendet.*"
                ),
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            await member.send(embed=dm_embed)
            sent += 1
        except Exception:
            failed += 1

    await interaction.followup.send(
        f"✅ Kartenkontrolle-DM gesendet!\n**Erfolgreich:** {sent} | **Fehlgeschlagen (DMs zu):** {failed}",
        ephemeral=True
    )


# ── /delete ─────────────────────────────────────────────────

@bot.tree.command(name="delete", description="[Team] Löscht Nachrichten im Kanal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(anzahl="Anzahl der zu löschenden Nachrichten (max. 100)")
@app_commands.default_permissions(manage_messages=True)
async def delete_messages(interaction: discord.Interaction, anzahl: int):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    if anzahl < 1 or anzahl > 100:
        await interaction.response.send_message("❌ Bitte eine Zahl zwischen 1 und 100 angeben.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    geloescht = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(
        f"✅ **{len(geloescht)}** Nachrichten wurden gelöscht.",
        ephemeral=True
    )

