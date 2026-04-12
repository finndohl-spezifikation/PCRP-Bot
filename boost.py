# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# boost.py — Boost Belohnungen Embed
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *

BOOST_CHANNEL_ID = 1491622819824402583
BOOST_COLOR      = 0xB44FE8
BOOST_MSG_FILE   = DATA_DIR / "boost_msg.json"
BOOST_BANNER_URL = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/boost_banner.png"


def _load_boost_data() -> dict:
    if BOOST_MSG_FILE.exists():
        with open(BOOST_MSG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message_id": None}


def _save_boost_data(data: dict):
    with open(BOOST_MSG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _build_boost_embed() -> discord.Embed:
    embed = discord.Embed(
        title="💎 Boost Belohnungen",
        description=(
            "**Pro Boost 5.000 $**\n\n"
            "**Ab 5 Boosts 1 Sportwagen deiner Wahl dazu**"
        ),
        color=BOOST_COLOR,
    )
    embed.set_image(url=BOOST_BANNER_URL)
    embed.set_footer(text="Paradise City Roleplay — Server Boosts")
    return embed


async def auto_boost_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(BOOST_CHANNEL_ID)
        if not channel:
            continue

        data = _load_boost_data()

        # Bestehende Nachricht bearbeiten
        if data.get("message_id"):
            try:
                msg = await channel.fetch_message(data["message_id"])
                await msg.edit(embed=_build_boost_embed(), view=discord.ui.View())
                print(f"[boost] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        # Neu senden
        try:
            new_msg = await channel.send(embed=_build_boost_embed(), view=discord.ui.View())
            data["message_id"] = new_msg.id
            _save_boost_data(data)
            print(f"[boost] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[boost] Fehler: {e}")
