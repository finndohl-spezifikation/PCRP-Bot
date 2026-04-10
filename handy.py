# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# handy.py — Handy System (Dispatch, Nummer, Apps)
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import log_bot_error
from economy_helpers import (
    has_handy, load_handy_numbers, save_handy_numbers,
    generate_la_phone_number
)


class HandyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ── Dispatch MD ──────────────────────────────────────────
    @discord.ui.button(
        label="🚨 | Dispatch MD",
        style=discord.ButtonStyle.red,
        custom_id="handy_dispatch_md",
        row=0
    )
    async def dispatch_md(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_dispatch(interaction, DISPATCH_MD_ROLE_ID, "MD")

    # ── Dispatch PD ──────────────────────────────────────────
    @discord.ui.button(
        label="🚨 | Dispatch PD",
        style=discord.ButtonStyle.red,
        custom_id="handy_dispatch_pd",
        row=0
    )
    async def dispatch_pd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_dispatch(interaction, DISPATCH_PD_ROLE_ID, "PD")

    # ── Dispatch ADAC ────────────────────────────────────────
    @discord.ui.button(
        label="🚨 | Dispatch ADAC",
        style=discord.ButtonStyle.red,
        custom_id="handy_dispatch_adac",
        row=0
    )
    async def dispatch_adac(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_dispatch(interaction, DISPATCH_ADAC_ROLE_ID, "ADAC")

    # ── Handy Nummer Einsehen ────────────────────────────────
    @discord.ui.button(
        label="📱 | Handy Nummer Einsehen",
        style=discord.ButtonStyle.blurple,
        custom_id="handy_nummer",
        row=1
    )
    async def handy_nummer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "❌ Du besitzt kein Handy. Kaufe es im Shop!",
                ephemeral=True
            )
            return

        numbers = load_handy_numbers()
        uid = str(interaction.user.id)

        if uid not in numbers:
            numbers[uid] = generate_la_phone_number()
            save_handy_numbers(numbers)

        phone = numbers[uid]
        embed = discord.Embed(
            title="📱 Deine Handynummer",
            description=(
                f"**Nummer:** `{phone}`\n"
                f"**Vorwahl:** Los Angeles (LA)\n\n"
                f"*Diese Nummer bleibt dauerhaft dieselbe.*"
            ),
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Nur du siehst diese Nachricht")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Instagram ────────────────────────────────────────────
    @discord.ui.button(
        label="📱 | Instagram",
        style=discord.ButtonStyle.blurple,
        custom_id="handy_instagram",
        row=1
    )
    async def instagram(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "❌ Du besitzt kein Handy. Kaufe es im Shop!",
                ephemeral=True
            )
            return

        guild = interaction.guild
        role  = guild.get_role(INSTAGRAM_ROLE_ID)
        if not role:
            await interaction.response.send_message("❌ Instagram-Rolle nicht gefunden.", ephemeral=True)
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role, reason="Handy: Instagram deinstalliert")
            embed = discord.Embed(
                description="📱 **App Erfolgreich Deinstalliert**\nInstagram wurde von deinem Handy entfernt.",
                color=MOD_COLOR
            )
        else:
            await member.add_roles(role, reason="Handy: Instagram installiert")
            embed = discord.Embed(
                description="📱 **App Erfolgreich Installiert**\nInstagram wurde auf deinem Handy installiert.",
                color=LOG_COLOR
            )
        embed.set_footer(text="Nur du siehst diese Nachricht")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Parship ──────────────────────────────────────────────
    @discord.ui.button(
        label="📱 | Parship",
        style=discord.ButtonStyle.blurple,
        custom_id="handy_parship",
        row=1
    )
    async def parship(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_handy(interaction.user):
            await interaction.response.send_message(
                "❌ Du besitzt kein Handy. Kaufe es im Shop!",
                ephemeral=True
            )
            return

        guild = interaction.guild
        role  = guild.get_role(PARSHIP_ROLE_ID)
        if not role:
            await interaction.response.send_message("❌ Parship-Rolle nicht gefunden.", ephemeral=True)
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role, reason="Handy: Parship deinstalliert")
            embed = discord.Embed(
                description="📱 **App Erfolgreich Deinstalliert**\nParship wurde von deinem Handy entfernt.",
                color=MOD_COLOR
            )
        else:
            await member.add_roles(role, reason="Handy: Parship installiert")
            embed = discord.Embed(
                description="📱 **App Erfolgreich Installiert**\nParship wurde auf deinem Handy installiert.",
                color=LOG_COLOR
            )
        embed.set_footer(text="Nur du siehst diese Nachricht")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def handle_dispatch(interaction: discord.Interaction, role_id: int, dispatch_type: str):
    if not has_handy(interaction.user):
        await interaction.response.send_message(
            "❌ Du besitzt kein Handy. Kaufe es im Shop!",
            ephemeral=True
        )
        return

    guild  = interaction.guild
    member = interaction.user
    role   = guild.get_role(role_id)

    if not role:
        await interaction.response.send_message(
            f"❌ Dispatch-Rolle nicht gefunden.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    dispatch_embed = discord.Embed(
        title="🚨 Dispatch 🚨",
        description=(
            f"**Ein Bewohner hat einen Dispatch abgesendet!**\n\n"
            f"🗺️ **Standort:** {member.mention}\n"
            f"📋 **Dispatch-Typ:** {dispatch_type}\n"
            f"⏰ **Zeit:** <t:{int(datetime.now(timezone.utc).timestamp())}:T>"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    dispatch_embed.set_footer(text=f"Kryptik Roleplay — Dispatch System")

    sent   = 0
    failed = 0
    for target in guild.members:
        if target.bot:
            continue
        if role not in target.roles:
            continue
        try:
            await target.send(embed=dispatch_embed)
            sent += 1
        except Exception:
            failed += 1

    confirm_embed = discord.Embed(
        title="✅ Dispatch gesendet!",
        description=(
            f"Dein **{dispatch_type}-Dispatch** wurde erfolgreich abgesendet.\n"
            f"**Benachrichtigt:** {sent} Einheiten"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.followup.send(embed=confirm_embed, ephemeral=True)


async def auto_handy_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(HANDY_CHANNEL_ID)
        if not channel:
            continue
        embed_exists = False
        try:
            async for msg in channel.history(limit=30):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Handy" in emb.title:
                            embed_exists = True
                            break
                if embed_exists:
                    break
        except Exception:
            pass
        if embed_exists:
            print(f"Handy-Embed bereits vorhanden in #{channel.name}, überspringe.")
            continue
        embed = discord.Embed(
            title="📱 Handy — Einstellungen",
            description=(
                "Willkommen in deinen Handy-Einstellungen!\n\n"
                "Hier kannst du deinen Notruf absetzen, deine Handynummer einsehen "
                "und Social-Media-Apps installieren oder deinstallieren.\n\n"
                "**🚨 Dispatch-Buttons** — Sende einen Notruf an die zuständige Einheit\n"
                "**📱 Handy Nummer** — Zeigt deine persönliche LA-Nummer\n"
                "**📱 Instagram / Parship** — Apps installieren & deinstallieren\n\n"
                "⚠️ *Du benötigst das Item* `📱| Handy` *aus dem Shop, um diese Funktionen zu nutzen.*"
            ),
            color=0x00BFFF,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Kryptik Roleplay — Handy System")
        try:
            await channel.send(embed=embed, view=HandyView())
            print(f"Handy-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_handy_setup fehlgeschlagen", str(e), guild)


async def give_handy_channel_access(guild: discord.Guild, member: discord.Member):
    channel = guild.get_channel(HANDY_CHANNEL_ID)
    if not channel:
        return
    try:
        await channel.set_permissions(
            member,
            view_channel=True,
            send_messages=False,
            read_message_history=True
        )
    except Exception as e:
        await log_bot_error("Handy-Kanal Berechtigung fehlgeschlagen", str(e), guild)
