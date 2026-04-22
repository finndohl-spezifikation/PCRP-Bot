# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# lobby.py \u2014 Lobby System (Abstimmung, \u00D6ffnen, Schlie\u00DFen)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
import support_voice as _sv


@bot.tree.command(name="lobby-abstimmung", description="[LOBBY] Sendet eine Lobby-Abstimmung", guild=discord.Object(id=GUILD_ID))
async def lobby_abstimmung(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not any(r.id == LOBBY_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr das Lobby-Team verf\u00FCgbar.", ephemeral=True)
        return

    kanal = interaction.guild.get_channel(LOBBY_CHANNEL_ID)
    if not kanal:
        await interaction.response.send_message("\u274C Lobby-Kanal nicht gefunden.", ephemeral=True)
        return

    datum = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    embed = discord.Embed(
        title="Lobby Abstimmung",
        description=(
            "\u2705 **Ich komme**\n\n"
            "\U0001F551 **Ich komme sp\u00E4ter**\n\n"
            "\u274C **Ich komme nicht**\n\n"
            f"**Datum:** {datum}\n\n"
            "**Uhrzeit:** 18:00"
        ),
        color=0xE67E22,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Lobby-System")

    GIF_URL   = "https://share.creavite.co/69d7a4bca828deb1587385dd.gif"
    ping_text = "<@&1490855734517174376>"

    await interaction.response.send_message("\u2705 Abstimmung gesendet!", ephemeral=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GIF_URL) as resp:
                if resp.status == 200:
                    gif_bytes = await resp.read()
                    gif_file  = discord.File(io.BytesIO(gif_bytes), filename="lobby.gif")
                    embed.set_image(url="attachment://lobby.gif")
                    msg = await kanal.send(content=ping_text, file=gif_file, embed=embed)
                else:
                    raise ValueError(f"HTTP {resp.status}")
    except Exception:
        embed.set_image(url=GIF_URL)
        msg = await kanal.send(content=ping_text, embed=embed)

    await msg.add_reaction("\u2705")
    await msg.add_reaction("\U0001F551")
    await msg.add_reaction("\u274C")


@bot.tree.command(name="lobby-open", description="[LOBBY] \u00D6ffnet die Lobby", guild=discord.Object(id=GUILD_ID))
async def lobby_open(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not any(r.id == LOBBY_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr das Lobby-Team verf\u00FCgbar.", ephemeral=True)
        return

    kanal = interaction.guild.get_channel(1490882585046290542)
    if not kanal:
        await interaction.response.send_message("\u274C Lobby-Kanal nicht gefunden.", ephemeral=True)
        return

    host_name = interaction.user.display_name

    embed = discord.Embed(
        title="Lobby Status",
        description=(
            "Jetzt Ge\u00F6ffnet\n\n"
            f"**Lobby Host**\n{host_name}\n\n"
            "Das Team von Paradise City Roleplay w\u00FCnscht euch Viel spa\u00DF beim RP"
        ),
        color=0xE67E22,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Lobby-System")

    GIF_URL   = "https://share.creavite.co/69d7bee5a828deb1587385f2.gif"
    ping_text = "<@&1490855734517174376>"

    await interaction.response.send_message("\u2705 Lobby ge\u00F6ffnet!", ephemeral=True)
    _sv.set_lobby_status(True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GIF_URL) as resp:
                if resp.status == 200:
                    gif_bytes = await resp.read()
                    gif_file  = discord.File(io.BytesIO(gif_bytes), filename="lobby_open.gif")
                    embed.set_image(url="attachment://lobby_open.gif")
                    await kanal.send(content=ping_text, file=gif_file, embed=embed)
                else:
                    raise ValueError(f"HTTP {resp.status}")
    except Exception:
        embed.set_image(url=GIF_URL)
        await kanal.send(content=ping_text, embed=embed)


@bot.tree.command(name="lobby-close", description="[LOBBY] Schlie\u00DFt die Lobby", guild=discord.Object(id=GUILD_ID))
async def lobby_close(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not any(r.id == LOBBY_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr das Lobby-Team verf\u00FCgbar.", ephemeral=True)
        return

    kanal = interaction.guild.get_channel(1490882585046290542)
    if not kanal:
        await interaction.response.send_message("\u274C Lobby-Kanal nicht gefunden.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Lobby Status",
        description=(
            "Jetzt Geschlossen\n\n"
            "Wir bedanken uns f\u00FCr Jeden spieler der heute am RP teilgenommen hat und "
            "W\u00FCnschen euch einen sch\u00F6nen Rest abend\n\n"
            "Wenn du heute Probleme im RP hattest melde dich gerne jederzeit \u00FCber ein "
            "Ticket im kanal <#1490885002030874775>"
        ),
        color=0xE67E22,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Lobby-System")

    GIF_URL   = "https://share.creavite.co/69d7c321a828deb1587385f6.gif"
    ping_text = "<@&1490855734517174376>"

    await interaction.response.send_message("\u2705 Lobby geschlossen!", ephemeral=True)
    _sv.set_lobby_status(False)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GIF_URL) as resp:
                if resp.status == 200:
                    gif_bytes = await resp.read()
                    gif_file  = discord.File(io.BytesIO(gif_bytes), filename="lobby_close.gif")
                    embed.set_image(url="attachment://lobby_close.gif")
                    await kanal.send(content=ping_text, file=gif_file, embed=embed)
                else:
                    raise ValueError(f"HTTP {resp.status}")
    except Exception:
        embed.set_image(url=GIF_URL)
        await kanal.send(content=ping_text, embed=embed)
