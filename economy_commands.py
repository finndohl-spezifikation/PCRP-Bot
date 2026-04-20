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
            title="\U0001F3E6 Eingezahlt",
            description=(
                f"**Eingezahlt:** {betrag:,} \U0001F4B5\n"
                f"\U0001F4B5 **Bargeld:** {user_data['cash']:,} \U0001F4B5\n"
                f"\U0001F3E6 **Konto:** {user_data['bank']:,} \U0001F4B5"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Paradise City Roleplay \u2022 Maze Bank")
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
            title="\U0001F4B8 Ausgezahlt",
            description=(
                f"**Ausgezahlt:** {betrag:,} \U0001F4B5\n"
                f"\U0001F4B5 **Bargeld:** {user_data['cash']:,} \U0001F4B5\n"
                f"\U0001F3E6 **Konto:** {user_data['bank']:,} \U0001F4B5"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Paradise City Roleplay \u2022 Maze Bank")
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
            description=(
                f"**An:** {self.ziel.mention}\n"
                f"**Betrag:** {betrag:,} \U0001F4B5\n"
                f"**Dein Kontostand:** {sender['bank']:,} \U0001F4B5"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Paradise City Roleplay \u2022 Maze Bank")
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
        description=(
            f"Du hast **{total_wage:,} \U0001F4B5** auf dein Konto erhalten.\n"
            f"**Kontostand:** {user_data['bank']:,} \U0001F4B5"
        ),
        color=LOG_COLOR,
        timestamp=now
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Lohnb\u00FCro")
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
        description=desc,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)
    embed.set_footer(text="Paradise City Roleplay \u2022 Maze Bank")

    view = KontostandView() if show_btns else None
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)



# Admin-Commands wurden ins Dashboard verschoben (dashboard.py)
