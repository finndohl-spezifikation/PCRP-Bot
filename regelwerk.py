# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════════════════════════════
# regelwerk.py — Serverregelwerk Embed
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════════════════════════════

from config import *

REGELWERK_CHANNEL_ID = 1490882546144383156
REGELWERK_FILE       = DATA_DIR / "regelwerk_msgs.json"
REGELWERK_FARBE      = 0xFF8C00  # Orange

# ── Embed-Texte ───────────────────────────────────────────────────────────────────────

_EMBED1_TITEL = "📋 Paradise City Roleplay — Serverregelwerk (1/2)"

_EMBED1_TEXT = """**0️⃣ Roleplay-Grundlagen & Begriffe**

**Was ist Roleplay (RP)?**
Roleplay bedeutet, dass du eine fiktive Rolle in einer realistischen Spielwelt übernimmst. Du handelst nicht als reale Person, sondern als dein Charakter und reagierst möglichst realistisch und glaubwürdig auf Situationen.

**📖 Wichtige Begriffe**
🔹 **IC** *(In Character)* — Alles, was im Spiel innerhalb deiner Rolle passiert.
🔹 **OOC** *(Out of Character)* — Alles außerhalb deines Charakters.
❌ **Metagaming** — Externe Informationen im RP nutzen. Verboten.
❌ **PowerRP** — Zwangshandlungen ohne Reaktionsmöglichkeit. Verboten.
✅ **FearRP** — Angemessenes Angstverhalten bei Gefahr. Pflicht.
❌ **FailRP** — Unrealistisches Verhalten. Verboten.
❌ **RDM** — Töten ohne RP-Grund. Verboten.
❌ **VDM** — Fahrzeug als Waffe nutzen. Verboten.
❌ **Combat Log** — Verlassen einer RP-Situation. Verboten.
❌ **IC/OOC Mixing** — Vermischung von IC und OOC. Verboten.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**1️⃣ Einreise & Charakter**

**§1 Einreisebedingungen**
Jeder Spieler stimmt zu, dass seine Discord-ID gespeichert wird, solange er auf dem Server aktiv ist.

**§1.1 Charaktererstellung** — Keine Whitelist oder Bewerbung erforderlich.
> • Jeder Spieler erstellt einen RP-Charakter
> • Realistische Angaben sind Pflicht — falsche Angaben sind verboten
> • Charakteränderung nur durch RP-Tod möglich

**§1.2 Einreisearten:** Legal · Illegal · Gruppeneinreise *(ab 5 Personen)*
**§1.3 Gruppeneinreise:** Ab 5 Personen — Nachweis im Support erforderlich.
**§1.4 Zweitcharaktere:** Nur mit Anmeldung im Support erlaubt.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**2️⃣ Verhalten auf dem Server**

**§2 Grundverhalten**
Respekt ist Pflicht. Diskriminierung und Beleidigungen sind verboten.

**§2.1 Spam & Werbung:** ❌ Keine Werbung · Keine Serverlinks · Kein Spam
**§2.2 Teamkommunikation:** Kein privater Kontakt zu Teammitgliedern.
**§2.3 Support:** Richtige Kategorie nutzen · Kein Spam · Geduld zeigen.
**§2.4 Serverstörung:** Griefing und Sabotage sind verboten.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**3️⃣ Support & Systeme**

**§3 Supportsystem:** Nur über Tickets oder Supportbereiche.
**§3.1 Ingame-Support:** Nur erlaubt wenn vom Serverteam genehmigt und ausschließlich in einem CO durchgeführt. Support im Jeder-Chat oder außerhalb eines COs ist verboten.
**§3.2 Clips:** Nur im Support verwenden.
**§3.3 Teamrechte & Warnsystem:** Missbrauch melden · Warns anfechtbar · Einspruch möglich.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**4️⃣ Serversicherheit**

**§4 Exploits & Bugs:** Das Ausnutzen von Bugs, Glitches oder Exploits ist streng verboten.
**§4.1 Bot-Fehler:** Müssen sofort gemeldet werden — Nutzung verboten.
**§4.2 Serverangriffe:** Führen zum sofortigen Ausschluss.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**5️⃣ Kommunikation & UI**

**§5 Ingame Voice:** Nur GTA-Ingame-Voice erlaubt.
**§5.1 Einzelfunks / Funk:** Erlaubt, solange die Lobby nicht voll ist. Bei voller Lobby müssen sie aufgelöst werden.
**§5.2 Minimap & Spieleranzeige:**
> ❌ Minimap beim Betreten der Lobby deaktivieren
> ❌ Spieleranzeige ebenfalls deaktivieren

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**6️⃣ Ingame-Regeln**

**§6 Realismus:** Alles muss realistisch gespielt werden.
**§6.1 Schusscall:** Pflicht — 15 Minuten gültig.
**§6.2 Bewusstlosigkeit:** Maximal 10 Minuten.
**§6.3 Dispatch-System:** Wenn ein Spieler bewusstlos aufgefunden wird, ist Folgendes Pflicht:
> • Dispatch abzusetzen **oder** eine Erstversorgung durchzuführen
**§6.4 RP-Tod:** Der Charakter verliert alle Items."""

_EMBED2_TITEL = "📋 Paradise City Roleplay — Serverregelwerk (2/2)"

_EMBED2_TEXT = """**7️⃣ Inventar & Besitzsystem**

**§7 Grundregel:** Nur verwenden, was im RP besessen wird.
**§7.1 Fahrzeuge:** Müssen im RP gekauft sein — Fahrzeugdiebstahl ist verboten.
**§7.2 Waffen & Items:** Nur eigene Items erlaubt.
**§7.3 Lager:** Items dürfen nicht verwendet werden, solange sie im Lager liegen. Sie dürfen erst wieder benutzt werden, sobald sie entnommen wurden.
**§7.4 Immobilien:** Nur mit RP-Besitz nutzbar.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**8️⃣ Polizei & Medizin**

**§8 PD-Regeln:** Kein grundloser Angriff auf die Polizei (PD).
**§8.1 MD-Regeln:** Der Medizinische Dienst (MD) darf nicht ausgeraubt oder entführt werden.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**9️⃣ Wirtschaft & Aktivitäten**

**§9 Farmregeln:** Nur nach Vorgabe erlaubt.
**§9.1 Minijobs:** Nur eine Aktivität gleichzeitig erlaubt.
**§9.2 Raubüberfälle:** Geltende Regeln sind einzuhalten.
**§9.3 Safezones:** Keine Gewalt erlaubt.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**🔟 Fahrzeuge & Tuning**

**§10 Fahrzeuge:** Müssen realistisch genutzt werden.
**§10.1 Tuning:**
> • Alles bis Stufe 2 erlaubt
> • Über Stufe 2 gilt als illegal
> • Jedes Tuning muss im RP erworben werden

**§10.2 Illegales Tuning:** Nur beim illegalen Tuner erhältlich.
**§10.3 Bennys Felgen:** Nur beim illegalen Tuner erhältlich.
**§10.4 F1-Reifen:** Nur bei Geländewagen erlaubt.
**§10.5 Kennzeichen:** Alle Kennzeichen erlaubt, außer Regierungskennzeichen *(SA Exempt)*. Leere Kennzeichen sind erlaubt, gelten jedoch als ungültig.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**1️⃣1️⃣ Kleidung**

**§11 Kleidungssystem** — Grundsätzlich erlaubt, außer:
> ❌ Gemoddete Outfits verboten
> ❌ Verglitchte Kleidung verboten
> ✅ Joggers erlaubt *(wenn keine unsichtbaren Stellen sichtbar sind)*
> ✅ Eselmütze / Spielverderberhut erlaubt
> ✅ Duffel Bags erlaubt *(realistisch einsetzen)*

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**1️⃣2️⃣ Servergrundsatz**

**§12 Grundregel**
Alles, was nicht ausdrücklich erlaubt ist, kann sanktioniert werden.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
*Die Serverleitung behält sich das Recht vor, das Regelwerk jederzeit zu verändern. Änderungen treten sofort in Kraft und werden im <#1490882547310399508> angekündigt.*"""


# ── Datei-Helpers ─────────────────────────────────────────────────────────────────────

def load_regelwerk_data():
    if REGELWERK_FILE.exists():
        with open(REGELWERK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"msg1": None, "msg2": None}


def save_regelwerk_data(data):
    with open(REGELWERK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Embeds bauen ──────────────────────────────────────────────────────────────────────

def build_embed1() -> discord.Embed:
    return discord.Embed(
        title=_EMBED1_TITEL,
        description=_EMBED1_TEXT,
        color=REGELWERK_FARBE,
    )


def build_embed2() -> discord.Embed:
    e = discord.Embed(
        title=_EMBED2_TITEL,
        description=_EMBED2_TEXT,
        color=REGELWERK_FARBE,
    )
    e.set_footer(text="Paradise City Roleplay • Serverregelwerk")
    return e


# ── Auto Setup ────────────────────────────────────────────────────────────────────────

async def auto_regelwerk_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(REGELWERK_CHANNEL_ID)
        if not channel:
            continue

        data = load_regelwerk_data()
        e1   = build_embed1()
        e2   = build_embed2()

        # Vorhandene Nachrichten aktualisieren
        updated = 0
        if data.get("msg1"):
            try:
                msg = await channel.fetch_message(data["msg1"])
                await msg.edit(embed=e1)
                updated += 1
            except Exception:
                data["msg1"] = None

        if data.get("msg2"):
            try:
                msg = await channel.fetch_message(data["msg2"])
                await msg.edit(embed=e2)
                updated += 1
            except Exception:
                data["msg2"] = None

        if updated == 2:
            print("[regelwerk] Embeds aktualisiert.")
            return

        # Alte Regelwerk-Embeds löschen
        try:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Serverregelwerk" in emb.title:
                            try:
                                await msg.delete()
                            except Exception:
                                pass
                            break
        except Exception:
            pass

        # Neu posten
        try:
            m1 = await channel.send(embed=e1)
            m2 = await channel.send(embed=e2)
            data["msg1"] = m1.id
            data["msg2"] = m2.id
            save_regelwerk_data(data)
            print(f"[regelwerk] Embeds gepostet in #{channel.name}")
        except Exception as exc:
            print(f"[regelwerk] Fehler beim Posten: {exc}")


# ── Slash Command: /setup-regelwerk ──────────────────────────────────────────────────

@bot.tree.command(
    name="setup-regelwerk",
    description="[Admin] Löscht das alte Regelwerk-Embed und postet ein neues",
    guild=discord.Object(id=GUILD_ID),
)
async def setup_regelwerk(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    for guild in bot.guilds:
        channel = guild.get_channel(REGELWERK_CHANNEL_ID)
        if not channel:
            continue

        data = load_regelwerk_data()

        # Alte Embeds löschen
        try:
            async for msg in channel.history(limit=30):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Serverregelwerk" in emb.title:
                            try:
                                await msg.delete()
                            except Exception:
                                pass
                            break
        except Exception:
            pass

        # IDs zurücksetzen und neu posten
        data["msg1"] = None
        data["msg2"] = None
        save_regelwerk_data(data)

        m1 = await channel.send(embed=build_embed1())
        m2 = await channel.send(embed=build_embed2())
        data["msg1"] = m1.id
        data["msg2"] = m2.id
        save_regelwerk_data(data)
        print(f"[regelwerk] Neu gepostet in #{channel.name}")

    await interaction.followup.send("✅ Regelwerk wurde neu gepostet.", ephemeral=True)
