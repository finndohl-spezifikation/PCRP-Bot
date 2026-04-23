# -*- coding: utf-8 -*-
# weed.py â€” Weed-System (Paradise City Roleplay)

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

ITEM_WEED_SAMEN_DEFAULT = "Weed Samen"
ITEM_WEED_DEFAULT       = "Weed"


# â”€â”€ Hilfsfunktionen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Persistent View: Weed verkaufen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class WeedInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

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
        nw   = normalize_item_name(ITEM_WEED_DEFAULT)
        hits = [i for i in inv if nw in normalize_item_name(i)]
        if not hits:
            await interaction.response.send_message(
                "\u274C Du hast kein **Weed** im Inventar.", ephemeral=True)
            return
        ud["inventory"] = [i for i in inv if nw not in normalize_item_name(i)]
        gramm    = len(hits)
        total_sg = gramm * WEED_PREIS_PRO_GRAMM
        ud["schwarzgeld"] = ud.get("schwarzgeld", 0) + total_sg
        eco[str(user.id)] = ud
        save_economy(eco)
        await interaction.response.send_message(
            f"\u2705 **{gramm}g Weed** verkauft!\n"
            f"\U0001F4B0 **{total_sg:,}$ Schwarzgeld** deinem Konto gutgeschrieben.", ephemeral=True)
        await _log_weed(interaction.guild, "\U0001F4B0 Weed verkauft",
            f"{user.mention} hat **{gramm}g Weed** \u2192 **{total_sg:,}$ Schwarzgeld**")


# â”€â”€ on_message â€” Foto startet Anbau direkt â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

    # BestÃ¤tigung im Kanal
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


# â”€â”€ Info-Embed â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _build_weed_info_embed() -> discord.Embed:
    emb = discord.Embed(
        title="\U0001F331 Weed Anbau",
        color=0x2ECC71,
        description=(
            "\u2501" * 32 + "\n\n"
            "**\U0001F4E6 Voraussetzung**\n"
            f"\u2503 **{WEED_SAMEN_PRO_RUNDE}x Weed Samen** pro Anbau-Runde\n"
            "\u2503 Erh\u00E4ltlich auf dem **Schwarzmarkt**\n\n"
            "**\U0001F4F8 Ablauf**\n"
            f"\u2503 Schicke ein Foto in <#{WEED_BILD_CHANNEL_ID}>\n"
            f"\u2503 Der Anbau startet **automatisch** \u2014 kein Button n\u00F6tig\n"
            f"\u2503 Ernte: zuf\u00E4llig **{WEED_GRAMM_MIN}\u2013{WEED_GRAMM_MAX}g Weed** nach **10 Min.**\n"
            "\u2503 Du bekommst eine **DM** wenn die Ernte fertig ist\n\n"
            "**\U0001F4B0 Verkauf**\n"
            f"\u2503 **{WEED_PREIS_PRO_GRAMM}\u00A0$ Schwarzgeld** pro Gramm\n"
            f"\u2503 Maximal: **{WEED_GRAMM_MAX * WEED_PREIS_PRO_GRAMM:,}\u00A0$** pro Runde\n"
            "\u2503 Nur f\u00FCr Nutzer mit der **Illegalen Rolle**\n\n"
            "\u2501" * 32 + "\n"
            "\U0001F4B0 Dr\u00FCcke **Weed verkaufen** um dein Weed direkt\n"
            f"in Schwarzgeld umzutauschen *({WEED_PREIS_PRO_GRAMM}\u00A0$ pro Gramm)*"
        ),
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_footer(text="Paradise City Roleplay \u2022 Weed-System")
    return emb


async def _weed_setup():
    await bot.wait_until_ready()
    await asyncio.sleep(3)
    try:
        channel = await bot.fetch_channel(WEED_INFO_CHANNEL_ID)
    except Exception as e:
        print(f"[weed] Info-Kanal nicht erreichbar: {e}")
        return

    try:
        async for msg in channel.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds:
                if any("Weed Anbau" in (e.title or "") for e in msg.embeds):
                    try:
                        await msg.delete()
                    except Exception:
                        pass
    except Exception:
        pass

    try:
        await channel.send(embed=_build_weed_info_embed(), view=WeedInfoView())
    except Exception as e:
        print(f"[weed] Senden fehlgeschlagen: {e}")


async def auto_weed_setup():
    await _weed_setup()
