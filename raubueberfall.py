# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# raubueberfall.py \u2014 Raub\u00FCberfall System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#
# Ablauf:
#   1. Spieler sendet Foto im Bild-Kanal (RAUB_BILD_CHANNEL_ID)
#   2. Bot l\u00F6scht das Foto, postet Beweis-Embed im Team-Kanal
#   3. Team best\u00E4tigt Erfolg oder Fehlschlag
#      Erfolgreich \u2192 7.000\u201313.000 $ + 1\u20136 Bier
#      Fehlschlag  \u2192 Info-DM, kein Geld
#   4. 24h-Cooldown pro Spieler
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

import io
import random
from config import *
from economy_helpers import (
    load_economy, save_economy, get_user, log_money_action
)
from dienst import get_on_duty

# \u2500\u2500 Konstanten \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

RAUB_INFO_CHANNEL_ID = 1490894312727117904   # Info-Embed beim Start
RAUB_BILD_CHANNEL_ID = 1490894314132213771   # Spieler sendet Foto hier
RAUB_TEAM_CHANNEL_ID = 1490878141235855491   # Team News \u2014 Beweis + Buttons

RAUB_BEUTE_MIN  = 7_000
RAUB_BEUTE_MAX  = 13_000
RAUB_BIER_MIN   = 1
RAUB_BIER_MAX   = 6
RAUB_MIN_PDL    = 2   # Mindestanzahl PDLer im Dienst

RAUB_CONFIRM_ROLES = {ADMIN_ROLE_ID, MOD_ROLE_ID}

RAUB_IMAGE_URL = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/raubueberfall.jpg"

# Verhindert Doppel-Einreichungen (user_id)
_pending_raube: set[int] = set()


# \u2500\u2500 Info-Embed (automatisch beim Start) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def build_raub_info_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\U0001F52B Raub\u00FCberfall",
        description=(
            "Plane einen Raub\u00FCberfall und kassiere deine Beute!\n\n"
            "**\U0001F465 Spieler:** Mindestens **2 Personen**\n"
            "**\U0001F694 Beamte:** Mindestens **2 Officers** im Dienst\n"
            "**\u23F1\uFE0F Dauer:** **15 Minuten**\n"
            "**\U0001F4B0 Beute:** zwischen **7.000 $** und **13.000 $** *(zuf\u00E4llig)*\n"
            "**\U0001F37A Bonus:** zwischen **1** und **6 Bier** *(zuf\u00E4llig)*"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="\u26A1 Ablauf",
        value=(
            "1. Raub\u00FCberfall **In-Game** mit min. 2 Spielern starten\n"
            f"2. Foto als Beweis in <#{RAUB_BILD_CHANNEL_ID}> senden\n"
            "3. Team best\u00E4tigt **Erfolg** oder **Fehlschlag**"
        ),
        inline=False
    )
    embed.set_image(url="https://136643ba-e2d7-462a-9d79-80b31d48cd0e-00-1tc3t15bfz4kf.sisko.replit.dev/raubueberfall_bar.png")
    embed.set_footer(text="Paradise City Roleplay \u2022 Raub\u00FCberfall System")
    return embed


# \u2500\u2500 Beweis-Embed (Team News) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_beweis_embed(user: discord.Member, bild_url: str) -> discord.Embed:
    embed = discord.Embed(
        title="\U0001F52B Raub\u00FCberfall \u2014 Beweis eingereicht",
        description=(
            f"{user.mention} hat einen **Raub\u00FCberfall** durchgef\u00FChrt.\n"
            "\u23F3 Bitte Ergebnis best\u00E4tigen."
        ),
        color=0xFF8C00,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F464 Spieler", value=f"{user.mention}\n`{user.display_name}`", inline=True)
    embed.add_field(name="\u23F1\uFE0F Dauer",   value="**15 Minuten**",                          inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay \u2022 Raub\u00FCberfall System | Nur Team")
    return embed


# \u2500\u2500 Ergebnis-Embed \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_result_embed(
    raeuber: discord.Member,
    bild_url: str,
    beute: int,
    bier: int,
    team_member: discord.Member,
    success: bool
) -> discord.Embed:
    if success:
        color = 0x00CC44
        title = "\U0001F52B Raub\u00FCberfall \u2014 Erfolgreich \u2705"
        desc  = (
            f"{raeuber.mention} hat **{beute:,}$** erbeutet \u2192 **Barbestand**.\n"
            f"Zudem erh\u00E4lt er **{bier}x Bier**."
        )
    else:
        color = 0xE74C3C
        title = "\U0001F52B Raub\u00FCberfall \u2014 Fehlgeschlagen \u274C"
        desc  = f"{raeuber.mention} ist **gescheitert**. Festnahme, Verletzung oder Abbruch."

    embed = discord.Embed(title=title, description=desc, color=color,
                          timestamp=datetime.now(timezone.utc))
    embed.add_field(name="\U0001F464 Spieler",       value=raeuber.mention,    inline=True)
    embed.add_field(name="\u2705 Best\u00E4tigt von", value=team_member.mention, inline=True)
    if success:
        embed.add_field(name="\U0001F4B0 Beute",  value=f"**{beute:,}$**", inline=True)
        embed.add_field(name="\U0001F37A Bonus",  value=f"**{bier}x Bier**", inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay \u2022 Raub\u00FCberfall System")
    return embed


# \u2500\u2500 Team-Button-View \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class RaubView(discord.ui.View):
    def __init__(self, raeuber_id: int, bild_url: str):
        super().__init__(timeout=None)
        self.raeuber_id = raeuber_id
        self.bild_url   = bild_url

    def _check_team(self, interaction: discord.Interaction) -> bool:
        return bool({r.id for r in interaction.user.roles} & RAUB_CONFIRM_ROLES)

    @discord.ui.button(label="\u2705  Erfolgreich", style=discord.ButtonStyle.success, custom_id="raubueberfall:erfolg")
    async def erfolg_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("\u274C Nur Team-Mitglieder k\u00F6nnen best\u00E4tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("\u274C Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        beute = random.randint(RAUB_BEUTE_MIN, RAUB_BEUTE_MAX)
        bier  = random.randint(RAUB_BIER_MIN, RAUB_BIER_MAX)

        eco = load_economy()
        user_data = get_user(eco, self.raeuber_id)
        user_data["cash"] = user_data.get("cash", 0) + beute
        for _ in range(bier):
            user_data.setdefault("inventory", []).append("Bier")
        save_economy(eco)

        await log_money_action(
            interaction.guild,
            "Raub\u00FCberfall Beute",
            f"{raeuber.mention} hat einen Raub\u00FCberfall durchgef\u00FChrt.\n"
            f"**Beute:** {beute:,}$ \u2192 Barbestand\n"
            f"**Bonus:** {bier}x Bier\n"
            f"**Best\u00E4tigt von:** {interaction.user.mention}"
        )

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(raeuber, self.bild_url, beute, bier, interaction.user, success=True),
            view=self
        )
        await interaction.response.send_message(
            f"\u2705 Raub von {raeuber.mention} als **Erfolgreich** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="\U0001F52B Raub\u00FCberfall \u2014 Erfolgreich! \U0001F4B0",
                description=(
                    f"Dein Raub\u00FCberfall war **erfolgreich**!\n\n"
                    f"**{beute:,}$** wurden in deinen **Barbestand** \u00FCbertragen.\n"
                    f"Zus\u00E4tzlich erh\u00E4ltst du **{bier}x Bier**."
                ),
                color=0x00CC44,
                timestamp=datetime.now(timezone.utc)
            )
            dm.add_field(name="\U0001F4B5 Beute",          value=f"**{beute:,}$**",   inline=True)
            dm.add_field(name="\U0001F37A Bonus",          value=f"**{bier}x Bier**", inline=True)
            dm.add_field(name="\U0001F4CD Gutgeschrieben", value="Barbestand (Cash)", inline=True)
            dm.set_footer(text="Paradise City Roleplay \u2022 Raub\u00FCberfall System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raube.discard(self.raeuber_id)

    @discord.ui.button(label="\u274C  Fehlschlag", style=discord.ButtonStyle.danger, custom_id="raubueberfall:fehlschlag")
    async def fehlschlag_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("\u274C Nur Team-Mitglieder k\u00F6nnen best\u00E4tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("\u274C Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        eco = load_economy()
        user_data = get_user(eco, self.raeuber_id)
        user_data["raub_last_raid"] = None
        save_economy(eco)

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(raeuber, self.bild_url, 0, 0, interaction.user, success=False),
            view=self
        )
        await interaction.response.send_message(
            f"\u2705 Raub von {raeuber.mention} als **Fehlschlag** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="\U0001F52B Raub\u00FCberfall \u2014 Fehlgeschlagen \u274C",
                description=(
                    "Dein Raub\u00FCberfall ist **fehlgeschlagen**.\n\n"
                    "\u2022 \U0001F694 Festnahme durch Officers\n"
                    "\u2022 \U0001F3E5 Verletzung / Tod\n"
                    "\u2022 \U0001F3F3\uFE0F Abbruch\n\n"
                    "Du erh\u00E4ltst **keine Beute**."
                ),
                color=0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            dm.set_footer(text="Paradise City Roleplay \u2022 Raub\u00FCberfall System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raube.discard(self.raeuber_id)


# \u2500\u2500 on_message \u2014 Foto-Erkennung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.listen("on_message")
async def raubueberfall_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if not RAUB_BILD_CHANNEL_ID or message.channel.id != RAUB_BILD_CHANNEL_ID:
        return

    attachment = None
    for att in message.attachments:
        if att.content_type and att.content_type.startswith("image/"):
            attachment = att
            break

    if not attachment:
        return

    user = message.author

    # \u2500\u2500 PDL-Pflicht pr\u00FCfen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    on_duty_lapd = get_on_duty("lapd")
    if len(on_duty_lapd) < RAUB_MIN_PDL:
        try:
            await message.reply(
                f"\u274C F\u00FCr einen Raub\u00FCberfall m\u00FCssen mindestens **{RAUB_MIN_PDL} Officers** im Dienst sein.\n"
                f"Aktuell im Dienst: **{len(on_duty_lapd)}**",
                delete_after=15
            )
        except discord.Forbidden:
            pass
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        return

    # \u2500\u2500 24h-Cooldown pr\u00FCfen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    eco       = load_economy()
    user_data = get_user(eco, user.id)
    last_raid = user_data.get("raub_last_raid")
    if last_raid:
        last_dt   = datetime.fromisoformat(last_raid)
        vergangen = (datetime.now(timezone.utc) - last_dt).total_seconds()
        if vergangen < 86400:
            verbleibend = int((86400 - vergangen) / 3600)
            minuten     = int(((86400 - vergangen) % 3600) / 60)
            try:
                await message.reply(
                    f"\u23F3 Du kannst erst in **{verbleibend}h {minuten}min** wieder einen Raub\u00FCberfall machen.",
                    delete_after=15
                )
            except discord.Forbidden:
                pass
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return

    if user.id in _pending_raube:
        try:
            await message.reply(
                "\u23F3 Du hast bereits einen laufenden Raub\u00FCberfall eingereicht. Warte auf das Ergebnis.",
                delete_after=10
            )
        except discord.Forbidden:
            pass
        return

    # \u2500\u2500 Bild-Bytes sofort sichern \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    try:
        img_bytes    = await attachment.read()
        img_filename = attachment.filename or "beweis.jpg"
    except Exception:
        return

    _pending_raube.add(user.id)

    # \u2500\u2500 24h-Cooldown setzen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    user_data["raub_last_raid"] = datetime.now(timezone.utc).isoformat()
    save_economy(eco)

    try:
        await message.delete()
    except discord.Forbidden:
        pass

    # \u2500\u2500 Beweis ins Team-Channel \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    team_channel = message.guild.get_channel(RAUB_TEAM_CHANNEL_ID)
    if not team_channel:
        _pending_raube.discard(user.id)
        return

    bild_url = ""
    view     = RaubView(raeuber_id=user.id, bild_url="")
    file     = discord.File(io.BytesIO(img_bytes), filename=img_filename)
    embed    = _build_beweis_embed(user, f"attachment://{img_filename}")
    sent_msg = await team_channel.send(file=file, embed=embed, view=view)
    if sent_msg.attachments:
        bild_url      = sent_msg.attachments[0].url
        view.bild_url = bild_url

    # \u2500\u2500 Best\u00E4tigungs-DM an Spieler \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    try:
        dm = discord.Embed(
            title="\U0001F52B Raub\u00FCberfall \u2014 Beweis eingereicht \u2705",
            description=(
                "Dein Beweis wurde erfolgreich eingereicht!\n\n"
                "Du hast ab jetzt **15 Minuten** Zeit."
            ),
            color=0xFF8C00,
            timestamp=datetime.now(timezone.utc)
        )
        dm.set_footer(text="Paradise City Roleplay \u2022 Raub\u00FCberfall System")
        await user.send(embed=dm)
    except discord.Forbidden:
        pass

    # \u2500\u2500 PDLer benachrichtigen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    for uid_str in on_duty_lapd:
        try:
            member = message.guild.get_member(int(uid_str))
            if not member:
                continue
            cop_embed = discord.Embed(
                title="\U0001F694 LAPD \u2014 Raub\u00FCberfall gemeldet!",
                description=(
                    f"**Verd\u00E4chtiger:** {user.mention} (`{user.display_name}`)"
                ),
                color=0x1E90FF,
                timestamp=datetime.now(timezone.utc)
            )
            cop_embed.set_thumbnail(url=user.display_avatar.url)
            if bild_url:
                cop_embed.set_image(url=bild_url)
            cop_embed.set_footer(text="Paradise City Roleplay \u2022 LAPD")
            await member.send(embed=cop_embed)
        except discord.Forbidden:
            pass


# \u2500\u2500 Auto-Setup beim Start \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _raub_info_auto_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(RAUB_INFO_CHANNEL_ID)
        if not channel:
            print(f"[raubueberfall] \u274C Kanal {RAUB_INFO_CHANNEL_ID} nicht gefunden")
            continue
        try:
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and msg.embeds:
                    print(f"[raubueberfall] \u2139\uFE0F Info-Embed bereits vorhanden, kein neues gesendet.")
                    break
            else:
                await channel.send(embed=build_raub_info_embed())
                print(f"[raubueberfall] \u2705 Info-Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[raubueberfall] \u274C Fehler beim Senden: {e}")


@bot.listen("on_ready")
async def raubueberfall_on_ready():
    await _raub_info_auto_setup()
