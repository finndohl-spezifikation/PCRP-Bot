# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# bingo.py \u2014 W\xf6chentliches Bingo-System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from __future__ import annotations
import asyncio
import random
from datetime import datetime, timezone

from config import *

BINGO_CHANNEL_ID    = 1490882562015498362
BINGO_ROLE_ID       = 1490855737130221598
BINGO_JOIN_SECONDS  = 300          # 5 Minuten Beitrittszeit
BINGO_CALL_INTERVAL = 20           # Sekunden zwischen zwei Zahlen
BINGO_GRACE_SECONDS = 60           # Schonfrist nach letzter Zahl
BINGO_MIN           = 1
BINGO_MAX           = 75           # Zahlenpool 1\u201375
BINGO_SIZE          = 4            # 4\xd74 Karte = 16 Felder

_game: dict | None = None          # Globaler Spielstand (ein Spiel gleichzeitig)


# \u2500\u2500 Hilfsfunktionen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _make_card() -> list[list[int]]:
    pool = random.sample(range(BINGO_MIN, BINGO_MAX + 1), BINGO_SIZE * BINGO_SIZE)
    return [pool[i * BINGO_SIZE:(i + 1) * BINGO_SIZE] for i in range(BINGO_SIZE)]


def _card_embed(view: BingoCardView) -> discord.Embed:
    called_set = _game["called_set"] if _game else set()
    prize      = _game["prize"]      if _game else "\u2014"
    called_lst = _game["called"]     if _game else []
    last       = called_lst[-1]      if called_lst else None

    rows = []
    for r in range(BINGO_SIZE):
        parts = []
        for c in range(BINGO_SIZE):
            n = view.card[r][c]
            if view.marked[r][c]:
                parts.append(f"\u2713{n:02d}")
            elif n in called_set:
                parts.append(f"\u25cf{n:02d}")
            else:
                parts.append(f"\u25cb{n:02d}")
        rows.append("  ".join(parts))
    grid = "```\\n" + "\\n".join(rows) + "\\n```"

    embed = discord.Embed(
        title="\U0001f3b1 Dein Bingo-Feld",
        description=grid,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(
        name="\U0001f522 Letzte Zahl",
        value=f"**{last}**" if last else "\u2014",
        inline=True,
    )
    embed.add_field(name="\U0001f3c6 Gewinn", value=prize, inline=True)
    embed.add_field(
        name=f"\U0001f4cb Zahlen ({len(called_lst)})",
        value=(" \xb7 ".join(str(x) for x in called_lst) or "\u2014")[:1024],
        inline=False,
    )
    embed.set_footer(text="\u2713 = markiert  \u25cf  = aufgerufen, noch nicht markiert  \u25cb = ausstehend")
    return embed


# \u2500\u2500 View & Buttons \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class BingoCardView(TimedDisableView):
    def __init__(self, user_id: int, card: list[list[int]]):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.user_id = user_id
        self.card    = card
        self.marked  = [[False] * BINGO_SIZE for _ in range(BINGO_SIZE)]
        self._rebuild()

    def _rebuild(self):
        self.clear_items()
        called_set = _game["called_set"] if _game else set()
        for r in range(BINGO_SIZE):
            for c in range(BINGO_SIZE):
                n      = self.card[r][c]
                marked = self.marked[r][c]
                called = n in called_set
                if marked:
                    style, label, disabled = discord.ButtonStyle.success, f"\u2713{n}", True
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

    def has_bingo(self) -> bool:
        m = self.marked
        s = BINGO_SIZE
        for r in range(s):
            if all(m[r][c] for c in range(s)):
                return True
        for c in range(s):
            if all(m[r][c] for r in range(s)):
                return True
        if all(m[i][i] for i in range(s)):
            return True
        if all(m[i][s - 1 - i] for i in range(s)):
            return True
        return False

    def marked_count(self) -> int:
        return sum(self.marked[r][c] for r in range(BINGO_SIZE) for c in range(BINGO_SIZE))


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
                "\u274c Das ist nicht deine Karte!", ephemeral=True
            )
            return

        if not _game or _game.get("ended"):
            await interaction.response.send_message(
                "\u274c Kein aktives Bingo-Spiel.", ephemeral=True
            )
            return

        if self._n not in _game["called_set"]:
            await interaction.response.send_message(
                f"\u274c Die Zahl **{self._n}** wurde noch nicht aufgerufen!", ephemeral=True
            )
            return

        if self._vref.marked[self._r][self._c]:
            await interaction.response.send_message("\u2705 Bereits markiert!", ephemeral=True)
            return

        self._vref.marked[self._r][self._c] = True
        self._vref.rebuild()
        await interaction.response.edit_message(
            embed=_card_embed(self._vref), view=self._vref
        )

        if self._vref.has_bingo():
            await _declare_winner(interaction.user)


# \u2500\u2500 Gewinn-Handling \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _declare_winner(user: discord.User | discord.Member):
    global _game
    if not _game or _game.get("ended"):
        return
    _game["ended"] = True

    prize   = _game["prize"]
    channel = bot.get_channel(BINGO_CHANNEL_ID)

    if channel:
        embed = discord.Embed(
            title="\U0001f389 BINGO! Wir haben einen Gewinner!",
            description=(
                f"\U0001f3c6 **{user.display_name}** hat das w\xf6chentliche Bingo gewonnen!\\n\\n"
                f"**Gewinn:** {prize}\\n\\n"
                f"Herzlichen Gl\xfcckwunsch! \U0001f38a"
            ),
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        await channel.send(embed=embed)

    try:
        dm = discord.Embed(
            title="\U0001f389 Gl\xfcckwunsch \u2014 Du hast gewonnen!",
            description=(
                f"Du hast das w\xf6chentliche **Bingo** gewonnen! \U0001f38a\\n\\n"
                f"**Gewinn:** {prize}\\n\\n"
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


# \u2500\u2500 Zahlen-Aufruf-Loop \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _call_loop():
    global _game
    pool = list(range(BINGO_MIN, BINGO_MAX + 1))
    random.shuffle(pool)

    for number in pool:
        if not _game or _game.get("ended"):
            return

        await asyncio.sleep(BINGO_CALL_INTERVAL)

        if not _game or _game.get("ended"):
            return

        _game["called"].append(number)
        _game["called_set"].add(number)

        for uid, view in list(_game["views"].items()):
            msg = _game["messages"].get(uid)
            if not msg:
                continue
            view.rebuild()
            try:
                await msg.edit(embed=_card_embed(view), view=view)
            except Exception:
                pass

        if _game.get("ended"):
            return

    # Alle Zahlen aufgerufen \u2014 60 Sekunden Schonfrist f\xfcr letzte Klicks
    if not _game or _game.get("ended"):
        return

    channel = bot.get_channel(BINGO_CHANNEL_ID)
    if channel:
        await channel.send(
            f"\U0001f3b1 Alle Zahlen wurden aufgerufen!\\n"
            f"Ihr habt noch **{BINGO_GRACE_SECONDS} Sekunden** um eure letzten Felder anzuklicken!"
        )

    await asyncio.sleep(BINGO_GRACE_SECONDS)

    if not _game or _game.get("ended"):
        return

    # Erst pr\xfcfen ob jemand Bingo hat (Klicks w\xe4hrend Schonfrist)
    bingo_uids = [
        uid for uid, view in _game["views"].items() if view.has_bingo()
    ]
    if bingo_uids:
        winner_uid = random.choice(bingo_uids)
        guild  = bot.get_guild(GUILD_ID)
        member = guild.get_member(winner_uid) if guild else None
        if member:
            await _declare_winner(member)
            return

    # Kein Bingo \u2014 Spieler mit den meisten markierten Feldern gewinnt
    if _game["views"]:
        best_uid = max(_game["views"], key=lambda uid: _game["views"][uid].marked_count())
        guild  = bot.get_guild(GUILD_ID)
        member = guild.get_member(best_uid) if guild else None
        if member:
            await _declare_winner(member)
            return

    if _game:
        _game["ended"] = True


# \u2500\u2500 /bingo Command \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="bingo",
    description="[Admin/Mod] Startet das w\xf6chentliche Bingo-Spiel",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(gewinn="Was gewinnt der Sieger? z.B. '50.000 $' oder 'VIP-Status'")
async def bingo_start(interaction: discord.Interaction, gewinn: str):
    global _game

    role_ids = [r.id for r in interaction.user.roles]
    if ADMIN_ROLE_ID not in role_ids and MOD_ROLE_ID not in role_ids:
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    if _game and not _game.get("ended"):
        await interaction.response.send_message(
            "\u274c Es l\xe4uft bereits ein Bingo-Spiel!", ephemeral=True
        )
        return

    await interaction.response.send_message(
        "\u2705 Bingo-Ank\xfcndigung wird gesendet...", ephemeral=True
    )

    channel = bot.get_channel(BINGO_CHANNEL_ID)
    if not channel:
        await interaction.followup.send("\u274c Bingo-Kanal nicht gefunden.", ephemeral=True)
        return

    embed = discord.Embed(
        title="\U0001f3b1 Das w\xf6chentliche Bingo hat begonnen!",
        description=(
            f"Reagiere mit \u2705 um mitzuspielen!\\n\\n"
            f"**\U0001f3c6 Gewinn:** {gewinn}\\n\\n"
            f"\u23f3 Eintragungszeit: **5 Minuten**\\n"
            f"Danach erh\xe4ltst du dein pers\xf6nliches Bingo-Feld per DM.\\n"
            f"Der Bot ruft alle **20 Sekunden** eine neue Zahl auf \u2014 "
            f"klicke sie auf deiner Karte an um sie zu markieren!\\n\\n"
            f"**Wer zuerst eine vollst\xe4ndige Reihe, Spalte oder Diagonale hat, gewinnt! \U0001f389**"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=f"Gestartet von {interaction.user.display_name}")

    announce_msg = await channel.send(
        content=f"<@&{BINGO_ROLE_ID}>",
        embed=embed,
    )
    await announce_msg.add_reaction("\u2705")

    _game = {
        "prize":      gewinn,
        "called":     [],
        "called_set": set(),
        "views":      {},
        "messages":   {},
        "ended":      False,
        "task":       None,
    }

    # \u2500\u2500 5 Minuten Beitrittszeit \u2500\u2500
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
        if str(reaction.emoji) == "\u2705":
            async for u in reaction.users():
                if not u.bot:
                    participants.append(u)
            break

    if not participants:
        await channel.send("\U0001f614 Niemand hat sich f\xfcr das Bingo eingetragen. Runde abgebrochen.")
        _game["ended"] = True
        return

    await channel.send(
        f"\U0001f3b1 **{len(participants)} Spieler** nehmen teil! "
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
                    f"\U0001f3b1 **Dein Bingo-Feld ist da!**\\n"
                    f"Gewinn: **{gewinn}**\\n\\n"
                    f"Sobald eine Zahl aufgerufen wird leuchtet sie **blau** auf \u2014 "
                    f"klicke sie um sie zu markieren!\\n"
                    f"Wer zuerst eine vollst\xe4ndige **Reihe, Spalte oder Diagonale** hat, gewinnt!"
                ),
                embed=_card_embed(view),
                view=view,
            )
            _game["messages"][user.id] = dm_msg
        except discord.Forbidden:
            dm_failed.append(user.display_name)

    if dm_failed:
        await channel.send(
            f"\u26a0\ufe0f Konnte keine DM senden an: {', '.join(dm_failed)} (DMs deaktiviert)"
        )

    if not _game["messages"]:
        await channel.send("\u274c Keine DMs konnten verschickt werden. Bingo abgebrochen.")
        _game["ended"] = True
        return

    await channel.send(
        "\u2705 Alle Felder verschickt \u2014 das Spiel beginnt jetzt! "
        "Erste Zahl in **20 Sekunden**... \U0001f3b1"
    )

    task = bot.loop.create_task(_call_loop())
    _game["task"] = task
