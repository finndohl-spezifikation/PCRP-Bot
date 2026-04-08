# Cryptik-Bot

Ein Discord-Bot für den **Kryptik Roleplay**-Server, entwickelt mit [discord.py](https://discordpy.readthedocs.io/). Der Bot bietet Moderation, Logging, ein Ticket-System, ein komplettes Economy-System mit Shop und Inventar, ein Ausweis-System sowie diverse Verwaltungsfunktionen.

---

## Inhaltsverzeichnis

- [Funktionen](#funktionen)
- [Deployment](#deployment)
- [Umgebungsvariablen](#umgebungsvariablen)
- [Slash Commands](#slash-commands)
  - [Economy](#economy)
  - [Inventar](#inventar)
  - [Warn-System](#warn-system)
  - [Ausweis-System](#ausweis-system)
  - [Team-Commands](#team-commands)
  - [Admin-Commands](#admin-commands)
- [Prefix-Commands](#prefix-commands)
- [Automatische Funktionen](#automatische-funktionen)
- [Datenspeicherung](#datenspeicherung)
- [Anforderungen](#anforderungen)

---

## Funktionen

| Funktion | Beschreibung |
|---|---|
| 🔗 Discord Link Schutz | Fremde Discord-Einladungen werden gelöscht, Nutzer getimeoutet |
| 🔗 Link Filter (Memes) | Links sind nur im Memes-Kanal erlaubt |
| 🤬 Vulgäre Wörter Filter | Nachrichten mit vulgären Ausdrücken werden gelöscht |
| 🚫 Spam Schutz | Bei Spam wird eine Verwarnung und danach ein 10-Minuten-Timeout erteilt |
| 🗑️ Nachrichten Log | Gelöschte Nachrichten werden protokolliert |
| ✏️ Bearbeitungs Log | Bearbeitete Nachrichten werden protokolliert |
| 🎭 Rollen Log | Rollenänderungen werden protokolliert |
| 👤 Member Log | Beitritte, Kicke und Bans werden protokolliert |
| 📥 Join Log + Invites | Neue Mitglieder und deren Einlader werden protokolliert |
| 🤖 Bot Kick | Bots werden automatisch vom Server gekickt |
| ⚠️ Fehler Logging | Bot-Fehler werden in einem dedizierten Kanal protokolliert |
| 🔇 Rollen-Entfernung (Timeout) | Beim Timeout werden alle Rollen entfernt |
| 🎟 Ticket System | Vollständiges Ticket-System mit Transkripten und Bewertungen |
| 🔢 Zähl-Kanal | Moderierter Kanal zum gemeinsamen Zählen |
| 💵 Economy System | Lohn, Banking, Shop, Inventar und Item-Verwaltung |

---

## Deployment

Der Bot ist für das Deployment auf **[Railway](https://railway.app/)** ausgelegt.

1. Repository auf Railway verbinden
2. Die erforderlichen [Umgebungsvariablen](#umgebungsvariablen) setzen
3. Ein Volume unter `/data` mounten und `DATA_DIR=/data` setzen, um persistente Daten zu gewährleisten
4. Der Bot startet automatisch über den `Procfile`-Worker-Prozess:
   ```
   worker: python bot.py
   ```

> **Hinweis:** Der Bot prüft beim Start, ob er auf Railway läuft (`RAILWAY_ENVIRONMENT`). Ist die Variable nicht gesetzt, beendet sich der Bot mit einem Hinweis. Für lokale Tests kann `FORCE_LOCAL_RUN=1` gesetzt werden.

---

## Umgebungsvariablen

| Variable | Erforderlich | Beschreibung |
|---|---|---|
| `DISCORD_TOKEN` | ✅ | Bot-Token aus dem Discord Developer Portal |
| `RAILWAY_ENVIRONMENT` | ✅ (auf Railway automatisch) | Wird von Railway automatisch gesetzt |
| `DATA_DIR` | ❌ | Pfad zum Datenverzeichnis (Standard: `./data`). Auf Railway auf `/data` setzen |
| `FORCE_LOCAL_RUN` | ❌ | Auf `1` setzen, um den Bot lokal ohne Railway-Umgebung zu starten |

---

## Slash Commands

Alle Slash Commands sind auf den konfigurierten Guild beschränkt.

### Economy

| Command | Berechtigung | Beschreibung |
|---|---|---|
| `/lohn-abholen` | Lohnklasse erforderlich | Stündlichen Lohn auf das Bankkonto einzahlen |
| `/kontostand` | Citizen/Lohnklasse (eigener), Team (anderer) | Bargeld und Kontostand anzeigen |
| `/einzahlen <betrag>` | Citizen/Lohnklasse | Bargeld auf das Bankkonto einzahlen |
| `/auszahlen <betrag>` | Citizen/Lohnklasse | Geld vom Bankkonto abheben |
| `/ueberweisen <nutzer> <betrag>` | Citizen/Lohnklasse | Geld an einen anderen Spieler überweisen |
| `/shop` | Citizen/Lohnklasse | Verfügbare Shop-Items anzeigen |
| `/buy <itemname>` | Citizen/Lohnklasse | Item aus dem Shop kaufen (nur mit Bargeld) |

> Tägliches Limit für Einzahlungen, Auszahlungen und Überweisungen: **1.000.000 💵** (anpassbar per `/set-limit`).

#### Lohnklassen

| Rolle | Lohn pro Stunde |
|---|---|
| Lohnklasse 1 | 1.500 💵 |
| Lohnklasse 2 | 2.500 💵 |
| Lohnklasse 3 | 3.500 💵 |
| Lohnklasse 4 | 4.500 💵 |
| Lohnklasse 5 | 5.500 💵 |
| Lohnklasse 6 | 6.500 💵 |
| Zusatzlohn-Rolle | +1.200 💵 |

---

### Inventar

| Command | Berechtigung | Beschreibung |
|---|---|---|
| `/rucksack [nutzer]` | Citizen/Lohnklasse (eigener), Team (anderer) | Inventar anzeigen |
| `/uebergeben <nutzer> <item>` | Alle | Item aus dem eigenen Inventar an einen anderen Spieler übergeben |
| `/verstecken <item> <ort>` | Alle | Item an einem Ort verstecken (mit Button zum Bergen) |

---

### Warn-System

| Command | Berechtigung | Beschreibung |
|---|---|---|
| `/warn <nutzer> <grund> <konsequenz>` | Team | Verwarnung für einen Spieler ausstellen |
| `/warn-list <nutzer>` | Team | Alle Verwarnungen eines Spielers anzeigen |
| `/remove-warn <nutzer>` | Team | Letzte Verwarnung eines Spielers entfernen |

> Bei **3 Verwarnungen** wird automatisch ein **2-Tage-Timeout** erteilt und alle Rollen werden entfernt.

---

### Ausweis-System

| Command | Berechtigung | Beschreibung |
|---|---|---|
| `/ausweisen` | Alle (im Ausweis-Kanal) | Eigenen Personalausweis anzeigen |

Neue Spieler erstellen ihren Ausweis über das **Einreise-System** im Einreise-Kanal. Es wird zwischen **legaler** und **illegaler** Einreise unterschieden. Nach der Einreise werden automatisch die Charakter-Rollen vergeben.

---

### Team-Commands

| Command | Berechtigung | Beschreibung |
|---|---|---|
| `/set-limit <nutzer> <limit>` | Team (Mod/Admin) | Individuelles Tageslimit für einen Spieler setzen |
| `/shop-add <itemname> <preis> [rolle]` | Team | Neues Item zum Shop hinzufügen (mit optionaler Rollenbeschränkung) |
| `/item-geben <nutzer> <item>` | Team | Item direkt an einen Spieler vergeben |
| `/item-entfernen <nutzer> <item>` | Team | Item von einem Spieler entfernen |
| `/warn <nutzer> <grund> <konsequenz>` | Team | Verwarnung ausstellen |
| `/warn-list <nutzer>` | Team | Verwarnungen anzeigen |
| `/remove-warn <nutzer>` | Team | Letzte Verwarnung entfernen |
| `/kartenkontrolle` | Team | DM-Erinnerung zur Kartenkontrolle an alle Spieler senden |
| `/delete <anzahl>` | Team | Bis zu 100 Nachrichten im aktuellen Kanal löschen |

---

### Admin-Commands

| Command | Berechtigung | Beschreibung |
|---|---|---|
| `/money-add <nutzer> <betrag>` | Admin | Einem Spieler Bargeld hinzufügen |
| `/remove-money <nutzer> <betrag>` | Admin | Bargeld von einem Spieler entfernen |
| `/item-add <nutzer> <itemname>` | Admin | Item direkt zum Inventar eines Spielers hinzufügen |
| `/remove-item <nutzer> <itemname>` | Admin | Item aus dem Inventar eines Spielers entfernen |
| `/ausweis-create <nutzer>` | Admin | Ausweis für einen Spieler erstellen |
| `/ausweis-remove <nutzer>` | Admin | Ausweis eines Spielers löschen |

---

## Prefix-Commands

| Command | Berechtigung | Beschreibung |
|---|---|---|
| `!hallo` | Alle | Bot antwortet mit einer Begrüßung |
| `!botstatus` | Admin | Bot-Status aller Funktionen anzeigen |
| `!testping` | Admin | Test-Ping an den Mod-Log-Kanal senden |
| `!ticketsetup` | Admin | Ticket-Embed manuell in den Ticket-Kanal posten |

---

## Automatische Funktionen

Beim Start des Bots werden folgende Embeds automatisch in den konfigurierten Kanälen gepostet (sofern noch nicht vorhanden):

- **Ticket-Embed** im Ticket-Setup-Kanal mit Auswahlmenü für Ticket-Arten
- **Lohnliste** im Lohnlisten-Kanal mit allen Lohnklassen und Stundenlöhnen
- **Einreise-Embed** im Einreise-Kanal mit Auswahlmenü für legale/illegale Einreise

Beim Beitritt neuer Mitglieder:
- Automatische Vergabe der Whitelist-Rolle
- Startguthaben von **5.000 💵** (Bargeld)
- Willkommens-DM und Nachricht im Willkommens-Kanal
- Standard-Nickname `RP Name | PSN` wird gesetzt

---

## Datenspeicherung

Alle Daten werden als JSON-Dateien im `DATA_DIR`-Verzeichnis gespeichert:

| Datei | Inhalt |
|---|---|
| `economy_data.json` | Kontostände, Inventare, Tageslimits, letzter Lohnabholzeitpunkt |
| `shop_data.json` | Shop-Items mit Preisen und optionalen Rollenbeschränkungen |
| `warns_data.json` | Verwarnungen aller Spieler |
| `hidden_items.json` | Versteckte Items mit Ort und Besitzer |
| `ausweis_data.json` | Ausweisdaten aller Spieler |

> **Wichtig:** Auf Railway ein persistentes Volume unter `/data` mounten und `DATA_DIR=/data` setzen. Ohne persistentes Volume gehen alle Daten bei einem Redeploy verloren.

---

## Anforderungen

- Python 3.10+
- `discord.py` (siehe `requirements.txt`)

```bash
pip install -r requirements.txt
```