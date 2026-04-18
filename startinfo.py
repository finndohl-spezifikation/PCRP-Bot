# -*- coding: utf-8 -*-
# startinfo.py \u2014 "Wo starte ich?" Embed
# Paradise City Roleplay Discord Bot

from config import *

STARTINFO_CHANNEL_ID = 1490878159032422433
STARTINFO_MSG_FILE   = DATA_DIR / "startinfo_msg.json"
STARTINFO_IMG_URL    = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/startinfo.jpg"


def _load_data() -> dict:
    if STARTINFO_MSG_FILE.exists():
        with open(STARTINFO_MSG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message_id": None}


def _save_data(data: dict):
    with open(STARTINFO_MSG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\U0001f306 Wo starte ich?",
        description=(
            "Willkommen in **Paradise City**! W\u00e4hle deinen Startpunkt je nach Einreiseart.\n"
            "Dein Startfahrzeug findest du in <#1490878159804174470>."
        ),
        color=LOG_COLOR,
    )
    embed.add_field(
        name="\u2708\ufe0f Legale Einreise",
        value=(
            "Du startest am **Flughafen** von Los Santos. "
            "Nimm ein Taxi zum Autohaus und hole dein Startfahrzeug ab."
        ),
        inline=True,
    )
    embed.add_field(
        name="\u2693 Illegale Einreise",
        value=(
            "Du kommst am **Hafen** von Los Santos an. "
            "Begib dich unauff\u00e4llig zum Autohaus, ohne vom LAPD erwischt zu werden."
        ),
        inline=True,
    )
    embed.set_thumbnail(url=STARTINFO_IMG_URL)
    embed.set_footer(text="Paradise City Roleplay \u2022 Start-Info")
    return embed


async def auto_startinfo_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(STARTINFO_CHANNEL_ID)
        if not channel:
            continue

        data = _load_data()

        if data.get("message_id"):
            try:
                msg = await channel.fetch_message(data["message_id"])
                await msg.edit(embed=_build_embed())
                print(f"[startinfo] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        try:
            new_msg = await channel.send(embed=_build_embed())
            data["message_id"] = new_msg.id
            _save_data(data)
            print(f"[startinfo] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[startinfo] Fehler: {e}")
