---
name: PCRP Discord bot conventions
description: Rules and setup for the user's external C# GTA RP Discord bot (Railway-hosted, GitHub repo)
---

- Project lives in `pcrp-bot/` (clone of github.com/finndohl-spezifikation/PCRP-Bot). Not a Replit artifact; user hosts on Railway via Dockerfile. Push to `main` after each finished feature.
- The secret `PCRP_BOT_TOKEN` is the **GitHub access token** (clone remote already embeds it), NOT the Discord token. Discord token is `DISCORD_BOT_TOKEN`, set by the user on Railway; bot is not run on Replit.
- User rules (mandatory, all future features):
  - Every embed must be dark orange — use `EmbedFactory` (`Common/EmbedFactory.cs`), never build embeds directly.
  - No footer text in any embed — embeds stay clean.
  - Panels (tickets etc.) are auto-posted once on bot startup with duplicate check; never `/setup`-style commands.
- Stack: .NET 8, Discord.Net, Generic Host with `BotService` BackgroundService; slash commands via Interaction modules, registered globally on Ready.
- User communicates in German; keep code comments/READMEs in German.
- Planned later: ASP.NET Core web dashboard in the same process/repo.
