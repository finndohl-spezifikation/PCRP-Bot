# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# bot_status.py — Automatisches Bot-Status Dashboard
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from __future__ import annotations
import discord
from typing import Optional
from config import bot, BOT_LOG_CHANNEL_ID, FEATURES
from datetime import datetime, timezone

_status = {name: (True, "") for name in FEATURES}
_status_message: Optional[discord.Message] = None


def _build_status_embed() -> discord.Embed:
    all_ok = all(ok for ok, _ in _status.values())
    color  = 0x00FF00 if all_ok else 0xFF0000

    lines = []
    for feature, (ok, err) in _status.items():
        indicator = "🟢" if ok else "🔴"
        line = f"{indicator} **{feature}**"
        if not ok and err:
            line += f"\n　　↳ *{err[:80]}*"
        lines.append(line)

    status_text = "**✅ Alle Systeme Online**" if all_ok else "**⚠️ Einige Systeme haben Fehler**"

    embed = discord.Embed(
        title="📊 Bot-Status Übersicht",
        description=status_text + "\n\n" + "\n".join(lines),
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay — Status System | Letzte Aktualisierung")
    return embed


async def _update_status_message():
    global _status_message
    if _status_message is None:
        return
    try:
        await _status_message.edit(embed=_build_status_embed())
    except Exception:
        _status_message = None


async def feature_error(name: str, error: str):
    if name in _status:
        _status[name] = (False, error)
        await _update_status_message()


async def feature_ok(name: str):
    if name in _status:
        _status[name] = (True, "")
        await _update_status_message()


async def auto_bot_status_setup():
    global _status_message
    for guild in bot.guilds:
        channel = guild.get_channel(BOT_LOG_CHANNEL_ID)
        if not channel:
            continue

        existing = None
        try:
            async for msg in channel.history(limit=30):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Bot-Status" in emb.title:
                            existing = msg
                            break
                if existing:
                    break
        except Exception:
            pass

        embed = _build_status_embed()
        try:
            if existing:
                await existing.edit(embed=embed)
                _status_message = existing
                print("[bot_status] ✅ Status-Embed aktualisiert")
            else:
                _status_message = await channel.send(embed=embed)
                print("[bot_status] ✅ Status-Embed gepostet")
        except Exception as e:
            print(f"[bot_status] ❌ Fehler: {e}")
        break


@bot.listen("on_ready")
async def bot_status_on_ready():
    await auto_bot_status_setup()
