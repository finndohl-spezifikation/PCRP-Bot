# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# embeds/boost.py — Boost Belohnungen Embed
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *

BOOST_CHANNEL_ID  = 1491622819824402583
BOOST_COLOR       = 0xB44FE8
BOOST_MSG_FILE    = DATA_DIR / "boost_msg.json"
BOOST_IMAGE_PATH  = Path(__file__).parent / "boost_banner.png"
BOOST_URL         = f"https://discord.com/channels/{GUILD_ID}/subscription"


def _load_boost_data() -> dict:
    if BOOST_MSG_FILE.exists():
        with open(BOOST_MSG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message_id": None, "image_url": None}


def _save_boost_data(data: dict):
    with open(BOOST_MSG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _build_boost_embed(image_url: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="💎 Boost Belohnungen",
        description=(
            "**Pro Boost 5.000 $**\n\n"
            "**Ab 5 Boosts 1 Sportwagen deiner Wahl dazu**"
        ),
        color=BOOST_COLOR,
    )
    if image_url:
        embed.set_image(url=image_url)
    embed.set_footer(text="Paradise City Roleplay — Server Boosts")
    return embed


class BoostView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Server Boosten",
            emoji="💜",
            style=discord.ButtonStyle.link,
            url=BOOST_URL,
        ))


async def auto_boost_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(BOOST_CHANNEL_ID)
        if not channel:
            continue

        data = _load_boost_data()

        # Bestehende Nachricht bearbeiten
        if data.get("message_id"):
            try:
                msg   = await channel.fetch_message(data["message_id"])
                embed = _build_boost_embed(data.get("image_url"))
                await msg.edit(embed=embed, view=BoostView())
                print(f"[boost] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        # Neu senden mit Bild
        embed = _build_boost_embed()
        file  = None
        if BOOST_IMAGE_PATH.exists():
            file = discord.File(str(BOOST_IMAGE_PATH), filename="boost_banner.png")
            embed.set_image(url="attachment://boost_banner.png")

        try:
            if file:
                new_msg = await channel.send(embed=embed, view=BoostView(), file=file)
            else:
                new_msg = await channel.send(embed=embed, view=BoostView())

            image_url = new_msg.attachments[0].url if new_msg.attachments else None
            data["message_id"] = new_msg.id
            data["image_url"]  = image_url
            _save_boost_data(data)
            print(f"[boost] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[boost] Fehler: {e}")
