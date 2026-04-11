# ══════════════════════════════════════════════════════════════
# dienst.py — Dienst-System (Anmelden / Abmelden)
# Kryptik / Cryptik Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *

DIENST_FILE    = DATA_DIR / "dienst_data.json"
DIENST_MSG_FILE = DATA_DIR / "dienst_message_ids.json"

EMBED_COLOR = 0x00BFFF  # Hellblau

# ── Fraktions-Konfiguration ──────────────────────────────────
DIENST_CONFIG = [
    {
        "faction":    "lapd",
        "name":       "LAPD",
        "emoji":      "🚔",
        "channel_id": 1490890327450587288,
        "role_id":    LAPD_ROLE_ID,
    },
    {
        "faction":    "lamd",
        "name":       "LAMD",
        "emoji":      "🚑",
        "channel_id": 1490890329027641475,
        "role_id":    LAMD_ROLE_ID,
    },
    {
        "faction":    "lacs",
        "name":       "LACS",
        "emoji":      "🚗",
        "channel_id": 1490890329979879506,
        "role_id":    LACS_ROLE_ID,
    },
]

_FACTION_BY_CHANNEL = {c["channel_id"]: c for c in DIENST_CONFIG}
_FACTION_BY_KEY     = {c["faction"]:    c for c in DIENST_CONFIG}


# ── JSON Helpers ─────────────────────────────────────────────

def load_dienst() -> dict:
    if DIENST_FILE.exists():
        with open(DIENST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {c["faction"]: {} for c in DIENST_CONFIG}


def save_dienst(data: dict):
    with open(DIENST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_msg_ids() -> dict:
    if DIENST_MSG_FILE.exists():
        with open(DIENST_MSG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_msg_ids(data: dict):
    with open(DIENST_MSG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Public Helper: wer ist im Dienst? ───────────────────────

def get_on_duty(faction: str) -> dict:
    """Gibt {user_id_str: start_time_iso} für eine Fraktion zurück."""
    return load_dienst().get(faction, {})


def count_on_duty(faction: str) -> int:
    return len(get_on_duty(faction))


# ── Embed Builder ────────────────────────────────────────────

def _build_dienst_embed(guild: discord.Guild, cfg: dict) -> discord.Embed:
    data    = load_dienst()
    on_duty = data.get(cfg["faction"], {})

    embed = discord.Embed(
        title=f"{cfg['emoji']} {cfg['name']} — Dienst",
        color=EMBED_COLOR,
        timestamp=datetime.now(timezone.utc),
    )

    if on_duty:
        lines = []
        for uid, start_iso in on_duty.items():
            member = guild.get_member(int(uid))
            name   = member.display_name if member else f"<@{uid}>"
            start  = datetime.fromisoformat(start_iso)
            lines.append(
                f"• **{name}** — seit <t:{int(start.timestamp())}:R>"
            )
        embed.add_field(
            name=f"✅ Im Dienst ({len(on_duty)})",
            value="\n".join(lines),
            inline=False,
        )
    else:
        embed.add_field(
            name="✅ Im Dienst (0)",
            value="*Niemand ist aktuell im Dienst.*",
            inline=False,
        )

    embed.set_footer(text="Cryptik Roleplay — Dienst-System")
    return embed


# ── Buttons ──────────────────────────────────────────────────

class AnmeldenButton(discord.ui.Button):
    def __init__(self, faction: str, cfg: dict):
        super().__init__(
            label="✅️| Anmelden",
            style=discord.ButtonStyle.green,
            custom_id=f"dienst_an:{faction}",
        )
        self.faction = faction
        self.cfg     = cfg

    async def callback(self, interaction: discord.Interaction):
        if not any(r.id == self.cfg["role_id"] for r in interaction.user.roles):
            await interaction.response.send_message(
                f"❌ Nur {self.cfg['name']}-Mitglieder können sich hier anmelden.",
                ephemeral=True,
            )
            return

        data = load_dienst()
        uid  = str(interaction.user.id)
        faction_data = data.setdefault(self.faction, {})

        if uid in faction_data:
            await interaction.response.send_message(
                "❌ Du bist bereits im Dienst angemeldet.", ephemeral=True
            )
            return

        start_time = datetime.now(timezone.utc)
        faction_data[uid] = start_time.isoformat()
        save_dienst(data)

        embed = discord.Embed(
            title=f"{self.cfg['emoji']} Dienstbeginn",
            description=(
                f"{interaction.user.mention} hat den **{self.cfg['name']}-Dienst** angetreten.\n\n"
                f"⏰ **Dienstbeginn:** <t:{int(start_time.timestamp())}:T>\n"
                f"👮 **Einheit:** {self.cfg['name']}\n"
                f"📋 **Status:** Im Dienst"
            ),
            color=0x2ECC71,
            timestamp=start_time,
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Cryptik Roleplay — Dienst-System")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        await _update_dienst_embed(interaction.guild, self.cfg)


class AbmeldenButton(discord.ui.Button):
    def __init__(self, faction: str, cfg: dict):
        super().__init__(
            label="❌️| Abmelden",
            style=discord.ButtonStyle.red,
            custom_id=f"dienst_ab:{faction}",
        )
        self.faction = faction
        self.cfg     = cfg

    async def callback(self, interaction: discord.Interaction):
        if not any(r.id == self.cfg["role_id"] for r in interaction.user.roles):
            await interaction.response.send_message(
                f"❌ Nur {self.cfg['name']}-Mitglieder können sich hier abmelden.",
                ephemeral=True,
            )
            return

        data = load_dienst()
        uid  = str(interaction.user.id)
        faction_data = data.get(self.faction, {})

        if uid not in faction_data:
            await interaction.response.send_message(
                "❌ Du bist nicht im Dienst angemeldet.", ephemeral=True
            )
            return

        start_iso  = faction_data.pop(uid)
        data[self.faction] = faction_data
        save_dienst(data)

        start_time = datetime.fromisoformat(start_iso)
        end_time   = datetime.now(timezone.utc)
        dauer      = end_time - start_time

        stunden  = int(dauer.total_seconds() // 3600)
        minuten  = int((dauer.total_seconds() % 3600) // 60)
        dauer_str = f"{stunden}h {minuten}min" if stunden else f"{minuten}min"

        embed = discord.Embed(
            title=f"{self.cfg['emoji']} Dienstende",
            description=(
                f"{interaction.user.mention} hat den **{self.cfg['name']}-Dienst** beendet.\n\n"
                f"🕐 **Dienstbeginn:** <t:{int(start_time.timestamp())}:T>\n"
                f"🕑 **Dienstende:** <t:{int(end_time.timestamp())}:T>\n"
                f"⏱️ **Dienstdauer:** {dauer_str}\n"
                f"👮 **Einheit:** {self.cfg['name']}\n"
                f"📋 **Status:** Abgemeldet"
            ),
            color=0xE74C3C,
            timestamp=end_time,
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Cryptik Roleplay — Dienst-System")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        await _update_dienst_embed(interaction.guild, self.cfg)


class DienstView(discord.ui.View):
    def __init__(self, faction: str, cfg: dict):
        super().__init__(timeout=None)
        self.add_item(AnmeldenButton(faction, cfg))
        self.add_item(AbmeldenButton(faction, cfg))


# ── Embed im Channel aktualisieren ──────────────────────────

async def _update_dienst_embed(guild: discord.Guild, cfg: dict):
    channel = guild.get_channel(cfg["channel_id"])
    if not channel:
        return

    msg_ids = load_msg_ids()
    msg_id  = msg_ids.get(cfg["faction"])

    embed = _build_dienst_embed(guild, cfg)
    view  = DienstView(cfg["faction"], cfg)

    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.edit(embed=embed, view=view)
            return
        except discord.NotFound:
            pass

    msg = await channel.send(embed=embed, view=view)
    msg_ids[cfg["faction"]] = str(msg.id)
    save_msg_ids(msg_ids)


# ── Auto-Setup beim Start ────────────────────────────────────

async def auto_dienst_setup():
    for guild in bot.guilds:
        for cfg in DIENST_CONFIG:
            channel = guild.get_channel(cfg["channel_id"])
            if not channel:
                continue

            msg_ids = load_msg_ids()
            msg_id  = msg_ids.get(cfg["faction"])

            # Schon vorhanden → nur View neu registrieren + Embed aktualisieren
            if msg_id:
                try:
                    msg = await channel.fetch_message(int(msg_id))
                    embed = _build_dienst_embed(guild, cfg)
                    view  = DienstView(cfg["faction"], cfg)
                    await msg.edit(embed=embed, view=view)
                    print(f"[dienst] {cfg['name']} Embed aktualisiert (ID {msg_id})")
                    continue
                except discord.NotFound:
                    pass

            embed = _build_dienst_embed(guild, cfg)
            view  = DienstView(cfg["faction"], cfg)
            msg   = await channel.send(embed=embed, view=view)
            msg_ids[cfg["faction"]] = str(msg.id)
            save_msg_ids(msg_ids)
            print(f"[dienst] {cfg['name']} Embed gepostet (ID {msg.id})")
