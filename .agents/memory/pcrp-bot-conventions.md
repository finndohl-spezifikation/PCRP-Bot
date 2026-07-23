---
name: PCRP Discord Bot Conventions
description: Tech-Stack, Struktur und nicht verhandelbare Regeln des PCRP-Discord-Bots.
---

## Sprache & Framework
- **Java** (GraalVM 22.3 / Java 19 auf Replit), **JDA 5.2.2**
- Maven Build, Fat-JAR via `maven-shade-plugin` → `target/pcrp-bot.jar`
- Externe Bot-Repo: GitHub `finndohl-spezifikation/PCRP-Bot`, Branch `main`
- Läuft auf **Railway** (erkennt Dockerfile automatisch)
- Bot läuft NICHT auf Replit — nur Build-Check und Push

## Push-Workflow
1. `dotnet build` / `mvn package -DskipTests -q` im `pcrp-bot/` Verzeichnis
2. Nach erfolgreichem Build: `/tmp/pcrp-push` (geklontes Repo, `.git` erhalten)
3. Inhalte löschen, neue Dateien kopieren (ohne `target/`), committen, pushen

## Nicht verhandelbare Regeln
- Jedes Embed **dunkelorange** `0xCC5500` via `EmbedFactory` — niemals direkt bauen
- **Kein Footer-Text** in Embeds (Ausnahme: Bot-Neustart-Embed → Java-Logo-Icon via `createWithFooterIcon()`)
- Panels / Startup-Infos **einmalig beim Start** posten mit Duplikat-Check — kein `/setup`-Befehl
- **Owner ID** `1259265007791636540L` hat keinerlei Einschränkungen und wird bei jedem Alert gepingt
- Alert-Kanal `1529636455079608431L`

## Projektstruktur (Java)
```
pcrp-bot/
  pom.xml
  Dockerfile
  src/main/java/de/pcrp/bot/
    Main.java                   ← JDA-Setup, StartupListener (Commands registrieren)
    common/
      EmbedFactory.java
      ModerationConfig.java
      LoggingConfig.java
      WordFilter.java
      DataStore.java
      MessageCache.java
      BotLogger.java
    listeners/
      LoggingListener.java
      ModerationListener.java
      GuildProtectionListener.java
      CommandListener.java
  src/main/resources/logback.xml
```

## Wichtige JDA 5.2.2 API-Eigenheiten (gelernte Fallen)
- `event.reply(embed)` existiert NICHT → `event.replyEmbeds(embed)` verwenden
- `guild.ban(member, days)` existiert NICHT → `guild.ban(member.getUser(), 0, TimeUnit.SECONDS).reason(...)`
- `GuildUpdateDefaultNotificationsEvent` existiert nicht in 5.2.2 → weglassen
- `GuildMemberUpdateRolesEvent` existiert nicht → stattdessen `GuildMemberRoleAddEvent` + `GuildMemberRoleRemoveEvent` (beide in `net.dv8tion.jda.api.events.guild.member`)
- Channel-Update-Events (`ChannelUpdateNameEvent` etc.) sind in Subpackage → `import net.dv8tion.jda.api.events.channel.update.*;` nötig
- `GuildVoiceStreamEvent` / `GuildVoiceVideoEvent` existieren in 5.2.2 nicht als separate Events
- `ActionType.MEMBER_ROLE_OVERRIDE` existiert nicht → `ActionType.MEMBER_ROLE_UPDATE`
- `MessageBulkDeleteEvent.isFromGuild()` existiert nicht (bulk delete ist immer von Guild)
- Lambda-Variable aus Schleife (z.B. `shown++`) muss in `final` kopiert werden

## Umgebungsvariablen (Railway)
- `DISCORD_TOKEN` — Discord Bot-Token
- `DATA_DIR` — optional, Standard `/app/data` (Railway Volume)

## Hinweis zu Secrets
- `PCRP_BOT_TOKEN` auf Replit = GitHub Access Token (zum Pushen), NICHT der Discord-Token
- Discord-Token ist `DISCORD_TOKEN` und wird nur auf Railway gesetzt

## Log-Kanal-IDs (alle in LoggingConfig.java)
- Server-Logs:      `1529636412628930723`
- Moderations-Logs: `1529636417636929707`
- Spieler-Logs:     `1529636419071639735`
- Nachrichten-Logs: `1529636425337667714`
- Rollen-Logs:      `1529636428370280509`
- Geld-Logs:        `1529636430362574968`
- Ticket-Logs:      `1529636431784317019`
