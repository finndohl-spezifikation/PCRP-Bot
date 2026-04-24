# -*- coding: utf-8 -*-
# fraktionen.py -- Hilfsfunktionen Fraktionsverwaltung
# Paradise City Roleplay Discord Bot

from config import *
import json

FRAK_WARN_CHANNEL_ID   = 1492701273571725433
FRAK_SPERRE_CHANNEL_ID = 1497050512028205186
FRAK_LIST_CHANNEL_ID   = 1492701250528084059
MAX_WARNS              = 3
FRAK_FOOTER            = "Mit freundlichen Gr\u00fc\u00dfen - Fraktionsleitung"

FRAK_FILE     = DATA_DIR / "fraktionen_data.json"
FRAK_LIST_MSG = DATA_DIR / "frak_list_msg.json"


# -- Datenzugriff ----------------------------------------------

def frak_load() -> dict:
    if FRAK_FILE.exists():
        try:
            return json.load(open(FRAK_FILE, encoding="utf-8"))
        except Exception:
            pass
    return {}


def frak_save(data: dict):
    with open(FRAK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def frak_load_msg() -> dict:
    if FRAK_LIST_MSG.exists():
        try:
            return json.load(open(FRAK_LIST_MSG, encoding="utf-8"))
        except Exception:
            pass
    return {}


def frak_save_msg(data: dict):
    with open(FRAK_LIST_MSG, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -- Berechtigung ---------------------------------------------

def frak_hat_recht(interaction: discord.Interaction) -> bool:
    role_ids = {r.id for r in interaction.user.roles}
    return bool(role_ids & {INHABER_ROLE_ID, ADMIN_ROLE_ID, DASH_ROLE_ID})


# -- Frak-Liste Embed -----------------------------------------

def frak_build_list_embed(data: dict) -> discord.Embed:
    emb = discord.Embed(
        title="\U0001f3db\ufe0f Aktuelle Fraktionen",
        color=0x2F3136,
        timestamp=datetime.now(timezone.utc),
    )
    if not data:
        emb.description = "*Keine Fraktionen eingetragen.*"
        emb.set_footer(text=FRAK_FOOTER)
        return emb

    lines = []
    for name, entry in sorted(data.items()):
        wc = len(entry.get("warns", []))
        if wc == 0:
            symbol = "\U0001f3db\ufe0f"
        elif wc == 1:
            symbol = "\u26a0\ufe0f"
        elif wc == 2:
            symbol = "\u26a0\ufe0f\u26a0\ufe0f"
        else:
            symbol = "\U0001f6a8"
        lines.append(f"{symbol} **{name}** \u2014 {wc}/{MAX_WARNS} Warns")

    emb.description = "\n".join(lines)
    emb.set_footer(text=FRAK_FOOTER)
    return emb


async def frak_update_list():
    try:
        channel = await bot.fetch_channel(FRAK_LIST_CHANNEL_ID)
    except Exception:
        return
    data     = frak_load()
    embed    = frak_build_list_embed(data)
    msg_data = frak_load_msg()
    msg_id   = msg_data.get("message_id")
    if msg_id:
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(embed=embed)
            return
        except Exception:
            pass
    sent = await channel.send(embed=embed)
    frak_save_msg({"message_id": sent.id})


# -- Autocomplete ---------------------------------------------

async def frakwarn_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    data = frak_load()
    return [
        app_commands.Choice(name=name, value=name)
        for name, entry in data.items()
        if entry.get("warns") and current.lower() in name.lower()
    ][:25]


async def frak_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    data = frak_load()
    return [
        app_commands.Choice(name=name, value=name)
        for name in data
        if current.lower() in name.lower()
    ][:25]
