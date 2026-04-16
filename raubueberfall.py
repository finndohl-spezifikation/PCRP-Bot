# -*- coding: utf-8 -*-
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# raubueberfall.py â€” RaubÃ¼berfall System
# Paradise City Roleplay Discord Bot
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#
# Ablauf:
#   1. Spieler sendet Foto im Bild-Kanal (RAUB_BILD_CHANNEL_ID)
#   2. Bot lÃ¶scht das Foto, postet Beweis-Embed im Team-Kanal
#   3. Team bestÃ¤tigt Erfolg oder Fehlschlag
#      Erfolgreich â†’ 7.000â€“13.000 $ + 1â€“6 Bier
#      Fehlschlag  â†’ Info-DM, kein Geld
#   4. 24h-Cooldown pro Spieler
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

import io
import random
from config import *
from economy_helpers import (
    load_economy, save_economy, get_user, log_money_action
)
from dienst import get_on_duty

# â”€â”€ Konstanten â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

RAUB_INFO_CHANNEL_ID = 1490894312727117904   # Info-Embed beim Start
RAUB_BILD_CHANNEL_ID = 1490894314132213771   # Spieler sendet Foto hier
RAUB_TEAM_CHANNEL_ID = 1490878141235855491   # Team News â€” Beweis + Buttons

RAUB_BEUTE_MIN  = 7_000
RAUB_BEUTE_MAX  = 13_000
RAUB_BIER_MIN   = 1
RAUB_BIER_MAX   = 6
RAUB_MIN_PDL    = 2   # Mindestanzahl PDLer im Dienst

RAUB_CONFIRM_ROLES = {ADMIN_ROLE_ID, MOD_ROLE_ID}

RAUB_IMAGE_URL = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/raubueberfall.jpg"

# Verhindert Doppel-Einreichungen (user_id)
_pending_raube: set[int] = set()


# â”€â”€ Info-Embed (automatisch beim Start) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_raub_info_embed() -> discord.Embed:
    embed = discord.Embed(
        title="ðŸ”« RaubÃ¼berfall",
        description=(
            "Plane einen RaubÃ¼berfall und kassiere deine Beute!\n\n"
            "**ðŸ‘¥ Spieler:** Mindestens **2 Personen**\n"
            "**ðŸš” Beamte:** Mindestens **2 Officers** im Dienst\n"
            "**â±ï¸ Dauer:** **15 Minuten**\n"
            "**ðŸ’° Beute:** zwischen **7.000 $** und **13.000 $** *(zufÃ¤llig)*\n"
            "**ðŸº Bonus:** zwischen **1** und **6 Bier** *(zufÃ¤llig)*"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="âš¡ Ablauf",
        value=(
            "1. RaubÃ¼berfall **In-Game** mit min. 2 Spielern starten\n"
            f"2. Foto als Beweis in <#{RAUB_BILD_CHANNEL_ID}> senden\n"
            "3. Team bestÃ¤tigt **Erfolg** oder **Fehlschlag**"
        ),
        inline=False
    )
    embed.set_image(url="https://136643ba-e2d7-462a-9d79-80b31d48cd0e-00-1tc3t15bfz4kf.sisko.replit.dev/raubueberfall_bar.png")
    embed.set_footer(text="Paradise City Roleplay â€¢ RaubÃ¼berfall System")
    return embed


# â”€â”€ Beweis-Embed (Team News) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _build_beweis_embed(user: discord.Member, bild_url: str) -> discord.Embed:
    embed = discord.Embed(
        title="ðŸ”« RaubÃ¼berfall â€” Beweis eingereicht",
        description=(
            f"{user.mention} hat einen **RaubÃ¼berfall** durchgefÃ¼hrt.\n"
            "â³ Bitte Ergebnis bestÃ¤tigen."
        ),
        color=0xFF8C00,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="ðŸ‘¤ Spieler", value=f"{user.mention}\n`{user.display_name}`", inline=True)
    embed.add_field(name="â±ï¸ Dauer",   value="**15 Minuten**",                          inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay â€¢ RaubÃ¼berfall System | Nur Team")
    return embed


# â”€â”€ Ergebnis-Embed â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
        title = "ðŸ”« RaubÃ¼berfall â€” Erfolgreich âœ…"
        desc  = (
            f"{raeuber.mention} hat **{beute:,}$** erbeutet â†’ **Barbestand**.\n"
            f"Zudem erhÃ¤lt er **{bier}x Bier**."
        )
    else:
        color = 0xE74C3C
        title = "ðŸ”« RaubÃ¼berfall â€” Fehlgeschlagen âŒ"
        desc  = f"{raeuber.mention} ist **gescheitert**. Festnahme, Verletzung oder Abbruch."

    embed = discord.Embed(title=title, description=desc, color=color,
                          timestamp=datetime.now(timezone.utc))
    embed.add_field(name="ðŸ‘¤ Spieler",       value=raeuber.mention,    inline=True)
    embed.add_field(name="âœ… BestÃ¤tigt von", value=team_member.mention, inline=True)
    if success:
        embed.add_field(name="ðŸ’° Beute",  value=f"**{beute:,}$**", inline=True)
        embed.add_field(name="ðŸº Bonus",  value=f"**{bier}x Bier**", inline=True)
    embed.set_image(url=bild_url)
    embed.set_footer(text="Paradise City Roleplay â€¢ RaubÃ¼berfall System")
    return embed


# â”€â”€ Team-Button-View â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class RaubView(discord.ui.View):
    def __init__(self, raeuber_id: int, bild_url: str):
        super().__init__(timeout=None)
        self.raeuber_id = raeuber_id
        self.bild_url   = bild_url

    def _check_team(self, interaction: discord.Interaction) -> bool:
        return bool({r.id for r in interaction.user.roles} & RAUB_CONFIRM_ROLES)

    @discord.ui.button(label="âœ…  Erfolgreich", style=discord.ButtonStyle.success, custom_id="raubueberfall:erfolg")
    async def erfolg_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("âŒ Nur Team-Mitglieder kÃ¶nnen bestÃ¤tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("âŒ Spieler nicht mehr auf dem Server.", ephemeral=True)
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
            "RaubÃ¼berfall Beute",
            f"{raeuber.mention} hat einen RaubÃ¼berfall durchgefÃ¼hrt.\n"
            f"**Beute:** {beute:,}$ â†’ Barbestand\n"
            f"**Bonus:** {bier}x Bier\n"
            f"**BestÃ¤tigt von:** {interaction.user.mention}"
        )

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=_build_result_embed(raeuber, self.bild_url, beute, bier, interaction.user, success=True),
            view=self
        )
        await interaction.response.send_message(
            f"âœ… Raub von {raeuber.mention} als **Erfolgreich** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="ðŸ”« RaubÃ¼berfall â€” Erfolgreich! ðŸ’°",
                description=(
                    f"Dein RaubÃ¼berfall war **erfolgreich**!\n\n"
                    f"**{beute:,}$** wurden in deinen **Barbestand** Ã¼bertragen.\n"
                    f"ZusÃ¤tzlich erhÃ¤ltst du **{bier}x Bier**."
                ),
                color=0x00CC44,
                timestamp=datetime.now(timezone.utc)
            )
            dm.add_field(name="ðŸ’µ Beute",          value=f"**{beute:,}$**",   inline=True)
            dm.add_field(name="ðŸº Bonus",          value=f"**{bier}x Bier**", inline=True)
            dm.add_field(name="ðŸ“ Gutgeschrieben", value="Barbestand (Cash)", inline=True)
            dm.set_footer(text="Paradise City Roleplay â€¢ RaubÃ¼berfall System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raube.discard(self.raeuber_id)

    @discord.ui.button(label="âŒ  Fehlschlag", style=discord.ButtonStyle.danger, custom_id="raubueberfall:fehlschlag")
    async def fehlschlag_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_team(interaction):
            await interaction.response.send_message("âŒ Nur Team-Mitglieder kÃ¶nnen bestÃ¤tigen.", ephemeral=True)
            return

        raeuber = interaction.guild.get_member(self.raeuber_id)
        if not raeuber:
            await interaction.response.send_message("âŒ Spieler nicht mehr auf dem Server.", ephemeral=True)
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
            f"âœ… Raub von {raeuber.mention} als **Fehlschlag** markiert.", ephemeral=True
        )

        try:
            dm = discord.Embed(
                title="ðŸ”« RaubÃ¼berfall â€” Fehlgeschlagen âŒ",
                description=(
                    "Dein RaubÃ¼berfall ist **fehlgeschlagen**.\n\n"
                    "â€¢ ðŸš” Festnahme durch Officers\n"
                    "â€¢ ðŸ¥ Verletzung / Tod\n"
                    "â€¢ ðŸ³ï¸ Abbruch\n\n"
                    "Du erhÃ¤ltst **keine Beute**."
                ),
                color=0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            dm.set_footer(text="Paradise City Roleplay â€¢ RaubÃ¼berfall System")
            await raeuber.send(embed=dm)
        except discord.Forbidden:
            pass

        _pending_raube.discard(self.raeuber_id)


# â”€â”€ on_message â€” Foto-Erkennung â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

    # â”€â”€ PDL-Pflicht prÃ¼fen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    on_duty_lapd = get_on_duty("lapd")
    if len(on_duty_lapd) < RAUB_MIN_PDL:
        try:
            await message.reply(
                f"âŒ FÃ¼r einen RaubÃ¼berfall mÃ¼ssen mindestens **{RAUB_MIN_PDL} Officers** im Dienst sein.\n"
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

    # â”€â”€ 24h-Cooldown prÃ¼fen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                    f"â³ Du kannst erst in **{verbleibend}h {minuten}min** wieder einen RaubÃ¼berfall machen.",
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
                "â³ Du hast bereits einen laufenden RaubÃ¼berfall eingereicht. Warte auf das Ergebnis.",
                delete_after=10
            )
        except discord.Forbidden:
            pass
        return

    # â”€â”€ Bild-Bytes sofort sichern â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    try:
        img_bytes    = await attachment.read()
        img_filename = attachment.filename or "beweis.jpg"
    except Exception:
        return

    _pending_raube.add(user.id)

    # â”€â”€ 24h-Cooldown setzen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    user_data["raub_last_raid"] = datetime.now(timezone.utc).isoformat()
    save_economy(eco)

    try:
        await message.delete()
    except discord.Forbidden:
        pass

    # â”€â”€ Beweis ins Team-Channel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # â”€â”€ BestÃ¤tigungs-DM an Spieler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    try:
        dm = discord.Embed(
            title="ðŸ”« RaubÃ¼berfall â€” Beweis eingereicht âœ…",
            description=(
                "Dein Beweis wurde erfolgreich eingereicht!\n\n"
                "Du hast ab jetzt **15 Minuten** Zeit."
            ),
            color=0xFF8C00,
            timestamp=datetime.now(timezone.utc)
        )
        dm.set_footer(text="Paradise City Roleplay â€¢ RaubÃ¼berfall System")
        await user.send(embed=dm)
    except discord.Forbidden:
        pass

    # â”€â”€ PDLer benachrichtigen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    for uid_str in on_duty_lapd:
        try:
            member = message.guild.get_member(int(uid_str))
            if not member:
                continue
            cop_embed = discord.Embed(
                title="ðŸš” LAPD â€” RaubÃ¼berfall gemeldet!",
                description=(
                    f"**VerdÃ¤chtiger:** {user.mention} (`{user.display_name}`)"
                ),
                color=0x1E90FF,
                timestamp=datetime.now(timezone.utc)
            )
            cop_embed.set_thumbnail(url=user.display_avatar.url)
            if bild_url:
                cop_embed.set_image(url=bild_url)
            cop_embed.set_footer(text="Paradise City Roleplay â€¢ LAPD")
            await member.send(embed=cop_embed)
        except discord.Forbidden:
            pass


# â”€â”€ Auto-Setup beim Start â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _raub_info_auto_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(RAUB_INFO_CHANNEL_ID)
        if not channel:
            continue

        embed        = build_raub_info_embed()
        existing_msg = None
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "RaubÃ¼berfall" in emb.title:
                            existing_msg = msg
                            break
                if existing_msg:
                    break
        except Exception:
            pass

        try:
            if existing_msg:
                await existing_msg.edit(embed=embed)
                print(f"[raubueberfall] âœ… Info-Embed aktualisiert in #{channel.name}")
            else:
                await channel.send(embed=embed)
                print(f"[raubueberfall] âœ… Info-Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[raubueberfall] âŒ Fehler beim Senden: {e}")


@bot.listen("on_ready")
async def raubueberfall_on_ready():
    await _raub_info_auto_setup()
