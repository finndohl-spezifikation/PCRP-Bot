# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# channel_format.py — Einmalige Channel/Kategorie-Formatierung
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════
#
# Was passiert beim ersten Bot-Start:
#   1. Alle Kategorien → GROSSSCHRIFT (kein Kursiv)
#   2. Alle normalen Channel → kursiv Unicode, erster Buchstabe groß
#   3. Neue Kategorie "13.1 NEWS" zwischen IC-Bereich und Glücksrad erstellen
#   4. "𝘎𝘰𝘷𝘦𝘳𝘯𝘮𝘦𝘯𝘵"-Channel in der neuen Kategorie erstellen
#
# Danach passiert nichts mehr beim Neustart (Flag-Datei verhindert es).
# Neue Channel werden automatisch formatiert (on_guild_channel_create).
#
# In bot.py eintragen:
#   import channel_format
# ══════════════════════════════════════════════════════════════

import discord
from config import bot, GUILD_ID, ADMIN_ROLE_ID, DATA_DIR

# ── Unicode-Bereiche ──────────────────────────────────────────
_IL = 0x1D622   # kursiv-klein a
_IU = 0x1D608   # kursiv-groß  A

FLAG_FILE = DATA_DIR / "channel_format_done.json"


# ── Hilfsfunktionen ───────────────────────────────────────────

def _italic_to_ascii(name: str) -> str:
    """Kursive Unicode-Zeichen → normales ASCII (Kleinbuchstaben)."""
    out = []
    for ch in name:
        cp = ord(ch)
        if _IL <= cp <= _IL + 25:
            out.append(chr(cp - _IL + ord('a')))
        elif _IU <= cp <= _IU + 25:
            out.append(chr(cp - _IU + ord('a')))
        else:
            out.append(ch)
    return ''.join(out)


def _ascii_to_italic(name: str) -> str:
    """ASCII → kursiv Unicode. Erster Buchstabe + nach '-' immer GROß."""
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
    """Channel-Name → kursiv Unicode mit großem Anfangsbuchstaben."""
    return _ascii_to_italic(_italic_to_ascii(name))


def format_category_name(name: str) -> str:
    """Kategorie-Name → reines GROSSSCHRIFT ASCII (kein kursiv)."""
    return _italic_to_ascii(name).upper()


# ── Einmalige Startup-Routine ─────────────────────────────────

@bot.listen('on_ready')
async def channel_format_on_ready():
    if FLAG_FILE.exists():
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    print("[channel_format] 🔄 Starte einmalige Formatierung ...")

    # 1. Alle Kategorien → GROSSSCHRIFT
    for cat in guild.categories:
        new_name = format_category_name(cat.name)
        if new_name != cat.name:
            try:
                await cat.edit(name=new_name)
            except Exception as e:
                print(f"[channel_format] ❌ Kategorie '{cat.name}': {e}")

    # 2. Alle normalen Channel → kursiv + Anfangsbuchstabe groß
    for ch in guild.channels:
        if isinstance(ch, discord.CategoryChannel):
            continue
        new_name = format_channel_name(ch.name)
        if new_name != ch.name:
            try:
                await ch.edit(name=new_name)
            except Exception as e:
                print(f"[channel_format] ❌ Channel '{ch.name}': {e}")

    # 3. Neue Kategorie "13.1 NEWS" erstellen (falls noch nicht vorhanden)
    existing = discord.utils.find(
        lambda c: '13.1' in _italic_to_ascii(c.name) or '13.1' in c.name,
        guild.categories
    )

    if not existing:
        # Position zwischen IC-Bereich und Glücksrad finden
        position = None
        for cat in sorted(guild.categories, key=lambda c: c.position):
            ascii_n = _italic_to_ascii(cat.name).upper()
            if 'IC' in ascii_n and ('BEREICH' in ascii_n or 'AREA' in ascii_n):
                position = cat.position + 1
            if 'GL' in ascii_n and ('CKSRAD' in ascii_n or 'CASINO' in ascii_n):
                if position is None:
                    position = cat.position
                break

        try:
            kwargs = {"name": "13.1 NEWS"}
            if position is not None:
                kwargs["position"] = position
            news_cat = await guild.create_category(**kwargs)
            print(f"[channel_format] ✅ Kategorie '13.1 NEWS' erstellt (Position {news_cat.position})")

            # Government-Channel in der neuen Kategorie
            await guild.create_text_channel(
                name=format_channel_name("government"),
                category=news_cat
            )
            print("[channel_format] ✅ Channel 'Government' erstellt")
        except Exception as e:
            print(f"[channel_format] ❌ Neue Kategorie/Channel fehlgeschlagen: {e}")

    # Flag setzen — läuft nie wieder
    FLAG_FILE.write_text('{"done": true}')
    print("[channel_format] ✅ Einmalige Formatierung abgeschlossen.")


# ── Neue Channel automatisch formatieren ─────────────────────

@bot.event
async def on_guild_channel_create(channel):
    if isinstance(channel, discord.CategoryChannel):
        return
    new_name = format_channel_name(channel.name)
    if new_name != channel.name:
        try:
            await channel.edit(name=new_name)
        except Exception as e:
            print(f"[channel_format] ❌ Auto-Format Fehler bei '{channel.name}': {e}")
