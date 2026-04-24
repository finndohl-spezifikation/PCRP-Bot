# -*- coding: utf-8 -*-
# starterpaket.py \u2014 Starter Paket Embed
# Paradise City Roleplay Discord Bot

from config import *

STARTERPAKET_CHANNEL_ID = 1490878159804174470
STARTERPAKET_MSG_FILE   = DATA_DIR / "starterpaket_msg.json"
STARTERPAKET_IMG_URL    = "https://130f7b21-a902-4ec0-9019-6c1791f5924b-00-2d2m2xzo65o8p.sisko.replit.dev/starterpaket.jpg"


def _load_data() -> dict:
    if STARTERPAKET_MSG_FILE.exists():
        with open(STARTERPAKET_MSG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message_id": None}


def _save_data(data: dict):
    with open(STARTERPAKET_MSG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\U0001f381 Starterpaket",
        description=(
            "Je nach Einreiseart erh\u00e4ltst du folgendes Starterpaket:\n"
            "Das Fahrzeug findest du am Startpunkt bereit."
        ),
        color=0xFF6600,
    )
    embed.add_field(
        name="\u2705 Legale Einreise",
        value="\U0001f4b0 **5.000 $** \u2502 \U0001f697 Declasse Rhapsody",
        inline=False,
    )
    embed.add_field(
        name="\U0001f6ab Illegale Einreise",
        value="\U0001f4b0 **5.000 $** \u2502 \U0001f697 Karin Kuruma",
        inline=False,
    )
    embed.add_field(
        name="\U0001f465 Gruppeneinreise *(ab 5 Personen)*",
        value="\U0001f4b0 **10.000 $ pro Person** \u2502 \U0001f697 Enus Huntley S",
        inline=False,
    )
    embed.set_image(url=STARTERPAKET_IMG_URL)
    embed.set_footer(text="Paradise City Roleplay \u2022 Starterpaket")
    return embed


async def auto_starterpaket_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(STARTERPAKET_CHANNEL_ID)
        if not channel:
            continue

        data = _load_data()

        if data.get("message_id"):
            try:
                msg = await channel.fetch_message(data["message_id"])
                await msg.edit(embed=_build_embed())
                print(f"[starterpaket] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        try:
            new_msg = await channel.send(embed=_build_embed())
            data["message_id"] = new_msg.id
            _save_data(data)
            print(f"[starterpaket] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[starterpaket] Fehler: {e}")
