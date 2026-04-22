# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# rechnungen.py \u2014 Rechnungs- & Mahnungs-System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from economy_helpers import load_economy, save_economy, get_user
import uuid

RECHNUNG_ROLLEN = (LAMD_ROLE_ID, LAPD_ROLE_ID, LACS_ROLE_ID, LSPD_ROLE_ID)


# \u2500\u2500 Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def load_rechnungen():
    if RECHNUNGEN_FILE.exists():
        with open(RECHNUNGEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_rechnungen(data):
    with open(RECHNUNGEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def hat_rechnung_rolle(member: discord.Member) -> bool:
    return any(r.id in RECHNUNG_ROLLEN for r in member.roles)


# \u2500\u2500 Modal: Rechnung schreiben \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class RechnungModal(discord.ui.Modal, title="\U0001F4C4 Rechnung schreiben"):
    summe = discord.ui.TextInput(
        label="Summe ($)",
        placeholder="z.B. 5000",
        max_length=12,
    )
    grund = discord.ui.TextInput(
        label="Grund der Rechnung",
        style=discord.TextStyle.paragraph,
        placeholder="z.B. Schadensersatz f\u00FCr besch\u00E4digtes Fahrzeug",
        max_length=300,
    )

    def __init__(self, an_member: discord.Member):
        super().__init__()
        self.an_member = an_member

    async def on_submit(self, interaction: discord.Interaction):
        try:
            summe_int = int(
                self.summe.value.strip()
                .replace("$", "").replace(".", "")
                .replace(",", "").replace(" ", "")
            )
            if summe_int <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "\u274C Ung\u00FCltige Summe \u2014 bitte eine positive Zahl eingeben.", ephemeral=True
            )
            return

        data = load_rechnungen()
        uid  = str(self.an_member.id)
        if uid not in data:
            data[uid] = []

        rechnung_id = str(uuid.uuid4())[:8].upper()
        now = datetime.now(timezone.utc)

        data[uid].append({
            "id":           rechnung_id,
            "von_id":       interaction.user.id,
            "von_name":     str(interaction.user),
            "von_display":  interaction.user.display_name,
            "an_id":        self.an_member.id,
            "an_name":      str(self.an_member),
            "summe":        summe_int,
            "grund":        self.grund.value.strip(),
            "erstellt_am":  now.isoformat(),
            "mahnung":      None,
        })
        save_rechnungen(data)

        embed = discord.Embed(
            title="\U0001F4C4 Rechnung ausgestellt",
            color=0xE67E22,
            timestamp=now,
        )
        embed.set_thumbnail(url=self.an_member.display_avatar.url)
        embed.add_field(name="An",            value=self.an_member.mention,    inline=True)
        embed.add_field(name="Summe",         value=f"\U0001F4B5 {summe_int:,}$",       inline=True)
        embed.add_field(name="Rechnungs-ID",  value=f"`{rechnung_id}`",         inline=True)
        embed.add_field(name="Grund",         value=self.grund.value.strip(),   inline=False)
        embed.set_footer(text="Paradise City Roleplay \u2022 Rechnungs-System")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 Button: Einzelne Rechnung bezahlen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class EinzelBezahlenButton(discord.ui.Button):
    def __init__(self, rechnung: dict, row: int = 0):
        super().__init__(
            label=f"[{rechnung['id']}] {rechnung['summe']:,}$ bezahlen",
            style=discord.ButtonStyle.green,
            custom_id=f"einzel_bezahlen:{rechnung['id']}:{rechnung['an_id']}",
            row=row,
        )
        self.rechnung_id = rechnung["id"]
        self.von_id      = rechnung["von_id"]
        self.an_id       = rechnung["an_id"]
        self.summe       = rechnung["summe"]

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.an_id:
            await interaction.response.send_message(
                "\u274C Nur der Schuldner kann diese Rechnung bezahlen.", ephemeral=True
            )
            return

        eco    = load_economy()
        zahler = get_user(eco, self.an_id)

        if zahler["bank"] < self.summe:
            await interaction.response.send_message(
                f"\u274C Nicht genug Guthaben. Du ben\u00F6tigst **{self.summe:,}$** "
                f"(Kontostand: {zahler['bank']:,}$).",
                ephemeral=True,
            )
            return

        zahler["bank"] -= self.summe
        empfaenger = get_user(eco, self.von_id)
        empfaenger["bank"] += self.summe
        save_economy(eco)

        rdata = load_rechnungen()
        uid   = str(self.an_id)
        rdata[uid] = [r for r in rdata.get(uid, []) if r["id"] != self.rechnung_id]
        save_rechnungen(rdata)

        embed = discord.Embed(
            title="\u2705 Rechnung bezahlt",
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Rechnungs-ID",     value=f"`{self.rechnung_id}`",  inline=True)
        embed.add_field(name="Betrag",           value=f"\U0001F4B5 {self.summe:,}$",    inline=True)
        embed.add_field(name="Neuer Kontostand", value=f"\U0001F4B3 {zahler['bank']:,}$", inline=True)
        embed.set_footer(text="Paradise City Roleplay \u2022 Rechnungs-System")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            await interaction.message.delete()
        except Exception:
            pass


# \u2500\u2500 Button: Alle Rechnungen auf einmal bezahlen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class AlleBezahlenButton(discord.ui.Button):
    def __init__(self, an_id: int, rechnungen: list, row: int = 4):
        gesamt = sum(r["summe"] for r in rechnungen)
        super().__init__(
            label=f"\U0001F4B3 Alle auf einmal bezahlen ({gesamt:,}$)",
            style=discord.ButtonStyle.blurple,
            custom_id=f"alle_bezahlen:{an_id}",
            row=row,
        )
        self.an_id      = an_id
        self.rechnungen = rechnungen
        self.gesamt     = gesamt

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.an_id:
            await interaction.response.send_message(
                "\u274C Nur der Schuldner kann seine Rechnungen bezahlen.", ephemeral=True
            )
            return

        eco    = load_economy()
        zahler = get_user(eco, self.an_id)

        if zahler["bank"] < self.gesamt:
            await interaction.response.send_message(
                f"\u274C Nicht genug Guthaben. Du ben\u00F6tigst **{self.gesamt:,}$** "
                f"(Kontostand: {zahler['bank']:,}$).",
                ephemeral=True,
            )
            return

        zahler["bank"] -= self.gesamt
        for r in self.rechnungen:
            empfaenger = get_user(eco, r["von_id"])
            empfaenger["bank"] += r["summe"]
        save_economy(eco)

        rdata = load_rechnungen()
        uid   = str(self.an_id)
        ids   = {r["id"] for r in self.rechnungen}
        rdata[uid] = [r for r in rdata.get(uid, []) if r["id"] not in ids]
        save_rechnungen(rdata)

        embed = discord.Embed(
            title="\u2705 Alle Rechnungen bezahlt",
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Anzahl",           value=str(len(self.rechnungen)), inline=True)
        embed.add_field(name="Gesamtbetrag",     value=f"\U0001F4B5 {self.gesamt:,}$",    inline=True)
        embed.add_field(name="Neuer Kontostand", value=f"\U0001F4B3 {zahler['bank']:,}$", inline=True)
        embed.set_footer(text="Paradise City Roleplay \u2022 Rechnungs-System")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            await interaction.message.delete()
        except Exception:
            pass


# \u2500\u2500 View: Rechnungen anzeigen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class RechnungenView(TimedDisableView):
    def __init__(self, rechnungen: list, an_id: int):
        super().__init__(timeout=300)
        for i, r in enumerate(rechnungen[:4]):
            self.add_item(EinzelBezahlenButton(r, row=i))
        if rechnungen:
            self.add_item(AlleBezahlenButton(an_id, rechnungen, row=4))


# \u2500\u2500 Modal: Mahnung schreiben \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class MahnungModal(discord.ui.Modal, title="\u26A0\uFE0F Mahnung schreiben"):
    frist = discord.ui.TextInput(
        label="Zahlungsfrist",
        placeholder="z.B. 15.04.2025",
        max_length=20,
    )
    konsequenz = discord.ui.TextInput(
        label="Konsequenz bei Nichtzahlung",
        style=discord.TextStyle.paragraph,
        placeholder="z.B. Festnahme, Fahrzeugbeschlagnahmung...",
        max_length=300,
    )

    def __init__(self, an_id: int, rechnung_id: str):
        super().__init__()
        self.an_id       = an_id
        self.rechnung_id = rechnung_id

    async def on_submit(self, interaction: discord.Interaction):
        data      = load_rechnungen()
        rechnungen = data.get(str(self.an_id), [])
        found     = False

        for r in rechnungen:
            if r["id"] == self.rechnung_id:
                r["mahnung"] = {
                    "frist":       self.frist.value.strip(),
                    "konsequenz":  self.konsequenz.value.strip(),
                    "von_id":      interaction.user.id,
                    "von_name":    str(interaction.user),
                    "erstellt_am": datetime.now(timezone.utc).isoformat(),
                }
                found = True
                break

        if not found:
            await interaction.response.send_message("\u274C Rechnung nicht gefunden.", ephemeral=True)
            return

        save_rechnungen(data)
        await interaction.response.send_message(
            f"\u26A0\uFE0F Mahnung f\u00FCr Rechnung `{self.rechnung_id}` erfolgreich hinzugef\u00FCgt.", ephemeral=True
        )


# \u2500\u2500 Select: Rechnung f\u00FCr Mahnung w\u00E4hlen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class MahnungSelect(discord.ui.Select):
    def __init__(self, an_id: int, rechnungen: list):
        self.an_id = an_id
        options = [
            discord.SelectOption(
                label=f"[{r['id']}] {r['summe']:,}$",
                value=r["id"],
                description=r["grund"][:50],
            )
            for r in rechnungen[:25]
        ]
        super().__init__(placeholder="Rechnung ausw\u00E4hlen...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            MahnungModal(an_id=self.an_id, rechnung_id=self.values[0])
        )


class MahnungView(TimedDisableView):
    def __init__(self, an_id: int, rechnungen: list):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.add_item(MahnungSelect(an_id, rechnungen))


# \u2500\u2500 Commands \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="rechnung-schreiben",
    description="[Beh\u00F6rde] Stelle eine Rechnung an einen Spieler aus",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="Spieler dem die Rechnung gestellt wird")
async def rechnung_schreiben(interaction: discord.Interaction, nutzer: discord.Member):
    is_privileged = any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID, INHABER_ROLE_ID) for r in interaction.user.roles)
    if not is_privileged and interaction.channel.id != RECHNUNGEN_CHANNEL_ID:
        await interaction.response.send_message(
            f"\u274C Diesen Command kannst du nur in <#{RECHNUNGEN_CHANNEL_ID}> benutzen.",
            ephemeral=True,
        )
        return
    if not hat_rechnung_rolle(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return
    await interaction.response.send_modal(RechnungModal(an_member=nutzer))


async def _zeige_rechnungen(interaction: discord.Interaction):
    """Gemeinsame Logik: Rechnungen ephemeral anzeigen."""
    data   = load_rechnungen()
    eigene = data.get(str(interaction.user.id), [])

    if not eigene:
        await interaction.response.send_message(
            "\u2705 Du hast keine offenen Rechnungen.", ephemeral=True
        )
        return

    embeds = []
    for r in eigene[:10]:
        color = 0xFF0000 if r.get("mahnung") else 0xE67E22
        embed = discord.Embed(
            title=f"\U0001F4C4 Rechnung `{r['id']}`",
            color=color,
            timestamp=datetime.fromisoformat(r["erstellt_am"]),
        )
        embed.add_field(name="Von",   value=r["von_display"], inline=True)
        embed.add_field(name="Summe", value=f"\U0001F4B5 {r['summe']:,}$", inline=True)
        embed.add_field(
            name="Ausgestellt am",
            value=datetime.fromisoformat(r["erstellt_am"]).strftime("%d.%m.%Y"),
            inline=True,
        )
        embed.add_field(name="Grund", value=r["grund"], inline=False)
        if r.get("mahnung"):
            m = r["mahnung"]
            embed.add_field(
                name="\u26A0\uFE0F MAHNUNG",
                value=f"**Frist:** {m['frist']}\n**Konsequenz:** {m['konsequenz']}",
                inline=False,
            )
        embed.set_footer(text="Paradise City Roleplay \u2022 Rechnungs-System")
        embeds.append(embed)

    hinweis = ""
    if len(eigene) > 4:
        hinweis = (
            f"\u26A0\uFE0F Du hast {len(eigene)} offene Rechnungen. "
            "Nur die ersten 4 k\u00F6nnen einzeln bezahlt werden \u2014 "
            "nutze **Alle auf einmal bezahlen** f\u00FCr alle."
        )
    if hinweis:
        embeds[0].description = hinweis

    view = RechnungenView(eigene, interaction.user.id)
    await interaction.response.send_message(embeds=embeds, view=view, ephemeral=True)


# \u2500\u2500 Persistent-Panel: Rechnungen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class RechnungenPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Rechnungen anzeigen",
        emoji="\U0001F4C4",
        style=discord.ButtonStyle.danger,
        custom_id="rechnungen_panel_anzeigen"
    )
    async def anzeigen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _zeige_rechnungen(interaction)


@bot.tree.command(
    name="setup-rechnungen-panel",
    description="[Admin] Postet das Rechnungen-Panel in den Rechnungen-Kanal",
    guild=discord.Object(id=GUILD_ID),
)
async def setup_rechnungen_panel(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return
    kanal = interaction.guild.get_channel(RECHNUNGEN_CHANNEL_ID)
    if not kanal:
        await interaction.response.send_message("\u274C Kanal nicht gefunden.", ephemeral=True)
        return
    sep = "\u2015" * 22
    embed = discord.Embed(
        title="\U0001F4C4 Rechnungen",
        description=(
            sep + "\n"
            "Klicke auf den Button um deine offenen Rechnungen\n"
            "einzusehen und zu bezahlen.\n"
            + sep
        ),
        color=0xE74C3C,
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Rechnungs-System")
    await kanal.send(embed=embed, view=RechnungenPanelView())
    await interaction.response.send_message("\u2705 Rechnungen-Panel gepostet.", ephemeral=True)


@bot.tree.command(
    name="mahnung",
    description="[Beh\u00F6rde] F\u00FCge einer Rechnung eine Mahnung hinzu",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="Spieler dessen Rechnung eine Mahnung erh\u00E4lt")
async def mahnung_cmd(interaction: discord.Interaction, nutzer: discord.Member):
    is_privileged = any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID, INHABER_ROLE_ID) for r in interaction.user.roles)
    if not is_privileged and interaction.channel.id != RECHNUNGEN_CHANNEL_ID:
        await interaction.response.send_message(
            f"\u274C Diesen Command kannst du nur in <#{RECHNUNGEN_CHANNEL_ID}> benutzen.",
            ephemeral=True,
        )
        return
    if not hat_rechnung_rolle(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    data       = load_rechnungen()
    rechnungen = data.get(str(nutzer.id), [])

    if not rechnungen:
        await interaction.response.send_message(
            f"\u274C **{nutzer.display_name}** hat keine offenen Rechnungen.", ephemeral=True
        )
        return

    if len(rechnungen) == 1:
        await interaction.response.send_modal(
            MahnungModal(an_id=nutzer.id, rechnung_id=rechnungen[0]["id"])
        )
    else:
        view = MahnungView(an_id=nutzer.id, rechnungen=rechnungen)
        await interaction.response.send_message(
            f"Welche Rechnung von **{nutzer.display_name}** soll eine Mahnung erhalten?",
            view=view,
            ephemeral=True,
        )
