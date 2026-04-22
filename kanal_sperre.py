# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# kanal_sperre.py \u2014 Server-weite Kanalsperre f\u00FCr Spieler
# Paradise City Roleplay Discord Bot
#
# /kanal-sperre      \u2192 Sperrt alle definierten Kan\u00E4le,
#                       postet rotes Embed, blockiert Threads
# /kanal-entsperren  \u2192 Stellt Rechte wieder her, l\u00F6scht Embeds
#
# Nur die Kan\u00E4le in SPERRE_CHANNEL_IDS werden angefasst.
# Alle anderen Kan\u00E4le bleiben unber\u00FChrt.
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

import json
import asyncio
from config import *

SPERRE_FILE = DATA_DIR / "kanal_sperre.json"

# \u2500\u2500 Feste Channel-Liste \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Nur diese Kan\u00E4le werden bei Sperre/Entsperrung angefasst.
# Kommentar-Kan\u00E4le = Nur Button-Interaktionen werden blockiert
SPIELER_ROLLE_ID = 1490855722534310003  # Rolle die gesperrt/entsperrt wird

# Kan\u00E4le wo nur Buttons blockiert werden (kein schreiben sowieso m\u00F6glich)
BUTTON_ONLY_CHANNEL_IDS: set[int] = {
    1490889784753782784,  # Rubbellose
    1492636063817138216,  # Lotto
}

SPERRE_CHANNEL_IDS: list[int] = [
    1491116234459185162,
    1491623633792143512,
    1490882588049408180,
    1492282065490546698,
    1490882589014364250,
    1490882590012604538,
    1490882591023173682,
    1490882596668707017,
    1490882592445304972,
    1490889784753782784,   # Button-Kanal
    1492636063817138216,   # Button-Kanal
    1490890319242461346,
    1492128730141954178,
    1490890320412672150,
    1490890321276702723,
    1490890348254200049,
    1490890349382734044,
    1492314171373649983,
    1490890311755628584,
    1492976742497783818,
    1492977067665526804,
    1490894244733255872,
    1490894246587404380,
    1490894250286649365,
    1490894253059080232,
    1490894255474872392,
    1490894290455498802,
    1490894294297477120,
    1490894296952344616,
    1490894299293024517,
    1490894301339713667,
    1490894262919893113,
    1490894266396967096,
    1490894274437447690,
    1493246459062128873,
    1490894309145313330,
    1490894311389134858,
    1490894314132213771,
    1490894317462753280,
    1490894320604020806,
]

# \u2500\u2500 Datei-Helfer \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _load() -> dict:
    try:
        with open(SPERRE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SPERRE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _ow_to_dict(ow: discord.PermissionOverwrite) -> dict:
    """Speichert alle explizit gesetzten Felder eines Overwrites."""
    result = {}
    for name, value in ow:
        if value is not None:
            result[name] = value  # True oder False
    return result


def _dict_to_ow(d: dict) -> discord.PermissionOverwrite:
    """Stellt einen Overwrite exakt aus gespeicherten Daten wieder her."""
    return discord.PermissionOverwrite(**d)


# \u2500\u2500 Rotes Sperre-Embed \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_sperre_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\U0001F512  Kanal gesperrt \u2014 Lobby geschlossen",
        description=(
            "Die **Lobby ist aktuell geschlossen**, daher ist dieser Kanal gesperrt.\n"
            "Schreiben ist w\u00E4hrend der Sperrung nicht m\u00F6glich.\n\n"
            "Sobald die Lobby wieder ge\u00F6ffnet wird, kannst du hier wieder schreiben."
        ),
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Kanalsperre")
    return embed


# \u2500\u2500 /kanal-sperre \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="kanal-sperre",
    description="[Mod] Sperrt alle definierten Spieler-Kan\u00E4le und postet eine Meldung",
    guild=discord.Object(id=GUILD_ID),
)
async def kanal_sperre(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    if _load():
        await interaction.response.send_message(
            "\u26A0\uFE0F Es ist bereits eine Kanalsperre aktiv.\n"
            "Nutze `/kanal-entsperren` um sie zuerst aufzuheben.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    guild        = interaction.guild
    spieler_role = guild.get_role(SPIELER_ROLLE_ID)
    if not spieler_role:
        await interaction.followup.send("\u274C Spieler-Rolle nicht gefunden.", ephemeral=True)
        return
    data     = {"channels": {}, "embeds": {}}
    gesperrt = 0
    fehler   = 0

    for ch_id in SPERRE_CHANNEL_IDS:
        channel = guild.get_channel(ch_id)
        if not channel:
            continue

        # Kompletten originalen Overwrite sichern
        ow = channel.overwrites_for(spieler_role)
        data["channels"][str(ch_id)] = _ow_to_dict(ow)

        # Sperren \u2014 Button-Kan\u00E4le nur use_application_commands, Rest alles
        if ch_id in BUTTON_ONLY_CHANNEL_IDS:
            ow.use_application_commands = False
        else:
            ow.send_messages            = False
            ow.create_public_threads    = False
            ow.create_private_threads   = False
            ow.use_application_commands = False

        try:
            await channel.set_permissions(spieler_role, overwrite=ow)

            # Rotes Embed still senden \u2014 keine Ungelesen-Markierung f\u00FCr Mitglieder
            msg = await channel.send(embed=_build_sperre_embed(), silent=True)
            data["embeds"][str(ch_id)] = msg.id
            gesperrt += 1
        except (discord.Forbidden, discord.HTTPException):
            fehler += 1

        await asyncio.sleep(0.5)

    _save(data)

    # Mod-Log
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="\U0001F512 Kanalsperre aktiviert",
            description=(
                f"**Ausgef\u00FChrt von:** {interaction.user.mention}\n"
                f"**Gesperrte Kan\u00E4le:** {gesperrt}"
                + (f"\n**Fehler:** {fehler}" if fehler else "")
                + "\n\nSpieler k\u00F6nnen in keinem der definierten Kan\u00E4le mehr schreiben oder Threads erstellen."
            ),
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc),
        )
        await log_ch.send(embed=embed)

    status = f"\u2705 {gesperrt} Kan\u00E4le gesperrt"
    if fehler:
        status += f"\n\u26A0\uFE0F {fehler} Kan\u00E4le konnten nicht gesperrt werden (fehlende Rechte?)"

    await interaction.followup.send(
        f"\U0001F512 **Kanalsperre aktiviert!**\n{status}",
        ephemeral=True,
    )


# \u2500\u2500 /kanal-entsperren \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="kanal-entsperren",
    description="[Mod] Hebt die Kanalsperre auf und l\u00F6scht alle Sperr-Embeds",
    guild=discord.Object(id=GUILD_ID),
)
async def kanal_entsperren(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    data = _load()
    if not data:
        await interaction.response.send_message(
            "\u2139\uFE0F Es ist gerade keine Kanalsperre aktiv.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    guild        = interaction.guild
    spieler_role = guild.get_role(SPIELER_ROLLE_ID)
    if not spieler_role:
        await interaction.followup.send("\u274C Spieler-Rolle nicht gefunden.", ephemeral=True)
        return
    restored = 0
    fehler   = 0

    # Embed-IDs aus gespeicherter JSON (zum L\u00F6schen der roten Embeds)
    embed_ids: dict = data.get("embeds", {})

    # Immer direkt \u00FCber die feste Channel-Liste gehen \u2014 nicht \u00FCber gespeicherte Daten
    for ch_id in SPERRE_CHANNEL_IDS:
        channel = guild.get_channel(ch_id)
        if not channel:
            continue

        try:
            ow = channel.overwrites_for(spieler_role)

            if ch_id in BUTTON_ONLY_CHANNEL_IDS:
                # Nur Buttons waren gesperrt \u2192 nur use_application_commands zur\u00FCcksetzen
                ow.use_application_commands = None
                if ow.is_empty():
                    await channel.set_permissions(spieler_role, overwrite=None)
                else:
                    await channel.set_permissions(spieler_role, overwrite=ow)
            else:
                # Normale Kan\u00E4le \u2192 send_messages explizit auf True
                ow.send_messages            = True
                ow.create_public_threads    = None
                ow.create_private_threads   = None
                ow.use_application_commands = None
                await channel.set_permissions(spieler_role, overwrite=ow)

            # Rotes Sperre-Embed l\u00F6schen
            msg_id = embed_ids.get(str(ch_id))
            if msg_id:
                try:
                    msg = await channel.fetch_message(int(msg_id))
                    await msg.delete()
                except (discord.NotFound, discord.HTTPException):
                    pass

            restored += 1
        except (discord.Forbidden, discord.HTTPException):
            fehler += 1

        await asyncio.sleep(0.5)

    # Daten-Datei l\u00F6schen
    if SPERRE_FILE.exists():
        SPERRE_FILE.unlink()

    # Mod-Log
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="\U0001F513 Kanalsperre aufgehoben",
            description=(
                f"**Ausgef\u00FChrt von:** {interaction.user.mention}\n"
                f"**Wiederhergestellte Kan\u00E4le:** {restored}"
                + (f"\n**Fehler:** {fehler}" if fehler else "")
                + "\n\nAlle Spieler k\u00F6nnen wieder normal schreiben."
            ),
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        await log_ch.send(embed=embed)

    status = f"\u2705 {restored} Kan\u00E4le entsperrt"
    if fehler:
        status += f"\n\u26A0\uFE0F {fehler} Kan\u00E4le konnten nicht entsperrt werden"

    await interaction.followup.send(
        f"\U0001F513 **Kanalsperre aufgehoben!**\n{status}",
        ephemeral=True,
              )
