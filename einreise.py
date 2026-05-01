# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════════
# einreise.py — Einreise- & Ausweis-System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════════

import os, traceback, logging
from config import *
from helpers import log_bot_error
try:
    import ausweis_tokens as _at
except ImportError:
    _at = None

_DASHBOARD_URL_DEFAULT = "https://130f7b21-a902-4ec0-9019-6c1791f5924b-00-2d2m2xzo65o8p.sisko.replit.dev"
_raw_url = os.environ.get("DASHBOARD_URL", "").strip().rstrip("/")
_DASHBOARD_URL = _raw_url if _raw_url.startswith("http") else _DASHBOARD_URL_DEFAULT


# ── Ausweis Helpers ──────────────────────────────────────────────

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





# ── Admin-Modal ──────────────────────────────────────────────────────────────

class AusweisCreateModal(discord.ui.Modal, title="\U0001FAAA Ausweis erstellen (Team)"):
    vollstaendiger_name = discord.ui.TextInput(
        label="Vollständiger Name (Vorname Nachname)",
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
        label="Nationalität / Herkunft",
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
            embed.add_field(name="Spieler",        value=member.mention,          inline=False)
            embed.add_field(name="Name",           value=f"{vorname} {nachname}", inline=True)
            embed.add_field(name="Geburtsdatum",   value=self.geburtsdatum.value, inline=True)
            embed.add_field(name="Alter",          value=self.alter.value,        inline=True)
            embed.add_field(name="Nationalität",   value=self.nationalitaet.value, inline=True)
            embed.add_field(name="Wohnort",        value=self.wohnort.value,      inline=True)
            embed.add_field(name="Einreiseart",    value=typ_label,               inline=True)
            embed.add_field(name="Ausweisnummer",  value=f"`{ausweisnummer}`",    inline=False)
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


# ── Einreise Select Menu ─────────────────────────────────────────

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
            placeholder="\u2708\uFE0F Wähle deine Einreiseart...",
            options=options,
            custom_id="einreise_select_main"
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            member   = interaction.user
            role_ids = [r.id for r in member.roles]

            if LEGAL_ROLE_ID in role_ids or ILLEGAL_ROLE_ID in role_ids:
                await interaction.response.send_message(
                    "\u274C Du hast bereits eine Einreiseart gew\u00e4hlt. Eine \u00c4nderung ist nur durch den RP-Tod m\u00f6glich.",
                    ephemeral=True
                )
                return

            typ = self.values[0]
            ausweis_data = load_ausweis()
            if str(member.id) in ausweis_data:
                await interaction.response.send_message(
                    "\u274C Du hast bereits einen Ausweis.",
                    ephemeral=True
                )
                return

            if _at is None:
                await interaction.response.send_message(
                    "\u274C Ausweis-System nicht verfügbar. Bitte einen Admin informieren (ausweis_tokens Modul fehlt).",
                    ephemeral=True
                )
                return

            tok  = _at.create(member.id, typ)
            link = f"{_DASHBOARD_URL}/ausweis/{tok}"

            typ_label = "\U0001F935 Legale Einreise" if typ == "legal" else "\U0001F977 Illegale Einreise"

            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="\U0001FAAA Ausweis erstellen",
                style=discord.ButtonStyle.link,
                url=link,
            ))

            await interaction.response.send_message(
                f"**{typ_label}** ausgew\u00e4hlt.\n"
                "Klicke auf den Button um deinen Ausweis im Browser auszuf\u00fcllen.\n"
                "\u23F1\uFE0F Der Link ist **15 Minuten** g\u00fcltig.",
                view=view,
                ephemeral=True
            )

        except Exception as _e:
            logging.error(f"[EinreiseSelect] FEHLER: {_e}\n{traceback.format_exc()}")
            try:
                await interaction.response.send_message(
                    f"\u274C Fehler: `{type(_e).__name__}: {_e}`\nBitte einen Admin informieren.",
                    ephemeral=True
                )
            except Exception:
                try:
                    await interaction.followup.send(
                        f"\u274C Fehler: `{type(_e).__name__}: {_e}`", ephemeral=True
                    )
                except Exception:
                    pass


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
            title="\u2708\uFE0F Einreise — Paradise City Roleplay",
            description=(
                "\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
                "\U0001F935\u200D\u2642\uFE0F **Legale Einreise**\n"
                "\u27A4 Du reist als **legale Person** ein. Keine illegalen Aktivitäten erlaubt.\n\n"
                "\U0001F977 **Illegale Einreise**\n"
                "\u27A4 Du reist als **illegale Person** ein. Keine staatlichen Berufe möglich.\n\n"
                "\u26A0\uFE0F **Hinweis:** Eine Änderung der Einreiseart ist nur durch den RP-Tod deines Charakters möglich."
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


# ── /ausweisen ───────────────────────────────────────────────────

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
            "\u274C Du hast noch keinen Ausweis. Wähle zuerst deine Einreiseart und erstelle deinen Ausweis."
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
    embed.add_field(name="Nationalität",  value=entry["nationalitaet"],                    inline=True)
    embed.add_field(name="Wohnort",       value=entry["wohnort"],                          inline=True)
    embed.add_field(name="Einreiseart",   value=typ_label,                                 inline=True)
    embed.add_field(name="Ausweisnummer", value=f"`{entry['ausweisnummer']}`",             inline=False)
    embed.set_footer(text="Paradise City Roleplay — Personalausweis")

    await interaction.response.send_message(embed=embed, ephemeral=is_team and nutzer is not None)


# ── /ausweis-remove ──────────────────────────────────────────────

@bot.tree.command(name="ausweis-remove", description="[Admin] Löscht den Ausweis eines Spielers", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nutzer="Spieler dessen Ausweis gelöscht werden soll")
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
        title="\U0001F5D1\uFE0F Ausweis gelöscht",
        description=(
            f"**Spieler:** {nutzer.mention}\n"
            f"**Gelöscht von:** {interaction.user.mention}"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /ausweis-create ──────────────────────────────────────────────

@bot.tree.command(name="ausweis-create", description="[Ausweis] Erstellt einen Ausweis für einen Spieler", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    nutzer="Spieler für den der Ausweis erstellt wird",
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
            f"\u274C {nutzer.mention} hat bereits einen Ausweis. Bitte zuerst mit /ausweis-remove löschen.",
            ephemeral=True
        )
        return

    await interaction.response.send_modal(
        AusweisCreateModal(target=nutzer, einreise_typ=einreise_typ)
    )
