# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# startinfo.py — "Wo starte ich?" Embed
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

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
        title="🌆 Wo starte ich?",
        color=LOG_COLOR,
    )
    embed.add_field(
        name="✈️ Du hast die legale Einreise gewählt?",
        value=(
            "> Da du als legaler Bewohner einreist, startest du bei uns am Flughafen von Los Santos.\n"
            "> Von dort aus kannst du dir ein Taxi zum Autohaus nehmen, um dein Startfahrzeug abzuholen.\n"
            "> Welches Startfahrzeug du bekommst, findest du in <#1490878159804174470>."
        ),
        inline=False,
    )
    embed.add_field(
        name="⚓ Du hast die illegale Einreise gewählt?",
        value=(
            "> Da du als illegaler Bewohner startest, kommst du am Hafen von Los Santos an.\n"
            "> Sobald du dort ankommst, begib dich unauffällig zum Autohaus, ohne vom LAPD erwischt zu werden,\n"
            "> und hole dein Startfahrzeug ab. Welches Startfahrzeug das ist, findest du in <#1490878159804174470>."
        ),
        inline=False,
    )
    embed.set_thumbnail(url=STARTINFO_IMG_URL)
    embed.set_footer(text="Paradise City Roleplay")
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
