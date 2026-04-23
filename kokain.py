# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# kokain.py \u2014 Kokain-Herstellungs-System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#
# Ablauf:
#   1. Info-Embed wird in KOKA_INFO_CHANNEL_ID gepostet (on_ready)
#      \u2192 Enth\xe4lt Standorte, Anleitung und "Kokain verkaufen" Button
#   2. Spieler sendet Foto in KOKA_BILD_CHANNEL_ID
#   3. Bot l\xf6scht Foto, zeigt Auswahl:
#      A) Kokabl\xe4tter sammeln \u2192 5 Min. \u2192 50-150 Bl\xe4tter ins Inventar
#      B) Kokain herstellen  \u2192 25 Bl\xe4tter n\xf6tig \u2192 15 Min. \u2192 500g Kokain
#   4. "Kokain verkaufen" Button: 500g = 2.950$ Schwarzgeld (Item)
#   5. Jede Interaktion wird in KOKA_LOG_CHANNEL_ID geloggt
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from economy_helpers import (
    load_economy, save_economy, get_user,
    load_team_shop, find_shop_item, normalize_item_name,
)

# \u2500\u2500 Kanal-IDs \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

KOKA_INFO_CHANNEL_ID = 1490894293135790190   # Info-Embed + Verkaufs-Button
KOKA_BILD_CHANNEL_ID = 1490894294297477120   # Foto-Einreichungs-Kanal
KOKA_LOG_CHANNEL_ID  = 1490878131240829028   # Log-Kanal

# \u2500\u2500 Spielwerte \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

KOKA_BLAETTER_CD_SECS   = 5 * 60    # 5 Minuten Cooldown Bl\xe4tter sammeln
KOKA_KOKAIN_CD_SECS     = 15 * 60   # 15 Minuten Cooldown Kokain herstellen
KOKA_BLAETTER_MIN       = 50
KOKA_BLAETTER_MAX       = 150
KOKA_BLAETTER_PRO_RUNDE = 25        # Bl\xe4tter pro Herstellungsrunde
KOKAIN_GRAMM            = 500
KOKAIN_WERT             = 2_950     # $ Schwarzgeld pro 500g

# \u2500\u2500 Item-Namen (aus Team-Shop, falls vorhanden) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

ITEM_BLAETTER_DEFAULT    = "Kokabl\xe4tter"
ITEM_KOKAIN_DEFAULT      = "Kokain 500g"
ITEM_SCHWARZGELD_DEFAULT = "Schwarzgeld"


def _shop_name(query: str, default: str) -> str:
    """Gibt den exakten Team-Shop-Namen zur\xfcck, oder default falls nicht gefunden."""
    try:
        items = load_team_shop()
        match = find_shop_item(items, query)
        if match:
            return match["name"]
    except Exception:
        pass
    return default


# \u2500\u2500 Inventar-Hilfsfunktionen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _count_item(user_id: int, query: str) -> int:
    eco = load_economy()
    user_data = get_user(eco, user_id)
    inventory = user_data.get("inventory", [])
    norm_q = normalize_item_name(query)
    return sum(1 for i in inventory if norm_q in normalize_item_name(i))


def _consume_n(user_id: int, query: str, count: int) -> bool:
    """Entfernt exakt 'count' Kopien eines Items. True = erfolgreich."""
    eco = load_economy()
    user_data = get_user(eco, user_id)
    inventory = user_data.get("inventory", [])
    norm_q = normalize_item_name(query)
    matching = [i for i in inventory if norm_q in normalize_item_name(i)]
    if len(matching) < count:
        return False
    removed = 0
    new_inv = []
    for item in inventory:
        if removed < count and norm_q in normalize_item_name(item):
            removed += 1
        else:
            new_inv.append(item)
    user_data["inventory"] = new_inv
    eco[str(user_id)] = user_data
    save_economy(eco)
    return True


def _add_items(user_id: int, item_name: str, count: int):
    eco = load_economy()
    user_data = get_user(eco, user_id)
    user_data.setdefault("inventory", []).extend([item_name] * count)
    eco[str(user_id)] = user_data
    save_economy(eco)


# \u2500\u2500 Cooldown-Hilfsfunktionen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _cd_remaining(user_id: int, field: str, secs: int) -> int:
    """Verbleibende Cooldown-Sekunden (0 = bereit)."""
    eco = load_economy()
    user_data = get_user(eco, user_id)
    last = user_data.get(field)
    if not last:
        return 0
    try:
        vergangen = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
        return max(0, int(secs - vergangen))
    except Exception:
        return 0


def _set_cd(user_id: int, field: str):
    eco = load_economy()
    user_data = get_user(eco, user_id)
    user_data[field] = datetime.now(timezone.utc).isoformat()
    eco[str(user_id)] = user_data
    save_economy(eco)


# \u2500\u2500 Log-Hilfsfunktion \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _log(guild: discord.Guild, title: str, description: str):
    ch = guild.get_channel(KOKA_LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title=f"\U0001f33f {title}",
            description=description,
            color=0xFF6B00,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="Paradise City \u2022 Kokain-System")
        try:
            await ch.send(embed=embed)
        except Exception:
            pass
    try:
        import dashboard_hooks as _dh
        _dh.log_activity("KOKAIN", f"{title}: {description[:120]}")
    except Exception:
        pass


# \u2500\u2500 Info-Embed \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_info_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\U0001f33f Kokain Herstellung",
        color=0xFF6B00,
        description=(
            "**\U0001f4cd Standorte**\n"
            f"\u2523 **1\ufe0f\u20e3 Kokabl\xe4tter sammeln** \u2014 Sandy Shores \xb7 Kokain-Feld\n"
            f"\u2517 **2\ufe0f\u20e3 Kokain herstellen** \u2014 Davis \xb7 Unterirdisches Labor\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "**Schritt 1 \u2014 \U0001f33f Kokabl\xe4tter sammeln**\n"
            f"\U0001f4f8 Schicke ein Foto in <#{KOKA_BILD_CHANNEL_ID}>\n"
            "\u23f3 Warte **5 Minuten** bis die Ernte abgeschlossen ist\n"
            "\U0001f3b2 Du erh\xe4ltst zuf\xe4llig **50 \u2013 150 Kokabl\xe4tter**\n\n"
            "**Schritt 2 \u2014 \u2697\ufe0f Kokain herstellen**\n"
            f"\U0001f4f8 Schicke ein Foto in <#{KOKA_BILD_CHANNEL_ID}>\n"
            "\U0001f33f Voraussetzung: **25 Kokabl\xe4tter** (werden automatisch entnommen)\n"
            "\u23f3 Herstellungszeit: **15 Minuten**\n"
            "\U0001f48a Ergebnis: **500g Kokain** \u2014 Wert: **2.950 $ Schwarzgeld**\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "\U0001f4b0 Dr\xfccke den Button **Kokain verkaufen** um dein Kokain\n"
            "direkt in Schwarzgeld umzutauschen *(500g = 2.950 $)*"
        ),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Kokain-System")
    return embed


# \u2500\u2500 Persistent View: Info-Embed Verkaufs-Button \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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
        eco = load_economy()
        user_data = get_user(eco, user.id)
        inventory = user_data.get("inventory", [])

        norm_koka = normalize_item_name(ITEM_KOKAIN_DEFAULT)
        matching = [i for i in inventory if norm_koka in normalize_item_name(i)]
        count = len(matching)

        if count == 0:
            await interaction.response.send_message(
                "\u274c Du hast kein **Kokain 500g** in deinem Inventar.",
                ephemeral=True,
            )
            return

        # Kokain entfernen & Schwarzgeld hinzuf\xfcgen
        new_inv = [i for i in inventory if norm_koka not in normalize_item_name(i)]
        sg_name = _shop_name(ITEM_SCHWARZGELD_DEFAULT, ITEM_SCHWARZGELD_DEFAULT)
        new_inv.extend([sg_name] * count)
        user_data["inventory"] = new_inv
        eco[str(user.id)] = user_data
        save_economy(eco)

        total = count * KOKAIN_WERT
        await interaction.response.send_message(
            f"\u2705 **{count}\xd7 500g Kokain** verkauft!\n"
            f"\U0001f4b0 **{total:,}$ Schwarzgeld** wurde deinem Inventar hinzugef\xfcgt.",
            ephemeral=True,
        )
        await _log(
            interaction.guild,
            "\U0001f4b0 Kokain verkauft",
            f"{user.mention} (`{user}`) hat **{count}\xd7 500g Kokain** verkauft "
            f"\u2192 **{total:,}$ Schwarzgeld** ins Inventar",
        )


# \u2500\u2500 Tempor\xe4re View: Auswahl nach Foto-Einreichung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class KokaAktionView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "\u274c Das ist nicht dein Foto!", ephemeral=True
            )
            return False
        return True

    def _disable_all(self):
        for child in self.children:
            child.disabled = True

    # \u2500\u2500 Button A: Kokabl\xe4tter sammeln \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    @discord.ui.button(
        label="\U0001f33f Kokabl\xe4tter sammeln  (5 Min.)",
        style=discord.ButtonStyle.success,
    )
    async def blaetter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        cd = _cd_remaining(user.id, "koka_blaetter_cd", KOKA_BLAETTER_CD_SECS)
        if cd > 0:
            m, s = divmod(cd, 60)
            await interaction.response.send_message(
                f"\u23f3 Du kannst erst in **{m}m {s}s** wieder Kokabl\xe4tter sammeln.",
                ephemeral=True,
            )
            return

        menge = random.randint(KOKA_BLAETTER_MIN, KOKA_BLAETTER_MAX)
        _set_cd(user.id, "koka_blaetter_cd")

        await interaction.response.send_message(
            f"\U0001f33f Du sammelst **Kokabl\xe4tter...**\n"
            f"\u23f3 Komm in **5 Minuten** zur\xfcck \u2013 du erh\xe4ltst **{menge} Kokabl\xe4tter**!",
            ephemeral=True,
        )
        self._disable_all()
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await _log(
            interaction.guild,
            "\U0001f33f Kokabl\xe4tter sammeln gestartet",
            f"{user.mention} (`{user}`) sammelt **{menge} Kokabl\xe4tter** \u2014 fertig in 5 Min.",
        )

        async def _liefern():
            await asyncio.sleep(KOKA_BLAETTER_CD_SECS)
            item_name = _shop_name(ITEM_BLAETTER_DEFAULT, ITEM_BLAETTER_DEFAULT)
            _add_items(user.id, item_name, menge)
            try:
                dm = await user.create_dm()
                await dm.send(
                    f"\u2705 **Kokabl\xe4tter geerntet!**\n"
                    f"\U0001f33f **{menge} Kokabl\xe4tter** wurden deinem Inventar hinzugef\xfcgt."
                )
            except Exception:
                pass
            await _log(
                interaction.guild,
                "\u2705 Kokabl\xe4tter erhalten",
                f"{user.mention} (`{user}`) hat **{menge} Kokabl\xe4tter** ins Inventar bekommen.",
            )

        bot.loop.create_task(_liefern())

    # \u2500\u2500 Button B: Kokain herstellen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    @discord.ui.button(
        label="\u2697\ufe0f Kokain herstellen  (15 Min.)",
        style=discord.ButtonStyle.danger,
    )
    async def kokain_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        # Cooldown pr\xfcfen
        cd = _cd_remaining(user.id, "koka_kokain_cd", KOKA_KOKAIN_CD_SECS)
        if cd > 0:
            m, s = divmod(cd, 60)
            await interaction.response.send_message(
                f"\u23f3 Du kannst erst in **{m}m {s}s** wieder Kokain herstellen.",
                ephemeral=True,
            )
            return

        # Bl\xe4tter pr\xfcfen
        vorrat = _count_item(user.id, ITEM_BLAETTER_DEFAULT)
        if vorrat < KOKA_BLAETTER_PRO_RUNDE:
            await interaction.response.send_message(
                f"\u274c Nicht genug Kokabl\xe4tter!\n"
                f"\U0001f33f Vorhanden: **{vorrat}** \xb7 Ben\xf6tigt: **{KOKA_BLAETTER_PRO_RUNDE}**",
                ephemeral=True,
            )
            return

        # Bl\xe4tter entnehmen
        if not _consume_n(user.id, ITEM_BLAETTER_DEFAULT, KOKA_BLAETTER_PRO_RUNDE):
            await interaction.response.send_message(
                "\u274c Fehler beim Entnehmen der Kokabl\xe4tter. Bitte erneut versuchen.",
                ephemeral=True,
            )
            return

        _set_cd(user.id, "koka_kokain_cd")

        await interaction.response.send_message(
            f"\u2697\ufe0f **Kokain wird hergestellt...**\n"
            f"\U0001f33f **{KOKA_BLAETTER_PRO_RUNDE} Kokabl\xe4tter** entnommen.\n"
            f"\u23f3 Komm in **15 Minuten** zur\xfcck \u2013 du erh\xe4ltst **500g Kokain**!",
            ephemeral=True,
        )
        self._disable_all()
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await _log(
            interaction.guild,
            "\u2697\ufe0f Kokain Herstellung gestartet",
            f"{user.mention} (`{user}`) stellt **500g Kokain** her \u2014 "
            f"fertig in 15 Min. ({KOKA_BLAETTER_PRO_RUNDE} Bl\xe4tter entnommen)",
        )

        async def _liefern():
            await asyncio.sleep(KOKA_KOKAIN_CD_SECS)
            item_name = _shop_name(ITEM_KOKAIN_DEFAULT, ITEM_KOKAIN_DEFAULT)
            _add_items(user.id, item_name, 1)
            try:
                dm = await user.create_dm()
                await dm.send(
                    f"\u2705 **Kokain hergestellt!**\n"
                    f"\U0001f48a **500g Kokain** wurde deinem Inventar hinzugef\xfcgt.\n"
                    f"\U0001f4b0 Wert: **{KOKAIN_WERT:,}$ Schwarzgeld** \u2014 "
                    f"verkaufe es \xfcber den Info-Kanal!"
                )
            except Exception:
                pass
            await _log(
                interaction.guild,
                "\u2705 Kokain hergestellt",
                f"{user.mention} (`{user}`) hat **500g Kokain** ins Inventar bekommen.",
            )

        bot.loop.create_task(_liefern())


# \u2500\u2500 on_message \u2014 Foto-Erkennung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.listen("on_message")
async def koka_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != KOKA_BILD_CHANNEL_ID:
        return

    has_image = any(
        att.content_type and att.content_type.startswith("image/")
        for att in message.attachments
    )
    if not has_image:
        return

    user = message.author

    try:
        await message.delete()
    except discord.Forbidden:
        pass

    embed = discord.Embed(
        title="\U0001f33f Kokain-System",
        description=(
            f"{user.mention}, was m\xf6chtest du tun?\n\n"
            "**\U0001f33f Kokabl\xe4tter sammeln** \u2014 5 Min. Wartezeit \xb7 50\u2013150 Bl\xe4tter\n"
            "**\u2697\ufe0f Kokain herstellen** \u2014 25 Bl\xe4tter n\xf6tig \xb7 15 Min. \xb7 500g Kokain\n\n"
            "*Diese Nachricht l\xe4uft in 2 Minuten ab.*"
        ),
        color=0xFF6B00,
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Kokain-System")

    view = KokaAktionView(user.id)
    try:
        await message.channel.send(embed=embed, view=view, delete_after=120)
    except Exception:
        pass

    await _log(
        message.guild,
        "\U0001f4f8 Foto eingereicht",
        f"{user.mention} (`{user}`) hat ein Foto im Koka-Kanal eingereicht.",
    )


# \u2500\u2500 on_ready \u2014 Info-Embed automatisch setzen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _koka_setup():
    await bot.wait_until_ready()
    for guild in bot.guilds:
        channel = guild.get_channel(KOKA_INFO_CHANNEL_ID)
        if not channel:
            # Fallback: direkt per API holen
            try:
                channel = await bot.fetch_channel(KOKA_INFO_CHANNEL_ID)
            except Exception:
                print(f"[kokain] \u274c Info-Kanal {KOKA_INFO_CHANNEL_ID} nicht gefunden")
                continue

        embed = _build_info_embed()
        view  = KokaInfoView()

        # Alte Bot-Embeds mit diesem Titel l\xf6schen, dann frisch senden
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Kokain Herstellung" in emb.title:
                            try:
                                await msg.delete()
                            except Exception:
                                pass
        except Exception:
            pass

        try:
            await channel.send(embed=embed, view=view)
            print(f"[kokain] \u2705 Info-Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[kokain] \u274c Fehler beim Embed-Setup: {e}")


@bot.listen("on_ready")
async def kokain_on_ready():
    bot.add_view(KokaInfoView())   # Persistent View nach Neustart registrieren
    await _koka_setup()
