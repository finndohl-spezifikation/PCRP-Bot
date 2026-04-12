# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# lotto.py — Lotto-System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from economy_helpers import load_economy, save_economy, get_user, normalize_item_name

LOTTO_CHANNEL_ID    = 1492636063817138216
LOTTO_MSG_FILE      = DATA_DIR / "lotto_msg.json"
LOTTO_TICKETS_FILE  = DATA_DIR / "lotto_tickets.json"
LOTTO_ITEM_NAME     = "🎟| Lottoschein"
LOTTO_VIP_ROLE_ID   = 1490855646558556282

# Gewinn-Preise je Anzahl richtiger Zahlen
LOTTO_PRIZES = {
    1: 50_000,
    2: 100_000,
    3: 200_000,
    4: 400_000,
    5: 800_000,
    6: 1_000_000,
}
LOTTO_SUPERZAHL_PRIZE = 3_000_000

# Gewinn-Wahrscheinlichkeiten
WIN_CHANCE_NORMAL = 0.06   # 6 %  — normale Spieler
WIN_CHANCE_VIP    = 0.20   # 20 % — VIP-Spieler
SUPER_CHANCE_NORMAL = 0.001  # 0.1 %
SUPER_CHANCE_VIP    = 0.004  # 0.4 %

# Verteilung der Gewinn-Tiers (1–6 Richtige), wenn Sieg-Roll bestanden
WIN_TIER_WEIGHTS = [50, 25, 13, 7, 3, 2]   # gewichtet für 1,2,3,4,5,6 Richtige

LOTTO_MAX_WEEKLY_WINNERS = 5  # Maximal 5 Gewinner pro Kalenderwoche


def _week_key(dt: datetime | None = None) -> str:
    """ISO-Kalenderwoche als String, z.B. '2025-W03'"""
    d = dt or datetime.now(timezone.utc)
    return f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"


# ── Datei-Helfer ──────────────────────────────────────────────

def _load_lotto_msg() -> dict:
    if LOTTO_MSG_FILE.exists():
        with open(LOTTO_MSG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message_id": None}


def _save_lotto_msg(data: dict):
    with open(LOTTO_MSG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _load_tickets() -> dict:
    if LOTTO_TICKETS_FILE.exists():
        with open(LOTTO_TICKETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tickets": [], "last_draw": None, "weekly_winners": {}}


def _save_tickets(data: dict):
    with open(LOTTO_TICKETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Gewinn-Logik ──────────────────────────────────────────────

def _evaluate_ticket(numbers: list[int], superzahl: int, is_vip: bool) -> dict:
    """
    Gibt zurück: {"correct": int, "superzahl_win": bool, "prize": int,
                  "drawn_numbers": list, "drawn_super": int}
    correct=0 und superzahl_win=False bedeutet Niete.
    """
    win_chance   = WIN_CHANCE_VIP    if is_vip else WIN_CHANCE_NORMAL
    super_chance = SUPER_CHANCE_VIP  if is_vip else SUPER_CHANCE_NORMAL

    # Superzahl-Ziehung (unabhängig)
    drawn_super    = random.randint(1, 10)
    superzahl_win  = (drawn_super == superzahl) and (random.random() < super_chance)

    # Gewinn-Roll
    correct = 0
    drawn_numbers = []

    if random.random() < win_chance:
        # Tier auswählen (wie viele Richtige)
        tier = random.choices(range(1, 7), weights=WIN_TIER_WEIGHTS, k=1)[0]
        correct = tier

        # Drawn numbers so generieren, dass genau `tier` Zahlen aus den
        # Spieler-Zahlen enthalten sind und der Rest zufällig ist
        correct_picks  = random.sample(numbers, min(tier, len(numbers)))
        remaining_pool = [n for n in range(1, 101) if n not in numbers]
        filler_count   = max(0, 6 - len(correct_picks))
        filler         = random.sample(remaining_pool, min(filler_count, len(remaining_pool)))
        drawn_numbers  = correct_picks + filler
        random.shuffle(drawn_numbers)
    else:
        # Niete — alle Drawn-Nummern aus dem Pool außerhalb Spieler-Zahlen
        pool = [n for n in range(1, 101) if n not in numbers]
        drawn_numbers = sorted(random.sample(pool, min(6, len(pool))))

    prize = 0
    if superzahl_win:
        prize += LOTTO_SUPERZAHL_PRIZE
    if correct > 0:
        prize += LOTTO_PRIZES.get(correct, 0)

    return {
        "correct":       correct,
        "superzahl_win": superzahl_win,
        "prize":         prize,
        "drawn_numbers": sorted(drawn_numbers),
        "drawn_super":   drawn_super,
    }


# ── Embed & View ──────────────────────────────────────────────

def _build_lotto_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎰 Paradise City Lotto",
        description=(
            "**Täglich um 12:00 Uhr werden die Gewinner gezogen!**\n\n"
            "**So funktioniert es:**\n"
            "Wähle **6 Zahlen** (1–100) und eine **Superzahl** (1–10).\n"
            "Du brauchst einen **🎟| Lottoschein** aus dem Shop (2.800 $).\n\n"
            "**Gewinntabelle:**\n"
            "🎯 1 Richtige → **50.000 $**\n"
            "🎯 2 Richtige → **100.000 $**\n"
            "🎯 3 Richtige → **200.000 $**\n"
            "🎯 4 Richtige → **400.000 $**\n"
            "🎯 5 Richtige → **800.000 $**\n"
            "🎯 6 Richtige → **1.000.000 $**\n"
            "⭐ Superzahl  → **3.000.000 $** *(extrem selten!)*\n\n"
            "Du kannst mehrere Scheine pro Tag kaufen & abgeben.\n"
            "⚠️ **Maximal 5 Gewinner pro Woche** — danach keine weiteren Gewinne bis nächste Woche.\n"
            "Gewinner werden per DM benachrichtigt."
        ),
        color=LOG_COLOR,
    )
    embed.set_footer(text="Paradise City Roleplay — Viel Glück!")
    return embed


class LottoModal(discord.ui.Modal, title="🎰 Lotto-Schein ausfüllen"):
    zahlen = discord.ui.TextInput(
        label="Deine 6 Zahlen (1–100, durch Komma getrennt)",
        placeholder="z.B. 7, 13, 42, 55, 78, 91",
        max_length=30,
    )
    superzahl = discord.ui.TextInput(
        label="Superzahl (1–10)",
        placeholder="z.B. 5",
        max_length=2,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Zahlen parsen & validieren
        try:
            parts = [p.strip() for p in self.zahlen.value.split(",") if p.strip()]
            nums  = [int(p) for p in parts]
        except ValueError:
            await interaction.response.send_message(
                "❌ Ungültige Eingabe. Bitte Zahlen durch Komma trennen (z.B. `7, 13, 42, 55, 78, 91`).",
                ephemeral=True
            )
            return

        if len(nums) != 6:
            await interaction.response.send_message(
                f"❌ Du musst genau **6 Zahlen** eingeben (du hast {len(nums)} eingegeben).",
                ephemeral=True
            )
            return
        if len(set(nums)) != 6:
            await interaction.response.send_message(
                "❌ Alle 6 Zahlen müssen **unterschiedlich** sein.",
                ephemeral=True
            )
            return
        if any(n < 1 or n > 100 for n in nums):
            await interaction.response.send_message(
                "❌ Alle Zahlen müssen zwischen **1 und 100** liegen.",
                ephemeral=True
            )
            return

        # Superzahl parsen
        try:
            sz = int(self.superzahl.value.strip())
        except ValueError:
            await interaction.response.send_message(
                "❌ Ungültige Superzahl. Bitte eine Zahl zwischen 1 und 10 eingeben.",
                ephemeral=True
            )
            return
        if sz < 1 or sz > 10:
            await interaction.response.send_message(
                "❌ Die Superzahl muss zwischen **1 und 10** liegen.",
                ephemeral=True
            )
            return

        # Lottoschein aus Inventar entfernen
        eco       = load_economy()
        user_data = get_user(eco, interaction.user.id)
        inv       = user_data.get("inventory", [])

        idx = next(
            (i for i, item in enumerate(inv)
             if normalize_item_name(item) == normalize_item_name(LOTTO_ITEM_NAME)),
            None
        )
        if idx is None:
            await interaction.response.send_message(
                f"❌ Du hast keinen **{LOTTO_ITEM_NAME}** im Inventar!\n"
                "Kaufe einen im Shop mit `/buy`.",
                ephemeral=True
            )
            return

        inv.pop(idx)
        user_data["inventory"] = inv
        save_economy(eco)

        # Ticket speichern
        data   = _load_tickets()
        ticket = {
            "id":           str(uuid.uuid4()),
            "user_id":      interaction.user.id,
            "numbers":      sorted(nums),
            "superzahl":    sz,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "draw_date":    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        data["tickets"].append(ticket)
        _save_tickets(data)

        nums_str = ", ".join(str(n) for n in sorted(nums))
        embed = discord.Embed(
            title="🎰 Lotto-Schein eingereicht!",
            description=(
                f"**Deine Zahlen:** {nums_str}\n"
                f"**Superzahl:** {sz}\n\n"
                "Die Ziehung findet täglich um **12:00 Uhr** statt.\n"
                "Gewinner werden per DM benachrichtigt — Viel Glück! 🍀"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class LottoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Lotto spielen",
        emoji="🎰",
        style=discord.ButtonStyle.primary,
        custom_id="lotto:spielen",
    )
    async def spielen(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LottoModal())


# ── Auto-Setup ────────────────────────────────────────────────

async def auto_lotto_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(LOTTO_CHANNEL_ID)
        if not channel:
            continue

        data  = _load_lotto_msg()
        embed = _build_lotto_embed()

        if data.get("message_id"):
            try:
                msg = await channel.fetch_message(data["message_id"])
                await msg.edit(embed=embed, view=LottoView())
                print(f"[lotto] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        try:
            new_msg = await channel.send(embed=embed, view=LottoView())
            data["message_id"] = new_msg.id
            _save_lotto_msg(data)
            print(f"[lotto] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[lotto] Fehler: {e}")


# ── Tägliche Ziehung ──────────────────────────────────────────

async def _run_draw(guild: discord.Guild):
    data = _load_tickets()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Nur Scheine von heute (oder noch nicht gezogene)
    tickets = [t for t in data["tickets"] if t.get("draw_date") == today]
    if not tickets:
        data["last_draw"] = today
        _save_tickets(data)
        return

    eco = load_economy()

    # Wochenlimit prüfen
    week         = _week_key()
    weekly_won   = data.get("weekly_winners", {}).get(week, 0)

    for ticket in tickets:
        # Wochenlimit erreicht — keine weiteren Gewinner
        if weekly_won >= LOTTO_MAX_WEEKLY_WINNERS:
            break

        member = guild.get_member(ticket["user_id"])
        if member is None:
            try:
                member = await guild.fetch_member(ticket["user_id"])
            except Exception:
                continue

        is_vip = any(r.id == LOTTO_VIP_ROLE_ID for r in member.roles)
        result = _evaluate_ticket(ticket["numbers"], ticket["superzahl"], is_vip)

        if result["prize"] <= 0:
            continue

        # Wochenlimit nochmal prüfen (könnte sich in der Schleife gefüllt haben)
        if weekly_won >= LOTTO_MAX_WEEKLY_WINNERS:
            break

        # Geld gutschreiben
        user_data = get_user(eco, ticket["user_id"])
        user_data["bank"] = user_data.get("bank", 0) + result["prize"]
        weekly_won += 1

        # DM senden
        drawn_str  = ", ".join(str(n) for n in result["drawn_numbers"])
        player_str = ", ".join(str(n) for n in ticket["numbers"])

        desc_parts = [
            f"**Deine Zahlen:** {player_str}",
            f"**Gezogene Zahlen:** {drawn_str}",
            f"**Superzahl:** {ticket['superzahl']} (gezogen: {result['drawn_super']})",
            "",
        ]
        if result["correct"] > 0:
            desc_parts.append(f"🎯 **{result['correct']} Richtige!**")
        if result["superzahl_win"]:
            desc_parts.append("⭐ **Superzahl getroffen!**")
        desc_parts.append(f"\n💰 **Gewinn: {result['prize']:,} $** wurden auf dein Bankkonto überwiesen!")

        dm_embed = discord.Embed(
            title="🎰 Du hast beim Lotto gewonnen!",
            description="\n".join(desc_parts),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        dm_embed.set_footer(text="Paradise City Roleplay — Lotto")
        try:
            await member.send(embed=dm_embed)
        except Exception:
            pass

    save_economy(eco)

    # Wochenzähler speichern
    if "weekly_winners" not in data:
        data["weekly_winners"] = {}
    data["weekly_winners"][week] = weekly_won

    # Gezogene Scheine entfernen, last_draw setzen
    data["tickets"]   = [t for t in data["tickets"] if t.get("draw_date") != today]
    data["last_draw"] = today
    _save_tickets(data)
    print(f"[lotto] Ziehung abgeschlossen für {today} — {len(tickets)} Schein(e), {weekly_won}/{LOTTO_MAX_WEEKLY_WINNERS} Wochengewinner")


async def lotto_draw_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now   = datetime.now(timezone.utc)
        # Deutschland: UTC+1 (Winter) / UTC+2 (Sommer) — 12:00 Uhr = 11:00 UTC (Winter)
        # Wir prüfen auf 11:00 UTC als Näherung (passt für CEST/CET)
        draw_hour_utc = 10  # 12:00 Uhr MEZ (UTC+2 Sommer) = 10 UTC
        data = _load_tickets()
        today = now.strftime("%Y-%m-%d")

        if now.hour == draw_hour_utc and now.minute < 5 and data.get("last_draw") != today:
            for guild in bot.guilds:
                try:
                    await _run_draw(guild)
                except Exception as e:
                    print(f"[lotto] Fehler bei Ziehung: {e}")
            await asyncio.sleep(300)  # 5 Min. Pause nach Ziehung
        else:
            await asyncio.sleep(30)


# ── Test-Command ──────────────────────────────────────────────

@bot.tree.command(
    name="lotto-test",
    description="[Admin] Sofort-Test der Lotto-Ziehung mit eigenen Zahlen",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    zahlen="6 Zahlen (1–100), durch Komma getrennt",
    superzahl="Superzahl (1–10)",
    vip="Als VIP-Spieler testen?",
)
async def lotto_test(
    interaction: discord.Interaction,
    zahlen: str,
    superzahl: int,
    vip: bool = False,
):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    try:
        parts = [p.strip() for p in zahlen.split(",") if p.strip()]
        nums  = [int(p) for p in parts]
    except ValueError:
        await interaction.response.send_message("❌ Ungültige Zahlen.", ephemeral=True)
        return

    if len(nums) != 6 or len(set(nums)) != 6 or any(n < 1 or n > 100 for n in nums):
        await interaction.response.send_message(
            "❌ Bitte genau 6 verschiedene Zahlen zwischen 1 und 100 eingeben.",
            ephemeral=True
        )
        return
    if superzahl < 1 or superzahl > 10:
        await interaction.response.send_message("❌ Superzahl muss zwischen 1 und 10 liegen.", ephemeral=True)
        return

    result = _evaluate_ticket(nums, superzahl, is_vip=vip)

    drawn_str  = ", ".join(str(n) for n in result["drawn_numbers"])
    player_str = ", ".join(str(n) for n in sorted(nums))

    desc_parts = [
        f"**Modus:** {'👑 VIP' if vip else '👤 Normal'}",
        f"**Deine Zahlen:** {player_str}",
        f"**Gezogene Zahlen:** {drawn_str}",
        f"**Superzahl:** {superzahl} (gezogen: {result['drawn_super']})",
        "",
        f"🎯 **Richtige:** {result['correct']}",
        f"⭐ **Superzahl getroffen:** {'Ja' if result['superzahl_win'] else 'Nein'}",
        f"💰 **Gewinn:** {result['prize']:,} $" if result["prize"] > 0 else "❌ **Niete**",
    ]

    embed = discord.Embed(
        title="🎰 Lotto Test-Ziehung",
        description="\n".join(desc_parts),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="lotto-setup",
    description="[Admin] Lotto-Embed manuell im Lotto-Kanal posten/aktualisieren",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
async def lotto_setup(interaction: discord.Interaction):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    channel = interaction.guild.get_channel(LOTTO_CHANNEL_ID)
    if not channel:
        try:
            channel = await interaction.guild.fetch_channel(LOTTO_CHANNEL_ID)
        except Exception:
            await interaction.followup.send(
                f"❌ Kanal `{LOTTO_CHANNEL_ID}` nicht gefunden. Bitte Channel-ID prüfen.",
                ephemeral=True
            )
            return

    data  = _load_lotto_msg()
    embed = _build_lotto_embed()

    if data.get("message_id"):
        try:
            msg = await channel.fetch_message(data["message_id"])
            await msg.edit(embed=embed, view=LottoView())
            await interaction.followup.send("✅ Lotto-Embed wurde aktualisiert!", ephemeral=True)
            return
        except Exception:
            pass

    try:
        new_msg = await channel.send(embed=embed, view=LottoView())
        data["message_id"] = new_msg.id
        _save_lotto_msg(data)
        await interaction.followup.send("✅ Lotto-Embed wurde gepostet!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Fehler beim Senden: `{e}`", ephemeral=True)
