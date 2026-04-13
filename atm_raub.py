# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# atm_raub.py — ATM-Raub System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════
#
# Ablauf:
#   1. Spieler sendet ein Foto im Bild-Kanal (ATM_BILD_CHANNEL_ID)
#   2. Bot postet automatisch im Raub-Kanal (ATM_RAUB_CHANNEL_ID):
#      → Embed mit dem Bild + Spieler-Info + Erfolgreich/Fehlschlag Buttons
#   3. Alle LAPD-Beamten im Dienst erhalten eine DM
#   4. Team drückt einen Button → Ergebnis-DM an den Spieler
#      Erfolgreich → zufällige Beute (7.000$–15.000$) in Barbestand
#      Fehlschlag  → keine Beute, Info-DM
# ══════════════════════════════════════════════════════════════

import random
from config import *
from economy_helpers import (
    load_economy, save_economy, get_user, log_money_action
)
from dienst import get_on_duty

# ── Konstanten ────────────────────────────────────────────────

ATM_BILD_CHANNEL_ID  = 1490894309145313330   # Kanal wo Spieler das Foto sendet
ATM_RAUB_CHANNEL_ID  = 1490894308088352961   # Kanal wo Bot das Embed + Buttons postet

BEUTE_MIN            = 7_000
BEUTE_MAX            = 15_000
NIETE_CHANCE         = 0.15   # 15% Chance – Farbbombe geplatzt → 0$

ATM_CONFIRM_ROLES    = {ADMIN_ROLE_ID, MOD_ROLE_ID}

ATM_IMAGE_URL        = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/atm_raub.jpg"

# user_id → True (verhindert Doppel-Einreichungen)
_pending_raids: set[int] = set()


# ── Info-Embed (automatisch beim Start gepostet) ──────────────

def build_atm_info_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏧 ATM-Raub",
        description=(
            "**💰 Beute:** 7.000$ – 15.000$ *(zufällig, Niete möglich)*\n"
            "**📍 Ort:** Nur ATMs innerhalb **Los Santos**\n"
            "**👤 Spieler:** Ab **1 Person** möglich"
        ),
        color=0xFF4500,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="🎒 Benötigte Items",
        value=(
            "🔧 **Brecheisen** → 5 Min. Dauer\n"
            "💣 **Plastiksprengstoff** → 3 Min. Dauer\n"
            f"*(Schwarzmarkt: <#{1492977067665526804}>)*"
        ),
        inline=True
    )
    embed.add_field(
        name="⚡ Ablauf",
        value=(
            f"1. Raub **In-Game** durchführen\n"
            f"2. Foto als Beweis in <#{ATM_BILD_CHANNEL_ID}> senden\n"
            f"3. Team bestätigt **Erfolg** oder **Fehlschlag**"
        ),
        inline=True
    )
    embed.set_thumbnail(url=ATM_IMAGE_URL)
    embed.set_footer(text="Paradise City Roleplay • ATM-System")
    return embed


# ── Beweis-Embed (wird im Raub-Kanal gepostet) ────────────────

def build_beweis_embed(user: discord.Member, bild_url: str) -> discord.Embed:
    embed = discord.Embed(
        title="🏧 ATM-Raub — Beweis eingereicht",
        description=(
            f"{user.mention} hat einen **ATM-Raub** durchgeführt und einen Beweis eingereicht.\n\n"
            "⏳ **Wartet auf Team-Bestätigung...**"
        ),
        color=0xFF8C00,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="👤 Spieler", value=f"{user.mention}\n`{user.display_name}`", inline=True)
    embed.add_field(name="📸 Beweis", value="Bild unten ↓", inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay • ATM-System | Nur Team kann bestätigen")
    return embed


# ── Ergebnis-Embed ────────────────────────────────────────────

def _build_result_embed(
    raeuber: discord.Member,
    bild_url: str,
    beute: int,
    niete: bool,
    team_member: discord.Member,
    success: bool
) -> discord.Embed:
    if success and not niete:
        color = 0x00CC44
        title = "🏧 ATM-Raub — Erfolgreich ✅"
        desc  = (
            f"{raeuber.mention} hat erfolgreich einen ATM ausgeraubt!\n"
            f"**{beute:,}$** wurden in den **Barbestand** übertragen."
        )
    elif success and niete:
        color = 0xFF8C00
        title = "🏧 ATM-Raub — Farbbombe geplatzt 💣"
        desc  = f"{raeuber.mention} hat den ATM geknackt, aber die **Farbbombe ist geplatzt**. Keine Beute."
    else:
        color = 0xE74C3C
        title = "🏧 ATM-Raub — Fehlgeschlagen ❌"
        desc  = f"{raeuber.mention} ist **gescheitert**. Festnahme, Verletzung oder Abbruch."

    embed = discord.Embed(title=title, description=desc, color=color,
                          timestamp=datetime.now(timezone.utc))
    embed.add_field(name="👤 Spieler", value=raeuber.mention, inline=True)
    embed.add_field(name="✅ Bestätigt von", value=team_member.mention, inline=True)
    if success and not niete:
        embed.add_field(name="💰 Beute", value=f"**{beute:,}$**", inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay • ATM-System")
    return embed


# ── Button-View ───────────────────────────────────────────────

class AtmRaubView(discord.ui.View):
    def __init__(self, raeuber_id: int, bild_url: str):
        super().__init__(timeout=None)
        self.raeuber_id = raeuber_id
        self.bild_url   = bild_url

    def _check_team(self, interaction: discord.Interaction) -> bool:
        role_ids = {r.id for r in interaction.user.roles}
        return bool(role_ids & ATM_CONFIRM_ROLES)

    @discord.ui.button(
        label="✅  Erfolgreich",
        style=discord.ButtonStyle.success,
        custom_id="atm_raub:erfolg"
    )
    async def erfolg_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message(
                "❌ Nur Team-Mitglieder können den Raub bestätigen.", ephemeral=True
            )
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message(
                "❌ Spieler nicht mehr auf dem Server.", ephemeral=True
            )
            return

        niete = random.random() < NIETE_CHANCE
        beute = 0 if niete else random.randint(BEUTE_MIN, BEUTE_MAX)

        if beute > 0:
            eco = load_economy()
            user_data = get_user(eco, self.raeuber_id)
            user_data["cash"] = user_data.get("cash", 0) + beute
            save_economy(eco)
            await log_money_action(
                interaction.guild,
                "ATM-Raub Beute",
                f"{raeuber.mention} hat einen ATM ausgeraubt.\n"
                f"**Beute:** {beute:,}$ → Barbestand\n"
                f"**Bestätigt von:** {interaction.user.mention}"
            )

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(raeuber, self.bild_url, beute, niete, interaction.user, success=True),
            view=self
        )
        await interaction.response.send_message(
            f"✅ Raub von {raeuber.mention} als **Erfolgreich** markiert.", ephemeral=True
        )

        try:
            if niete:
                dm = discord.Embed(
                    title="🏧 ATM-Raub — Pech gehabt! 💣",
                    description=(
                        "Dein ATM-Raub war technisch erfolgreich, aber...\n"
                        "**Die Farbbombe ist geplatzt!**\n\n"
                        "Du gehst leider **leer aus** — kein Geld diesmal."
                    ),
                    color=0xFF4500,
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                dm = discord.Embed(
                    title="🏧 ATM-Raub — Erfolgreich! 💰",
                    description=(
                        f"Dein ATM-Raub war **erfolgreich**!\n\n"
                        f"**{beute:,}$** wurden direkt in deinen **Barbestand** übertragen."
                    ),
                    color=0x00CC44,
                    timestamp=datetime.now(timezone.utc)
                )
                dm.add_field(name="💵 Beute", value=f"**{beute:,}$**", inline=True)
                dm.add_field(name="📍 Gutgeschrieben", value="Barbestand (Cash)", inline=True)
            dm.set_footer(text="Paradise City Roleplay • ATM-System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raids.discard(self.raeuber_id)

    @discord.ui.button(
        label="❌  Fehlschlag",
        style=discord.ButtonStyle.danger,
        custom_id="atm_raub:fehlschlag"
    )
    async def fehlschlag_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message(
                "❌ Nur Team-Mitglieder können den Raub bestätigen.", ephemeral=True
            )
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message(
                "❌ Spieler nicht mehr auf dem Server.", ephemeral=True
            )
            return

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(raeuber, self.bild_url, 0, False, interaction.user, success=False),
            view=self
        )
        await interaction.response.send_message(
            f"✅ Raub von {raeuber.mention} als **Fehlschlag** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="🏧 ATM-Raub — Fehlgeschlagen ❌",
                description=(
                    "Dein ATM-Raub ist **fehlgeschlagen**.\n\n"
                    "Mögliche Gründe:\n"
                    "• 🚔 Du wurdest festgenommen\n"
                    "• 🏥 Du wurdest verletzt oder getötet\n"
                    "• 🏳️ Der Raub wurde abgebrochen\n\n"
                    "Du erhältst **keine Beute**. Beim nächsten Mal mehr Glück!"
                ),
                color=0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            dm.set_footer(text="Paradise City Roleplay • ATM-System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raids.discard(self.raeuber_id)


# ── on_message — Bild-Erkennung ───────────────────────────────

@bot.listen("on_message")
async def atm_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != ATM_BILD_CHANNEL_ID:
        return

    bild_url = None
    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            bild_url = attachment.url
            break

    if not bild_url:
        return

    user = message.author

    if user.id in _pending_raids:
        try:
            await message.reply(
                "⏳ Du hast bereits einen laufenden Raub eingereicht. Warte bis dieser abgeschlossen ist.",
                delete_after=10
            )
        except discord.Forbidden:
            pass
        return

    _pending_raids.add(user.id)

    raub_channel = message.guild.get_channel(ATM_RAUB_CHANNEL_ID)
    if not raub_channel:
        _pending_raids.discard(user.id)
        return

    view  = AtmRaubView(raeuber_id=user.id, bild_url=bild_url)
    embed = build_beweis_embed(user, bild_url)
    await raub_channel.send(embed=embed, view=view)

    try:
        await message.add_reaction("✅")
    except discord.Forbidden:
        pass

    on_duty_lapd = get_on_duty("lapd")
    for uid_str in on_duty_lapd:
        try:
            member = message.guild.get_member(int(uid_str))
            if not member:
                continue
            cop_embed = discord.Embed(
                title="🚔 LAPD — ATM-Raub gemeldet!",
                description=(
                    "Ein **ATM-Raub** wurde eingereicht!\n\n"
                    f"**Verdächtiger:** {user.mention} (`{user.display_name}`)\n\n"
                    f"Prüfe den Kanal <#{ATM_RAUB_CHANNEL_ID}> für Details."
                ),
                color=0x1E90FF,
                timestamp=datetime.now(timezone.utc)
            )
            cop_embed.set_thumbnail(url=user.display_avatar.url)
            cop_embed.set_image(url=bild_url)
            cop_embed.set_footer(text="Paradise City Roleplay • LAPD Benachrichtigung")
            await member.send(embed=cop_embed)
        except discord.Forbidden:
            pass


# ── Auto-Setup beim Start ─────────────────────────────────────

async def _atm_info_auto_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(ATM_RAUB_CHANNEL_ID)
        if not channel:
            continue

        embed = build_atm_info_embed()

        existing_msg = None
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "ATM-Raub" in emb.title and "Informationen" in emb.title:
                            existing_msg = msg
                            break
                if existing_msg:
                    break
        except Exception:
            pass

        try:
            if existing_msg:
                await existing_msg.edit(embed=embed)
                print(f"[atm_raub] ✅ Info-Embed aktualisiert in #{channel.name}")
            else:
                await channel.send(embed=embed)
                print(f"[atm_raub] ✅ Info-Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[atm_raub] ❌ Fehler: {e}")


@bot.listen("on_ready")
async def atm_raub_on_ready():
    await _atm_info_auto_setup()
