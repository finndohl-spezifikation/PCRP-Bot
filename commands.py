# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# misc_commands.py \u2014 Verschiedene Slash Commands
#   /kartenkontrolle, /delete, /commands
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from helpers import is_admin, is_team
import fraktionen as _frak

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


# -- /kokain-setup ---------------------------------------------

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


# -- /weed-setup -----------------------------------------------

@bot.tree.command(
    name="weed-setup",
    description="[Team] Sendet das Weed Info-Embed in den Kanal",
    guild=discord.Object(id=GUILD_ID),
)
async def weed_setup_cmd(interaction: discord.Interaction):
    role_ids = {r.id for r in interaction.user.roles}
    if not (role_ids & {INHABER_ROLE_ID, ADMIN_ROLE_ID, DASH_ROLE_ID, TICKET_MOD_ROLE_ID}):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    import weed as _weed
    result = await _weed._weed_setup()
    await interaction.followup.send(result, ephemeral=True)


# -- /fraktions-warn -------------------------------------------

@bot.tree.command(
    name="fraktions-warn",
    description="[Fraktionsleitung] Erteilt einer Fraktion einen offiziellen Warn",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    fraktion="Name der Fraktion",
    grund="Grund f\u00fcr den Warn",
    konsequenz="Konsequenz bei weiteren Verst\u00f6\u00dfen",
)
async def fraktions_warn_cmd(
    interaction: discord.Interaction,
    fraktion: str,
    grund: str,
    konsequenz: str,
):
    if not _frak.frak_hat_recht(interaction):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)

    data  = _frak.frak_load()
    entry = data.setdefault(fraktion, {"warns": []})
    warns = entry["warns"]

    if len(warns) >= _frak.MAX_WARNS:
        await interaction.followup.send(
            f"\u274c **{fraktion}** hat bereits {_frak.MAX_WARNS}/{_frak.MAX_WARNS} Warns.",
            ephemeral=True,
        )
        return

    warns.append({
        "grund":      grund,
        "konsequenz": konsequenz,
        "datum":      datetime.now(timezone.utc).strftime("%d.%m.%Y"),
        "issuer":     str(interaction.user),
    })
    _frak.frak_save(data)
    wc = len(warns)

    if wc == 1:
        warn_symbol = "\u26a0\ufe0f"
    elif wc == 2:
        warn_symbol = "\u26a0\ufe0f\u26a0\ufe0f"
    else:
        warn_symbol = "\U0001f6a8 **LETZTER WARN**"

    emb = discord.Embed(
        title=f"\u26a0\ufe0f Fraktions-Warn \u2014 {fraktion}",
        color=0xE67E22,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(name="\U0001f3db\ufe0f Fraktion",  value=fraktion,   inline=False)
    emb.add_field(name="\U0001f4cb Grund",           value=grund,      inline=False)
    emb.add_field(name="\u2696\ufe0f Konsequenz",    value=konsequenz, inline=False)
    emb.add_field(name="\U0001f4ca Warn-Stand",      value=f"{warn_symbol}  ({wc}/{_frak.MAX_WARNS})", inline=False)
    emb.set_footer(text=_frak.FRAK_FOOTER)

    try:
        ch = await bot.fetch_channel(_frak.FRAK_WARN_CHANNEL_ID)
        await ch.send(embed=emb)
    except Exception as e:
        await interaction.followup.send(f"\u274c Senden fehlgeschlagen: {e}", ephemeral=True)
        return

    await _frak.frak_update_list()
    await interaction.followup.send(
        f"\u2705 Warn f\u00fcr **{fraktion}** eingetragen ({wc}/{_frak.MAX_WARNS}).", ephemeral=True
    )


# -- /fraktions-sperre -----------------------------------------

@bot.tree.command(
    name="fraktions-sperre",
    description="[Fraktionsleitung] Sperrt eine Fraktion",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    fraktion="Name der Fraktion",
    grund="Grund f\u00fcr die Sperre",
    dauer="Dauer der Sperre (z. B. 7 Tage / permanent)",
)
async def fraktions_sperre_cmd(
    interaction: discord.Interaction,
    fraktion: str,
    grund: str,
    dauer: str,
):
    if not _frak.frak_hat_recht(interaction):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)

    emb = discord.Embed(
        title=f"\U0001f512 Fraktions-Sperre \u2014 {fraktion}",
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(name="\U0001f3db\ufe0f Fraktion", value=fraktion, inline=False)
    emb.add_field(name="\U0001f4cb Grund",          value=grund,    inline=False)
    emb.add_field(name="\u23f3 Dauer",              value=dauer,    inline=False)
    emb.set_footer(text=_frak.FRAK_FOOTER)

    try:
        ch = await bot.fetch_channel(_frak.FRAK_SPERRE_CHANNEL_ID)
        await ch.send(embed=emb)
    except Exception as e:
        await interaction.followup.send(f"\u274c Senden fehlgeschlagen: {e}", ephemeral=True)
        return

    await interaction.followup.send(
        f"\u2705 Sperre f\u00fcr **{fraktion}** gesendet.", ephemeral=True
    )


# -- /remove-frakwarn ------------------------------------------

@bot.tree.command(
    name="remove-frakwarn",
    description="[Fraktionsleitung] Entfernt einen Warn einer Fraktion",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(fraktion="Fraktion deren letzten Warn du entfernen m\u00f6chtest")
@app_commands.autocomplete(fraktion=_frak.frakwarn_autocomplete)
async def remove_frakwarn_cmd(
    interaction: discord.Interaction,
    fraktion: str,
):
    if not _frak.frak_hat_recht(interaction):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)

    data  = _frak.frak_load()
    entry = data.get(fraktion)

    if not entry or not entry.get("warns"):
        await interaction.followup.send(
            f"\u274c **{fraktion}** hat keine Warns.", ephemeral=True
        )
        return

    removed = entry["warns"].pop()
    _frak.frak_save(data)
    wc = len(entry["warns"])

    emb = discord.Embed(
        title=f"\u2705 Fraktions-Warn entfernt \u2014 {fraktion}",
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(name="\U0001f3db\ufe0f Fraktion",        value=fraktion,          inline=False)
    emb.add_field(name="\U0001f5d1\ufe0f Entfernter Warn", value=removed["grund"],  inline=False)
    emb.add_field(name="\U0001f4ca Verbleibende Warns",    value=f"{wc}/{_frak.MAX_WARNS}", inline=False)
    emb.set_footer(text=_frak.FRAK_FOOTER)

    try:
        ch = await bot.fetch_channel(_frak.FRAK_WARN_CHANNEL_ID)
        await ch.send(embed=emb)
    except Exception as e:
        await interaction.followup.send(f"\u274c Senden fehlgeschlagen: {e}", ephemeral=True)
        return

    await _frak.frak_update_list()
    await interaction.followup.send(
        f"\u2705 Warn von **{fraktion}** entfernt. Noch {wc}/{_frak.MAX_WARNS} Warns.", ephemeral=True
    )


# -- /frak-list ------------------------------------------------

@bot.tree.command(
    name="frak-list",
    description="[Fraktionsleitung] Aktualisiert die Fraktionsliste im Kanal",
    guild=discord.Object(id=GUILD_ID),
)
async def frak_list_cmd(interaction: discord.Interaction):
    if not _frak.frak_hat_recht(interaction):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await _frak.frak_update_list()
    await interaction.followup.send("\u2705 Fraktionsliste aktualisiert.", ephemeral=True)
