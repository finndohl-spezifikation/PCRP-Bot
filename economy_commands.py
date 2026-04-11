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


# /lohn-abholen
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


# /kontostand
@bot.tree.command(name="kontostand", description="[Konto] Zeigt den Kontostand an", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Mitglied dessen Kontostand abgerufen werden soll")
async def kontostand(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids  = [r.id for r in interaction.user.roles]
    is_team_m = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids

    if nutzer is not None:
        if not is_team_m:
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, den Kontostand anderer Mitglieder abzurufen.",
                ephemeral=True
            )
            return
        ziel = nutzer
    else:
        if not is_team_m and interaction.channel.id != BANK_CHANNEL_ID:
            await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
            return
        if not is_team_m and not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
            return
        ziel = interaction.user

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
    await interaction.response.send_message(embed=embed, ephemeral=True)


# /einzahlen
@bot.tree.command(name="einzahlen", description="[Konto] Zahle Bargeld auf dein Bankkonto ein", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wählen oder eingeben (1.000 – 10.000.000 💵)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def einzahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
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
    await interaction.response.send_message(embed=embed)


# /auszahlen
@bot.tree.command(name="auszahlen", description="[Konto] Hebe Geld von deinem Bankkonto ab", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(betrag="Betrag wählen oder eingeben (1.000 – 10.000.000 💵)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def auszahlen(interaction: discord.Interaction, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
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
    await interaction.response.send_message(embed=embed)


# /ueberweisen
@bot.tree.command(name="ueberweisen", description="[Konto] Überweise Geld an einen anderen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Empfänger", betrag="Betrag wählen oder eingeben (1.000 – 10.000.000 💵)")
@app_commands.autocomplete(betrag=betrag_autocomplete)
async def ueberweisen(interaction: discord.Interaction, nutzer: discord.Member, betrag: int):
    role_ids = [r.id for r in interaction.user.roles]
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and interaction.channel.id != BANK_CHANNEL_ID:
        await interaction.response.send_message(channel_error(BANK_CHANNEL_ID), ephemeral=True)
        return

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("❌ Du hast keine Berechtigung.", ephemeral=True)
        return

    if nutzer.id == interaction.user.id:
        await interaction.response.send_message("❌ Du kannst nicht an dich selbst überweisen.", ephemeral=True)
        return

    if betrag <= 0:
        await interaction.response.send_message("❌ Betrag muss größer als 0 sein.", ephemeral=True)
        return

    eco        = load_economy()
    sender     = get_user(eco, interaction.user.id)
    receiver   = get_user(eco, nutzer.id)
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
        f"**Von:** {interaction.user.mention} → **An:** {nutzer.mention}\n"
        f"**Betrag:** {betrag:,} 💵 | **Sender-Bank danach:** {sender['bank']:,} 💵"
    )

    embed = discord.Embed(
        title="💳 Überweisung",
        description=(
            f"**An:** {nutzer.mention}\n"
            f"**Betrag:** {betrag:,} 💵\n"
            f"**Dein Kontostand:** {sender['bank']:,} 💵"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed)


# /money-add
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


# /remove-money
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


# /set-limit (Team only)
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
