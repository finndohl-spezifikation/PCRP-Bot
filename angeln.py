# -*- coding: utf-8 -*-
# angeln.py \u2014 Angel-System (Paradise City Roleplay)

from config import *
from economy_helpers import (
    load_economy, save_economy, get_user,
    load_team_shop, find_shop_item, normalize_item_name,
    load_angler_shop, save_angler_shop,
)

ANGELN_INFO_CHANNEL_ID  = 1490894254006993026
ANGELN_BILD_CHANNEL_ID  = 1490894255474872392
ANGELN_LOG_CHANNEL_ID   = 1490878131240829028

ANGELN_CD_SECS          = 10 * 60

ANGELN_MSG_FILE         = DATA_DIR / "angeln_info_msg.json"

ANGLER_SHOP_CHANNEL_ID  = 1497804333541097532
ANGLER_SHOP_MSG_FILE    = DATA_DIR / "angler_shop_msg.json"

ANGEL_NAME  = "Angel"
ANGEL_PRICE = 800

FISCHKOEDER_NAME  = "Fischk\u00f6der"
FISCHKOEDER_PRICE = 400

HOCHWERTIGE_KOEDER_NAME   = "Hochwertiger Angelk\u00f6der"
HOCHWERTIGE_KOEDER_PRICE  = 750
HOCHWERTIGE_KOEDER_BONUS  = 5

# Fische (nur nicht-M\u00fcll, nicht-text, nicht-Sonderitem)
ANGELN_FISCHE_NAMEN = {
    n for (n, _, _, _, _, nur_txt, _uk) in []  # wird sp\u00e4ter bef\u00fcllt
}
_MUELL_NAMEN  = {"Stiefel", "Benutztes Kondom", "Seetang", "Sack M\u00fcll"}
_SONDER_NAMEN = {"Schmuckk\u00e4stchen", "Antiker Kavallerie-Dolch"}

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
    ("Stiefel",           14,  1, 3,     0, False, None),
    ("Benutztes Kondom",  12,  1, 1,     0, False, None),
    ("Seetang",           24,  1, 5,     0, False, None),
    ("Sack M\u00fcll",    12,  1, 2,     0, False, None),
    # Sonstiges
    ("Schmuckk\u00e4stchen",                        11, 1, 1,    0, False, None),
    ("Flasche mit dem Lohn Check von der Laura",    12, 1, 1,    0, True,  "hat_laura_check"),
    ("Antiker Kavallerie-Dolch",                    18, 1, 1,    0, False, None),
]

# Fisch-Namen + Wert-Lookup (nach Loot-Tabelle berechnet)
ANGELN_FISCHE_NAMEN = {
    n for (n, _, _, _, _, nur_txt, _uk) in ANGELN_LOOT
    if not nur_txt and n not in _MUELL_NAMEN and n not in _SONDER_NAMEN
}
ANGELN_WERT = {n: w for (n, _, _, _, w, _, _) in ANGELN_LOOT}


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


def _is_koeder_name(raw_name: str) -> bool:
    """True wenn der Itemname auf einen K\u00F6der hindeutet
    (egal ob 'K\u00F6der', 'Fischk\u00F6der', 'Angelk\u00F6der', 'Hochwertiger K\u00F6der' usw.).
    Pr\u00FCft sowohl die normalisierte Form als auch die rohe (mit Umlauten)."""
    n_norm = normalize_item_name(raw_name)
    n_raw  = raw_name.lower()
    return ("koeder" in n_norm) or ("k\u00F6der" in n_raw)


def _is_hochwertig_koeder_name(raw_name: str) -> bool:
    n_norm = normalize_item_name(raw_name)
    n_raw  = raw_name.lower()
    return _is_koeder_name(raw_name) and (
        "hochwertig" in n_norm or "hochwertig" in n_raw
        or "premium"   in n_norm or "premium"   in n_raw
    )


def _hat_angel(user_id: int) -> bool:
    """Tolerante Angel-Erkennung: matched 'Angel', 'Angelrute' usw.,
    aber NICHT 'Angelk\u00F6der' (das ist ein K\u00F6der, keine Rute)."""
    ud = get_user(load_economy(), user_id)
    target_norm = normalize_item_name(ANGEL_NAME)
    for raw in ud.get("inventory", []):
        if _is_koeder_name(raw):
            continue  # K\u00F6der ist keine Rute
        n = normalize_item_name(raw)
        if n == target_norm:
            return True
        if n.startswith("angel"):  # Angelrute, Angel-Set, etc.
            return True
    return False


def _detect_koeder(user_id: int) -> str | None:
    """Gibt den ECHTEN Inventar-Namen des K\u00F6ders zur\u00FCck (damit
    _remove_koeder_by_name ihn 1:1 entfernen kann).
    Bevorzugt hochwertige K\u00F6der \u00FCber normale.
    Tolerant gegen\u00FCber Schreibweisen \u2014 erkennt 'K\u00F6der',
    'Fischk\u00F6der', 'Angelk\u00F6der', 'Hochwertiger K\u00F6der' etc."""
    ud  = get_user(load_economy(), user_id)
    inv = ud.get("inventory", [])
    # Erst nach hochwertigem suchen
    for raw in inv:
        if _is_hochwertig_koeder_name(raw):
            return raw
    # Dann irgendeinen K\u00F6der
    for raw in inv:
        if _is_koeder_name(raw):
            return raw
    return None


def _remove_koeder_by_name(user_id: int, name: str) -> bool:
    eco = load_economy()
    ud  = get_user(eco, user_id)
    inv = ud.get("inventory", [])
    for i, item in enumerate(inv):
        if normalize_item_name(item) == normalize_item_name(name):
            inv.pop(i)
            eco[str(user_id)] = ud
            save_economy(eco)
            return True
    return False


def _hat_koeder(user_id: int) -> bool:
    return _detect_koeder(user_id) is not None


def _remove_koeder(user_id: int) -> bool:
    name = _detect_koeder(user_id)
    if name:
        return _remove_koeder_by_name(user_id, name)
    return False


def _verkaufe_fische(user_id: int) -> tuple:
    """Entfernt alle Fische aus dem Inventar, schreibt Betrag auf das Bankkonto.
    Gibt (anzahl_fische, betrag, detail_lines) zur\u00fcck."""
    from collections import Counter
    eco = load_economy()
    ud  = get_user(eco, user_id)
    inv = ud.get("inventory", [])

    keep       = []
    gefangen   = []
    for item in inv:
        matched = next(
            (fn for fn in ANGELN_FISCHE_NAMEN
             if normalize_item_name(fn) == normalize_item_name(item)),
            None
        )
        if matched:
            gefangen.append(matched)
        else:
            keep.append(item)

    if not gefangen:
        return 0, 0, []

    counts = Counter(gefangen)
    betrag = sum(ANGELN_WERT.get(n, 0) * c for n, c in counts.items())

    lines = []
    for fname, cnt in sorted(counts.items(), key=lambda x: -ANGELN_WERT.get(x[0], 0)):
        wert = ANGELN_WERT.get(fname, 0)
        if wert > 0:
            lines.append(f"\u27a4 **{fname}** \u00d7{cnt} \u2014 {wert * cnt:,}\u00a0$".replace(",", "."))
        else:
            lines.append(f"\u27a4 **{fname}** \u00d7{cnt}")

    ud["inventory"]   = keep
    ud["bank"]        = int(ud.get("bank", 0)) + betrag
    eco[str(user_id)] = ud
    save_economy(eco)
    return len(gefangen), betrag, lines




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

def _roll_fang(user_id: int, bonus_chance: int = 0) -> tuple[list[tuple[str,int,int]], list[str], int]:
    """
    Gibt zur\u00fcck:
      items_inventar: [(item_name, anzahl, wert_gesamt), ...]  \u2014 maximal 1 Eintrag
      text_only:      [beschreibung, ...]
      betrag:         Gesamtbetrag
    bonus_chance: zus\u00e4tzliche Chance in % pro Item (z.B. durch Hochwertigen K\u00f6der)
    Pro Angelversuch wird immer nur EIN Item gefangen.
    """
    hat_laura = _hat_laura_check(user_id)

    # Alle Items sammeln, die ihre Chance-Pr\u00fcfung bestehen
    kandidaten = []
    for (name, chance, mn, mx, wert, nur_text, ukey) in ANGELN_LOOT:
        eff_chance = min(100, chance + bonus_chance)
        if random.randint(1, 100) > eff_chance:
            continue
        if ukey == "hat_laura_check" and hat_laura:
            continue
        kandidaten.append((name, mn, mx, wert, nur_text, ukey))

    # Kein Treffer \u2192 nichts gefangen
    if not kandidaten:
        return [], [], 0

    # Nur EIN zuf\u00e4lliges Item aus den Treffern ausw\u00e4hlen
    (name, mn, mx, wert, nur_text, ukey) = random.choice(kandidaten)
    anzahl = random.randint(mn, mx)

    if nur_text:
        if ukey == "hat_laura_check":
            _set_laura_check(user_id)
        return [], [f"\U0001F37E Du hast eine **Flasche mit dem Lohn Check von der Laura** gefunden!"], 0
    else:
        shop_name = _shop_name_angeln(name)
        return [(shop_name, anzahl, wert * anzahl)], [], wert * anzahl


# \u2500\u2500 on_message: Foto startet Angeln \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

import time as _time  # f\u00FCr Zeitstempel im Duplikatschutz


def _angeln_msg_bereits_verarbeitet(msg_id: int) -> bool:
    """Pr\u00FCft ob die Nachrichten-ID schon verarbeitet wurde.
    Speichert den Zustand in der Economy-JSON, damit auch mehrere
    Bot-Prozesse (z.B. lokal + Railway) keine Doppelnachrichten senden."""
    try:
        eco  = load_economy()
        seen = eco.get("_angeln_seen_msgs", {})
        now  = _time.time()
        # Eintr\u00E4ge \u00E4lter als 2 Minuten bereinigen
        seen = {k: v for k, v in seen.items() if now - v < 120}
        if str(msg_id) in seen:
            eco["_angeln_seen_msgs"] = seen
            save_economy(eco)
            return True
        seen[str(msg_id)] = now
        eco["_angeln_seen_msgs"] = seen
        save_economy(eco)
        return False
    except Exception:
        return False


async def angeln_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != ANGELN_BILD_CHANNEL_ID:
        return

    # Duplikatschutz: Nachricht nur einmal verarbeiten.
    # Funktioniert auch bei mehreren gleichzeitigen Bot-Prozessen,
    # da der Zustand in der gemeinsamen Economy-JSON gespeichert wird.
    if _angeln_msg_bereits_verarbeitet(message.id):
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

    # Angel-Check (Rute)
    if not _hat_angel(user.id):
        try:
            await message.channel.send(
                f"{user.mention} \u274C Du hast keine **{ANGEL_NAME}**!\n"
                f"\U0001F3A3 Kaufe eine im <#{ANGLER_SHOP_CHANNEL_ID}>.",
                delete_after=10,
            )
        except Exception:
            pass
        return

    # K\u00f6der-Check
    koeder_name = _detect_koeder(user.id)
    if koeder_name is None:
        try:
            await message.channel.send(
                f"{user.mention} \u274C Du hast keinen **K\u00f6der**!\n"
                f"\U0001F3A3 Kaufe einen im <#{ANGLER_SHOP_CHANNEL_ID}>.",
                delete_after=10,
            )
        except Exception:
            pass
        return

    bonus_chance = HOCHWERTIGE_KOEDER_BONUS if _is_hochwertig_koeder_name(koeder_name) else 0
    _remove_koeder_by_name(user.id, koeder_name)
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

        items_inv, text_only, _ = _roll_fang(user.id, bonus_chance)

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

        # Schmuckkästchen-Button falls geangelt
        hat_schmukkastchen = any(
            "Schmuckk" in item_name and "stchen" in item_name
            for (item_name, _, _) in items_inv
        )

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
            if hat_schmukkastchen:
                await user.send(embed=embed_dm, view=SchmuckkastchenView(user.id))
            else:
                await user.send(embed=embed_dm)
        except Exception:
            pass

    bot.loop.create_task(_fangen())


# Listener nur einmal registrieren — verhindert Doppel-Nachrichten
# auch wenn angeln.py mehrfach importiert wird.
if not getattr(bot, "_angeln_listener_registered", False):
    bot._angeln_listener_registered = True
    bot.add_listener(angeln_bild_listener, "on_message")


# \u2500\u2500 Views \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500



# ─── Schmuckkästchen-View ────────────────────────────────────────────────────

class SchmuckkastchenView(discord.ui.View):
    """Erscheint in der DM wenn der Spieler ein Schmuckkästchen geangelt hat."""

    def __init__(self, user_id: int):
        super().__init__(timeout=86400)   # 24 Stunden
        self.user_id = user_id
        self.opened  = False

    @discord.ui.button(
        label="Schmuckk\u00e4stchen \u00d6ffnen",
        style=discord.ButtonStyle.primary,
        emoji="\U0001F4DC",
    )
    async def oeffnen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "\u274C Das ist nicht dein Schmuckk\u00e4stchen.", ephemeral=True
            )
            return
        if self.opened:
            await interaction.response.send_message(
                "\u274C Du hast das Schmuckk\u00e4stchen bereits ge\u00f6ffnet.", ephemeral=True
            )
            return

        self.opened     = True
        button.disabled = True
        button.label    = "Ge\u00f6ffnet"

        import random
        if random.random() < 0.60:
            # 60 % — 3x Diamant
            diamant_name = _shop_name_angeln("Diamant") or "Diamant"
            _add_items_angeln(self.user_id, diamant_name, 3)
            emb = discord.Embed(
                title="\U0001F48E Schmuckk\u00e4stchen ge\u00f6ffnet!",
                description=(
                    "Du hast das Schmuckk\u00e4stchen ge\u00f6ffnet und gefunden:\n\n"
                    f"\u27A4 **{diamant_name}** \u00D73 \u2192 direkt in dein Inventar"
                ),
                color=0x9B59B6,
                timestamp=datetime.now(timezone.utc),
            )
        else:
            # 40 % — Seltenes Artefakt
            emb = discord.Embed(
                title="\u2728 Schmuckk\u00e4stchen ge\u00f6ffnet!",
                description=(
                    "Du hast das Schmuckk\u00e4stchen ge\u00f6ffnet und gefunden:\n\n"
                    "\u27A4 **Artefakt**\n"
                    "*(Seltenes Artefakt)*"
                ),
                color=0xF1C40F,
                timestamp=datetime.now(timezone.utc),
            )
        emb.set_footer(text="Paradise City Roleplay \u2022 Angel-System")
        await interaction.response.edit_message(embed=emb, view=self)

class FischVerkaufenView(discord.ui.View):
    """Ephemeraler Bestaetigungs-View nach Klick auf 'Fische verkaufen'."""

    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="Alle Fische verkaufen",
        style=discord.ButtonStyle.green,
        emoji="\U0001F4B0",
    )
    async def verkaufen_btn(self, interaction: discord.Interaction, _btn):
        fish_count, sg_total, lines = _verkaufe_fische(interaction.user.id)
        if fish_count == 0:
            await interaction.response.edit_message(
                content="\u274C Du hast keine Fische im Inventar.",
                embed=None, view=None,
            )
            return

        desc = "\n".join(lines)
        if sg_total > 0:
            desc += f"\n\n\U0001F4B0 Gesamt: **{sg_total:,}\u00a0$ (Bankkonto)**".replace(",", ".")
        emb = discord.Embed(
            title="\u2705 Fische verkauft!",
            description=desc,
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        emb.set_footer(text="Paradise City Roleplay \u2022 Angel-System")
        await interaction.response.edit_message(embed=emb, view=None)
        await _log_angeln(
            interaction.guild,
            "\U0001F4B0 Fische verkauft",
            f"{interaction.user.mention} hat **{fish_count} Fische** f\u00fcr **{sg_total:,}\u00a0$ (Bank)** verkauft.".replace(",", "."),
        )


class AnglernInfoView(discord.ui.View):
    """Persistenter View am Angel-Info-Embed."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fische verkaufen",
        style=discord.ButtonStyle.blurple,
        emoji="\U0001F41F",
        custom_id="angeln_info:verkaufen",
    )
    async def fische_verkaufen(self, interaction: discord.Interaction, _btn):
        eco = load_economy()
        ud  = get_user(eco, interaction.user.id)
        inv = ud.get("inventory", [])

        from collections import Counter
        gefangen = [
            fn for item in inv
            for fn in ANGELN_FISCHE_NAMEN
            if normalize_item_name(fn) == normalize_item_name(item)
        ]

        if not gefangen:
            await interaction.response.send_message(
                "\u274C Du hast keine Fische im Inventar.", ephemeral=True,
            )
            return

        counts   = Counter(gefangen)
        sg_total = sum(ANGELN_WERT.get(n, 0) * c for n, c in counts.items())
        lines    = []
        for fname, cnt in sorted(counts.items(), key=lambda x: -ANGELN_WERT.get(x[0], 0)):
            wert = ANGELN_WERT.get(fname, 0)
            if wert > 0:
                lines.append(f"\u27a4 **{fname}** \u00d7{cnt} \u2014 {wert * cnt:,}\u00a0$".replace(",", "."))
            else:
                lines.append(f"\u27a4 **{fname}** \u00d7{cnt}")

        desc = "\n".join(lines)
        if sg_total > 0:
            desc += f"\n\n\U0001F4B0 Gesamt: **{sg_total:,}\u00a0$ (Bankkonto)**".replace(",", ".")
        emb = discord.Embed(
            title="\U0001F41F Fische im Inventar",
            description=desc,
            color=0x1E90FF,
            timestamp=datetime.now(timezone.utc),
        )
        emb.set_footer(text="Paradise City Roleplay \u2022 Angel-System")
        await interaction.response.send_message(embed=emb, view=FischVerkaufenView(), ephemeral=True)


class AnglershopKaufenModal(discord.ui.Modal):
    """Generisches Kauf-Modal f\u00fcr den Angler Shop."""

    def __init__(self, item_name: str, item_price: int):
        preis_fmt = f"{item_price:,}".replace(",", ".")
        super().__init__(title=f"{item_name[:45]} kaufen")
        self.item_name  = item_name
        self.item_price = item_price
        self.menge_input = discord.ui.TextInput(
            label=f"Menge  (Preis: {preis_fmt}\u00a0$ / St\u00fcck)",
            placeholder="z.B. 1",
            default="1",
            min_length=1,
            max_length=3,
            required=True,
        )
        self.add_item(self.menge_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            menge = int(self.menge_input.value.strip())
        except ValueError:
            await interaction.response.send_message(
                "\u274C Bitte eine g\u00fcltige Zahl eingeben.", ephemeral=True,
            )
            return
        if menge < 1 or menge > 100:
            await interaction.response.send_message(
                "\u274C Menge muss zwischen 1 und 100 liegen.", ephemeral=True,
            )
            return

        gesamtpreis = self.item_price * menge
        eco = load_economy()
        ud  = get_user(eco, interaction.user.id)

        if int(ud.get("cash", 0)) < gesamtpreis:
            preis_fmt = f"{gesamtpreis:,}".replace(",", ".")
            cash_fmt  = f"{int(ud.get('cash', 0)):,}".replace(",", ".")
            await interaction.response.send_message(
                f"\u274C Nicht genug **Bargeld**!\n"
                f"Preis: **{preis_fmt}\u00a0$** \u2014 Dein Bargeld: **{cash_fmt}\u00a0$**",
                ephemeral=True,
            )
            return

        ud["cash"] = int(ud.get("cash", 0)) - gesamtpreis
        ud.setdefault("inventory", []).extend([self.item_name] * menge)
        eco[str(interaction.user.id)] = ud
        save_economy(eco)

        preis_fmt = f"{gesamtpreis:,}".replace(",", ".")
        cash_fmt  = f"{int(ud['cash']):,}".replace(",", ".")
        emb = discord.Embed(
            title="\u2705 Gekauft!",
            description=(
                f"Du hast **{menge}x {self.item_name}** f\u00fcr **{preis_fmt}\u00a0$** gekauft.\n"
                f"Verbleibendes Bargeld: **{cash_fmt}\u00a0$**"
            ),
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        emb.set_footer(text="Paradise City Roleplay \u2022 Angler Shop")
        await interaction.response.send_message(embed=emb, ephemeral=True)


# Keine hartcodierten Items mehr. Die komplette Item-Liste kommt
# IMMER aus der JSON-Datei (load_angler_shop), damit \u00C4nderungen via
# /shop-add, /shop-edit oder /delete-item sofort wirken \u2014 auch wenn
# alle Items gel\u00F6scht werden.
ANGLER_SHOP_ITEMS = [
    {"name": ANGEL_NAME,              "price": ANGEL_PRICE},
    {"name": FISCHKOEDER_NAME,        "price": FISCHKOEDER_PRICE},
    {"name": HOCHWERTIGE_KOEDER_NAME, "price": HOCHWERTIGE_KOEDER_PRICE},
]


def _current_angler_items() -> list:
    """Liefert die aktuelle Angler-Shop-Item-Liste live aus der JSON.
    Gibt leere Liste zur\u00FCck wenn keine Items vorhanden \u2014 KEIN Fallback
    auf hartcodierte Items, damit L\u00F6schungen wirklich greifen.

    Dedupliziert Items anhand des Namens (case-insensitive, getrimmt),
    damit Discord-Select-Menus nicht mit "option value already used"
    crashen, falls die JSON aus Versehen doppelte Eintr\u00E4ge enth\u00E4lt
    (z.\u202FB. nach mehrfachem /shop-add)."""
    try:
        items = load_angler_shop()
    except Exception:
        items = []
    if not items:
        return []

    seen   = set()
    unique = []
    for it in items:
        name = str(it.get("name", "")).strip().lower()
        if not name or name in seen:
            continue
        seen.add(name)
        unique.append(it)
    return unique


def _build_angler_items_embed(member: discord.Member) -> discord.Embed:
    eco  = load_economy()
    ud   = get_user(eco, member.id)
    cash = int(ud.get("cash", 0))
    sep  = "\u2015" * 22
    lines = [
        f"\u27A4 **{it['name']}**\u3000\u2014\u3000`{it['price']:,} \U0001F4B5`"
        for it in _current_angler_items()
    ]
    desc = sep + "\n" + "\n".join(lines) + "\n" + sep
    emb  = discord.Embed(
        title="\U0001F3A3  Angler Shop",
        description=desc,
        color=0x1E90FF,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(name="\U0001F4B5 Dein Bargeld", value=f"**{cash:,} $**", inline=True)
    emb.set_footer(text="\U0001F3A3 Item w\u00e4hlen \u2022 Nur Bargeld")
    return emb


class AnglershopItemSelect(discord.ui.Select):
    def __init__(self):
        items = _current_angler_items()
        if items:
            options = [
                discord.SelectOption(
                    label=it["name"][:100],
                    value=it["name"][:100],
                    description=f"{it.get('price', 0):,} \U0001F4B5",
                )
                for it in items
            ]
            placeholder = "\U0001F6D2 Item ausw\u00e4hlen\u2026"
            disabled    = False
        else:
            options = [discord.SelectOption(label="Keine Items verf\u00FCgbar", value="_none_")]
            placeholder = "\u274C Keine Items verf\u00FCgbar"
            disabled    = True
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            row=0,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        name = self.values[0]
        item = next((it for it in _current_angler_items() if it["name"] == name), None)
        if not item:
            await interaction.response.send_message("\u274C Item nicht gefunden.", ephemeral=True)
            return
        await interaction.response.send_modal(
            AnglershopKaufenModal(item["name"], item["price"])
        )


class AnglershopPageView(discord.ui.View):
    """Ephemeraler Shop-View mit Dropdown (nicht persistent)."""

    def __init__(self, member: discord.Member):
        super().__init__(timeout=120)
        self.add_item(AnglershopItemSelect())

        close_btn = discord.ui.Button(
            label="\u2716 Schlie\u00dfen",
            style=discord.ButtonStyle.danger,
            row=1,
        )

        async def close_cb(interaction: discord.Interaction):
            try:
                await interaction.response.defer()
                await interaction.delete_original_response()
            except Exception:
                pass

        close_btn.callback = close_cb
        self.add_item(close_btn)


class AnglershopView(discord.ui.View):
    """Persistenter View am Angler-Shop-Kanal-Embed."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="\U0001F3A3 Shop \u00f6ffnen",
        style=discord.ButtonStyle.primary,
        custom_id="angler_shop:open",
    )
    async def open_btn(self, interaction: discord.Interaction, _btn):
        # Defer sofort \u2014 verhindert "Interaktion fehlgeschlagen", auch wenn
        # der Embed-/View-Aufbau l\u00E4nger dauert oder eine Exception wirft.
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)
        except Exception as _e:
            print(f"[angler_shop] defer fehlgeschlagen: {_e}")

        try:
            emb  = _build_angler_items_embed(interaction.user)
            view = AnglershopPageView(interaction.user)
            await interaction.followup.send(embed=emb, view=view, ephemeral=True)
        except Exception as _e:
            import traceback
            traceback.print_exc()
            try:
                await interaction.followup.send(
                    f"\u274C Angler-Shop konnte nicht ge\u00F6ffnet werden: `{_e}`",
                    ephemeral=True,
                )
            except Exception:
                pass


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

    sep = "\u2501" * 32
    default_desc = (
        "**\U0001F4CD Standort**\n"
        "> Fahre zum **Pier** \u2014 Bild 1\n\n"
        f"{sep}\n\n"
        "**\U0001F4F8 Ablauf**\n"
        f"> Du ben\u00f6tigst eine **Angel** + einen **K\u00f6der** aus dem <#{ANGLER_SHOP_CHANNEL_ID}>\n"
        f"> Schicke ein Foto in <#{ANGELN_BILD_CHANNEL_ID}>\n"
        "> Angeln startet **automatisch** \u2014 1 K\u00f6der wird verbraucht\n"
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
            await existing.edit(embed=_build_angeln_info_embed(), view=AnglernInfoView())
            return "\u2705 Angel Info-Embed aktualisiert."
        except Exception:
            pass

    try:
        sent = await channel.send(embed=_build_angeln_info_embed(), view=AnglernInfoView())
        json.dump({"message_id": sent.id}, open(ANGELN_MSG_FILE, "w", encoding="utf-8"), indent=2)
        return "\u2705 Angel Info-Embed gesendet."
    except Exception as e:
        return f"\u274C Senden fehlgeschlagen: {e}"


async def auto_angeln_setup():
    await bot.wait_until_ready()
    await asyncio.sleep(3)
    result = await _angeln_setup()
    print(f"[angeln] {result}")


# \u2500\u2500 Angler Shop \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_angler_shop_embed() -> discord.Embed:
    # Items werden bewusst NICHT mehr im Channel-Embed angezeigt.
    # Die Item-Liste erscheint erst, wenn der Spieler den Shop \u00FCber den
    # Button \u00F6ffnet (ephemerales Embed).
    sep = "\u2015" * 22
    desc = (
        "\U0001F3A3 **Willkommen im Angler Shop!**\n"
        f"{sep}\n"
        "\u27A4 Du ben\u00f6tigst eine **Angel** und einen **K\u00f6der** pro Session.\n"
        "\u27A4 Bezahlung nur mit **Bargeld** (\U0001F4B5).\n\n"
        "Klicke auf den Button um den Shop zu \u00f6ffnen!"
    )
    emb = discord.Embed(
        title="\U0001F3A3  Angler Shop",
        description=desc,
        color=0x1E90FF,
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_footer(text="Paradise City Roleplay \u2022 Angler Shop")
    return emb


async def _angler_shop_setup() -> str:
    try:
        channel = await bot.fetch_channel(ANGLER_SHOP_CHANNEL_ID)
    except Exception as e:
        return f"\u274C Angler Shop Kanal nicht erreichbar ({ANGLER_SHOP_CHANNEL_ID}): {e}"

    msg_id = None
    try:
        if ANGLER_SHOP_MSG_FILE.exists():
            msg_id = json.load(open(ANGLER_SHOP_MSG_FILE, encoding="utf-8")).get("message_id")
    except Exception:
        pass

    if msg_id:
        try:
            existing = await channel.fetch_message(msg_id)
            await existing.edit(embed=_build_angler_shop_embed(), view=AnglershopView())
            return "\u2705 Angler Shop aktualisiert."
        except Exception:
            pass

    try:
        sent = await channel.send(embed=_build_angler_shop_embed(), view=AnglershopView())
        json.dump({"message_id": sent.id}, open(ANGLER_SHOP_MSG_FILE, "w", encoding="utf-8"), indent=2)
        return "\u2705 Angler Shop gesendet."
    except Exception as e:
        return f"\u274C Angler Shop senden fehlgeschlagen: {e}"


async def auto_angler_shop_setup():
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    result = await _angler_shop_setup()
    print(f"[angler_shop] {result}")
