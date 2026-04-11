# ══════════════════════════════════════════════════════════════
# beschlagnahmung.py — Fahrzeug-Beschlagnahmung & Inventar-Konfiszierung
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

import os, sys

# Sicherstellen dass bot_split/ im Pfad ist egal wo diese Datei liegt
_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in [
    os.path.join(_HERE, "bot_split"),   # liegt im Repo-Root → bot_split/ daneben
    _HERE,                               # liegt bereits in bot_split/
]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from config import *
from economy_helpers import load_economy, save_economy, get_user, find_inventory_item
import uuid

# Direkt definiert — funktioniert auch wenn config.py noch nicht aktualisiert wurde
BESCHLAGNAHMUNG_CHANNEL_ID = 1492316049922592990
BESCHLAGNAHMUNG_CHANNEL    = 1492316049922592990

if "BESCHLAGNAHMUNG_FILE" not in dir():
    from pathlib import Path as _Path
    BESCHLAGNAHMUNG_FILE = _Path(os.environ.get("DATA_DIR", _Path(__file__).parent / "data")) / "beschlagnahmung_data.json"
    BESCHLAGNAHMUNG_FILE.parent.mkdir(parents=True, exist_ok=True)


# ── JSON Helpers ─────────────────────────────────────────────

def load_beschlagnahmung():
    if BESCHLAGNAHMUNG_FILE.exists():
        with open(BESCHLAGNAHMUNG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_beschlagnahmung(data):
    with open(BESCHLAGNAHMUNG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Berechtigungs-Check ──────────────────────────────────────

def ist_lapd(member: discord.Member) -> bool:
    return any(r.id == LAPD_ROLE_ID for r in member.roles)


def channel_check(interaction: discord.Interaction) -> bool:
    return interaction.channel.id == BESCHLAGNAHMUNG_CHANNEL


# ── Autocomplete: Beschlagnahmte Fahrzeuge eines Spielers ────

async def fahrzeug_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    nutzer = interaction.namespace.nutzer
    if nutzer is None:
        return []
    data    = load_beschlagnahmung()
    einträge = data.get(str(nutzer.id), [])
    choices = [
        app_commands.Choice(name=e["fahrzeug"][:100], value=e["id"])
        for e in einträge
        if current.lower() in e["fahrzeug"].lower()
    ]
    return choices[:25]


# ══════════════════════════════════════════════════════════════
# /beschlagnahmen
# ══════════════════════════════════════════════════════════════

@bot.tree.command(
    name="beschlagnahmen",
    description="[LAPD] Fahrzeug eines Spielers beschlagnahmen",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    nutzer="Spieler dessen Fahrzeug beschlagnahmt wird",
    fahrzeug="Fahrzeugbezeichnung (z.B. BMW M3, Kennzeichen XY-123)",
    grund="Grund der Beschlagnahmung (optional)",
)
async def beschlagnahmen_cmd(
    interaction: discord.Interaction,
    nutzer: discord.Member,
    fahrzeug: str,
    grund: str = "Kein Grund angegeben",
):
    if not channel_check(interaction):
        await interaction.response.send_message(
            f"❌ Diesen Command kannst du nur in <#{BESCHLAGNAHMUNG_CHANNEL}> benutzen.",
            ephemeral=True,
        )
        return
    if not ist_lapd(interaction.user):
        await interaction.response.send_message("❌ Nur LAPD darf Fahrzeuge beschlagnahmen.", ephemeral=True)
        return

    eintrag = {
        "id":          str(uuid.uuid4())[:8],
        "fahrzeug":    fahrzeug,
        "grund":       grund,
        "von_id":      interaction.user.id,
        "von_display": interaction.user.display_name,
        "datum":       datetime.now(timezone.utc).isoformat(),
    }

    data = load_beschlagnahmung()
    uid  = str(nutzer.id)
    data.setdefault(uid, []).append(eintrag)
    save_beschlagnahmung(data)

    embed = discord.Embed(
        title="🚔 Fahrzeug beschlagnahmt",
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Spieler",     value=nutzer.mention,              inline=True)
    embed.add_field(name="Fahrzeug",    value=fahrzeug,                    inline=True)
    embed.add_field(name="Beamter",     value=interaction.user.mention,    inline=True)
    embed.add_field(name="Grund",       value=grund,                       inline=False)
    embed.add_field(name="Eintrags-ID", value=f"`{eintrag['id']}`",        inline=True)
    embed.set_footer(text="Cryptik Roleplay — LAPD Beschlagnahmung")
    await interaction.response.send_message(content=nutzer.mention, embed=embed)

    # DM an den Spieler
    try:
        dm_embed = discord.Embed(
            title="🚔 Dein Fahrzeug wurde beschlagnahmt",
            description=f"**{fahrzeug}** wurde von der LAPD beschlagnahmt.",
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc),
        )
        dm_embed.add_field(name="Grund",    value=grund,                       inline=False)
        dm_embed.add_field(name="Beamter",  value=interaction.user.display_name, inline=True)
        dm_embed.set_footer(text="Cryptik Roleplay — LAPD")
        await nutzer.send(embed=dm_embed)
    except discord.Forbidden:
        pass


# ══════════════════════════════════════════════════════════════
# /remove-beschlagnahmung
# ══════════════════════════════════════════════════════════════

@bot.tree.command(
    name="remove-beschlagnahmung",
    description="[LAPD] Fahrzeugbeschlagnahmung rückgängig machen",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    nutzer="Spieler dessen Beschlagnahmung aufgehoben wird",
    fahrzeug="Fahrzeug (aus der Liste auswählen)",
)
@app_commands.autocomplete(fahrzeug=fahrzeug_autocomplete)
async def remove_beschlagnahmung_cmd(
    interaction: discord.Interaction,
    nutzer: discord.Member,
    fahrzeug: str,
):
    if not channel_check(interaction):
        await interaction.response.send_message(
            f"❌ Diesen Command kannst du nur in <#{BESCHLAGNAHMUNG_CHANNEL}> benutzen.",
            ephemeral=True,
        )
        return
    if not ist_lapd(interaction.user):
        await interaction.response.send_message("❌ Nur LAPD darf Beschlagnahmungen aufheben.", ephemeral=True)
        return

    data  = load_beschlagnahmung()
    uid   = str(nutzer.id)
    liste = data.get(uid, [])

    # Suche per ID (Autocomplete) oder Fahrzeugname
    treffer = next((e for e in liste if e["id"] == fahrzeug or e["fahrzeug"].lower() == fahrzeug.lower()), None)

    if not treffer:
        await interaction.response.send_message(
            f"❌ Keine Beschlagnahmung für **{nutzer.display_name}** mit diesem Fahrzeug gefunden.",
            ephemeral=True,
        )
        return

    data[uid] = [e for e in liste if e["id"] != treffer["id"]]
    save_beschlagnahmung(data)

    embed = discord.Embed(
        title="✅ Beschlagnahmung aufgehoben",
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Spieler",  value=nutzer.mention,           inline=True)
    embed.add_field(name="Fahrzeug", value=treffer["fahrzeug"],      inline=True)
    embed.add_field(name="Beamter",  value=interaction.user.mention, inline=True)
    embed.set_footer(text="Cryptik Roleplay — LAPD Beschlagnahmung")
    await interaction.response.send_message(content=nutzer.mention, embed=embed)

    # DM an den Spieler
    try:
        dm_embed = discord.Embed(
            title="✅ Dein Fahrzeug wurde freigegeben",
            description=f"**{treffer['fahrzeug']}** wurde von der LAPD freigegeben.",
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        dm_embed.add_field(name="Freigegeben von", value=interaction.user.display_name, inline=True)
        dm_embed.set_footer(text="Cryptik Roleplay — LAPD")
        await nutzer.send(embed=dm_embed)
    except discord.Forbidden:
        pass


# ══════════════════════════════════════════════════════════════
# /konfiszieren — Item aus Inventar entfernen (LAPD)
# ══════════════════════════════════════════════════════════════

@bot.tree.command(
    name="konfiszieren",
    description="[LAPD] Item aus dem Inventar eines Spielers entfernen",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    nutzer="Spieler dem das Item entnommen wird",
    item="Name des Items",
    menge="Anzahl (Standard: 1)",
)
async def konfiszieren_cmd(
    interaction: discord.Interaction,
    nutzer: discord.Member,
    item: str,
    menge: int = 1,
):
    if not channel_check(interaction):
        await interaction.response.send_message(
            f"❌ Diesen Command kannst du nur in <#{BESCHLAGNAHMUNG_CHANNEL}> benutzen.",
            ephemeral=True,
        )
        return
    if not ist_lapd(interaction.user):
        await interaction.response.send_message("❌ Nur LAPD darf Items konfiszieren.", ephemeral=True)
        return
    if menge < 1:
        await interaction.response.send_message("❌ Menge muss mindestens 1 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    inventar  = user_data.get("inventory", [])

    entfernt = []
    for _ in range(menge):
        match = find_inventory_item(inventar, item)
        if not match:
            break
        inventar.remove(match)
        entfernt.append(match)

    if not entfernt:
        await interaction.response.send_message(
            f"❌ **{nutzer.display_name}** besitzt kein Item namens **{item}**.",
            ephemeral=True,
        )
        return

    user_data["inventory"] = inventar
    save_economy(eco)

    embed = discord.Embed(
        title="📦 Item konfisziert",
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Spieler",  value=nutzer.mention,              inline=True)
    embed.add_field(name="Item",     value=entfernt[0],                 inline=True)
    embed.add_field(name="Menge",    value=str(len(entfernt)),          inline=True)
    embed.add_field(name="Beamter",  value=interaction.user.mention,    inline=True)
    embed.set_footer(text="Cryptik Roleplay — LAPD Konfiszierung")
    await interaction.response.send_message(content=nutzer.mention, embed=embed)
