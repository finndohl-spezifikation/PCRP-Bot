# PCRP-Bot

Custom Discord Roleplay Bot für den PCRP GTA RP Server (C# / .NET 8, Discord.Net).

## Features

- `/hallo` — der Bot begrüßt den Nutzer
- **Moderationssystem**
  - Wortfilter: vulgäre Kraftausdrücke werden sofort gelöscht
  - Spamschutz: mehr als 7 Nachrichten in kürzester Zeit → DM-Verwarnung, beim 2. Mal 10 Minuten Timeout
  - Anti-Nuke: fremde Bots werden sofort permanent gebannt (DM an Einladenden + Aktivitätswarnung)
  - Serverschutz: Massenlöschung von Kanälen/Kategorien/Rollen → 14 Tage Timeout, DM, Aktivitätswarnung und automatische Wiederherstellung (Name, Berechtigungen, Rollenfarbe)
  - 67/sixseven wird automatisch zu 69/sixnine geändert
  - Fremde Discord-Server-Links: löschen, 14 Tage Timeout, DM + Aktivitätswarnung
  - Aktivitätswarnungen gehen in den konfigurierten Kanal und pingen den Inhaber
  - Der Inhaber hat keinerlei Einschränkungen

**Benötigte Bot-Berechtigungen:** Nachrichten verwalten, Mitglieder moderieren (Timeout), Mitglieder bannen, Webhooks verwalten, Audit-Log einsehen.
**Wichtig:** Im Discord Developer Portal müssen die Privileged Intents **Server Members** und **Message Content** aktiviert sein.

## Regeln (Projektstandard)

- Alle Embeds sind **dunkelorange** (`EmbedFactory`), keine Ausnahmen
- **Keine Footer-Texte** in Embeds
- Panels/Embeds werden automatisch beim Bot-Start einmalig gesendet (kein `/setup`)

## Deployment (Railway)

1. Repo mit Railway verbinden — das `Dockerfile` wird automatisch erkannt
2. Environment Variable setzen: `DISCORD_TOKEN` (Discord Bot Token)
3. Volume unter `/app/data` mounten — dort speichert der Bot alle persistenten Daten

## Lokal starten

```bash
DISCORD_TOKEN=... DATA_DIR=./data dotnet run --project src/PCRP.Bot
```
