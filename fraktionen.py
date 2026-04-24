# -*- coding: utf-8 -*-
# fraktionen.py -- Fraktions-Warn, Sperre & Verwaltung
# Paradise City Roleplay Discord Bot

from config import *
import json

FRAK_WARN_CHANNEL_ID   = 1492701273571725433
FRAK_SPERRE_CHANNEL_ID = 1497050512028205186
FRAK_LIST_CHANNEL_ID   = 1492701250528084059
MAX_WARNS              = 3
FRAK_FOOTER            = "Mit freundlichen Gr\u00FC\u00DFen - Fraktionsleitung"

FRAK_FILE         = DATA_DIR / "fraktionen_data.json"
FRAK_LIST_MSG     = DATA_DIR / "frak_list_msg.json"

WARN_EMOJIS = ["\u26a0\ufe0f", "\u26a0\ufe0f\u26a0\ufe0f", "\ud83d\udea8"]


# -- Datenzugriff ----------------------------------------------

def _load() -> dict:
    if FRAK_FILE.exists():
        try:
            return json.load(open(FRAK_FILE, encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save(data: dict):
    with open(FRAK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_msg() -> dict:
    if FRAK_LIST_MSG.exists():
        try:
            return json.load(open(FRAK_LIST_MSG, encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_msg(data: dict):
    with open(FRAK_LIST_MSG, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -- Berechtigung ---------------------------------------------

def _hat_recht(interaction: discord.Interaction) -> bool:
    role_ids = {r.id for r in interaction.user.roles}
    return bool(role_ids & {INHABER_ROLE_ID, ADMIN_ROLE_ID, DASH_ROLE_ID})


# -- Frak-Liste Embed -----------------------------------------

def _build_list_embed(data: dict) -> discord.Embed:
    emb = discord.Embed(
        title="\U0001f3db\ufe0f Aktuelle Fraktionen",
        color=0x2F3136,
        timestamp=datetime.now(timezone.utc),
    )
    if not data:
        emb.description = "*Keine Fraktionen eingetragen.*"
        emb.set_footer(text=FRAK_FOOTER)
        return emb

    lines = []
    for name, entry in sorted(data.items()):
        warns = entry.get("warns", [])
        wc    = len(warns)
        if wc == 0:
            symbol = "\u2705"
        elif wc == 1:
            symbol = "\u26a0\ufe0f"
        elif wc == 2:
            symbol = "\u26a0\ufe0f\u26a0\ufe0f"
        else:
            symbol = "\ud83d\udea8"
        lines.append(f"{symbol} **{name}** \u2014 {wc}/{MAX_WARNS} Warns")

    emb.description = "\n".join(lines)
    emb.set_footer(text=FRAK_FOOTER)
    return emb


async def _update_frak_list():
    try:
        channel = await bot.fetch_channel(FRAK_LIST_CHANNEL_ID)
    except Exception:
        return
    data  = _load()
    embed = _build_list_embed(data)
    msg_data = _load_msg()
    msg_id   = msg_data.get("message_id")
    if msg_id:
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(embed=embed)
            return
        except Exception:
            pass
    sent = await channel.send(embed=embed)
    _save_msg({"message_id": sent.id})


# -- /fraktions-warn ------------------------------------------

@bot.tree.command(
    name="fraktions-warn",
    description="[Fraktionsleitung] Erteilt einer Fraktion einen offiziellen Warn",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    fraktion="Name der Fraktion",
    grund="Grund f\u00fcr den Warn",
    konsequenz="Konsequenz bei weiteren Verst\u00f6\u00dfen",
)
async def fraktions_warn(
    interaction: discord.Interaction,
    fraktion: str,
    grund: str,
    konsequenz: str,
):
    if not _hat_recht(interaction):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    data   = _load()
    entry  = data.setdefault(fraktion, {"warns": []})
    warns  = entry["warns"]

    if len(warns) >= MAX_WARNS:
        await interaction.followup.send(
            f"\u274c **{fraktion}** hat bereits {MAX_WARNS}/{MAX_WARNS} Warns erreicht.",
            ephemeral=True,
        )
        return

    warns.append({
        "grund":      grund,
        "konsequenz": konsequenz,
        "datum":      datetime.now(timezone.utc).strftime("%d.%m.%Y"),
        "issuer":     str(interaction.user),
    })
    _save(data)
    wc = len(warns)

    if wc == 1:
        warn_symbol = "\u26a0\ufe0f"
    elif wc == 2:
        warn_symbol = "\u26a0\ufe0f\u26a0\ufe0f"
    else:
        warn_symbol = "\ud83d\udea8 **LETZTER WARN**"

    emb = discord.Embed(
        title=f"\u26a0\ufe0f Fraktions-Warn \u2014 {fraktion}",
        color=0xE67E22,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(name="\U0001f3db\ufe0f Fraktion",    value=fraktion,    inline=False)
    emb.add_field(name="\U0001f4cb Grund",             value=grund,       inline=False)
    emb.add_field(name="\u2696\ufe0f Konsequenz",      value=konsequenz,  inline=False)
    emb.add_field(name="\ud83d\udcca Warn-Stand",      value=f"{warn_symbol}  ({wc}/{MAX_WARNS})", inline=False)
    emb.set_footer(text=FRAK_FOOTER)

    try:
        channel = await bot.fetch_channel(FRAK_WARN_CHANNEL_ID)
        await channel.send(embed=emb)
    except Exception as e:
        await interaction.followup.send(f"\u274c Senden fehlgeschlagen: {e}", ephemeral=True)
        return

    await _update_frak_list()
    await interaction.followup.send(
        f"\u2705 Warn f\u00fcr **{fraktion}** eingetragen ({wc}/{MAX_WARNS}).", ephemeral=True
    )


# -- /fraktions-sperre ----------------------------------------

@bot.tree.command(
    name="fraktions-sperre",
    description="[Fraktionsleitung] Sperrt eine Fraktion",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    fraktion="Name der Fraktion",
    grund="Grund f\u00fcr die Sperre",
    dauer="Dauer der Sperre (z.\u00a0B. 7 Tage / permanent)",
)
async def fraktions_sperre(
    interaction: discord.Interaction,
    fraktion: str,
    grund: str,
    dauer: str,
):
    if not _hat_recht(interaction):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    emb = discord.Embed(
        title=f"\U0001f512 Fraktions-Sperre \u2014 {fraktion}",
        color=0xE74C3C,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(name="\U0001f3db\ufe0f Fraktion", value=fraktion, inline=False)
    emb.add_field(name="\U0001f4cb Grund",          value=grund,    inline=False)
    emb.add_field(name="\u23f3 Dauer",              value=dauer,    inline=False)
    emb.set_footer(text=FRAK_FOOTER)

    try:
        channel = await bot.fetch_channel(FRAK_SPERRE_CHANNEL_ID)
        await channel.send(embed=emb)
    except Exception as e:
        await interaction.followup.send(f"\u274c Senden fehlgeschlagen: {e}", ephemeral=True)
        return

    await interaction.followup.send(
        f"\u2705 Sperre f\u00fcr **{fraktion}** gesendet.", ephemeral=True
    )


# -- /remove-frakwarn -----------------------------------------

async def _frakwarn_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    data = _load()
    choices = [
        app_commands.Choice(name=name, value=name)
        for name, entry in data.items()
        if entry.get("warns") and current.lower() in name.lower()
    ]
    return choices[:25]


@bot.tree.command(
    name="remove-frakwarn",
    description="[Fraktionsleitung] Entfernt einen Warn einer Fraktion",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(fraktion="Fraktion deren letzten Warn du entfernen m\u00f6chtest")
@app_commands.autocomplete(fraktion=_frakwarn_autocomplete)
async def remove_frakwarn(
    interaction: discord.Interaction,
    fraktion: str,
):
    if not _hat_recht(interaction):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    data  = _load()
    entry = data.get(fraktion)

    if not entry or not entry.get("warns"):
        await interaction.followup.send(
            f"\u274c **{fraktion}** hat keine Warns.", ephemeral=True
        )
        return

    removed = entry["warns"].pop()
    _save(data)
    wc = len(entry["warns"])

    emb = discord.Embed(
        title=f"\u2705 Fraktions-Warn entfernt \u2014 {fraktion}",
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(name="\U0001f3db\ufe0f Fraktion",      value=fraktion,             inline=False)
    emb.add_field(name="\U0001f5d1\ufe0f Entfernter Warn", value=removed["grund"],    inline=False)
    emb.add_field(name="\ud83d\udcca Verbleibende Warns", value=f"{wc}/{MAX_WARNS}",  inline=False)
    emb.set_footer(text=FRAK_FOOTER)

    try:
        channel = await bot.fetch_channel(FRAK_WARN_CHANNEL_ID)
        await channel.send(embed=emb)
    except Exception as e:
        await interaction.followup.send(f"\u274c Senden fehlgeschlagen: {e}", ephemeral=True)
        return

    await _update_frak_list()
    await interaction.followup.send(
        f"\u2705 Warn von **{fraktion}** entfernt. Noch {wc}/{MAX_WARNS} Warns.", ephemeral=True
    )


# -- /frak-list -----------------------------------------------

@bot.tree.command(
    name="frak-list",
    description="[Fraktionsleitung] Aktualisiert die Fraktionsliste im Kanal",
    guild=discord.Object(id=GUILD_ID),
)
async def frak_list(interaction: discord.Interaction):
    if not _hat_recht(interaction):
        await interaction.response.send_message("\u274c Keine Berechtigung.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await _update_frak_list()
    await interaction.followup.send("\u2705 Fraktionsliste aktualisiert.", ephemeral=True)
