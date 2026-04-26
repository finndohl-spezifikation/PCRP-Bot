# -*- coding: utf-8 -*-
# angeln.py \u2014 Angel-System (Paradise City Roleplay)

from config import *
from economy_helpers import (
    load_economy, save_economy, get_user,
    load_team_shop, find_shop_item, normalize_item_name,
)

ANGELN_INFO_CHANNEL_ID  = 1490894254006993026
ANGELN_BILD_CHANNEL_ID  = 1490894255474872392
ANGELN_LOG_CHANNEL_ID   = 1490878131240829028

ANGELN_CD_SECS          = 10 * 60

ANGELN_MSG_FILE         = DATA_DIR / "angeln_info_msg.json"

ANGELN_EMBED_DEFAULT = {
    "title":       "\U0001F3A3 Angeln",
    "description": None,
    "color":       0x1E90FF,
    "footer":      "Paradise City Roleplay \u2022 Angel-System",
}

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Loot-Tabelle
# (item_name, chance_pct, min_anz, max_anz, wert_pro_stueck, nur_text, unique_key)
# nur_text=True  -> nicht ins Inventar, nur als Textnachricht
# unique_key     -> eco-Feld das verhindert ein zweites Erhalten (oder None)
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

ANGELN_LOOT = [
    # Fische
    ("Goldener Saibling",  3,  1, 1, 35000, False, None),
    ("Riffhai",            4,  1, 1, 17800, False, None),
    ("Stachelrochen",      6,  1, 2, 12300, False, None),
    ("Delfin",             8,  1, 2,  9700, False, None),
    ("Schwertfisch",      17,  1, 3,  6500, False, None),
    ("Lachs",             19,  1, 3,  4300, False, None),
    ("Forelle",           22,  1, 3,  3200, False, None),
    ("Hecht",             15,  1, 2,  3300, False, None),
    ("Wels",              12,  1, 1,  5600, False, None),
    ("Barrakuda",         19,  1, 1,  5400, False, None),
    ("Tintenfisch",       23,  1, 2,  4200, False, None),
    ("Aal",                7,  1, 1,  7700, False, None),
    ("Krebs",             37,  1, 4,  1200, False, None),
    ("Seegurke",          39,  1, 4,  1200, False, None),
    # M\u00fcll
    ("Stiefel",           14,  1, 3,   900, False, None),
    ("Benutztes Kondom",  12,  1, 1,     0, False, None),
    ("Seetang",           24,  1, 5,   700, False, None),
    ("Sack M\u00fcll",    12,  1, 2,     0, False, None),
    # Sonstiges
    ("Schmuckk\u00e4stchen",                        11, 1, 1, 4800, False, None),
    ("Flasche mit dem Lohn Check von der Laura",    12, 1, 1,    0, True,  "hat_laura_check"),
    ("Antiker Kavallerie-Dolch",                    18, 1, 1,    0, False, None),
]


# \u2500\u2500 Hilfsfunktionen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _shop_name_angeln(query: str) -> str:
    try:
        match = find_shop_item(load_team_shop(), query)
        if match:
            return match["name"]
    except Exception:
        pass
    return query


def _add_items_angeln(user_id: int, item_name: str, count: int):
    eco = load_economy()
    ud  = get_user(eco, user_id)
    ud.setdefault("inventory", []).extend([item_name] * count)
    eco[str(user_id)] = ud
    save_economy(eco)


def _set_angeln_cd(user_id: int):
    eco = load_economy()
    ud  = get_user(eco, user_id)
    ud["angeln_cd"] = datetime.now(timezone.utc).isoformat()
    eco[str(user_id)] = ud
    save_economy(eco)


def _angeln_cd_remaining(user_id: int) -> int:
    try:
        ud   = get_user(load_economy(), user_id)
        last = ud.get("angeln_cd")
        if not last:
            return 0
        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
        return max(0, int(ANGELN_CD_SECS - elapsed))
    except Exception:
        return 0


def _hat_laura_check(user_id: int) -> bool:
    try:
        ud = get_user(load_economy(), user_id)
        return bool(ud.get("hat_laura_check", False))
    except Exception:
        return False


def _set_laura_check(user_id: int):
    eco = load_economy()
    ud  = get_user(eco, user_id)
    ud["hat_laura_check"] = True
    eco[str(user_id)] = ud
    save_economy(eco)




async def _log_angeln(guild, title: str, desc: str):
    ch = guild.get_channel(ANGELN_LOG_CHANNEL_ID) if guild else None
    if ch:
        emb = discord.Embed(
            title=f"\U0001F3A3 {title}", description=desc,
            color=0x1E90FF, timestamp=datetime.now(timezone.utc),
        )
        emb.set_footer(text="Paradise City \u2022 Angel-System")
        try:
            await ch.send(embed=emb)
        except Exception:
            pass


# \u2500\u2500 Loot-Berechnung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _roll_fang(user_id: int) -> tuple[list[tuple[str,int,int]], list[str], int]:
    """
    Gibt zur\u00fcck:
      items_inventar: [(item_name, anzahl, wert_gesamt), ...]
      text_only:      [beschreibung, ...]
      schwarzgeld:    Gesamtbetrag
    """
    hat_laura = _hat_laura_check(user_id)
    items_inventar = []
    text_only      = []
    schwarzgeld    = 0

    for (name, chance, mn, mx, wert, nur_text, ukey) in ANGELN_LOOT:
        if random.randint(1, 100) > chance:
            continue
        if ukey == "hat_laura_check" and hat_laura:
            continue

        anzahl = random.randint(mn, mx)

        if nur_text:
            if ukey == "hat_laura_check":
                _set_laura_check(user_id)
            text_only.append(
                f"\U0001F37E Du hast eine **Flasche mit dem Lohn Check von der Laura** gefunden!"
            )
        else:
            shop_name = _shop_name_angeln(name)
            items_inventar.append((shop_name, anzahl, wert * anzahl))
            schwarzgeld += wert * anzahl

    return items_inventar, text_only, schwarzgeld


# \u2500\u2500 on_message: Foto startet Angeln \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.listen("on_message")
async def angeln_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != ANGELN_BILD_CHANNEL_ID:
        return

    IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
    img_atts = [
        att for att in message.attachments
        if (att.content_type and att.content_type.startswith("image/"))
        or att.filename.lower().endswith(IMAGE_EXTS)
    ]
    if not img_atts:
        return

    user  = message.author
    guild = message.guild

    try:
        log_files = [await att.to_file() for att in img_atts]
    except Exception:
        log_files = []

    try:
        await message.delete()
    except Exception:
        pass

    # Cooldown-Check
    cd = _angeln_cd_remaining(user.id)
    if cd > 0:
        m, s = divmod(cd, 60)
        try:
            await message.channel.send(
                f"{user.mention} \u23F3 Du angelst noch \u2014 noch **{m}m {s}s** bis du wieder angeln kannst!",
                delete_after=6,
            )
        except Exception:
            pass
        return

    _set_angeln_cd(user.id)

    # Foto im Log speichern
    try:
        log_ch = guild.get_channel(ANGELN_LOG_CHANNEL_ID) or await bot.fetch_channel(ANGELN_LOG_CHANNEL_ID)
        if log_ch:
            emb = discord.Embed(
                title="\U0001F4F8 Angeln gestartet",
                description=(
                    f"{user.mention} hat ein Foto eingereicht.\n"
                    f"\U0001F3A3 Angeln l\u00e4uft \u2014 Fang in **10 Min.**"
                ),
                color=0x1E90FF,
                timestamp=datetime.now(timezone.utc),
            )
            emb.set_footer(text="Paradise City \u2022 Angel-System")
            await log_ch.send(embed=emb, files=log_files)
    except Exception as e:
        print(f"[angeln] Log-Fehler: {e}")

    # Best\u00e4tigung im Kanal
    try:
        await message.channel.send(
            f"{user.mention} \U0001F3A3 **Angeln gestartet!**\n"
            f"\u23F3 In **10 Minuten** ist dein Fang fertig \u2014 du bekommst eine DM.",
            delete_after=10,
        )
    except Exception:
        pass

    # Fang nach 10 Minuten
    async def _fangen():
        await asyncio.sleep(ANGELN_CD_SECS)

        items_inv, text_only, _ = _roll_fang(user.id)

        # Alle Items ins Inventar
        for (item_name, anzahl, _wert) in items_inv:
            _add_items_angeln(user.id, item_name, anzahl)

        # DM aufbauen
        if not items_inv and not text_only:
            fang_text = "\u2694\uFE0F Leider nichts gefangen \u2014 heute war kein guter Tag!"
        else:
            lines = []
            for (item_name, anzahl, _wert) in items_inv:
                lines.append(f"\u27A4 **{item_name}** \u00D7{anzahl}")
            for t in text_only:
                lines.append(f"\u27A4 {t}")
            fang_text = "\n".join(lines)

        embed_dm = discord.Embed(
            title="\U0001F3A3 Fang abgeschlossen!",
            description=f"**Dein Fang vom Pier:**\n\n{fang_text}",
            color=0x1E90FF,
            timestamp=datetime.now(timezone.utc),
        )
        embed_dm.set_footer(text="Paradise City Roleplay \u2022 Angel-System")

        item_namen = ", ".join(f"{anzahl}x {n}" for (n, anzahl, _) in items_inv) or "nichts"
        await _log_angeln(guild, "\u2705 Fang abgeschlossen",
            f"{user.mention} hat geangelt \u2014 Fang: {item_namen}")

        try:
            await user.send(embed=embed_dm)
        except Exception:
            pass

    bot.loop.create_task(_fangen())


# \u2500\u2500 Info-Embed \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_angeln_info_embed() -> discord.Embed:
    # Kategorien aus Loot-Tabelle
    fische = [(n, w) for (n, _, _, _, w, nur_txt, _uk) in ANGELN_LOOT
              if not nur_txt and n not in (
                  "Stiefel", "Benutztes Kondom", "Seetang", "Sack M\u00fcll",
                  "Schmuckk\u00e4stchen", "Antiker Kavallerie-Dolch")]
    muell  = [(n, w) for (n, _, _, _, w, nur_txt, _uk) in ANGELN_LOOT
              if not nur_txt and n in ("Stiefel", "Benutztes Kondom", "Seetang", "Sack M\u00fcll")]
    sonder = [(n, w) for (n, _, _, _, w, nur_txt, _uk) in ANGELN_LOOT
              if not nur_txt and n in ("Schmuckk\u00e4stchen", "Antiker Kavallerie-Dolch")]

    def fmt_item(name, wert):
        if wert > 0:
            return f"> \u27a4 **{name}** \u2014 {wert:,}\u00a0$".replace(",", ".")
        return f"> \u27a4 **{name}**"

    fische_lines  = "\n".join(fmt_item(n, w) for n, w in fische)
    muell_lines   = "\n".join(fmt_item(n, w) for n, w in muell)
    sonder_lines  = "\n".join(fmt_item(n, w) for n, w in sonder)
    sonder_lines += "\n> \u27a4 **???**"

    sep = "\u2501" * 32
    default_desc = (
        "**\U0001F4CD Standort**\n"
        "> Fahre zum **Pier** \u2014 Bild 1\n\n"
        f"{sep}\n\n"
        "**\U0001F4F8 Ablauf**\n"
        f"> Schicke ein Foto in <#{ANGELN_BILD_CHANNEL_ID}>\n"
        "> Angeln startet **automatisch**\n"
        "> Nach **10 Minuten** bekommst du eine **DM** mit deinem Fang\n"
        "> Items landen direkt in deinem **Inventar**\n\n"
        f"{sep}\n\n"
        "\U0001F41F **M\u00f6gliche F\u00e4nge \u2014 Fische**\n"
        f"{fische_lines}\n\n"
        f"{sep}\n\n"
        "\U0001F9F9 **M\u00f6gliche F\u00e4nge \u2014 M\u00fcll**\n"
        f"{muell_lines}\n\n"
        f"{sep}\n\n"
        "\u2728 **M\u00f6gliche F\u00e4nge \u2014 Sonstiges**\n"
        f"{sonder_lines}\n\n"
        f"{sep}\n"
        "\U0001F4E6 Alle Funde landen direkt in deinem **Inventar**."
    )
    emb = discord.Embed(
        title="\U0001F3A3 Angeln",
        color=0x1E90FF,
        description=default_desc,
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_footer(text="Paradise City Roleplay \u2022 Angel-System")
    return emb


async def _angeln_setup() -> str:
    try:
        channel = await bot.fetch_channel(ANGELN_INFO_CHANNEL_ID)
    except Exception as e:
        return f"\u274C Kanal nicht erreichbar (ID {ANGELN_INFO_CHANNEL_ID}): {e}"

    msg_id = None
    try:
        if ANGELN_MSG_FILE.exists():
            msg_id = json.load(open(ANGELN_MSG_FILE, encoding="utf-8")).get("message_id")
    except Exception:
        pass

    if msg_id:
        try:
            existing = await channel.fetch_message(msg_id)
            await existing.edit(embed=_build_angeln_info_embed())
            return "\u2705 Angel Info-Embed aktualisiert."
        except Exception:
            pass

    try:
        sent = await channel.send(embed=_build_angeln_info_embed())
        json.dump({"message_id": sent.id}, open(ANGELN_MSG_FILE, "w", encoding="utf-8"), indent=2)
        return "\u2705 Angel Info-Embed gesendet."
    except Exception as e:
        return f"\u274C Senden fehlgeschlagen: {e}"


async def auto_angeln_setup():
    await bot.wait_until_ready()
    await asyncio.sleep(3)
    result = await _angeln_setup()
    print(f"[angeln] {result}")
