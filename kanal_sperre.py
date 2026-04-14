# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# kanal_sperre.py — Server-weite Kanalsperre für Spieler
# Paradise City Roleplay Discord Bot
#
# /kanal-sperre      → Sperrt alle definierten Kanäle,
#                       postet rotes Embed, blockiert Threads
# /kanal-entsperren  → Stellt Rechte wieder her, löscht Embeds
#
# Nur die Kanäle in SPERRE_CHANNEL_IDS werden angefasst.
# Alle anderen Kanäle bleiben unberührt.
# ══════════════════════════════════════════════════════════════

import json
import asyncio
from config import *

SPERRE_FILE = DATA_DIR / "kanal_sperre.json"

# ── Feste Channel-Liste ───────────────────────────────────────
# Nur diese Kanäle werden bei Sperre/Entsperrung angefasst.
# Kommentar-Kanäle = Nur Button-Interaktionen werden blockiert
SPIELER_ROLLE_ID = 1490855722534310003  # Rolle die gesperrt/entsperrt wird

# Kanäle wo nur Buttons blockiert werden (kein schreiben sowieso möglich)
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

# ── Datei-Helfer ──────────────────────────────────────────────

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


# ── Rotes Sperre-Embed ────────────────────────────────────────

def _build_sperre_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🔒  Kanal gesperrt — Lobby geschlossen",
        description=(
            "Die **Lobby ist aktuell geschlossen**, daher ist dieser Kanal gesperrt.\n"
            "Schreiben ist während der Sperrung nicht möglich.\n\n"
            "Sobald die Lobby wieder geöffnet wird, kannst du hier wieder schreiben."
        ),
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay • Kanalsperre")
    return embed


# ── /kanal-sperre ─────────────────────────────────────────────

@bot.tree.command(
    name="kanal-sperre",
    description="[Mod] Sperrt alle definierten Spieler-Kanäle und postet eine Meldung",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.default_permissions(manage_channels=True)
async def kanal_sperre(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    if _load():
        await interaction.response.send_message(
            "⚠️ Es ist bereits eine Kanalsperre aktiv.\n"
            "Nutze `/kanal-entsperren` um sie zuerst aufzuheben.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    guild        = interaction.guild
    spieler_role = guild.get_role(SPIELER_ROLLE_ID)
    if not spieler_role:
        await interaction.followup.send("❌ Spieler-Rolle nicht gefunden.", ephemeral=True)
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

        # Sperren — Button-Kanäle nur use_application_commands, Rest alles
        if ch_id in BUTTON_ONLY_CHANNEL_IDS:
            ow.use_application_commands = False
        else:
            ow.send_messages            = False
            ow.create_public_threads    = False
            ow.create_private_threads   = False
            ow.use_application_commands = False

        try:
            await channel.set_permissions(spieler_role, overwrite=ow)

            # Rotes Embed still senden — keine Ungelesen-Markierung für Mitglieder
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
            title="🔒 Kanalsperre aktiviert",
            description=(
                f"**Ausgeführt von:** {interaction.user.mention}\n"
                f"**Gesperrte Kanäle:** {gesperrt}"
                + (f"\n**Fehler:** {fehler}" if fehler else "")
                + "\n\nSpieler können in keinem der definierten Kanäle mehr schreiben oder Threads erstellen."
            ),
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc),
        )
        await log_ch.send(embed=embed)

    status = f"✅ {gesperrt} Kanäle gesperrt"
    if fehler:
        status += f"\n⚠️ {fehler} Kanäle konnten nicht gesperrt werden (fehlende Rechte?)"

    await interaction.followup.send(
        f"🔒 **Kanalsperre aktiviert!**\n{status}",
        ephemeral=True,
    )


# ── /kanal-entsperren ─────────────────────────────────────────

@bot.tree.command(
    name="kanal-entsperren",
    description="[Mod] Hebt die Kanalsperre auf und löscht alle Sperr-Embeds",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.default_permissions(manage_channels=True)
async def kanal_entsperren(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    data = _load()
    if not data:
        await interaction.response.send_message(
            "ℹ️ Es ist gerade keine Kanalsperre aktiv.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    guild        = interaction.guild
    spieler_role = guild.get_role(SPIELER_ROLLE_ID)
    if not spieler_role:
        await interaction.followup.send("❌ Spieler-Rolle nicht gefunden.", ephemeral=True)
        return
    restored = 0
    fehler   = 0

    # Embed-IDs aus gespeicherter JSON (zum Löschen der roten Embeds)
    embed_ids: dict = data.get("embeds", {})

    # Immer direkt über die feste Channel-Liste gehen — nicht über gespeicherte Daten
    for ch_id in SPERRE_CHANNEL_IDS:
        channel = guild.get_channel(ch_id)
        if not channel:
            continue

        try:
            ow = channel.overwrites_for(spieler_role)

            if ch_id in BUTTON_ONLY_CHANNEL_IDS:
                # Nur Buttons waren gesperrt → nur use_application_commands zurücksetzen
                ow.use_application_commands = None
                if ow.is_empty():
                    await channel.set_permissions(spieler_role, overwrite=None)
                else:
                    await channel.set_permissions(spieler_role, overwrite=ow)
            else:
                # Normale Kanäle → send_messages explizit auf True
                ow.send_messages            = True
                ow.create_public_threads    = None
                ow.create_private_threads   = None
                ow.use_application_commands = None
                await channel.set_permissions(spieler_role, overwrite=ow)

            # Rotes Sperre-Embed löschen
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

    # Daten-Datei löschen
    if SPERRE_FILE.exists():
        SPERRE_FILE.unlink()

    # Mod-Log
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="🔓 Kanalsperre aufgehoben",
            description=(
                f"**Ausgeführt von:** {interaction.user.mention}\n"
                f"**Wiederhergestellte Kanäle:** {restored}"
                + (f"\n**Fehler:** {fehler}" if fehler else "")
                + "\n\nAlle Spieler können wieder normal schreiben."
            ),
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        await log_ch.send(embed=embed)

    status = f"✅ {restored} Kanäle entsperrt"
    if fehler:
        status += f"\n⚠️ {fehler} Kanäle konnten nicht entsperrt werden"

    await interaction.followup.send(
        f"🔓 **Kanalsperre aufgehoben!**\n{status}",
        ephemeral=True,
              )
