import discord
from discord import app_commands
from config import *

@bot.tree.command(
    name="hallo",
    description="Sagt hallo",
    guild=discord.Object(id=GUILD_ID)
)
async def hallo(interaction: discord.Interaction):
    """Sagt hallo zum Nutzer"""
    await interaction.response.send_message(f"Hallo {interaction.user.mention}! 👋")

@bot.tree.command(
    name="ping",
    description="Zeigt den Bot-Ping",
    guild=discord.Object(id=GUILD_ID)
)
async def ping(interaction: discord.Interaction):
    """Zeigt die Latenz des Bots"""
    await interaction.response.send_message(f"Pong! 🏓 {round(bot.latency * 1000)}ms")

@bot.tree.command(
    name="userinfo",
    description="Zeigt Informationen über einen Nutzer",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    user="Der Nutzer, über den Informationen angezeigt werden sollen"
)
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    """Zeigt Nutzerinformationen"""
    if user is None:
        user = interaction.user
    
    embed = discord.Embed(
        title=f"👤 Informationen über {user.display_name}",
        color=user.color,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    
    embed.add_field(name="🏷️ Username", value=f"{user.name}#{user.discriminator}", inline=True)
    embed.add_field(name="🆔 User ID", value=f"`{user.id}`", inline=True)
    embed.add_field(name="📅 Beigetreten", value=f"<t:{int(user.joined_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🎭 Top Rolle", value=user.top_role.mention if user.top_role else "Keine Rolle", inline=True)
    embed.add_field(name="🤖 Bot?", value="Ja" if user.bot else "Nein", inline=True)
    
    if len(user.roles) > 1:
        roles = [role.mention for role in user.roles[1:]]  # @everyone überspringen
        embed.add_field(name="🎭 Rollen", value=", ".join(roles[:10]) + ("..." if len(roles) > 10 else ""), inline=False)
    
    embed.set_footer(text=f"Angefordert von {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(
    name="serverinfo",
    description="Zeigt Informationen über den Server",
    guild=discord.Object(id=GUILD_ID)
)
async def serverinfo(interaction: discord.Interaction):
    """Zeigt Serverinformationen"""
    guild = interaction.guild
    
    embed = discord.Embed(
        title=f"🏰 Informationen über {guild.name}",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.set_thumbnail(url=guild.icon.url if guild.icon else guild.default_icon.url)
    
    embed.add_field(name="👑 Besitzer", value=guild.owner.mention, inline=True)
    embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="👥 Mitglieder", value=f"{guild.member_count}", inline=True)
    embed.add_field(name="📅 Erstellt", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🎭 Rollen", value=len(guild.roles), inline=True)
    embed.add_field(name="💬 Kanäle", value=len(guild.text_channels) + len(guild.voice_channels), inline=True)
    
    if guild.banner:
        embed.set_image(url=guild.banner.url)
    
    embed.set_footer(text=f"Angefordert von {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(
    name="hilfe",
    description="Zeigt Hilfe für die Commands",
    guild=discord.Object(id=GUILD_ID)
)
async def hilfe(interaction: discord.Interaction):
    """Zeigt Hilfe-Embed"""
    embed = discord.Embed(
        title="📚 Bot Hilfe",
        description="Hier sind alle verfügbaren Commands:",
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)
    )
    
    commands_list = [
        "👋 `/hallo` - Sagt hallo",
        "🏓 `/ping` - Zeigt Bot-Ping",
        "👤 `/userinfo` - Nutzerinformationen",
        "🏰 `/serverinfo` - Serverinformationen",
        "📚 `/hilfe` - Diese Hilfe"
    ]
    
    embed.add_field(name="🔧 Allgemeine Commands", value="\n".join(commands_list), inline=False)
    
    embed.add_field(
        name="💡 Tipp",
        value="Manche Commands haben zusätzliche Optionen. Schau dir die Command-Suggestions in Discord an!",
        inline=False
    )
    
    embed.set_footer(text=f"Angefordert von {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

print("✅ commands.py erfolgreich geladen - Commands bereit!")
