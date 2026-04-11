# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# help_embed.py — Automatisches Command-Übersicht Embed
# Paradise City Roleplay Discord Bot
#
# Liest alle registrierten Slash-Commands aus dem Bot-Tree,
# gruppiert sie nach Kategorie-Präfix ([Kategorie]) und
# postet / aktualisiert ein hellblaues Embed im Info-Kanal.
#
# Speichert die Nachrichten-ID in data/help_message_id.json
# damit die Nachricht bei jedem Neustart editiert wird.
# ══════════════════════════════════════════════════════════════

import re
import json
import os
from config import *

HELP_CHANNEL_ID  = 1491624319598460958
MESSAGE_ID_FILE  = str(DATA_DIR / "help_message_id.json")
EMBED_COLOR      = 0xE67E22   # Hellblau

# ── Kategorie-Konfiguration ────────────────────────────────────
# Schlüssel = Präfix in der Command-Beschreibung ([Präfix])
# Wert      = (Emoji, Anzeigename, Wer darf es nutzen)
CATEGORY_MAP = {
    "Konto":    ("💰", "Konto",                   "Alle Spieler"),
    "Inventar": ("🎒", "Inventar",                "Alle Spieler"),
    "Shop":     ("🏪", "Shop",                    "Alle Spieler / Shop-Admin"),
    "Ausweis":  ("🪪", "Ausweis",                 "Bürger / Admin / Mod"),
    "Behörde":  ("🚗", "Führerschein / Behörde",  "Behörden-Team"),
}

# Staff-only Kategorien (Warn, Admin, Team, LOBBY, Allgemein) werden nicht angezeigt
HIDDEN_CATEGORIES = {"Warn", "Admin", "Team", "LOBBY", "Allgemein"}

CATEGORY_ORDER = [
    "Konto", "Inventar", "Shop", "Ausweis", "Behörde", "__other__",
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
    return match.group(1) if match else "__other__"


def _build_embed(commands: list) -> discord.Embed:
    grouped = {}
    for cmd in commands:
        prefix = _get_prefix(cmd.description)
        if prefix in HIDDEN_CATEGORIES:
            continue
        grouped.setdefault(prefix, []).append(f"`/{cmd.name}` — {cmd.description}")

    total = sum(len(v) for v in grouped.values())

    embed = discord.Embed(
        title="📋 Paradise City Roleplay — Bot Commands",
        description=(
            "Hier findest du alle verfügbaren Slash-Commands des Servers,\n"
            "sortiert nach Kategorie. Tippe `/` um sie zu nutzen.\n\u200b"
        ),
        color=EMBED_COLOR,
        timestamp=datetime.now(timezone.utc),
    )

    for key in CATEGORY_ORDER:
        if key not in grouped:
            continue
        if key == "__other__":
            emoji, cat_name, who = "📌", "Sonstiges", "Alle"
        else:
            emoji, cat_name, who = CATEGORY_MAP.get(key, ("📌", key, "Team"))

        lines = "\n".join(grouped[key])
        embed.add_field(
            name=f"{emoji}  {cat_name}",
            value=f"**Zugriff:** {who}\n{lines}\n\u200b",
            inline=False,
        )

    embed.set_footer(
        text=f"📊 Insgesamt {total} aktive Command{'s' if total != 1 else ''} | Automatisch aktualisiert"
    )
    return embed


async def update_help_embed():
    guild   = bot.get_guild(GUILD_ID)
    channel = guild and guild.get_channel(HELP_CHANNEL_ID)
    if not channel:
        print(f"[help_embed] ❌ Kanal {HELP_CHANNEL_ID} nicht gefunden.")
        return

    commands = bot.tree.get_commands(guild=discord.Object(id=GUILD_ID))
    if not commands:
        print("[help_embed] ⚠️ Keine Commands im Tree gefunden.")
        return

    embed      = _build_embed(commands)
    message_id = _load_message_id()

    if message_id:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(embed=embed)
            print(f"[help_embed] ✅ Embed aktualisiert (ID {message_id})")
            return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"[help_embed] ⚠️ Edit fehlgeschlagen: {e}")

    msg = await channel.send(embed=embed)
    _save_message_id(msg.id)
    print(f"[help_embed] ✅ Neues Embed gesendet (ID {msg.id})")


@bot.tree.command(
    name="help-update",
    description="[Admin] Aktualisiert das Command-Übersicht Embed manuell",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.default_permissions(administrator=True)
async def help_update(interaction: discord.Interaction):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    await update_help_embed()
    await interaction.followup.send("✅ Embed erfolgreich aktualisiert!", ephemeral=True)
