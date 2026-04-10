# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# misc_commands.py — Verschiedene Slash Commands
#   /kartenkontrolle, /delete, /commands
# Kryptik / Cryptik Roleplay Discord Bot
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


# ── /commands ───────────────────────────────────────────────

@bot.tree.command(name="commands", description="Zeigt alle Bot-Commands an", guild=discord.Object(id=GUILD_ID))
async def commands_list(interaction: discord.Interaction):
    if not any(r.id == MOD_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🤖 Bot Commands — Übersicht",
        color=0x00BFFF,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="💳 Konto",
        value=(
            "`/lohn-abholen` — Stündlichen Lohn abholen\n"
            "`/kontostand` — Kontostand anzeigen\n"
            "`/einzahlen` — Bargeld einzahlen\n"
            "`/auszahlen` — Geld abheben\n"
            "`/ueberweisen` — Geld überweisen"
        ),
        inline=False
    )
    embed.add_field(
        name="🛒 Shop",
        value=(
            "`/shop` — Shop anzeigen\n"
            "`/buy` — Item kaufen\n"
            "`/shop-add` — Item zum Shop hinzufügen\n"
            "`/delete-item` — Item aus dem Shop entfernen"
        ),
        inline=False
    )
    embed.add_field(
        name="🎒 Inventar",
        value=(
            "`/rucksack` — Inventar anzeigen\n"
            "`/uebergeben` — Item übergeben\n"
            "`/verstecken` — Item verstecken\n"
            "`/use-item` — Item benutzen"
        ),
        inline=False
    )
    embed.add_field(
        name="⚠️ Warn-System",
        value=(
            "`/warn` — Verwarnung ausgeben\n"
            "`/warn-list` — Verwarnungen anzeigen\n"
            "`/remove-warn` — Verwarnung entfernen"
        ),
        inline=False
    )
    embed.add_field(
        name="🎟 Ticket",
        value=(
            "`/ticket` (Drop-Down) — Ticket erstellen"
        ),
        inline=False
    )
    embed.add_field(
        name="🪪 Ausweis & Führerschein",
        value=(
            "`/ausweisen` — Ausweis vorzeigen\n"
            "`/ausweis-create` — Ausweis erstellen\n"
            "`/create-führerschein` — Führerschein ausstellen\n"
            "`/führerschein` — Führerschein anzeigen\n"
            "`/führerschein-edit` — Führerschein bearbeiten\n"
            "`/remove-führerschein` — Führerschein entziehen\n"
            "`/führerschein-geben` — Führerschein zurückgeben"
        ),
        inline=False
    )
    embed.add_field(
        name="🔨 Admin",
        value=(
            "`/money-add` — Geld hinzufügen\n"
            "`/remove-money` — Geld entfernen\n"
            "`/item-add` — Item an Spieler geben\n"
            "`/remove-item` — Item von Spieler entfernen\n"
            "`/team-warn` — Team-Verwarnung ausgeben\n"
            "`/teamwarn-list` — Team-Verwarnungen anzeigen\n"
            "`/remove-teamwarn` — Team-Verwarnung entfernen\n"
            "`/ausweis-remove` — Ausweis löschen"
        ),
        inline=False
    )
    embed.add_field(
        name="🎮 Lobby",
        value=(
            "`/lobby-abstimmung` — Lobby-Abstimmung senden\n"
            "`/lobby-open` — Lobby öffnen\n"
            "`/lobby-close` — Lobby schließen"
        ),
        inline=False
    )
    embed.add_field(
        name="🎉 Events & Giveaways",
        value=(
            "`/create-event` — Event erstellen\n"
            "`/create-giveaway` — Giveaway erstellen\n"
            "`/abstimmung` — Abstimmung erstellen"
        ),
        inline=False
    )
    embed.add_field(
        name="🎰 Casino",
        value="`/casino` (Button) — Glücksrad drehen (1× täglich)",
        inline=False
    )
    embed.set_footer(text="Cryptik Roleplay — Bot Commands")
    await interaction.response.send_message(embed=embed, ephemeral=True)
