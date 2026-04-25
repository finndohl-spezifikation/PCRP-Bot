# -*- coding: utf-8 -*-
# kokain.py \u2014 Kokain-System (Paradise City Roleplay)

from config import *
from economy_helpers import (
    load_economy, save_economy, get_user,
    load_team_shop, find_shop_item, normalize_item_name,
)

KOKA_INFO_CHANNEL_ID     = 1490894293135790190
KOKA_BILD_CHANNEL_ID     = 1490894294297477120
KOKA_LOG_CHANNEL_ID      = 1490878131240829028

KOKA_MSG_FILE         = DATA_DIR / "koka_info_msg.json"
EMBED_CONFIGS_FILE    = DATA_DIR / "embed_configs.json"
BUTTON_CONFIGS_FILE   = DATA_DIR / "button_configs.json"

KOKA_EMBED_DEFAULT = {
    "title":  "\U0001F33F Kokain Herstellung",
    "description": None,
    "color":  0xFF6B00,
    "footer": "Paradise City Roleplay \u2022 Kokain-System",
}
KOKA_BTN_DEFAULT = {
    "koka_sell_btn": {"label": "\U0001F4B0 Kokain verkaufen", "style": "success"},
}


def _load_embed_cfg_koka() -> dict:
    try:
        if EMBED_CONFIGS_FILE.exists():
            d = json.load(open(EMBED_CONFIGS_FILE, encoding="utf-8"))
            merged = dict(KOKA_EMBED_DEFAULT)
            merged.update(d.get("kokain") or {})
            return merged
    except Exception:
        pass
    return dict(KOKA_EMBED_DEFAULT)


def _load_button_cfg_koka(key: str) -> dict:
    try:
        if BUTTON_CONFIGS_FILE.exists():
            d = json.load(open(BUTTON_CONFIGS_FILE, encoding="utf-8"))
            merged = dict(KOKA_BTN_DEFAULT.get(key, {}))
            merged.update(d.get(key) or {})
            return merged
    except Exception:
        pass
    return dict(KOKA_BTN_DEFAULT.get(key, {}))


KOKA_BLAETTER_CD_SECS    = 5 * 60
KOKA_KOKAIN_CD_SECS      = 15 * 60
KOKA_BLAETTER_MIN        = 50
KOKA_BLAETTER_MAX        = 150
KOKA_BLAETTER_PRO_RUNDE  = 35
KOKAIN_WERT              = 2_950
KOKAIN_GRAMM             = 250

ITEM_BLAETTER_DEFAULT    = "Kokabl\u00E4tter"
ITEM_KOKAIN_DEFAULT      = "Kokain"
ITEM_SCHWARZGELD_DEFAULT = "Schwarzgeld"


# \u2500\u2500 Hilfsfunktionen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _shop_name(query: str, default: str) -> str:
    try:
        match = find_shop_item(load_team_shop(), query)
        if match:
            return match["name"]
    except Exception:
        pass
    return default


def _count_item(user_id: int, query: str) -> int:
    eco = load_economy()
    inv = get_user(eco, user_id).get("inventory", [])
    nq  = normalize_item_name(query)
    return sum(1 for i in inv if nq in normalize_item_name(i))


def _consume_n(user_id: int, query: str, count: int) -> bool:
    eco  = load_economy()
    ud   = get_user(eco, user_id)
    inv  = ud.get("inventory", [])
    nq   = normalize_item_name(query)
    if sum(1 for i in inv if nq in normalize_item_name(i)) < count:
        return False
    removed, new_inv = 0, []
    for item in inv:
        if removed < count and nq in normalize_item_name(item):
            removed += 1
        else:
            new_inv.append(item)
    ud["inventory"] = new_inv
    eco[str(user_id)] = ud
    save_economy(eco)
    return True


def _add_items(user_id: int, item_name: str, count: int):
    eco = load_economy()
    ud  = get_user(eco, user_id)
    ud.setdefault("inventory", []).extend([item_name] * count)
    eco[str(user_id)] = ud
    save_economy(eco)


def _cd_remaining(user_id: int, field: str, secs: int) -> int:
    try:
        ud   = get_user(load_economy(), user_id)
        last = ud.get(field)
        if not last:
            return 0
        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
        return max(0, int(secs - elapsed))
    except Exception:
        return 0


def _set_cd(user_id: int, field: str):
    eco = load_economy()
    ud  = get_user(eco, user_id)
    ud[field] = datetime.now(timezone.utc).isoformat()
    eco[str(user_id)] = ud
    save_economy(eco)


def _set_foto_cd(user_id: int, secs: int, action: str = ""):
    eco = load_economy()
    ud  = get_user(eco, user_id)
    ud["koka_foto_cd"]        = datetime.now(timezone.utc).isoformat()
    ud["koka_foto_cd_secs"]   = secs
    ud["koka_foto_cd_action"] = action
    eco[str(user_id)] = ud
    save_economy(eco)


async def _log(guild, title: str, desc: str):
    ch = guild.get_channel(KOKA_LOG_CHANNEL_ID) if guild else None
    if ch:
        emb = discord.Embed(
            title=f"\U0001F33F {title}", description=desc,
            color=0xFF6B00, timestamp=datetime.now(timezone.utc),
        )
        emb.set_footer(text="Paradise City \u2022 Kokain-System")
        try:
            await ch.send(embed=emb)
        except Exception:
            pass


# \u2500\u2500 Persistent View: Kokain verkaufen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class KokaInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        cfg = _load_button_cfg_koka("koka_sell_btn")
        _style_map = {
            "success":   discord.ButtonStyle.success,
            "danger":    discord.ButtonStyle.danger,
            "primary":   discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary,
        }
        for child in self.children:
            if getattr(child, "custom_id", "") == "koka_sell_btn":
                if cfg.get("label"):
                    child.label = cfg["label"]
                if cfg.get("style") in _style_map:
                    child.style = _style_map[cfg["style"]]

    @discord.ui.button(
        label="\U0001F4B0 Kokain verkaufen",
        style=discord.ButtonStyle.success,
        custom_id="koka_sell_btn",
    )
    async def sell(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        eco  = load_economy()
        ud   = get_user(eco, user.id)
        inv  = ud.get("inventory", [])
        nk   = normalize_item_name(ITEM_KOKAIN_DEFAULT)
        hits = [i for i in inv if nk in normalize_item_name(i)]
        if not hits:
            await interaction.response.send_message(
                "\u274C Du hast kein **Kokain** im Inventar.", ephemeral=True)
            return
        ud["inventory"] = [i for i in inv if nk not in normalize_item_name(i)]
        total_sg  = (len(hits) * KOKAIN_WERT) // KOKAIN_GRAMM
        eco[str(user.id)] = ud
        save_economy(eco)
        await interaction.response.send_message(
            f"\u2705 **{len(hits)}g Kokain** verarbeitet!\n"
            f"\u23f3 **{total_sg:,}$** werden von der **Serverleitung** manuell vergeben.", ephemeral=True)
        await _log(interaction.guild, "\U0001f48a Kokain verkauft",
            f"{user.mention} hat **{len(hits)}g Kokain** verarbeitet \u2014 **{total_sg:,}$** ausstehend")


# \u2500\u2500 Tempor\u00E4re View: Auswahl nach Foto-Einreichung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class KokaAktionView(discord.ui.View):
    def __init__(self, author_id: int, guild_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.guild_id  = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "\u274C Das ist nicht deine Auswahl!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="\U0001F33F Kokabl\u00E4tter sammeln  (5 Min.)", style=discord.ButtonStyle.success)
    async def blaetter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user  = interaction.user
        guild = bot.get_guild(self.guild_id)

        _set_foto_cd(user.id, KOKA_BLAETTER_CD_SECS, action="sammeln")

        await interaction.response.send_message(
            f"\U0001F33F **Kokabl\u00E4tter sammeln gestartet!**\n"
            f"\u23F3 In **5 Minuten** erh\u00E4ltst du deine Kokabl\u00E4tter.\n"
            f"\U0001F4F8 Erst danach kannst du wieder ein Foto schicken.",
            ephemeral=True,
        )
        try:
            await interaction.message.delete()
        except Exception:
            pass

        await _log(guild, "\U0001F33F Sammeln gestartet",
            f"{user.mention} sammelt Kokabl\u00E4tter \u2014 fertig in 5 Min.")

        async def _liefern():
            menge = random.randint(KOKA_BLAETTER_MIN, KOKA_BLAETTER_MAX)
            await asyncio.sleep(KOKA_BLAETTER_CD_SECS)
            _add_items(user.id, _shop_name(ITEM_BLAETTER_DEFAULT, ITEM_BLAETTER_DEFAULT), menge)
            await _log(guild, "\u2705 Kokabl\u00E4tter erhalten",
                f"{user.mention} hat **{menge} Kokabl\u00E4tter** erhalten.")
            try:
                await user.send(
                    f"\U0001F33F **Ernte abgeschlossen!**\n"
                    f"Du hast **{menge} Kokabl\u00E4tter** erhalten und sie wurden deinem Inventar hinzugef\u00FCgt."
                )
            except Exception:
                pass
        bot.loop.create_task(_liefern())

    @discord.ui.button(label="\u2697\uFE0F Kokain herstellen  (15 Min.)", style=discord.ButtonStyle.danger)
    async def kokain_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user  = interaction.user
        guild = bot.get_guild(self.guild_id)

        vorrat = _count_item(user.id, ITEM_BLAETTER_DEFAULT)
        if vorrat < KOKA_BLAETTER_PRO_RUNDE:
            await interaction.response.send_message(
                f"\u274C Nicht genug Kokabl\u00E4tter!\n"
                f"\U0001F33F Vorhanden: **{vorrat}** \u00B7 Ben\u00F6tigt: **{KOKA_BLAETTER_PRO_RUNDE}**",
                ephemeral=True)
            return

        if not _consume_n(user.id, ITEM_BLAETTER_DEFAULT, KOKA_BLAETTER_PRO_RUNDE):
            await interaction.response.send_message(
                "\u274C Fehler beim Entnehmen der Kokabl\u00E4tter.", ephemeral=True)
            return

        _set_foto_cd(user.id, KOKA_KOKAIN_CD_SECS, action="herstellen")

        await interaction.response.send_message(
            f"\u2697\uFE0F **Kokain Herstellung gestartet!**\n"
            f"\U0001F33F **{KOKA_BLAETTER_PRO_RUNDE} Kokabl\u00E4tter** entnommen.\n"
            f"\u23F3 In **15 Minuten** erh\u00E4ltst du **250g Kokain**.\n"
            f"\U0001F4F8 Erst danach kannst du wieder ein Foto schicken.",
            ephemeral=True,
        )
        try:
            await interaction.message.delete()
        except Exception:
            pass

        await _log(guild, "\u2697\uFE0F Herstellung gestartet",
            f"{user.mention} stellt **250g Kokain** her \u2014 fertig in 15 Min. "
            f"({KOKA_BLAETTER_PRO_RUNDE} Bl\u00E4tter entnommen)")

        async def _liefern():
            await asyncio.sleep(KOKA_KOKAIN_CD_SECS)
            _add_items(user.id, _shop_name(ITEM_KOKAIN_DEFAULT, ITEM_KOKAIN_DEFAULT), KOKAIN_GRAMM)
            await _log(guild, "\u2705 Kokain hergestellt",
                f"{user.mention} hat **{KOKAIN_GRAMM}\u00D7 Kokain ({KOKAIN_GRAMM}g)** erhalten.")
            try:
                await user.send(
                    f"\u2697\uFE0F **Herstellung abgeschlossen!**\n"
                    f"**{KOKAIN_GRAMM}\u00D7 Kokain ({KOKAIN_GRAMM}g)** wurde deinem Inventar hinzugef\u00FCgt.\n"
                    f"\U0001F4B0 Du kannst es jetzt im Kokain-Kanal verkaufen *(2.950 $ Schwarzgeld f\u00FCr 250g)*."
                )
            except Exception:
                pass
        bot.loop.create_task(_liefern())


# \u2500\u2500 Cooldown-Feld (einheitlich f\u00FCr beide Aktionen) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _foto_cd_remaining(user_id: int) -> tuple[int, str]:
    """Gibt (verbleibende Sekunden, Aktion) zur\u00FCck."""
    eco = load_economy()
    ud  = get_user(eco, user_id)
    last    = ud.get("koka_foto_cd")
    cd_secs = ud.get("koka_foto_cd_secs", KOKA_BLAETTER_CD_SECS)
    action  = ud.get("koka_foto_cd_action", "")
    if not last:
        return 0, action
    try:
        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
        return max(0, int(cd_secs - elapsed)), action
    except Exception:
        return 0, action


# \u2500\u2500 on_message \u2014 Foto-Erkennung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.listen("on_message")
async def koka_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != KOKA_BILD_CHANNEL_ID:
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

    # Bilder herunterladen BEVOR die Nachricht gel\u00F6scht wird
    try:
        log_files = [await att.to_file() for att in img_atts]
    except Exception:
        log_files = []

    try:
        await message.delete()
    except Exception:
        pass

    cd, action = _foto_cd_remaining(user.id)
    if cd > 0:
        m, s = divmod(cd, 60)
        if action == "sammeln":
            aktion_text = "am **Kokabl\u00E4tter sammeln**"
        elif action == "herstellen":
            aktion_text = "bei der **Kokain Herstellung**"
        else:
            aktion_text = "im **Cooldown**"
        try:
            await message.channel.send(
                f"{user.mention} \u23F3 Du bist aktuell noch {aktion_text} \u2014 noch **{m}m {s}s**!",
                delete_after=5,
            )
        except Exception:
            pass
        return

    try:
        log_ch = guild.get_channel(KOKA_LOG_CHANNEL_ID) or await bot.fetch_channel(KOKA_LOG_CHANNEL_ID)
        if log_ch:
            emb = discord.Embed(
                title="\U0001F4F8 Foto eingereicht",
                description=f"{user.mention} hat ein Foto in <#{KOKA_BILD_CHANNEL_ID}> eingereicht.",
                color=0xFF6B00,
                timestamp=datetime.now(timezone.utc),
            )
            emb.set_footer(text="Paradise City \u2022 Kokain-System")
            await log_ch.send(embed=emb, files=log_files)
    except Exception as e:
        print(f"[kokain] Log-Fehler: {e}")

    embed = discord.Embed(
        title="\U0001F33F Kokain-System",
        description=(
            f"{user.mention}, was m\u00F6chtest du tun?\n\n"
            "\U0001F33F **Kokabl\u00E4tter sammeln** \u2014 5 Min. Cooldown \u00B7 50\u2013150 Bl\u00E4tter\n"
            "\u2697\uFE0F **Kokain herstellen** \u2014 15 Min. Cooldown \u00B7 35 Bl\u00E4tter n\u00F6tig \u00B7 250\u00D7 Kokain (250g)"
        ),
        color=0xFF6B00,
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Nur du kannst diese Buttons dr\u00FCcken")

    try:
        await message.channel.send(embed=embed, view=KokaAktionView(user.id, guild.id))
    except Exception as e:
        print(f"[kokain] Fehler beim Senden: {e}")


# \u2500\u2500 Info-Embed \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_info_embed() -> discord.Embed:
    cfg = _load_embed_cfg_koka()
    default_desc = (
        "**\U0001F4CD Standorte**\n"
        f"\u2523 **1\ufe0f\u20e3 Kokabll\u00e4tter sammeln** \u2014 Bild 1\n"
        f"\u2517 **2\ufe0f\u20e3 Kokain herstellen** \u2014 Bild 2\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        "**Schritt 1 \u2014 \U0001F33F Kokabll\u00e4tter sammeln**\n"
        f"\U0001F4F8 Schicke ein Foto in <#{KOKA_BILD_CHANNEL_ID}>\n"
        "\u23F3 Warte **5 Minuten** bis die Ernte abgeschlossen ist\n"
        "\U0001F3B2 Du erh\u00e4ltst zuf\u00e4llig **50 \u2013 150 Kokabll\u00e4tter**\n\n"
        "**Schritt 2 \u2014 \u2697\ufe0f Kokain herstellen**\n"
        f"\U0001F4F8 Schicke ein Foto in <#{KOKA_BILD_CHANNEL_ID}>\n"
        "\U0001F33F Voraussetzung: **35 Kokabll\u00e4tter**\n"
        "\u23F3 Herstellungszeit: **15 Minuten**\n"
        "\U0001F48A Ergebnis: **250\u00d7 Kokain (250g)** \u2014 Wert: **2.950\u00a0$ Schwarzgeld**\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\U0001F4B0 Dr\u00fccke **Kokain verkaufen** um dein Kokain direkt\n"
        "in Schwarzgeld umzutauschen *(250g = 2.950\u00a0$)*"
    )
    emb = discord.Embed(
        title=cfg.get("title", "\U0001F33F Kokain Herstellung"),
        color=cfg.get("color", 0xFF6B00),
        description=cfg.get("description") or default_desc,
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_footer(text=cfg.get("footer", "Paradise City Roleplay \u2022 Kokain-System"))
    return emb


async def _koka_setup() -> str:
    await bot.wait_until_ready()
    await asyncio.sleep(3)
    try:
        channel = await bot.fetch_channel(KOKA_INFO_CHANNEL_ID)
    except Exception as e:
        print(f"[kokain] Info-Kanal nicht erreichbar: {e}")
        return f"\u274C Kanal nicht erreichbar: {e}"

    msg_id = None
    try:
        if KOKA_MSG_FILE.exists():
            msg_id = json.load(open(KOKA_MSG_FILE, encoding="utf-8")).get("message_id")
    except Exception:
        pass

    if msg_id:
        try:
            existing = await channel.fetch_message(msg_id)
            await existing.edit(embed=_build_info_embed(), view=KokaInfoView())
            print("[kokain] \u2705 Info-Embed aktualisiert.")
            return "\u2705 Kokain Info-Embed aktualisiert."
        except Exception:
            pass

    try:
        sent = await channel.send(embed=_build_info_embed(), view=KokaInfoView())
        json.dump({"message_id": sent.id}, open(KOKA_MSG_FILE, "w", encoding="utf-8"), indent=2)
        print("[kokain] \u2705 Info-Embed gesendet.")
        return "\u2705 Kokain Info-Embed gesendet."
    except Exception as e:
        print(f"[kokain] Senden fehlgeschlagen: {e}")
        return f"\u274C Senden fehlgeschlagen: {e}"


async def auto_kokain_setup():
    await _koka_setup()
