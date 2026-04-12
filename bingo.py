# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# bingo.py — Wöchentliches Bingo-System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from __future__ import annotations
import asyncio
import random
from datetime import datetime, timezone

from config import *

BINGO_CHANNEL_ID    = 1490882562015498362
BINGO_ROLE_ID       = 1490855737130221598
BINGO_JOIN_SECONDS  = 300          # 5 Minuten Beitrittszeit
BINGO_CALL_INTERVAL = 30           # Sekunden zwischen zwei Zahlen
BINGO_MIN           = 1
BINGO_MAX           = 50           # Zahlenpool 1–50
BINGO_SIZE          = 5            # 5×5 Karte = 25 Felder

_game: dict | None = None          # Globaler Spielstand (ein Spiel gleichzeitig)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _make_card() -> list[list[int]]:
    pool = random.sample(range(BINGO_MIN, BINGO_MAX + 1), BINGO_SIZE * BINGO_SIZE)
    return [pool[i * BINGO_SIZE:(i + 1) * BINGO_SIZE] for i in range(BINGO_SIZE)]


def _card_embed(view: BingoCardView) -> discord.Embed:
    called_set = _game["called_set"] if _game else set()
    prize      = _game["prize"]      if _game else "—"
    called_lst = _game["called"]     if _game else []
    last       = called_lst[-1]      if called_lst else None

    lines = []
    for r in range(BINGO_SIZE):
        parts = []
        for c in range(BINGO_SIZE):
            n = view.card[r][c]
            if view.marked[r][c]:
                parts.append(f"**✓{n:02d}**")
            elif n in called_set:
                parts.append(f"__{n:02d}__")
            else:
                parts.append(f"`{n:02d}`")
        lines.append("  ".join(parts))

    called_str = " · ".join(str(x) for x in called_lst) if called_lst else "—"

    embed = discord.Embed(
        title="🎱 Dein Bingo-Feld",
        description="\n".join(lines),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(
        name="🔢 Letzte Zahl",
        value=f"**{last}**" if last else "—",
        inline=True,
    )
    embed.add_field(name="🏆 Gewinn", value=prize, inline=True)
    embed.add_field(
        name=f"📋 Aufgerufene Zahlen ({len(called_lst)})",
        value=called_str if len(called_str) <= 1024 else called_str[-1020:],
        inline=False,
    )
    embed.set_footer(
        text="✓xx = markiert  |  __xx__ = aufgerufen, noch nicht markiert  |  `xx` = noch nicht aufgerufen"
    )
    return embed


# ── View & Buttons ────────────────────────────────────────────────────────────

class BingoCardView(discord.ui.View):
    def __init__(self, user_id: int, card: list[list[int]]):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.card    = card
        self.marked  = [[False] * BINGO_SIZE for _ in range(BINGO_SIZE)]
        self._rebuild()

    def _rebuild(self):
        self.clear_items()
        called_set = _game["called_set"] if _game else set()
        for r in range(BINGO_SIZE):
            for c in range(BINGO_SIZE):
                n       = self.card[r][c]
                marked  = self.marked[r][c]
                called  = n in called_set
                if marked:
                    style, label, disabled = discord.ButtonStyle.success, f"✓{n}", True
                elif called:
                    style, label, disabled = discord.ButtonStyle.primary, str(n), False
                else:
                    style, label, disabled = discord.ButtonStyle.secondary, str(n), True
                self.add_item(
                    BingoButton(
                        row_idx=r, col_idx=c, number=n, view_ref=self,
                        style=style, label=label, disabled=disabled,
                    )
                )

    def rebuild(self):
        self._rebuild()

    def is_full(self) -> bool:
        return all(self.marked[r][c] for r in range(BINGO_SIZE) for c in range(BINGO_SIZE))


class BingoButton(discord.ui.Button):
    def __init__(self, row_idx: int, col_idx: int, number: int,
                 view_ref: BingoCardView, **kwargs):
        super().__init__(row=row_idx, **kwargs)
        self._r    = row_idx
        self._c    = col_idx
        self._n    = number
        self._vref = view_ref

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self._vref.user_id:
            await interaction.response.send_message(
                "❌ Das ist nicht deine Karte!", ephemeral=True
            )
            return

        if not _game or _game.get("ended"):
            await interaction.response.send_message(
                "❌ Kein aktives Bingo-Spiel.", ephemeral=True
            )
            return

        if self._n not in _game["called_set"]:
            await interaction.response.send_message(
                f"❌ Die Zahl **{self._n}** wurde noch nicht aufgerufen!", ephemeral=True
            )
            return

        if self._vref.marked[self._r][self._c]:
            await interaction.response.send_message("✅ Bereits markiert!", ephemeral=True)
            return

        self._vref.marked[self._r][self._c] = True
        self._vref.rebuild()
        await interaction.response.edit_message(embed=_card_embed(self._vref), view=self._vref)

        if self._vref.is_full():
            await _declare_winner(interaction.user)


# ── Gewinn-Handling ───────────────────────────────────────────────────────────

async def _declare_winner(user: discord.User | discord.Member):
    global _game
    if not _game or _game.get("ended"):
        return
    _game["ended"] = True

    prize   = _game["prize"]
    channel = bot.get_channel(BINGO_CHANNEL_ID)

    if channel:
        embed = discord.Embed(
            title="🎉 BINGO! Wir haben einen Gewinner!",
            description=(
                f"🏆 **{user.display_name}** hat das wöchentliche Bingo gewonnen!\n\n"
                f"**Gewinn:** {prize}\n\n"
                f"Herzlichen Glückwunsch! 🎊"
            ),
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        await channel.send(embed=embed)

    try:
        dm = discord.Embed(
            title="🎉 Glückwunsch — Du hast gewonnen!",
            description=(
                f"Du hast das wöchentliche **Bingo** gewonnen! 🎊\n\n"
                f"**Gewinn:** {prize}\n\n"
                f"Melde dich beim Team um deinen Gewinn abzuholen!"
            ),
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        await user.send(embed=dm)
    except discord.Forbidden:
        pass

    if _game.get("task") and not _game["task"].done():
        _game["task"].cancel()


# ── Zahlen-Aufruf-Loop ────────────────────────────────────────────────────────

async def _call_loop():
    global _game
    pool = list(range(BINGO_MIN, BINGO_MAX + 1))
    random.shuffle(pool)
    channel = bot.get_channel(BINGO_CHANNEL_ID)

    for number in pool:
        if not _game or _game.get("ended"):
            break

        await asyncio.sleep(BINGO_CALL_INTERVAL)

        if not _game or _game.get("ended"):
            break

        _game["called"].append(number)
        _game["called_set"].add(number)

        total = BINGO_MAX - BINGO_MIN + 1
        if channel:
            await channel.send(
                f"🎱 **Neue Bingo-Zahl: {number}**  ·  "
                f"{len(_game['called'])}/{total} Zahlen aufgerufen"
            )

        for uid, view in list(_game["views"].items()):
            msg = _game["messages"].get(uid)
            if not msg:
                continue
            view.rebuild()
            try:
                await msg.edit(embed=_card_embed(view), view=view)
            except Exception:
                pass

    if _game and not _game.get("ended"):
        _game["ended"] = True
        if channel:
            await channel.send(
                "😔 Alle Zahlen wurden aufgerufen — kein Gewinner in dieser Runde."
            )


# ── /bingo Command ────────────────────────────────────────────────────────────

@bot.tree.command(
    name="bingo",
    description="[Admin/Mod] Startet das wöchentliche Bingo-Spiel",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(gewinn="Was gewinnt der Sieger? z.B. '50.000 $' oder 'VIP-Status'")
async def bingo_start(interaction: discord.Interaction, gewinn: str):
    global _game

    role_ids = [r.id for r in interaction.user.roles]
    if ADMIN_ROLE_ID not in role_ids and MOD_ROLE_ID not in role_ids:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    if _game and not _game.get("ended"):
        await interaction.response.send_message(
            "❌ Es läuft bereits ein Bingo-Spiel!", ephemeral=True
        )
        return

    await interaction.response.send_message(
        "✅ Bingo-Ankündigung wird gesendet...", ephemeral=True
    )

    channel = bot.get_channel(BINGO_CHANNEL_ID)
    if not channel:
        await interaction.followup.send("❌ Bingo-Kanal nicht gefunden.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎱 Das wöchentliche Bingo hat begonnen!",
        description=(
            f"Reagiere mit ✅ um mitzuspielen!\n\n"
            f"**🏆 Gewinn:** {gewinn}\n\n"
            f"⏳ Eintragungszeit: **5 Minuten**\n"
            f"Danach erhältst du dein persönliches Bingo-Feld per DM.\n"
            f"Der Bot ruft dann alle 30 Sekunden eine neue Zahl aus — "
            f"markiere sie auf deiner Karte!\n\n"
            f"**Wer zuerst alle Felder füllt gewinnt! 🎉**"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=f"Gestartet von {interaction.user.display_name}")

    announce_msg = await channel.send(
        content=f"<@&{BINGO_ROLE_ID}>",
        embed=embed,
    )
    await announce_msg.add_reaction("✅")

    _game = {
        "prize":      gewinn,
        "called":     [],
        "called_set": set(),
        "views":      {},
        "messages":   {},
        "ended":      False,
        "task":       None,
    }

    # ── 5 Minuten Beitrittszeit ──
    await asyncio.sleep(BINGO_JOIN_SECONDS)

    if _game.get("ended"):
        return

    # Reaktionen auslesen
    try:
        announce_msg = await channel.fetch_message(announce_msg.id)
    except Exception:
        _game["ended"] = True
        return

    participants: list[discord.User] = []
    for reaction in announce_msg.reactions:
        if str(reaction.emoji) == "✅":
            async for u in reaction.users():
                if not u.bot:
                    participants.append(u)
            break

    if not participants:
        await channel.send("😔 Niemand hat sich für das Bingo eingetragen. Runde abgebrochen.")
        _game["ended"] = True
        return

    await channel.send(
        f"🎱 **{len(participants)} Spieler** nehmen teil! "
        f"Bingo-Felder werden jetzt per DM versendet..."
    )

    # Karten per DM versenden
    dm_failed: list[str] = []
    for user in participants:
        card = _make_card()
        view = BingoCardView(user_id=user.id, card=card)
        _game["views"][user.id] = view
        try:
            dm_msg = await user.send(
                content=(
                    f"🎱 **Dein Bingo-Feld ist da!**\n"
                    f"Gewinn: **{gewinn}**\n\n"
                    f"Sobald eine Zahl aufgerufen wird erscheint sie **blau** — drücke sie um sie zu markieren!"
                ),
                embed=_card_embed(view),
                view=view,
            )
            _game["messages"][user.id] = dm_msg
        except discord.Forbidden:
            dm_failed.append(user.display_name)

    if dm_failed:
        await channel.send(
            f"⚠️ Konnte keine DM senden an: {', '.join(dm_failed)} (DMs deaktiviert)"
        )

    if not _game["messages"]:
        await channel.send("❌ Keine DMs konnten verschickt werden. Bingo abgebrochen.")
        _game["ended"] = True
        return

    await channel.send(
        "✅ Alle Felder verschickt — das Spiel beginnt jetzt! "
        "Erste Zahl in **30 Sekunden**... 🎱"
    )

    task = bot.loop.create_task(_call_loop())
    _game["task"] = task
