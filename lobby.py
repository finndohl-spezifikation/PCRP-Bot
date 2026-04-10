# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# lobby.py — Lobby System (Abstimmung, Öffnen, Schließen)
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *


@bot.tree.command(name="lobby-abstimmung", description="[LOBBY] Sendet eine Lobby-Abstimmung", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def lobby_abstimmung(interaction: discord.Interaction):
    if not any(r.id == LOBBY_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Dieser Befehl ist nur für das Lobby-Team verfügbar.", ephemeral=True)
        return

    kanal = interaction.guild.get_channel(LOBBY_CHANNEL_ID)
    if not kanal:
        await interaction.response.send_message("❌ Lobby-Kanal nicht gefunden.", ephemeral=True)
        return

    datum = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    embed = discord.Embed(
        title="Lobby Abstimmung",
        description=(
            "✅ **Ich komme**\n\n"
            "🕑 **Ich komme später**\n\n"
            "❌ **Ich komme nicht**\n\n"
            f"**Datum:** {datum}\n\n"
            "**Uhrzeit:** 18:00"
        ),
        color=0x00BFFF,
        timestamp=datetime.now(timezone.utc)
    )

    GIF_URL   = "https://share.creavite.co/69d7a4bca828deb1587385dd.gif"
    ping_text = "<@&1490855734517174376>"

    await interaction.response.send_message("✅ Abstimmung gesendet!", ephemeral=True)

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

    await msg.add_reaction("✅")
    await msg.add_reaction("🕑")
    await msg.add_reaction("❌")


@bot.tree.command(name="lobby-open", description="[LOBBY] Öffnet die Lobby", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def lobby_open(interaction: discord.Interaction):
    if not any(r.id == LOBBY_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Dieser Befehl ist nur für das Lobby-Team verfügbar.", ephemeral=True)
        return

    kanal = interaction.guild.get_channel(1490882585046290542)
    if not kanal:
        await interaction.response.send_message("❌ Lobby-Kanal nicht gefunden.", ephemeral=True)
        return

    host_name = interaction.user.display_name

    embed = discord.Embed(
        title="Lobby Status",
        description=(
            "Jetzt Geöffnet\n\n"
            f"**Lobby Host**\n{host_name}\n\n"
            "Das Team von Cryptik Roleplay wünscht euch Viel spaß beim RP"
        ),
        color=0x00BFFF,
        timestamp=datetime.now(timezone.utc)
    )

    GIF_URL   = "https://share.creavite.co/69d7bee5a828deb1587385f2.gif"
    ping_text = "<@&1490855734517174376>"

    await interaction.response.send_message("✅ Lobby geöffnet!", ephemeral=True)

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


@bot.tree.command(name="lobby-close", description="[LOBBY] Schließt die Lobby", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def lobby_close(interaction: discord.Interaction):
    if not any(r.id == LOBBY_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Dieser Befehl ist nur für das Lobby-Team verfügbar.", ephemeral=True)
        return

    kanal = interaction.guild.get_channel(1490882585046290542)
    if not kanal:
        await interaction.response.send_message("❌ Lobby-Kanal nicht gefunden.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Lobby Status",
        description=(
            "Jetzt Geschlossen\n\n"
            "Wir bedanken uns für Jeden spieler der heute am RP teilgenommen hat und "
            "Wünschen euch einen schönen Rest abend\n\n"
            "Wenn du heute Probleme im RP hattest melde dich gerne jederzeit über ein "
            "Ticket im kanal <#1490885002030874775>"
        ),
        color=0x00BFFF,
        timestamp=datetime.now(timezone.utc)
    )

    GIF_URL   = "https://share.creavite.co/69d7c321a828deb1587385f6.gif"
    ping_text = "<@&1490855734517174376>"

    await interaction.response.send_message("✅ Lobby geschlossen!", ephemeral=True)

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
