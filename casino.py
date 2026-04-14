# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# casino.py — Rubbellos-System (interaktives Rubbeln)
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from typing import Optional
from config import *
from helpers import log_bot_error
from economy_helpers import (
    load_economy, save_economy, get_user, load_shop, save_shop, normalize_item_name
)

RUBBELLOS_ITEM  = "🎟️| Rubbellos"
RUBBELLOS_PREIS = 1_000

# Speichert die letzte Rubbellos-Nachricht pro User für automatisches Löschen
_active_scratch_messages: dict[int, discord.WebhookMessage] = {}

CASINO_PRIZES = [
    {
        "id":           "niete",
        "label":        "❌  Niete",
        "symbol":       "❌",
        "weight":       30,
        "typ":          "niete",
        "beschreibung": "Leider eine **Niete** — vielleicht beim nächsten Mal!",
    },
    {
        "id":           "geld1k",
        "label":        "💵  1.000 $",
        "symbol":       "💵 1K",
        "weight":       10,
        "typ":          "geld",
        "betrag":       1_000,
        "beschreibung": "**1.000 $** wurden auf dein Bankkonto überwiesen!",
    },
    {
        "id":           "geld2500",
        "label":        "💵  2.500 $",
        "symbol":       "💵 2.5K",
        "weight":       20,
        "typ":          "geld",
        "betrag":       2_500,
        "beschreibung": "**2.500 $** wurden auf dein Bankkonto überwiesen!",
    },
    {
        "id":           "geld5k",
        "label":        "💰  5.000 $",
        "symbol":       "💰 5K",
        "weight":       5,
        "typ":          "geld",
        "betrag":       5_000,
        "beschreibung": "**5.000 $** wurden auf dein Bankkonto überwiesen!",
    },
    {
        "id":           "geld10k",
        "label":        "💰  10.000 $",
        "symbol":       "💰 10K",
        "weight":       5,
        "typ":          "geld",
        "betrag":       10_000,
        "beschreibung": "**10.000 $** wurden auf dein Bankkonto überwiesen!",
    },
    {
        "id":           "geld25k",
        "label":        "🤑  25.000 $",
        "symbol":       "🤑 25K",
        "weight":       2,
        "typ":          "geld",
        "betrag":       25_000,
        "beschreibung": "**25.000 $** wurden auf dein Bankkonto überwiesen!",
    },
    {
        "id":           "marlboro",
        "label":        "🚬  10× Marlboro Rot",
        "symbol":       "🚬",
        "weight":       8,
        "typ":          "item",
        "item":         "🚬| Marlboro Rot",
        "menge":        10,
        "beschreibung": "**10× 🚬| Marlboro Rot** wurden deinem Inventar hinzugefügt!",
    },
    {
        "id":           "efahrrad",
        "label":        "🚲  Elektro Fahrrad",
        "symbol":       "🚲",
        "weight":       3,
        "typ":          "item",
        "item":         "🚲| Elektro Fahrrad",
        "menge":        1,
        "beschreibung": "**1× 🚲| Elektro Fahrrad** wurde deinem Inventar hinzugefügt!",
    },
    {
        "id":           "golfschlaeger",
        "label":        "🏌️  Golfschläger",
        "symbol":       "🏌️",
        "weight":       7,
        "typ":          "item",
        "item":         "🏌️| Golfschläger",
        "menge":        1,
        "beschreibung": "**1× 🏌️| Golfschläger** wurde deinem Inventar hinzugefügt!",
    },
    {
        "id":           "lottolos",
        "label":        "🎟  Lottoschein",
        "symbol":       "🎟",
        "weight":       5,
        "typ":          "item",
        "item":         "🎟| Lottoschein",
        "menge":        1,
        "beschreibung": "**1× 🎟| Lottoschein** wurde deinem Inventar hinzugefügt!",
    },
    {
        "id":           "autohaus",
        "label":        "🚘  20% Gutschein Autohaus",
        "symbol":       "🚘",
        "weight":       5,
        "typ":          "item",
        "item":         "🚘| 20% Autohaus Gutschein",
        "menge":        1,
        "beschreibung": "**1× 🚘| 20% Autohaus Gutschein** wurde deinem Inventar hinzugefügt!",
    },
]

# Alle verfügbaren Symbole für Felder — Niete-Symbol wird NICHT als Feld angezeigt
_ALL_SYMBOLS = [p["symbol"] for p in CASINO_PRIZES if p["typ"] != "niete"]


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
    Erstellt 9 Feld-Symbole für das Rubbellos.
    Nur echte Gewinn-Symbole werden verwendet.
    Gewinn: Gewinn-Symbol genau 3× + 6 andere Symbole (max. 2× gleich).
    Niete:  9 Symbole, kein Symbol 3× vorhanden.
    """
    from collections import Counter

    if prize["typ"] == "niete":
        # Alle Symbole außer Niete als mögliche Füller, max 2× das gleiche
        pool = [s for s in _ALL_SYMBOLS if s != "❌"]
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
            # Sicherstellen, dass kein anderes Symbol auch 3× vorkommt
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
            title = "🎟️ Rubbellos — Leider Niete!"
        else:
            color = 0x2ECC71
            title = "🎟️ Rubbellos — Gewonnen!"
        desc = (
            f"🎯 **Ergebnis:** {prize['beschreibung']}"
        )
    else:
        color = 0xE67E22
        title = "🎟️ Rubbellos — Rubbele alle Felder frei!"
        desc  = f"Noch **{remaining}** Feld{'er' if remaining != 1 else ''} übrig — klick die 🎫 Buttons!"

    embed = discord.Embed(title=title, description=desc, color=color,
                          timestamp=datetime.now(timezone.utc))
    if member:
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{member.display_name} • Nur du siehst diese Nachricht")
    return embed


# ── Scratch-Button ────────────────────────────────────────────

class ScratchButton(discord.ui.Button):
    def __init__(self, index: int, row_num: int):
        super().__init__(
            label="🎫",
            style=discord.ButtonStyle.secondary,
            row=row_num,
            custom_id=f"scratch_cell:{index}:{uuid.uuid4().hex[:8]}",
        )
        self.cell_index = index

    async def callback(self, interaction: discord.Interaction):
        view: ScratchCardView = self.view

        if interaction.user.id != view.owner_id:
            await interaction.response.send_message(
                "❌ Das ist nicht dein Rubbellos!", ephemeral=True
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


class ScratchCardView(discord.ui.View):
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
        inventory = user_data.setdefault("inventory", [])
        inventory.extend([prize["item"]] * prize["menge"])
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
            title="🎟️ Rubbellos — Gewinn",
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


# ── Haupt-Button im Casino-Channel ────────────────────────────

class CasinoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎟️| Rubbeln",
        style=discord.ButtonStyle.primary,
        custom_id="casino_drehen",
    )
    async def casino_drehen(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user

        if not any(r.id == CITIZEN_ROLE_ID for r in member.roles):
            await interaction.response.send_message(
                "❌ Du benötigst die **Bewohner**-Rolle um ein Rubbellos einzulösen.",
                ephemeral=True,
            )
            return

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
                f"❌ Du hast kein **{RUBBELLOS_ITEM}** in deinem Inventar.\n"
                f"Kaufe eines im Shop für **{RUBBELLOS_PREIS:,} $**!",
                ephemeral=True,
            )
            return

        # Rubbellos aus Inventar entfernen & Gewinn vorab bestimmen
        inventory.pop(idx)
        save_economy(eco)

        # Alte Rubbellos-Nachricht dieses Users löschen
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


# ── Embed-Setup im Casino-Channel ─────────────────────────────

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

        prize_lines = "\n".join(f"　 {p['label']}" for p in CASINO_PRIZES)
        embed = discord.Embed(
            title="🎟️ Rubbellose",
            description=(
                f"{prize_lines}\n\n"
                "──────────────────────\n"
                f"🛒 **Kaufe ein Rubbellos** im Shop für **{RUBBELLOS_PREIS:,} $**.\n"
                "🎟️ **Drücke den Button** um dein Rubbellos einzulösen.\n\n"
                "💡 *Rubbele alle 9 Felder frei — 3× dasselbe Symbol = Gewinn!*\n"
                "🏆 *Beim Sportwagen-Hauptgewinn bitte ein Ticket erstellen!*"
            ),
            color=0xE67E22,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name="🎟️ Paradise City Roleplay — Rubbellose",
            icon_url=bot.user.display_avatar.url,
        )
        embed.set_footer(text="Paradise City Roleplay — Rubbellose • Viel Glück! 🍀")
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
