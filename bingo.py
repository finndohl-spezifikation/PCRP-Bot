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
BINGO_CALL_INTERVAL = 20           # Sekunden zwischen zwei Zahlen
BINGO_MIN           = 1
BINGO_MAX           = 75           # Zahlenpool 1–75
BINGO_SIZE          = 4            # 4×4 Karte = 16 Felder

_game: dict | None = None          # Globaler Spielstand (ein Spiel gleichzeitig)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _make_card() -> list[list[int]]:
    pool = random.sample(range(BINGO_MIN, BINGO_MAX + 1), BINGO_SIZE * BINGO_SIZE)
    return [pool[i * BINGO_SIZE:(i + 1) * BINGO_SIZE] for i in range(BINGO_SIZE)]


def _has_bingo(marked: list[list[bool]]) -> bool:
    s = BINGO_SIZE
    for r in range(s):
        if all(marked[r][c] for c in range(s)):
            return True
    for c in range(s):
        if all(marked[r][c] for r in range(s)):
            return True
    if all(marked[i][i] for i in range(s)):
        return True
    if all(marked[i][s - 1 - i] for i in range(s)):
        return True
    return False


def _marked_count(marked: list[list[bool]]) -> int:
    return sum(marked[r][c] for r in range(BINGO_SIZE) for c in range(BINGO_SIZE))


def _build_embed(pdata: dict) -> discord.Embed:
    prize      = _game["prize"]   if _game else "—"
    called_lst = _game["called"]  if _game else []

    rows = []
    for r in range(BINGO_SIZE):
        parts = []
        for c in range(BINGO_SIZE):
            n = pdata["card"][r][c]
            if pdata["marked"][r][c]:
                parts.append(f"✓{n:02d}")
            else:
                parts.append(f"○{n:02d}")
        rows.append("  ".join(parts))
    grid = "```\n" + "\n".join(rows) + "\n```"

    embed = discord.Embed(
        title="🎱 Dein Bingo-Feld",
        description=grid,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(
        name="🔢 Letzte Zahl",
        value=f"**{called_lst[-1]}**" if called_lst else "—",
        inline=True,
    )
    embed.add_field(name="🏆 Gewinn", value=prize, inline=True)
    embed.add_field(
        name=f"📋 Zahlen ({len(called_lst)})",
        value=(" · ".join(str(x) for x in called_lst) or "—")[:1024],
        inline=False,
    )
    embed.set_footer(text="✓ = aufgerufen  ○ = ausstehend")
    return embed


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

    for number in pool:
        if not _game or _game.get("ended"):
            break

        await asyncio.sleep(BINGO_CALL_INTERVAL)

        if not _game or _game.get("ended"):
            break

        _game["called"].append(number)
        _game["called_set"].add(number)

        # Zahl bei allen Spielern automatisch markieren
        bingo_uids: list[int] = []
        for uid, pdata in list(_game["players"].items()):
            for r in range(BINGO_SIZE):
                for c in range(BINGO_SIZE):
                    if pdata["card"][r][c] == number:
                        pdata["marked"][r][c] = True
            if _has_bingo(pdata["marked"]):
                bingo_uids.append(uid)

        # Alle DM-Karten aktualisieren
        for uid, pdata in list(_game["players"].items()):
            msg = _game["messages"].get(uid)
            if not msg:
                continue
            try:
                await msg.edit(embed=_build_embed(pdata))
            except Exception:
                pass

        # Bingo sofort auswerten
        if bingo_uids:
            winner_uid = random.choice(bingo_uids)
            guild  = bot.get_guild(GUILD_ID)
            member = guild.get_member(winner_uid) if guild else None
            if member:
                await _declare_winner(member)
            return

    # Alle Zahlen aufgerufen — Spieler mit den meisten Markierungen gewinnt
    if _game and not _game.get("ended"):
        best_uid = max(
            _game["players"],
            key=lambda uid: _marked_count(_game["players"][uid]["marked"])
        )
        guild  = bot.get_guild(GUILD_ID)
        member = guild.get_member(best_uid) if guild else None
        if member:
            await _declare_winner(member)
        else:
            _game["ended"] = True


# ── /bingo Command ────────────────────────────────────────────────────────────

@bot.tree.command(
    name="bingo",
    description="[Admin/Mod] Startet das wöchentliche Bingo-Spiel",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.default_permissions(manage_messages=True)
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
            f"Der Bot ruft alle **20 Sekunden** eine neue Zahl auf — "
            f"aufgerufene Zahlen werden auf deiner Karte automatisch markiert!\n\n"
            f"**Wer zuerst eine vollständige Reihe, Spalte oder Diagonale hat, gewinnt! 🎉**"
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
        "players":    {},
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
        card   = _make_card()
        pdata  = {"card": card, "marked": [[False] * BINGO_SIZE for _ in range(BINGO_SIZE)]}
        _game["players"][user.id] = pdata
        try:
            dm_msg = await user.send(
                content=(
                    f"🎱 **Dein Bingo-Feld ist da!**\n"
                    f"Gewinn: **{gewinn}**\n\n"
                    f"Aufgerufene Zahlen werden **automatisch** auf deiner Karte markiert.\n"
                    f"Wer zuerst eine vollständige **Reihe, Spalte oder Diagonale** hat, gewinnt!"
                ),
                embed=_build_embed(pdata),
            )
            _game["messages"][user.id] = dm_msg
        except discord.Forbidden:
            dm_failed.append(user.display_name)
            _game["players"].pop(user.id, None)

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
        "Erste Zahl in **20 Sekunden**... 🎱"
    )

    task = bot.loop.create_task(_call_loop())
    _game["task"] = task
