# -*- coding: utf-8 -*-
# \\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550
# human_labs_raub.py \\u2014 Humane Labs Raub\\u00FCberfall System
# Paradise City Roleplay Discord Bot
#
# Ablauf:
#   1. Spieler sendet Foto im Bild-Kanal (HL_BILD_CHANNEL_ID)
#   2. Bot l\\u00F6scht Foto, postet Beweis-Embed im Team-Kanal
#   3. Team best\\u00E4tigt Erfolg oder Fehlschlag
#      Erfolgreich \\u2192 55.000\\u201373.000 $ + zuf\\u00E4llige Chemikalien ins Inventar
#      Fehlschlag  \\u2192 Info-DM, kein Geld
#   4. 24h-Cooldown pro Spieler
# \\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550\\u2550

import io
import random
from config import *
from economy_helpers import (
    load_economy, save_economy, get_user, log_money_action
)
from dienst import get_on_duty

# \\u2500\\u2500 Konstanten \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

HL_INFO_CHANNEL_ID = 1490894316170641458   # Info-Embed beim Start
HL_BILD_CHANNEL_ID = 1490894317462753280   # Spieler sendet Foto hier
HL_TEAM_CHANNEL_ID = 1490878141235855491   # Team News \\u2014 Beweis + Buttons

HL_MIN_PDL = 4   # Mindestanzahl PDLer im Dienst

HL_CONFIRM_ROLES = {ADMIN_ROLE_ID, MOD_ROLE_ID}

HL_IMAGE_URL = "https://136643ba-e2d7-462a-9d79-80b31d48cd0e-00-1tc3t15bfz4kf.sisko.replit.dev/humane_labs.jpg"

HL_BEUTE_MIN     = 55_000
HL_BEUTE_MAX     = 73_000
HL_CHEMIE_MIN    = 50     # Mindestmenge Chemikalien (Einheiten)
HL_CHEMIE_MAX    = 150    # Maximalmenge Chemikalien (Einheiten)

# Verhindert Doppel-Einreichungen (user_id)
_pending_hl: set[int] = set()


# \\u2500\\u2500 Info-Embed (automatisch beim Start) \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

def build_hl_info_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\\U0001F9EA Humane Labs \\u2014 Raub\\u00FCberfall",
        description=(
            "Das **Humane Labs** hat zu viel Ware bestellt \\u2014 nutze deine Chance!\\n\\n"
            "**\\U0001F465 Spieler:** Mindestens **3 Personen**\\n"
            "**\\U0001F694 Beamte:** Mindestens **4 Officers** im Dienst\\n"
            "**\\u23F1\\uFE0F Dauer:** **20 Minuten**\\n"
            "**\\U0001F4B0 Beute:** zwischen **55.000 $** und **73.000 $** *(zuf\\u00E4llig)*\\n"
            "**\\U0001F9EA Bonus:** **50\\u2013150\\u00D7 Chemikalien** ins Inventar *(zuf\\u00E4llig)*"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="\\u26A1 Ablauf",
        value=(
            "1. Raub **In-Game** mit min. 3 Spielern starten\\n"
            f"2. Foto als Beweis in <#{HL_BILD_CHANNEL_ID}> senden\\n"
            "3. Team best\\u00E4tigt **Erfolg** oder **Fehlschlag**"
        ),
        inline=False
    )
    embed.set_image(url=HL_IMAGE_URL)
    embed.set_footer(text="Paradise City Roleplay \\u2022 Humane Labs System")
    return embed


# \\u2500\\u2500 Beweis-Embed (Team News) \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

def _build_beweis_embed(user: discord.Member, bild_url: str) -> discord.Embed:
    embed = discord.Embed(
        title="\\U0001F9EA Humane Labs \\u2014 Beweis eingereicht",
        description=(
            f"{user.mention} hat einen **Humane Labs Raub\\u00FCberfall** durchgef\\u00FChrt.\\n"
            "\\u23F3 Bitte Ergebnis best\\u00E4tigen."
        ),
        color=0xFF8C00,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\\U0001F464 Spieler", value=f"{user.mention}\\n`{user.display_name}`", inline=True)
    embed.add_field(name="\\u23F1\\uFE0F Dauer",   value="**20 Minuten**",                          inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay \\u2022 Humane Labs System | Nur Team")
    return embed


# \\u2500\\u2500 Ergebnis-Embed \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

def _build_result_embed(
    raeuber: discord.Member,
    bild_url: str,
    beute_wert: int,
    chemie: int,
    team_member: discord.Member,
    success: bool
) -> discord.Embed:
    if success:
        color = 0x00CC44
        title = "\\U0001F9EA Humane Labs \\u2014 Erfolgreich \\u2705"
        desc  = (
            f"{raeuber.mention} hat das **Humane Labs** erfolgreich ausgeraubt.\\n"
            f"**{beute_wert:,}$** landen im Barbestand."
        )
    else:
        color = 0xE74C3C
        title = "\\U0001F9EA Humane Labs \\u2014 Fehlgeschlagen \\u274C"
        desc  = f"{raeuber.mention} ist **gescheitert**. Festnahme, Verletzung oder Abbruch."

    embed = discord.Embed(title=title, description=desc, color=color,
                          timestamp=datetime.now(timezone.utc))
    embed.add_field(name="\\U0001F464 Spieler",       value=raeuber.mention,    inline=True)
    embed.add_field(name="\\u2705 Best\\u00E4tigt von", value=team_member.mention, inline=True)
    if success:
        embed.add_field(name="\\U0001F4B0 Beute",      value=f"**{beute_wert:,}$**",    inline=True)
        embed.add_field(name="\\U0001F9EA Chemikalien", value=f"**{chemie}\\u00D7** ins Inventar", inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay \\u2022 Humane Labs System")
    return embed


# \\u2500\\u2500 Team-Button-View \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

class HumanLabsView(TimedDisableView):
    def __init__(self, raeuber_id: int, bild_url: str):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.raeuber_id = raeuber_id
        self.bild_url   = bild_url

    def _check_team(self, interaction: discord.Interaction) -> bool:
        return bool({r.id for r in interaction.user.roles} & HL_CONFIRM_ROLES)

    @discord.ui.button(label="\\u2705  Erfolgreich", style=discord.ButtonStyle.success, custom_id="human_labs:erfolg")
    async def erfolg_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("\\u274C Nur Team-Mitglieder k\\u00F6nnen best\\u00E4tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("\\u274C Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        beute_wert = random.randint(HL_BEUTE_MIN, HL_BEUTE_MAX)
        chemie     = random.randint(HL_CHEMIE_MIN, HL_CHEMIE_MAX)

        eco = load_economy()
        user_data = get_user(eco, self.raeuber_id)
        user_data["cash"] = user_data.get("cash", 0) + beute_wert
        for _ in range(chemie):
            user_data.setdefault("inventory", []).append("Chemikalien")
        save_economy(eco)

        await log_money_action(
            interaction.guild,
            "Humane Labs Beute",
            f"{raeuber.mention} hat das Humane Labs ausgeraubt.\\n"
            f"**Beute:** {beute_wert:,}$ \\u2192 Barbestand\\n"
            f"**Chemikalien:** {chemie}\\u00D7 ins Inventar\\n"
            f"**Best\\u00E4tigt von:** {interaction.user.mention}"
        )

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(raeuber, self.bild_url, beute_wert, chemie, interaction.user, success=True),
            view=self
        )
        await interaction.response.send_message(
            f"\\u2705 Raub von {raeuber.mention} als **Erfolgreich** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="\\U0001F9EA Humane Labs \\u2014 Erfolgreich! \\U0001F4B0",
                description=(
                    f"Dein Raub\\u00FCberfall im **Humane Labs** war **erfolgreich**!\\n\\n"
                    f"**{beute_wert:,}$** wurden in deinen **Barbestand** \\u00FCbertragen.\\n"
                    f"Zus\\u00E4tzlich erh\\u00E4ltst du **{chemie}\\u00D7 Chemikalien** ins Inventar."
                ),
                color=0x00CC44,
                timestamp=datetime.now(timezone.utc)
            )
            dm.add_field(name="\\U0001F4B5 Beute",          value=f"**{beute_wert:,}$**",       inline=True)
            dm.add_field(name="\\U0001F9EA Chemikalien",    value=f"**{chemie}\\u00D7**",             inline=True)
            dm.add_field(name="\\U0001F4CD Gutgeschrieben", value="Barbestand (Cash)",          inline=True)
            dm.set_footer(text="Paradise City Roleplay \\u2022 Humane Labs System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_hl.discard(self.raeuber_id)

    @discord.ui.button(label="\\u274C  Fehlschlag", style=discord.ButtonStyle.danger, custom_id="human_labs:fehlschlag")
    async def fehlschlag_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("\\u274C Nur Team-Mitglieder k\\u00F6nnen best\\u00E4tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("\\u274C Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        eco = load_economy()
        user_data = get_user(eco, self.raeuber_id)
        user_data["hl_last_raid"] = None
        save_economy(eco)

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(raeuber, self.bild_url, 0, 0, interaction.user, success=False),
            view=self
        )
        await interaction.response.send_message(
            f"\\u2705 Raub von {raeuber.mention} als **Fehlschlag** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="\\U0001F9EA Humane Labs \\u2014 Fehlgeschlagen \\u274C",
                description=(
                    "Dein Raub\\u00FCberfall im **Humane Labs** ist **fehlgeschlagen**.\\n\\n"
                    "\\u2022 \\U0001F694 Festnahme durch Officers\\n"
                    "\\u2022 \\U0001F3E5 Verletzung / Tod\\n"
                    "\\u2022 \\U0001F3F3\\uFE0F Abbruch\\n\\n"
                    "Du erh\\u00E4ltst **keine Beute**."
                ),
                color=0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            dm.set_footer(text="Paradise City Roleplay \\u2022 Humane Labs System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_hl.discard(self.raeuber_id)


# \\u2500\\u2500 on_message \\u2014 Foto-Erkennung \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

@bot.listen("on_message")
async def human_labs_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != HL_BILD_CHANNEL_ID:
        return

    attachment = None
    for att in message.attachments:
        if att.content_type and att.content_type.startswith("image/"):
            attachment = att
            break

    if not attachment:
        return

    user = message.author

    # \\u2500\\u2500 PDL-Pflicht pr\\u00FCfen \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500
    on_duty_lapd = get_on_duty("lapd")
    if len(on_duty_lapd) < HL_MIN_PDL:
        try:
            await message.reply(
                f"\\u274C F\\u00FCr einen Humane Labs Raub m\\u00FCssen mindestens **{HL_MIN_PDL} Officers** im Dienst sein.\\n"
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

    # \\u2500\\u2500 24h-Cooldown pr\\u00FCfen \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500
    eco       = load_economy()
    user_data = get_user(eco, user.id)
    last_raid = user_data.get("hl_last_raid")
    if last_raid:
        last_dt   = datetime.fromisoformat(last_raid)
        vergangen = (datetime.now(timezone.utc) - last_dt).total_seconds()
        if vergangen < 86400:
            verbleibend = int((86400 - vergangen) / 3600)
            minuten     = int(((86400 - vergangen) % 3600) / 60)
            try:
                await message.reply(
                    f"\\u23F3 Du kannst erst in **{verbleibend}h {minuten}min** wieder das Humane Labs ausrauben.",
                    delete_after=15
                )
            except discord.Forbidden:
                pass
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return

    if user.id in _pending_hl:
        try:
            await message.reply(
                "\\u23F3 Du hast bereits einen laufenden Raub eingereicht. Warte auf das Ergebnis.",
                delete_after=10
            )
        except discord.Forbidden:
            pass
        return

    # \\u2500\\u2500 Bild-Bytes sofort sichern \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500
    try:
        img_bytes    = await attachment.read()
        img_filename = attachment.filename or "beweis.jpg"
    except Exception:
        return

    _pending_hl.add(user.id)

    # \\u2500\\u2500 24h-Cooldown setzen \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500
    user_data["hl_last_raid"] = datetime.now(timezone.utc).isoformat()
    save_economy(eco)

    try:
        await message.delete()
    except discord.Forbidden:
        pass

    # \\u2500\\u2500 Beweis ins Team-Channel \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500
    team_channel = message.guild.get_channel(HL_TEAM_CHANNEL_ID)
    if not team_channel:
        _pending_hl.discard(user.id)
        return

    bild_url = ""
    view     = HumanLabsView(raeuber_id=user.id, bild_url="")
    file     = discord.File(io.BytesIO(img_bytes), filename=img_filename)
    embed    = _build_beweis_embed(user, f"attachment://{img_filename}")
    sent_msg = await team_channel.send(file=file, embed=embed, view=view)
    if sent_msg.attachments:
        bild_url      = sent_msg.attachments[0].url
        view.bild_url = bild_url

    # \\u2500\\u2500 Best\\u00E4tigungs-DM an Spieler \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500
    try:
        dm = discord.Embed(
            title="\\U0001F9EA Humane Labs \\u2014 Beweis eingereicht \\u2705",
            description=(
                "Dein Beweis wurde erfolgreich eingereicht!\\n\\n"
                "Du hast ab jetzt **20 Minuten** Zeit."
            ),
            color=0xFF8C00,
            timestamp=datetime.now(timezone.utc)
        )
        dm.set_footer(text="Paradise City Roleplay \\u2022 Humane Labs System")
        await user.send(embed=dm)
    except discord.Forbidden:
        pass

    # \\u2500\\u2500 PDLer benachrichtigen \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500
    for uid_str in on_duty_lapd:
        try:
            member = message.guild.get_member(int(uid_str))
            if not member:
                continue
            cop_embed = discord.Embed(
                title="\\U0001F694 LAPD \\u2014 Humane Labs Raub gemeldet!",
                description=f"**Verd\\u00E4chtiger:** {user.mention} (`{user.display_name}`)",
                color=0x1E90FF,
                timestamp=datetime.now(timezone.utc)
            )
            cop_embed.set_thumbnail(url=user.display_avatar.url)
            if bild_url:
                cop_embed.set_image(url=bild_url)
            cop_embed.set_footer(text="Paradise City Roleplay \\u2022 LAPD")
            await member.send(embed=cop_embed)
        except discord.Forbidden:
            pass


# \\u2500\\u2500 Auto-Setup beim Start \\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500

async def _hl_info_auto_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(HL_INFO_CHANNEL_ID)
        if not channel:
            continue

        embed        = build_hl_info_embed()
        existing_msg = None
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Humane Labs" in emb.title:
                            existing_msg = msg
                            break
                if existing_msg:
                    break
        except Exception:
            pass

        try:
            if existing_msg:
                await existing_msg.edit(embed=embed)
                print(f"[human_labs_raub] \\u2705 Info-Embed aktualisiert in #{channel.name}")
            else:
                await channel.send(embed=embed)
                print(f"[human_labs_raub] \\u2705 Info-Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[human_labs_raub] \\u274C Fehler beim Senden: {e}")


@bot.listen("on_ready")
async def human_labs_on_ready():
    await _hl_info_auto_setup()
