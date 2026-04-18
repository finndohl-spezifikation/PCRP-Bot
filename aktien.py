# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# aktien.py \u2014 Aktienmarkt-System
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

from __future__ import annotations
import asyncio
import json
import random
from datetime import datetime, timezone

from config import *
from economy_helpers import load_economy, save_economy, get_user

AKTIEN_FILE             = DATA_DIR / "aktien.json"
AKTIEN_UPDATE_INTERVAL  = 3600        # Kurs-Update einmal st\u00FCndlich
AKTIEN_MIN_PREIS        = 100         # Minimum-Kurs in $
AKTIEN_VERLAUF_MAX      = 20          # Wie viele Kurswerte gespeichert werden

# \u2500\u2500 Aktien-Definitionen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
AKTIEN: dict[str, dict] = {
    "maze_bank": {
        "name":        "Maze Bank",
        "emoji":       "\U0001F3E6",
        "channel_id":  1493359040045125844,
        "start_preis": 1000,
    },
    "benefactor": {
        "name":        "Benefactor",
        "emoji":       "\U0001F697",
        "channel_id":  1493359230118527078,
        "start_preis": 800,
    },
    "goldwand": {
        "name":        "Goldwand",
        "emoji":       "\U0001F4B0",
        "channel_id":  1493360407224516648,
        "start_preis": 500,
    },
    "the_diamond": {
        "name":        "The Diamond",
        "emoji":       "\U0001F48E",
        "channel_id":  1493360555401154700,
        "start_preis": 1200,
    },
}

AKTIE_CHOICES = [
    app_commands.Choice(name=f"{v['emoji']} {v['name']}", value=k)
    for k, v in AKTIEN.items()
]


# \u2500\u2500 Datei-Handling \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _load_aktien() -> dict:
    if AKTIEN_FILE.exists():
        with open(AKTIEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    data = {}
    for key, info in AKTIEN.items():
        data[key] = {
            "preis":            float(info["start_preis"]),
            "verlauf":          [float(info["start_preis"])],
            "embed_message_id": None,
            "letzte_news":      None,
        }
    _save_aktien(data)
    return data


def _save_aktien(data: dict):
    with open(AKTIEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# \u2500\u2500 Kurs-Embed bauen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _sparkline(preise: list[float]) -> str:
    blocks = "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
    if len(preise) < 2:
        return blocks[3] * len(preise)
    mn, mx = min(preise), max(preise)
    if mn == mx:
        return blocks[3] * len(preise)
    return "".join(blocks[int((p - mn) / (mx - mn) * 7)] for p in preise)


def _fmt(betrag: float) -> str:
    return f"{int(betrag):,}".replace(",", ".") + " $"


def _build_kurs_embed(key: str, aktien_data: dict) -> discord.Embed:
    info    = AKTIEN[key]
    eintrag = aktien_data[key]
    preis   = eintrag["preis"]
    verlauf = eintrag["verlauf"]

    if len(verlauf) >= 2:
        change_abs = preis - verlauf[-2]
        change_pct = (change_abs / verlauf[-2]) * 100
        if change_pct > 0:
            trend_sym   = "\u25B2"
            trend_color = 0x2ECC71
        elif change_pct < 0:
            trend_sym   = "\u25BC"
            trend_color = 0xE74C3C
        else:
            trend_sym   = "\u2192"
            trend_color = 0x95A5A6
        change_line = f"{trend_sym} {change_pct:+.1f}%   ({'+' if change_abs >= 0 else ''}{_fmt(change_abs)})"
    else:
        trend_color = LOG_COLOR
        change_line = "\u2014"

    spark = _sparkline(verlauf[-15:])

    embed = discord.Embed(
        title=f"{info['emoji']} {info['name']}",
        description=(
            f"## {_fmt(preis)}\n"
            f"{change_line}\n\n"
            f"`{spark}`\n\n"
            f"\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557\n"
            f"  `/aktie-kaufen {key}`\n"
            f"  `/aktie-verkaufen {key}`\n"
            f"  `/depot`\n"
            f"\u255A\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255D"
        ),
        color=trend_color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Aktienmarkt \u2022 Kurs wird st\u00FCndlich aktualisiert")
    return embed


# \u2500\u2500 Channel-Embed senden / aktualisieren \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _update_channel_embed(key: str, aktien_data: dict):
    info    = AKTIEN[key]
    eintrag = aktien_data[key]
    channel = bot.get_channel(info["channel_id"])
    if not channel:
        return

    embed = _build_kurs_embed(key, aktien_data)
    mid   = eintrag.get("embed_message_id")

    if mid:
        try:
            msg = await channel.fetch_message(mid)
            await msg.edit(embed=embed)
            return
        except Exception:
            pass

    # Neu senden und ID speichern
    try:
        # Kanal leeren (alte Nachrichten)
        await channel.purge(limit=10)
        new_msg = await channel.send(embed=embed)
        aktien_data[key]["embed_message_id"] = new_msg.id
    except Exception:
        pass


# \u2500\u2500 Preis-Update \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _update_all_prices():
    """Aktualisiert alle Kurse automatisch (st\u00FCndlich)."""
    aktien_data = _load_aktien()

    for key in AKTIEN:
        eintrag = aktien_data[key]
        change  = random.choices([-200, -100, 100, 200], weights=[1, 2, 2, 1])[0]
        neuer_preis = max(AKTIEN_MIN_PREIS, int(eintrag["preis"]) + change)
        eintrag["preis"] = float(neuer_preis)
        eintrag["verlauf"].append(float(neuer_preis))
        if len(eintrag["verlauf"]) > AKTIEN_VERLAUF_MAX:
            eintrag["verlauf"] = eintrag["verlauf"][-AKTIEN_VERLAUF_MAX:]

    _save_aktien(aktien_data)

    for key in AKTIEN:
        await _update_channel_embed(key, aktien_data)


# \u2500\u2500 Setup & Loop \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def aktien_channel_setup():
    """Einmalig beim Start: Embeds in Kan\u00E4le senden."""
    aktien_data = _load_aktien()
    for key in AKTIEN:
        await _update_channel_embed(key, aktien_data)
    _save_aktien(aktien_data)
    print("[aktien] Kan\u00E4le eingerichtet.")


async def aktien_update_loop():
    await bot.wait_until_ready()
    await aktien_channel_setup()
    while not bot.is_closed():
        await asyncio.sleep(AKTIEN_UPDATE_INTERVAL)
        await _update_all_prices()
        print(f"[aktien] Kurse aktualisiert um {datetime.now().strftime('%H:%M')}")


async def aktien_setup():
    """Von on_ready oder setup_all_embeds aufrufen."""
    bot.loop.create_task(aktien_update_loop())


# \u2500\u2500 /aktie-kaufen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="aktie-kaufen",
    description="Kaufe Aktien am Aktienmarkt",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(aktie="Welche Aktie kaufen?", anzahl="Wie viele St\u00FCck?")
@app_commands.choices(aktie=AKTIE_CHOICES)
async def aktie_kaufen(interaction: discord.Interaction, aktie: str, anzahl: int):
    if anzahl <= 0:
        await interaction.response.send_message("\u274C Anzahl muss mindestens 1 sein.", ephemeral=True)
        return

    aktien_data = _load_aktien()
    if aktie not in aktien_data:
        await interaction.response.send_message("\u274C Unbekannte Aktie.", ephemeral=True)
        return

    preis_pro_stueck = aktien_data[aktie]["preis"]
    gesamtpreis      = preis_pro_stueck * anzahl

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    kontostand = user_data.get("bank", 0)

    if kontostand < gesamtpreis:
        await interaction.response.send_message(
            f"\u274C Nicht genug Geld!\n"
            f"**Ben\u00F6tigt:** {_fmt(gesamtpreis)}\n"
            f"**Kontostand:** {_fmt(kontostand)}",
            ephemeral=True,
        )
        return

    user_data["bank"] = kontostand - gesamtpreis

    depot = user_data.setdefault("aktien", {})
    if aktie in depot:
        # Durchschnittlichen Einstandspreis berechnen
        alt_anzahl  = depot[aktie]["anzahl"]
        alt_preis   = depot[aktie]["einstand"]
        neu_anzahl  = alt_anzahl + anzahl
        depot[aktie]["einstand"] = ((alt_preis * alt_anzahl) + (preis_pro_stueck * anzahl)) / neu_anzahl
        depot[aktie]["anzahl"]   = neu_anzahl
    else:
        depot[aktie] = {"anzahl": anzahl, "einstand": preis_pro_stueck}

    save_economy(eco)

    info = AKTIEN[aktie]
    embed = discord.Embed(
        title="\u2705 Aktien gekauft",
        description=(
            f"**{info['emoji']} {info['name']}** \u2014 {anzahl}x St\u00FCck\n\n"
            f"**Kurs:** {_fmt(preis_pro_stueck)} / St\u00FCck\n"
            f"**Gesamt:** {_fmt(gesamtpreis)}\n"
            f"**Neuer Kontostand:** {_fmt(user_data['bank'])}"
        ),
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Aktienmarkt")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 /aktie-verkaufen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="aktie-verkaufen",
    description="Verkaufe Aktien aus deinem Depot",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(aktie="Welche Aktie verkaufen?", anzahl="Wie viele St\u00FCck?")
@app_commands.choices(aktie=AKTIE_CHOICES)
async def aktie_verkaufen(interaction: discord.Interaction, aktie: str, anzahl: int):
    if anzahl <= 0:
        await interaction.response.send_message("\u274C Anzahl muss mindestens 1 sein.", ephemeral=True)
        return

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    depot     = user_data.get("aktien", {})

    if aktie not in depot or depot[aktie]["anzahl"] < anzahl:
        im_besitz = depot.get(aktie, {}).get("anzahl", 0)
        info = AKTIEN.get(aktie, {})
        await interaction.response.send_message(
            f"\u274C Nicht genug Aktien im Depot!\n"
            f"**{info.get('emoji', '')} {info.get('name', aktie)}:** {im_besitz}x im Besitz",
            ephemeral=True,
        )
        return

    aktien_data      = _load_aktien()
    preis_pro_stueck = aktien_data[aktie]["preis"]
    gesamterloes     = preis_pro_stueck * anzahl

    einstand     = depot[aktie]["einstand"]
    gewinn_verlust = (preis_pro_stueck - einstand) * anzahl
    gv_str       = f"{'\u25B2' if gewinn_verlust >= 0 else '\u25BC'} {_fmt(abs(gewinn_verlust))}"

    depot[aktie]["anzahl"] -= anzahl
    if depot[aktie]["anzahl"] == 0:
        del depot[aktie]

    user_data["bank"] = user_data.get("bank", 0) + gesamterloes
    save_economy(eco)

    info = AKTIEN[aktie]
    embed = discord.Embed(
        title="\u2705 Aktien verkauft",
        description=(
            f"**{info['emoji']} {info['name']}** \u2014 {anzahl}x St\u00FCck\n\n"
            f"**Kurs:** {_fmt(preis_pro_stueck)} / St\u00FCck\n"
            f"**Erl\u00F6s:** {_fmt(gesamterloes)}\n"
            f"**Gewinn/Verlust:** {gv_str}\n"
            f"**Neuer Kontostand:** {_fmt(user_data['bank'])}"
        ),
        color=0x2ECC71 if gewinn_verlust >= 0 else 0xE74C3C,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Aktienmarkt")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# \u2500\u2500 /depot \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="depot",
    description="Zeige dein Aktien-Depot",
    guild=discord.Object(id=GUILD_ID),
)
async def depot(interaction: discord.Interaction):
    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)
    depot_d   = user_data.get("aktien", {})

    if not depot_d:
        await interaction.response.send_message(
            "\U0001F4ED Du besitzt noch keine Aktien.\nKaufe welche mit `/aktie-kaufen`!",
            ephemeral=True,
        )
        return

    aktien_data  = _load_aktien()
    gesamt_wert  = 0.0
    gesamt_kosten = 0.0
    zeilen       = []

    for key, pos in depot_d.items():
        info     = AKTIEN.get(key, {"emoji": "\U0001F4C8", "name": key})
        kurs     = aktien_data.get(key, {}).get("preis", 0)
        wert     = kurs * pos["anzahl"]
        kosten   = pos["einstand"] * pos["anzahl"]
        gv       = wert - kosten
        gv_sym   = "\u25B2" if gv >= 0 else "\u25BC"
        gesamt_wert  += wert
        gesamt_kosten += kosten
        zeilen.append(
            f"{info['emoji']} **{info['name']}** \u2014 {pos['anzahl']}x\n"
            f"\u2523 Kurs: {_fmt(kurs)}  |  Wert: {_fmt(wert)}\n"
            f"\u2517 Einstand: {_fmt(pos['einstand'])}  |  G/V: {gv_sym} {_fmt(abs(gv))}"
        )

    gesamt_gv     = gesamt_wert - gesamt_kosten
    gesamt_gv_sym = "\u25B2" if gesamt_gv >= 0 else "\u25BC"

    embed = discord.Embed(
        title=f"\U0001F4C2 Depot \u2014 {interaction.user.display_name}",
        description="\n\n".join(zeilen),
        color=0x2ECC71 if gesamt_gv >= 0 else 0xE74C3C,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="\U0001F4BC Gesamtwert",      value=_fmt(gesamt_wert),                      inline=True)
    embed.add_field(name="\U0001F4CA Gesamt G/V",      value=f"{gesamt_gv_sym} {_fmt(abs(gesamt_gv))}", inline=True)
    embed.add_field(name="\U0001F4B5 Kontostand",       value=_fmt(user_data.get("bank", 0)),          inline=True)
    embed.set_footer(text="Paradise City Roleplay \u2022 Aktienmarkt")
    await interaction.response.send_message(embed=embed, ephemeral=True)
