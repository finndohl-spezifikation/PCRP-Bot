# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# channel_format.py — Automatische Kursiv-Formatierung von Channel-Namen
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════
#
# Funktionen:
#   • to_italic_unicode(text)       — ASCII → kursiv Unicode (erster Buchstabe + nach "-" groß)
#   • capitalize_italic_name(name)  — bestehende kursive Namen korrigieren (ersten Buchstaben großschreiben)
#   • /channel-format               — Alle Channel im Server einmalig formatieren (Admin only)
#   • on_guild_channel_create       — Neue Channel werden automatisch formatiert
#
# In bot.py eintragen:
#   import channel_format
# ══════════════════════════════════════════════════════════════

import discord
from config import bot, GUILD_ID, ADMIN_ROLE_ID

# ── Unicode-Bereiche ──────────────────────────────────────────
_ITALIC_LOWER_START = 0x1D622   # 𝘢
_ITALIC_LOWER_END   = 0x1D63B   # 𝘻
_ITALIC_UPPER_START = 0x1D608   # 𝘈
_LOWER_TO_UPPER_OFFSET = 26     # Differenz zwischen kursiv-Groß und kursiv-Klein


def to_italic_unicode(text: str) -> str:
    """
    Wandelt einen normalen ASCII-Text in kursive Unicode-Zeichen um.
    Der erste Buchstabe und jeder Buchstabe nach einem '-' wird großgeschrieben.

    Beispiel: "beispiel-channel" → "𝘉𝘦𝘪𝘴𝘱𝘪𝘦𝘭-𝘊𝘩𝘢𝘯𝘯𝘦𝘭"
    """
    result = []
    capitalize_next = True

    for char in text:
        if char == '-':
            result.append('-')
            capitalize_next = True
        elif 'a' <= char <= 'z':
            if capitalize_next:
                result.append(chr(_ITALIC_UPPER_START + ord(char) - ord('a')))
            else:
                result.append(chr(_ITALIC_LOWER_START + ord(char) - ord('a')))
            capitalize_next = False
        elif 'A' <= char <= 'Z':
            result.append(chr(_ITALIC_UPPER_START + ord(char) - ord('A')))
            capitalize_next = False
        else:
            result.append(char)
            if char not in (' ',):
                capitalize_next = False

    return ''.join(result)


def capitalize_italic_name(name: str) -> str:
    """
    Korrigiert einen bereits kursiven Channel-Namen:
    Macht den ersten Buchstaben und jeden Buchstaben nach '-' großgeschrieben.

    Beispiel: "𝘣𝘦𝘪𝘴𝘱𝘪𝘦𝘭-𝘊𝘩𝘢𝘯𝘯𝘦𝘭" → "𝘉𝘦𝘪𝘴𝘱𝘪𝘦𝘭-𝘊𝘩𝘢𝘯𝘯𝘦𝘭"
    """
    result = []
    capitalize_next = True

    for char in name:
        cp = ord(char)
        if char == '-':
            result.append('-')
            capitalize_next = True
        elif _ITALIC_LOWER_START <= cp <= _ITALIC_LOWER_END and capitalize_next:
            result.append(chr(cp - _LOWER_TO_UPPER_OFFSET))
            capitalize_next = False
        else:
            result.append(char)
            if char not in (' ',):
                capitalize_next = False

    return ''.join(result)


def _needs_fix(name: str) -> bool:
    """Gibt True zurück wenn der Name korrigiert werden muss."""
    return capitalize_italic_name(name) != name


# ── Slash Command: /channel-format ───────────────────────────

@bot.tree.command(
    name="channel-format",
    description="Formatiert alle Channel-Namen kursiv mit großem Anfangsbuchstaben.",
    guild=discord.Object(id=GUILD_ID)
)
async def channel_format_cmd(interaction: discord.Interaction):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung für diesen Befehl.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    renamed = 0
    skipped = 0
    errors = 0

    for channel in interaction.guild.channels:
        new_name = to_italic_unicode(channel.name)
        if new_name == channel.name:
            skipped += 1
            continue
        try:
            await channel.edit(name=new_name, reason="channel-format: Kursiv-Großschreibung korrigiert")
            renamed += 1
        except Exception as e:
            print(f"[channel_format] ❌ Fehler bei #{channel.name}: {e}")
            errors += 1

    await interaction.followup.send(
        f"✅ Fertig!\n"
        f"**Umbenannt:** {renamed}\n"
        f"**Bereits korrekt:** {skipped}\n"
        f"**Fehler:** {errors}",
        ephemeral=True
    )


# ── Event: Neuer Channel wird automatisch formatiert ─────────

@bot.event
async def on_guild_channel_create(channel):
    new_name = to_italic_unicode(channel.name)
    if new_name != channel.name:
        try:
            await channel.edit(name=new_name, reason="channel-format: Automatische Kursiv-Formatierung")
        except Exception as e:
            print(f"[channel_format] ❌ Auto-Format Fehler bei #{channel.name}: {e}")
