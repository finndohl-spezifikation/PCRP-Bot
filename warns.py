# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# warns.py \u2014 Warn System (Spieler-Warns & Team-Warns)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from economy_helpers import (
    load_warns, save_warns, get_user_warns,
    load_team_warns, save_team_warns, get_user_team_warns
)


@bot.tree.command(name="warn", description="[Warn] Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if interaction.user.id != OWNER_ID and not any(r.id == WARN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)
    warn_entry = {
        "grund":       grund,
        "konsequenz":  konsequenz,
        "warned_by":   interaction.user.id,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }
    user_warns.append(warn_entry)
    save_warns(warns)
    warn_count = len(user_warns)

    badge = "\U0001F534" if warn_count >= 3 else "\U0001F7E1" if warn_count == 2 else "\U0001F7E2"
    embed = discord.Embed(
        title=f"\u26A0\uFE0F Verwarnung ausgestellt",
        description=f"\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015",
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F464 Spieler",      value=nutzer.mention,              inline=True)
    embed.add_field(name=f"{badge} Warns gesamt",   value=f"**{warn_count}**",         inline=True)
    embed.add_field(name="\U0001F6E1\uFE0F Verwarnt von", value=interaction.user.mention, inline=True)
    embed.add_field(name="\U0001F4CB Grund",        value=grund,                       inline=False)
    embed.add_field(name="\u2694\uFE0F Konsequenz", value=konsequenz,                  inline=False)
    embed.set_thumbnail(url=nutzer.display_avatar.url)
    embed.set_footer(text="\U0001F6E1\uFE0F Warn-System \u2022 Paradise City Roleplay")
    log_ch = interaction.guild.get_channel(WARN_LOG_CHANNEL_ID)
    if log_ch:
        await log_ch.send(embed=embed)

    await interaction.response.send_message(
        f"\u2705 Verwarnung f\u00FCr {nutzer.mention} gespeichert. (Warns gesamt: **{warn_count}**)", ephemeral=True
    )

    if warn_count >= WARN_AUTO_TIMEOUT_COUNT:
        timeout_dur = timedelta(days=2)
        try:
            await nutzer.timeout(timeout_dur, reason=f"Automatischer Timeout: {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht")
        except Exception:
            pass
        try:
            roles_to_remove = [r for r in nutzer.roles if r != interaction.guild.default_role and not r.managed]
            if roles_to_remove:
                await nutzer.remove_roles(*roles_to_remove, reason="Automatischer Timeout: 3 Warns")
        except Exception:
            pass
        try:
            dm_embed = discord.Embed(
                title="\U0001F507 Du wurdest getimeoutet",
                description=(
                    f"Du hast auf **{interaction.guild.name}** {WARN_AUTO_TIMEOUT_COUNT} Verwarnungen erhalten "
                    f"und wurdest daher f\u00FCr **2 Tage** getimeoutet.\n\n"
                    f"**Letzte Verwarnung:**\n"
                    f"Grund: {grund}\nKonsequenz: {konsequenz}\n\n"
                    f"Deine Rollen wurden vor\u00FCbergehend entfernt.\n"
                    f"Nach dem Timeout melde dich bitte bei einem Teammitglied."
                ),
                color=MOD_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            dm_embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
            await nutzer.send(embed=dm_embed)
        except Exception:
            pass
        timeout_embed = discord.Embed(
            title="\U0001F507 Automatischer Timeout",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Grund:** {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht\n"
                f"**Dauer:** 2 Tage\n"
                f"**Rollen entfernt:** \u2705"
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        timeout_embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
        if log_ch:
            await log_ch.send(embed=timeout_embed)


@bot.tree.command(name="warn-list", description="[Warn] Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def warn_list(interaction: discord.Interaction, nutzer: discord.Member):
    if interaction.user.id != OWNER_ID and not any(r.id == WARN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"\u2705 {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        ts  = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** \u2014 {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"\u26A0\uFE0F Warns von {nutzer.display_name}",
        description="\n".join(lines),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesamt: {len(user_warns)} Warn(s)")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="remove-warn", description="[Warn] Letzte Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def remove_warn(interaction: discord.Interaction, nutzer: discord.Member):
    if interaction.user.id != OWNER_ID and not any(r.id == WARN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"\u2139\uFE0F {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_warns(warns)

    embed = discord.Embed(
        title="\u2705 Verwarnung entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernte Verwarnung:** {removed['grund']}\n"
            f"**Verbleibende Warns:** {len(user_warns)}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="team-warn", description="[Admin] Team-Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def team_warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if interaction.user.id != OWNER_ID and not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr Admins verf\u00FCgbar.", ephemeral=True)
        return

    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)
    warn_entry = {
        "grund":      grund,
        "konsequenz": konsequenz,
        "warned_by":  interaction.user.id,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }
    user_warns.append(warn_entry)
    save_team_warns(warns)
    warn_count = len(user_warns)

    embed = discord.Embed(
        title="\U0001F6E1\uFE0F Team-Verwarnung",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Grund:** {grund}\n"
            f"**Konsequenz:** {konsequenz}\n"
            f"**Verwarnt von:** {interaction.user.mention}\n"
            f"**Team-Warns gesamt:** {warn_count}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
    log_ch = interaction.guild.get_channel(TEAM_WARN_LOG_CHANNEL_ID)
    if log_ch:
        await log_ch.send(embed=embed)

    try:
        dm_embed = discord.Embed(
            title="\U0001F6E1\uFE0F Du hast eine Team-Verwarnung erhalten",
            description=(
                f"**Server:** {interaction.guild.name}\n"
                f"**Grund:** {grund}\n"
                f"**Konsequenz:** {konsequenz}\n"
                f"**Team-Warns gesamt:** {warn_count}\n\n"
                f"Bitte halte dich an die Serverregeln."
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        dm_embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
        await nutzer.send(embed=dm_embed)
    except Exception:
        pass

    await interaction.response.send_message(
        f"\u2705 Team-Verwarnung f\u00FCr {nutzer.mention} gespeichert. (Team-Warns gesamt: **{warn_count}**)",
        ephemeral=True
    )


@bot.tree.command(name="teamwarn-list", description="[Admin] Team-Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def teamwarn_list(interaction: discord.Interaction, nutzer: discord.Member):
    if interaction.user.id != OWNER_ID and not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr Admins verf\u00FCgbar.", ephemeral=True)
        return

    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"\u2705 {nutzer.mention} hat keine Team-Verwarnungen.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        ts = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** \u2014 {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"\U0001F6E1\uFE0F Team-Warns von {nutzer.display_name}",
        description="\n".join(lines),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesamt: {len(user_warns)} Team-Warn(s)")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="remove-teamwarn", description="[Admin] Letzte Team-Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def remove_teamwarn(interaction: discord.Interaction, nutzer: discord.Member):
    if interaction.user.id != OWNER_ID and not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Dieser Befehl ist nur f\u00FCr Admins verf\u00FCgbar.", ephemeral=True)
        return

    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"\u2139\uFE0F {nutzer.mention} hat keine Team-Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_team_warns(warns)

    log_ch = interaction.guild.get_channel(TEAM_WARN_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="\U0001F5D1\uFE0F Team-Verwarnung entfernt",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Entfernte Verwarnung:** {removed['grund']}\n"
                f"**Entfernt von:** {interaction.user.mention}\n"
                f"**Verbleibende Team-Warns:** {len(user_warns)}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        log_embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
        await log_ch.send(embed=log_embed)

    embed = discord.Embed(
        title="\u2705 Team-Verwarnung entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernte Verwarnung:** {removed['grund']}\n"
            f"**Verbleibende Team-Warns:** {len(user_warns)}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
    await interaction.response.send_message(embed=embed, ephemeral=True)
