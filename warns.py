# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# warns.py — Warn System (Spieler-Warns & Team-Warns)
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from economy_helpers import (
    load_warns, save_warns, get_user_warns,
    load_team_warns, save_team_warns, get_user_team_warns
)


@bot.tree.command(name="warn", description="[Warn] Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if not any(r.id == WARN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
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

    embed = discord.Embed(
        title="⚠️ Verwarnung",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Grund:** {grund}\n"
            f"**Konsequenz:** {konsequenz}\n"
            f"**Verwarnt von:** {interaction.user.mention}\n"
            f"**Warns gesamt:** {warn_count}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    log_ch = interaction.guild.get_channel(WARN_LOG_CHANNEL_ID)
    if log_ch:
        await log_ch.send(embed=embed)

    await interaction.response.send_message(
        f"✅ Verwarnung für {nutzer.mention} gespeichert. (Warns gesamt: **{warn_count}**)", ephemeral=True
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
                title="🔇 Du wurdest getimeoutet",
                description=(
                    f"Du hast auf **{interaction.guild.name}** {WARN_AUTO_TIMEOUT_COUNT} Verwarnungen erhalten "
                    f"und wurdest daher für **2 Tage** getimeoutet.\n\n"
                    f"**Letzte Verwarnung:**\n"
                    f"Grund: {grund}\nKonsequenz: {konsequenz}\n\n"
                    f"Deine Rollen wurden vorübergehend entfernt.\n"
                    f"Nach dem Timeout melde dich bitte bei einem Teammitglied."
                ),
                color=MOD_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            await nutzer.send(embed=dm_embed)
        except Exception:
            pass
        timeout_embed = discord.Embed(
            title="🔇 Automatischer Timeout",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Grund:** {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht\n"
                f"**Dauer:** 2 Tage\n"
                f"**Rollen entfernt:** ✅"
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        if log_ch:
            await log_ch.send(embed=timeout_embed)


@bot.tree.command(name="warn-list", description="[Warn] Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler")
async def warn_list(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id == WARN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"✅ {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        ts  = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** — {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"⚠️ Warns von {nutzer.display_name}",
        description="\n".join(lines),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesamt: {len(user_warns)} Warn(s)")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="remove-warn", description="[Warn] Letzte Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler")
async def remove_warn(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id == WARN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"ℹ️ {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_warns(warns)

    embed = discord.Embed(
        title="✅ Verwarnung entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernte Verwarnung:** {removed['grund']}\n"
            f"**Verbleibende Warns:** {len(user_warns)}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="team-warn", description="[Admin] Team-Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def team_warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Dieser Befehl ist nur für Admins verfügbar.", ephemeral=True)
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
        title="🛡️ Team-Verwarnung",
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
    log_ch = interaction.guild.get_channel(TEAM_WARN_LOG_CHANNEL_ID)
    if log_ch:
        await log_ch.send(embed=embed)

    try:
        dm_embed = discord.Embed(
            title="🛡️ Du hast eine Team-Verwarnung erhalten",
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
        await nutzer.send(embed=dm_embed)
    except Exception:
        pass

    await interaction.response.send_message(
        f"✅ Team-Verwarnung für {nutzer.mention} gespeichert. (Team-Warns gesamt: **{warn_count}**)",
        ephemeral=True
    )


@bot.tree.command(name="teamwarn-list", description="[Admin] Team-Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler")
async def teamwarn_list(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Dieser Befehl ist nur für Admins verfügbar.", ephemeral=True)
        return

    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"✅ {nutzer.mention} hat keine Team-Verwarnungen.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        ts = w.get("timestamp", "")[:10]
        lines.append(f"**#{i}** — {w['grund']} | Konsequenz: {w['konsequenz']} *(am {ts})*")

    embed = discord.Embed(
        title=f"🛡️ Team-Warns von {nutzer.display_name}",
        description="\n".join(lines),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Gesamt: {len(user_warns)} Team-Warn(s)")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="remove-teamwarn", description="[Admin] Letzte Team-Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler")
async def remove_teamwarn(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("❌ Dieser Befehl ist nur für Admins verfügbar.", ephemeral=True)
        return

    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.response.send_message(
            f"ℹ️ {nutzer.mention} hat keine Team-Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_team_warns(warns)

    log_ch = interaction.guild.get_channel(TEAM_WARN_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="🗑️ Team-Verwarnung entfernt",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Entfernte Verwarnung:** {removed['grund']}\n"
                f"**Entfernt von:** {interaction.user.mention}\n"
                f"**Verbleibende Team-Warns:** {len(user_warns)}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        await log_ch.send(embed=log_embed)

    embed = discord.Embed(
        title="✅ Team-Verwarnung entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernte Verwarnung:** {removed['grund']}\n"
            f"**Verbleibende Team-Warns:** {len(user_warns)}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
