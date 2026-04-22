# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# casino.py \u2014 Rubbellos-System (interaktives Rubbeln)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from typing import Optional
from config import *
from helpers import log_bot_error
from economy_helpers import (
    load_economy, save_economy, get_user, load_shop, save_shop,
    load_team_shop, normalize_item_name
)

RUBBELLOS_ITEM  = "\U0001F39F\uFE0F| Rubbellos"
RUBBELLOS_PREIS = 1_000

# Speichert die letzte Rubbellos-Nachricht pro User f\u00FCr automatisches L\u00F6schen
_active_scratch_messages: dict[int, discord.WebhookMessage] = {}

CASINO_PRIZES = [
    {
        "id":           "niete",
        "label":        "\u274C  Niete",
        "symbol":       "\u274C",
        "weight":       30,
        "typ":          "niete",
        "beschreibung": "Leider eine **Niete** \u2014 vielleicht beim n\u00E4chsten Mal!",
    },
    {
        "id":           "geld1k",
        "label":        "\U0001F4B5  1.000 $",
        "symbol":       "\U0001F4B5 1K",
        "weight":       10,
        "typ":          "geld",
        "betrag":       1_000,
        "beschreibung": "**1.000 $** wurden auf dein Bankkonto \u00FCberwiesen!",
    },
    {
        "id":           "geld2500",
        "label":        "\U0001F4B5  2.500 $",
        "symbol":       "\U0001F4B5 2.5K",
        "weight":       20,
        "typ":          "geld",
        "betrag":       2_500,
        "beschreibung": "**2.500 $** wurden auf dein Bankkonto \u00FCberwiesen!",
    },
    {
        "id":           "geld5k",
        "label":        "\U0001F4B0  5.000 $",
        "symbol":       "\U0001F4B0 5K",
        "weight":       5,
        "typ":          "geld",
        "betrag":       5_000,
        "beschreibung": "**5.000 $** wurden auf dein Bankkonto \u00FCberwiesen!",
    },
    {
        "id":           "geld10k",
        "label":        "\U0001F4B0  10.000 $",
        "symbol":       "\U0001F4B0 10K",
        "weight":       5,
        "typ":          "geld",
        "betrag":       10_000,
        "beschreibung": "**10.000 $** wurden auf dein Bankkonto \u00FCberwiesen!",
    },
    {
        "id":           "geld25k",
        "label":        "\U0001F911  25.000 $",
        "symbol":       "\U0001F911 25K",
        "weight":       2,
        "typ":          "geld",
        "betrag":       25_000,
        "beschreibung": "**25.000 $** wurden auf dein Bankkonto \u00FCberwiesen!",
    },
    {
        "id":           "marlboro",
        "label":        "\U0001F6AC  10\u00D7 Marlboro Rot",
        "symbol":       "\U0001F6AC",
        "weight":       8,
        "typ":          "item",
        "item":         "\U0001F6AC| Marlboro Rot",
        "menge":        10,
        "beschreibung": "**10\u00D7 \U0001F6AC| Marlboro Rot** wurden deinem Inventar hinzugef\u00FCgt!",
    },
    {
        "id":           "efahrrad",
        "label":        "\U0001F6B2  Elektro Fahrrad",
        "symbol":       "\U0001F6B2",
        "weight":       3,
        "typ":          "item",
        "item":         "\U0001F6B2| Elektro Fahrrad",
        "menge":        1,
        "beschreibung": "**1\u00D7 \U0001F6B2| Elektro Fahrrad** wurde deinem Inventar hinzugef\u00FCgt!",
    },
    {
        "id":           "golfschlaeger",
        "label":        "\U0001F3CC\uFE0F  Golfschl\u00E4ger",
        "symbol":       "\U0001F3CC\uFE0F",
        "weight":       7,
        "typ":          "item",
        "item":         "\U0001F3CC\uFE0F| Golfschl\u00E4ger",
        "menge":        1,
        "beschreibung": "**1\u00D7 \U0001F3CC\uFE0F| Golfschl\u00E4ger** wurde deinem Inventar hinzugef\u00FCgt!",
    },
    {
        "id":           "lottolos",
        "label":        "\U0001F39F  Lottoschein",
        "symbol":       "\U0001F39F",
        "weight":       5,
        "typ":          "item",
        "item":         "\U0001F39F| Lottoschein",
        "menge":        1,
        "beschreibung": "**1\u00D7 \U0001F39F| Lottoschein** wurde deinem Inventar hinzugef\u00FCgt!",
    },
    {
        "id":           "autohaus",
        "label":        "\U0001F698  20% Gutschein Autohaus",
        "symbol":       "\U0001F698",
        "weight":       5,
        "typ":          "item",
        "item":         "\U0001F698| 20% Autohaus Gutschein",
        "menge":        1,
        "beschreibung": "**1\u00D7 \U0001F698| 20% Autohaus Gutschein** wurde deinem Inventar hinzugef\u00FCgt!",
    },
]

# Alle verf\u00FCgbaren Symbole f\u00FCr Felder \u2014 Niete-Symbol wird NICHT als Feld angezeigt
_ALL_SYMBOLS = [p["symbol"] for p in CASINO_PRIZES if p["typ"] != "niete"]


def _resolve_prize_item(prize_name: str) -> str:
    """Sucht den exakten Item-Namen zuerst im Team-Shop, dann im normalen Shop.
    Gibt den gefundenen Namen zur\u00FCck, oder den Original-Namen falls nirgends gefunden.
    Erstellt KEINE neuen Items."""
    norm = normalize_item_name(prize_name)
    for item in load_team_shop():
        if normalize_item_name(item["name"]) == norm:
            return item["name"]
    for item in load_shop():
        if normalize_item_name(item["name"]) == norm:
            return item["name"]
    return prize_name


def _ensure_casino_shop_items():
    shop     = load_shop()
    existing = {normalize_item_name(i["name"]) for i in shop}
    if normalize_item_name(RUBBELLOS_ITEM) not in existing:
        shop.append({"name": RUBBELLOS_ITEM, "price": RUBBELLOS_PREIS})
        save_shop(shop)


def _pick_prize() -> dict:
    weights = [p["weight"] for p in CASINO_PRIZES]
    return random.choices(CASINO_PRIZES, weights=weights, k=1)[0]


def _generate_card_values(prize: dict) -> list[str]:
    """
    Erstellt 9 Feld-Symbole f\u00FCr das Rubbellos.
    Nur echte Gewinn-Symbole werden verwendet.
    Gewinn: Gewinn-Symbol genau 3\u00D7 + 6 andere Symbole (max. 2\u00D7 gleich).
    Niete:  9 Symbole, kein Symbol 3\u00D7 vorhanden.
    """
    from collections import Counter

    if prize["typ"] == "niete":
        # Alle Symbole au\u00DFer Niete als m\u00F6gliche F\u00FCller, max 2\u00D7 das gleiche
        pool = [s for s in _ALL_SYMBOLS if s != "\u274C"]
        while True:
            cells = random.choices(pool, k=9)
            if max(Counter(cells).values()) <= 2:
                return cells
    else:
        win_sym = prize["symbol"]
        others  = [s for s in _ALL_SYMBOLS if s != win_sym]
        while True:
            fillers = random.choices(others, k=6)
            cells   = [win_sym, win_sym, win_sym] + fillers
            # Sicherstellen, dass kein anderes Symbol auch 3\u00D7 vorkommt
            counts = Counter(fillers)
            if max(counts.values()) <= 2:
                random.shuffle(cells)
                return cells


def _build_scratch_embed(
    revealed: list[bool],
    values: list[str],
    done: bool = False,
    prize: dict | None = None,
    member: discord.Member | None = None,
) -> discord.Embed:
    remaining = revealed.count(False)

    if done and prize:
        if prize["typ"] == "niete":
            color = 0xFF4444
            title = "\U0001F39F\uFE0F Rubbellos \u2014 Leider Niete!"
        else:
            color = 0x2ECC71
            title = "\U0001F39F\uFE0F Rubbellos \u2014 Gewonnen!"
        desc = (
            f"\U0001F3AF **Ergebnis:** {prize['beschreibung']}"
        )
    else:
        color = 0xE67E22
        title = "\U0001F39F\uFE0F Rubbellos \u2014 Rubbele alle Felder frei!"
        desc  = f"Noch **{remaining}** Feld{'er' if remaining != 1 else ''} \u00FCbrig \u2014 klick die \U0001F3AB Buttons!"

    embed = discord.Embed(title=title, description=desc, color=color,
                          timestamp=datetime.now(timezone.utc))
    if member:
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{member.display_name} \u2022 Nur du siehst diese Nachricht")
    return embed


# \u2500\u2500 Scratch-Button \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class ScratchButton(discord.ui.Button):
    def __init__(self, index: int, row_num: int):
        super().__init__(
            label="\U0001F3AB",
            style=discord.ButtonStyle.secondary,
            row=row_num,
            custom_id=f"scratch_cell:{index}:{uuid.uuid4().hex[:8]}",
        )
        self.cell_index = index

    async def callback(self, interaction: discord.Interaction):
        view: ScratchCardView = self.view

        if interaction.user.id != view.owner_id:
            await interaction.response.send_message(
                "\u274C Das ist nicht dein Rubbellos!", ephemeral=True
            )
            return

        if view.revealed[self.cell_index]:
            await interaction.response.defer()
            return

        # Feld aufdecken
        view.revealed[self.cell_index] = True
        sym = view.values[self.cell_index]

        self.label    = sym
        self.disabled = True
        self.style    = discord.ButtonStyle.secondary

        all_done = all(view.revealed)
        embed = _build_scratch_embed(
            view.revealed,
            view.values,
            done=all_done,
            prize=view.prize if all_done else None,
            member=interaction.user,
        )

        if all_done:
            # Alle Buttons deaktivieren
            for item in view.children:
                item.disabled = True
            view.stop()

            # Gewinn auszahlen & loggen
            await _payout_and_log(interaction, view.prize)

        await interaction.response.edit_message(embed=embed, view=view)


class ScratchCardView(TimedDisableView):
    def __init__(self, values: list[str], prize: dict, owner_id: int):
        super().__init__(timeout=300)
        self.values   = values
        self.prize    = prize
        self.owner_id = owner_id
        self.revealed = [False] * 9

        for i in range(9):
            self.add_item(ScratchButton(index=i, row_num=i // 3))


async def _payout_and_log(interaction: discord.Interaction, prize: dict):
    member = interaction.user
    eco    = load_economy()
    user_data = get_user(eco, member.id)
    now = datetime.now(timezone.utc)

    if prize["typ"] == "geld":
        user_data["bank"] = user_data.get("bank", 0) + prize["betrag"]
        save_economy(eco)

    elif prize["typ"] == "item":
        resolved  = _resolve_prize_item(prize["item"])
        inventory = user_data.setdefault("inventory", [])
        inventory.extend([resolved] * prize["menge"])
        save_economy(eco)

    elif prize["typ"] == "sportwagen":
        save_economy(eco)

    else:
        save_economy(eco)

    log_ch = interaction.guild.get_channel(CASINO_LOG_CHANNEL_ID)
    if log_ch:
        log_color = (
            0xFFD700 if prize["typ"] == "sportwagen"
            else (0xFF4444 if prize["typ"] == "niete" else 0xE67E22)
        )
        log_embed = discord.Embed(
            title="\U0001F39F\uFE0F Rubbellos \u2014 Gewinn",
            description=(
                f"**Spieler:** {member.mention} (`{member}`)\n"
                f"**Gewinn:** {prize['label'].strip()}\n"
                f"**Zeit:** <t:{int(now.timestamp())}:F>"
            ),
            color=log_color,
            timestamp=now,
        )
        log_embed.set_thumbnail(url=member.display_avatar.url)
        try:
            await log_ch.send(embed=log_embed)
        except Exception:
            pass


# \u2500\u2500 Haupt-Button im Casino-Channel \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class CasinoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="\U0001F39F\uFE0F| Rubbeln",
        style=discord.ButtonStyle.primary,
        custom_id="casino_drehen",
    )
    async def casino_drehen(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user


        eco       = load_economy()
        user_data = get_user(eco, member.id)
        inventory = user_data.setdefault("inventory", [])

        norm_los = normalize_item_name(RUBBELLOS_ITEM)
        idx = next(
            (i for i, item in enumerate(inventory) if normalize_item_name(item) == norm_los),
            None,
        )
        if idx is None:
            await interaction.response.send_message(
                f"\u274C Du hast kein **{RUBBELLOS_ITEM}** in deinem Inventar.\n"
                f"Kaufe eines im Shop f\u00FCr **{RUBBELLOS_PREIS:,} $**!",
                ephemeral=True,
            )
            return

        # Rubbellos aus Inventar entfernen & Gewinn vorab bestimmen
        inventory.pop(idx)
        save_economy(eco)

        # Alte Rubbellos-Nachricht dieses Users l\u00F6schen
        if member.id in _active_scratch_messages:
            try:
                await _active_scratch_messages[member.id].delete()
            except Exception:
                pass
            del _active_scratch_messages[member.id]

        prize  = _pick_prize()
        values = _generate_card_values(prize)

        view  = ScratchCardView(values=values, prize=prize, owner_id=member.id)
        embed = _build_scratch_embed(
            revealed=[False] * 9,
            values=values,
            member=member,
        )

        await interaction.response.defer(ephemeral=True)
        msg = await interaction.followup.send(embed=embed, view=view, ephemeral=True, wait=True)
        _active_scratch_messages[member.id] = msg


# \u2500\u2500 Embed-Setup im Casino-Channel \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_CASINO_MSG_FILE = DATA_DIR / "casino_msg.json"

def _load_casino_msg_id() -> int | None:
    if _CASINO_MSG_FILE.exists():
        try:
            return json.load(open(_CASINO_MSG_FILE))["message_id"]
        except Exception:
            pass
    return None

def _save_casino_msg_id(mid: int):
    with open(_CASINO_MSG_FILE, "w") as f:
        json.dump({"message_id": mid}, f)

async def auto_casino_setup():
    _ensure_casino_shop_items()
    for guild in bot.guilds:
        channel = guild.get_channel(CASINO_CHANNEL_ID)
        if not channel:
            continue

        prize_lines = "\n".join(f"\u3000 {p['label']}" for p in CASINO_PRIZES)
        embed = discord.Embed(
            title="\U0001F39F\uFE0F Rubbellose",
            description=(
                f"{prize_lines}\n\n"
                "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
                f"\U0001F6D2 **Kaufe ein Rubbellos** im Shop f\u00FCr **{RUBBELLOS_PREIS:,} $**.\n"
                "\U0001F39F\uFE0F **Dr\u00FCcke den Button** um dein Rubbellos einzul\u00F6sen.\n\n"
                "\U0001F4A1 *Rubbele alle 9 Felder frei \u2014 3\u00D7 dasselbe Symbol = Gewinn!*\n"
                "\U0001F3C6 *Beim Sportwagen-Hauptgewinn bitte ein Ticket erstellen!*"
            ),
            color=0xE67E22,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name="\U0001F39F\uFE0F Paradise City Roleplay \u2014 Rubbellose",
            icon_url=bot.user.display_avatar.url,
        )
        embed.set_footer(text="Paradise City Roleplay \u2022 Rubbellose | Viel Gl\u00FCck! \U0001F340")
        embed.set_thumbnail(url="https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/rubbellos.jpg")
        view = CasinoView()

        mid = _load_casino_msg_id()
        if mid:
            try:
                msg = await channel.fetch_message(mid)
                await msg.edit(embed=embed, view=view)
                print(f"[casino] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        try:
            new_msg = await channel.send(embed=embed, view=view)
            _save_casino_msg_id(new_msg.id)
            print(f"[casino] Embed gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_casino_setup fehlgeschlagen", str(e), guild)
