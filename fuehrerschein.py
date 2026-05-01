# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# fuehrerschein.py \u2014 F\u00FChrerschein System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from helpers import is_admin


def load_fuehrerschein():
    if FUEHRERSCHEIN_FILE.exists():
        with open(FUEHRERSCHEIN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_fuehrerschein(data):
    with open(FUEHRERSCHEIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def has_fuehrerschein_erstellen_perm(member: discord.Member) -> bool:
    return any(r.id in (FUEHRERSCHEIN_ERSTELLEN_ROLE_ID, ADMIN_ROLE_ID, MOD_ROLE_ID) for r in member.roles)


def has_fuehrerschein_entziehen_perm(member: discord.Member) -> bool:
    return any(r.id in (FUEHRERSCHEIN_ENTZIEHEN_ROLE_ID, ADMIN_ROLE_ID, MOD_ROLE_ID) for r in member.roles)


# \u2500\u2500 Modal f\u00FCr F\u00FChrerschein-Erstellung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class FuehrerscheinModal(discord.ui.Modal, title="\U0001FAAA F\u00FChrerschein ausstellen"):
    vorname = discord.ui.TextInput(
        label="Vorname",
        placeholder="z.B. Max",
        max_length=50,
    )
    nachname = discord.ui.TextInput(
        label="Nachname",
        placeholder="z.B. Mustermann",
        max_length=50,
    )
    geburtsdatum = discord.ui.TextInput(
        label="Geburtsdatum",
        placeholder="TT.MM.JJJJ",
        max_length=10,
    )
    ausweisnummer = discord.ui.TextInput(
        label="Ausweisnummer",
        placeholder="z.B. AB-123456",
        max_length=20,
    )
    fuehrerschein_klasse = discord.ui.TextInput(
        label="F\u00FChrerschein-Klasse(n)",
        placeholder="z.B. B, BE, C \u2014 mehrere mit Komma trennen",
        max_length=50,
    )

    def __init__(self, zielperson: discord.Member):
        super().__init__()
        self.zielperson = zielperson

    async def on_submit(self, interaction: discord.Interaction):
        data = load_fuehrerschein()
        uid  = str(self.zielperson.id)
        now  = datetime.now(timezone.utc)

        data[uid] = {
            "vorname":              self.vorname.value.strip(),
            "nachname":             self.nachname.value.strip(),
            "geburtsdatum":         self.geburtsdatum.value.strip(),
            "ausweisnummer":        self.ausweisnummer.value.strip(),
            "fuehrerschein_klasse": self.fuehrerschein_klasse.value.strip(),
            "ausgestellt_am":       now.isoformat(),
            "ausgestellt_von_id":   interaction.user.id,
            "ausgestellt_von_name": str(interaction.user),
            "discord_id":           self.zielperson.id,
            "discord_name":         str(self.zielperson),
            "entzogen":             False,
            "entzug_grund":         None,
            "entzug_von_id":        None,
            "entzug_von_name":      None,
            "entzug_zeit":          None,
        }
        save_fuehrerschein(data)

        embed = discord.Embed(
            title="\U0001FAAA F\u00FChrerschein ausgestellt",
            color=0x00AA00,
            timestamp=now,
        )
        embed.set_author(name="Paradise City Roleplay \u2014 F\u00FChrerschein")
        embed.set_thumbnail(url=self.zielperson.display_avatar.url)
        embed.add_field(name="Inhaber",              value=self.zielperson.mention,                                      inline=True)
        embed.add_field(name="Name",                 value=f"{self.vorname.value.strip()} {self.nachname.value.strip()}", inline=True)
        embed.add_field(name="Geburtsdatum",         value=self.geburtsdatum.value.strip(),                              inline=True)
        embed.add_field(name="Ausweisnummer",        value=f"`{self.ausweisnummer.value.strip()}`",                     inline=True)
        embed.add_field(name="F\u00FChrerschein-Klasse",  value=self.fuehrerschein_klasse.value.strip(),                     inline=True)
        embed.add_field(name="Ausgestellt von",      value=interaction.user.mention,                                    inline=True)
        embed.set_footer(text="Paradise City Roleplay \u2014 F\u00FChrerschein")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            player_embed = discord.Embed(
                title="\U0001F697 Dein F\u00FChrerschein wurde ausgestellt!",
                color=0x00AA00,
                timestamp=now,
            )
            player_embed.add_field(name="Name",                value=f"{self.vorname.value.strip()} {self.nachname.value.strip()}", inline=True)
            player_embed.add_field(name="Klasse(n)",           value=self.fuehrerschein_klasse.value.strip(),                       inline=True)
            player_embed.add_field(name="Ausgestellt am",      value=now.strftime("%d.%m.%Y"),                                      inline=True)
            player_embed.add_field(name="Ausgestellt von",     value=interaction.user.display_name,                                 inline=False)
            player_embed.set_footer(text="Paradise City Roleplay \u2014 F\u00FChrerschein")
            await self.zielperson.send(embed=player_embed)
        except Exception:
            pass


# \u2500\u2500 Modal f\u00FCr F\u00FChrerschein-Entzug \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class FuehrerscheinEntzugModal(discord.ui.Modal, title="\U0001F6AB F\u00FChrerschein entziehen"):
    grund = discord.ui.TextInput(
        label="Grund des Entzugs",
        style=discord.TextStyle.paragraph,
        placeholder="z.B. Fahren unter Alkoholeinfluss...",
        required=True,
        max_length=500,
    )

    def __init__(self, zielperson: discord.Member, grund_required: bool = True):
        super().__init__()
        self.zielperson = zielperson
        if not grund_required:
            self.grund.required = False
            self.grund.placeholder = "(Optional) Grund des Entzugs..."

    async def on_submit(self, interaction: discord.Interaction):
        data = load_fuehrerschein()
        uid  = str(self.zielperson.id)
        entry = data.get(uid)

        if not entry:
            await interaction.response.send_message(
                f"\u274C **{self.zielperson.display_name}** hat keinen F\u00FChrerschein.", ephemeral=True
            )
            return

        if entry.get("entzogen"):
            await interaction.response.send_message(
                f"\u274C Der F\u00FChrerschein von **{self.zielperson.display_name}** ist bereits entzogen.", ephemeral=True
            )
            return

        now = datetime.now(timezone.utc)
        grund_text = (
            self.grund.value.strip()
            if self.grund.value and self.grund.value.strip()
            else "Kein Grund angegeben"
        )

        entry["entzogen"]        = True
        entry["entzug_grund"]    = grund_text
        entry["entzug_von_id"]   = interaction.user.id
        entry["entzug_von_name"] = str(interaction.user)
        entry["entzug_zeit"]     = now.isoformat()
        save_fuehrerschein(data)

        embed = discord.Embed(
            title="\U0001F6AB F\u00FChrerschein entzogen",
            color=0xFF0000,
            timestamp=now,
        )
        embed.set_author(name="Paradise City Roleplay \u2014 F\u00FChrerschein")
        embed.set_thumbnail(url=self.zielperson.display_avatar.url)
        embed.add_field(name="Inhaber",      value=self.zielperson.mention,  inline=True)
        embed.add_field(name="Entzogen von", value=interaction.user.mention, inline=True)
        embed.add_field(name="Grund",        value=grund_text,               inline=False)
        embed.set_footer(text="Paradise City Roleplay \u2014 F\u00FChrerschein")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# /create-f\u00FChrerschein
@bot.tree.command(
    name="create-f\u00FChrerschein",
    description="[Beh\u00F6rde] Erstelle einen F\u00FChrerschein f\u00FCr einen Spieler",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="Spieler f\u00FCr den der F\u00FChrerschein ausgestellt wird")
async def create_fuehrerschein(interaction: discord.Interaction, nutzer: discord.Member):
    if not has_fuehrerschein_erstellen_perm(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return
    modal = FuehrerscheinModal(zielperson=nutzer)
    await interaction.response.send_modal(modal)


# /f\u00FChrerschein
@bot.tree.command(
    name="f\u00FChrerschein",
    description="[Ausweis] Zeige deinen F\u00FChrerschein vor",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="(Nur Team) F\u00FChrerschein eines anderen Spielers abrufen")
async def fuehrerschein(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids = [r.id for r in interaction.user.roles]
    is_team  = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids


    target = nutzer if (is_team and nutzer) else interaction.user

    data  = load_fuehrerschein()
    entry = data.get(str(target.id))

    if not entry:
        msg = (
            f"\u274C **{target.display_name}** besitzt keinen F\u00FChrerschein."
            if target != interaction.user else
            "\u274C Du besitzt keinen F\u00FChrerschein."
        )
        await interaction.response.send_message(msg, ephemeral=True)
        return

    status_emoji = "\U0001F6AB **ENTZOGEN**" if entry.get("entzogen") else "\u2705 G\u00FCltig"
    embed = discord.Embed(
        title="\U0001F697 F\u00FChrerschein",
        color=0xFF0000 if entry.get("entzogen") else 0x00AA00,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(name="Paradise City Roleplay \u2014 F\u00FChrerschein")
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Inhaber",             value=target.mention,                                      inline=True)
    embed.add_field(name="Name",                value=f"{entry['vorname']} {entry['nachname']}",           inline=True)
    embed.add_field(name="Geburtsdatum",        value=entry["geburtsdatum"],                               inline=True)
    embed.add_field(name="Ausweisnummer",       value=f"`{entry['ausweisnummer']}`",                      inline=True)
    embed.add_field(name="F\u00FChrerschein-Klasse", value=entry["fuehrerschein_klasse"],                      inline=True)
    embed.add_field(name="Status",              value=status_emoji,                                       inline=True)

    if entry.get("entzogen"):
        embed.add_field(name="Entzugsgrund", value=entry.get("entzug_grund", "\u2014"), inline=False)

    embed.set_footer(text="Paradise City Roleplay \u2014 F\u00FChrerschein")
    await interaction.response.send_message(embed=embed, ephemeral=is_team and nutzer is not None)


# /remove-f\u00FChrerschein
@bot.tree.command(
    name="remove-f\u00FChrerschein",
    description="[Beh\u00F6rde] Entziehe einem Spieler den F\u00FChrerschein",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="Spieler dem der F\u00FChrerschein entzogen werden soll")
async def remove_fuehrerschein(interaction: discord.Interaction, nutzer: discord.Member):
    if not has_fuehrerschein_entziehen_perm(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return
    grund_optional = is_admin(interaction.user)
    modal = FuehrerscheinEntzugModal(zielperson=nutzer, grund_required=not grund_optional)
    await interaction.response.send_modal(modal)


# /f\u00FChrerschein-geben
@bot.tree.command(
    name="f\u00FChrerschein-geben",
    description="[Beh\u00F6rde] Gib einem Spieler den entzogenen F\u00FChrerschein zur\u00FCck",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="Spieler dem der F\u00FChrerschein zur\u00FCckgegeben werden soll")
async def fuehrerschein_geben(interaction: discord.Interaction, nutzer: discord.Member):
    if not has_fuehrerschein_entziehen_perm(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    data  = load_fuehrerschein()
    uid   = str(nutzer.id)
    entry = data.get(uid)

    if not entry:
        await interaction.response.send_message(
            f"\u274C **{nutzer.display_name}** hat keinen F\u00FChrerschein.", ephemeral=True
        )
        return

    if not entry.get("entzogen"):
        await interaction.response.send_message(
            f"\u274C Der F\u00FChrerschein von **{nutzer.display_name}** ist nicht entzogen.", ephemeral=True
        )
        return

    entry["entzogen"]        = False
    entry["entzug_grund"]    = None
    entry["entzug_von_id"]   = None
    entry["entzug_von_name"] = None
    entry["entzug_zeit"]     = None
    save_fuehrerschein(data)

    embed = discord.Embed(
        title="\u2705 F\u00FChrerschein zur\u00FCckgegeben",
        color=0x00AA00,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(name="Paradise City Roleplay \u2014 F\u00FChrerschein")
    embed.set_thumbnail(url=nutzer.display_avatar.url)
    embed.add_field(name="Inhaber",           value=nutzer.mention,          inline=True)
    embed.add_field(name="Zur\u00FCckgegeben von", value=interaction.user.mention,inline=True)
    embed.add_field(name="Name",              value=f"{entry['vorname']} {entry['nachname']}", inline=False)
    embed.set_footer(text="Paradise City Roleplay \u2014 F\u00FChrerschein")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 Modal f\u00FCr F\u00FChrerschein-Bearbeitung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class FuehrerscheinEditModal(discord.ui.Modal, title="\u270F\uFE0F F\u00FChrerschein bearbeiten"):
    vorname = discord.ui.TextInput(
        label="Vorname",
        max_length=50,
    )
    nachname = discord.ui.TextInput(
        label="Nachname",
        max_length=50,
    )
    geburtsdatum = discord.ui.TextInput(
        label="Geburtsdatum",
        placeholder="TT.MM.JJJJ",
        max_length=10,
    )
    ausweisnummer = discord.ui.TextInput(
        label="Ausweisnummer",
        max_length=20,
    )
    fuehrerschein_klasse = discord.ui.TextInput(
        label="F\u00FChrerschein-Klasse(n)",
        placeholder="z.B. B, BE, C",
        max_length=50,
    )

    def __init__(self, zielperson: discord.Member, entry: dict):
        super().__init__()
        self.zielperson = zielperson
        self.vorname.default             = entry.get("vorname", "")
        self.nachname.default            = entry.get("nachname", "")
        self.geburtsdatum.default        = entry.get("geburtsdatum", "")
        self.ausweisnummer.default       = entry.get("ausweisnummer", "")
        self.fuehrerschein_klasse.default = entry.get("fuehrerschein_klasse", "")

    async def on_submit(self, interaction: discord.Interaction):
        data  = load_fuehrerschein()
        uid   = str(self.zielperson.id)
        entry = data.get(uid)

        if not entry:
            await interaction.response.send_message(
                f"\u274C **{self.zielperson.display_name}** hat keinen F\u00FChrerschein mehr.", ephemeral=True
            )
            return

        entry["vorname"]              = self.vorname.value.strip()
        entry["nachname"]             = self.nachname.value.strip()
        entry["geburtsdatum"]         = self.geburtsdatum.value.strip()
        entry["ausweisnummer"]        = self.ausweisnummer.value.strip()
        entry["fuehrerschein_klasse"] = self.fuehrerschein_klasse.value.strip()
        entry["bearbeitet_von_id"]    = interaction.user.id
        entry["bearbeitet_von_name"]  = str(interaction.user)
        entry["bearbeitet_am"]        = datetime.now(timezone.utc).isoformat()
        save_fuehrerschein(data)

        now = datetime.now(timezone.utc)
        embed = discord.Embed(
            title="\u270F\uFE0F F\u00FChrerschein bearbeitet",
            color=0xFFA500,
            timestamp=now,
        )
        embed.set_author(name="Paradise City Roleplay \u2014 F\u00FChrerschein")
        embed.set_thumbnail(url=self.zielperson.display_avatar.url)
        embed.add_field(name="Inhaber",             value=self.zielperson.mention,                                              inline=True)
        embed.add_field(name="Bearbeitet von",      value=interaction.user.mention,                                            inline=True)
        embed.add_field(name="Name",                value=f"{entry['vorname']} {entry['nachname']}",                           inline=False)
        embed.add_field(name="Geburtsdatum",        value=entry["geburtsdatum"],                                               inline=True)
        embed.add_field(name="Ausweisnummer",       value=f"`{entry['ausweisnummer']}`",                                      inline=True)
        embed.add_field(name="F\u00FChrerschein-Klasse", value=entry["fuehrerschein_klasse"],                                      inline=True)
        embed.set_footer(text="Paradise City Roleplay \u2014 F\u00FChrerschein")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            dm_embed = discord.Embed(
                title="\u270F\uFE0F Dein F\u00FChrerschein wurde aktualisiert",
                color=0xFFA500,
                timestamp=now,
            )
            dm_embed.add_field(name="Name",                value=f"{entry['vorname']} {entry['nachname']}", inline=True)
            dm_embed.add_field(name="Klasse(n)",           value=entry["fuehrerschein_klasse"],             inline=True)
            dm_embed.add_field(name="Ausweisnummer",       value=f"`{entry['ausweisnummer']}`",            inline=True)
            dm_embed.add_field(name="Bearbeitet von",      value=interaction.user.display_name,             inline=False)
            dm_embed.set_footer(text="Paradise City Roleplay \u2014 F\u00FChrerschein")
            await self.zielperson.send(embed=dm_embed)
        except Exception:
            pass


# /f\u00FChrerschein-edit
@bot.tree.command(
    name="f\u00FChrerschein-edit",
    description="[Beh\u00F6rde] Bearbeite den F\u00FChrerschein eines Spielers",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="Spieler dessen F\u00FChrerschein bearbeitet werden soll")
async def fuehrerschein_edit(interaction: discord.Interaction, nutzer: discord.Member):
    if not has_fuehrerschein_erstellen_perm(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    data  = load_fuehrerschein()
    uid   = str(nutzer.id)
    entry = data.get(uid)

    if not entry:
        await interaction.response.send_message(
            f"\u274C **{nutzer.display_name}** hat keinen F\u00FChrerschein.\n"
            f"Erstelle zuerst einen mit `/create-f\u00FChrerschein`.",
            ephemeral=True
        )
        return

    modal = FuehrerscheinEditModal(zielperson=nutzer, entry=entry)
    await interaction.response.send_modal(modal)


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# Fahrlehrer-Lizenz System
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

def load_fahrlehrer_lizenz():
    if FAHRLEHRER_LIZENZ_FILE.exists():
        with open(FAHRLEHRER_LIZENZ_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_fahrlehrer_lizenz(data):
    with open(FAHRLEHRER_LIZENZ_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class FahrlehrerLizenzModal(discord.ui.Modal, title="\U0001F4CB Fahrlehrer-Lizenz ausstellen"):
    vorname = discord.ui.TextInput(
        label="Vorname",
        placeholder="z.B. Max",
        max_length=50,
    )
    nachname = discord.ui.TextInput(
        label="Nachname",
        placeholder="z.B. Mustermann",
        max_length=50,
    )
    geburtsdatum = discord.ui.TextInput(
        label="Geburtsdatum",
        placeholder="TT.MM.JJJJ",
        max_length=10,
    )
    lizenznummer = discord.ui.TextInput(
        label="Lizenznummer",
        placeholder="z.B. FL-2024-001",
        max_length=20,
    )

    def __init__(self, zielperson: discord.Member):
        super().__init__()
        self.zielperson = zielperson

    async def on_submit(self, interaction: discord.Interaction):
        data = load_fahrlehrer_lizenz()
        uid  = str(self.zielperson.id)
        now  = datetime.now(timezone.utc)

        data[uid] = {
            "vorname":             self.vorname.value.strip(),
            "nachname":            self.nachname.value.strip(),
            "geburtsdatum":        self.geburtsdatum.value.strip(),
            "lizenznummer":        self.lizenznummer.value.strip(),
            "ausgestellt_am":      now.isoformat(),
            "ausgestellt_von_id":  interaction.user.id,
            "ausgestellt_von_name":str(interaction.user),
            "discord_id":          self.zielperson.id,
            "discord_name":        str(self.zielperson),
            "entzogen":            False,
            "entzug_grund":        None,
            "entzug_von_id":       None,
            "entzug_von_name":     None,
            "entzug_zeit":         None,
        }
        save_fahrlehrer_lizenz(data)

        embed = discord.Embed(
            title="\U0001F4CB Fahrlehrer-Lizenz ausgestellt",
            color=0x00AA00,
            timestamp=now,
        )
        embed.set_author(name="Paradise City Roleplay \u2014 Fahrlehrer-Lizenz")
        embed.set_thumbnail(url=self.zielperson.display_avatar.url)
        embed.add_field(name="Inhaber",          value=self.zielperson.mention,                                       inline=True)
        embed.add_field(name="Name",             value=f"{self.vorname.value.strip()} {self.nachname.value.strip()}", inline=True)
        embed.add_field(name="Geburtsdatum",     value=self.geburtsdatum.value.strip(),                              inline=True)
        embed.add_field(name="Lizenznummer",     value=f"`{self.lizenznummer.value.strip()}`",                       inline=True)
        embed.add_field(name="Ausgestellt von",  value=interaction.user.mention,                                     inline=True)
        embed.set_footer(text="Paradise City Roleplay \u2014 Fahrlehrer-Lizenz")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            dm_embed = discord.Embed(
                title="\U0001F4CB Deine Fahrlehrer-Lizenz wurde ausgestellt!",
                color=0x00AA00,
                timestamp=now,
            )
            dm_embed.add_field(name="Name",             value=f"{self.vorname.value.strip()} {self.nachname.value.strip()}", inline=True)
            dm_embed.add_field(name="Lizenznummer",     value=f"`{self.lizenznummer.value.strip()}`",                       inline=True)
            dm_embed.add_field(name="Ausgestellt am",   value=now.strftime("%d.%m.%Y"),                                     inline=True)
            dm_embed.add_field(name="Ausgestellt von",  value=interaction.user.display_name,                                inline=False)
            dm_embed.set_footer(text="Paradise City Roleplay \u2014 Fahrlehrer-Lizenz")
            await self.zielperson.send(embed=dm_embed)
        except Exception:
            pass


class FahrlehrerLizenzEntzugModal(discord.ui.Modal, title="\U0001F6AB Fahrlehrer-Lizenz entziehen"):
    grund = discord.ui.TextInput(
        label="Grund des Entzugs",
        style=discord.TextStyle.paragraph,
        placeholder="z.B. Versto\u00DF gegen Fahrschulregeln...",
        required=True,
        max_length=500,
    )

    def __init__(self, zielperson: discord.Member):
        super().__init__()
        self.zielperson = zielperson

    async def on_submit(self, interaction: discord.Interaction):
        data  = load_fahrlehrer_lizenz()
        uid   = str(self.zielperson.id)
        entry = data.get(uid)

        if not entry:
            await interaction.response.send_message(
                f"\u274C **{self.zielperson.display_name}** besitzt keine Fahrlehrer-Lizenz.", ephemeral=True
            )
            return

        if entry.get("entzogen"):
            await interaction.response.send_message(
                f"\u274C Die Lizenz von **{self.zielperson.display_name}** ist bereits entzogen.", ephemeral=True
            )
            return

        now        = datetime.now(timezone.utc)
        grund_text = self.grund.value.strip() or "Kein Grund angegeben"

        entry["entzogen"]         = True
        entry["entzug_grund"]     = grund_text
        entry["entzug_von_id"]    = interaction.user.id
        entry["entzug_von_name"]  = str(interaction.user)
        entry["entzug_zeit"]      = now.isoformat()
        save_fahrlehrer_lizenz(data)

        embed = discord.Embed(
            title="\U0001F6AB Fahrlehrer-Lizenz entzogen",
            color=0xFF0000,
            timestamp=now,
        )
        embed.set_author(name="Paradise City Roleplay \u2014 Fahrlehrer-Lizenz")
        embed.set_thumbnail(url=self.zielperson.display_avatar.url)
        embed.add_field(name="Inhaber",      value=self.zielperson.mention,  inline=True)
        embed.add_field(name="Entzogen von", value=interaction.user.mention, inline=True)
        embed.add_field(name="Grund",        value=grund_text,               inline=False)
        embed.set_footer(text="Paradise City Roleplay \u2014 Fahrlehrer-Lizenz")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# /create-fahrlehrer (Admin + Mod only)
@bot.tree.command(
    name="create-fahrlehrer",
    description="[Admin] Erstelle eine Fahrlehrer-Lizenz f\u00FCr einen Spieler",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="Spieler f\u00FCr den die Fahrlehrer-Lizenz ausgestellt wird")
async def create_fahrlehrer(interaction: discord.Interaction, nutzer: discord.Member):
    await interaction.response.send_modal(FahrlehrerLizenzModal(zielperson=nutzer))


# /fahrlehrer-lizenz (Fahrlehrer + Admin + Mod)
@bot.tree.command(
    name="fahrlehrer-lizenz",
    description="[Fahrlehrer] Zeige deine Fahrlehrer-Lizenz vor",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="(Nur Team) Lizenz eines anderen Spielers abrufen")
async def fahrlehrer_lizenz(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids = [r.id for r in interaction.user.roles]
    is_team  = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids

    if not any(r in role_ids for r in (FUEHRERSCHEIN_ERSTELLEN_ROLE_ID, ADMIN_ROLE_ID, MOD_ROLE_ID)):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    target = nutzer if (is_team and nutzer) else interaction.user

    data  = load_fahrlehrer_lizenz()
    entry = data.get(str(target.id))

    if not entry:
        msg = (
            f"\u274C **{target.display_name}** besitzt keine Fahrlehrer-Lizenz."
            if target != interaction.user else
            "\u274C Du besitzt keine Fahrlehrer-Lizenz."
        )
        await interaction.response.send_message(msg, ephemeral=True)
        return

    status_emoji = "\U0001F6AB **ENTZOGEN**" if entry.get("entzogen") else "\u2705 G\u00FCltig"
    embed = discord.Embed(
        title="\U0001F4CB Fahrlehrer-Lizenz",
        color=0xFF0000 if entry.get("entzogen") else 0x00AA00,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(name="Paradise City Roleplay \u2014 Fahrlehrer-Lizenz")
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Inhaber",      value=target.mention,                            inline=True)
    embed.add_field(name="Name",         value=f"{entry['vorname']} {entry['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum", value=entry["geburtsdatum"],                     inline=True)
    embed.add_field(name="Lizenznummer", value=f"`{entry['lizenznummer']}`",              inline=True)
    embed.add_field(name="Status",       value=status_emoji,                              inline=True)

    if entry.get("entzogen"):
        embed.add_field(name="Entzugsgrund", value=entry.get("entzug_grund", "\u2014"), inline=False)

    embed.set_footer(text="Paradise City Roleplay \u2014 Fahrlehrer-Lizenz")
    await interaction.response.send_message(embed=embed, ephemeral=is_team and nutzer is not None)


# /remove-lizenz (LAPD + Mod + Admin)
@bot.tree.command(
    name="remove-lizenz",
    description="[Beh\u00F6rde] Entziehe einem Spieler die Fahrlehrer-Lizenz",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(nutzer="Spieler dem die Fahrlehrer-Lizenz entzogen werden soll")
async def remove_lizenz(interaction: discord.Interaction, nutzer: discord.Member):
    await interaction.response.send_modal(FahrlehrerLizenzEntzugModal(zielperson=nutzer))
