# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# atm_raub.py \u2014 ATM-Raub System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#
# Ablauf:
#   1. Spieler sendet Foto im Bild-Kanal (ATM_BILD_CHANNEL_ID)
#   2. Bot l\u00F6scht Foto und schickt Spieler eine DM mit Auswahl:
#      Welchen Gegenstand nutzt du? (Brecheisen / Plastiksprengstoff)
#      \u2192 inkl. Hinweis: je nach Gegenstand 5 oder 10 Minuten Zeit
#   3. Spieler w\u00E4hlt Gegenstand \u2192 Bot postet Beweis-Embed im Team-Kanal
#   4. Alle LAPD-Beamten im Dienst erhalten eine DM
#   5. Team dr\u00FCckt Button \u2192 Ergebnis-DM an den Spieler
#      Erfolgreich \u2192 3.000$\u201310.000$ in Barbestand
#      Fehlschlag  \u2192 Info-DM, kein Geld
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

import io
import random
from config import *
from economy_helpers import (
    load_economy, save_economy, get_user, log_money_action,
    has_item, consume_item
)
from dienst import get_on_duty

# \u2500\u2500 Konstanten \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

ATM_BILD_CHANNEL_ID  = 1490894309145313330   # Spieler sendet Foto hier
ATM_INFO_CHANNEL_ID  = 1490894308088352961   # Info-Embed beim Start
ATM_TEAM_CHANNEL_ID  = 1490878141235855491   # Team News \u2014 Beweis + Buttons

BEUTE_MIN            = 3_000
BEUTE_MAX            = 10_000

ATM_CONFIRM_ROLES    = {ADMIN_ROLE_ID, MOD_ROLE_ID, DASH_ROLE_ID}

ATM_IMAGE_URL        = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/atm_raub.jpg"

# Aufbrechmittel: key \u2192 Anzeigename, Minuten, Inventar-Suchbegriff
ATM_ITEMS = {
    "brecheisen":  {"label": "\U0001F527 Brecheisen",         "minuten": 10, "inv": "Brecheisen"},
    "sprengstoff": {"label": "\U0001F4A3 Plastiksprengstoff",  "minuten": 5,  "inv": "Plastiksprengstoff"},
}

# Verhindert Doppel-Einreichungen (user_id)
_pending_raids: set[int] = set()


# \u2500\u2500 Info-Embed (automatisch beim Start) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def build_atm_info_embed() -> discord.Embed:
    embed = discord.Embed(
        title="\U0001F3E7 ATM-Raub",
        description=(
            "**\U0001F4B0 Beute:** 3.000$ \u2013 10.000$ *(zuf\u00E4llig)*\n"
            "**\U0001F4CD Ort:** Alle ATMs im gesamten Staat erlaubt\n"
            "**\U0001F464 Spieler:** Ab **1 Person** m\u00F6glich\n"
            "**\U0001F694 Beamte:** Mindestens **2 Officers** im Dienst"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="\U0001F392 Ben\u00F6tigte Items",
        value=(
            f"\U0001F527 **Brecheisen** \u2192 10 Min.\n\u2517 <#{1492976742497783818}>\n\n"
            f"\U0001F4A3 **Plastiksprengstoff** \u2192 5 Min.\n\u2517 <#{1492977067665526804}>"
        ),
        inline=True
    )
    embed.add_field(
        name="\u26A1 Ablauf",
        value=(
            "1. Raub **In-Game** durchf\u00FChren\n"
            f"2. Foto als Beweis in <#{ATM_BILD_CHANNEL_ID}> senden\n"
            "3. Gegenstand in der **DM ausw\u00E4hlen**\n"
            "4. Team best\u00E4tigt **Erfolg** oder **Fehlschlag**"
        ),
        inline=True
    )
    embed.set_image(url=ATM_IMAGE_URL)
    embed.set_footer(text="Paradise City Roleplay \u2022 ATM-System")
    return embed


# \u2500\u2500 Beweis-Embed (Team News) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def build_beweis_embed(
    user: discord.Member,
    bild_url: str,
    item_label: str,
    item_minuten: int
) -> discord.Embed:
    embed = discord.Embed(
        title="\U0001F3E7 ATM-Raub \u2014 Beweis eingereicht",
        description=(
            f"{user.mention} hat einen **ATM-Raub** durchgef\u00FChrt.\n"
            "\u23F3 Bitte Ergebnis best\u00E4tigen."
        ),
        color=0xFF8C00,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="\U0001F464 Spieler",    value=f"{user.mention}\n`{user.display_name}`", inline=True)
    embed.add_field(name="\U0001F527 Gegenstand", value=f"**{item_label}**",                       inline=True)
    embed.add_field(name="\u23F1\uFE0F Zeit",       value=f"**{item_minuten} Minuten**",              inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay \u2022 ATM-System | Best\u00E4tigung: Highteam")
    return embed


# \u2500\u2500 Ergebnis-Embed \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_result_embed(
    raeuber: discord.Member,
    bild_url: str,
    beute: int,
    team_member: discord.Member,
    success: bool,
    item_label: str = ""
) -> discord.Embed:
    if success:
        color = 0x00CC44
        title = "\U0001F3E7 ATM-Raub \u2014 Erfolgreich \u2705"
        desc  = f"{raeuber.mention} hat **{beute:,}$** erbeutet \u2192 **Barbestand**."
    else:
        color = 0xE74C3C
        title = "\U0001F3E7 ATM-Raub \u2014 Fehlgeschlagen \u274C"
        desc  = f"{raeuber.mention} ist **gescheitert**. Festnahme, Verletzung oder Abbruch."

    embed = discord.Embed(title=title, description=desc, color=color,
                          timestamp=datetime.now(timezone.utc))
    embed.add_field(name="\U0001F464 Spieler",       value=raeuber.mention,    inline=True)
    embed.add_field(name="\u2705 Best\u00E4tigt von", value=team_member.mention, inline=True)
    if item_label:
        embed.add_field(name="\U0001F527 Gegenstand", value=item_label, inline=True)
    if success:
        embed.add_field(name="\U0001F4B0 Beute", value=f"**{beute:,}$**", inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay \u2022 ATM-System")
    return embed


# \u2500\u2500 Team-Button-View \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class AtmRaubView(TimedDisableView):
    def __init__(self, raeuber_id: int, bild_url: str, item_label: str, item_minuten: int, item_inv: str):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.raeuber_id   = raeuber_id
        self.bild_url     = bild_url
        self.item_label   = item_label
        self.item_minuten = item_minuten
        self.item_inv     = item_inv   # Inventar-Name f\u00FCr R\u00FCckgabe bei Fehlschlag

    def _check_team(self, interaction: discord.Interaction) -> bool:
        return bool({r.id for r in interaction.user.roles} & ATM_CONFIRM_ROLES)

    @discord.ui.button(label="\u2705  Erfolgreich", style=discord.ButtonStyle.success, custom_id="atm_raub:erfolg")
    async def erfolg_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message(f"\u274C Nur <@&{DASH_ROLE_ID}> d\u00FCrfen best\u00E4tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("\u274C Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        beute = random.randint(BEUTE_MIN, BEUTE_MAX)

        eco = load_economy()
        user_data = get_user(eco, self.raeuber_id)
        user_data["schwarzgeld"] = int(user_data.get("schwarzgeld", 0)) + beute
        save_economy(eco)

        await log_money_action(
            interaction.guild,
            "ATM-Raub Beute",
            f"{raeuber.mention} hat einen ATM ausgeraubt.\n"
            f"**Gegenstand:** {self.item_label}\n"
            f"**Beute:** {beute:,}$ (Schwarzgeld gutgeschrieben)\n"
            f"**Best\u00E4tigt von:** {interaction.user.mention}"
        )

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(
                raeuber, self.bild_url, beute, interaction.user,
                success=True, item_label=self.item_label
            ),
            view=self
        )
        await interaction.response.send_message(
            f"\u2705 Raub von {raeuber.mention} als **Erfolgreich** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="\U0001F3E7 ATM-Raub \u2014 Erfolgreich! \U0001F4B0",
                description=(
                    f"Dein ATM-Raub war **erfolgreich**!\n\n"
                    f"**{beute:,}$** wurden deinem **Schwarzgeld** gutgeschrieben."
                ),
                color=0x00CC44,
                timestamp=datetime.now(timezone.utc)
            )
            dm.add_field(name="\U0001F527 Gegenstand",      value=self.item_label,    inline=True)
            dm.add_field(name="\U0001F4B5 Schwarzgeld +",   value=f"**{beute:,}$**", inline=True)
            dm.set_footer(text="Paradise City Roleplay \u2022 ATM-System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raids.discard(self.raeuber_id)

    @discord.ui.button(label="\u274C  Fehlschlag", style=discord.ButtonStyle.danger, custom_id="atm_raub:fehlschlag")
    async def fehlschlag_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message(f"\u274C Nur <@&{DASH_ROLE_ID}> d\u00FCrfen best\u00E4tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("\u274C Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        # Item zur\u00FCck ins Inventar + Cooldown zur\u00FCcksetzen
        eco       = load_economy()
        user_data = get_user(eco, self.raeuber_id)
        user_data.setdefault("inventory", []).append(self.item_inv)
        user_data["atm_last_raid"] = None
        save_economy(eco)

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(
                raeuber, self.bild_url, 0, interaction.user,
                success=False, item_label=self.item_label
            ),
            view=self
        )
        await interaction.response.send_message(
            f"\u2705 Raub von {raeuber.mention} als **Fehlschlag** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="\U0001F3E7 ATM-Raub \u2014 Fehlgeschlagen \u274C",
                description=(
                    "Dein ATM-Raub ist **fehlgeschlagen**.\n\n"
                    "\u2022 \U0001F694 Festnahme durch LAPD\n"
                    "\u2022 \U0001F3E5 Verletzung / Tod\n"
                    "\u2022 \U0001F3F3\uFE0F Abbruch\n\n"
                    f"Dein **{self.item_inv}** wurde dir zur\u00FCckgegeben.\n"
                    "Du erh\u00E4ltst **keine Beute**."
                ),
                color=0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            dm.add_field(name="\U0001F527 Gegenstand", value=self.item_label, inline=True)
            dm.set_footer(text="Paradise City Roleplay \u2022 ATM-System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raids.discard(self.raeuber_id)


# \u2500\u2500 Gegenstand-Auswahl-View (per DM) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class GegenstandView(TimedDisableView):
    """Wird dem Spieler per DM geschickt. Er w\u00E4hlt seinen Gegenstand."""

    def __init__(self, raeuber: discord.Member, img_bytes: bytes, img_filename: str, guild_id: int):
        super().__init__(timeout=300)   # 5 Minuten Zeit zum Ausw\u00E4hlen
        self.raeuber      = raeuber
        self.img_bytes    = img_bytes
        self.img_filename = img_filename
        self.guild_id     = guild_id
        self._done        = False

    async def on_timeout(self):
        _pending_raids.discard(self.raeuber.id)

    async def _submit(self, interaction: discord.Interaction, item_key: str):
        if self._done:
            await interaction.response.send_message("\u23F3 Du hast bereits einen Gegenstand gew\u00E4hlt.", ephemeral=True)
            return

        item = ATM_ITEMS[item_key]

        # \u2500\u2500 Inventar-Check \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        if not has_item(self.raeuber, item["inv"]):
            # Buttons NICHT deaktivieren \u2014 Spieler kann noch wechseln
            await interaction.response.send_message(
                f"\u274C Du hast kein **{item['label']}** in deinem Inventar!\n"
                f"Kaufe es zuerst im Shop und versuche es erneut.",
                ephemeral=True
            )
            _pending_raids.discard(self.raeuber.id)
            return

        self._done = True

        # \u2500\u2500 Item verbrauchen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        consume_item(self.raeuber, item["inv"])

        for child in self.children:
            child.disabled = True

        # Best\u00E4tigungs-DM aktualisieren
        confirm_embed = discord.Embed(
            title="\U0001F3E7 ATM-Raub \u2014 Beweis eingereicht \u2705",
            description=(
                "Dein Beweis wurde erfolgreich eingereicht!\n\n"
                f"**Gegenstand:** {item['label']} *(aus deinem Inventar entnommen)*\n\n"
                f"Du hast ab jetzt **{item['minuten']} Minuten** Zeit."
            ),
            color=0xFF8C00,
            timestamp=datetime.now(timezone.utc)
        )
        confirm_embed.set_footer(text="Paradise City Roleplay \u2022 ATM-System")
        await interaction.response.edit_message(embed=confirm_embed, view=self)

        # Beweis ins Team-Channel posten (Bild als Datei hochladen)
        guild = bot.get_guild(self.guild_id)
        if guild:
            team_channel = guild.get_channel(ATM_TEAM_CHANNEL_ID)
            bild_url = ""
            if team_channel:
                # Bild + Embed + Buttons in EINER Nachricht \u2192 Bild im Embed unten
                file         = discord.File(io.BytesIO(self.img_bytes), filename=self.img_filename)
                beweis_embed = build_beweis_embed(
                    self.raeuber,
                    f"attachment://{self.img_filename}",
                    item["label"],
                    item["minuten"]
                )
                view = AtmRaubView(
                    raeuber_id=self.raeuber.id,
                    bild_url="",          # Platzhalter \u2014 wird nach dem Senden gesetzt
                    item_label=item["label"],
                    item_minuten=item["minuten"],
                    item_inv=item["inv"]
                )
                sent_msg = await team_channel.send(file=file, embed=beweis_embed, view=view)
                # Echte Attachment-URL f\u00FCr das Ergebnis-Embed sichern
                if sent_msg.attachments:
                    bild_url = sent_msg.attachments[0].url
                    view.bild_url = bild_url

            # LAPD benachrichtigen
            on_duty_lapd = get_on_duty("lapd")
            for uid_str in on_duty_lapd:
                try:
                    member = guild.get_member(int(uid_str))
                    if not member:
                        continue
                    cop_embed = discord.Embed(
                        title="\U0001F694 LAPD \u2014 ATM-Raub gemeldet!",
                        description=(
                            f"**Verd\u00E4chtiger:** {self.raeuber.mention} (`{self.raeuber.display_name}`)\n"
                            f"**Gegenstand:** {item['label']}"
                        ),
                        color=0x1E90FF,
                        timestamp=datetime.now(timezone.utc)
                    )
                    cop_embed.set_thumbnail(url=self.raeuber.display_avatar.url)
                    if bild_url:
                        cop_embed.set_image(url=bild_url)
                    cop_embed.set_footer(text="Paradise City Roleplay \u2022 LAPD")
                    await member.send(embed=cop_embed)
                except discord.Forbidden:
                    pass

    @discord.ui.button(label="\U0001F527 Brecheisen (10 Min.)", style=discord.ButtonStyle.primary)
    async def brecheisen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._submit(interaction, "brecheisen")

    @discord.ui.button(label="\U0001F4A3 Plastiksprengstoff (5 Min.)", style=discord.ButtonStyle.danger)
    async def sprengstoff_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._submit(interaction, "sprengstoff")


# \u2500\u2500 on_message \u2014 Foto-Erkennung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.listen("on_message")
async def atm_bild_listener(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != ATM_BILD_CHANNEL_ID:
        return

    attachment = None
    for att in message.attachments:
        if att.content_type and att.content_type.startswith("image/"):
            attachment = att
            break

    if not attachment:
        return

    user = message.author

    # \u2500\u2500 Officer-Pflicht pr\u00FCfen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    on_duty_lapd = get_on_duty("lapd")
    if len(on_duty_lapd) < 2:
        try:
            await message.reply(
                "\u274C F\u00FCr einen ATM-Raub m\u00FCssen mindestens **2 Officers** im Dienst sein.\n"
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
    last_raid = user_data.get("atm_last_raid")
    if last_raid:
        last_dt  = datetime.fromisoformat(last_raid)
        vergangen = (datetime.now(timezone.utc) - last_dt).total_seconds()
        if vergangen < 86400:
            verbleibend = int((86400 - vergangen) / 3600)
            minuten     = int(((86400 - vergangen) % 3600) / 60)
            try:
                await message.reply(
                    f"\u23F3 Du kannst erst in **{verbleibend}h {minuten}min** wieder einen ATM ausrauben.",
                    delete_after=15
                )
            except discord.Forbidden:
                pass
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return

    if user.id in _pending_raids:
        try:
            await message.reply(
                "\u23F3 Du hast bereits einen laufenden Raub eingereicht. Warte auf das Ergebnis.",
                delete_after=10
            )
        except discord.Forbidden:
            pass
        return

    # \u2500\u2500 Bild-Bytes sofort sichern (vor dem L\u00F6schen) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    try:
        img_bytes    = await attachment.read()
        img_filename = attachment.filename or "beweis.jpg"
    except Exception:
        return

    _pending_raids.add(user.id)

    try:
        await message.delete()
    except discord.Forbidden:
        pass

    # \u2500\u2500 24h-Cooldown setzen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    user_data["atm_last_raid"] = datetime.now(timezone.utc).isoformat()
    save_economy(eco)

    # DM mit Gegenstand-Auswahl schicken
    try:
        dm_embed = discord.Embed(
            title="\U0001F3E7 ATM-Raub \u2014 Gegenstand w\u00E4hlen",
            description=(
                "Dein Foto wurde empfangen!\n\n"
                "**Mit welchem Gegenstand brichst du den ATM auf?**\n"
                "W\u00E4hle unten einen der beiden Gegenst\u00E4nde aus.\n\n"
                "\u23F1\uFE0F **Je nach Gegenstand hast du 10 oder 5 Minuten Zeit.**\n"
                "Du hast **5 Minuten**, um hier auszuw\u00E4hlen."
            ),
            color=0xFF8C00,
            timestamp=datetime.now(timezone.utc)
        )
        dm_embed.add_field(
            name="\U0001F527 Brecheisen",
            value="10 Minuten Zeit\n\u2517 Kaufbar im Baumarkt",
            inline=True
        )
        dm_embed.add_field(
            name="\U0001F4A3 Plastiksprengstoff",
            value="5 Minuten Zeit\n\u2517 Kaufbar im Schwarzmarkt",
            inline=True
        )
        dm_embed.set_footer(text="Paradise City Roleplay \u2022 ATM-System")

        view = GegenstandView(raeuber=user, img_bytes=img_bytes, img_filename=img_filename, guild_id=message.guild.id)
        await user.send(embed=dm_embed, view=view)

    except discord.Forbidden:
        # Spieler hat DMs deaktiviert \u2014 direkt ohne Gegenstand einreichen
        _pending_raids.discard(user.id)
        try:
            await message.channel.send(
                f"{user.mention} \u274C Bitte \u00F6ffne deine **DMs** damit du den Gegenstand ausw\u00E4hlen kannst!",
                delete_after=15
            )
        except discord.Forbidden:
            pass


# \u2500\u2500 Auto-Setup beim Start \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _atm_info_auto_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(ATM_INFO_CHANNEL_ID)
        if not channel:
            continue

        embed = build_atm_info_embed()
        existing_msg = None
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "ATM-Raub" in emb.title:
                            existing_msg = msg
                            break
                if existing_msg:
                    break
        except Exception:
            pass

        try:
            if existing_msg:
                await existing_msg.edit(embed=embed)
                print(f"[atm_raub] \u2705 Info-Embed aktualisiert in #{channel.name}")
            else:
                await channel.send(embed=embed)
                print(f"[atm_raub] \u2705 Info-Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[atm_raub] \u274C Fehler: {e}")


@bot.listen("on_ready")
async def atm_raub_on_ready():
    await _atm_info_auto_setup()
