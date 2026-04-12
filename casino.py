# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# casino.py — Rubbellos-System
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

CASINO_PRIZES = [
    {
        "id":           "bier",
        "label":        "🍺  10× Bier",
        "weight":       45,
        "typ":          "item",
        "item":         "🍺| Bier",
        "menge":        10,
        "beschreibung": "**10× 🍺| Bier** wurden deinem Inventar hinzugefügt!",
    },
    {
        "id":           "geld5k",
        "label":        "💵  5.000 $",
        "weight":       35,
        "typ":          "geld",
        "betrag":       5_000,
        "beschreibung": "**5.000 $** wurden auf dein Bankkonto überwiesen!",
    },
    {
        "id":           "niete",
        "label":        "❌  Niete",
        "weight":       30,
        "typ":          "niete",
        "beschreibung": "Leider eine **Niete** — vielleicht beim nächsten Mal!",
    },
    {
        "id":           "geld10k",
        "label":        "💰  10.000 $",
        "weight":       25,
        "typ":          "geld",
        "betrag":       10_000,
        "beschreibung": "**10.000 $** wurden auf dein Bankkonto überwiesen!",
    },
    {
        "id":           "taschenlampe",
        "label":        "🔦  Taschenlampe",
        "weight":       25,
        "typ":          "item",
        "item":         "🔦| Taschenlampe",
        "menge":        1,
        "beschreibung": "**1× 🔦| Taschenlampe** wurde deinem Inventar hinzugefügt!",
    },
    {
        "id":           "koeder",
        "label":        "🪱  10× Angel Köder",
        "weight":       40,
        "typ":          "item",
        "item":         "🪱| Angel Köder",
        "menge":        10,
        "beschreibung": "**10× 🪱| Angel Köder** wurden deinem Inventar hinzugefügt!",
    },
    {
        "id":           "sportwagen",
        "label":        "🚗  SPORTWAGEN!",
        "weight":       5,
        "typ":          "sportwagen",
        "beschreibung": "🏆 **HAUPTGEWINN!** Du hast einen **Sportwagen** deiner Wahl (bis 200.000 $) gewonnen!",
    },
]


def _ensure_casino_shop_items():
    shop     = load_shop()
    existing = {normalize_item_name(i["name"]) for i in shop}
    defaults = [
        {"name": RUBBELLOS_ITEM,      "price": RUBBELLOS_PREIS},
        {"name": "🔦| Taschenlampe",  "price": 500},
        {"name": "🪱| Angel Köder",   "price": 500},
        {"name": "🍺| Bier",          "price": 200},
    ]
    changed = False
    for entry in defaults:
        if normalize_item_name(entry["name"]) not in existing:
            shop.append({"name": entry["name"], "price": entry["price"]})
            changed = True
    if changed:
        save_shop(shop)


def _pick_prize() -> dict:
    weights = [p["weight"] for p in CASINO_PRIZES]
    return random.choices(CASINO_PRIZES, weights=weights, k=1)[0]


def _build_result_embed(gewinn: dict, member: discord.Member, color: int) -> discord.Embed:
    lines = []
    for p in CASINO_PRIZES:
        if p["id"] == gewinn["id"]:
            lines.append(f"➤ **{p['label']}** ⬅")
        else:
            lines.append(f"　 {p['label']}")
    body = "\n".join(lines)

    embed = discord.Embed(
        title="🎟️ Rubbellos — Ergebnis",
        description=(
            f"{body}\n\n"
            "──────────────────────\n"
            f"🎯 **Dein Gewinn:**\n{gewinn['beschreibung']}"
        ),
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"{member.display_name} • Nur du siehst diese Nachricht")
    return embed


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

        inventory.pop(idx)

        gewinn = _pick_prize()
        now    = datetime.now(timezone.utc)

        if gewinn["typ"] == "geld":
            user_data["bank"] = user_data.get("bank", 0) + gewinn["betrag"]
            save_economy(eco)
            result_color = 0x2ECC71

        elif gewinn["typ"] == "item":
            _ensure_casino_shop_items()
            inventory.extend([gewinn["item"]] * gewinn["menge"])
            save_economy(eco)
            result_color = 0x2ECC71

        elif gewinn["typ"] == "sportwagen":
            save_economy(eco)
            result_color = 0xFFD700
            ticket_ch      = interaction.guild.get_channel(TICKET_SETUP_CHANNEL_ID)
            ticket_mention = ticket_ch.mention if ticket_ch else f"<#{TICKET_SETUP_CHANNEL_ID}>"
            gewinn = dict(gewinn)
            gewinn["beschreibung"] = (
                f"🏆 **HAUPTGEWINN!** 🏆\n"
                f"Du hast einen **Sportwagen deiner Wahl** (bis 200.000 $) gewonnen!\n\n"
                f"Bitte erstelle ein Ticket in {ticket_mention} um deinen Gewinn abzuholen!"
            )

        else:
            save_economy(eco)
            result_color = 0xFF4444

        result_embed = _build_result_embed(gewinn, member, result_color)
        await interaction.response.send_message(embed=result_embed, ephemeral=True)

        log_ch = interaction.guild.get_channel(CASINO_LOG_CHANNEL_ID)
        if log_ch:
            log_color = (
                0xFFD700 if gewinn["typ"] == "sportwagen"
                else (0xFF4444 if gewinn["typ"] == "niete" else 0xE67E22)
            )
            log_embed = discord.Embed(
                title="🎟️ Rubbellos — Gewinn",
                description=(
                    f"**Spieler:** {member.mention} (`{member}`)\n"
                    f"**Gewinn:** {gewinn['label'].strip()}\n"
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
                "💡 *Gewinne landen automatisch in deinem Inventar oder auf deinem Bankkonto.*\n"
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
        view = CasinoView()

        # Bestehende Nachricht bearbeiten
        mid = _load_casino_msg_id()
        if mid:
            try:
                msg = await channel.fetch_message(mid)
                await msg.edit(embed=embed, view=view)
                print(f"[casino] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        # Neu senden und ID speichern
        try:
            new_msg = await channel.send(embed=embed, view=view)
            _save_casino_msg_id(new_msg.id)
            print(f"[casino] Embed gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_casino_setup fehlgeschlagen", str(e), guild)
