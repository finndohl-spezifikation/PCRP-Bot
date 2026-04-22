# -*- coding: utf-8 -*-
# nebenserver.py \\u2014 Nebenserver Embed (\\U0001F30D Import / Export \\U0001F30D)
# Paradise City Roleplay Discord Bot

from config import *

NEBENSERVER_CHANNEL_ID = 1490890378579017778
NEBENSERVER_MSG_FILE   = DATA_DIR / "nebenserver_msg.json"
NEBENSERVER_INVITE     = "https://discord.gg/tYTmu8K7hK"


def _load_data() -> dict:
    if NEBENSERVER_MSG_FILE.exists():
        with open(NEBENSERVER_MSG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message_id": None}


def _save_data(data: dict):
    with open(NEBENSERVER_MSG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\\U0001F30D Import / Export \\U0001F30D",
        description="Hier kannst du den Nebenserver **Import / Export** betreten.",
        color=LOG_COLOR,
    )
    embed.set_footer(text="Paradise City Roleplay \\u2022 Nebenserver")
    return embed


def _build_view() -> discord.ui.View:
    view = discord.ui.View(timeout=INTERACTION_VIEW_TIMEOUT)
    view.add_item(discord.ui.Button(
        label="\\U0001F30D Server beitreten",
        url=NEBENSERVER_INVITE,
        style=discord.ButtonStyle.link
    ))
    return view


async def auto_nebenserver_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(NEBENSERVER_CHANNEL_ID)
        if not channel:
            continue

        data = _load_data()

        if data.get("message_id"):
            try:
                msg = await channel.fetch_message(data["message_id"])
                await msg.edit(embed=_build_embed(), view=_build_view())
                print(f"[nebenserver] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        try:
            new_msg = await channel.send(embed=_build_embed(), view=_build_view())
            data["message_id"] = new_msg.id
            _save_data(data)
            print(f"[nebenserver] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[nebenserver] Fehler: {e}")
