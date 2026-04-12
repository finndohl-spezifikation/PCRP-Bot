# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# boost.py — Boost Belohnungen Embed + automatische Belohnung
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

from config import *
from economy_helpers import load_economy, save_economy, get_user

BOOST_CHANNEL_ID    = 1491622819824402583
BOOST_LOG_CHANNEL_ID = 1491622860207292576
BOOST_COLOR         = 0xB44FE8
BOOST_MSG_FILE      = DATA_DIR / "boost_msg.json"
BOOST_COUNTS_FILE   = DATA_DIR / "boost_counts.json"
BOOST_BANNER_URL    = "https://4dc1d74d-ea8e-46f4-b123-1e1a11f5dfed-00-c2y924gtit5c.worf.replit.dev/api/files/boost_banner.png"
BOOST_BETRAG        = 5_000
BOOST_AUTO_BETRAG   = 5   # Ab dieser Anzahl → Ticket für Sportwagen

# ── Datenverwaltung ───────────────────────────────────────────

def _load_boost_data() -> dict:
    if BOOST_MSG_FILE.exists():
        with open(BOOST_MSG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message_id": None}


def _save_boost_data(data: dict):
    with open(BOOST_MSG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _load_boost_counts() -> dict:
    if BOOST_COUNTS_FILE.exists():
        with open(BOOST_COUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_boost_counts(data: dict):
    with open(BOOST_COUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Belohnungs-Embed (im Boost-Info-Channel) ─────────────────

def _build_boost_embed() -> discord.Embed:
    embed = discord.Embed(
        title="💎 Boost Belohnungen",
        description=(
            "**Pro Boost 5.000 $**\n\n"
            "**Ab 5 Boosts 1 Sportwagen deiner Wahl dazu**"
        ),
        color=BOOST_COLOR,
    )
    embed.set_image(url=BOOST_BANNER_URL)
    embed.set_footer(text="Paradise City Roleplay — Server Boosts")
    return embed


async def auto_boost_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(BOOST_CHANNEL_ID)
        if not channel:
            continue

        data = _load_boost_data()

        if data.get("message_id"):
            try:
                msg = await channel.fetch_message(data["message_id"])
                await msg.edit(embed=_build_boost_embed(), attachments=[], view=discord.ui.View())
                print(f"[boost] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        try:
            new_msg = await channel.send(embed=_build_boost_embed(), view=discord.ui.View())
            data["message_id"] = new_msg.id
            _save_boost_data(data)
            print(f"[boost] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[boost] Fehler: {e}")


# ── Boost-Event: automatische Belohnung ──────────────────────

@bot.listen("on_member_update")
async def boost_reward_on_member_update(before: discord.Member, after: discord.Member):
    # Nur wenn jemand NEU boosted (premium_since: None → gesetzt)
    if before.premium_since is not None or after.premium_since is None:
        return

    guild   = after.guild
    log_ch  = guild.get_channel(BOOST_LOG_CHANNEL_ID)

    # Geld gutschreiben
    eco = load_economy()
    user_data = get_user(eco, after.id)
    user_data["cash"] = user_data.get("cash", 0) + BOOST_BETRAG
    save_economy(eco)

    # Boost-Zähler hochzählen
    counts = _load_boost_counts()
    uid    = str(after.id)
    counts[uid] = counts.get(uid, 0) + 1
    total_boosts = counts[uid]
    _save_boost_counts(counts)

    # Kanalbenachrichtigung
    if not log_ch:
        return

    beschreibung = (
        f"{after.mention} hat den Server geboostet! 🎉\n\n"
        f"💰 **+{BOOST_BETRAG:,} $** wurden deinem Konto gutgeschrieben.\n"
        f"📊 **Deine Boosts gesamt:** {total_boosts}"
    )

    if total_boosts >= BOOST_AUTO_BETRAG:
        beschreibung += (
            f"\n\n🏎️ **Du hast {total_boosts} Boosts erreicht!**\n"
            f"Öffne ein **Ticket**, um deinen Sportwagen deiner Wahl abzuholen!"
        )

    embed = discord.Embed(
        title="💜 Server Boost — Danke!",
        description=beschreibung,
        color=BOOST_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_author(
        name=after.display_name,
        icon_url=after.display_avatar.url
    )
    embed.set_image(url=BOOST_BANNER_URL)
    embed.set_footer(text="Paradise City Roleplay — Server Boosts")

    try:
        await log_ch.send(embed=embed)
    except Exception as e:
        print(f"[boost] Fehler beim Senden der Belohnungsnachricht: {e}")
