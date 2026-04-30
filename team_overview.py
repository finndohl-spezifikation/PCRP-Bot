# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════════════════════════════
# team_overview.py — Team Übersicht mit On/Off Duty System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════════════════════════════

from config import *

# ── Hierarchie: (role_id, outfit_text oder None) ──────────────────────────────────────
# Reihenfolge bestimmt die Anzeigereihenfolge im Embed.
# Rollen ohne Outfit-Beschreibung: None eintragen.
# ─────────────────────────────────────────────────────────────────────────────────────
TEAM_HIERARCHIE = [
    (1490855647259136053, "Teamoutfit Schwarz"),      # Owner
    (1490855648978669599, "Teamoutfit Schwarz"),      # Stv Owner
    (1490855654347505706, "Teamoutfit Weiß"),         # Serverleitung
    (1490855657543303239, "Teamoutfit Weiß"),         # Stv Serverleitung
    (1490855655408664577, "Teamoutfit Blau"),         # Teamleitung
    (1490855656352251987, "Teamoutfit Blau"),         # Stv Teamleitung
    (1490855659506372743, "Teamoutfit Rot"),          # Projektleitung
    (1490855661137956879, "Teamoutfit Rot"),          # Stv Projektleitung
    (1496136847338770693, "Teamoutfit Gelb"),         # Community Manager (NEU)
    (1490855664854106225, "Teamoutfit Weißgelb"),     # Administrator III
    (1490855679282516100, "Teamoutfit Weißgelb"),     # Administrator II
    (1490855680708579389, "Teamoutfit Weißgelb"),     # Administrator I
    (1490855688208126095, "Teamoutfit Weißgelb"),     # Test Administrator
    (1490855689424212110, "Teamoutfit Weißpink"),     # Moderator III
    (1490855690183381087, "Teamoutfit Weißpink"),     # Moderator II
    (1492678578071146536, "Teamoutfit Weißpink"),     # Moderator I
    (1492678644277969048, "Teamoutfit Weißpink"),     # Test Moderator
    (1490855692477923520, "Teamoutfit Schwarzweiß"),  # Supportleitung
    (1490855693786550404, "Teamoutfit Schwarzweiß"),  # Stv Support Leitung
    (1490855695363342358, "Teamoutfit Weißgrün"),     # Supporter III
    (1490855695912931329, "Teamoutfit Weißgrün"),     # Supporter II
    (1498395437206601828, "Teamoutfit Weißgrün"),     # Supporter I
    (1498395500137807932, "Teamoutfit Weißgrün"),     # Test Supporter
]

# IDs aller Team-Rollen (für Button-Berechtigung)
TEAM_ROLE_IDS = set(rid for rid, _ in TEAM_HIERARCHIE) | set(TEAM_ROLES)


# ── Datei-Helpers ─────────────────────────────────────────────────────────────────────

def load_duty():
    if DUTY_FILE.exists():
        with open(DUTY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"on_duty": [], "message_id": None}


def save_duty(data):
    with open(DUTY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Embed Builder ─────────────────────────────────────────────────────────────────────

def build_team_embed(guild: discord.Guild, duty_data: dict) -> discord.Embed:
    on_duty_set = set(duty_data.get("on_duty", []))

    lines     = []
    gesamt    = 0
    on_count  = 0
    off_count = 0

    for role_id, outfit in TEAM_HIERARCHIE:
        role = guild.get_role(role_id)
        if not role:
            continue

        # Rollenname immer anzeigen
        lines.append(f"\n**{role.name}**")

        # Outfit-Text in Kursiv direkt darunter
        if outfit:
            lines.append(f"*{outfit}*")

        mitglieder = [m for m in role.members if not m.bot]

        if not mitglieder:
            lines.append("*(Rolle nicht besetzt)*")
        else:
            for m in sorted(mitglieder, key=lambda x: x.display_name.lower()):
                if m.id in on_duty_set:
                    lines.append(f"> {m.mention} \U0001F7E2")
                    on_count  += 1
                else:
                    lines.append(f"> {m.mention} \U0001F534")
                    off_count += 1
                gesamt += 1

        lines.append("")

    beschreibung = "\n".join(lines)
    beschreibung += (
        "\n\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
        f"\U0001F465 **Aktuelle Teammitglieder gesamt:** {gesamt}\n\n"
        f"\U0001F7E2 **On Duty** ({on_count}) \u2014 *Teammitglied ist aktiv im Support und Co.*\n"
        f"\U0001F534 **Off Duty** ({off_count}) \u2014 *Teammitglied bearbeitet derzeit keine Supportanfragen und Co.*"
    )

    embed = discord.Embed(
        title="\U0001F3C6 Team \u00DCbersicht \u2014 Paradise City Roleplay",
        description=beschreibung,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Team-\u00DCbersicht | Zuletzt aktualisiert")
    return embed


# ── Persistent View ───────────────────────────────────────────────────────────────────

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
        emoji="\U0001F4F1",
        style=discord.ButtonStyle.success,
        custom_id="team_on_duty",
    )
    async def on_duty_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_team(interaction.user):
            await interaction.response.send_message(
                "\u274C Nur Teammitglieder k\u00F6nnen ihren Dienststatus \u00E4ndern.",
                ephemeral=True,
            )
            return

        duty_data = load_duty()
        uid = interaction.user.id
        if uid not in duty_data["on_duty"]:
            duty_data["on_duty"].append(uid)
            save_duty(duty_data)

        await interaction.response.send_message(
            "\u2705 Du bist jetzt **\U0001F7E2 On Duty**.", ephemeral=True
        )
        await self._update_embed(interaction)

    @discord.ui.button(
        label="Off Duty",
        emoji="\U0001F4F5",
        style=discord.ButtonStyle.danger,
        custom_id="team_off_duty",
    )
    async def off_duty_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_team(interaction.user):
            await interaction.response.send_message(
                "\u274C Nur Teammitglieder k\u00F6nnen ihren Dienststatus \u00E4ndern.",
                ephemeral=True,
            )
            return

        duty_data = load_duty()
        uid = interaction.user.id
        if uid in duty_data["on_duty"]:
            duty_data["on_duty"].remove(uid)
            save_duty(duty_data)

        await interaction.response.send_message(
            "\u2705 Du bist jetzt **\U0001F534 Off Duty**.", ephemeral=True
        )
        await self._update_embed(interaction)


# ── Auto Setup ────────────────────────────────────────────────────────────────────────

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
                        if emb.title and "Team \u00DCbersicht" in emb.title:
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


# ── Slash Command: /setup-teamembed ──────────────────────────────────────────────────

@bot.tree.command(
    name="setup-teamembed",
    description="[Team] Löscht das alte Team-Embed und postet ein neues mit allen Änderungen",
    guild=discord.Object(id=GUILD_ID),
)
async def setup_teamembed(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not any(r.id in TEAM_ROLE_IDS | {INHABER_ROLE_ID} for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    for guild in bot.guilds:
        channel = guild.get_channel(TEAM_OVERVIEW_CHANNEL_ID)
        if not channel:
            continue

        duty_data = load_duty()

        # Alle Bot-Nachrichten mit Team-Embed im Kanal löschen
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Team \u00DCbersicht" in emb.title:
                            try:
                                await msg.delete()
                            except Exception:
                                pass
                            break
        except Exception as e:
            print(f"[team_overview] Fehler beim Löschen: {e}")

        # message_id zurücksetzen und neu posten
        duty_data["message_id"] = None
        save_duty(duty_data)

        embed   = build_team_embed(guild, duty_data)
        view    = TeamOverviewView()
        new_msg = await channel.send(embed=embed, view=view)
        duty_data["message_id"] = new_msg.id
        save_duty(duty_data)
        print(f"[team_overview] Neues Embed gepostet in #{channel.name}")

    await interaction.followup.send("\u2705 Team-Embed wurde neu erstellt.", ephemeral=True)
