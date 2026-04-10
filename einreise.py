# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# einreise.py — Einreise- & Ausweis-System
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from helpers import log_bot_error


# ── Ausweis Helpers ──────────────────────────────────────────

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


# ── Einreise DM Flow ─────────────────────────────────────────

async def einreise_chat_flow(channel: discord.TextChannel, member: discord.Member, guild: discord.Guild, einreise_typ: str):
    def dm_check(m):
        return m.author.id == member.id and isinstance(m.channel, discord.DMChannel)

    felder = [
        ("vorname",       "📝 **Vorname** — Bitte gib deinen Vornamen ein:"),
        ("nachname",      "📝 **Nachname** — Bitte gib deinen Nachnamen ein:"),
        ("geburtsdatum",  "📝 **Geburtsdatum** — Bitte gib dein Geburtsdatum ein (Format: TT.MM.JJJJ):"),
        ("alter",         "📝 **Alter** — Bitte gib dein Alter ein (z.B. 25):"),
        ("nationalitaet", "📝 **Nationalität** — Bitte gib deine Nationalität ein (z.B. Deutsch):"),
        ("wohnort",       "📝 **Wohnort** — Bitte gib deinen Wohnort ein (z.B. Los Santos):"),
    ]

    antworten = {}
    typ_label = "🤵 Legale Einreise" if einreise_typ == "legal" else "🥷 Illegale Einreise"

    try:
        dm = await member.create_dm()
        await dm.send(
            f"🪪 **Ausweis-Erstellung gestartet!** ({typ_label})\n"
            f"Beantworte bitte die folgenden **{len(felder)} Fragen**. "
            f"Du hast jeweils **2 Minuten** pro Antwort."
        )
    except Exception:
        await channel.send(
            f"{member.mention} ❌ Ich kann dir keine DM senden. Bitte aktiviere DMs von Servermitgliedern.",
            delete_after=15
        )
        return

    for key, frage in felder:
        await dm.send(frage)
        try:
            antwort = await bot.wait_for("message", check=dm_check, timeout=120.0)
            antworten[key] = antwort.content.strip()
        except asyncio.TimeoutError:
            await dm.send("❌ Zeit abgelaufen! Bitte wähle deine Einreiseart erneut.")
            return

    ausweisnummer = generate_ausweisnummer()

    ausweis_data = load_ausweis()
    ausweis_data[str(member.id)] = {
        "vorname":       antworten["vorname"],
        "nachname":      antworten["nachname"],
        "geburtsdatum":  antworten["geburtsdatum"],
        "alter":         antworten["alter"],
        "nationalitaet": antworten["nationalitaet"],
        "wohnort":       antworten["wohnort"],
        "einreise_typ":  einreise_typ,
        "ausweisnummer": ausweisnummer,
        "discord_name":  str(member),
        "discord_id":    member.id,
    }
    save_ausweis(ausweis_data)

    rollen_zu_vergeben = [
        guild.get_role(rid)
        for rid in CHARAKTER_ROLLEN
        if guild.get_role(rid) is not None
    ]
    if rollen_zu_vergeben:
        try:
            await member.add_roles(*rollen_zu_vergeben, reason="Charakter erstellt")
        except Exception:
            pass

    bewerber = guild.get_role(BEWERBER_ROLE_ID)
    if bewerber and bewerber in member.roles:
        try:
            await member.remove_roles(bewerber, reason="Ausweis erstellt — Bewerber-Rolle entfernt")
        except Exception:
            pass

    embed = discord.Embed(
        title="🪪 Ausweis ausgestellt",
        description="Dein Ausweis wurde erfolgreich erstellt!",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Name",         value=f"{antworten['vorname']} {antworten['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum", value=antworten["geburtsdatum"],                          inline=True)
    embed.add_field(name="Alter",        value=antworten["alter"],                                 inline=True)
    embed.add_field(name="Nationalität", value=antworten["nationalitaet"],                        inline=True)
    embed.add_field(name="Wohnort",      value=antworten["wohnort"],                              inline=True)
    embed.add_field(name="Einreiseart",  value=typ_label,                                         inline=True)
    embed.add_field(name="Ausweisnummer",value=f"`{ausweisnummer}`",                              inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Kryptik Roleplay — Ausweis")

    await dm.send("✅ **Dein Ausweis wurde erfolgreich erstellt!**", embed=embed)


# ── Einreise Select Menu ─────────────────────────────────────

class EinreiseSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Legale Einreise",
                emoji="🤵",
                value="legal",
                description="Einreise als legaler Bewohner"
            ),
            discord.SelectOption(
                label="Illegale Einreise",
                emoji="🥷",
                value="illegal",
                description="Einreise als illegale Person"
            ),
        ]
        super().__init__(
            placeholder="✈️ Wähle deine Einreiseart...",
            options=options,
            custom_id="einreise_select_main"
        )

    async def callback(self, interaction: discord.Interaction):
        member   = interaction.user
        guild    = interaction.guild
        role_ids = [r.id for r in member.roles]

        if LEGAL_ROLE_ID in role_ids or ILLEGAL_ROLE_ID in role_ids:
            await interaction.response.send_message(
                "❌ Du hast bereits eine Einreiseart gewählt. Eine Änderung ist nur durch den RP-Tod möglich.",
                ephemeral=True
            )
            return

        typ     = self.values[0]
        role_id = LEGAL_ROLE_ID if typ == "legal" else ILLEGAL_ROLE_ID
        role    = guild.get_role(role_id)

        if role:
            try:
                await member.add_roles(role, reason=f"Einreise: {typ}")
            except Exception as e:
                await log_bot_error("Einreise-Rolle vergeben fehlgeschlagen", str(e), guild)

        await interaction.response.send_message(
            f"✅ **{'Legale' if typ == 'legal' else 'Illegale'} Einreise** gewählt!\n"
            f"Die Ausweis-Erstellung startet gleich hier im Chat. Bitte beachte die Fragen.",
            ephemeral=True
        )
        asyncio.create_task(einreise_chat_flow(interaction.channel, member, guild, typ))


class EinreiseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EinreiseSelect())


async def auto_einreise_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(EINREISE_CHANNEL_ID)
        if not channel:
            continue
        already_posted = False
        try:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Einreise" in emb.title:
                            already_posted = True
                            break
                if already_posted:
                    break
        except Exception:
            pass
        if already_posted:
            print(f"Einreise-Embed bereits vorhanden in #{channel.name}")
            continue
        embed = discord.Embed(
            title="✈️ Einreise — Kryptik Roleplay",
            description=(
                "🤵‍♂️ **Legale Einreise** 🤵‍♂️\n"
                "Du wirst auf unserem Server als Legale Person einreisen. "
                "Du darfst als Legaler Bewohner keine Illegalen Aktivitäten ausführen.\n\n"
                "🥷 **Illegale Einreise** 🥷\n"
                "Du wirst auf unserem Server als Illegale Person einreisen. "
                "Du darfst keine Staatlichen Berufe ausüben.\n\n"
                "⚠️ **Hinweis** ⚠️\n"
                "Eine Änderung der Einreiseart ist nur durch den RP-Tod deines Charakters möglich."
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Kryptik Roleplay — Einreisesystem")
        try:
            await channel.send(embed=embed, view=EinreiseView())
            print(f"Einreise-Embed automatisch gepostet in #{channel.name}")
        except Exception as e:
            await log_bot_error("auto_einreise_setup fehlgeschlagen", str(e), guild)


# /ausweisen
@bot.tree.command(name="ausweisen", description="[Ausweis] Zeige deinen Ausweis vor", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="(Nur Team) Ausweis eines anderen Spielers abrufen")
async def ausweisen(interaction: discord.Interaction, nutzer: discord.Member = None):
    role_ids = [r.id for r in interaction.user.roles]
    is_team  = ADMIN_ROLE_ID in role_ids or MOD_ROLE_ID in role_ids

    if CITIZEN_ROLE_ID not in role_ids and not is_team:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    if interaction.channel.id != AUSWEIS_CHANNEL_ID and not is_team:
        await interaction.response.send_message(
            f"❌ Diesen Command kannst du nur in <#{AUSWEIS_CHANNEL_ID}> benutzen.", ephemeral=True
        )
        return

    target = nutzer if (is_team and nutzer) else interaction.user

    ausweis_data = load_ausweis()
    entry = ausweis_data.get(str(target.id))

    if not entry:
        msg = (
            f"❌ **{target.display_name}** hat noch keinen Ausweis."
            if target != interaction.user else
            "❌ Du hast noch keinen Ausweis. Wähle zuerst deine Einreiseart und erstelle deinen Ausweis."
        )
        await interaction.response.send_message(msg, ephemeral=True)
        return

    typ_label = "🤵 Legale Einreise" if entry.get("einreise_typ") == "legal" else "🥷 Illegale Einreise"

    embed = discord.Embed(
        title="🪪 Personalausweis",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Name",          value=f"{entry['vorname']} {entry['nachname']}", inline=True)
    embed.add_field(name="Geburtsdatum",  value=entry["geburtsdatum"],                     inline=True)
    embed.add_field(name="Alter",         value=entry.get("alter", "?"),                   inline=True)
    embed.add_field(name="Nationalität",  value=entry["nationalitaet"],                   inline=True)
    embed.add_field(name="Wohnort",       value=entry["wohnort"],                          inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                 inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{entry['ausweisnummer']}`",            inline=False)
    embed.set_footer(text="Kryptik Roleplay — Personalausweis")

    await interaction.response.send_message(embed=embed, ephemeral=is_team and nutzer is not None)


# /ausweis-remove (Admin only)
@bot.tree.command(name="ausweis-remove", description="[Admin] Löscht den Ausweis eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
@app_commands.describe(nutzer="Spieler dessen Ausweis geloescht werden soll")
async def ausweis_remove(interaction: discord.Interaction, nutzer: discord.Member):
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    uid = str(nutzer.id)

    if uid not in ausweis_data:
        await interaction.response.send_message(
            f"❌ {nutzer.mention} hat keinen Ausweis.", ephemeral=True
        )
        return

    del ausweis_data[uid]
    save_ausweis(ausweis_data)

    embed = discord.Embed(
        title="🗑️ Ausweis gelöscht",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Gelöscht von:** {interaction.user.mention}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Admin Ausweis-Erstellen (DM-basiert) ─────────────────────

async def ausweis_create_dm_flow(admin: discord.Member, guild: discord.Guild, target: discord.Member, original_channel: discord.TextChannel):
    def dm_check(m):
        return m.author.id == admin.id and isinstance(m.channel, discord.DMChannel)

    felder = [
        ("vorname",      "📝 **Vorname** des Spielers:"),
        ("nachname",     "📝 **Nachname** des Spielers:"),
        ("geburtsdatum", "📝 **Geburtsdatum** (Format: TT.MM.JJJJ):"),
        ("alter",        "📝 **Alter** (z.B. 25):"),
        ("herkunft",     "📝 **Herkunft** (z.B. Deutsch):"),
        ("wohnort",      "📝 **Wohnort** (z.B. Los Santos):"),
        ("einreise_typ", "📝 **Einreiseart** — Tippe `legal` oder `illegal`:"),
    ]

    antworten = {}

    try:
        dm = await admin.create_dm()
        await dm.send(
            f"🪪 **Ausweis-Erstellung für {target.display_name} gestartet!**\n"
            f"Beantworte bitte die folgenden **{len(felder)} Fragen**. "
            f"Du hast jeweils **2 Minuten** pro Antwort."
        )
    except Exception:
        await original_channel.send(
            f"{admin.mention} ❌ Ich kann dir keine DM senden. Bitte aktiviere DMs von Servermitgliedern.",
            delete_after=15
        )
        return

    for key, frage in felder:
        await dm.send(frage)
        try:
            antwort = await bot.wait_for("message", check=dm_check, timeout=120.0)
            wert = antwort.content.strip()

            if key == "einreise_typ":
                if wert.lower() not in ("legal", "illegal"):
                    await dm.send("❌ Ungültige Eingabe. Bitte starte den Command erneut und tippe `legal` oder `illegal`.")
                    return
                wert = wert.lower()

            antworten[key] = wert
        except asyncio.TimeoutError:
            await dm.send("❌ Zeit abgelaufen! Bitte starte `/ausweis-create` erneut.")
            return

    ausweisnummer = generate_ausweisnummer()
    typ_label     = "🤵 Legale Einreise" if antworten["einreise_typ"] == "legal" else "🥷 Illegale Einreise"

    ausweis_data = load_ausweis()
    ausweis_data[str(target.id)] = {
        "vorname":       antworten["vorname"],
        "nachname":      antworten["nachname"],
        "geburtsdatum":  antworten["geburtsdatum"],
        "alter":         antworten["alter"],
        "nationalitaet": antworten["herkunft"],
        "wohnort":       antworten["wohnort"],
        "einreise_typ":  antworten["einreise_typ"],
        "ausweisnummer": ausweisnummer,
        "erstellt_von":  str(admin),
    }
    save_ausweis(ausweis_data)

    rollen_zu_vergeben = [
        guild.get_role(rid)
        for rid in CHARAKTER_ROLLEN
        if guild.get_role(rid) is not None
    ]
    if rollen_zu_vergeben:
        try:
            await target.add_roles(*rollen_zu_vergeben, reason="Charakter erstellt (Team)")
        except Exception:
            pass

    bewerber = guild.get_role(BEWERBER_ROLE_ID)
    if bewerber and bewerber in target.roles:
        try:
            await target.remove_roles(bewerber, reason="Ausweis erstellt — Bewerber-Rolle entfernt")
        except Exception:
            pass

    embed = discord.Embed(
        title="🪪 Ausweis erstellt",
        color=0x000000,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Spieler",      value=target.mention,                                        inline=False)
    embed.add_field(name="Name",         value=f"{antworten['vorname']} {antworten['nachname']}",     inline=True)
    embed.add_field(name="Geburtsdatum", value=antworten["geburtsdatum"],                             inline=True)
    embed.add_field(name="Alter",        value=antworten["alter"],                                    inline=True)
    embed.add_field(name="Herkunft",     value=antworten["herkunft"],                                 inline=True)
    embed.add_field(name="Wohnort",      value=antworten["wohnort"],                                  inline=True)
    embed.add_field(name="Einreiseart",  value=typ_label,                                             inline=True)
    embed.add_field(name="Ausweisnummer",value=f"`{ausweisnummer}`",                                 inline=False)
    embed.set_footer(text=f"Erstellt von {admin.display_name}")

    await dm.send("✅ **Ausweis erfolgreich erstellt!**", embed=embed)


# /ausweis-create (Team only)
@bot.tree.command(name="ausweis-create", description="[Ausweis] Erstellt einen Ausweis für einen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(nutzer="Spieler fuer den der Ausweis erstellt wird")
async def ausweis_create(interaction: discord.Interaction, nutzer: discord.Member):
    if not any(r.id in (ADMIN_ROLE_ID, MOD_ROLE_ID) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)
        return

    ausweis_data = load_ausweis()
    if str(nutzer.id) in ausweis_data:
        await interaction.response.send_message(
            f"❌ {nutzer.mention} hat bereits einen Ausweis. Bitte zuerst mit /ausweis-remove löschen.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"✅ Ausweis-Erstellung für **{nutzer.display_name}** gestartet!\n"
        f"Ich schicke dir die Fragen per **DM** — nur du siehst sie.",
        ephemeral=True
    )
    asyncio.create_task(ausweis_create_dm_flow(interaction.user, interaction.guild, nutzer, interaction.channel))
