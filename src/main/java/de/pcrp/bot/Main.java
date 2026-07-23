package de.pcrp.bot;

import de.pcrp.bot.common.*;
import de.pcrp.bot.listeners.*;
import de.pcrp.bot.web.WebServer;
import net.dv8tion.jda.api.*;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.session.ReadyEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.commands.DefaultMemberPermissions;
import net.dv8tion.jda.api.interactions.commands.OptionType;
import net.dv8tion.jda.api.interactions.commands.build.*;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.requests.GatewayIntent;
import net.dv8tion.jda.api.utils.ChunkingFilter;
import net.dv8tion.jda.api.utils.MemberCachePolicy;
import net.dv8tion.jda.api.utils.cache.CacheFlag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.List;

public class Main {

    private static final Logger log = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args) throws Exception {
        String token = System.getenv("DISCORD_TOKEN");
        if (token == null || token.isBlank()) {
            log.error("DISCORD_TOKEN ist nicht gesetzt. Bot kann nicht starten.");
            System.exit(1);
        }

        // Web-Server starten (PORT wird von Railway gesetzt, Standard 8080)
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        WebServer.start(port);

        ModerationListener   moderationListener  = new ModerationListener();
        GuildProtectionListener protectionListener = new GuildProtectionListener();
        WelcomeListener      welcomeListener     = new WelcomeListener();

        JDABuilder.createDefault(token)
            .enableIntents(
                GatewayIntent.GUILD_MESSAGES,
                GatewayIntent.MESSAGE_CONTENT,
                GatewayIntent.GUILD_MEMBERS,
                GatewayIntent.GUILD_MODERATION,
                GatewayIntent.GUILD_INVITES,
                GatewayIntent.GUILD_VOICE_STATES
            )
            .enableCache(
                CacheFlag.VOICE_STATE,
                CacheFlag.MEMBER_OVERRIDES
            )
            .setMemberCachePolicy(MemberCachePolicy.ALL)
            .setChunkingFilter(ChunkingFilter.ALL)
            .addEventListeners(
                new StartupListener(),
                moderationListener,
                protectionListener,
                new LoggingListener(),
                new CommandListener(),
                welcomeListener
            )
            .build();
    }

    // ─── Startup ────────────────────────────────────────────────────────────────

    public static class StartupListener extends ListenerAdapter {

        private static final Logger log = LoggerFactory.getLogger(StartupListener.class);

        @Override
        public void onReady(ReadyEvent event) {
            JDA jda = event.getJDA();
            BotContext.setJda(jda);

            // Globale Commands entfernen (kein 1h-Delay)
            jda.updateCommands().queue();

            List<CommandData> commands = buildCommands();
            for (Guild guild : jda.getGuilds()) {
                guild.updateCommands()
                    .addCommands(commands)
                    .queue(
                        ok  -> log.info("Commands auf '{}' registriert.", guild.getName()),
                        err -> log.error("Fehler beim Registrieren auf '{}'.", guild.getName(), err)
                    );

                // Meldeamt-Panel einmalig posten (Duplikat-Schutz via DataStore)
                postMeldeamtPanel(guild);
            }

            log.info("Bot bereit – eingeloggt als {}.", jda.getSelfUser().getAsTag());
        }

        private static void postMeldeamtPanel(Guild guild) {
            String key    = "panel-meldeamt-" + guild.getId();
            String webUrl = System.getenv().getOrDefault("WEB_URL", "https://example.com");

            TextChannel ch = guild.getTextChannelById(LoggingConfig.MELDEAMT_CHANNEL_ID);
            if (ch == null) { log.warn("[Meldeamt] Panel-Kanal nicht gefunden."); return; }

            // Format gespeicherter Wert: "messageId|webUrl"
            String stored     = DataStore.readString(key);
            String storedMsgId  = null;
            String storedUrl    = null;
            if (stored != null && stored.contains("|")) {
                storedMsgId = stored.split("\\|", 2)[0];
                storedUrl   = stored.split("\\|", 2)[1];
            } else if (stored != null && !stored.isBlank()) {
                // Altes Format (nur Message-ID, kein URL-Teil) → neu senden
                storedMsgId = stored.trim();
            }

            boolean urlChanged = !webUrl.equals(storedUrl);

            if (storedMsgId != null) {
                final String msgId = storedMsgId;
                if (urlChanged) {
                    // Domain hat sich geändert → altes Panel löschen und frisches senden
                    ch.retrieveMessageById(msgId).queue(
                        msg -> msg.delete().queue(
                            v   -> sendPanel(ch, key, webUrl),
                            err -> sendPanel(ch, key, webUrl)
                        ),
                        err -> sendPanel(ch, key, webUrl)
                    );
                } else {
                    // URL gleich → nur prüfen ob Nachricht noch existiert
                    ch.retrieveMessageById(msgId).queue(
                        msg -> log.info("[Meldeamt] Panel aktiv (ID: {}), kein Neuversand.", msgId),
                        err -> {
                            log.info("[Meldeamt] Panel wurde gelöscht, sende neu.");
                            DataStore.deleteKey(key);
                            sendPanel(ch, key, webUrl);
                        }
                    );
                }
            } else {
                sendPanel(ch, key, webUrl);
            }
        }

        private static void sendPanel(TextChannel ch, String key, String webUrl) {
            ch.sendMessageEmbeds(
                EmbedFactory.create()
                    .setTitle("🏛️ Paradise City Einwohner Meldeamt")
                    .setDescription(
                        "__**Legale Einreise**__\n\n" +
                        "- Ausweis,\n" +
                        "- Zugang zur Staatlichen Jobs,\n" +
                        "- Zugang zur Legalen Routen,\n\n" +
                        "__**Illegale Einreise**__\n\n" +
                        "- Keinen Ausweis,\n" +
                        "- Zugang zur Keinen Staatlichen Jobs,\n" +
                        "- Zugang zur Illegalen Routen,\n\n" +
                        "__**Gruppen Einreise**__\n\n" +
                        "- Ab 4 Personen,\n" +
                        "- Mehr Startgeld,\n" +
                        "- Exklusives Starterfahrzeug")
                    .setTimestamp(Instant.now())
                    .build()
            )
            .addActionRow(Button.link(webUrl, "🏛️ Jetzt Einreisen"))
            .queue(
                msg -> DataStore.writeString(key, msg.getId() + "|" + webUrl),
                err -> log.error("[Meldeamt] Panel konnte nicht gepostet werden.", err)
            );
        }

        private static List<CommandData> buildCommands() {
            return List.of(

                Commands.slash("löschen", "Löscht 1–200 Nachrichten im aktuellen Kanal")
                    .addOption(OptionType.INTEGER, "anzahl",
                        "Anzahl der zu löschenden Nachrichten (1–200)", true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MESSAGE_MANAGE)),

                Commands.slash("bannen", "Bannt ein Mitglied permanent vom Server")
                    .addOption(OptionType.USER,   "mitglied", "Das Mitglied, das gebannt werden soll", true)
                    .addOption(OptionType.STRING,  "grund",    "Grund für den Bann", false)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.BAN_MEMBERS)),

                Commands.slash("entbannen", "Hebt den Bann eines Mitglieds auf")
                    .addOptions(new OptionData(OptionType.STRING, "nutzer",
                        "Gebannter Nutzer (Vorschläge erscheinen beim Tippen)", true, true))
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.BAN_MEMBERS)),

                Commands.slash("timeout", "Gibt einem Mitglied einen Timeout")
                    .addOption(OptionType.USER, "mitglied", "Das Mitglied", true)
                    .addOptions(new OptionData(OptionType.STRING, "dauer",
                        "Dauer des Timeouts", true)
                            .addChoice("5 Minuten",  "5m")
                            .addChoice("10 Minuten", "10m")
                            .addChoice("30 Minuten", "30m")
                            .addChoice("1 Stunde",   "1h")
                            .addChoice("6 Stunden",  "6h")
                            .addChoice("12 Stunden", "12h")
                            .addChoice("1 Tag",      "1d")
                            .addChoice("3 Tage",     "3d")
                            .addChoice("7 Tage",     "7d")
                            .addChoice("14 Tage",    "14d"))
                    .addOption(OptionType.STRING, "grund", "Grund für den Timeout", false)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("ausweis", "Zeigt deinen Personalausweis (nur im Ausweis-Kanal)")
                    .addOptions(new OptionData(OptionType.STRING, "nutzer",
                        "Discord-Nutzername für fremden Ausweis (optional)", false))
                    .setDefaultPermissions(DefaultMemberPermissions.ENABLED),

                Commands.slash("set-einreise", "Sendet das Einwohner-Meldeamt Panel (nur Owner)")
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.ADMINISTRATOR))
            );
        }
    }
}
