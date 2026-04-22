# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# shop_raub.py \u2014 Shop-Raub System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#
# Ablauf:
#   1. Spieler sendet Foto im Bild-Kanal (SHOP_RAUB_BILD_CHANNEL_ID)
#   2. Bot l\xf6scht das Foto, postet Beweis-Embed im Team-Kanal
#   3. Team best\xe4tigt Erfolg oder Fehlschlag
#      Erfolgreich \u2192 10.000 / 20.000 / 35.000 $ (zuf\xe4llig)
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

SHOP_RAUB_INFO_CHANNEL_ID = 1490894310118392012   # Info-Embed beim Start
SHOP_RAUB_BILD_CHANNEL_ID = 1490894311389134858   # Spieler sendet Foto hier
SHOP_RAUB_TEAM_CHANNEL_ID = 1490878141235855491   # Team News \u2014 Beweis + Buttons

BEUTE_MIN = 12_000
BEUTE_MAX = 22_000

SHOP_RAUB_CONFIRM_ROLES = {ADMIN_ROLE_ID, MOD_ROLE_ID}

SHOP_RAUB_IMAGE_URL = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/shop_raub.jpg?v=2"

# Verhindert Doppel-Einreichungen (user_id)
_pending_shop_raids: set[int] = set()


# \u2500\u2500 Info-Embed (automatisch beim Start) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def build_shop_raub_info_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\U0001f3ea Shop-Raub",
        description=(
            "Raube einen der Shops in Los Angeles aus und kassiere deine Beute!\\n\\n"
            "**\U0001f4cd Ort:** Shops in **Los Angeles**\\n"
            "**\U0001f465 Spieler:** **2\u20133 Personen** empfohlen\\n"
            "**\U0001f694 Beamte:** Mindestens **2 Officers** im Dienst\\n"
            "**\u23f1\ufe0f Dauer:** **15 Minuten**\\n"
            "**\U0001f4b0 Beute:** zwischen **12.000 $** und **22.000 $** *(zuf\xe4llig)*"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="\u26a1 Ablauf",
        value=(
            "1. Raub **In-Game** mit 2\u20133 Spielern starten\\n"
            f"2. Foto als Beweis in <#{SHOP_RAUB_BILD_CHANNEL_ID}> senden\\n"
            "3. Team best\xe4tigt **Erfolg** oder **Fehlschlag**"
        ),
        inline=False
    )
    embed.set_image(url=SHOP_RAUB_IMAGE_URL)
    embed.set_footer(text="Paradise City Roleplay \u2022 Shop-Raub System")
    return embed



# \u2500\u2500 Beweis-Embed (Team News) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_beweis_embed(user: discord.Member, bild_url: str) -> discord.Embed:
    embed = discord.Embed(
        title="\U0001f3ea Shop-Raub \u2014 Beweis eingereicht",
        description=(
            f"{user.mention} hat einen **Shop-Raub** durchgef\xfchrt.\\n"
            "\u23f3 Bitte Ergebnis best\xe4tigen."
        ),
        color=0xFF8C00,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001f464 Spieler",  value=f"{user.mention}\\n`{user.display_name}`", inline=True)
    embed.add_field(name="\u23f1\ufe0f Dauer",    value="**15 Minuten**",                          inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay \u2022 Shop-Raub System | Nur Team")
    return embed


# \u2500\u2500 Ergebnis-Embed \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_result_embed(
    raeuber: discord.Member,
    bild_url: str,
    beute: int,
    team_member: discord.Member,
    success: bool
) -> discord.Embed:
    if success:
        color = 0x00CC44
        title = "\U0001f3ea Shop-Raub \u2014 Erfolgreich \u2705"
        desc  = f"{raeuber.mention} hat **{beute:,}$** erbeutet \u2192 **Barbestand**."
    else:
        color = 0xE74C3C
        title = "\U0001f3ea Shop-Raub \u2014 Fehlgeschlagen \u274c"
        desc  = f"{raeuber.mention} ist **gescheitert**. Festnahme, Verletzung oder Abbruch."

    embed = discord.Embed(title=title, description=desc, color=color,
                          timestamp=datetime.now(timezone.utc))
    embed.add_field(name="\U0001f464 Spieler",       value=raeuber.mention,    inline=True)
    embed.add_field(name="\u2705 Best\xe4tigt von", value=team_member.mention, inline=True)
    if success:
        embed.add_field(name="\U0001f4b0 Beute", value=f"**{beute:,}$**", inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay \u2022 Shop-Raub System")
    return embed


# \u2500\u2500 Team-Button-View \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class ShopRaubView(TimedDisableView):
    def __init__(self, raeuber_id: int, bild_url: str):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.raeuber_id = raeuber_id
        self.bild_url   = bild_url

    def _check_team(self, interaction: discord.Interaction) -> bool:
        return bool({r.id for r in interaction.user.roles} & SHOP_RAUB_CONFIRM_ROLES)

    @discord.ui.button(label="\u2705  Erfolgreich", style=discord.ButtonStyle.success, custom_id="shop_raub:erfolg")
    async def erfolg_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("\u274c Nur Team-Mitglieder k\xf6nnen best\xe4tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("\u274c Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        beute = random.randint(BEUTE_MIN, BEUTE_MAX)

        eco = load_economy()
        user_data = get_user(eco, self.raeuber_id)
        user_data["cash"] = user_data.get("cash", 0) + beute
        save_economy(eco)

        await log_money_action(
            interaction.guild,
            "Shop-Raub Beute",
            f"{raeuber.mention} hat einen Shop ausgeraubt.\\n"
            f"**Beute:** {beute:,}$ \u2192 Barbestand\\n"
            f"**Best\xe4tigt von:** {interaction.user.mention}"
        )

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(raeuber, self.bild_url, beute, interaction.user, success=True),
            view=self
        )
        await interaction.response.send_message(
            f"\u2705 Raub von {raeuber.mention} als **Erfolgreich** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="\U0001f3ea Shop-Raub \u2014 Erfolgreich! \U0001f4b0",
                description=(
                    f"Dein Shop-Raub war **erfolgreich**!\\n\\n"
                    f"**{beute:,}$** wurden in deinen **Barbestand** \xfcbertragen."
                ),
                color=0x00CC44,
                timestamp=datetime.now(timezone.utc)
            )
            dm.add_field(name="\U0001f4b5 Beute",          value=f"**{beute:,}$**",  inline=True)
            dm.add_field(name="\U0001f4cd Gutgeschrieben", value="Barbestand (Cash)", inline=True)
            dm.set_footer(text="Paradise City Roleplay \u2022 Shop-Raub System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_shop_raids.discard(self.raeuber_id)

    @discord.ui.button(label="\u274c  Fehlschlag", style=discord.ButtonStyle.danger, custom_id="shop_raub:fehlschlag")
    async def fehlschlag_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("\u274c Nur Team-Mitglieder k\xf6nnen best\xe4tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("\u274c Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        # Cooldown zur\xfccksetzen bei Fehlschlag
        eco = load_economy()
        user_data = get_user(eco, self.raeuber_id)
        user_data["shop_raub_last_raid"] = None
        save_economy(eco)

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(raeuber, self.bild_url, 0, interaction.user, success=False),
            view=self
        )
        await interaction.response.send_message(
            f"\u2705 Raub von {raeuber.mention} als **Fehlschlag** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="\U0001f3ea Shop-Raub \u2014 Fehlgeschlagen \u274c",
                description=(
                    "Dein Shop-Raub ist **fehlgeschlagen**.\\n\\n"
                    "\u2022 \U0001f694 Festnahme durch LAPD\\n"
                    "\u2022 \U0001f3e5 Verletzung / Tod\\n"
                    "\u2022 \U0001f3f3\ufe0f Abbruch\\n\\n"
                    "Du erh\xe4ltst **keine Beute**."
                ),
                color=0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            dm.set_footer(text="Paradise City Roleplay \u2022 Shop-Raub System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_shop_raids.discard(self.raeuber_id)


# \u2500\u2500 on_message \u2014 Foto-Erkennung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.listen("on_message")
async def shop_raub_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != SHOP_RAUB_BILD_CHANNEL_ID:
        return

    attachment = None
    for att in message.attachments:
        if att.content_type and att.content_type.startswith("image/"):
            attachment = att
            break

    if not attachment:
        return

    user = message.author

    # \u2500\u2500 Officer-Pflicht pr\xfcfen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    on_duty_lapd = get_on_duty("lapd")
    if len(on_duty_lapd) < 2:
        try:
            await message.reply(
                "\u274c F\xfcr einen Shop-Raub m\xfcssen mindestens **2 Officers** im Dienst sein.\\n"
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

    # \u2500\u2500 24h-Cooldown pr\xfcfen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    eco       = load_economy()
    user_data = get_user(eco, user.id)
    last_raid = user_data.get("shop_raub_last_raid")
    if last_raid:
        last_dt   = datetime.fromisoformat(last_raid)
        vergangen = (datetime.now(timezone.utc) - last_dt).total_seconds()
        if vergangen < 86400:
            verbleibend = int((86400 - vergangen) / 3600)
            minuten     = int(((86400 - vergangen) % 3600) / 60)
            try:
                await message.reply(
                    f"\u23f3 Du kannst erst in **{verbleibend}h {minuten}min** wieder einen Shop ausrauben.",
                    delete_after=15
                )
            except discord.Forbidden:
                pass
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return

    if user.id in _pending_shop_raids:
        try:
            await message.reply(
                "\u23f3 Du hast bereits einen laufenden Raub eingereicht. Warte auf das Ergebnis.",
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

    _pending_shop_raids.add(user.id)

    # \u2500\u2500 24h-Cooldown setzen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    user_data["shop_raub_last_raid"] = datetime.now(timezone.utc).isoformat()
    save_economy(eco)

    try:
        await message.delete()
    except discord.Forbidden:
        pass

    # \u2500\u2500 Beweis ins Team-Channel (Bild + Embed + Buttons) \u2500\u2500\u2500\u2500\u2500\u2500\u2500
    team_channel = message.guild.get_channel(SHOP_RAUB_TEAM_CHANNEL_ID)
    if not team_channel:
        _pending_shop_raids.discard(user.id)
        return

    bild_url = ""
    view     = ShopRaubView(raeuber_id=user.id, bild_url="")
    file     = discord.File(io.BytesIO(img_bytes), filename=img_filename)
    embed    = _build_beweis_embed(user, f"attachment://{img_filename}")
    sent_msg = await team_channel.send(file=file, embed=embed, view=view)
    if sent_msg.attachments:
        bild_url      = sent_msg.attachments[0].url
        view.bild_url = bild_url

    # \u2500\u2500 Best\xe4tigungs-DM an Spieler \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    try:
        dm = discord.Embed(
            title="\U0001f3ea Shop-Raub \u2014 Beweis eingereicht \u2705",
            description=(
                "Dein Beweis wurde erfolgreich eingereicht!\\n\\n"
                "Du hast ab jetzt **15 Minuten** Zeit."
            ),
            color=0xFF8C00,
            timestamp=datetime.now(timezone.utc)
        )
        dm.set_footer(text="Paradise City Roleplay \u2022 Shop-Raub System")
        await user.send(embed=dm)
    except discord.Forbidden:
        pass

    # \u2500\u2500 LAPD benachrichtigen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    for uid_str in on_duty_lapd:
        try:
            member = message.guild.get_member(int(uid_str))
            if not member:
                continue
            cop_embed = discord.Embed(
                title="\U0001f694 LAPD \u2014 Shop-Raub gemeldet!",
                description=(
                    f"**Verd\xe4chtiger:** {user.mention} (`{user.display_name}`)"
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

async def _shop_raub_info_auto_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(SHOP_RAUB_INFO_CHANNEL_ID)
        if not channel:
            continue

        embed        = build_shop_raub_info_embed()
        existing_msg = None
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Shop-Raub" in emb.title:
                            existing_msg = msg
                            break
                if existing_msg:
                    break
        except Exception:
            pass

        try:
            if existing_msg:
                await existing_msg.edit(embed=embed)
                print(f"[shop_raub] \u2705 Info-Embed aktualisiert in #{channel.name}")
            else:
                await channel.send(embed=embed)
                print(f"[shop_raub] \u2705 Info-Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[shop_raub] \u274c Fehler beim Senden: {e}")


@bot.listen("on_ready")
async def shop_raub_on_ready():
    await _shop_raub_info_auto_setup()

