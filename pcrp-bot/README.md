# PCRP-Bot

Custom Discord Roleplay Bot für den PCRP GTA RP Server (C# / .NET 8, Discord.Net).

## Features

- `/hallo` — der Bot begrüßt den Nutzer

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
