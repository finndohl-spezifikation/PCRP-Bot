import os
import discord
from discord.ext import commands
from datetime import datetime, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot_start_time = None

# Kanal-ID, in den die Nachricht gesendet wird
CHANNEL_ID = 1490878151897911557

@bot.event
async def on_ready():
    global bot_start_time
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")

    # Einmalig "Hallo" in den Kanal senden
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Hallo! 👋")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if bot_start_time and message.created_at < bot_start_time:
        return
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    rolle = member.guild.get_role(1490855725516460234)
    if rolle:
        try:
            await member.add_roles(rolle)
        except discord.Forbidden:
            pass
    try:
        embed = discord.Embed(
            description=(
                "> Willkommen auf Kryptik Roleplay deinem RP server mit Ultimativem Spaß und Hochwertigem RP\n\n"
                "> Wir wünschen dir viel Spaß auf unserem Server und hoffen das du dich bei uns Gut Zurecht findest\n\n"
                "> Solltest du mal Schwierigkeiten haben melde dich gerne Jederzeit über ein Support Ticket im channel <#1490855943230066818>"
            ),
            color=0x00BFFF
        )
        await member.send(content=member.mention, embed=embed)
    except discord.Forbidden:
        pass

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! 👋")

token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
