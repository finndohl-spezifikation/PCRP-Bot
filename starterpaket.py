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
    sep = "\u2015" * 22
    embed = discord.Embed(
        title="\U0001f381 Starterpaket \u2014 Paradise City Roleplay",
        description=(
            "Willkommen auf **Paradise City Roleplay**!\n"
            "Je nach Einreiseart erh\u00e4ltst du beim Start folgendes Paket.\n"
            "Das Fahrzeug steht bereits am Startpunkt bereit.\n"
            f"{sep}"
        ),
        color=0xFF6600,
    )
    embed.add_field(
        name="\u2705 Legale Einreise",
        value=(
            "\u27A1 \U0001f4b0 **5.000 $** Startkapital\n"
            "\u27A1 \U0001f697 **Declasse Rhapsody**"
        ),
        inline=True,
    )
    embed.add_field(
        name="\U0001f6ab Illegale Einreise",
        value=(
            "\u27A1 \U0001f4b0 **5.000 $** Startkapital\n"
            "\u27A1 \U0001f697 **Karin Kuruma**"
        ),
        inline=True,
    )
    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(
        name="\U0001f465 Gruppeneinreise *(ab 5 Personen)*",
        value=(
            "\u27A1 \U0001f4b0 **10.000 $ pro Person** Startkapital\n"
            "\u27A1 \U0001f697 **Enus Huntley S**"
        ),
        inline=False,
    )
    embed.set_image(url=STARTERPAKET_IMG_URL)
    embed.set_footer(text="Paradise City Roleplay \u2022 Viel Spa\xdf auf dem Server!")
    return embed


async def auto_starterpaket_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(STARTERPAKET_CHANNEL_ID)
        if not channel:
            continue

        data = _load_data()
        existing_msg = None

        # 1. Gespeicherte Message-ID ausprobieren
        if data.get("message_id"):
            try:
                existing_msg = await channel.fetch_message(data["message_id"])
            except Exception:
                pass

        # 2. Fallback: Channel-Verlauf nach bestehendem Bot-Embed scannen
        if not existing_msg:
            try:
                async for msg in channel.history(limit=50):
                    if msg.author.id == bot.user.id and msg.embeds:
                        if msg.embeds[0].title and "Starterpaket" in msg.embeds[0].title:
                            existing_msg = msg
                            data["message_id"] = msg.id
                            _save_data(data)
                            break
            except Exception:
                pass

        if existing_msg:
            try:
                await existing_msg.edit(embed=_build_embed())
                print(f"[starterpaket] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        # 3. Wirklich neu senden
        try:
            new_msg = await channel.send(embed=_build_embed())
            data["message_id"] = new_msg.id
            _save_data(data)
            print(f"[starterpaket] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[starterpaket] Fehler: {e}")

