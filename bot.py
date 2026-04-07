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

# Kanal-ID für einmalige Hallo-Nachricht beim Bot-Start
CHANNEL_ID = 1490878151897911557

@bot.event
async def on_ready():
    global bot_start_time
    bot_start_time = datetime.now(timezone.utc)
    print(f"Bot ist online als {bot.user} (ID: {bot.user.id})")

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Hallo! 👋")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Verhindert, dass alte Nachrichten nach einem Neustart verarbeitet werden
    if bot_start_time and message.created_at < bot_start_time:
        return
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    # Sicherheitscheck: Wurde der User in dieser Session schon begrüßt?
    if member.id in welcomed_members:
        return

    # 1. Rolle zuweisen
    rolle = member.guild.get_role(1490855725516460234)
    if rolle:
        try:
            await member.add_roles(rolle)
        except discord.Forbidden:
            print(f"Fehler: Keine Berechtigung, die Rolle an {member.name} zu vergeben.")

    # 2. Willkommens-Embed erstellen (Alles in einem Block!)
    embed = discord.Embed(
        title="Herzlich Willkommen!",
        description=(
            f"Hallo {member.mention}, willkommen auf **Kryptik Roleplay**!\n\n"
            "Wir wünschen dir viel Spaß auf unserem Server und hoffen, dass du dich gut zurechtfindest.\n\n"
            "**Support:**\n"
            "Bei Problemen melde dich jederzeit über ein Support Ticket im Channel <#1490855943230066818>."
        ),
        color=0x00BFFF,
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
    embed.set_footer(text="Kryptik Roleplay • Willkommensteam")

    # 3. Nachricht senden
    try:
        # Hier wird nur EINMAL gesendet, das Embed enthält alle Infos
        await member.send(embed=embed)
        welcomed_members.add(member.id) # Merken, damit keine Dubletten kommen
    except discord.Forbidden:
        print(f"Konnte DM an {member.name} nicht senden (DMs deaktiviert).")

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! 👋")

token = os.environ.get("DISCORD_TOKEN")
if not token:
    # Falls du lokal testest und keine Umgebungsvariable hast, kannst du den Token hier eintragen:
    # token = "DEIN_TOKEN_HIER"
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
