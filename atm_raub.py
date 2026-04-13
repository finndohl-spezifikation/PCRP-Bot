# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# atm_raub.py — ATM-Raub System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════
#
# Ablauf:
#   1. Spieler sendet Foto im Bild-Kanal (ATM_BILD_CHANNEL_ID)
#   2. Bot löscht Foto und schickt Spieler eine DM mit Auswahl:
#      Welchen Gegenstand nutzt du? (Brecheisen / Plastiksprengstoff)
#      → inkl. Hinweis: je nach Gegenstand 5 oder 10 Minuten Zeit
#   3. Spieler wählt Gegenstand → Bot postet Beweis-Embed im Team-Kanal
#   4. Alle LAPD-Beamten im Dienst erhalten eine DM
#   5. Team drückt Button → Ergebnis-DM an den Spieler
#      Erfolgreich → 3.000$–10.000$ in Barbestand
#      Fehlschlag  → Info-DM, kein Geld
# ══════════════════════════════════════════════════════════════

import io
import random
from config import *
from economy_helpers import (
    load_economy, save_economy, get_user, log_money_action,
    has_item, consume_item
)
from dienst import get_on_duty

# ── Konstanten ────────────────────────────────────────────────

ATM_BILD_CHANNEL_ID  = 1490894309145313330   # Spieler sendet Foto hier
ATM_INFO_CHANNEL_ID  = 1490894308088352961   # Info-Embed beim Start
ATM_TEAM_CHANNEL_ID  = 1490878141235855491   # Team News — Beweis + Buttons

BEUTE_MIN            = 3_000
BEUTE_MAX            = 10_000

ATM_CONFIRM_ROLES    = {ADMIN_ROLE_ID, MOD_ROLE_ID}

ATM_IMAGE_URL        = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/atm_raub.jpg"

# Aufbrechmittel: key → Anzeigename, Minuten, Inventar-Suchbegriff
ATM_ITEMS = {
    "brecheisen":  {"label": "🔧 Brecheisen",         "minuten": 10, "inv": "Brecheisen"},
    "sprengstoff": {"label": "💣 Plastiksprengstoff",  "minuten": 5,  "inv": "Plastiksprengstoff"},
}

# Verhindert Doppel-Einreichungen (user_id)
_pending_raids: set[int] = set()


# ── Info-Embed (automatisch beim Start) ───────────────────────

def build_atm_info_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏧 ATM-Raub",
        description=(
            "**💰 Beute:** 3.000$ – 10.000$ *(zufällig)*\n"
            "**📍 Ort:** Alle ATMs im gesamten Staat erlaubt\n"
            "**👤 Spieler:** Ab **1 Person** möglich"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="🎒 Benötigte Items",
        value=(
            f"🔧 **Brecheisen** → 10 Min.\n┗ <#{1492976742497783818}>\n\n"
            f"💣 **Plastiksprengstoff** → 5 Min.\n┗ <#{1492977067665526804}>"
        ),
        inline=True
    )
    embed.add_field(
        name="⚡ Ablauf",
        value=(
            "1. Raub **In-Game** durchführen\n"
            f"2. Foto als Beweis in <#{ATM_BILD_CHANNEL_ID}> senden\n"
            "3. Gegenstand in der **DM auswählen**\n"
            "4. Team bestätigt **Erfolg** oder **Fehlschlag**"
        ),
        inline=True
    )
    embed.set_image(url=ATM_IMAGE_URL)
    embed.set_footer(text="Paradise City Roleplay • ATM-System")
    return embed


# ── Beweis-Embed (Team News) ──────────────────────────────────

def build_beweis_embed(
    user: discord.Member,
    bild_url: str,
    item_label: str,
    item_minuten: int
) -> discord.Embed:
    embed = discord.Embed(
        title="🏧 ATM-Raub — Beweis eingereicht",
        description=(
            f"{user.mention} hat einen **ATM-Raub** durchgeführt.\n"
            "⏳ Bitte Ergebnis bestätigen."
        ),
        color=0xFF8C00,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="👤 Spieler",    value=f"{user.mention}\n`{user.display_name}`", inline=True)
    embed.add_field(name="🔧 Gegenstand", value=f"**{item_label}**",                       inline=True)
    embed.add_field(name="⏱️ Zeit",       value=f"**{item_minuten} Minuten**",              inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay • ATM-System | Nur Team")
    return embed


# ── Ergebnis-Embed ────────────────────────────────────────────

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
        title = "🏧 ATM-Raub — Erfolgreich ✅"
        desc  = f"{raeuber.mention} hat **{beute:,}$** erbeutet → **Barbestand**."
    else:
        color = 0xE74C3C
        title = "🏧 ATM-Raub — Fehlgeschlagen ❌"
        desc  = f"{raeuber.mention} ist **gescheitert**. Festnahme, Verletzung oder Abbruch."

    embed = discord.Embed(title=title, description=desc, color=color,
                          timestamp=datetime.now(timezone.utc))
    embed.add_field(name="👤 Spieler",       value=raeuber.mention,    inline=True)
    embed.add_field(name="✅ Bestätigt von", value=team_member.mention, inline=True)
    if item_label:
        embed.add_field(name="🔧 Gegenstand", value=item_label, inline=True)
    if success:
        embed.add_field(name="💰 Beute", value=f"**{beute:,}$**", inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay • ATM-System")
    return embed


# ── Team-Button-View ──────────────────────────────────────────

class AtmRaubView(discord.ui.View):
    def __init__(self, raeuber_id: int, bild_url: str, item_label: str, item_minuten: int, item_inv: str):
        super().__init__(timeout=None)
        self.raeuber_id   = raeuber_id
        self.bild_url     = bild_url
        self.item_label   = item_label
        self.item_minuten = item_minuten
        self.item_inv     = item_inv   # Inventar-Name für Rückgabe bei Fehlschlag

    def _check_team(self, interaction: discord.Interaction) -> bool:
        return bool({r.id for r in interaction.user.roles} & ATM_CONFIRM_ROLES)

    @discord.ui.button(label="✅  Erfolgreich", style=discord.ButtonStyle.success, custom_id="atm_raub:erfolg")
    async def erfolg_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("❌ Nur Team-Mitglieder können bestätigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("❌ Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        beute = random.randint(BEUTE_MIN, BEUTE_MAX)

        eco = load_economy()
        user_data = get_user(eco, self.raeuber_id)
        user_data["cash"] = user_data.get("cash", 0) + beute
        save_economy(eco)

        await log_money_action(
            interaction.guild,
            "ATM-Raub Beute",
            f"{raeuber.mention} hat einen ATM ausgeraubt.\n"
            f"**Gegenstand:** {self.item_label}\n"
            f"**Beute:** {beute:,}$ → Barbestand\n"
            f"**Bestätigt von:** {interaction.user.mention}"
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
            f"✅ Raub von {raeuber.mention} als **Erfolgreich** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="🏧 ATM-Raub — Erfolgreich! 💰",
                description=(
                    f"Dein ATM-Raub war **erfolgreich**!\n\n"
                    f"**{beute:,}$** wurden in deinen **Barbestand** übertragen."
                ),
                color=0x00CC44,
                timestamp=datetime.now(timezone.utc)
            )
            dm.add_field(name="🔧 Gegenstand",    value=self.item_label,         inline=True)
            dm.add_field(name="💵 Beute",          value=f"**{beute:,}$**",        inline=True)
            dm.add_field(name="📍 Gutgeschrieben", value="Barbestand (Cash)",      inline=True)
            dm.set_footer(text="Paradise City Roleplay • ATM-System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raids.discard(self.raeuber_id)

    @discord.ui.button(label="❌  Fehlschlag", style=discord.ButtonStyle.danger, custom_id="atm_raub:fehlschlag")
    async def fehlschlag_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("❌ Nur Team-Mitglieder können bestätigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("❌ Spieler nicht mehr auf dem Server.", ephemeral=True)
            return

        # Item zurück ins Inventar + Cooldown zurücksetzen
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
            f"✅ Raub von {raeuber.mention} als **Fehlschlag** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="🏧 ATM-Raub — Fehlgeschlagen ❌",
                description=(
                    "Dein ATM-Raub ist **fehlgeschlagen**.\n\n"
                    "• 🚔 Festnahme durch LAPD\n"
                    "• 🏥 Verletzung / Tod\n"
                    "• 🏳️ Abbruch\n\n"
                    f"Dein **{self.item_inv}** wurde dir zurückgegeben.\n"
                    "Du erhältst **keine Beute**."
                ),
                color=0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            dm.add_field(name="🔧 Gegenstand", value=self.item_label, inline=True)
            dm.set_footer(text="Paradise City Roleplay • ATM-System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raids.discard(self.raeuber_id)


# ── Gegenstand-Auswahl-View (per DM) ─────────────────────────

class GegenstandView(discord.ui.View):
    """Wird dem Spieler per DM geschickt. Er wählt seinen Gegenstand."""

    def __init__(self, raeuber: discord.Member, img_bytes: bytes, img_filename: str, guild_id: int):
        super().__init__(timeout=300)   # 5 Minuten Zeit zum Auswählen
        self.raeuber      = raeuber
        self.img_bytes    = img_bytes
        self.img_filename = img_filename
        self.guild_id     = guild_id
        self._done        = False

    async def on_timeout(self):
        _pending_raids.discard(self.raeuber.id)

    async def _submit(self, interaction: discord.Interaction, item_key: str):
        if self._done:
            await interaction.response.send_message("⏳ Du hast bereits einen Gegenstand gewählt.", ephemeral=True)
            return

        item = ATM_ITEMS[item_key]

        # ── Inventar-Check ────────────────────────────────────
        if not has_item(self.raeuber, item["inv"]):
            # Buttons NICHT deaktivieren — Spieler kann noch wechseln
            await interaction.response.send_message(
                f"❌ Du hast kein **{item['label']}** in deinem Inventar!\n"
                f"Kaufe es zuerst im Shop und versuche es erneut.",
                ephemeral=True
            )
            _pending_raids.discard(self.raeuber.id)
            return

        self._done = True

        # ── Item verbrauchen ──────────────────────────────────
        consume_item(self.raeuber, item["inv"])

        for child in self.children:
            child.disabled = True

        # Bestätigungs-DM aktualisieren
        confirm_embed = discord.Embed(
            title="🏧 ATM-Raub — Beweis eingereicht ✅",
            description=(
                "Dein Beweis wurde erfolgreich eingereicht!\n\n"
                f"**Gegenstand:** {item['label']} *(aus deinem Inventar entnommen)*\n"
                f"**Deine Zeit:** {item['minuten']} Minuten\n\n"
                "Das Team überprüft deinen Raub und bestätigt das Ergebnis in Kürze.\n"
                "Du wirst per DM benachrichtigt sobald eine Entscheidung getroffen wurde."
            ),
            color=0xFF8C00,
            timestamp=datetime.now(timezone.utc)
        )
        confirm_embed.set_footer(text="Paradise City Roleplay • ATM-System")
        await interaction.response.edit_message(embed=confirm_embed, view=self)

        # Beweis ins Team-Channel posten (Bild als Datei hochladen)
        guild = bot.get_guild(self.guild_id)
        if guild:
            team_channel = guild.get_channel(ATM_TEAM_CHANNEL_ID)
            bild_url = ""
            if team_channel:
                # Bild + Embed + Buttons in EINER Nachricht → Bild im Embed unten
                file         = discord.File(io.BytesIO(self.img_bytes), filename=self.img_filename)
                beweis_embed = build_beweis_embed(
                    self.raeuber,
                    f"attachment://{self.img_filename}",
                    item["label"],
                    item["minuten"]
                )
                view = AtmRaubView(
                    raeuber_id=self.raeuber.id,
                    bild_url="",          # Platzhalter — wird nach dem Senden gesetzt
                    item_label=item["label"],
                    item_minuten=item["minuten"],
                    item_inv=item["inv"]
                )
                sent_msg = await team_channel.send(file=file, embed=beweis_embed, view=view)
                # Echte Attachment-URL für das Ergebnis-Embed sichern
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
                        title="🚔 LAPD — ATM-Raub gemeldet!",
                        description=(
                            f"**Verdächtiger:** {self.raeuber.mention} (`{self.raeuber.display_name}`)\n"
                            f"**Gegenstand:** {item['label']}\n\n"
                            f"Prüfe <#{ATM_TEAM_CHANNEL_ID}> für Details."
                        ),
                        color=0x1E90FF,
                        timestamp=datetime.now(timezone.utc)
                    )
                    cop_embed.set_thumbnail(url=self.raeuber.display_avatar.url)
                    if bild_url:
                        cop_embed.set_image(url=bild_url)
                    cop_embed.set_footer(text="Paradise City Roleplay • LAPD")
                    await member.send(embed=cop_embed)
                except discord.Forbidden:
                    pass

    @discord.ui.button(label="🔧 Brecheisen (10 Min.)", style=discord.ButtonStyle.primary)
    async def brecheisen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._submit(interaction, "brecheisen")

    @discord.ui.button(label="💣 Plastiksprengstoff (5 Min.)", style=discord.ButtonStyle.danger)
    async def sprengstoff_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._submit(interaction, "sprengstoff")


# ── on_message — Foto-Erkennung ───────────────────────────────

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

    # ── 24h-Cooldown prüfen ────────────────────────────────────
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
                    f"⏳ Du kannst erst in **{verbleibend}h {minuten}min** wieder einen ATM ausrauben.",
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
                "⏳ Du hast bereits einen laufenden Raub eingereicht. Warte auf das Ergebnis.",
                delete_after=10
            )
        except discord.Forbidden:
            pass
        return

    # ── Bild-Bytes sofort sichern (vor dem Löschen) ───────────
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

    # ── 24h-Cooldown setzen ────────────────────────────────────
    user_data["atm_last_raid"] = datetime.now(timezone.utc).isoformat()
    save_economy(eco)

    # DM mit Gegenstand-Auswahl schicken
    try:
        dm_embed = discord.Embed(
            title="🏧 ATM-Raub — Gegenstand wählen",
            description=(
                "Dein Foto wurde empfangen!\n\n"
                "**Mit welchem Gegenstand brichst du den ATM auf?**\n"
                "Wähle unten einen der beiden Gegenstände aus.\n\n"
                "⏱️ **Je nach Gegenstand hast du 10 oder 5 Minuten Zeit.**\n"
                "Du hast **5 Minuten**, um hier auszuwählen."
            ),
            color=0xFF8C00,
            timestamp=datetime.now(timezone.utc)
        )
        dm_embed.add_field(
            name="🔧 Brecheisen",
            value="10 Minuten Zeit\n┗ Kaufbar im Baumarkt",
            inline=True
        )
        dm_embed.add_field(
            name="💣 Plastiksprengstoff",
            value="5 Minuten Zeit\n┗ Kaufbar im Schwarzmarkt",
            inline=True
        )
        dm_embed.set_footer(text="Paradise City Roleplay • ATM-System")

        view = GegenstandView(raeuber=user, img_bytes=img_bytes, img_filename=img_filename, guild_id=message.guild.id)
        await user.send(embed=dm_embed, view=view)

    except discord.Forbidden:
        # Spieler hat DMs deaktiviert — direkt ohne Gegenstand einreichen
        _pending_raids.discard(user.id)
        try:
            await message.channel.send(
                f"{user.mention} ❌ Bitte öffne deine **DMs** damit du den Gegenstand auswählen kannst!",
                delete_after=15
            )
        except discord.Forbidden:
            pass


# ── Auto-Setup beim Start ─────────────────────────────────────

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
                print(f"[atm_raub] ✅ Info-Embed aktualisiert in #{channel.name}")
            else:
                await channel.send(embed=embed)
                print(f"[atm_raub] ✅ Info-Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[atm_raub] ❌ Fehler: {e}")


@bot.listen("on_ready")
async def atm_raub_on_ready():
    await _atm_info_auto_setup()
