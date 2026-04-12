# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# auto_geben.py — Fahrzeug-Vergabe-System
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════

import json
from config import *
from economy_helpers import load_economy, save_economy, get_user

# ── Berechtigte Rollen ────────────────────────────────────────

AUTO_GEBEN_ROLES = {ADMIN_ROLE_ID, MOD_ROLE_ID, 1490855761822093452, 1490855760911925258}

# ── Fahrzeugliste nach Kategorie ──────────────────────────────

AUTOS: list[str] = [
    # Sportwagen
    "Annis Elegy RH8", "Annis Elegy Retro Custom", "Annis Euros", "Annis Hellion",
    "Annis RE-7B", "Annis S80RR", "Annis ZR350", "Benefactor Feltzer",
    "Benefactor Krieger", "Benefactor Schafter GT", "Benefactor Schafter LWB",
    "Benefactor Schafter V12", "Benefactor Stirling GT", "Benefactor Surano",
    "Bollokan Prairie", "Bravado Banshee", "Bravado Banshee 900R",
    "Bravado Buffalo", "Bravado Buffalo S", "Bravado Buffalo STX",
    "Bravado Gauntlet", "Bravado Gauntlet Classic", "Bravado Gauntlet Hellfire",
    "Bravado Hotring Hellfire", "Bravado Verlierer", "Bravado Verlierer 2",
    "Canis Mesa", "Canis Seminole Frontier", "Coquette", "Coquette BlackFin",
    "Coquette Classic", "Coil Cyclone", "Coil Cyclone II", "Coil Voltic",
    "Declasse Drift Yosemite", "Declasse Mamba", "Declasse Scramjet",
    "Declasse Tampa", "Declasse Voodoo", "Dewbauchee Exemplar",
    "Dewbauchee JB700", "Dewbauchee JB700W", "Dewbauchee Massacro",
    "Dewbauchee Rapid GT", "Dewbauchee Seven-70", "Dewbauchee Specter",
    "Dewbauchee Vagner", "Dinka Blista Compact", "Dinka Jester",
    "Dinka Jester Classic", "Dinka Jester RR", "Dinka RT3000",
    "Dinka Sugoi", "Dinka Toro", "Emperor Vectre", "Enus Deity",
    "Enus Paragon R", "Enus Paragon R Armored", "Enus Stafford",
    "Enus Windsor", "Enus Windsor Drop", "Grotti Brioso 300",
    "Grotti Carbonizzare", "Grotti Cheetah", "Grotti Cheetah Classic",
    "Grotti Furia", "Grotti GT500", "Grotti Itali GTO",
    "Grotti Itali RSX", "Grotti Stinger", "Grotti Stinger GT",
    "Grotti Turismo Classic", "Grotti Turismo R", "Grotti Visione",
    "Hijak Ruston", "HVY Nightshark", "Imponte Deluxo",
    "Imponte Dukes", "Imponte Dukes O'Death", "Imponte Nightshade",
    "Imponte Phoenix", "Imponte Ruiner", "Imponte Ruiner 2000",
    "Imponte Ruiner 3", "Imponte Tempesta", "Imponte Torero XO",
    "Invetero Coquette", "Jobuilt Phantom Custom", "Karin 190z",
    "Karin Asterope GT", "Karin Calico GTF", "Karin Everon",
    "Karin Futo", "Karin Futo GTX", "Karin Kuruma",
    "Karin Kuruma Armored", "Karin Previon", "Karin Sultan",
    "Karin Sultan Classic", "Karin Sultan RS", "Karin Sultan RS Classic",
    "Lampadati Felon", "Lampadati Felon GT", "Lampadati Furore GT",
    "Lampadati Komoda", "Lampadati Novak", "Lampadati Pigalle",
    "Lampadati Tropos Rallye", "Maibatsu Penumbra FF",
    "Maibatsu Sunrise", "Maxwell Asbo", "Maxwell Vagrant",
    "Maxwell Vargant", "MTL Pounder Custom", "Nagasaki Outlaw",
    "Ocelot Ardent", "Ocelot Growler", "Ocelot Jugular",
    "Ocelot Locust", "Ocelot R88", "Ocelot Swinger",
    "Ocelot Torero", "Ocelot Virtue", "Obey 8F Drafter",
    "Obey I-Wagen", "Obey Omnis", "Obey Omnis e-GT",
    "Obey Rocoto", "Obey Tailgater", "Obey Tailgater S",
    "Obey Zeno", "Overflod Entity MT", "Overflod Entity XF",
    "Overflod Entity XXR", "Overflod Imorgon", "Overflod Tyrant",
    "Pegassi Infernus", "Pegassi Infernus Classic", "Pegassi Osiris",
    "Pegassi Reaper", "Pegassi Tempesta", "Pegassi Tezeract",
    "Pegassi Torero XO", "Pegassi Zentorno", "Pegassi Zorrusso",
    "Progen GP1", "Progen Emerus", "Progen Itali GTB",
    "Progen Itali GTB Custom", "Progen PR4", "Progen T20",
    "Progen Tyrus", "Rune Cheburek", "Schyster Deviant",
    "Schyster Fusilade", "Schyster Greenwood", "Shyster Fusilade",
    "Truffade Adder", "Truffade Nero", "Truffade Nero Custom",
    "Truffade Thrax", "Ubermacht Cypher", "Ubermacht Niobe",
    "Ubermacht Oracle XS", "Ubermacht Rebla GTS", "Ubermacht SC1",
    "Ubermacht Sentinel", "Ubermacht Sentinel Classic",
    "Ubermacht Zion", "Ubermacht Zion Cabrio", "Vapid Caracara 4x4",
    "Vapid Clique", "Vapid Dominator", "Vapid Dominator ASP",
    "Vapid Dominator GTT", "Vapid Dominator GTX", "Vapid FMJ",
    "Vapid Flash GT", "Vapid GB200", "Vapid Imperator",
    "Vapid Peyote", "Vapid Peyote Custom", "Vapid Peyote Gasser",
    "Vapid Pisswasser Dominator", "Vapid Retinue", "Vapid Retinue MkII",
    "Vapid Speedo Custom", "Vapid Slamvan Custom", "Vapid Unnamed",
    "Weeny Dynasty", "Weeny Issi Classic", "Weeny Issi Sport",
    "Western Rampant Rocket",
    # SUV / Geländewagen
    "Albany Cavalcade", "Albany Cavalcade FXT", "Benefactor Dubsta",
    "Benefactor Dubsta 6x6", "Benefactor Serrano", "Benefactor Toros",
    "Bravado Gresley", "Canis Freecrawler", "Canis Kalahari",
    "Canis Mesa", "Canis Seminole", "Canis Taos",
    "Declasse Granger", "Declasse Rancher XL", "FathomFisher",
    "Gallivanter Baller", "Gallivanter Baller LE",
    "Gallivanter Baller LE LWB", "Gallivanter Baller ST",
    "Gallivanter Baller ST-D", "HVY Brickade 6x6",
    "Invetero Coquette BlackFin", "Karin Beejay XL", "Mammoth Patriot",
    "Mammoth Patriot Mil-Spec", "Mammoth Patriot Stretch",
    "Nagasaki Blazer", "Nagasaki Blazer Aqua", "Nagasaki Blazer Hot Rod",
    "Nagasaki Blazer Lifeguard", "Ocelot Centenario", "Obey Radius",
    "Vapid Guardian", "Vapid Riata", "Vulcar Warrener HKR",
    # Muscle Cars
    "Albany Buccaneer", "Albany Buccaneer Custom", "Albany Primo",
    "Albany Primo Custom", "Bravado Greenwood", "Declasse Cheetah Classic",
    "Declasse Moonbeam", "Declasse Moonbeam Custom", "Declasse Sabre Turbo",
    "Declasse Sabre Turbo Custom", "Imponte DF8-90", "Imponte Paleto",
    "Imponte Vice City Hauler", "Invetero Coquette Classic",
    "Vapid Blade", "Vapid Slamvan", "Vapid Stambler",
    # Klassiker / Oldtimer
    "Albany Roosevelt", "Albany Roosevelt Valor", "Albany Virgo",
    "Albany Virgo Classic", "Albany Virgo Classic Custom",
    "Declasse Tornado", "Declasse Tornado Custom",
    "Declasse Tornado Rat Rod", "Lampadati Michelli GT",
    # Limousinen / Busse
    "Albany Emperor", "Albany Emperor Beater", "Albany Stretch",
    "Benefactor Schafter LWB Armored", "Enus Cognoscenti",
    "Enus Cognoscenti 55", "Enus Cognoscenti 55 Armored",
    "Enus Cognoscenti Cabrio", "Enus Super Diamond", "Enus Superlite",
    # Kleinwagen
    "Bollokan Prairie", "Dinka Blista", "Grotti Brioso R/A",
    "Pfister Comet", "Pfister Comet SR", "Pfister Neon",
    "Pfister Growler", "Weeny Issi", "Weeny Issi Classic",
]

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

FLUGZEUGE: list[str] = [
    "Atomic Blimp", "B-11 Strikeforce", "Besra", "Bifta",
    "Bombushka", "Buckingham Nimbus", "Cuban 800", "Dodo",
    "Duster", "Hydra", "Imponte Deluxo", "JoBuilt P-996 LAZER",
    "Jobuilt Mammatus", "LF-22 Starling", "Luxor",
    "Luxor Deluxe", "Mammoth Avenger", "Mammoth Hydra",
    "Miljet", "Mogul", "Molotok", "Nimbus",
    "P-45 Nokota", "P-996 LAZER", "Pyro", "RO-86 Alkonost",
    "Rogue", "Seabreeze", "Shamal", "Smuggler's Plane",
    "Titan", "Tula", "Ultralight", "V-65 Molotok",
    "Velum", "Velum 5-Seater", "Vestra", "XT-2000 Western",
    "XA-21",
]

HELIKOPTER: list[str] = [
    "Akula", "Annihilator", "Annihilator Stealth",
    "APC Helicopter", "Buckingham Volatus",
    "Buzzard", "Buzzard Attack Chopper", "Cargobob",
    "Cargobob Jetsam", "FH-1 Hunter", "Frogger",
    "Frogger TPE", "Hunter", "Maverick",
    "Militär-Buzzard", "Police Maverick",
    "Savage", "Sea Sparrow", "Sea Sparrow 2",
    "Skylift", "Sparrow", "Supervolito",
    "Supervolito Carbon", "Swift", "Swift Deluxe",
    "Valkyrie", "Valkyrie MOD.0", "Volatus",
]

# ── Autocomplete-Funktion ─────────────────────────────────────

def _alle_fahrzeuge() -> list[tuple[str, str]]:
    """Gibt alle Fahrzeuge als (anzeige, wert) zurück."""
    result = []
    for name in AUTOS:
        result.append((f"🚗| {name}", f"🚗| {name}"))
    for name in MOTORRAEDER:
        result.append((f"🏍| {name}", f"🏍| {name}"))
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
    # Berechtigungsprüfung
    role_ids = {r.id for r in interaction.user.roles}
    if not role_ids & AUTO_GEBEN_ROLES:
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung für diesen Befehl.", ephemeral=True
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
        pass  # DMs deaktiviert — kein Fehler werfen
