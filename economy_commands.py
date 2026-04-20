# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# economy_commands.py \u2014 Economy Slash Commands (Konto, Lohn, etc.)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from helpers import is_admin
from economy_helpers import (
    load_economy, save_economy, get_user, reset_daily_if_needed,
    has_citizen_or_wage, betrag_autocomplete, log_money_action, channel_error
)


# \u2500\u2500 Betrag-Parser (z. B. "1.000" \u2192 1000) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def parse_betrag(text: str) -> int | None:
    try:
        return int(text.replace(".", "").replace(",", "").strip())
    except ValueError:
        return None


# \u2500\u2500 Modals \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class EinzahlenModal(discord.ui.Modal, title="\U0001F3E6 Einzahlen"):
    betrag_input = discord.ui.TextInput(
        label="Betrag (\U0001F4B5)",
        placeholder="z. B. 5000",
        min_length=1,
        max_length=12,
    )

    async def on_submit(self, interaction: discord.Interaction):
        betrag = parse_betrag(self.betrag_input.value)
        if betrag is None or betrag <= 0:
            await interaction.response.send_message("\u274C Ung\u00FCltiger Betrag.", ephemeral=True)
            return

        role_ids = [r.id for r in interaction.user.roles]
        is_adm   = ADMIN_ROLE_ID in role_ids

        if not is_adm and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
            return

        eco       = load_economy()
        user_data = get_user(eco, interaction.user.id)
        reset_daily_if_needed(user_data)

        if user_data["cash"] < betrag:
            await interaction.response.send_message(
                f"\u274C Nicht genug Bargeld. Dein Bargeld: **{user_data['cash']:,} \U0001F4B5**", ephemeral=True
            )
            return

        if not is_adm:
            user_limit = user_data.get("custom_limit") or DAILY_LIMIT
            remaining  = user_limit - user_data["daily_deposit"]
            if betrag > remaining:
                await interaction.response.send_message(
                    f"\u274C Tageslimit erreicht. Du kannst heute noch **{remaining:,} \U0001F4B5** einzahlen. "
                    f"(Limit: **{user_limit:,} \U0001F4B5**)",
                    ephemeral=True
                )
                return
            user_data["daily_deposit"] += betrag

        user_data["cash"] -= betrag
        user_data["bank"] += betrag
        save_economy(eco)
        await log_money_action(
            interaction.guild,
            "Einzahlung",
            f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} \U0001F4B5\n"
            f"**Bargeld danach:** {user_data['cash']:,} \U0001F4B5 | **Bank danach:** {user_data['bank']:,} \U0001F4B5"
        )

        embed = discord.Embed(
            title="\U0001F3E6 Einzahlung erfolgreich",
            description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F4B8 Eingezahlt",  value=f"**{betrag:,} $**",             inline=True)
        embed.add_field(name="\U0001F4B5 Bargeld",     value=f"{user_data['cash']:,} $",       inline=True)
        embed.add_field(name="\U0001F3E6 Bank",        value=f"{user_data['bank']:,} $",       inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="\U0001F3DB\uFE0F Maze Bank \u2022 Paradise City Roleplay")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class AuszahlenModal(discord.ui.Modal, title="\U0001F4B8 Auszahlen"):
    betrag_input = discord.ui.TextInput(
        label="Betrag (\U0001F4B5)",
        placeholder="z. B. 5000",
        min_length=1,
        max_length=12,
    )

    async def on_submit(self, interaction: discord.Interaction):
        betrag = parse_betrag(self.betrag_input.value)
        if betrag is None or betrag <= 0:
            await interaction.response.send_message("\u274C Ung\u00FCltiger Betrag.", ephemeral=True)
            return

        role_ids = [r.id for r in interaction.user.roles]
        is_adm   = ADMIN_ROLE_ID in role_ids

        if not is_adm and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
            return

        eco       = load_economy()
        user_data = get_user(eco, interaction.user.id)
        reset_daily_if_needed(user_data)

        dispo_limit = user_data.get("dispo", 0)
        if user_data["bank"] + dispo_limit < betrag:
            if dispo_limit > 0:
                await interaction.response.send_message(
                    f"\u274C Nicht genug Guthaben. \U0001F3E6 **Konto:** {user_data['bank']:,} \U0001F4B5 | \U0001F4CA **Dispo:** -{dispo_limit:,} \U0001F4B5",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"\u274C Nicht genug Guthaben. \U0001F3E6 **Konto:** {user_data['bank']:,} \U0001F4B5", ephemeral=True
                )
            return

        if not is_adm:
            user_limit = user_data.get("custom_limit") or DAILY_LIMIT
            remaining  = user_limit - user_data["daily_withdraw"]
            if betrag > remaining:
                await interaction.response.send_message(
                    f"\u274C Tageslimit erreicht. Du kannst heute noch **{remaining:,} \U0001F4B5** auszahlen. "
                    f"(Limit: **{user_limit:,} \U0001F4B5**)",
                    ephemeral=True
                )
                return
            user_data["daily_withdraw"] += betrag

        user_data["bank"] -= betrag
        user_data["cash"] += betrag
        save_economy(eco)
        await log_money_action(
            interaction.guild,
            "Auszahlung",
            f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} \U0001F4B5\n"
            f"**Bargeld danach:** {user_data['cash']:,} \U0001F4B5 | **Bank danach:** {user_data['bank']:,} \U0001F4B5"
        )

        embed = discord.Embed(
            title="\U0001F4B8 Auszahlung erfolgreich",
            description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F4B8 Ausgezahlt", value=f"**{betrag:,} $**",       inline=True)
        embed.add_field(name="\U0001F4B5 Bargeld",    value=f"{user_data['cash']:,} $", inline=True)
        embed.add_field(name="\U0001F3E6 Bank",       value=f"{user_data['bank']:,} $", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="\U0001F3DB\uFE0F Maze Bank \u2022 Paradise City Roleplay")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class UeberweisungsBetragModal(discord.ui.Modal, title="\U0001F4B3 \u00DCberweisen"):
    betrag_input = discord.ui.TextInput(
        label="Betrag (\U0001F4B5)",
        placeholder="z. B. 5000",
        min_length=1,
        max_length=12,
    )

    def __init__(self, ziel: discord.Member):
        super().__init__()
        self.ziel = ziel

    async def on_submit(self, interaction: discord.Interaction):
        betrag = parse_betrag(self.betrag_input.value)
        if betrag is None or betrag <= 0:
            await interaction.response.send_message("\u274C Ung\u00FCltiger Betrag.", ephemeral=True)
            return

        role_ids = [r.id for r in interaction.user.roles]
        is_adm   = ADMIN_ROLE_ID in role_ids

        if not is_adm and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
            return

        eco      = load_economy()
        sender   = get_user(eco, interaction.user.id)
        receiver = get_user(eco, self.ziel.id)
        reset_daily_if_needed(sender)

        if sender["bank"] < betrag:
            await interaction.response.send_message(
                f"\u274C Nicht genug Guthaben. Dein Kontostand: **{sender['bank']:,} \U0001F4B5**", ephemeral=True
            )
            return

        if not is_adm:
            user_limit = sender.get("custom_limit") or DAILY_LIMIT
            remaining  = user_limit - sender["daily_transfer"]
            if betrag > remaining:
                await interaction.response.send_message(
                    f"\u274C Tageslimit erreicht. Du kannst heute noch **{remaining:,} \U0001F4B5** \u00FCberweisen. "
                    f"(Limit: **{user_limit:,} \U0001F4B5**)",
                    ephemeral=True
                )
                return
            sender["daily_transfer"] += betrag

        sender["bank"]   -= betrag
        receiver["bank"] += betrag
        save_economy(eco)
        await log_money_action(
            interaction.guild,
            "\u00DCberweisung",
            f"**Von:** {interaction.user.mention} \u2192 **An:** {self.ziel.mention}\n"
            f"**Betrag:** {betrag:,} \U0001F4B5 | **Sender-Bank danach:** {sender['bank']:,} \U0001F4B5"
        )

        embed = discord.Embed(
            title="\U0001F4B3 \u00DCberweisung erfolgreich",
            description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F4E4 An",          value=self.ziel.mention,          inline=True)
        embed.add_field(name="\U0001F4B0 Betrag",      value=f"**{betrag:,} $**",        inline=True)
        embed.add_field(name="\U0001F3E6 Dein Konto",  value=f"{sender['bank']:,} $",    inline=True)
        embed.set_thumbnail(url=self.ziel.display_avatar.url)
        embed.set_footer(text="\U0001F3DB\uFE0F Maze Bank \u2022 Paradise City Roleplay")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class EmpfaengerAuswahlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Empf\u00E4nger ausw\u00E4hlen...",
        min_values=1,
        max_values=1,
    )
    async def select_empfaenger(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        ziel = select.values[0]
        if ziel.bot:
            await interaction.response.send_message("\u274C Du kannst nicht an einen Bot \u00FCberweisen.", ephemeral=True)
            return
        if ziel.id == interaction.user.id:
            await interaction.response.send_message("\u274C Du kannst nicht an dich selbst \u00FCberweisen.", ephemeral=True)
            return
        await interaction.response.send_modal(UeberweisungsBetragModal(ziel))


# \u2500\u2500 Kontostand View (Buttons) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class KontostandView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Einzahlen", emoji="\U0001F3E6", style=discord.ButtonStyle.success)
    async def einzahlen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_citizen_or_wage(interaction.user) and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
            return
        await interaction.response.send_modal(EinzahlenModal())

    @discord.ui.button(label="Auszahlen", emoji="\U0001F4B8", style=discord.ButtonStyle.danger)
    async def auszahlen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_citizen_or_wage(interaction.user) and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
            return
        await interaction.response.send_modal(AuszahlenModal())

    @discord.ui.button(label="\u00DCberweisen", emoji="\U0001F4B3", style=discord.ButtonStyle.primary)
    async def ueberweisen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_citizen_or_wage(interaction.user) and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
            return
        await interaction.response.send_message(
            "**\U0001F4B3 An wen m\u00F6chtest du \u00FCberweisen?**\nW\u00E4hle den Empf\u00E4nger aus der Liste:",
            view=EmpfaengerAuswahlView(),
            ephemeral=True,
        )


# \u2500\u2500 /lohn-abholen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="lohn-abholen", description="[Konto] Hole deinen st\u00FCndlichen Lohn ab", guild=discord.Object(id=GUILD_ID))
async def lohn_abholen(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids or INHABER_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != LOHN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(LOHN_CHANNEL_ID), ephemeral=True)
        return

    main_wages = [WAGE_ROLES[r] for r in role_ids if r in WAGE_ROLES]
    if len(main_wages) > 1:
        await interaction.response.send_message(
            "\u274C Du hast mehrere Lohnklassen. Bitte wende dich ans Team.", ephemeral=True
        )
        return
    if not main_wages:
        await interaction.response.send_message(
            "\u274C Du hast keine Lohnklasse und kannst keinen Lohn abholen.", ephemeral=True
        )
        return

    total_wage = main_wages[0]
    if ADDITIONAL_WAGE_ROLE_ID in role_ids:
        total_wage += ADDITIONAL_WAGE_ROLE_WAGE

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    now       = datetime.now(timezone.utc)

    if user_data["last_wage"]:
        last = datetime.fromisoformat(user_data["last_wage"])
        diff = (now - last).total_seconds()
        if diff < 3600:
            remaining = int(3600 - diff)
            mins = remaining // 60
            secs = remaining % 60
            await interaction.response.send_message(
                f"\u274C Du kannst deinen Lohn erst in **{mins}m {secs}s** wieder abholen.",
                ephemeral=True
            )
            return

    user_data["bank"]      += total_wage
    user_data["last_wage"]  = now.isoformat()
    save_economy(eco)

    embed = discord.Embed(
        title="\U0001F4B5 Lohn abgeholt!",
        description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
        color=0x2ECC71,
        timestamp=now
    )
    embed.add_field(name="\U0001F4B0 Lohn",    value=f"**+{total_wage:,} $**",        inline=True)
    embed.add_field(name="\U0001F3E6 Konto",   value=f"{user_data['bank']:,} $",      inline=True)
    embed.add_field(name="\u23F0 N\u00E4chster Lohn", value="in 1 Stunde",            inline=True)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="\U0001F4BC Lohnb\u00FCro \u2022 Paradise City Roleplay")
    await interaction.response.send_message(embed=embed)


# \u2500\u2500 /konto \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="konto", description="[Konto] Zeigt den Kontostand an", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Mitglied dessen Kontostand abgerufen werden soll")
async def kontostand(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids  = [r.id for r in interaction.user.roles]
    is_adm    = ADMIN_ROLE_ID in role_ids or INHABER_ROLE_ID in role_ids
    is_team_m = is_adm or MOD_ROLE_ID in role_ids

    if nutzer is not None:
        if not is_team_m:
            await interaction.response.send_message(
                "\u274C Du hast keine Berechtigung, den Kontostand anderer Mitglieder abzurufen.",
                ephemeral=True
            )
            return
        ziel      = nutzer
        show_btns = False
    else:
        if not is_team_m and interaction.channel.id != BANK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
            return
        if not is_team_m and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
            return
        ziel      = interaction.user
        show_btns = True

    eco       = load_economy()
    user_data = get_user(eco, ziel.id)
    save_economy(eco)

    dispo     = user_data.get("dispo", 0)
    titel = "\U0001F4B3 Kontostand" if ziel.id == interaction.user.id else f"\U0001F4B3 Kontostand \u2014 {ziel.display_name}"
    desc  = (
        f"\U0001F4B5 **Bargeld:** {int(user_data['cash']):,} \U0001F4B5\n"
        f"\U0001F3E6 **Konto:** {int(user_data['bank']):,} \U0001F4B5\n"
        f"\U0001F4B0 **Gesamt:** {int(user_data['cash']) + int(user_data['bank']):,} \U0001F4B5"
    )
    if dispo > 0:
        desc += f"\n\U0001F4CA **Dispo:** bis -{dispo:,} \U0001F4B5"
    embed = discord.Embed(
        title=titel,
        description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F4B5 Bargeld",  value=f"{int(user_data['cash']):,} $",                              inline=True)
    embed.add_field(name="\U0001F3E6 Bank",     value=f"{int(user_data['bank']):,} $",                              inline=True)
    embed.add_field(name="\U0001F4B0 Gesamt",   value=f"**{int(user_data['cash'])+int(user_data['bank']):,} $**",   inline=True)
    if dispo > 0:
        embed.add_field(name="\U0001F4CA Dispo", value=f"bis -{dispo:,} $", inline=True)
    embed.set_thumbnail(url=ziel.display_avatar.url)
    embed.set_footer(text="\U0001F3DB\uFE0F Maze Bank \u2022 Paradise City Roleplay")

    view = KontostandView() if show_btns else None
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# \u2500\u2500 /money-add \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="money-add", description="[Admin] F\u00FCge einem Spieler Geld hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
async def money_add(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("\u274C Betrag muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld hinzugef\u00FCgt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** +{betrag:,} \U0001F4B5\n"
        f"**Bank danach:** {user_data['bank']:,} \U0001F4B5\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="\U0001F4B0 Geld hinzugef\u00FCgt",
        description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F464 Spieler",        value=nutzer.mention,              inline=True)
    embed.add_field(name="\U0001F4B0 Hinzugef\u00FCgt", value=f"**+{betrag:,} $**",     inline=True)
    embed.add_field(name="\U0001F3E6 Bank danach",    value=f"{user_data['bank']:,} $",  inline=True)
    embed.set_thumbnail(url=nutzer.display_avatar.url)
    embed.set_footer(text=f"\u2699\uFE0F Admin: {interaction.user.display_name} \u2022 Paradise City Roleplay")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 /remove-money \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="remove-money", description="[Admin] Entferne Geld von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
async def remove_money(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("\u274C Betrag muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] = max(0, user_data["cash"] - betrag)
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld entfernt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** -{betrag:,} \U0001F4B5\n"
        f"**Bargeld danach:** {user_data['cash']:,} \U0001F4B5\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="\U0001F4B8 Geld entfernt",
        description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F464 Spieler",     value=nutzer.mention,              inline=True)
    embed.add_field(name="\U0001F4B8 Entfernt",    value=f"**-{betrag:,} $**",        inline=True)
    embed.add_field(name="\U0001F4B5 Bargeld",     value=f"{user_data['cash']:,} $",  inline=True)
    embed.set_thumbnail(url=nutzer.display_avatar.url)
    embed.set_footer(text=f"\u2699\uFE0F Admin: {interaction.user.display_name} \u2022 Paradise City Roleplay")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 /set-limit \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="set-limit", description="[Team] Setzt das individuelle Tageslimit eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", limit="Neues Tageslimit")
@app_commands.choices(limit=LIMIT_CHOICES)
async def set_limit(interaction: discord.Interaction, nutzer: discord.Member, limit: int):
    role_ids = [r.id for r in interaction.user.roles]
    if ADMIN_ROLE_ID not in role_ids and MOD_ROLE_ID not in role_ids:
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["custom_limit"] = limit
    save_economy(eco)

    embed = discord.Embed(
        title="\u2699\uFE0F Tageslimit gesetzt",
        description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
        color=0x9B59B6,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F464 Spieler",      value=nutzer.mention,       inline=True)
    embed.add_field(name="\U0001F4CA Tageslimit",   value=f"**{limit:,} $**",   inline=True)
    embed.add_field(name="\U0001F4CB Gilt f\u00FCr", value="Ein \u2022 Aus \u2022 Transfer", inline=True)
    embed.set_thumbnail(url=nutzer.display_avatar.url)
    embed.set_footer(text=f"\u2699\uFE0F Team: {interaction.user.display_name} \u2022 Paradise City Roleplay")
    await interaction.response.send_message(embed=embed)


# \u2500\u2500 /dispo \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="dispo", description="[Admin] Setzt das Dispo-Limit eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler", betrag="Maximales Minus-Limit in $ (0 = kein Dispo)")
async def dispo_cmd(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    if betrag < 0:
        await interaction.response.send_message("\u274C Betrag muss 0 oder gr\u00F6\u00DFer sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["dispo"] = betrag
    save_economy(eco)

    await log_money_action(
        interaction.guild,
        "Admin: Dispo gesetzt",
        f"**Spieler:** {nutzer.mention}\n"
        f"**Dispo-Limit:** -{betrag:,} \U0001F4B5\n"
        f"**Gesetzt von:** {interaction.user.mention}"
    )

    if betrag == 0:
        beschreibung = (
            f"**Spieler:** {nutzer.mention}\n"
            f"**Dispo:** deaktiviert\n"
            f"*(Konto kann nicht mehr ins Minus gehen)*"
        )
    else:
        beschreibung = (
            f"**Spieler:** {nutzer.mention}\n"
            f"**Dispo-Limit:** bis -{betrag:,} \U0001F4B5\n"
            f"*(Konto darf bis zu diesem Betrag ins Minus gehen)*"
        )

    embed = discord.Embed(
        title="\U0001F4CA Dispo gesetzt",
        description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
        color=0x9B59B6,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F464 Spieler",   value=nutzer.mention,      inline=True)
    embed.add_field(name="\U0001F4CA Dispo",     value=f"**-{dispo:,} $**", inline=True)
    embed.add_field(name="\U0001F4CB Info",      value=beschreibung,        inline=False)
    embed.set_thumbnail(url=nutzer.display_avatar.url)
    embed.set_footer(text=f"\u2699\uFE0F Admin: {interaction.user.display_name} \u2022 Paradise City Roleplay")
    await interaction.response.send_message(embed=embed)


# \u2500\u2500 /raub-cooldown \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_RAUB_CHOICES = [
    app_commands.Choice(name="\U0001F37A Bar-Raub\u00FCberfall",  value="raub_last_raid"),
    app_commands.Choice(name="\U0001F3E7 ATM-Raub",              value="atm_last_raid"),
    app_commands.Choice(name="\U0001F6D2 Shop-Raub",             value="shop_raub_last_raid"),
    app_commands.Choice(name="\U0001F9EA Humane Labs",            value="hl_last_raid"),
    app_commands.Choice(name="\U0001F3E6 Staatsbank",             value="sb_last_raid"),
]

@bot.tree.command(name="raub-cooldown", description="[Admin] Entfernt den 24h Raub-Cooldown eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler dessen Raub-Cooldown zur\u00FCckgesetzt werden soll", raub="Welcher Raub-Cooldown?")
@app_commands.choices(raub=_RAUB_CHOICES)
async def raub_cooldown_reset(interaction: discord.Interaction, nutzer: discord.Member, raub: app_commands.Choice[str]):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)

    if not user_data.get(raub.value):
        await interaction.response.send_message(
            f"\u2139\uFE0F {nutzer.mention} hat aktuell keinen aktiven Cooldown f\u00FCr **{raub.name}**.",
            ephemeral=True
        )
        return

    user_data[raub.value] = None
    save_economy(eco)

    await log_money_action(
        interaction.guild,
        "Admin: Raub-Cooldown zur\u00FCckgesetzt",
        f"**Spieler:** {nutzer.mention}\n**Raub:** {raub.name}\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="\u23F1\uFE0F Raub-Cooldown zur\u00FCckgesetzt",
        description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F464 Spieler",  value=nutzer.mention, inline=True)
    embed.add_field(name="\U0001F52B Raub",     value=raub.name,      inline=True)
    embed.add_field(name="\u2705 Status",       value="Sofort wieder m\u00F6glich", inline=True)
    embed.set_thumbnail(url=nutzer.display_avatar.url)
    embed.set_footer(text=f"\u2699\uFE0F Admin: {interaction.user.display_name} \u2022 Paradise City Roleplay")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 Hilfsfunktion: Nur Server-Inhaber oder Bot-Inhaber \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _nur_inhaber(interaction: discord.Interaction) -> bool:
    if interaction.guild and interaction.guild.owner_id == interaction.user.id:
        return True
    try:
        info = await bot.application_info()
        owner_ids = {m.id for m in info.team.members} if info.team else {info.owner.id}
        return interaction.user.id in owner_ids
    except Exception:
        return False


# \u2500\u2500 /money-reset \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="money-reset",
    description="[Inhaber] Setzt Bargeld & Bank auf 0 \u2014 einzeln oder alle Spieler",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Einzelner Spieler (leer = ALLE zur\u00FCcksetzen)")
async def money_reset(interaction: discord.Interaction, nutzer: discord.Member = None):
    if not await _nur_inhaber(interaction):
        await interaction.response.send_message(
            "\u274C Nur der Server-Inhaber oder Bot-Inhaber kann diesen Command nutzen.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    eco = load_economy()

    if nutzer:
        ud = get_user(eco, nutzer.id)
        ud["cash"] = 0
        ud["bank"] = 0
        save_economy(eco)
        embed = discord.Embed(
            title="\U0001F4B8 Konto zur\u00FCckgesetzt",
            description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F464 Spieler",   value=nutzer.mention, inline=True)
        embed.add_field(name="\U0001F4B5 Bargeld",   value="**$0**",       inline=True)
        embed.add_field(name="\U0001F3E6 Bank",      value="**$0**",       inline=True)
        embed.set_thumbnail(url=nutzer.display_avatar.url)
        embed.set_footer(text=f"\U0001F451 {interaction.user.display_name} \u2022 Paradise City Roleplay")
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        count = sum(1 for ud in eco.values() if isinstance(ud, dict) and (ud.update({"cash": 0, "bank": 0}) or True))
        save_economy(eco)
        embed = discord.Embed(
            title="\U0001F4B8 Alle Konten zur\u00FCckgesetzt",
            description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F465 Betroffene",   value=f"**{count} Spieler**", inline=True)
        embed.add_field(name="\U0001F4B5 Bargeld",      value="**$0**",               inline=True)
        embed.add_field(name="\U0001F3E6 Bank",         value="**$0**",               inline=True)
        embed.set_footer(text=f"\U0001F451 {interaction.user.display_name} \u2022 Paradise City Roleplay")
        await interaction.followup.send(embed=embed, ephemeral=True)


# \u2500\u2500 /inventar-reset \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="inventar-reset",
    description="[Inhaber] Leert Inventar & Lager \u2014 einzeln oder alle Spieler",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Einzelner Spieler (leer = ALLE zur\u00FCcksetzen)")
async def inventar_reset(interaction: discord.Interaction, nutzer: discord.Member = None):
    if not await _nur_inhaber(interaction):
        await interaction.response.send_message(
            "\u274C Nur der Server-Inhaber oder Bot-Inhaber kann diesen Command nutzen.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    eco = load_economy()

    if nutzer:
        ud = get_user(eco, nutzer.id)
        ud["inventory"] = []
        ud["lager"]     = []
        save_economy(eco)
        embed = discord.Embed(
            title="\U0001F392 Inventar zur\u00FCckgesetzt",
            description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F464 Spieler",    value=nutzer.mention, inline=True)
        embed.add_field(name="\U0001F392 Rucksack",   value="**Geleert**",  inline=True)
        embed.add_field(name="\U0001F3E0 Lager",      value="**Geleert**",  inline=True)
        embed.set_thumbnail(url=nutzer.display_avatar.url)
        embed.set_footer(text=f"\U0001F451 {interaction.user.display_name} \u2022 Paradise City Roleplay")
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        count = 0
        for ud in eco.values():
            if isinstance(ud, dict):
                ud["inventory"] = []
                ud["lager"]     = []
                count += 1
        save_economy(eco)
        embed = discord.Embed(
            title="\U0001F392 Alle Inventare zur\u00FCckgesetzt",
            description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F465 Betroffene",  value=f"**{count} Spieler**", inline=True)
        embed.add_field(name="\U0001F392 Rucksack",    value="**Geleert**",          inline=True)
        embed.add_field(name="\U0001F3E0 Lager",       value="**Geleert**",          inline=True)
        embed.set_footer(text=f"\U0001F451 {interaction.user.display_name} \u2022 Paradise City Roleplay")
        await interaction.followup.send(embed=embed, ephemeral=True)


# \u2500\u2500 /hard-reset \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="hard-reset",
    description="[Inhaber] Setzt ALLE Kontost\u00E4nde + Inventare aller Spieler auf 0",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
async def hard_reset(interaction: discord.Interaction):
    if not await _nur_inhaber(interaction):
        await interaction.response.send_message(
            "\u274C Nur der Server-Inhaber oder Bot-Inhaber kann diesen Command nutzen.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    eco   = load_economy()
    count = 0
    for ud in eco.values():
        if isinstance(ud, dict):
            ud["cash"]      = 0
            ud["bank"]      = 0
            ud["inventory"] = []
            ud["lager"]     = []
            count          += 1
    save_economy(eco)

    embed = discord.Embed(
        title="\u26A0\uFE0F Hard-Reset durchgef\u00FChrt",
        description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F465 Spieler",     value=f"**{count}**",    inline=True)
    embed.add_field(name="\U0001F4B5 Bargeld",     value="**$0**",          inline=True)
    embed.add_field(name="\U0001F3E6 Bank",        value="**$0**",          inline=True)
    embed.add_field(name="\U0001F392 Rucksack",    value="**Geleert**",     inline=True)
    embed.add_field(name="\U0001F3E0 Lager",       value="**Geleert**",     inline=True)
    embed.set_footer(text=f"\U0001F451 {interaction.user.display_name} \u2022 Paradise City Roleplay")
    await interaction.followup.send(embed=embed, ephemeral=True)
