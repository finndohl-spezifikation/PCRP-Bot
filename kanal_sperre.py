# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# kanal_sperre.py — Server-weite Kanalsperre für Spieler
# Paradise City Roleplay Discord Bot
#
# /kanal-sperre   → Sperrt alle Kanäle wo @everyone schreiben darf
# /kanal-entsperren → Stellt die ursprünglichen Rechte wieder her
#
# Wichtig: Kanäle wo Spieler eh nicht schreiben dürfen werden
#           NICHT angefasst. Nur bereits freigeschaltete Kanäle
#           werden gesperrt/entsperrt.
# ══════════════════════════════════════════════════════════════

import json
import asyncio
from config import *

SPERRE_FILE = DATA_DIR / "kanal_sperre.json"

# ── Datei-Helfer ──────────────────────────────────────────────

def _load_sperre() -> dict:
    try:
        with open(SPERRE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_sperre(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SPERRE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _clear_sperre():
    if SPERRE_FILE.exists():
        SPERRE_FILE.unlink()


# ── /kanal-sperre ─────────────────────────────────────────────

@bot.tree.command(
    name="kanal-sperre",
    description="[Mod] Sperrt alle Kanäle für Spieler (nur Kanäle die sie nutzen dürfen)",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.default_permissions(manage_channels=True)
async def kanal_sperre(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    if _load_sperre():
        await interaction.response.send_message(
            "⚠️ Es ist bereits eine Kanalsperre aktiv.\n"
            "Nutze `/kanal-entsperren` um sie zuerst aufzuheben.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    guild        = interaction.guild
    everyone     = guild.default_role
    gesperrte    = {}   # {str(channel_id): "allow" | "neutral"}
    anzahl       = 0

    for channel in guild.channels:
        # Nur Text-Kanäle
        if not isinstance(channel, discord.TextChannel):
            continue

        # Aufgelöste Permission für @everyone prüfen
        resolved = channel.permissions_for(everyone)
        if not resolved.send_messages:
            # Spieler dürfen dort eh nicht schreiben → nicht anfassen
            continue

        # Originalen Overwrite-Wert merken (True = explizit erlaubt, None = geerbt)
        overwrite = channel.overwrites_for(everyone)
        original  = overwrite.send_messages  # True oder None

        # Auf False setzen
        overwrite.send_messages = False
        try:
            await channel.set_permissions(everyone, overwrite=overwrite)
            gesperrte[str(channel.id)] = "allow" if original is True else "neutral"
            anzahl += 1
        except discord.Forbidden:
            pass

        await asyncio.sleep(0.4)  # Rate-Limit einhalten

    _save_sperre(gesperrte)

    # Mod-Log
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="🔒 Kanalsperre aktiviert",
            description=(
                f"**Ausgeführt von:** {interaction.user.mention}\n"
                f"**Gesperrte Kanäle:** {anzahl}\n\n"
                "Spieler können in keinem freigeschalteten Kanal mehr schreiben.\n"
                f"Zum Aufheben: `/kanal-entsperren`"
            ),
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc),
        )
        await log_ch.send(embed=embed)

    await interaction.followup.send(
        f"🔒 **Kanalsperre aktiviert!**\n{anzahl} Kanäle wurden gesperrt.\n"
        f"Spieler können bis zur Entsperrung nirgends mehr schreiben.",
        ephemeral=True,
    )


# ── /kanal-entsperren ─────────────────────────────────────────

@bot.tree.command(
    name="kanal-entsperren",
    description="[Mod] Hebt die aktive Kanalsperre auf und stellt alle Rechte wieder her",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.default_permissions(manage_channels=True)
async def kanal_entsperren(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    gesperrte = _load_sperre()
    if not gesperrte:
        await interaction.response.send_message(
            "ℹ️ Es ist gerade keine Kanalsperre aktiv.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    guild    = interaction.guild
    everyone = guild.default_role
    anzahl   = 0

    for channel_id_str, original in gesperrte.items():
        channel = guild.get_channel(int(channel_id_str))
        if not channel:
            continue  # Kanal wurde zwischenzeitlich gelöscht → überspringen

        overwrite = channel.overwrites_for(everyone)

        if original == "allow":
            # War explizit erlaubt → wieder auf True setzen
            overwrite.send_messages = True
        else:
            # War geerbt (neutral) → Override entfernen damit Kategorie greift
            overwrite.send_messages = None

        try:
            # Falls der Overwrite jetzt komplett leer ist → ganz entfernen
            if overwrite.is_empty():
                await channel.set_permissions(everyone, overwrite=None)
            else:
                await channel.set_permissions(everyone, overwrite=overwrite)
            anzahl += 1
        except discord.Forbidden:
            pass

        await asyncio.sleep(0.4)  # Rate-Limit einhalten

    _clear_sperre()

    # Mod-Log
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(
            title="🔓 Kanalsperre aufgehoben",
            description=(
                f"**Ausgeführt von:** {interaction.user.mention}\n"
                f"**Wiederhergestellte Kanäle:** {anzahl}\n\n"
                "Alle Spieler können wieder normal schreiben."
            ),
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        await log_ch.send(embed=embed)

    await interaction.followup.send(
        f"🔓 **Kanalsperre aufgehoben!**\n{anzahl} Kanäle wurden wiederhergestellt.\n"
        "Alle Spieler können wieder normal schreiben.",
        ephemeral=True,
  )
