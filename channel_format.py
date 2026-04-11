
# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# channel_format.py — Automatische Kursiv-Formatierung von Channel-Namen
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════
#
# Funktionen:
#   • /channel-format   — Alle Channel kursiv + Anfangsbuchstabe groß (Admin only)
#   • on_guild_channel_create — Neue Channel automatisch formatieren
#
# In bot.py eintragen:
#   import channel_format
# ══════════════════════════════════════════════════════════════

import discord
from config import bot, GUILD_ID, ADMIN_ROLE_ID

# ── Unicode-Bereiche ──────────────────────────────────────────
_IL = 0x1D622   # kursiv-klein a
_IU = 0x1D608   # kursiv-groß  A


def _italic_to_ascii(name: str) -> str:
    """Wandelt kursive Unicode-Zeichen zurück in normales ASCII (Kleinbuchstaben)."""
    out = []
    for ch in name:
        cp = ord(ch)
        if _IL <= cp <= _IL + 25:           # kursiv-klein a–z
            out.append(chr(cp - _IL + ord('a')))
        elif _IU <= cp <= _IU + 25:         # kursiv-groß A–Z
            out.append(chr(cp - _IU + ord('a')))
        else:
            out.append(ch)
    return ''.join(out)


def _ascii_to_italic(name: str) -> str:
    """
    Wandelt normalen ASCII-Text in kursive Unicode-Zeichen um.
    Erster Buchstabe und jeder Buchstabe nach '-' wird GROßGESCHRIEBEN.
    """
    out = []
    cap = True
    for ch in name:
        if ch == '-':
            out.append('-')
            cap = True
        elif 'a' <= ch <= 'z':
            out.append(chr((_IU if cap else _IL) + ord(ch) - ord('a')))
            cap = False
        elif 'A' <= ch <= 'Z':
            out.append(chr(_IU + ord(ch) - ord('A')))
            cap = False
        else:
            out.append(ch)
            cap = False
    return ''.join(out)


def format_channel_name(name: str) -> str:
    """
    Egal ob der Name schon kursiv ist oder normales ASCII:
    Immer korrekt kursiv + Anfangsbuchstabe groß zurückgeben.
    """
    return _ascii_to_italic(_italic_to_ascii(name))


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
        new_name = format_channel_name(channel.name)
        if new_name == channel.name:
            skipped += 1
            continue
        try:
            await channel.edit(name=new_name, reason="channel-format: Kursiv-Formatierung")
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
    new_name = format_channel_name(channel.name)
    if new_name != channel.name:
        try:
            await channel.edit(name=new_name, reason="channel-format: Automatische Formatierung")
        except Exception as e:
            print(f"[channel_format] ❌ Auto-Format Fehler bei #{channel.name}: {e}")
