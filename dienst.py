# ══════════════════════════════════════════════════════════════
# dienst.py — Dienst-System (Anmelden / Abmelden) — Unified
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *

DIENST_FILE     = DATA_DIR / "dienst_data.json"
DIENST_MSG_FILE = DATA_DIR / "dienst_message_ids.json"

DIENST_CHANNEL_ID = 1492939533895860504
EMBED_COLOR       = LOG_COLOR   # Orange

# ── Fraktions-Konfiguration ──────────────────────────────────

DIENST_CONFIG = [
    {
        "faction": "lapd",
        "name":    "LAPD",
        "emoji":   "🚔",
        "role_id": LAPD_ROLE_ID,
    },
    {
        "faction": "lamd",
        "name":    "LAMD",
        "emoji":   "🚑",
        "role_id": LAMD_ROLE_ID,
    },
    {
        "faction": "lacs",
        "name":    "LACS",
        "emoji":   "🚗",
        "role_id": LACS_ROLE_ID,
    },
]

_ALL_ROLE_IDS = {c["role_id"] for c in DIENST_CONFIG}
_FACTION_BY_ROLE = {c["role_id"]: c for c in DIENST_CONFIG}


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


# ── Public Helper ────────────────────────────────────────────

def get_on_duty(faction: str) -> dict:
    return load_dienst().get(faction, {})


def count_on_duty(faction: str) -> int:
    return len(get_on_duty(faction))


# ── Embed Builder ────────────────────────────────────────────

def _build_unified_embed(guild: discord.Guild) -> discord.Embed:
    data = load_dienst()

    embed = discord.Embed(
        title="🛡️ Dienst — Übersicht",
        description="Melde dich mit den Buttons unten an oder ab.",
        color=EMBED_COLOR,
        timestamp=datetime.now(timezone.utc),
    )

    for cfg in DIENST_CONFIG:
        on_duty = data.get(cfg["faction"], {})
        if on_duty:
            lines = []
            for uid, start_iso in on_duty.items():
                member = guild.get_member(int(uid))
                name   = member.display_name if member else f"<@{uid}>"
                start  = datetime.fromisoformat(start_iso)
                lines.append(f"• **{name}** — seit <t:{int(start.timestamp())}:R>")
            value = "\n".join(lines)
        else:
            value = "*Niemand im Dienst.*"

        embed.add_field(
            name=f"{cfg['emoji']} {cfg['name']} — Im Dienst ({len(on_duty)})",
            value=value,
            inline=False,
        )

    embed.set_footer(text="Paradise City Roleplay — Dienst-System")
    return embed


# ── View / Buttons ────────────────────────────────────────────

class DienstUnifiedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def _get_faction(self, member: discord.Member) -> dict | None:
        """Gibt die passende Fraktions-Config zurück oder None."""
        for role in member.roles:
            if role.id in _FACTION_BY_ROLE:
                return _FACTION_BY_ROLE[role.id]
        return None

    @discord.ui.button(
        label="🔛| Anmelden",
        style=discord.ButtonStyle.green,
        custom_id="dienst_unified_an",
    )
    async def anmelden(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
        cfg = self._get_faction(interaction.user)
        if not cfg:
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung. Nur LAPD, LAMD und LACS können sich anmelden.",
                ephemeral=True,
            )
            return

        data         = load_dienst()
        uid          = str(interaction.user.id)
        faction_data = data.setdefault(cfg["faction"], {})

        if uid in faction_data:
            await interaction.response.send_message(
                "❌ Du bist bereits im Dienst angemeldet.", ephemeral=True
            )
            return

        start_time            = datetime.now(timezone.utc)
        faction_data[uid]     = start_time.isoformat()
        save_dienst(data)

        confirm = discord.Embed(
            title=f"{cfg['emoji']} Dienstbeginn",
            description=(
                f"{interaction.user.mention} hat den **{cfg['name']}-Dienst** angetreten.\n\n"
                f"⏰ **Dienstbeginn:** <t:{int(start_time.timestamp())}:T>\n"
                f"👮 **Einheit:** {cfg['name']}\n"
                f"📋 **Status:** Im Dienst"
            ),
            color=0x2ECC71,
            timestamp=start_time,
        )
        confirm.set_thumbnail(url=interaction.user.display_avatar.url)
        confirm.set_footer(text="Paradise City Roleplay — Dienst-System")
        await interaction.response.send_message(embed=confirm, ephemeral=True)

        await _update_unified_embed(interaction.guild)

    @discord.ui.button(
        label="📴| Abmelden",
        style=discord.ButtonStyle.red,
        custom_id="dienst_unified_ab",
    )
    async def abmelden(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
        cfg = self._get_faction(interaction.user)
        if not cfg:
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung. Nur LAPD, LAMD und LACS können sich abmelden.",
                ephemeral=True,
            )
            return

        data         = load_dienst()
        uid          = str(interaction.user.id)
        faction_data = data.get(cfg["faction"], {})

        if uid not in faction_data:
            await interaction.response.send_message(
                "❌ Du bist nicht im Dienst angemeldet.", ephemeral=True
            )
            return

        start_iso             = faction_data.pop(uid)
        data[cfg["faction"]]  = faction_data
        save_dienst(data)

        start_time = datetime.fromisoformat(start_iso)
        end_time   = datetime.now(timezone.utc)
        dauer      = end_time - start_time
        stunden    = int(dauer.total_seconds() // 3600)
        minuten    = int((dauer.total_seconds() % 3600) // 60)
        dauer_str  = f"{stunden}h {minuten}min" if stunden else f"{minuten}min"

        confirm = discord.Embed(
            title=f"{cfg['emoji']} Dienstende",
            description=(
                f"{interaction.user.mention} hat den **{cfg['name']}-Dienst** beendet.\n\n"
                f"🕐 **Dienstbeginn:** <t:{int(start_time.timestamp())}:T>\n"
                f"🕑 **Dienstende:** <t:{int(end_time.timestamp())}:T>\n"
                f"⏱️ **Dienstdauer:** {dauer_str}\n"
                f"👮 **Einheit:** {cfg['name']}\n"
                f"📋 **Status:** Abgemeldet"
            ),
            color=0xE74C3C,
            timestamp=end_time,
        )
        confirm.set_thumbnail(url=interaction.user.display_avatar.url)
        confirm.set_footer(text="Paradise City Roleplay — Dienst-System")
        await interaction.response.send_message(embed=confirm, ephemeral=True)

        await _update_unified_embed(interaction.guild)


# ── Embed aktualisieren ───────────────────────────────────────

async def _update_unified_embed(guild: discord.Guild):
    channel = guild.get_channel(DIENST_CHANNEL_ID)
    if not channel:
        return

    msg_ids = load_msg_ids()
    msg_id  = msg_ids.get("unified")
    embed   = _build_unified_embed(guild)
    view    = DienstUnifiedView()

    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.edit(embed=embed, view=view)
            return
        except discord.NotFound:
            pass

    msg = await channel.send(embed=embed, view=view)
    msg_ids["unified"] = str(msg.id)
    save_msg_ids(msg_ids)


# ── Auto-Setup beim Start ────────────────────────────────────

async def auto_dienst_setup():
    print("[dienst] Setup startet...")
    for guild in bot.guilds:
        try:
            channel = guild.get_channel(DIENST_CHANNEL_ID)
            if not channel:
                print(f"[dienst] ❌ Channel {DIENST_CHANNEL_ID} nicht gefunden!")
                continue

            msg_ids = load_msg_ids()
            msg_id  = msg_ids.get("unified")
            embed   = _build_unified_embed(guild)
            view    = DienstUnifiedView()

            if msg_id:
                try:
                    msg = await channel.fetch_message(int(msg_id))
                    await msg.edit(embed=embed, view=view)
                    print(f"[dienst] ✅ Unified Embed aktualisiert (ID {msg_id})")
                    continue
                except discord.NotFound:
                    print("[dienst] ⚠️ Embed nicht mehr vorhanden — sende neu.")
                    msg_ids.pop("unified", None)
                    save_msg_ids(msg_ids)
                except Exception as e:
                    print(f"[dienst] ⚠️ Edit-Fehler: {e}")

            msg = await channel.send(embed=embed, view=view)
            msg_ids["unified"] = str(msg.id)
            save_msg_ids(msg_ids)
            print(f"[dienst] ✅ Unified Embed gepostet in #{channel.name} (ID {msg.id})")

        except Exception as e:
            print(f"[dienst] ❌ Fehler: {e}")
