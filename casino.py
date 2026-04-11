# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# casino.py — Casino Glücksrad System
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import log_bot_error
from economy_helpers import (
    load_economy, save_economy, get_user, load_shop, save_shop, normalize_item_name
)


CASINO_ITEM_BIER         = "🍺| Bier"
CASINO_ITEM_TASCHENLAMPE = "🔦| Taschenlampe"
CASINO_ITEM_KOEDER       = "🪱| Angel Köder"

CASINO_PRIZES = [
    {
        "id":           "bier",
        "label":        "🍺  10× Bier",
        "weight":       45,
        "typ":          "item",
        "item":         CASINO_ITEM_BIER,
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
        "item":         CASINO_ITEM_TASCHENLAMPE,
        "menge":        1,
        "beschreibung": "**1× 🔦| Taschenlampe** wurde deinem Inventar hinzugefügt!",
    },
    {
        "id":           "koeder",
        "label":        "🪱  10× Angel Köder",
        "weight":       40,
        "typ":          "item",
        "item":         CASINO_ITEM_KOEDER,
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

_PRIZE_ORDER = ["bier", "geld5k", "niete", "geld10k", "taschenlampe", "koeder", "sportwagen"]


def _load_casino_cd():
    if CASINO_COOLDOWN_FILE.exists():
        with open(CASINO_COOLDOWN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_casino_cd(data):
    with open(CASINO_COOLDOWN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _ensure_casino_shop_items():
    shop = load_shop()
    existing = {normalize_item_name(i["name"]) for i in shop}
    defaults = [
        {"name": CASINO_ITEM_TASCHENLAMPE, "price": 500},
        {"name": CASINO_ITEM_KOEDER,       "price": 500},
        {"name": CASINO_ITEM_BIER,         "price": 200},
    ]
    changed = False
    for entry in defaults:
        if normalize_item_name(entry["name"]) not in existing:
            shop.append({"name": entry["name"], "price": entry["price"]})
            changed = True
    if changed:
        save_shop(shop)


def _spin_wheel() -> dict:
    weights = [p["weight"] for p in CASINO_PRIZES]
    return random.choices(CASINO_PRIZES, weights=weights, k=1)[0]


def _build_wheel_embed(highlight_id: str | None, title: str, color: int) -> discord.Embed:
    lines = []
    for p in CASINO_PRIZES:
        if p["id"] == highlight_id:
            lines.append(f"➤ **{p['label']}** ⬅")
        else:
            lines.append(f"　 {p['label']}")
    wheel_body = "\n".join(lines)
    embed = discord.Embed(
        title=title,
        description=wheel_body,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Cryptik Roleplay — Casino Glücksrad")
    return embed


class CasinoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎰| Drehen",
        style=discord.ButtonStyle.primary,
        custom_id="casino_drehen",
    )
    async def casino_drehen(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user

        if not any(r.id == CITIZEN_ROLE_ID for r in member.roles):
            await interaction.response.send_message(
                "❌ Du benötigst die **Bewohner**-Rolle um das Glücksrad nutzen zu können.",
                ephemeral=True,
            )
            return

        cooldowns = _load_casino_cd()
        uid       = str(member.id)
        now       = datetime.now(timezone.utc)

        if uid in cooldowns:
            last_spin = datetime.fromisoformat(cooldowns[uid])
            diff      = (now - last_spin).total_seconds()
            if diff < 86400:
                remaining = 86400 - diff
                h = int(remaining // 3600)
                m = int((remaining % 3600) // 60)
                await interaction.response.send_message(
                    f"⏰ Du kannst das Glücksrad erst wieder in **{h}h {m}m** drehen!",
                    ephemeral=True,
                )
                return

        cooldowns[uid] = now.isoformat()
        _save_casino_cd(cooldowns)

        gewinn = _spin_wheel()

        await interaction.response.defer(ephemeral=True, thinking=True)

        prize_ids    = _PRIZE_ORDER
        target_idx   = prize_ids.index(gewinn["id"])
        spin_sequence: list[str] = []
        for i in range(21):
            spin_sequence.append(prize_ids[i % len(prize_ids)])
        for offset in [3, 2, 1, 0]:
            spin_sequence.append(prize_ids[(target_idx - offset) % len(prize_ids)])

        msg = None
        for idx, seg_id in enumerate(spin_sequence):
            embed = _build_wheel_embed(seg_id, "🎰 Das Rad dreht sich...", 0x00BFFF)
            if msg is None:
                msg = await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                try:
                    await msg.edit(embed=embed)
                except Exception:
                    pass
            if idx < 14:
                await asyncio.sleep(0.15)
            elif idx < 18:
                await asyncio.sleep(0.35)
            elif idx < 21:
                await asyncio.sleep(0.65)
            else:
                await asyncio.sleep(0.95)

        eco       = load_economy()
        user_data = get_user(eco, member.id)

        if gewinn["typ"] == "geld":
            user_data["bank"] = user_data.get("bank", 0) + gewinn["betrag"]
            save_economy(eco)
            result_color = 0x00FF88

        elif gewinn["typ"] == "item":
            _ensure_casino_shop_items()
            user_data.setdefault("inventory", []).extend([gewinn["item"]] * gewinn["menge"])
            save_economy(eco)
            result_color = 0x00FF88

        elif gewinn["typ"] == "sportwagen":
            result_color = 0xFFD700
            ticket_ch = interaction.guild.get_channel(TICKET_SETUP_CHANNEL_ID)
            ticket_mention = ticket_ch.mention if ticket_ch else f"<#{TICKET_SETUP_CHANNEL_ID}>"
            gewinn = dict(gewinn)
            gewinn["beschreibung"] = (
                f"🏆 **HAUPTGEWINN!** 🏆\n"
                f"Du hast einen **Sportwagen deiner Wahl** (bis 200.000 $) gewonnen!\n\n"
                f"Bitte erstelle ein Ticket in {ticket_mention} um deinen Gewinn abzuholen!"
            )

        else:
            result_color = 0xFF4444

        result_embed = _build_wheel_embed(gewinn["id"], "🎰 Glücksrad — Ergebnis", result_color)
        result_embed.description = (
            result_embed.description
            + "\n\n──────────────────────\n"
            f"🎯 **Dein Gewinn:**\n{gewinn['beschreibung']}"
        )
        result_embed.set_thumbnail(url=member.display_avatar.url)
        result_embed.set_footer(text=f"{member.display_name} • Nur du siehst diese Nachricht")

        try:
            if msg:
                await msg.edit(embed=result_embed)
            else:
                await interaction.followup.send(embed=result_embed, ephemeral=True)
        except Exception:
            pass

        log_ch = interaction.guild.get_channel(CASINO_LOG_CHANNEL_ID)
        if log_ch:
            log_color = 0xFFD700 if gewinn["typ"] == "sportwagen" else (0xFF4444 if gewinn["typ"] == "niete" else 0x00BFFF)
            log_embed = discord.Embed(
                title="🎰 Casino — Glücksrad Spin",
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


async def auto_casino_setup():
    _ensure_casino_shop_items()
    for guild in bot.guilds:
        channel = guild.get_channel(CASINO_CHANNEL_ID)
        if not channel:
            continue
        already = False
        try:
            async for msg in channel.history(limit=30):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Glücksrad" in emb.title:
                            already = True
                            break
                if already:
                    break
        except Exception:
            pass
        if already:
            print(f"Casino-Embed bereits vorhanden in #{channel.name}, überspringe.")
            continue

        wheel_lines = "\n".join(f"　 {p['label']}" for p in CASINO_PRIZES)
        embed = discord.Embed(
            title="🎰 Glücksrad",
            description=(
                f"{wheel_lines}\n\n"
                "──────────────────────\n"
                "🎯 **Drücke den Button um das Rad zu drehen!**\n"
                "⏰ Jeder **Bewohner** kann **1× alle 24 Stunden** drehen.\n\n"
                "💡 *Gewinne landen automatisch in deinem Inventar oder auf deinem Bankkonto.*\n"
                "🏆 *Beim Sportwagen-Hauptgewinn bitte ein Ticket erstellen!*"
            ),
            color=0x87CEEB,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name="🎰 Cryptik Roleplay Casino",
            icon_url=bot.user.display_avatar.url,
        )
        embed.set_footer(text="Cryptik Roleplay — Casino • Viel Glück! 🍀")
        try:
            await channel.send(embed=embed, view=CasinoView())
            print(f"Casino-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_casino_setup fehlgeschlagen", str(e), guild)
