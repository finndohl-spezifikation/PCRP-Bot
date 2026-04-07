import os
import discord
import asyncio

GUILD_ID        = 1490839259907887239
MEMBER_ROLE_ID  = 1490855722534310003
ILLEGAL_ROLE_ID = 1490855730767597738

MEMBER_BLOCKED_CATEGORIES = [
    "Server Logs", "Serverteam", "Einreisen",
    "Illegales Farmen", "Raubüberfälle", "Illegaler Minijob"
]

ILLEGAL_ALLOWED_CATEGORIES = ["Illegales Farmen", "Raubüberfälle", "Illegaler Minijob"]

ILLEGAL_WRITE_CHANNELS = [
    "jagen", "autos stehlen", "drogenfahrt",
    "weed farmen", "kokain herstellen", "lsd herstellen",
    "meth herstellen", "moonshine herstellen"
]

MEMBER_WRITE_SINGLE = ["chat", "memes", "counter", "drehen", "ebay", "shop"]
MEMBER_WRITE_CATEGORIES_EXCEPT_INFO = ["Legales Farmen", "Minijobs"]
MEMBER_WRITE_ALL_IN_CATEGORY = ["IC Bereich"]
MEMBER_SMARTPHONE_BLOCKED = ["einstellungen", "dispatch"]

intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild nicht gefunden!")
        await client.close()
        return

    everyone     = guild.default_role
    member_role  = guild.get_role(MEMBER_ROLE_ID)
    illegal_role = guild.get_role(ILLEGAL_ROLE_ID)

    # ── Schritt 1: Alle Channels auf Privat (@everyone kein Sehen) ───
    print("Schritt 1: Alle Channels auf Privat setzen...")
    for channel in guild.channels:
        if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
            continue
        await channel.set_permissions(everyone, view_channel=False)
        print(f"PRIVAT: {channel.name}")
        await asyncio.sleep(0.3)
    print("Alle Channels privat gesetzt.")

    # ── Schritt 2: MEMBER_ROLE Berechtigungen ────────────────────────
    print("Schritt 2: MEMBER_ROLE Berechtigungen setzen...")
    for channel in guild.channels:
        if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
            continue
        category_name = channel.category.name if channel.category else ""
        channel_lower = channel.name.lower()

        if member_role:
            if category_name in MEMBER_BLOCKED_CATEGORIES:
                await channel.set_permissions(member_role, view_channel=False)
                print(f"MEMBER: Kein Sehen — {category_name}/{channel.name}")
            else:
                can_write = False
                if any(w in channel_lower for w in MEMBER_WRITE_SINGLE):
                    can_write = True
                if category_name in MEMBER_WRITE_ALL_IN_CATEGORY:
                    can_write = True
                if category_name == "Smartphone":
                    if channel_lower not in MEMBER_SMARTPHONE_BLOCKED:
                        can_write = True
                if category_name in MEMBER_WRITE_CATEGORIES_EXCEPT_INFO:
                    if not channel_lower.startswith("info"):
                        can_write = True
                if can_write:
                    await channel.set_permissions(
                        member_role,
                        view_channel=True,
                        send_messages=True
                    )
                    print(f"MEMBER: Sehen + Schreiben — {category_name}/{channel.name}")
                else:
                    await channel.set_permissions(
                        member_role,
                        view_channel=True,
                        send_messages=False,
                        create_public_threads=False
                    )
                    print(f"MEMBER: Nur Sehen — {category_name}/{channel.name}")
        await asyncio.sleep(0.4)

    # ── Schritt 3: ILLEGAL_ROLE Berechtigungen ───────────────────────
    print("Schritt 3: ILLEGAL_ROLE Berechtigungen setzen...")
    for channel in guild.channels:
        if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
            continue
        category_name = channel.category.name if channel.category else ""
        channel_lower = channel.name.lower()

        if illegal_role:
            if category_name in ILLEGAL_ALLOWED_CATEGORIES:
                can_write = any(w in channel_lower for w in ILLEGAL_WRITE_CHANNELS)
                if can_write:
                    await channel.set_permissions(
                        illegal_role,
                        view_channel=True,
                        send_messages=True
                    )
                    print(f"ILLEGAL: Sehen + Schreiben — {category_name}/{channel.name}")
                else:
                    await channel.set_permissions(
                        illegal_role,
                        view_channel=True,
                        send_messages=False,
                        create_public_threads=False
                    )
                    print(f"ILLEGAL: Nur Sehen — {category_name}/{channel.name}")
            else:
                await channel.set_permissions(illegal_role, view_channel=False)
                print(f"ILLEGAL: Kein Sehen — {category_name}/{channel.name}")
        await asyncio.sleep(0.4)

    print("Fertig! Alle Berechtigungen gesetzt.")
    await client.close()


token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

client.run(token)
