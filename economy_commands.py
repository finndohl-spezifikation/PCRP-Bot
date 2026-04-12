# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# economy_commands.py — Economy Slash Commands (Konto, Lohn, etc.)
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import is_admin
from economy_helpers import (
    load_economy, save_economy, get_user, reset_daily_if_needed,
    has_citizen_or_wage, betrag_autocomplete, log_money_action, channel_error
)


# ── Betrag-Parser (z. B. "1.000" → 1000) ─────────────────────

def parse_betrag(text: str) -> int | None:
    try:
        return int(text.replace(".", "").replace(",", "").strip())
    except ValueError:
        return None


# ── Modals ────────────────────────────────────────────────────

class EinzahlenModal(discord.ui.Modal, title="🏦 Einzahlen"):
    betrag_input = discord.ui.TextInput(
        label="Betrag (💵)",
        placeholder="z. B. 5000",
        min_length=1,
        max_length=12,
    )

    async def on_submit(self, interaction: discord.Interaction):
        betrag = parse_betrag(self.betrag_input.value)
        if betrag is None or betrag <= 0:
            await interaction.response.send_message("❌ Ungültiger Betrag.", ephemeral=True)
            return

        role_ids = [r.id for r in interaction.user.roles]
        is_adm   = ADMIN_ROLE_ID in role_ids

        if not is_adm and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
            return

        eco       = load_economy()
        user_data = get_user(eco, interaction.user.id)
        reset_daily_if_needed(user_data)

        if user_data["cash"] < betrag:
            await interaction.response.send_message(
                f"❌ Nicht genug Bargeld. Dein Bargeld: **{user_data['cash']:,} 💵**", ephemeral=True
            )
            return

        if not is_adm:
            user_limit = user_data.get("custom_limit") or DAILY_LIMIT
            remaining  = user_limit - user_data["daily_deposit"]
            if betrag > remaining:
                await interaction.response.send_message(
                    f"❌ Tageslimit erreicht. Du kannst heute noch **{remaining:,} 💵** einzahlen. "
                    f"(Limit: **{user_limit:,} 💵**)",
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
            f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} 💵\n"
            f"**Bargeld danach:** {user_data['cash']:,} 💵 | **Bank danach:** {user_data['bank']:,} 💵"
        )

        embed = discord.Embed(
            title="🏦 Eingezahlt",
            description=(
                f"**Eingezahlt:** {betrag:,} 💵\n"
                f"**Bargeld:** {user_data['cash']:,} 💵\n"
                f"**Bank:** {user_data['bank']:,} 💵"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class AuszahlenModal(discord.ui.Modal, title="💸 Auszahlen"):
    betrag_input = discord.ui.TextInput(
        label="Betrag (💵)",
        placeholder="z. B. 5000",
        min_length=1,
        max_length=12,
    )

    async def on_submit(self, interaction: discord.Interaction):
        betrag = parse_betrag(self.betrag_input.value)
        if betrag is None or betrag <= 0:
            await interaction.response.send_message("❌ Ungültiger Betrag.", ephemeral=True)
            return

        role_ids = [r.id for r in interaction.user.roles]
        is_adm   = ADMIN_ROLE_ID in role_ids

        if not is_adm and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
            return

        eco       = load_economy()
        user_data = get_user(eco, interaction.user.id)
        reset_daily_if_needed(user_data)

        if user_data["bank"] < betrag:
            await interaction.response.send_message(
                f"❌ Nicht genug Guthaben. Dein Kontostand: **{user_data['bank']:,} 💵**", ephemeral=True
            )
            return

        if not is_adm:
            user_limit = user_data.get("custom_limit") or DAILY_LIMIT
            remaining  = user_limit - user_data["daily_withdraw"]
            if betrag > remaining:
                await interaction.response.send_message(
                    f"❌ Tageslimit erreicht. Du kannst heute noch **{remaining:,} 💵** auszahlen. "
                    f"(Limit: **{user_limit:,} 💵**)",
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
            f"**Spieler:** {interaction.user.mention}\n**Betrag:** {betrag:,} 💵\n"
            f"**Bargeld danach:** {user_data['cash']:,} 💵 | **Bank danach:** {user_data['bank']:,} 💵"
        )

        embed = discord.Embed(
            title="💸 Ausgezahlt",
            description=(
                f"**Ausgezahlt:** {betrag:,} 💵\n"
                f"**Bargeld:** {user_data['cash']:,} 💵\n"
                f"**Bank:** {user_data['bank']:,} 💵"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class UeberweisungsModal(discord.ui.Modal, title="💳 Überweisen"):
    empfaenger_input = discord.ui.TextInput(
        label="Empfänger (User-ID oder @Mention)",
        placeholder="z. B. 123456789012345678",
        min_length=1,
        max_length=30,
    )
    betrag_input = discord.ui.TextInput(
        label="Betrag (💵)",
        placeholder="z. B. 5000",
        min_length=1,
        max_length=12,
    )

    async def on_submit(self, interaction: discord.Interaction):
        betrag = parse_betrag(self.betrag_input.value)
        if betrag is None or betrag <= 0:
            await interaction.response.send_message("❌ Ungültiger Betrag.", ephemeral=True)
            return

        # Mention oder reine ID parsen
        raw = self.empfaenger_input.value.strip().lstrip("<@!").rstrip(">")
        try:
            ziel_id = int(raw)
        except ValueError:
            await interaction.response.send_message(
                "❌ Ungültige User-ID. Gib eine gültige ID oder einen @Mention ein.", ephemeral=True
            )
            return

        if ziel_id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Du kannst nicht an dich selbst überweisen.", ephemeral=True
            )
            return

        ziel_member = interaction.guild.get_member(ziel_id)
        if ziel_member is None:
            await interaction.response.send_message(
                "❌ Mitglied nicht gefunden. Bitte prüfe die User-ID.", ephemeral=True
            )
            return

        role_ids = [r.id for r in interaction.user.roles]
        is_adm   = ADMIN_ROLE_ID in role_ids

        if not is_adm and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
            return

        eco      = load_economy()
        sender   = get_user(eco, interaction.user.id)
        receiver = get_user(eco, ziel_id)
        reset_daily_if_needed(sender)

        if sender["bank"] < betrag:
            await interaction.response.send_message(
                f"❌ Nicht genug Guthaben. Dein Kontostand: **{sender['bank']:,} 💵**", ephemeral=True
            )
            return

        if not is_adm:
            user_limit = sender.get("custom_limit") or DAILY_LIMIT
            remaining  = user_limit - sender["daily_transfer"]
            if betrag > remaining:
                await interaction.response.send_message(
                    f"❌ Tageslimit erreicht. Du kannst heute noch **{remaining:,} 💵** überweisen. "
                    f"(Limit: **{user_limit:,} 💵**)",
                    ephemeral=True
                )
                return
            sender["daily_transfer"] += betrag

        sender["bank"]   -= betrag
        receiver["bank"] += betrag
        save_economy(eco)
        await log_money_action(
            interaction.guild,
            "Überweisung",
            f"**Von:** {interaction.user.mention} → **An:** {ziel_member.mention}\n"
            f"**Betrag:** {betrag:,} 💵 | **Sender-Bank danach:** {sender['bank']:,} 💵"
        )

        embed = discord.Embed(
            title="💳 Überweisung",
            description=(
                f"**An:** {ziel_member.mention}\n"
                f"**Betrag:** {betrag:,} 💵\n"
                f"**Dein Kontostand:** {sender['bank']:,} 💵"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Kontostand View (Buttons) ─────────────────────────────────

class KontostandView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Einzahlen", emoji="🏦", style=discord.ButtonStyle.success)
    async def einzahlen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_citizen_or_wage(interaction.user) and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
            return
        await interaction.response.send_modal(EinzahlenModal())

    @discord.ui.button(label="Auszahlen", emoji="💸", style=discord.ButtonStyle.danger)
    async def auszahlen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_citizen_or_wage(interaction.user) and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
            return
        await interaction.response.send_modal(AuszahlenModal())

    @discord.ui.button(label="Überweisen", emoji="💳", style=discord.ButtonStyle.primary)
    async def ueberweisen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_citizen_or_wage(interaction.user) and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
            return
        await interaction.response.send_modal(UeberweisungsModal())


# ── /lohn-abholen ─────────────────────────────────────────────

@bot.tree.command(name="lohn-abholen", description="[Konto] Hole deinen stündlichen Lohn ab", guild=discord.Object(id=GUILD_ID))
async def lohn_abholen(interaction: discord.Interaction):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != LOHN_CHANNEL_ID:
        await interaction.response.send_message(channel_error(LOHN_CHANNEL_ID), ephemeral=True)
        return

    main_wages = [WAGE_ROLES[r] for r in role_ids if r in WAGE_ROLES]
    if len(main_wages) > 1:
        await interaction.response.send_message(
            "❌ Du hast mehrere Lohnklassen. Bitte wende dich ans Team.", ephemeral=True
        )
        return
    if not main_wages:
        await interaction.response.send_message(
            "❌ Du hast keine Lohnklasse und kannst keinen Lohn abholen.", ephemeral=True
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
                f"❌ Du kannst deinen Lohn erst in **{mins}m {secs}s** wieder abholen.",
                ephemeral=True
            )
            return

    user_data["bank"]      += total_wage
    user_data["last_wage"]  = now.isoformat()
    save_economy(eco)

    embed = discord.Embed(
        title="💵 Lohn abgeholt!",
        description=(
            f"Du hast **{total_wage:,} 💵** auf dein Konto erhalten.\n"
            f"**Kontostand:** {user_data['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=now
    )
    await interaction.response.send_message(embed=embed)


# ── /kontostand ───────────────────────────────────────────────

@bot.tree.command(name="kontostand", description="[Konto] Zeigt den Kontostand an", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Mitglied dessen Kontostand abgerufen werden soll")
async def kontostand(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids  = [r.id for r in interaction.user.roles]
    is_adm    = ADMIN_ROLE_ID in role_ids
    is_team_m = is_adm or MOD_ROLE_ID in role_ids

    if nutzer is not None:
        if not is_team_m:
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, den Kontostand anderer Mitglieder abzurufen.",
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
            await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
            return
        ziel      = interaction.user
        show_btns = True

    eco       = load_economy()
    user_data = get_user(eco, ziel.id)
    save_economy(eco)

    titel = "💳 Kontostand" if ziel.id == interaction.user.id else f"💳 Kontostand — {ziel.display_name}"
    embed = discord.Embed(
        title=titel,
        description=(
            f"**Bargeld:** {user_data['cash']:,} 💵\n"
            f"**Bank:** {user_data['bank']:,} 💵\n"
            f"**Gesamt:** {user_data['cash'] + user_data['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=ziel.display_avatar.url)

    view = KontostandView() if show_btns else None
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ── /money-add ────────────────────────────────────────────────

@bot.tree.command(name="money-add", description="[Team] Füge einem Spieler Geld hinzu", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
async def money_add(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not any(r.id in (MONEY_ADD_ROLE_1_ID, MONEY_ADD_ROLE_2_ID, ADMIN_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["bank"] += betrag
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld hinzugefügt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** +{betrag:,} 💵\n"
        f"**Bank danach:** {user_data['bank']:,} 💵\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="💰 Geld hinzugefügt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Hinzugefügt:** {betrag:,} 💵\n"
            f"**Kontostand:** {user_data['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /remove-money ─────────────────────────────────────────────

@bot.tree.command(name="remove-money", description="[Admin] Entferne Geld von einem Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler", betrag="Betrag in $")
async def remove_money(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["cash"] = max(0, user_data["cash"] - betrag)
    save_economy(eco)
    await log_money_action(
        interaction.guild,
        "Admin: Geld entfernt",
        f"**Spieler:** {nutzer.mention}\n**Betrag:** -{betrag:,} 💵\n"
        f"**Bargeld danach:** {user_data['cash']:,} 💵\n**Admin:** {interaction.user.mention}"
    )

    embed = discord.Embed(
        title="💸 Geld entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernt:** {betrag:,} 💵\n"
            f"**Bargeld:** {user_data['cash']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /set-limit ────────────────────────────────────────────────

@bot.tree.command(name="set-limit", description="[Team] Setzt das individuelle Tageslimit eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", limit="Neues Tageslimit")
@app_commands.choices(limit=LIMIT_CHOICES)
async def set_limit(interaction: discord.Interaction, nutzer: discord.Member, limit: int):
    role_ids = [r.id for r in interaction.user.roles]
    if ADMIN_ROLE_ID not in role_ids and MOD_ROLE_ID not in role_ids:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, nutzer.id)
    user_data["custom_limit"] = limit
    save_economy(eco)

    embed = discord.Embed(
        title="⚙️ Limit gesetzt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Neues Tageslimit:** {limit:,} 💵\n"
            f"*(gilt für Einzahlen, Auszahlen & Überweisen)*"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesetzt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)
