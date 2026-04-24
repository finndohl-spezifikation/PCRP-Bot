# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# einreise.py \u2014 Einreise- & Ausweis-System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from config import *
from helpers import log_bot_error


# \u2500\u2500 Ausweis Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def load_ausweis():
    if AUSWEIS_FILE.exists():
        with open(AUSWEIS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_ausweis(data):
    with open(AUSWEIS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_ausweisnummer():
    letters = random.choices(string.ascii_uppercase, k=2)
    digits  = random.choices(string.digits, k=6)
    return "".join(letters) + "-" + "".join(digits)


async def _assign_charakter_rollen(member: discord.Member, guild: discord.Guild,
                                    einreise_typ: str):
    if not guild:
        return
    try:
        role_id = LEGAL_ROLE_ID if einreise_typ == "legal" else ILLEGAL_ROLE_ID
        role    = guild.get_role(role_id)
        if role:
            await member.add_roles(role, reason=f"Einreise: {einreise_typ}")
    except Exception:
        pass

    try:
        rollen = [guild.get_role(rid) for rid in CHARAKTER_ROLLEN if guild.get_role(rid)]
        if rollen:
            await member.add_roles(*rollen, reason="Charakter erstellt")
    except Exception:
        pass

    try:
        bewerber = guild.get_role(BEWERBER_ROLE_ID)
        if bewerber and bewerber in member.roles:
            await member.remove_roles(bewerber, reason="Ausweis erstellt")
    except Exception:
        pass


# \u2500\u2500 Spieler-Modal \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

# \u2500\u2500 DM Q&A Ausweis \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_pending_ausweis: dict = {}   # uid -> {step, einreise_typ, data}

_AUSWEIS_FRAGEN = [
    ("vollstaendiger_name", "\U0001f4dd **Schritt 1/5 \u2014 Vollst\u00e4ndiger Name**\nBitte gib deinen vollst\u00e4ndigen Roleplay-Namen ein *(Vorname Nachname)*:"),
    ("geburtsdatum",        "\U0001f4c5 **Schritt 2/5 \u2014 Geburtsdatum**\nFormat: TT.MM.JJJJ"),
    ("alter",               "\U0001f522 **Schritt 3/5 \u2014 Alter**\nWie alt ist dein Charakter?"),
    ("nationalitaet",       "\U0001f30d **Schritt 4/5 \u2014 Nationalit\u00e4t**\nz.B. Deutsch, Amerikanisch \u2026"),
    ("wohnort",             "\U0001f3e0 **Schritt 5/5 \u2014 Wohnort**\nz.B. Los Santos"),
]


@bot.listen("on_message")
async def _ausweis_dm_listener(message: discord.Message):
    if message.guild is not None or message.author.bot:
        return
    uid = message.author.id
    if uid not in _pending_ausweis:
        return
    session = _pending_ausweis[uid]
    step    = session["step"]
    field, _ = _AUSWEIS_FRAGEN[step]
    session["data"][field] = message.content.strip()
    step += 1
    session["step"] = step
    if step < len(_AUSWEIS_FRAGEN):
        _, frage = _AUSWEIS_FRAGEN[step]
        await message.channel.send(frage)
        return
    del _pending_ausweis[uid]
    data         = session["data"]
    einreise_typ = session["einreise_typ"]
    guild        = bot.get_guild(GUILD_ID)
    member       = guild.get_member(uid) if guild else None
    name_parts   = data["vollstaendiger_name"].strip().split(None, 1)
    vorname      = name_parts[0] if name_parts else "?"
    nachname     = name_parts[1] if len(name_parts) > 1 else "?"
    ausweisnummer = generate_ausweisnummer()
    typ_label     = "\U0001f935 Legale Einreise" if einreise_typ == "legal" else "\U0001f977 Illegale Einreise"
    ausweis_data  = load_ausweis()
    ausweis_data[str(uid)] = {
        "vorname":       vorname,
        "nachname":      nachname,
        "geburtsdatum":  data["geburtsdatum"],
        "alter":         data["alter"],
        "nationalitaet": data["nationalitaet"],
        "wohnort":       data["wohnort"],
        "einreise_typ":  einreise_typ,
        "ausweisnummer": ausweisnummer,
        "discord_name":  str(message.author),
        "discord_id":    uid,
    }
    save_ausweis(ausweis_data)
    if guild and member:
        await _assign_charakter_rollen(member, guild, einreise_typ)
    embed = discord.Embed(
        title="\U0001faaa Ausweis ausgestellt",
        description="Dein Ausweis wurde erfolgreich erstellt! \U0001f389",
        color=0x000000,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Name",              value=f"{vorname} {nachname}",  inline=True)
    embed.add_field(name="Geburtsdatum",      value=data["geburtsdatum"],     inline=True)
    embed.add_field(name="Alter",             value=data["alter"],            inline=True)
    embed.add_field(name="Nationalit\u00e4t", value=data["nationalitaet"],    inline=True)
    embed.add_field(name="Wohnort",           value=data["wohnort"],          inline=True)
    embed.add_field(name="Einreiseart",       value=typ_label,                inline=True)
    embed.add_field(name="Ausweisnummer",     value=f"`{ausweisnummer}`",     inline=False)
    if member:
        embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Paradise City Roleplay \u2014 Ausweis")
    await message.channel.send(embed=embed)



# \u2500\u2500 Admin-Modal \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class AusweisCreateModal(discord.ui.Modal, title="\U0001FAAA Ausweis erstellen (Team)"):
    vollstaendiger_name = discord.ui.TextInput(
        label="Vollst\u00E4ndiger Name (Vorname Nachname)",
        placeholder="z.B. Max Mustermann",
        max_length=100,
    )
    geburtsdatum = discord.ui.TextInput(
        label="Geburtsdatum",
        placeholder="TT.MM.JJJJ",
        max_length=10,
    )
    alter = discord.ui.TextInput(
        label="Alter",
        placeholder="z.B. 25",
        max_length=3,
    )
    nationalitaet = discord.ui.TextInput(
        label="Nationalit\u00E4t / Herkunft",
        placeholder="z.B. Deutsch",
        max_length=50,
    )
    wohnort = discord.ui.TextInput(
        label="Wohnort",
        placeholder="z.B. Los Santos",
        max_length=100,
    )

    def __init__(self, target: discord.Member, einreise_typ: str):
        super().__init__()
        self.target       = target
        self.einreise_typ = einreise_typ

    async def on_submit(self, interaction: discord.Interaction):
        import traceback as _tb, logging as _log
        try:
            admin  = interaction.user
            guild  = interaction.guild or bot.get_guild(GUILD_ID)
            member = self.target

            name_parts = self.vollstaendiger_name.value.strip().split(None, 1)
            vorname    = name_parts[0] if name_parts else "?"
            nachname   = name_parts[1] if len(name_parts) > 1 else "?"

            ausweisnummer = generate_ausweisnummer()
            typ_label     = "\U0001F935 Legale Einreise" if self.einreise_typ == "legal" else "\U0001F977 Illegale Einreise"

            ausweis_data = load_ausweis()
            ausweis_data[str(member.id)] = {
                "vorname":       vorname,
                "nachname":      nachname,
                "geburtsdatum":  self.geburtsdatum.value,
                "alter":         self.alter.value,
                "nationalitaet": self.nationalitaet.value,
                "wohnort":       self.wohnort.value,
                "einreise_typ":  self.einreise_typ,
                "ausweisnummer": ausweisnummer,
                "discord_name":  str(member),
                "discord_id":    member.id,
                "erstellt_von":  str(admin),
            }
            save_ausweis(ausweis_data)

            if guild:
                await _assign_charakter_rollen(member, guild, self.einreise_typ)

            embed = discord.Embed(
                title="\U0001FAAA Ausweis erstellt",
                color=0x000000,
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(name="Spieler",           value=member.mention,          inline=False)
            embed.add_field(name="Name",              value=f"{vorname} {nachname}", inline=True)
            embed.add_field(name="Geburtsdatum",      value=self.geburtsdatum.value, inline=True)
            embed.add_field(name="Alter",             value=self.alter.value,        inline=True)
            embed.add_field(name="Nationalit\u00E4t", value=self.nationalitaet.value, inline=True)
            embed.add_field(name="Wohnort",           value=self.wohnort.value,      inline=True)
            embed.add_field(name="Einreiseart",       value=typ_label,               inline=True)
            embed.add_field(name="Ausweisnummer",     value=f"`{ausweisnummer}`",    inline=False)
            embed.set_footer(text=f"Erstellt von {admin.display_name}")

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as _e:
            _log.error(f"[AusweisCreateModal] FEHLER: {_e}\n{_tb.format_exc()}")
            try:
                await interaction.response.send_message(
                    f"\u274C Fehler beim Erstellen: `{type(_e).__name__}: {_e}`\nBitte einen Admin informieren.",
                    ephemeral=True
                )
            except Exception:
                try:
                    await interaction.followup.send(
                        f"\u274C Fehler: `{type(_e).__name__}: {_e}`", ephemeral=True
                    )
                except Exception:
                    pass


# \u2500\u2500 Einreise Select Menu \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class EinreiseSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Legale Einreise",
                emoji="\U0001F935",
                value="legal",
                description="Einreise als legaler Bewohner"
            ),
            discord.SelectOption(
                label="Illegale Einreise",
                emoji="\U0001F977",
                value="illegal",
                description="Einreise als illegale Person"
            ),
        ]
        super().__init__(
            placeholder="\u2708\uFE0F W\u00E4hle deine Einreiseart...",
            options=options,
            custom_id="einreise_select_main"
        )

    async def callback(self, interaction: discord.Interaction):
        member   = interaction.user
        role_ids = [r.id for r in member.roles]

        if LEGAL_ROLE_ID in role_ids or ILLEGAL_ROLE_ID in role_ids:
            await interaction.response.send_message(
                "\u274C Du hast bereits eine Einreiseart gew\u00E4hlt. Eine \u00C4nderung ist nur durch den RP-Tod m\u00F6glich.",
                ephemeral=True
            )
            return

        typ      = self.values[0]
        typ_name = "Legale Einreise" if typ == "legal" else "Illegale Einreise"
        typ_emoji = "\U0001f935"     if typ == "legal" else "\U0001f977"
        uid = member.id
        _pending_ausweis[uid] = {"step": 0, "einreise_typ": typ, "data": {}}
        _, erste_frage = _AUSWEIS_FRAGEN[0]
        intro = (
            f"\U0001faaa **Ausweis erstellen \u2014 {typ_emoji} {typ_name}**\n"
            "\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
            "Beantworte bitte die folgenden Fragen. Schreibe jeweils deine Antwort als normale Nachricht.\n\n"
            + erste_frage
        )
        try:
            await member.send(intro)
            await interaction.response.send_message(
                "\u2705 Ich habe dir eine DM geschickt! \U0001f4ec\n"
                "\u27a4 Beantworte dort die Fragen um deinen Ausweis zu erstellen.",
                ephemeral=True
            )
        except discord.Forbidden:
            _pending_ausweis.pop(uid, None)
            await interaction.response.send_message(
                "\u274c Ich konnte dir keine DM senden.\n"
                "\u27a4 Bitte aktiviere **DMs von Servermitgliedern** in deinen Datenschutzeinstellungen.",
                ephemeral=True
            )


class EinreiseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EinreiseSelect())


_EINREISE_MSG_FILE = DATA_DIR / "einreise_msg.json"


def _load_einreise_msg_id() -> int | None:
    if _EINREISE_MSG_FILE.exists():
        try:
            return json.load(open(_EINREISE_MSG_FILE))["message_id"]
        except Exception:
            pass
    return None


def _save_einreise_msg_id(mid: int):
    with open(_EINREISE_MSG_FILE, "w") as f:
        json.dump({"message_id": mid}, f)


async def auto_einreise_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(EINREISE_CHANNEL_ID)
        if not channel:
            continue

        embed = discord.Embed(
            title="\u2708\uFE0F Einreise \u2014 Paradise City Roleplay",
            description=(
                "\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
                "\U0001F935\u200D\u2642\uFE0F **Legale Einreise**\n"
                "\u27A4 Du reist als **legale Person** ein. Keine illegalen Aktivit\u00E4ten erlaubt.\n\n"
                "\U0001F977 **Illegale Einreise**\n"
                "\u27A4 Du reist als **illegale Person** ein. Keine staatlichen Berufe m\u00F6glich.\n\n"
                "\u26A0\uFE0F **Hinweis:** Eine \u00C4nderung der Einreiseart ist nur durch den RP-Tod deines Charakters m\u00F6glich."
            ),
            color=0xFF6600,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_image(url="https://130f7b21-a902-4ec0-9019-6c1791f5924b-00-2d2m2xzo65o8p.sisko.replit.dev/charakter_erstellung.jpg")
        embed.set_footer(text="\u2708\uFE0F Einreise-System \u2022 Paradise City Roleplay")
        view = EinreiseView()

        mid = _load_einreise_msg_id()
        if mid:
            try:
                msg = await channel.fetch_message(mid)
                await msg.edit(embed=embed, view=view)
                print(f"[einreise] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        try:
            new_msg = await channel.send(embed=embed, view=view)
            _save_einreise_msg_id(new_msg.id)
            print(f"[einreise] Embed gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_einreise_setup fehlgeschlagen", str(e), guild)


# \u2500\u2500 /ausweisen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="ausweisen", description="[Ausweis] Zeige deinen Ausweis vor", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Ausweis eines anderen Spielers abrufen")
async def ausweisen(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids = [r.id for r in interaction.user.roles]
    is_team  = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids

    if CITIZEN_ROLE_ID not in role_ids and not is_team:
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    if interaction.channel.id != AUSWEIS_CHANNEL_ID and not is_team:
        await interaction.response.send_message(
            f"\u274C Diesen Command kannst du nur in <#{AUSWEIS_CHANNEL_ID}> benutzen.", ephemeral=True
        )
        return

    target = nutzer if (is_team and nutzer) else interaction.user

    ausweis_data = load_ausweis()
    entry = ausweis_data.get(str(target.id))

    if not entry:
        msg = (
            f"\u274C **{target.display_name}** hat noch keinen Ausweis."
            if target != interaction.user else
            "\u274C Du hast noch keinen Ausweis. W\u00E4hle zuerst deine Einreiseart und erstelle deinen Ausweis."
        )
        await interaction.response.send_message(msg, ephemeral=True)
        return

    typ_label = "\U0001F935 Legale Einreise" if entry.get("einreise_typ") == "legal" else "\U0001F977 Illegale Einreise"

    embed = discord.Embed(
        title="\U0001FAAA Personalausweis",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Name",          value=f"{entry['vorname']} {entry['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum",  value=entry["geburtsdatum"],                     inline=True)
    embed.add_field(name="Alter",         value=entry.get("alter", "?"),                   inline=True)
    embed.add_field(name="Nationalit\u00E4t",  value=entry["nationalitaet"],                   inline=True)
    embed.add_field(name="Wohnort",       value=entry["wohnort"],                          inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                 inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{entry['ausweisnummer']}`",            inline=False)
    embed.set_footer(text="Paradise City Roleplay \u2014 Personalausweis")

    await interaction.response.send_message(embed=embed, ephemeral=is_team and nutzer is not None)


# \u2500\u2500 /ausweis-remove \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="ausweis-remove", description="[Admin] L\u00F6scht den Ausweis eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler dessen Ausweis gel\u00F6scht werden soll")
async def ausweis_remove(interaction: discord.Interaction, nutzer: discord.Member):
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    uid = str(nutzer.id)

    if uid not in ausweis_data:
        await interaction.response.send_message(
            f"\u274C {nutzer.mention} hat keinen Ausweis.", ephemeral=True
        )
        return

    del ausweis_data[uid]
    save_ausweis(ausweis_data)

    embed = discord.Embed(
        title="\U0001F5D1\uFE0F Ausweis gel\u00F6scht",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Gel\u00F6scht von:** {interaction.user.mention}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 /ausweis-create \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(name="ausweis-create", description="[Ausweis] Erstellt einen Ausweis f\u00FCr einen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    nutzer="Spieler f\u00FCr den der Ausweis erstellt wird",
    einreise_typ="Einreiseart des Spielers"
)
@app_commands.choices(einreise_typ=[
    app_commands.Choice(name="Legal",   value="legal"),
    app_commands.Choice(name="Illegal", value="illegal"),
])
async def ausweis_create(interaction: discord.Interaction, nutzer: discord.Member,
                         einreise_typ: str = "legal"):
    ausweis_data = load_ausweis()
    if str(nutzer.id) in ausweis_data:
        await interaction.response.send_message(
            f"\u274C {nutzer.mention} hat bereits einen Ausweis. Bitte zuerst mit /ausweis-remove l\u00F6schen.",
            ephemeral=True
        )
        return

    await interaction.response.send_modal(
        AusweisCreateModal(target=nutzer, einreise_typ=einreise_typ)
        )
