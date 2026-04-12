# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# starterpaket.py — Starter Paket Embed
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *

STARTERPAKET_CHANNEL_ID = 1490878159804174470
STARTERPAKET_MSG_FILE   = DATA_DIR / "starterpaket_msg.json"
STARTERPAKET_IMG_URL    = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/starterpaket.png"


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
        title="🎁 Starter Paket",
        color=LOG_COLOR,
    )
    embed.add_field(
        name="💰 Startgeld",
        value="> 5.000 $",
        inline=False,
    )
    embed.add_field(
        name="🚗 Startfahrzeug",
        value=(
            "> **Declasse Voodoo**\n"
            "> *(Standard — keine Tuning-Optionen)*\n"
            "> **oder**\n"
            "> **BMX Fahrrad**"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚠️ Hinweis",
        value=(
            "> Das Fahrzeug **Declasse Voodoo** wird ausschließlich im Standard-Zustand ausgegeben.\n"
            "> Es darf keine Tuning-Optionen enthalten."
        ),
        inline=False,
    )
    embed.set_image(url=STARTERPAKET_IMG_URL)
    embed.set_footer(text="Paradise City Roleplay — Starter Paket")
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
