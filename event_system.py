# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# event_system.py \u2014 Event Erstellen System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *


async def create_event_channel_flow(admin: discord.Member, guild: discord.Guild, channel: discord.TextChannel):
    def check(m):
        return m.author.id == admin.id and m.channel.id == channel.id

    felder = [
        ("was",        "\U0001f4cb **Was ist das Event?** (z.B. Fahrzeugrennen, Bankraub, Stadtfest):"),
        ("startpunkt", "\U0001f4cd **Wo ist der Startpunkt?** (z.B. Pillbox Hill, Legion Square):"),
        ("erklaerung", "\U0001f4dd **Erkl\xe4rung / Beschreibung des Events:**"),
        ("dauer",      "\u23f1\ufe0f **Dauer des Events?** (z.B. 1 Stunde, 30 Minuten):"),
        ("preis",      "\U0001f4b0 **Preis / Belohnung?** (z.B. 50.000$, Kein Preis):"),
    ]

    antworten = {}

    for key, frage in felder:
        frage_msg = await channel.send(f"{admin.mention} {frage}")
        try:
            antwort = await bot.wait_for("message", check=check, timeout=INTERACTION_VIEW_TIMEOUT)
        except asyncio.TimeoutError:
            try:
                await frage_msg.delete()
            except Exception:
                pass
            await channel.send(f"{admin.mention} \u23f1\ufe0f Event-Erstellung abgebrochen: 5 Minuten keine Antwort.", delete_after=10)
            return
        antworten[key] = antwort.content.strip()
        try:
            await frage_msg.delete()
            await antwort.delete()
        except Exception:
            pass

    event_channel = guild.get_channel(EVENT_ANNOUNCEMENT_CHANNEL_ID)
    if event_channel is None:
        await channel.send(f"{admin.mention} \u274c Event-Channel nicht gefunden.", delete_after=10)
        return

    ping_role    = guild.get_role(EVENT_PING_ROLE_ID)
    role_mention = ping_role.mention if ping_role else ""

    embed = discord.Embed(
        title="\U0001f389 Neues Event!",
        color=0x00B4D8,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001f4cb Event",       value=antworten["was"],        inline=False)
    embed.add_field(name="\U0001f4cd Startpunkt",  value=antworten["startpunkt"], inline=True)
    embed.add_field(name="\u23f1\ufe0f Dauer",       value=antworten["dauer"],      inline=True)
    embed.add_field(name="\U0001f4b0 Preis",       value=antworten["preis"],      inline=True)
    embed.add_field(name="\U0001f4dd Beschreibung",value=antworten["erklaerung"], inline=False)
    embed.set_footer(text=f"Event erstellt von {admin.display_name}")

    await event_channel.send(content=role_mention, embed=embed)
    await channel.send(
        f"{admin.mention} \u2705 **Event wurde erfolgreich gepostet** in {event_channel.mention}!",
        delete_after=10
    )


@bot.tree.command(name="create-event", description="[Team] Erstellt ein neues Event", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def create_event(interaction: discord.Interaction):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.send_message(
        "\U0001f389 **Event-Erstellung gestartet!** Beantworte die Fragen hier im Channel.",
        ephemeral=True
    )
    asyncio.create_task(create_event_channel_flow(interaction.user, interaction.guild, interaction.channel))
