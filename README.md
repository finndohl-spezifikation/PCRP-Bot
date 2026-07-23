# PCRP-Bot

Discord-Bot für den PCRP GTA-RP-Server – geschrieben in **Java** mit **JDA 5**.
Läuft auf **Railway** via Docker, Quellcode auf GitHub.

## Features

### Moderationssystem
- **Wortfilter** – vulgäre Kraftausdrücke sofort löschen (Deutsch + Englisch, Leetspeak-Normalisierung)
- **Spamschutz** – mehr als 7 Nachrichten in ~10 Sekunden → DM-Verwarnung, beim 2. Mal 10 Min. Timeout
- **67-Filter** – „67" / „sixseven" wird automatisch zu „69" / „sixnine" (im Namen des Nutzers neu gepostet)
- **Eigenwerbungs-Schutz** – fremde Discord-Links: löschen, 14 Tage Timeout, DM + Alert
- **Anti-Nuke (Fremdbots)** – sofortiger Perma-Bann + DM an Einladenden + Alert
- **Serverschutz (Massenlöschung)** – Kanäle/Kategorien/Rollen: 14 Tage Timeout, DM, Alert + automatische Wiederherstellung

### Slash-Commands
| Befehl | Berechtigung | Funktion |
|--------|-------------|---------|
| `/löschen [anzahl: 1-200]` | Nachrichten verwalten | Löscht Nachrichten im Kanal |
| `/bannen [mitglied] [grund?]` | Mitglieder bannen | Permanenter Bann + DM |
| `/entbannen [nutzer]` | Mitglieder bannen | Bann aufheben (Autocomplete aus Bannliste) |
| `/timeout [mitglied] [dauer] [grund?]` | Mitglieder moderieren | Timeout mit Dropdown-Auswahl (5 Min – 14 Tage) |

### Log-System (7 Kanäle)
- Server-Logs, Moderations-Logs, Spieler-Logs, Nachrichten-Logs, Rollen-Logs, Geld-Logs, Ticket-Logs

## Technisches

- **Sprache:** Java 21 · JDA 5.2.2
- **Build:** Maven → Fat-JAR via `maven-shade-plugin`
- **Deployment:** Railway erkennt `Dockerfile` automatisch
- **Persistenz:** Railway Volume bei `/app/data` (via `DATA_DIR` Umgebungsvariable überschreibbar)

## Benötigte Discord-Berechtigungen

Der Bot braucht: **Administrator** (oder einzeln: Nachrichten verwalten, Mitglieder moderieren, Mitglieder bannen, Webhooks verwalten, Audit-Log einsehen)

## Benötigte Privileged Intents (Discord Developer Portal)

- **Server Members Intent** ✅ aktivieren
- **Message Content Intent** ✅ aktivieren

## Umgebungsvariablen (Railway)

| Variable | Beschreibung |
|----------|-------------|
| `DISCORD_TOKEN` | Discord Bot Token |
| `DATA_DIR` | (Optional) Pfad für persistente Daten, Standard: `/app/data` |
