# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# misc_commands.py \u2014 Verschiedene Slash Commands
#   /kartenkontrolle, /delete, /commands
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from helpers import is_admin, is_team

# \u2500\u2500 /ping \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Kein default_member_permissions \u2192 f\u00FCr alle Spieler sichtbar (Debug-Command)

@bot.tree.command(name="ping", description="Pr\u00FCft ob der Bot erreichbar ist", guild=discord.Object(id=GUILD_ID))
async def ping_cmd(interaction: discord.Interaction):
    ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"\U0001F3D3 Pong! `{ms} ms`", ephemeral=True)


# \u2500\u2500 /kartenkontrolle \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="kartenkontrolle", description="[Team] Kartenkontrolle-Erinnerung per DM senden", guild=discord.Object(id=GUILD_ID))
async def kartenkontrolle(interaction: discord.Interaction):
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
                title="\U0001FAAA Kartenkontrolle",
                description=(
                    f"**Hallo {member.display_name}!**\n\n"
                    f"Es findet gerade eine **Kartenkontrolle** statt.\n"
                    f"Bitte begib dich in den Kanal:\n"
                    f"[\U0001F517 Zur Kartenkontrolle]({channel_link})\n\n"
                    f"*Diese Nachricht wurde automatisch durch das Team gesendet.*"
                ),
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            dm_embed.set_footer(text="Paradise City Roleplay \u2022 Kartenkontrolle")
            await member.send(embed=dm_embed)
            sent += 1
        except Exception:
            failed += 1

    await interaction.followup.send(
        f"\u2705 Kartenkontrolle-DM gesendet!\n**Erfolgreich:** {sent} | **Fehlgeschlagen (DMs zu):** {failed}",
        ephemeral=True
    )


# \u2500\u2500 /delete \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="delete", description="[Team] L\u00F6scht Nachrichten im Kanal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(anzahl="Anzahl der zu l\u00F6schenden Nachrichten (max. 100)")
async def delete_messages(interaction: discord.Interaction, anzahl: int):
    if anzahl < 1 or anzahl > 100:
        await interaction.response.send_message("\u274C Bitte eine Zahl zwischen 1 und 100 angeben.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    geloescht = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(
        f"\u2705 **{len(geloescht)}** Nachrichten wurden gel\u00F6scht.",
        ephemeral=True
    )


# \u2500\u2500 /anonym-nachricht \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

ANONYM_CHANNEL_ID = 1490890321276702723

@bot.tree.command(name="anonym-nachricht", description="Sende eine komplett anonyme Nachricht", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nachricht="Deine anonyme Nachricht")
async def anonym_nachricht(interaction: discord.Interaction, nachricht: str):
    if interaction.channel_id != ANONYM_CHANNEL_ID:
        ziel = f"<#{ANONYM_CHANNEL_ID}>"
        await interaction.response.send_message(
            f"\u274c Dieser Command funktioniert nur in {ziel}.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        description=f"\U0001f575\ufe0f **Anonyme Nachricht:**\n\n{nachricht}",
        color=0x2b2d31,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Anonyme Nachricht \u2022 Absender unbekannt")

    await interaction.response.send_message("\u2705 Deine Nachricht wurde anonym gesendet.", ephemeral=True)
    await interaction.channel.send(embed=embed)


# \u2500\u2500 /server-info \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="server-info", description="Zeigt aktuelle Server-Statistiken an", guild=discord.Object(id=GUILD_ID))
async def server_info(interaction: discord.Interaction):
    g = interaction.guild

    # Mitglieder
    total_members = g.member_count
    bots          = sum(1 for m in g.members if m.bot)
    humans        = total_members - bots

    # Kan\u00e4le
    text_ch  = len(g.text_channels)
    voice_ch = len(g.voice_channels)
    cats     = len(g.categories)
    total_ch = text_ch + voice_ch

    # Rollen (ohne @everyone)
    roles = len(g.roles) - 1

    # Commands
    cmds = len(bot.tree.get_commands(guild=discord.Object(id=g.id)))

    # Server-Erstellungsdatum
    created = g.created_at.strftime("%d.%m.%Y um %H:%M Uhr")

    embed = discord.Embed(
        title=f"\U0001f4ca {g.name} \u2014 Server-Info",
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)

    embed.add_field(
        name="\U0001f465 Mitglieder",
        value=(
            f"Gesamt: **{total_members}**\n"
            f"Spieler: **{humans}**\n"
            f"Bots: **{bots}**"
        ),
        inline=True,
    )
    embed.add_field(
        name="\U0001f4ac Kan\u00e4le",
        value=(
            f"Gesamt: **{total_ch}**\n"
            f"Text: **{text_ch}**\n"
            f"Voice: **{voice_ch}**\n"
            f"Kategorien: **{cats}**"
        ),
        inline=True,
    )
    embed.add_field(
        name="\U0001f6e1\ufe0f Rollen",
        value=f"Gesamt: **{roles}**",
        inline=True,
    )
    embed.add_field(
        name="\u2753 Commands",
        value=f"Registriert: **{cmds}**",
        inline=True,
    )
    embed.add_field(
        name="\U0001f4c5 Server erstellt",
        value=created,
        inline=True,
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Server-Info")

    await interaction.response.send_message(embed=embed)


# \u2500\u2500 /kokain-setup \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="kokain-setup",
    description="[Team] Sendet das Kokain Info-Embed in den Kanal",
    guild=discord.Object(id=GUILD_ID),
)
async def kokain_setup_cmd(interaction: discord.Interaction):
    role_ids = {r.id for r in interaction.user.roles}
    if not (role_ids & {INHABER_ROLE_ID, ADMIN_ROLE_ID, DASH_ROLE_ID, TICKET_MOD_ROLE_ID}):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    import kokain as _kokain
    await _kokain._koka_setup()
    await interaction.followup.send("\u2705 Kokain Info-Embed gesendet.", ephemeral=True)
