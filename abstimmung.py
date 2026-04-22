# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# abstimmung.py \u2014 Abstimmungs-System (Reaction Polls)
# Kryptik / Cryptik Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from economy_helpers import (
    abstimmung_polls, save_abstimmung, build_abstimmung_embed
)


# /abstimmung
@bot.tree.command(
    name="abstimmung",
    description="[Allgemein] Erstelle eine Abstimmung mit Balken",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    frage="Die Frage oder das Thema der Abstimmung",
    option_ja="Name f\u00FCr den gr\u00FCnen Balken (\u2705) \u2014 Standard: Zustimmung",
    option_nein="Name f\u00FCr den roten Balken (\u274C) \u2014 Standard: Ablehnung"
)
async def abstimmung_cmd(interaction: discord.Interaction, frage: str, option_ja: str = "Zustimmung", option_nein: str = "Ablehnung"):
    if interaction.user.id != OWNER_ID and not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr das Serverteam verf\u00FCgbar.", ephemeral=True)
        return

    poll = {
        "question":     frage,
        "option_ja":    option_ja,
        "option_nein":  option_nein,
        "channel_id":   interaction.channel.id,
        "green_voters": [],
        "red_voters":   [],
    }
    embed     = build_abstimmung_embed(poll)
    ping_text = f"<@&{CITIZEN_ROLE_ID}>"
    await interaction.response.send_message(content=ping_text, embed=embed)
    msg = await interaction.original_response()

    poll["message_id"] = msg.id
    abstimmung_polls[str(msg.id)] = poll
    save_abstimmung(abstimmung_polls)

    await msg.add_reaction("\u2705")
    await msg.add_reaction("\u274C")


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return
    msg_id = str(payload.message_id)
    if msg_id not in abstimmung_polls:
        return

    poll      = abstimmung_polls[msg_id]
    uid       = payload.user_id
    emoji_str = str(payload.emoji)
    is_green  = "\u2705" in emoji_str
    is_red    = "\u274C" in emoji_str

    if not is_green and not is_red:
        try:
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, discord.Object(id=uid))
        except Exception:
            pass
        return

    if is_green:
        if uid not in poll["green_voters"]:
            poll["green_voters"].append(uid)
        if uid in poll["red_voters"]:
            poll["red_voters"].remove(uid)
            try:
                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                user    = await bot.fetch_user(uid)
                await message.remove_reaction("\u274C", user)
            except Exception:
                pass
    elif is_red:
        if uid not in poll["red_voters"]:
            poll["red_voters"].append(uid)
        if uid in poll["green_voters"]:
            poll["green_voters"].remove(uid)
            try:
                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                user    = await bot.fetch_user(uid)
                await message.remove_reaction("\u2705", user)
            except Exception:
                pass

    save_abstimmung(abstimmung_polls)

    try:
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        embed   = build_abstimmung_embed(poll)
        await message.edit(embed=embed)
    except Exception:
        pass


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return
    msg_id = str(payload.message_id)
    if msg_id not in abstimmung_polls:
        return

    poll      = abstimmung_polls[msg_id]
    uid       = payload.user_id
    emoji_str = str(payload.emoji)
    is_green  = "\u2705" in emoji_str
    is_red    = "\u274C" in emoji_str

    changed = False
    if is_green and uid in poll["green_voters"]:
        poll["green_voters"].remove(uid)
        changed = True
    elif is_red and uid in poll["red_voters"]:
        poll["red_voters"].remove(uid)
        changed = True

    if not changed:
        return

    save_abstimmung(abstimmung_polls)

    try:
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        embed   = build_abstimmung_embed(poll)
        await message.edit(embed=embed)
    except Exception:
        pass
