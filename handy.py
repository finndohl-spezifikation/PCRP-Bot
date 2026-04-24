# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# handy.py \u2014 Handy System (Dispatch, Nummer, Apps)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from helpers import log_bot_error
from economy_helpers import (
    has_handy, has_sim_karte, consume_sim_karte,
    load_handy_numbers, save_handy_numbers,
    generate_la_phone_number
)
from handy_games import start_tetris, start_snake
# Dispatch-Typ \u2192 Dienst-Fraktion
DISPATCH_FACTION_MAP = {
    "pd":   "lapd",
    "md":   "lamd",
    "adac": "lacs",
}


# \u2500\u2500 Dispatch Auswahlmen\u00fc \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class DispatchSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="\U0001f691 Dispatch MD",   value="md",   description="Notruf an den Medizinischen Dienst"),
            discord.SelectOption(label="\U0001f694 Dispatch PD",   value="pd",   description="Notruf an die Polizei"),
            discord.SelectOption(label="\U0001f697 Dispatch ADAC", value="adac", description="Notruf an den ADAC"),
        ]
        super().__init__(
            placeholder="\U0001f6a8 Dispatch Abschicken",
            options=options,
            custom_id="handy_dispatch_select",
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        mapping = {
            "md":   (DISPATCH_MD_ROLE_ID,   "MD"),
            "pd":   (DISPATCH_PD_ROLE_ID,   "PD"),
            "adac": (DISPATCH_ADAC_ROLE_ID, "ADAC"),
        }
        role_id, label = mapping[self.values[0]]
        await handle_dispatch(interaction, role_id, label)


# \u2500\u2500 Apps Auswahlmen\u00fc \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class AppsSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="\U0001f4f8 Instagram", value="instagram", description="Instagram installieren / deinstallieren"),
            discord.SelectOption(label="\U0001f498 Parship",   value="parship",   description="Parship installieren / deinstallieren"),
            discord.SelectOption(label="\U0001f6d2 Ebay",      value="ebay",      description="Ebay installieren / deinstallieren"),
        ]
        super().__init__(
            placeholder="\U0001f4f1 Apps",
            options=options,
            custom_id="handy_apps_select",
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        if not has_handy(interaction.user):
            await interaction.response.send_message("\u274c Du besitzt kein Handy. Kaufe es im Shop!", ephemeral=True)
            return
        mapping = {
            "instagram": (INSTAGRAM_ROLE_ID, "Instagram"),
            "parship":   (PARSHIP_ROLE_ID,   "Parship"),
            "ebay":      (EBAY_ROLE_ID,      "Ebay"),
        }
        role_id, name = mapping[self.values[0]]
        await handle_app_toggle(interaction, role_id, name)


# \u2500\u2500 Handy Einstellungen Auswahlmen\u00fc \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class EinstellungenSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="\U0001f4f1 Handy Nummer anzeigen", value="nummer",    description="Zeigt deine aktuelle Handynummer"),
            discord.SelectOption(label="\U0001f4f1 SIM Karte Wechseln",    value="sim",       description="Neue Nummer generieren (braucht SIM-Karte)"),
            discord.SelectOption(label="\u2705 Handy Einschalten",      value="handy_an",  description="Handy einschalten \u2014 du bist erreichbar"),
            discord.SelectOption(label="\u274c Handy Ausschalten",      value="handy_aus", description="Handy ausschalten \u2014 du bist nicht erreichbar"),
        ]
        super().__init__(
            placeholder="\u2699\ufe0f Handy Einstellungen",
            options=options,
            custom_id="handy_einstellungen_select",
            row=2
        )

    async def callback(self, interaction: discord.Interaction):
        if not has_handy(interaction.user):
            await interaction.response.send_message("\u274c Du besitzt kein Handy. Kaufe es im Shop!", ephemeral=True)
            return

        wahl   = self.values[0]
        guild  = interaction.guild
        member = interaction.user

        if wahl == "nummer":
            numbers = load_handy_numbers()
            uid     = str(member.id)
            if uid not in numbers:
                numbers[uid] = generate_la_phone_number()
                save_handy_numbers(numbers)
            phone = numbers[uid]
            embed = discord.Embed(
                title="\U0001f4f1 Deine Handynummer",
                description=(
                    f"**Nummer:** `{phone}`\n"
                    f"**Vorwahl:** Los Angeles (LA)\n\n"
                    f"*Du kannst deine Nummer per SIM-Wechsel \u00e4ndern.*"
                ),
                color=0xE67E22,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="Nur du siehst diese Nachricht")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif wahl == "sim":
            if not has_sim_karte(member):
                await interaction.response.send_message(
                    "\u274c Du besitzt keine SIM-Karte. Kaufe `\U0001f4f1| Sim Karte` im Shop!", ephemeral=True
                )
                return
            numbers     = load_handy_numbers()
            uid         = str(member.id)
            alte_nummer = numbers.get(uid)
            neue_nummer = generate_la_phone_number()
            while neue_nummer == alte_nummer:
                neue_nummer = generate_la_phone_number()
            numbers[uid] = neue_nummer
            save_handy_numbers(numbers)
            consume_sim_karte(member)

            embed = discord.Embed(
                title="\U0001f4f1 SIM-Karte gewechselt",
                description=(
                    f"Deine neue Handynummer lautet:\n**`{neue_nummer}`**\n\n"
                    f"Du bist unter der alten Nummer nicht mehr erreichbar."
                ),
                color=0xE67E22,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="Nur du siehst diese Nachricht")
            await interaction.response.send_message(embed=embed, ephemeral=True)

            sim_channel = guild.get_channel(SIM_WECHSEL_CHANNEL_ID)
            if sim_channel:
                public_embed = discord.Embed(
                    title="\U0001f4f1 Nummer gewechselt",
                    description=(
                        f"{member.mention} hat seine SIM-Karte gewechselt.\n\n"
                        f"Er/Sie ist unter der **alten Nummer nicht mehr erreichbar**."
                    ),
                    color=0xE67E22,
                    timestamp=datetime.now(timezone.utc)
                )
                public_embed.set_thumbnail(url=member.display_avatar.url)
                public_embed.set_footer(text="Paradise City Roleplay \u2022 SIM-System")
                try:
                    await sim_channel.send(embed=public_embed)
                except Exception:
                    pass

        elif wahl == "handy_an":
            role = guild.get_role(HANDY_AN_ROLE_ID)
            if not role:
                await interaction.response.send_message("\u274c Rolle nicht gefunden.", ephemeral=True)
                return
            if role in member.roles:
                embed = discord.Embed(description="\U0001f4f1 Dein Handy ist bereits **eingeschaltet**.", color=LOG_COLOR)
            else:
                aus_role = guild.get_role(HANDY_AUS_ROLE_ID)
                if aus_role and aus_role in member.roles:
                    await member.remove_roles(aus_role, reason="Handy eingeschaltet")
                await member.add_roles(role, reason="Handy eingeschaltet")
                embed = discord.Embed(description="\U0001f4f1 **Handy eingeschaltet!**\nDu bist jetzt erreichbar.", color=LOG_COLOR)
            embed.set_footer(text="Nur du siehst diese Nachricht")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif wahl == "handy_aus":
            role = guild.get_role(HANDY_AUS_ROLE_ID)
            if not role:
                await interaction.response.send_message("\u274c Rolle nicht gefunden.", ephemeral=True)
                return
            if role in member.roles:
                embed = discord.Embed(description="\U0001f4f1 Dein Handy ist bereits **ausgeschaltet**.", color=MOD_COLOR)
            else:
                an_role = guild.get_role(HANDY_AN_ROLE_ID)
                if an_role and an_role in member.roles:
                    await member.remove_roles(an_role, reason="Handy ausgeschaltet")
                await member.add_roles(role, reason="Handy ausgeschaltet")
                embed = discord.Embed(description="\U0001f4f1 **Handy ausgeschaltet!**\nDu bist nicht mehr erreichbar.", color=MOD_COLOR)
            embed.set_footer(text="Nur du siehst diese Nachricht")
            await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 Spiele Auswahlmen\u00fc \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class SpieleSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="\U0001f3ae Tetris", value="tetris", description="Tetris spielen \u2014 Steine stapeln!"),
            discord.SelectOption(label="\U0001f40d Snake",  value="snake",  description="Snake spielen \u2014 Apfel fressen!"),
        ]
        super().__init__(
            placeholder="\U0001f3ae Spiele",
            options=options,
            custom_id="handy_spiele_select",
            row=3,
        )

    async def callback(self, interaction: discord.Interaction):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "\u274c Du besitzt kein Handy. Kaufe es im Shop!", ephemeral=True
            )
            return
        an_role = interaction.guild.get_role(HANDY_AN_ROLE_ID)
        if not an_role or an_role not in interaction.user.roles:
            await interaction.response.send_message(
                "\u274c Dein Handy ist **ausgeschaltet**!\nSchalte es zuerst unter \u2699\ufe0f Handy Einstellungen ein.",
                ephemeral=True,
            )
            return
        if self.values[0] == "tetris":
            await start_tetris(interaction)
        else:
            await start_snake(interaction)


# \u2500\u2500 Haupt-View \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class HandyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DispatchSelect())
        self.add_item(AppsSelect())
        self.add_item(EinstellungenSelect())
        self.add_item(SpieleSelect())


async def handle_app_toggle(interaction: discord.Interaction, role_id: int, app_name: str):
    guild  = interaction.guild
    member = interaction.user
    role   = guild.get_role(role_id)
    if not role:
        await interaction.response.send_message(f"\u274c {app_name}-Rolle nicht gefunden.", ephemeral=True)
        return

    if role in member.roles:
        await member.remove_roles(role, reason=f"Handy: {app_name} deinstalliert")
        embed = discord.Embed(
            description=f"\U0001f4f1 **App Erfolgreich Deinstalliert**\n{app_name} wurde von deinem Handy entfernt.",
            color=MOD_COLOR
        )
    else:
        await member.add_roles(role, reason=f"Handy: {app_name} installiert")
        embed = discord.Embed(
            description=f"\U0001f4f1 **App Erfolgreich Installiert**\n{app_name} wurde auf deinem Handy installiert.",
            color=LOG_COLOR
        )
    embed.set_footer(text="Nur du siehst diese Nachricht")
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def handle_dispatch(interaction: discord.Interaction, role_id: int, dispatch_type: str):
    if not has_handy(interaction.user):
        await interaction.response.send_message(
            "\u274c Du besitzt kein Handy. Kaufe es im Shop!",
            ephemeral=True
        )
        return

    guild  = interaction.guild
    member = interaction.user

    await interaction.response.defer(ephemeral=True)

    # Wer ist aktuell im Dienst? (Lazy import vermeidet zirkul\u00e4ren Import)
    from dienst import get_on_duty
    faction    = DISPATCH_FACTION_MAP.get(dispatch_type.lower(), None)
    on_duty    = get_on_duty(faction) if faction else {}
    now_ts     = int(datetime.now(timezone.utc).timestamp())

    dispatch_embed = discord.Embed(
        title="\U0001f6a8 Dispatch \U0001f6a8",
        description=(
            f"**Ein Bewohner hat einen Dispatch abgesendet!**\n\n"
            f"\U0001f5fa\ufe0f **Von:** {member.mention}\n"
            f"\U0001f4cb **Dispatch-Typ:** {dispatch_type}\n"
            f"\u23f0 **Zeit:** <t:{now_ts}:T>\n"
            f"\U0001f46e **Einheiten im Dienst:** {len(on_duty)}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    dispatch_embed.set_footer(text="Paradise City Roleplay \u2022 Dispatch-System")

    sent   = 0
    failed = 0

    for uid in on_duty:
        target = guild.get_member(int(uid))
        if not target or target.bot:
            continue
        try:
            await target.send(embed=dispatch_embed)
            sent += 1
        except Exception:
            failed += 1

    confirm_embed = discord.Embed(
        title="\u2705 Dispatch gesendet!",
        description=(
            f"Dein **{dispatch_type}-Dispatch** wurde erfolgreich abgesendet.\n"
            f"**Einheiten im Dienst:** {len(on_duty)}\n"
            f"**Benachrichtigt:** {sent} Einheit{'en' if sent != 1 else ''}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    confirm_embed.set_footer(text="Paradise City Roleplay \u2022 Dispatch-System")
    await interaction.followup.send(embed=confirm_embed, ephemeral=True)


def _build_handy_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\U0001f4f1 Handy \u2014 Einstellungen",
        description=(
            "Willkommen in deinen Handy-Einstellungen!\n\n"
            "**\U0001f6a8 Dispatch-Buttons** \u2014 Sende einen Notruf an die zust\u00e4ndige Einheit\n"
            "**\U0001f4f1 Handy Nummer** \u2014 Zeigt deine pers\u00f6nliche LA-Nummer\n"
            "**\U0001f4f1 SIM Karte Wechseln** \u2014 Neue Nummer generieren & \u00f6ffentlich ank\u00fcndigen\n"
            "**\U0001f4f1 Handy Einschalten / Aus** \u2014 Erreichbarkeit steuern\n"
            "**\U0001f4f1 Instagram / Parship / Ebay** \u2014 Apps installieren & deinstallieren\n"
            "**\U0001f3ae Tetris / \U0001f40d Snake** \u2014 Spiele direkt auf deinem Handy *(nur wenn Handy AN)*\n\n"
            "\u26a0\ufe0f *Du ben\u00f6tigst das Item* `\U0001f4f1| Handy` *aus dem Shop, um diese Funktionen zu nutzen.*"
        ),
        color=0xE67E22,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Handy-System")
    return embed


async def auto_handy_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(HANDY_CHANNEL_ID)
        if not channel:
            continue

        existing_msg = None
        try:
            async for msg in channel.history(limit=30):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Handy" in emb.title:
                            existing_msg = msg
                            break
                if existing_msg:
                    break
        except Exception:
            pass

        embed = _build_handy_embed()
        try:
            if existing_msg:
                await existing_msg.edit(embed=embed, view=HandyView())
                print(f"Handy-Embed aktualisiert in #{channel.name}")
            else:
                await channel.send(embed=embed, view=HandyView())
                print(f"Handy-Embed gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_handy_setup fehlgeschlagen", str(e), guild)


async def give_handy_channel_access(guild: discord.Guild, member: discord.Member):
    channel = guild.get_channel(HANDY_CHANNEL_ID)
    if not channel:
        return
    try:
        await channel.set_permissions(
            member,
            view_channel=True,
            send_messages=False,
            read_message_history=True
        )
    except Exception as e:
        await log_bot_error("Handy-Kanal Berechtigung fehlgeschlagen", str(e), guild)
