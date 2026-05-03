# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════════════════════
# help_embed.py — Automatisches Command-Übersicht Embed
# Paradise City Roleplay Discord Bot
#
# Liest alle registrierten Slash-Commands aus dem Bot-Tree,
# gruppiert sie nach Kategorie-Präfix ([Kategorie]) und
# postet / aktualisiert ein Embed im Info-Kanal.
#
# Speichert die Nachrichten-ID in data/help_message_id.json
# damit die Nachricht bei jedem Neustart editiert wird.
# ══════════════════════════════════════════════════════════════════════════════

import re
import json
import os
from config import *

HELP_CHANNEL_ID  = 1491624319598460958
MESSAGE_ID_FILE  = str(DATA_DIR / "help_message_id.json")
EMBED_COLOR      = 0xE67E22

# ── Kategorie-Konfiguration ────────────────────────────────────────────────
# Schlüssel = Präfix in der Command-Beschreibung ([Präfix])
# Wert      = (Emoji, Anzeigename, Wer darf es nutzen)
CATEGORY_MAP = {
    "Konto":        ("\U0001f4b0", "Konto",                    "Alle Spieler"),
    "Inventar":     ("\U0001f392", "Inventar",                 "Alle Spieler"),
    "Shop":         ("\U0001f3ea", "Shop",                     "Alle Spieler / Shop-Admin"),
    "Ausweis":      ("\U0001faaa", "Ausweis",                  "Bürger / Admin / Mod"),
    "Behörde":      ("\U0001f697", "Führerschein / Behörde",   "Behörden-Team"),
    "IC":           ("\U0001f3ad", "IC Aktionen",              "Alle Spieler"),
    "Aktien":       ("\U0001f4c8", "Aktienmarkt",              "Alle Spieler"),
    "Angeln":       ("\U0001f3a3", "Angeln",                   "Alle Spieler"),
    "Angler Shop":  ("\U0001f3ea", "Angler Shop",              "Alle Spieler"),
    "Lotto":        ("\U0001f3b0", "Lotto",                    "Alle Spieler"),
    "Casino":       ("\U0001f3b2", "Casino",                   "Alle Spieler"),
    "Bingo":        ("\U0001f4b0", "Bingo",                    "Alle Spieler"),
    "Weed":         ("\U0001f33f", "Weed-Farm",                "Alle Spieler"),
    "Kokain":       ("\u2697\ufe0f", "Kokain-Labor",           "Alle Spieler"),
    "Fraktion":     ("\U0001f3f3\ufe0f", "Fraktionen",         "Alle Spieler"),
    "Einreise":     ("\u2708\ufe0f", "Einreise",               "Alle Spieler"),
    "Sonstiges":    ("\U0001f4cc", "Sonstiges",                "Alle Spieler"),
}

# Commands ohne [Kategorie]-Präfix werden hier manuell zugeordnet
NAME_CATEGORY_MAP: dict[str, str] = {
    "erste-hilfe":    "IC",
    "ortung":         "IC",
    "fesseln":        "IC",
    "aktie-kaufen":   "Aktien",
    "aktie-verkaufen":"Aktien",
    "depot":          "Aktien",
    "ausweisen":      "Ausweis",
    "ausweis-remove": "Ausweis",
}

# Staff-only Kategorien werden NICHT angezeigt
HIDDEN_CATEGORIES = {"Warn", "Admin", "Mod", "Team", "LOBBY", "Allgemein"}

CATEGORY_ORDER = [
    "Konto", "Inventar", "Shop", "Ausweis", "Behörde", "IC", "Aktien",
    "Angeln", "Angler Shop", "Lotto", "Casino", "Bingo",
    "Weed", "Kokain", "Fraktion", "Einreise", "Sonstiges",
]


def _load_message_id():
    try:
        with open(MESSAGE_ID_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return int(data.get("message_id", 0)) or None
    except Exception:
        return None


def _save_message_id(message_id: int):
    os.makedirs("data", exist_ok=True)
    with open(MESSAGE_ID_FILE, "w", encoding="utf-8") as f:
        json.dump({"message_id": message_id}, f)


def _get_prefix(description: str) -> str:
    match = re.match(r"\[([^\]]+)\]", description)
    # Kein Präfix → landet in Sonstiges
    return match.group(1) if match else "Sonstiges"


def _strip_prefix(description: str) -> str:
    """Entfernt den [Kategorie]-Präfix aus der Command-Beschreibung."""
    return re.sub(r"^\[[^\]]+\]\s*", "", description)


def _build_embed(commands: list) -> discord.Embed:
    grouped = {}
    for cmd in commands:
        # Zuerst prüfen ob Command manuell einer Kategorie zugeordnet ist
        if cmd.name in NAME_CATEGORY_MAP:
            category = NAME_CATEGORY_MAP[cmd.name]
        else:
            category = _get_prefix(cmd.description)

        if category in HIDDEN_CATEGORIES:
            continue

        # Unbekannte Kategorien → Sonstiges
        if category not in CATEGORY_MAP:
            category = "Sonstiges"

        clean_desc = _strip_prefix(cmd.description)
        grouped.setdefault(category, []).append((cmd.name, clean_desc))

    total = sum(len(v) for v in grouped.values())

    embed = discord.Embed(
        title="\U0001f4cb Paradise City Roleplay \u2014 Commands",
        description=(
            "Alle verfügbaren Slash-Commands auf einem Blick.\n"
            "Tippe `/` um loszulegen.\n\u200b"
        ),
        color=EMBED_COLOR,
        timestamp=datetime.now(timezone.utc),
    )

    for key in CATEGORY_ORDER:
        if key not in grouped:
            continue
        emoji, cat_name, who = CATEGORY_MAP.get(key, ("\U0001f4cc", key, "Alle"))

        lines = "\n".join(
            f"\u2570 `/{name}` \u2014 {desc}"
            for name, desc in sorted(grouped[key], key=lambda x: x[0])
        )

        embed.add_field(
            name=f"{emoji}  **{cat_name}**",
            value=f"*Zugriff: {who}*\n{lines}\n\u200b",
            inline=False,
        )

    embed.set_footer(text=f"Paradise City Roleplay  \u2022  {total} Commands verfügbar")
    return embed


async def update_help_embed():
    guild   = bot.get_guild(GUILD_ID)
    channel = guild and guild.get_channel(HELP_CHANNEL_ID)
    if not channel:
        print(f"[help_embed] \u274c Kanal {HELP_CHANNEL_ID} nicht gefunden.")
        return

    commands = bot.tree.get_commands(guild=discord.Object(id=GUILD_ID))
    if not commands:
        print("[help_embed] \u26a0\ufe0f Keine Commands im Tree gefunden.")
        return

    embed      = _build_embed(commands)
    message_id = _load_message_id()

    if message_id:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(embed=embed)
            print(f"[help_embed] \u2705 Embed aktualisiert (ID {message_id})")
            return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"[help_embed] \u26a0\ufe0f Edit fehlgeschlagen: {e}")

    msg = await channel.send(embed=embed)
    _save_message_id(msg.id)
    print(f"[help_embed] \u2705 Neues Embed gesendet (ID {msg.id})")


@bot.tree.command(
    name="help-update",
    description="Aktualisiert das Command-Übersicht Embed manuell",
    guild=discord.Object(id=GUILD_ID),
)
async def help_update(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await update_help_embed()
    await interaction.followup.send("\u2705 Embed erfolgreich aktualisiert!", ephemeral=True)
