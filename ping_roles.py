# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# ping_roles.py — Ping-Rollen Auswahl (Hinzufügen / Entfernen)
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

import discord
from config import bot

PING_ROLES_CHANNEL_ID = 1490882567690518579

PING_ROLE_IDS = [
    1490855734517174376,
    1490855737130221598,
    1490855739495813150,
    1490855738644365603,
    1490855733124923486,
    1490855740435468320,
]

PING_ROLES_COLOR = 0xE67E22


class PingRoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str = "Ping-Rolle"):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.blurple,
            custom_id=f"ping_role_{role_id}"
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message(
                "❌ Rolle nicht gefunden.", ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role, reason="Ping-Rolle selbst entfernt")
            await interaction.response.send_message(
                f"✅ {role.mention} wurde **entfernt**.", ephemeral=True
            )
        else:
            await interaction.user.add_roles(role, reason="Ping-Rolle selbst hinzugefügt")
            await interaction.response.send_message(
                f"✅ {role.mention} wurde **hinzugefügt**.", ephemeral=True
            )


class PingRolesView(discord.ui.View):
    def __init__(self, guild: discord.Guild = None):
        super().__init__(timeout=None)
        for role_id in PING_ROLE_IDS:
            label = "Ping-Rolle"
            if guild:
                role = guild.get_role(role_id)
                if role:
                    label = role.name
            self.add_item(PingRoleButton(role_id=role_id, label=label))


async def auto_ping_roles_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(PING_ROLES_CHANNEL_ID)
        if not channel:
            continue

        role_list = ""
        for role_id in PING_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                role_list += f"• {role.mention}\n"

        embed = discord.Embed(
            title="🔔 Ping-Rollen",
            description=(
                "Hier kannst du deine Ping-Rollen selbst auswählen.\n"
                "Klicke auf einen Button um eine Rolle **hinzuzufügen** oder zu **entfernen**.\n\n"
                f"{role_list}"
            ),
            color=PING_ROLES_COLOR,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Paradise City Roleplay — Ping-Rollen System")
        view = PingRolesView(guild)

        # Vorhandenes Embed suchen und aktualisieren
        existing_msg = None
        try:
            async for msg in channel.history(limit=30):
                if msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Ping" in emb.title:
                            existing_msg = msg
                            break
                if existing_msg:
                    break
        except Exception:
            pass

        try:
            if existing_msg and existing_msg.author.id == bot.user.id:
                await existing_msg.edit(embed=embed, view=view)
                print(f"[ping_roles] ✅ Ping-Rollen Embed aktualisiert in #{channel.name}")
            else:
                # Fremde Embeds (z.B. alter Bot) löschen falls möglich
                if existing_msg:
                    try:
                        await existing_msg.delete()
                    except Exception:
                        pass
                await channel.send(embed=embed, view=view)
                print(f"[ping_roles] ✅ Ping-Rollen Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[ping_roles] ❌ Fehler: {e}")


@bot.listen("on_ready")
async def ping_roles_on_ready():
    for guild in bot.guilds:
        bot.add_view(PingRolesView(guild))
        break
    await auto_ping_roles_setup()
