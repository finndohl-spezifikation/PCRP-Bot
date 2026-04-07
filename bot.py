import os
import discord
from discord.ext import commands
from datetime import datetime, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot_start_time = None

# Set für Mitglieder, denen bereits die Willkommensnachricht geschickt wurde
welcomed_members = set()

# Kanal-ID für einmalige Hallo-Nachricht beim Bot-Start (optional)
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
    # Prüfen, ob Mitglied schon begrüßt wurde
    if member.id in welcomed_members:
        return

    # Rolle hinzufügen
    rolle = member.guild.get_role(1490855725516460234)
    if rolle:
        try:
            await member.add_roles(rolle)
        except discord.Forbidden:
            pass

    # Willkommensnachricht sauber, nur einmal
    try:
        embed = discord.Embed(
            description=(
                f"Willkommen auf Kryptik Roleplay, {member.display_name}!\n\n"
                "Wir wünschen dir viel Spaß auf unserem Server und hoffen, dass du dich gut zurechtfindest.\n\n"
                "Bei Problemen melde dich jederzeit über ein Support Ticket im Channel <#1490855943230066818>."
            ),
            color=0x00BFFF
        )
        await member.send(embed=embed)  # <- kein content=member.mention
        welcomed_members.add(member.id)
    except discord.Forbidden:
        pass

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! 👋")

token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
