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
2. Environment Variable setzen: `DISCORD_BOT_TOKEN` (Discord Bot Token)

## Lokal starten

```bash
DISCORD_BOT_TOKEN=... dotnet run --project src/PCRP.Bot
```
