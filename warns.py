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

# Warn-Rollen: Warn-Anzahl -> Rollen-ID
WARN_ROLLEN: dict[int, int] = {
    1: 1490855747192361000,
    2: 1490855745842053221,
    3: 1490855744868716695,
    4: 1490855743610552491,
    5: 1490855743015092405,
}


async def _assign_warn_rolle(member: discord.Member, guild: discord.Guild, warn_count: int) -> None:
    """Entfernt alle alten Warn-Rollen und setzt die passende für warn_count."""
    try:
        alle_warn_role_ids = set(WARN_ROLLEN.values())
        alte = [r for r in member.roles if r.id in alle_warn_role_ids]
        if alte:
            await member.remove_roles(*alte, reason="Warn-Rollen aktualisieren")
        neue_id = WARN_ROLLEN.get(warn_count)
        if neue_id:
            neue_rolle = guild.get_role(neue_id)
            if neue_rolle:
                await member.add_roles(neue_rolle, reason=f"Verwarnung #{warn_count}")
    except Exception as _e:
        print(f"[warns] Warn-Rolle Fehler: {_e}")



# Log-Kanal für alle Warn-Aktionen
_WARN_LOG_ID = 1490878132230819840

async def _warn_log(embed: discord.Embed) -> None:
    """Sendet ein Embed in den Warn-Log-Kanal."""
    try:
        ch = bot.get_channel(_WARN_LOG_ID) or await bot.fetch_channel(_WARN_LOG_ID)
        await ch.send(embed=embed)
    except Exception as _e:
        print(f"[warns] Log-Fehler: {_e}")


@bot.tree.command(name="warn", description="[Warn] Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    await interaction.response.defer(ephemeral=True)
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

    # Warn-Rolle automatisch vergeben
    guild_obj = interaction.guild or bot.get_guild(GUILD_ID)
    if guild_obj:
        await _assign_warn_rolle(nutzer, guild_obj, warn_count)

    badge = "\U0001F534" if warn_count >= 5 else "\U0001F7E1" if warn_count >= 3 else "\U0001F7E2"
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
    await _warn_log(embed)

    await interaction.followup.send(
        f"\u2705 Verwarnung f\u00FCr {nutzer.mention} gespeichert. (Warns gesamt: **{warn_count}**)", ephemeral=True
    )

    if warn_count >= WARN_AUTO_TIMEOUT_COUNT:
        timeout_dur = timedelta(days=2)
        try:
            await nutzer.timeout(timeout_dur, reason=f"Automatischer Timeout: {WARN_AUTO_TIMEOUT_COUNT} Warns erreicht")
        except Exception:
            pass
        # Rollen werden bei Timeout nicht entfernt
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
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        timeout_embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
        await _warn_log(timeout_embed)

    if warn_count >= WARN_AUTO_BAN_COUNT:
        try:
            dm_ban_embed = discord.Embed(
                title="\U0001f6ab Du wurdest gebannt",
                description=(
                    f"Du hast auf **{interaction.guild.name}** {WARN_AUTO_BAN_COUNT} Verwarnungen erhalten "
                    f"und wurdest daher permanent vom Server entfernt.\n\n"
                    f"**Letzte Verwarnung:**\n"
                    f"Grund: {grund}\nKonsequenz: {konsequenz}"
                ),
                color=MOD_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            dm_ban_embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
            await nutzer.send(embed=dm_ban_embed)
        except Exception:
            pass
        try:
            await nutzer.ban(reason=f"Automatischer Ban: {WARN_AUTO_BAN_COUNT} Warns erreicht", delete_message_days=0)
        except Exception:
            pass
        ban_embed = discord.Embed(
            title="\U0001f6ab Automatischer Ban",
            description=(
                f"**Spieler:** {nutzer.mention}\n"
                f"**Grund:** {WARN_AUTO_BAN_COUNT} Warns erreicht\n"
                f"**Ban:** Permanent"
            ),
            color=MOD_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        ban_embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
        await _warn_log(ban_embed)


@bot.tree.command(name="warn-list", description="[Warn] Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def warn_list(interaction: discord.Interaction, nutzer: discord.Member):
    await interaction.response.defer(ephemeral=True)
    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.followup.send(
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
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="remove-warn", description="[Warn] Letzte Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def remove_warn(interaction: discord.Interaction, nutzer: discord.Member):
    await interaction.response.defer(ephemeral=True)
    warns      = load_warns()
    user_warns = get_user_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.followup.send(
            f"\u2139\uFE0F {nutzer.mention} hat keine Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_warns(warns)

    remove_embed = discord.Embed(
        title="\u2705 Verwarnung entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernte Verwarnung:** {removed['grund']}\n"
            f"**Konsequenz:** {removed.get('konsequenz', '\u2014')}\n"
            f"**Entfernt von:** {interaction.user.mention}\n"
            f"**Verbleibende Warns:** {len(user_warns)}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    remove_embed.set_thumbnail(url=nutzer.display_avatar.url)
    remove_embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
    await _warn_log(remove_embed)
    await interaction.followup.send(embed=remove_embed, ephemeral=True)


@bot.tree.command(name="team-warn", description="[Admin] Team-Verwarnung an einen Spieler ausgeben", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler", grund="Grund der Verwarnung", konsequenz="Konsequenz")
async def team_warn(interaction: discord.Interaction, nutzer: discord.Member, grund: str, konsequenz: str):
    await interaction.response.defer(ephemeral=True)
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
    await _warn_log(embed)

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

    await interaction.followup.send(
        f"\u2705 Team-Verwarnung f\u00FCr {nutzer.mention} gespeichert. (Team-Warns gesamt: **{warn_count}**)",
        ephemeral=True
    )


@bot.tree.command(name="teamwarn-list", description="[Admin] Team-Verwarnungen eines Spielers anzeigen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def teamwarn_list(interaction: discord.Interaction, nutzer: discord.Member):
    await interaction.response.defer(ephemeral=True)
    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.followup.send(
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
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="remove-teamwarn", description="[Admin] Letzte Team-Verwarnung eines Spielers entfernen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler")
async def remove_teamwarn(interaction: discord.Interaction, nutzer: discord.Member):
    await interaction.response.defer(ephemeral=True)
    warns      = load_team_warns()
    user_warns = get_user_team_warns(warns, nutzer.id)

    if not user_warns:
        await interaction.followup.send(
            f"\u2139\uFE0F {nutzer.mention} hat keine Team-Verwarnungen.", ephemeral=True
        )
        return

    removed = user_warns.pop()
    save_team_warns(warns)

    rtw_log_embed = discord.Embed(
        title="\U0001F5D1\uFE0F Team-Verwarnung entfernt",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Entfernte Verwarnung:** {removed['grund']}\n"
            f"**Konsequenz:** {removed.get('konsequenz', '\u2014')}\n"
            f"**Entfernt von:** {interaction.user.mention}\n"
            f"**Verbleibende Team-Warns:** {len(user_warns)}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    rtw_log_embed.set_thumbnail(url=nutzer.display_avatar.url)
    rtw_log_embed.set_footer(text="Paradise City Roleplay \u2022 Warn-System")
    await _warn_log(rtw_log_embed)

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
    await interaction.followup.send(embed=embed, ephemeral=True)


# \u2500\u2500 /ban-list \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_BAN_LIST_PAGE_SIZE = 10

class BanListView(discord.ui.View):
    def __init__(self, bans: list, requester: discord.Member):
        super().__init__(timeout=120)
        self.bans      = bans
        self.requester = requester
        self.page      = 0
        self.max_page  = max(0, (len(bans) - 1) // _BAN_LIST_PAGE_SIZE)
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= self.max_page

    def build_embed(self) -> discord.Embed:
        start = self.page * _BAN_LIST_PAGE_SIZE
        chunk = self.bans[start:start + _BAN_LIST_PAGE_SIZE]
        lines = []
        for idx, (user, reason) in enumerate(chunk, start + 1):
            reason_short = (reason[:60] + "\u2026") if reason and len(reason) > 60 else (reason or "kein Grund")
            lines.append(f"`{idx}.` **{user}** (`{user.id}`)\n    \U0001f4cb {reason_short}")
        embed = discord.Embed(
            title=f"\U0001f6ab Ban-Liste \u2014 {len(self.bans)} gebannte Spieler",
            description="\n\n".join(lines) if lines else "*Keine Bans vorhanden.*",
            color=0xFF0000,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(
            text=f"Seite {self.page + 1}/{self.max_page + 1} \u2022 Paradise City Roleplay"
        )
        return embed

    async def _check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.requester.id:
            await interaction.response.send_message("\u274C Nur der Aufrufer darf bl\u00e4ttern.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="\u25c4 Zur\u00fcck", style=discord.ButtonStyle.secondary, custom_id="banlist_prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check(interaction):
            return
        self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Weiter \u25ba", style=discord.ButtonStyle.secondary, custom_id="banlist_next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check(interaction):
            return
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


@bot.tree.command(
    name="ban-list",
    description="[Mod] Zeigt alle gebannten Spieler des Servers",
    guild=discord.Object(id=GUILD_ID),
)
async def ban_list(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)
    try:
        bans = [(entry.user, entry.reason) async for entry in interaction.guild.bans()]
    except Exception as e:
        await interaction.followup.send(f"\u274C Fehler beim Laden der Bans: `{e}`", ephemeral=True)
        return

    if not bans:
        await interaction.followup.send("\u2705 Keine Bans auf diesem Server.", ephemeral=True)
        return

    view  = BanListView(bans, interaction.user)
    embed = view.build_embed()
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

