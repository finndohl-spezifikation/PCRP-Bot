# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# giveaway.py \u2014 Giveaway System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

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

    frage1 = await channel.send(f"{admin.mention} \U0001F381 **Was wird verlost?** (z.B. 500.000$, Fahrzeug, Item):")
    try:
        antwort1 = await bot.wait_for("message", check=check, timeout=INTERACTION_VIEW_TIMEOUT)
    except asyncio.TimeoutError:
        try:
            await frage1.delete()
        except Exception:
            pass
        await channel.send(f"{admin.mention} \u23F1\uFE0F Giveaway-Erstellung abgebrochen: 5 Minuten keine Antwort.", delete_after=10)
        return
    gewinn = antwort1.content.strip()
    try:
        await frage1.delete()
        await antwort1.delete()
    except Exception:
        pass

    frage2 = await channel.send(f"{admin.mention} \u23F1\uFE0F **Wie lange l\u00E4uft das Giveaway?** (z.B. `2 Tage`, `12 Stunden`, `30 Minuten`):")
    while True:
        try:
            antwort2 = await bot.wait_for("message", check=check, timeout=INTERACTION_VIEW_TIMEOUT)
        except asyncio.TimeoutError:
            try:
                await frage2.delete()
            except Exception:
                pass
            await channel.send(f"{admin.mention} \u23F1\uFE0F Giveaway-Erstellung abgebrochen: 5 Minuten keine Antwort.", delete_after=10)
            return
        laufzeit_text = antwort2.content.strip()
        sekunden     = parse_dauer_zu_sekunden(laufzeit_text)
        try:
            await antwort2.delete()
        except Exception:
            pass
        if sekunden and sekunden > 0:
            break
        await channel.send(
            f"{admin.mention} \u274C Zeitformat nicht erkannt. Bitte so eingeben: `2 Tage`, `12 Stunden`, `30 Minuten`",
            delete_after=8
        )
    try:
        await frage2.delete()
    except Exception:
        pass

    giveaway_channel = guild.get_channel(GIVEAWAY_CHANNEL_ID)
    if giveaway_channel is None:
        await channel.send(f"{admin.mention} \u274C Giveaway-Channel nicht gefunden.", delete_after=10)
        return

    end_timestamp = int((datetime.now(timezone.utc).timestamp()) + sekunden)

    embed = discord.Embed(
        title="\U0001F389 Giveaway gestartet!",
        description=(
            f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
            f"\u27A4 Reagiere mit \U0001F389 um teilzunehmen!\n"
            f"\u26A0\uFE0F Nur Spieler mit der B\u00FCrger-Rolle d\u00FCrfen mitmachen."
        ),
        color=0xF1C40F,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F381 Gewinn",    value=f"**{gewinn}**",              inline=False)
    embed.add_field(name="\u23F1\uFE0F Endet",   value=f"<t:{end_timestamp}:R>",    inline=True)
    embed.add_field(name="\U0001F4C5 Datum",     value=f"<t:{end_timestamp}:F>",    inline=True)
    embed.set_footer(text=f"\U0001F3AE Paradise City Roleplay \u2022 Giveaway von {admin.display_name}")

    msg = await giveaway_channel.send(embed=embed)
    await msg.add_reaction("\U0001F389")
    await channel.send(
        f"{admin.mention} \u2705 **Giveaway wurde erfolgreich gepostet** in {giveaway_channel.mention}!\n"
        f"Endet: <t:{end_timestamp}:R>",
        delete_after=10
    )

    await asyncio.sleep(sekunden)

    try:
        msg = await giveaway_channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji="\U0001F389")
        if reaction:
            teilnehmer = []
            async for u in reaction.users():
                if u.bot:
                    continue
                member = guild.get_member(u.id)
                if member and any(r.id == CITIZEN_ROLE_ID for r in member.roles):
                    teilnehmer.append(u)
            if teilnehmer:
                winner = random.choice(teilnehmer)
                win_embed = discord.Embed(
                    title="\U0001F389 Giveaway beendet!",
                    description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
                    color=0xF1C40F,
                    timestamp=datetime.now(timezone.utc)
                )
                win_embed.add_field(name="\U0001F381 Gewinn",         value=f"**{gewinn}**",      inline=False)
                win_embed.add_field(name="\U0001F947 Gewinner",       value=winner.mention,        inline=True)
                win_embed.add_field(name="\U0001F465 Teilnehmer",     value=str(len(teilnehmer)),  inline=True)
                win_embed.set_thumbnail(url=winner.display_avatar.url if hasattr(winner, "display_avatar") else discord.Embed.Empty)
                win_embed.set_footer(text="\U0001F3AE Paradise City Roleplay \u2022 Giveaway-System")
                await giveaway_channel.send(content=winner.mention, embed=win_embed)
            else:
                await giveaway_channel.send(
                    "\u274C Kein berechtigter Teilnehmer (ben\u00F6tigt: B\u00FCrger-Rolle)."
                )
    except Exception as e:
        await log_bot_error("Giveaway-Auswertung fehlgeschlagen", str(e), guild)


@bot.tree.command(name="create-giveaway", description="[Team] Erstellt ein neues Giveaway", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def create_giveaway(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.send_message(
        "\U0001F381 **Giveaway-Erstellung gestartet!** Beantworte die Fragen hier im Channel.",
        ephemeral=True
    )
    asyncio.create_task(create_giveaway_channel_flow(interaction.user, interaction.guild, interaction.channel))
