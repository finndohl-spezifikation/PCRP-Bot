# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# commands.py — Prefix Commands (!hallo, !testping, !botstatus, etc.)
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import is_admin, send_bot_status
from ticket import TicketSelectView
from handy import HandyView


@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo, {ctx.author.display_name}! 👋")


@bot.command(name="testping")
async def testping(ctx):
    if not is_admin(ctx.author):
        return
    kanal = ctx.guild.get_channel(JOIN_LOG_CHANNEL_ID)
    rolle = ctx.guild.get_role(MOD_ROLE_ID)
    if kanal and rolle:
        await kanal.send(f"{rolle.mention} Dies ist ein Test-Ping vom Bot!")
    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="botstatus")
async def botstatus(ctx):
    if not is_admin(ctx.author):
        return
    await send_bot_status()
    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="ticketsetup")
async def ticketsetup(ctx):
    if not is_admin(ctx.author):
        return
    channel = ctx.guild.get_channel(TICKET_SETUP_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Ticket-Kanal nicht gefunden!")
        return
    embed = discord.Embed(
        title="🎟 Support — Ticket erstellen",
        description=(
            "Benötigst du Hilfe oder möchtest ein Anliegen melden?\n\n"
            "Wähle unten im Menü die passende Ticket-Art aus.\n"
            "Unser Team wird sich schnellstmöglich um dich kümmern.\n\n"
            "**Verfügbare Ticket-Arten:**\n"
            "🎟 **Support** — Allgemeiner Support\n"
            "🎟 **Highteam Ticket** — Direkter Kontakt zum Highteam\n"
            "🎟 **Fraktions Bewerbung** — Bewirb dich für eine Fraktion\n"
            "🎟 **Beschwerde Ticket** — Beschwerde einreichen\n"
            "🎟 **Bug Report** — Fehler oder Bug melden"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay • Support-System")
    await channel.send(embed=embed, view=TicketSelectView())
    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="handysetup")
async def handysetup(ctx):
    """Postet das Handy-Embed erneut im Handy-Kanal. Nur für Admins."""
    if not is_admin(ctx.author):
        return
    channel = ctx.guild.get_channel(HANDY_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Handy-Kanal nicht gefunden!")
        return
    try:
        async for msg in channel.history(limit=20):
            if msg.author.id == ctx.bot.user.id and msg.embeds:
                for emb in msg.embeds:
                    if emb.title and "Handy" in emb.title:
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                        break
    except Exception:
        pass
    embed = discord.Embed(
        title="📱 Handy — Einstellungen",
        description=(
            "Willkommen in deinen Handy-Einstellungen!\n\n"
            "Hier kannst du deinen Notruf absetzen, deine Handynummer einsehen "
            "und Social-Media-Apps installieren oder deinstallieren.\n\n"
            "**🚨 Dispatch-Buttons** — Sende einen Notruf an die zuständige Einheit\n"
            "**📱 Handy Nummer** — Zeigt deine persönliche LA-Nummer\n"
            "**📱 Instagram / Parship** — Apps installieren & deinstallieren\n\n"
            "⚠️ *Du benötigst das Item* `📱| Handy` *aus dem Shop, um diese Funktionen zu nutzen.*"
        ),
        color=0xE67E22,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay • Handy-System")
    await channel.send(embed=embed, view=HandyView())
    try:
        await ctx.message.delete()
    except Exception:
        pass
