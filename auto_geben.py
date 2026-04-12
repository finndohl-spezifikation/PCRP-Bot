# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# auto_geben.py — Fahrzeug-Vergabe-System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

import json
from config import *
from economy_helpers import load_economy, save_economy, get_user

# ── Rollen ────────────────────────────────────────────────────

AUTO_GEBEN_ROLES   = {ADMIN_ROLE_ID, MOD_ROLE_ID, 1490855761822093452, 1490855760911925258}
VIP_ONLY_ROLE_ID   = 1490855760911925258          # Darf auch Supers / LKW / Flugzeug / Heli vergeben

# Kategorien die NUR VIP_ONLY_ROLE_ID vergeben darf (erkannt am Emoji-Präfix)
VIP_ONLY_PREFIXES  = {"🏎|", "🚛|", "✈️|", "🚁|"}

# ── Fahrzeugliste nach Kategorie ──────────────────────────────

# Supersportwagen — nur VIP 🏎|
SUPERSPORTWAGEN: list[str] = [
    "Adder", "Annis RE-7B", "Annis S80RR", "Bravado Banshee 900R",
    "Coil Cyclone", "Coil Cyclone II", "Declasse Scramjet",
    "Dewbauchee Vagner", "Dinka Jester RR", "Grotti Furia",
    "Grotti Itali GTO", "Grotti Itali RSX", "Grotti Turismo R",
    "Grotti Visione", "Hijak Ruston", "Imponte Deluxo",
    "Imponte Ruiner 2000", "Imponte Tempesta", "Lampadati Furore GT",
    "Nagasaki Outlaw", "Ocelot Jugular", "Ocelot Locust",
    "Ocelot R88", "Ocelot Swinger", "Ocelot Virtue",
    "Obey Zeno", "Overflod Entity MT", "Overflod Entity XF",
    "Overflod Entity XXR", "Overflod Imorgon", "Overflod Tyrant",
    "Pegassi Infernus Classic", "Pegassi Osiris", "Pegassi Reaper",
    "Pegassi Tempesta", "Pegassi Tezeract", "Pegassi Zentorno",
    "Pegassi Zorrusso", "Progen Emerus", "Progen GP1",
    "Progen Itali GTB", "Progen Itali GTB Custom", "Progen PR4",
    "Progen T20", "Progen Tyrus", "Truffade Adder",
    "Truffade Nero", "Truffade Nero Custom", "Truffade Thrax",
    "Vapid FMJ", "Vapid Flash GT", "Benefactor Krieger",
    "Dewbauchee Seven-70", "Grotti Cheetah", "Grotti Cheetah Classic",
    "Imponte Torero XO", "Pegassi Torero XO", "Ocelot Ardent",
    "Annis Euros", "Dinka RT3000",
]

# LKW / Schwerlast — nur VIP 🚛|
LKWS: list[str] = [
    "Jobuilt Hauler", "Jobuilt Hauler Custom", "Jobuilt Phantom",
    "Jobuilt Phantom Custom", "Jobuilt Phantom Wedge",
    "MTL Brickade", "MTL Cerberus", "MTL Flatbed",
    "MTL Mixer", "MTL Mixer 2", "MTL Packer",
    "MTL Pounder", "MTL Pounder Custom", "MTL Wastelander",
    "Vapid Contender", "HVY Brickade 6x6",
]

# Flugzeuge — nur VIP ✈️|
FLUGZEUGE: list[str] = [
    "Atomic Blimp", "B-11 Strikeforce", "Besra",
    "Buckingham Nimbus", "Cuban 800", "Dodo",
    "Duster", "JoBuilt P-996 LAZER", "Jobuilt Mammatus",
    "LF-22 Starling", "Luxor", "Luxor Deluxe",
    "Mammoth Avenger", "Mammoth Hydra", "Miljet",
    "Mogul", "Molotok", "P-45 Nokota", "P-996 LAZER",
    "Pyro", "RO-86 Alkonost", "Rogue", "Seabreeze",
    "Shamal", "Smuggler's Plane", "Titan", "Tula",
    "Ultralight", "V-65 Molotok", "Velum", "Velum 5-Seater",
    "Vestra", "XA-21",
]

# Helikopter — nur VIP 🚁|
HELIKOPTER: list[str] = [
    "Akula", "Annihilator", "Annihilator Stealth",
    "Buckingham Volatus", "Buzzard", "Buzzard Attack Chopper",
    "Cargobob", "Cargobob Jetsam", "FH-1 Hunter",
    "Frogger", "Frogger TPE", "Hunter", "Maverick",
    "Police Maverick", "Savage", "Sea Sparrow",
    "Sea Sparrow 2", "Skylift", "Sparrow",
    "Supervolito", "Supervolito Carbon", "Swift",
    "Swift Deluxe", "Valkyrie", "Valkyrie MOD.0", "Volatus",
]

# Normale Autos 🚗|
AUTOS: list[str] = [
    # Sportwagen
    "Annis Elegy RH8", "Annis Elegy Retro Custom", "Annis Hellion",
    "Annis ZR350", "Benefactor Feltzer", "Benefactor Schafter GT",
    "Benefactor Schafter LWB", "Benefactor Schafter V12",
    "Benefactor Stirling GT", "Benefactor Surano",
    "Bravado Banshee", "Bravado Buffalo", "Bravado Buffalo S",
    "Bravado Buffalo STX", "Bravado Gauntlet", "Bravado Gauntlet Classic",
    "Bravado Gauntlet Hellfire", "Bravado Hotring Hellfire",
    "Bravado Verlierer", "Bravado Verlierer 2",
    "Canis Mesa", "Canis Seminole Frontier", "Coquette",
    "Coquette BlackFin", "Coquette Classic", "Coil Voltic",
    "Declasse Drift Yosemite", "Declasse Mamba", "Declasse Tampa",
    "Declasse Voodoo", "Dewbauchee Exemplar", "Dewbauchee JB700",
    "Dewbauchee JB700W", "Dewbauchee Massacro", "Dewbauchee Rapid GT",
    "Dewbauchee Specter", "Dinka Blista Compact", "Dinka Jester",
    "Dinka Jester Classic", "Dinka Sugoi", "Dinka Toro",
    "Emperor Vectre", "Enus Deity", "Enus Paragon R",
    "Enus Paragon R Armored", "Enus Stafford", "Enus Windsor",
    "Enus Windsor Drop", "Grotti Brioso 300", "Grotti Carbonizzare",
    "Grotti GT500", "Grotti Stinger", "Grotti Stinger GT",
    "Grotti Turismo Classic", "Hijak Ruston", "HVY Nightshark",
    "Imponte Dukes", "Imponte Dukes O'Death", "Imponte Nightshade",
    "Imponte Phoenix", "Imponte Ruiner", "Imponte Ruiner 3",
    "Invetero Coquette", "Karin 190z", "Karin Asterope GT",
    "Karin Calico GTF", "Karin Everon", "Karin Futo", "Karin Futo GTX",
    "Karin Kuruma", "Karin Kuruma Armored", "Karin Previon",
    "Karin Sultan", "Karin Sultan Classic", "Karin Sultan RS",
    "Karin Sultan RS Classic", "Lampadati Felon", "Lampadati Felon GT",
    "Lampadati Komoda", "Lampadati Novak", "Lampadati Pigalle",
    "Lampadati Tropos Rallye", "Maibatsu Penumbra FF",
    "Maibatsu Sunrise", "Maxwell Asbo", "Maxwell Vagrant",
    "Maxwell Vargant", "Nagasaki Outlaw", "Ocelot Growler",
    "Obey 8F Drafter", "Obey I-Wagen", "Obey Omnis",
    "Obey Omnis e-GT", "Obey Rocoto", "Obey Tailgater",
    "Obey Tailgater S", "Overflod Imorgon", "Pegassi Infernus",
    "Pegassi Zorrusso", "Progen Emerus", "Rune Cheburek",
    "Schyster Deviant", "Schyster Fusilade", "Schyster Greenwood",
    "Ubermacht Cypher", "Ubermacht Niobe", "Ubermacht Oracle XS",
    "Ubermacht Rebla GTS", "Ubermacht SC1", "Ubermacht Sentinel",
    "Ubermacht Sentinel Classic", "Ubermacht Zion", "Ubermacht Zion Cabrio",
    "Vapid Caracara 4x4", "Vapid Clique", "Vapid Dominator",
    "Vapid Dominator ASP", "Vapid Dominator GTT", "Vapid Dominator GTX",
    "Vapid GB200", "Vapid Imperator", "Vapid Peyote", "Vapid Peyote Custom",
    "Vapid Peyote Gasser", "Vapid Pisswasser Dominator",
    "Vapid Retinue", "Vapid Retinue MkII", "Vapid Speedo Custom",
    "Vapid Slamvan Custom", "Weeny Dynasty", "Weeny Issi Classic",
    "Weeny Issi Sport", "Western Rampant Rocket",
    # SUV / Geländewagen
    "Albany Cavalcade", "Albany Cavalcade FXT", "Benefactor Dubsta",
    "Benefactor Dubsta 6x6", "Benefactor Serrano", "Benefactor Toros",
    "Bravado Gresley", "Canis Freecrawler", "Canis Kalahari",
    "Canis Seminole", "Canis Taos", "Declasse Granger",
    "Declasse Rancher XL", "Gallivanter Baller", "Gallivanter Baller LE",
    "Gallivanter Baller LE LWB", "Gallivanter Baller ST",
    "Gallivanter Baller ST-D", "Karin Beejay XL",
    "Mammoth Patriot", "Mammoth Patriot Mil-Spec", "Mammoth Patriot Stretch",
    "Nagasaki Blazer", "Nagasaki Blazer Aqua", "Nagasaki Blazer Hot Rod",
    "Nagasaki Blazer Lifeguard", "Obey Radius", "Vapid Guardian",
    "Vapid Riata", "Vulcar Warrener HKR",
    # Muscle Cars
    "Albany Buccaneer", "Albany Buccaneer Custom", "Albany Primo",
    "Albany Primo Custom", "Bravado Greenwood", "Declasse Moonbeam",
    "Declasse Moonbeam Custom", "Declasse Sabre Turbo",
    "Declasse Sabre Turbo Custom", "Imponte DF8-90",
    "Invetero Coquette Classic", "Vapid Blade", "Vapid Slamvan",
    "Vapid Stambler",
    # Klassiker / Oldtimer
    "Albany Roosevelt", "Albany Roosevelt Valor", "Albany Virgo",
    "Albany Virgo Classic", "Albany Virgo Classic Custom",
    "Declasse Tornado", "Declasse Tornado Custom",
    "Declasse Tornado Rat Rod", "Lampadati Michelli GT",
    # Limousinen
    "Albany Emperor", "Albany Emperor Beater", "Albany Stretch",
    "Benefactor Schafter LWB Armored", "Enus Cognoscenti",
    "Enus Cognoscenti 55", "Enus Cognoscenti 55 Armored",
    "Enus Cognoscenti Cabrio", "Enus Super Diamond", "Enus Superlite",
    # Kleinwagen
    "Bollokan Prairie", "Dinka Blista", "Grotti Brioso R/A",
    "Pfister Comet", "Pfister Comet SR", "Pfister Neon",
    "Pfister Growler", "Weeny Issi",
]

# Motorräder 🏍|
MOTORRAEDER: list[str] = [
    "Bati 801", "Bati 801RR", "Bravado BF400", "Bravado Rat Bike",
    "Carbon RS", "Daemon", "Daemon Custom", "Defiler",
    "Dinka Akuma", "Double T", "Enduro", "FCR 1000",
    "FCR 1000 Custom", "Faggio", "Faggio Mod", "Faggio Sport",
    "Gargoyle", "Hakuchou", "Hakuchou Custom", "Hakuchou Drag",
    "Hexer", "Innovation", "Lectro", "Manchez",
    "Manchez Scout", "Manchez Scout C", "Nagasaki BF400",
    "Nagasaki Carbon RS", "Nagasaki Shotaro", "Nagasaki Stryder",
    "Nemesis", "NightBlade", "Oppressor", "Oppressor MK II",
    "PCJ-600", "Rampant Rocket", "Rat Bike", "Reever",
    "Sanchez", "Sanchez Livery", "Sanctus", "Shitzu Hakuchou",
    "Shitzu Hybrid", "Shitzu PCJ-600", "Sovereign", "Stryder",
    "Thrust", "Vader", "Vortex", "Wolfsbane",
    "Western Daemon", "Western Nightmare Deathbike",
    "Western Powersurge", "Western Reever", "Western Sovereign",
    "Zombie Bobber", "Zombie Chopper",
]

# ── Autocomplete ──────────────────────────────────────────────

def _alle_fahrzeuge() -> list[tuple[str, str]]:
    result = []
    for name in AUTOS:
        result.append((f"🚗| {name}", f"🚗| {name}"))
    for name in MOTORRAEDER:
        result.append((f"🏍| {name}", f"🏍| {name}"))
    for name in SUPERSPORTWAGEN:
        result.append((f"🏎| {name}", f"🏎| {name}"))
    for name in LKWS:
        result.append((f"🚛| {name}", f"🚛| {name}"))
    for name in FLUGZEUGE:
        result.append((f"✈️| {name}", f"✈️| {name}"))
    for name in HELIKOPTER:
        result.append((f"🚁| {name}", f"🚁| {name}"))
    return result


async def fahrzeug_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    current_lower = current.lower()
    matches = [
        app_commands.Choice(name=anzeige[:100], value=wert[:100])
        for anzeige, wert in _alle_fahrzeuge()
        if current_lower in anzeige.lower()
    ]
    return matches[:25]


# ── /auto-geben ───────────────────────────────────────────────

@bot.tree.command(
    name="auto-geben",
    description="Gib einem Spieler ein Fahrzeug (Team only)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    spieler="Der Spieler der das Fahrzeug erhält",
    fahrzeug="Fahrzeugname (mit Autocomplete suchen)",
    nummernschild="Kennzeichen des Fahrzeugs (optional)"
)
@app_commands.autocomplete(fahrzeug=fahrzeug_autocomplete)
async def auto_geben(
    interaction: discord.Interaction,
    spieler: discord.Member,
    fahrzeug: str,
    nummernschild: str = None
):
    role_ids = {r.id for r in interaction.user.roles}

    # Grundlegende Berechtigungsprüfung
    if not role_ids & AUTO_GEBEN_ROLES:
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung für diesen Befehl.", ephemeral=True
        )
        return

    # Prüfen ob das Fahrzeug eine VIP-only Kategorie ist
    fahrzeug_prefix = fahrzeug.split(" ")[0] + " "  # z.B. "🏎| " oder "✈️| "
    # Korrekte Prefix-Erkennung via Split
    prefix_teil = fahrzeug.split("|")[0] + "|" if "|" in fahrzeug else ""

    if prefix_teil in VIP_ONLY_PREFIXES and VIP_ONLY_ROLE_ID not in role_ids:
        kategorie_namen = {
            "🏎|": "Supersportwagen",
            "🚛|": "LKW",
            "✈️|": "Flugzeuge",
            "🚁|": "Helikopter",
        }
        kategorie = kategorie_namen.get(prefix_teil, "dieses Fahrzeug")
        await interaction.response.send_message(
            f"❌ **{kategorie}** dürfen nur von <@&{VIP_ONLY_ROLE_ID}> vergeben werden.",
            ephemeral=True
        )
        return

    # Fahrzeug ins Inventar schreiben
    eco       = load_economy()
    user_data = get_user(eco, spieler.id)
    if "inventory" not in user_data:
        user_data["inventory"] = []

    inventar_eintrag = fahrzeug
    if nummernschild:
        inventar_eintrag += f" [{nummernschild.upper()}]"

    user_data["inventory"].append(inventar_eintrag)
    save_economy(eco)

    # Bestätigung an den Ausführenden
    embed = discord.Embed(
        title="🚘 Fahrzeug vergeben",
        description=(
            f"**Fahrzeug:** {fahrzeug}\n"
            f"**Kennzeichen:** {nummernschild.upper() if nummernschild else '*(keines)*'}\n"
            f"**Empfänger:** {spieler.mention}\n"
            f"**Vergeben von:** {interaction.user.mention}"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=spieler.display_avatar.url)
    embed.set_footer(text="Paradise City Roleplay — Fahrzeugverwaltung")
    await interaction.response.send_message(embed=embed)

    # DM an den Empfänger
    try:
        dm_embed = discord.Embed(
            title="🚘 Du hast ein Fahrzeug erhalten!",
            description=(
                f"**Fahrzeug:** {fahrzeug}\n"
                f"**Kennzeichen:** {nummernschild.upper() if nummernschild else '*(keines)*'}\n\n"
                f"Das Fahrzeug wurde deinem Inventar hinzugefügt.\n"
                f"Vergeben von: {interaction.user.mention}"
            ),
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        dm_embed.set_footer(text="Paradise City Roleplay — Fahrzeugverwaltung")
        await spieler.send(embed=dm_embed)
    except Exception:
        pass  # DMs deaktiviert — kein Fehler
