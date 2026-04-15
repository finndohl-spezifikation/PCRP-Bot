# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# team_overview.py — Team Übersicht mit On/Off Duty System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *


# ── Datei-Helpers ─────────────────────────────────────────────

def load_duty():
    if DUTY_FILE.exists():
        with open(DUTY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"on_duty": [], "message_id": None}


def save_duty(data):
    with open(DUTY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Embed Builder ─────────────────────────────────────────────

def build_team_embed(guild: discord.Guild, duty_data: dict) -> discord.Embed:
    on_duty_set = set(duty_data.get("on_duty", []))

    lines     = []
    gesamt    = 0
    on_count  = 0
    off_count = 0

    for role_id in TEAM_ROLES:
        role = guild.get_role(role_id)
        if not role:
            continue

        mitglieder = [m for m in role.members if not m.bot]
        if not mitglieder:
            continue

        lines.append(f"\n**{role.name}**")
        for m in sorted(mitglieder, key=lambda x: x.display_name.lower()):
            if m.id in on_duty_set:
                lines.append(f"> {m.mention} 🟢")
                on_count  += 1
            else:
                lines.append(f"> {m.mention} 🔴")
                off_count += 1
            gesamt += 1
        lines.append("")

    beschreibung = "\n".join(lines)
    beschreibung += (
        "\n\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
        f"👥 **Insgesamt:** {gesamt} Teammitglieder\n"
        f"🟢 **On Duty:** {on_count}  ·  🔴 **Off Duty:** {off_count}"
    )

    embed = discord.Embed(
        title="🏆 Team Übersicht — Paradise City Roleplay",
        description=beschreibung,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay • Team-Übersicht | Zuletzt aktualisiert")
    return embed


# ── Persistent View ───────────────────────────────────────────

class TeamOverviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def _is_team(self, member: discord.Member) -> bool:
        return any(r.id in TEAM_ROLE_IDS for r in member.roles)

    async def _update_embed(self, interaction: discord.Interaction):
        duty_data = load_duty()
        embed     = build_team_embed(interaction.guild, duty_data)
        try:
            await interaction.message.edit(embed=embed, view=self)
        except Exception:
            pass

    @discord.ui.button(
        label="On Duty",
        emoji="📱",
        style=discord.ButtonStyle.success,
        custom_id="team_on_duty",
    )
    async def on_duty_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_team(interaction.user):
            await interaction.response.send_message(
                "❌ Nur Teammitglieder können ihren Dienststatus ändern.",
                ephemeral=True,
            )
            return

        duty_data = load_duty()
        uid = interaction.user.id
        if uid not in duty_data["on_duty"]:
            duty_data["on_duty"].append(uid)
            save_duty(duty_data)

        await interaction.response.send_message(
            "✅ Du bist jetzt **🟢 On Duty**.", ephemeral=True
        )
        await self._update_embed(interaction)

    @discord.ui.button(
        label="Off Duty",
        emoji="📵",
        style=discord.ButtonStyle.danger,
        custom_id="team_off_duty",
    )
    async def off_duty_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_team(interaction.user):
            await interaction.response.send_message(
                "❌ Nur Teammitglieder können ihren Dienststatus ändern.",
                ephemeral=True,
            )
            return

        duty_data = load_duty()
        uid = interaction.user.id
        if uid in duty_data["on_duty"]:
            duty_data["on_duty"].remove(uid)
            save_duty(duty_data)

        await interaction.response.send_message(
            "✅ Du bist jetzt **🔴 Off Duty**.", ephemeral=True
        )
        await self._update_embed(interaction)


# ── Auto Setup ────────────────────────────────────────────────

async def auto_team_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(TEAM_OVERVIEW_CHANNEL_ID)
        if not channel:
            continue

        duty_data = load_duty()
        embed     = build_team_embed(guild, duty_data)
        view      = TeamOverviewView()

        # Vorhandene Nachricht bearbeiten
        if duty_data.get("message_id"):
            try:
                msg = await channel.fetch_message(duty_data["message_id"])
                await msg.edit(embed=embed, view=view)
                print(f"[team_overview] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        # Altes Embed suchen und löschen
        try:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Team Übersicht" in emb.title:
                            try:
                                await msg.delete()
                            except Exception:
                                pass
                            break
        except Exception:
            pass

        # Neu posten
        try:
            new_msg = await channel.send(embed=embed, view=view)
            duty_data["message_id"] = new_msg.id
            save_duty(duty_data)
            print(f"[team_overview] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[team_overview] Fehler: {e}")


# ── Slash Command: /team-refresh ──────────────────────────────

@bot.tree.command(
    name="team-refresh",
    description="[Team] Aktualisiert die Team-Übersicht manuell",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.default_permissions(manage_messages=True)
async def team_refresh(interaction: discord.Interaction):
    if not any(r.id in TEAM_ROLE_IDS for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    await auto_team_setup()
    await interaction.followup.send("✅ Team-Übersicht wurde aktualisiert.", ephemeral=True)
