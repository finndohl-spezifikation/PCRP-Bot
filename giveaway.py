# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# giveaway.py — Giveaway System
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import log_bot_error


def parse_dauer_zu_sekunden(text: str):
    text = text.lower().strip()
    einheiten = {
        "tag": 86400, "tage": 86400,
        "stunde": 3600, "stunden": 3600,
        "minute": 60, "minuten": 60,
        "sekunde": 1, "sekunden": 1,
    }
    gesamt  = 0
    gefunden = False
    teile   = text.split()
    i = 0
    while i < len(teile):
        try:
            zahl = float(teile[i].replace(",", "."))
            if i + 1 < len(teile):
                einheit = teile[i + 1].rstrip(".")
                if einheit in einheiten:
                    gesamt  += int(zahl * einheiten[einheit])
                    gefunden = True
                    i += 2
                    continue
        except ValueError:
            pass
        i += 1
    return gesamt if gefunden else None


async def create_giveaway_channel_flow(admin: discord.Member, guild: discord.Guild, channel: discord.TextChannel):
    def check(m):
        return m.author.id == admin.id and m.channel.id == channel.id

    frage1 = await channel.send(f"{admin.mention} 🎁 **Was wird verlost?** (z.B. 500.000$, Fahrzeug, Item):")
    antwort1 = await bot.wait_for("message", check=check, timeout=None)
    gewinn = antwort1.content.strip()
    try:
        await frage1.delete()
        await antwort1.delete()
    except Exception:
        pass

    frage2 = await channel.send(f"{admin.mention} ⏱️ **Wie lange läuft das Giveaway?** (z.B. `2 Tage`, `12 Stunden`, `30 Minuten`):")
    while True:
        antwort2     = await bot.wait_for("message", check=check, timeout=None)
        laufzeit_text = antwort2.content.strip()
        sekunden     = parse_dauer_zu_sekunden(laufzeit_text)
        try:
            await antwort2.delete()
        except Exception:
            pass
        if sekunden and sekunden > 0:
            break
        await channel.send(
            f"{admin.mention} ❌ Zeitformat nicht erkannt. Bitte so eingeben: `2 Tage`, `12 Stunden`, `30 Minuten`",
            delete_after=8
        )
    try:
        await frage2.delete()
    except Exception:
        pass

    giveaway_channel = guild.get_channel(GIVEAWAY_CHANNEL_ID)
    if giveaway_channel is None:
        await channel.send(f"{admin.mention} ❌ Giveaway-Channel nicht gefunden.", delete_after=10)
        return

    end_timestamp = int((datetime.now(timezone.utc).timestamp()) + sekunden)

    embed = discord.Embed(
        title="🎉 Giveaway!",
        color=0xF1C40F,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="🎁 Gewinn", value=gewinn,                   inline=False)
    embed.add_field(name="⏱️ Endet",  value=f"<t:{end_timestamp}:R>", inline=True)
    embed.add_field(name="📅 Datum",  value=f"<t:{end_timestamp}:F>", inline=True)
    embed.set_footer(text=f"Giveaway erstellt von {admin.display_name} • Reagiere mit 🎉 um teilzunehmen!")

    msg = await giveaway_channel.send(embed=embed)
    await msg.add_reaction("🎉")
    await channel.send(
        f"{admin.mention} ✅ **Giveaway wurde erfolgreich gepostet** in {giveaway_channel.mention}!\n"
        f"Endet: <t:{end_timestamp}:R>",
        delete_after=10
    )

    await asyncio.sleep(sekunden)

    try:
        msg = await giveaway_channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        if reaction:
            users = [u async for u in reaction.users() if not u.bot]
            if users:
                winner = random.choice(users)
                win_embed = discord.Embed(
                    title="🎉 Giveaway beendet!",
                    description=(
                        f"**Gewinn:** {gewinn}\n"
                        f"**Gewinner:** {winner.mention} 🎊\n\n"
                        f"Herzlichen Glückwunsch!"
                    ),
                    color=0xF1C40F,
                    timestamp=datetime.now(timezone.utc)
                )
                await giveaway_channel.send(content=winner.mention, embed=win_embed)
            else:
                await giveaway_channel.send("❌ Niemand hat am Giveaway teilgenommen.")
    except Exception as e:
        await log_bot_error("Giveaway-Auswertung fehlgeschlagen", str(e), guild)


@bot.tree.command(name="create-giveaway", description="[Team] Erstellt ein neues Giveaway", guild=discord.Object(id=GUILD_ID))
async def create_giveaway(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.send_message(
        "🎁 **Giveaway-Erstellung gestartet!** Beantworte die Fragen hier im Channel.",
        ephemeral=True
    )
    asyncio.create_task(create_giveaway_channel_flow(interaction.user, interaction.guild, interaction.channel))
