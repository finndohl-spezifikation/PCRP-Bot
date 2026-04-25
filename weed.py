# -*- coding: utf-8 -*-
# weed.py \u2014 Weed-System (Paradise City Roleplay)

from config import *
from economy_helpers import (
    load_economy, save_economy, get_user,
    load_team_shop, find_shop_item, normalize_item_name,
)

WEED_INFO_CHANNEL_ID   = 1490894289079767050
WEED_BILD_CHANNEL_ID   = 1490894290455498802
WEED_LOG_CHANNEL_ID    = 1490878131240829028

WEED_CD_SECS           = 10 * 60
WEED_GRAMM_MIN         = 120
WEED_GRAMM_MAX         = 500
WEED_PREIS_PRO_GRAMM   = 30
WEED_SAMEN_PRO_RUNDE   = 10

ITEM_WEED_SAMEN_DEFAULT    = "Weed Samen"
ITEM_WEED_DEFAULT          = "Weed"
ITEM_SCHWARZGELD_DEFAULT   = "Schwarzgeld"

WEED_MSG_FILE         = DATA_DIR / "weed_info_msg.json"
EMBED_CONFIGS_FILE    = DATA_DIR / "embed_configs.json"
BUTTON_CONFIGS_FILE   = DATA_DIR / "button_configs.json"

WEED_EMBED_DEFAULT = {
    "title":       "\U0001F331 Weed Anbau",
    "description": None,
    "color":       0x2ECC71,
    "footer":      "Paradise City Roleplay \u2022 Weed-System",
}
WEED_BTN_DEFAULT = {
    "weed_sell_btn": {"label": "\U0001F4B0 Weed verkaufen", "style": "success"},
}


def _load_embed_cfg_weed() -> dict:
    try:
        if EMBED_CONFIGS_FILE.exists():
            d = json.load(open(EMBED_CONFIGS_FILE, encoding="utf-8"))
            merged = dict(WEED_EMBED_DEFAULT)
            merged.update(d.get("weed") or {})
            return merged
    except Exception:
        pass
    return dict(WEED_EMBED_DEFAULT)


def _load_button_cfg_weed(key: str) -> dict:
    try:
        if BUTTON_CONFIGS_FILE.exists():
            d = json.load(open(BUTTON_CONFIGS_FILE, encoding="utf-8"))
            merged = dict(WEED_BTN_DEFAULT.get(key, {}))
            merged.update(d.get(key) or {})
            return merged
    except Exception:
        pass
    return dict(WEED_BTN_DEFAULT.get(key, {}))


# -- Hilfsfunktionen ------------------------------------------

def _shop_name_weed(query: str, default: str) -> str:
    try:
        match = find_shop_item(load_team_shop(), query)
        if match:
            return match["name"]
    except Exception:
        pass
    return default


def _count_item_weed(user_id: int, query: str) -> int:
    eco = load_economy()
    inv = get_user(eco, user_id).get("inventory", [])
    nq  = normalize_item_name(query)
    return sum(1 for i in inv if nq in normalize_item_name(i))


def _consume_n_weed(user_id: int, query: str, count: int) -> bool:
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


def _add_items_weed(user_id: int, item_name: str, count: int):
    eco = load_economy()
    ud  = get_user(eco, user_id)
    ud.setdefault("inventory", []).extend([item_name] * count)
    eco[str(user_id)] = ud
    save_economy(eco)


def _set_weed_cd(user_id: int):
    eco = load_economy()
    ud  = get_user(eco, user_id)
    ud["weed_foto_cd"] = datetime.now(timezone.utc).isoformat()
    eco[str(user_id)] = ud
    save_economy(eco)


def _weed_cd_remaining(user_id: int) -> int:
    try:
        eco  = load_economy()
        ud   = get_user(eco, user_id)
        last = ud.get("weed_foto_cd")
        if not last:
            return 0
        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
        return max(0, int(WEED_CD_SECS - elapsed))
    except Exception:
        return 0


async def _log_weed(guild, title: str, desc: str):
    ch = guild.get_channel(WEED_LOG_CHANNEL_ID) if guild else None
    if ch:
        emb = discord.Embed(
            title=f"\U0001F7E2 {title}", description=desc,
            color=0x2ECC71, timestamp=datetime.now(timezone.utc),
        )
        emb.set_footer(text="Paradise City \u2022 Weed-System")
        try:
            await ch.send(embed=emb)
        except Exception:
            pass


# -- Persistent View: Weed verkaufen --------------------------

class WeedInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        cfg = _load_button_cfg_weed("weed_sell_btn")
        _style_map = {
            "success":   discord.ButtonStyle.success,
            "danger":    discord.ButtonStyle.danger,
            "primary":   discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary,
        }
        for child in self.children:
            if getattr(child, "custom_id", "") == "weed_sell_btn":
                if cfg.get("label"):
                    child.label = cfg["label"]
                if cfg.get("style") in _style_map:
                    child.style = _style_map[cfg["style"]]

    @discord.ui.button(
        label="\U0001F4B0 Weed verkaufen",
        style=discord.ButtonStyle.success,
        custom_id="weed_sell_btn",
    )
    async def sell(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        eco  = load_economy()
        ud   = get_user(eco, user.id)
        inv  = ud.get("inventory", [])

        # Weed-Items finden (nur "Weed", nicht "Weed Samen")
        nw      = normalize_item_name(ITEM_WEED_DEFAULT)
        ns      = normalize_item_name(ITEM_WEED_SAMEN_DEFAULT)
        hits    = [i for i in inv if nw in normalize_item_name(i) and ns not in normalize_item_name(i)]
        if not hits:
            await interaction.response.send_message(
                "\u274C Du hast kein **Weed** im Inventar.", ephemeral=True)
            return

        # Weed-Items entfernen, Samen behalten
        new_inv    = []
        to_remove  = len(hits)
        for item in inv:
            nitem = normalize_item_name(item)
            if nw in nitem and ns not in nitem and to_remove > 0:
                to_remove -= 1
            else:
                new_inv.append(item)
        ud["inventory"] = new_inv

        gramm    = len(hits)
        total_sg = gramm * WEED_PREIS_PRO_GRAMM
        ud["schwarzgeld"] = int(ud.get("schwarzgeld", 0)) + total_sg

        eco[str(user.id)] = ud
        save_economy(eco)
        await interaction.response.send_message(
            f"\u2705 **{gramm}g Weed** verkauft!\n"
            f"\U0001f4b5 **{total_sg:,}$** wurden deinem **Schwarzgeld** gutgeschrieben.", ephemeral=True)
        await _log_weed(interaction.guild, "\U0001f4b0 Weed verkauft",
            f"{user.mention} hat **{gramm}g Weed** verkauft \u2014 **{total_sg:,}$** Schwarzgeld gutgeschrieben")


# -- on_message: Foto startet Anbau direkt --------------------

@bot.listen("on_message")
async def weed_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != WEED_BILD_CHANNEL_ID:
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
    cd = _weed_cd_remaining(user.id)
    if cd > 0:
        m, s = divmod(cd, 60)
        try:
            await message.channel.send(
                f"{user.mention} \u23F3 Du bist noch beim **Weed anbauen** \u2014 noch **{m}m {s}s**!",
                delete_after=6,
            )
        except Exception:
            pass
        return

    # Samen-Check
    vorrat = _count_item_weed(user.id, ITEM_WEED_SAMEN_DEFAULT)
    if vorrat < WEED_SAMEN_PRO_RUNDE:
        try:
            await message.channel.send(
                f"{user.mention} \u274C Nicht genug **Weed Samen**!\n"
                f"\U0001F331 Vorhanden: **{vorrat}** \u00B7 Ben\u00F6tigt: **{WEED_SAMEN_PRO_RUNDE}**\n"
                f"Kaufe Weed Samen auf dem **Schwarzmarkt**.",
                delete_after=8,
            )
        except Exception:
            pass
        return

    # Samen verbrauchen
    if not _consume_n_weed(user.id, ITEM_WEED_SAMEN_DEFAULT, WEED_SAMEN_PRO_RUNDE):
        try:
            await message.channel.send(
                f"{user.mention} \u274C Fehler beim Entnehmen der Weed Samen.",
                delete_after=6,
            )
        except Exception:
            pass
        return

    _set_weed_cd(user.id)

    # Foto im Log speichern
    try:
        log_ch = guild.get_channel(WEED_LOG_CHANNEL_ID) or await bot.fetch_channel(WEED_LOG_CHANNEL_ID)
        if log_ch:
            emb = discord.Embed(
                title="\U0001F4F8 Anbau gestartet",
                description=(
                    f"{user.mention} hat ein Foto eingereicht.\n"
                    f"\U0001F331 **{WEED_SAMEN_PRO_RUNDE}x Weed Samen** entnommen \u2014 Ernte in **10 Min.**"
                ),
                color=0x2ECC71,
                timestamp=datetime.now(timezone.utc),
            )
            emb.set_footer(text="Paradise City \u2022 Weed-System")
            await log_ch.send(embed=emb, files=log_files)
    except Exception as e:
        print(f"[weed] Log-Fehler: {e}")

    # Best\u00E4tigung im Kanal
    try:
        await message.channel.send(
            f"{user.mention} \U0001F331 **Weed Anbau gestartet!**\n"
            f"\U0001F4E6 **{WEED_SAMEN_PRO_RUNDE}x Weed Samen** entnommen.\n"
            f"\u23F3 In **10 Minuten** ist die Ernte fertig \u2014 du bekommst eine DM.",
            delete_after=10,
        )
    except Exception:
        pass

    # Ernten nach 10 Minuten
    async def _ernten():
        await asyncio.sleep(WEED_CD_SECS)
        gramm     = random.randint(WEED_GRAMM_MIN, WEED_GRAMM_MAX)
        item_name = _shop_name_weed(ITEM_WEED_DEFAULT, ITEM_WEED_DEFAULT)
        _add_items_weed(user.id, item_name, gramm)
        await _log_weed(guild, "\u2705 Ernte abgeschlossen",
            f"{user.mention} hat **{gramm}g Weed** geerntet.")
        try:
            await user.send(
                f"\U0001F331 **Ernte abgeschlossen!**\n"
                f"**{gramm}g Weed** wurden deinem Inventar hinzugef\u00FCgt.\n"
                f"\U0001F4B0 Du kannst es jetzt im Weed-Kanal verkaufen "
                f"*(30\u00A0$ Schwarzgeld pro Gramm)*."
            )
        except Exception:
            pass
    bot.loop.create_task(_ernten())


# -- Info-Embed ------------------------------------------------

def _build_weed_info_embed() -> discord.Embed:
    cfg = _load_embed_cfg_weed()
    default_desc = (
        "**\U0001F4E6 Voraussetzung**\n"
        f"> **{WEED_SAMEN_PRO_RUNDE}x Weed Samen** (Schwarzmarkt)\n\n"
        "**\U0001F4F8 Ablauf**\n"
        f"> Foto in <#{WEED_BILD_CHANNEL_ID}> schicken\n"
        "> Anbau startet **automatisch**\n"
        f"> Ernte nach **10 Min.**: {WEED_GRAMM_MIN}\u2013{WEED_GRAMM_MAX}g Weed\n"
        "> Du bekommst eine **DM** bei Fertigstellung\n\n"
        "**\U0001F4B0 Verkauf**\n"
        f"> **{WEED_PREIS_PRO_GRAMM}$ Schwarzgeld** pro Gramm\n\n"
        f"\U0001F4B0 Dr\u00FCcke **Weed verkaufen** um dein Weed gegen Schwarzgeld einzutauschen."
    )
    emb = discord.Embed(
        title=cfg.get("title", "\U0001F331 Weed Anbau"),
        color=cfg.get("color", 0x2ECC71),
        description=cfg.get("description") or default_desc,
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_footer(text=cfg.get("footer", "Paradise City Roleplay \u2022 Weed-System"))
    return emb


async def _weed_setup() -> str:
    try:
        channel = await bot.fetch_channel(WEED_INFO_CHANNEL_ID)
    except Exception as e:
        return f"\u274C Kanal nicht erreichbar (ID {WEED_INFO_CHANNEL_ID}): {e}"

    msg_id = None
    try:
        if WEED_MSG_FILE.exists():
            msg_id = json.load(open(WEED_MSG_FILE, encoding="utf-8")).get("message_id")
    except Exception:
        pass

    if msg_id:
        try:
            existing = await channel.fetch_message(msg_id)
            await existing.edit(embed=_build_weed_info_embed(), view=WeedInfoView())
            return "\u2705 Weed Info-Embed aktualisiert."
        except Exception:
            pass

    try:
        sent = await channel.send(embed=_build_weed_info_embed(), view=WeedInfoView())
        json.dump({"message_id": sent.id}, open(WEED_MSG_FILE, "w", encoding="utf-8"), indent=2)
        return "\u2705 Weed Info-Embed gesendet."
    except Exception as e:
        return f"\u274C Senden fehlgeschlagen: {e}"


async def auto_weed_setup():
    await bot.wait_until_ready()
    await asyncio.sleep(3)
    result = await _weed_setup()
    print(f"[weed] {result}")
