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

KOKA_BLAETTER_CD_SECS    = 5 * 60
KOKA_KOKAIN_CD_SECS      = 15 * 60
KOKA_BLAETTER_MIN        = 50
KOKA_BLAETTER_MAX        = 150
KOKA_BLAETTER_PRO_RUNDE  = 35
KOKAIN_WERT              = 2_950

ITEM_BLAETTER_DEFAULT    = "Kokabl\xe4tter"
ITEM_KOKAIN_DEFAULT      = "Kokain 250g"
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
            title=f"\U0001f33f {title}", description=desc,
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

    @discord.ui.button(
        label="\U0001f4b0 Kokain verkaufen",
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
                "\u274c Du hast kein **Kokain 250g** im Inventar.", ephemeral=True)
            return
        ud["inventory"] = [i for i in inv if nk not in normalize_item_name(i)]
        sg    = _shop_name(ITEM_SCHWARZGELD_DEFAULT, ITEM_SCHWARZGELD_DEFAULT)
        total = len(hits) * KOKAIN_WERT
        ud["inventory"].extend([sg] * total)
        eco[str(user.id)] = ud
        save_economy(eco)
        await interaction.response.send_message(
            f"\u2705 **{len(hits)}\xd7 250g Kokain** verkauft!\n"
            f"\U0001f4b0 **{total:,}\xd7 Schwarzgeld** ins Inventar.", ephemeral=True)
        await _log(interaction.guild, "\U0001f4b0 Kokain verkauft",
            f"{user.mention} hat **{len(hits)}\xd7 250g** \u2192 **{total:,}\xd7 Schwarzgeld**")


# \u2500\u2500 Tempor\xe4re View: Auswahl nach Foto-Einreichung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class KokaAktionView(discord.ui.View):
    def __init__(self, author_id: int, guild_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.guild_id  = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "\u274c Das ist nicht deine Auswahl!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="\U0001f33f Kokabl\xe4tter sammeln  (5 Min.)", style=discord.ButtonStyle.success)
    async def blaetter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user  = interaction.user
        guild = bot.get_guild(self.guild_id)

        _set_foto_cd(user.id, KOKA_BLAETTER_CD_SECS, action="sammeln")

        await interaction.response.send_message(
            f"\U0001f33f **Kokabl\xe4tter sammeln gestartet!**\n"
            f"\u23f3 In **5 Minuten** erh\xe4ltst du deine Kokabl\xe4tter.\n"
            f"\U0001f4f8 Erst danach kannst du wieder ein Foto schicken.",
            ephemeral=True,
        )
        try:
            await interaction.message.delete()
        except Exception:
            pass

        await _log(guild, "\U0001f33f Sammeln gestartet",
            f"{user.mention} sammelt Kokabl\xe4tter \u2014 fertig in 5 Min.")

        async def _liefern():
            menge = random.randint(KOKA_BLAETTER_MIN, KOKA_BLAETTER_MAX)
            await asyncio.sleep(KOKA_BLAETTER_CD_SECS)
            _add_items(user.id, _shop_name(ITEM_BLAETTER_DEFAULT, ITEM_BLAETTER_DEFAULT), menge)
            await _log(guild, "\u2705 Kokabl\xe4tter erhalten",
                f"{user.mention} hat **{menge} Kokabl\xe4tter** erhalten.")
            try:
                await user.send(
                    f"\U0001f33f **Ernte abgeschlossen!**\n"
                    f"Du hast **{menge} Kokabl\xe4tter** erhalten und sie wurden deinem Inventar hinzugef\xfcgt."
                )
            except Exception:
                pass
        bot.loop.create_task(_liefern())

    @discord.ui.button(label="\u2697\ufe0f Kokain herstellen  (15 Min.)", style=discord.ButtonStyle.danger)
    async def kokain_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user  = interaction.user
        guild = bot.get_guild(self.guild_id)

        vorrat = _count_item(user.id, ITEM_BLAETTER_DEFAULT)
        if vorrat < KOKA_BLAETTER_PRO_RUNDE:
            await interaction.response.send_message(
                f"\u274c Nicht genug Kokabl\xe4tter!\n"
                f"\U0001f33f Vorhanden: **{vorrat}** \xb7 Ben\xf6tigt: **{KOKA_BLAETTER_PRO_RUNDE}**",
                ephemeral=True)
            return

        if not _consume_n(user.id, ITEM_BLAETTER_DEFAULT, KOKA_BLAETTER_PRO_RUNDE):
            await interaction.response.send_message(
                "\u274c Fehler beim Entnehmen der Kokabl\xe4tter.", ephemeral=True)
            return

        _set_foto_cd(user.id, KOKA_KOKAIN_CD_SECS, action="herstellen")

        await interaction.response.send_message(
            f"\u2697\ufe0f **Kokain Herstellung gestartet!**\n"
            f"\U0001f33f **{KOKA_BLAETTER_PRO_RUNDE} Kokabl\xe4tter** entnommen.\n"
            f"\u23f3 In **15 Minuten** erh\xe4ltst du **250g Kokain**.\n"
            f"\U0001f4f8 Erst danach kannst du wieder ein Foto schicken.",
            ephemeral=True,
        )
        try:
            await interaction.message.delete()
        except Exception:
            pass

        await _log(guild, "\u2697\ufe0f Herstellung gestartet",
            f"{user.mention} stellt **250g Kokain** her \u2014 fertig in 15 Min. "
            f"({KOKA_BLAETTER_PRO_RUNDE} Bl\xe4tter entnommen)")

        async def _liefern():
            await asyncio.sleep(KOKA_KOKAIN_CD_SECS)
            _add_items(user.id, _shop_name(ITEM_KOKAIN_DEFAULT, ITEM_KOKAIN_DEFAULT), 1)
            await _log(guild, "\u2705 Kokain hergestellt",
                f"{user.mention} hat **250g Kokain** erhalten.")
            try:
                await user.send(
                    f"\u2697\ufe0f **Herstellung abgeschlossen!**\n"
                    f"**250g Kokain** wurde deinem Inventar hinzugef\xfcgt.\n"
                    f"\U0001f4b0 Du kannst es jetzt im Kokain-Kanal verkaufen *(2.950 $ Schwarzgeld)*."
                )
            except Exception:
                pass
        bot.loop.create_task(_liefern())


# \u2500\u2500 Cooldown-Feld (einheitlich f\xfcr beide Aktionen) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _foto_cd_remaining(user_id: int) -> tuple[int, str]:
    """Gibt (verbleibende Sekunden, Aktion) zur\xfcck."""
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

    # Bilder herunterladen BEVOR die Nachricht gel\xf6scht wird
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
            aktion_text = "am **Kokabl\xe4tter sammeln**"
        elif action == "herstellen":
            aktion_text = "bei der **Kokain Herstellung**"
        else:
            aktion_text = "im **Cooldown**"
        try:
            await message.channel.send(
                f"{user.mention} \u23f3 Du bist aktuell noch {aktion_text} \u2014 noch **{m}m {s}s**!",
                delete_after=5,
            )
        except Exception:
            pass
        return

    try:
        log_ch = guild.get_channel(KOKA_LOG_CHANNEL_ID) or await bot.fetch_channel(KOKA_LOG_CHANNEL_ID)
        if log_ch:
            emb = discord.Embed(
                title="\U0001f4f8 Foto eingereicht",
                description=f"{user.mention} hat ein Foto in <#{KOKA_BILD_CHANNEL_ID}> eingereicht.",
                color=0xFF6B00,
                timestamp=datetime.now(timezone.utc),
            )
            emb.set_footer(text="Paradise City \u2022 Kokain-System")
            await log_ch.send(embed=emb, files=log_files)
    except Exception as e:
        print(f"[kokain] Log-Fehler: {e}")

    embed = discord.Embed(
        title="\U0001f33f Kokain-System",
        description=(
            f"{user.mention}, was m\xf6chtest du tun?\n\n"
            "\U0001f33f **Kokabl\xe4tter sammeln** \u2014 5 Min. Cooldown \xb7 50\u2013150 Bl\xe4tter\n"
            "\u2697\ufe0f **Kokain herstellen** \u2014 15 Min. Cooldown \xb7 35 Bl\xe4tter n\xf6tig \xb7 250g Kokain"
        ),
        color=0xFF6B00,
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Nur du kannst diese Buttons dr\xfccken")

    try:
        await message.channel.send(embed=embed, view=KokaAktionView(user.id, guild.id))
    except Exception as e:
        print(f"[kokain] Fehler beim Senden: {e}")


# \u2500\u2500 Info-Embed \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_info_embed() -> discord.Embed:
    emb = discord.Embed(
        title="\U0001f33f Kokain Herstellung",
        color=0xFF6B00,
        description=(
            "**\U0001f4cd Standorte**\n"
            f"\u2523 **1\ufe0f\u20e3 Kokabl\xe4tter sammeln** \u2014 Bild 1\n"
            f"\u2517 **2\ufe0f\u20e3 Kokain herstellen** \u2014 Bild 2\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "**Schritt 1 \u2014 \U0001f33f Kokabl\xe4tter sammeln**\n"
            f"\U0001f4f8 Schicke ein Foto in <#{KOKA_BILD_CHANNEL_ID}>\n"
            "\u23f3 Warte **5 Minuten** bis die Ernte abgeschlossen ist\n"
            "\U0001f3b2 Du erh\xe4ltst zuf\xe4llig **50 \u2013 150 Kokabl\xe4tter**\n\n"
            "**Schritt 2 \u2014 \u2697\ufe0f Kokain herstellen**\n"
            f"\U0001f4f8 Schicke ein Foto in <#{KOKA_BILD_CHANNEL_ID}>\n"
            "\U0001f33f Voraussetzung: **35 Kokabl\xe4tter**\n"
            "\u23f3 Herstellungszeit: **15 Minuten**\n"
            "\U0001f48a Ergebnis: **250g Kokain** \u2014 Wert: **2.950 $ Schwarzgeld**\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "\U0001f4b0 Dr\xfccke **Kokain verkaufen** um dein Kokain direkt\n"
            "in Schwarzgeld umzutauschen *(250g = 2.950 $)*"
        ),
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_footer(text="Paradise City Roleplay \u2022 Kokain-System")
    return emb


async def _koka_setup():
    await bot.wait_until_ready()
    await asyncio.sleep(3)
    try:
        channel = await bot.fetch_channel(KOKA_INFO_CHANNEL_ID)
    except Exception as e:
        print(f"[kokain] Info-Kanal nicht erreichbar: {e}")
        return

    try:
        async for msg in channel.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds:
                if any("Kokain Herstellung" in (e.title or "") for e in msg.embeds):
                    try:
                        await msg.delete()
                    except Exception:
                        pass
    except Exception:
        pass

    try:
        await channel.send(embed=_build_info_embed(), view=KokaInfoView())
    except Exception as e:
        print(f"[kokain] Senden fehlgeschlagen: {e}")


async def auto_kokain_setup():
    await _koka_setup()
