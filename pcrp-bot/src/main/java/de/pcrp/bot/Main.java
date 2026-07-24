package de.pcrp.bot;

import de.pcrp.bot.common.*;
import de.pcrp.bot.listeners.*;
import de.pcrp.bot.listeners.PollListener;
import de.pcrp.bot.web.WebServer;
import net.dv8tion.jda.api.*;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.session.ReadyEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.commands.DefaultMemberPermissions;
import net.dv8tion.jda.api.interactions.commands.OptionType;
import net.dv8tion.jda.api.interactions.commands.build.*;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu;
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

        ModerationListener      moderationListener  = new ModerationListener();
        GuildProtectionListener protectionListener  = new GuildProtectionListener();
        WelcomeListener         welcomeListener     = new WelcomeListener();
        TicketListener          ticketListener      = new TicketListener();
        PollListener            pollListener        = new PollListener();
        GiveawayListener        giveawayListener    = new GiveawayListener();
        RoleMenuListener        roleMenuListener    = new RoleMenuListener();

        JDABuilder.createDefault(token)
            .enableIntents(
                GatewayIntent.GUILD_MESSAGES,
                GatewayIntent.MESSAGE_CONTENT,
                GatewayIntent.GUILD_MEMBERS,
                GatewayIntent.GUILD_MODERATION,
                GatewayIntent.GUILD_INVITES,
                GatewayIntent.GUILD_VOICE_STATES,
                GatewayIntent.GUILD_MESSAGE_REACTIONS
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
                welcomeListener,
                ticketListener,
                pollListener,
                giveawayListener,
                roleMenuListener
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

                // Panels einmalig posten (Duplikat-Schutz via DataStore)
                postMeldeamtPanel(guild);

                postSimplePanel(guild, "startpunkt", LoggingConfig.STARTPUNKT_CHANNEL_ID,
                    "🗺️ Startpunkt",
                    "__**Legale Einreise**__\n\n" +
                    "- Startpunkt am Flughafen von Los Angeles\n\n" +
                    "__**Illegale Einreise**__\n\n" +
                    "- Startpunkt am Hafen von Los Angeles");

                postSimplePanel(guild, "starterpaket", LoggingConfig.STARTER_PAKET_CHANNEL_ID,
                    "🎁 Starter Paket",
                    "__**Legale Einreise**__\n\n" +
                    "- 5.000$\n" +
                    "- Declasse Rhapsody\n\n" +
                    "__**Illegale Einreise**__\n\n" +
                    "- 5.000$\n" +
                    "- Karin Kuruma\n\n" +
                    "__**Legale Gruppeneinreise**__\n\n" +
                    "- 10.000$ Pro Person\n" +
                    "- Enus Huntley S 1 Pro Person\n\n" +
                    "__**Illegale Gruppeneinreise**__\n\n" +
                    "- 10.000$ Pro Person\n" +
                    "- Enus Huntley S 1 Pro Person");

                postSimplePanel(guild, "rpeinstellungen", LoggingConfig.RP_EINSTELLUNGEN_CHANNEL_ID,
                    "🎮 RP Spiel Einstellungen",
                    "__**Spieleranzeige**__\n\n" +
                    "- Online\n" +
                    "- Optionen\n" +
                    "- Spieleranzeige auf aus Stellen\n\n" +
                    "__**Minimap**__\n\n" +
                    "- Einstellungen\n" +
                    "- Radar auf aus Stellen");

                postTicketPanel(guild);
                postRegelwerkPanels(guild);
                RoleMenuListener.postPanel(guild);

                postSimplePanel(guild, "fraktionen", LoggingConfig.FRAKTIONSREGELWERK_CHANNEL_ID,
                    "⚔️ Fraktionsregelwerk — Paradise City Roleplay",
                    "Dieses Regelwerk gilt für alle Fraktionen. Jedes Mitglied ist verpflichtet, die folgenden Bestimmungen einzuhalten.\n\n" +
                    "**⚔️ Verhalten**\n" +
                    "`§1` Grundloser Angriff auf Spieler, Beamte oder andere Fraktionen ohne RP-Hintergrund ist untersagt. Unrealistisches Verhalten ist zu unterlassen.\n" +
                    "`§2` Fraktionen dürfen illegale Routen beanspruchen — Klärung und Durchsetzung erfolgt ausschließlich IC.\n" +
                    "`§3` Gambo-Verhalten (nicht RP-basiertes Kampfverhalten) ist untersagt. Verstöße → Fraktionsverwarnung. Wiederholung → Auflösung.\n\n" +
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                    "**🏢 Organisation**\n" +
                    "`§4` Bewerbung vor Gründung erforderlich. Entscheidung liegt bei der Projektleitung. Kein Anspruch auf Genehmigung.\n" +
                    "`§5` Echtnamen sowie Fraktionsnamen anderer Server sind erlaubt.\n" +
                    "`§6` Keine Einschränkungen bei Kleidung, Fahrzeugen oder Immobilien — Nutzung muss im RP erfolgen.\n" +
                    "`§7` Kein festes Mitgliederlimit. Ab 15 Mitgliedern kann eine Aufteilung angeordnet werden.\n\n" +
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                    "**📦 Ressourcen**\n" +
                    "`§8` Keine Fraktionsgüter vom Server. Fahrzeuge, Immobilien, Waffen und Gegenstände werden IC erworben. Ausnahme: Kleidung.\n\n" +
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                    "**⚠️ Sanktionen**\n" +
                    "`§9` Wiederholtes Fehlverhalten → Fraktionsverwarnung. Im Extremfall → Sperre oder Auflösung. Einzelvergehen werden individuell bestraft. Fehlverhalten im Fraktionsnamen kann die gesamte Fraktion sanktionieren.\n" +
                    "`§10` Die Projektleitung behält sich das Recht vor, das Regelwerk jederzeit zu ändern. Änderungen treten sofort in Kraft.");

                postSimplePanel(guild, "safezones", LoggingConfig.SAFEZONES_CHANNEL_ID,
                    "🛡️ Safe Zones — Paradise City Roleplay",
                    "Regierungsgebäude, alle Flächen und Objekte staatlicher Unternehmen sowie Spieler, die sich dort befinden, dürfen weder angegriffen noch entführt werden.\n\n" +
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                    "**⚠️ Ausnahme — PD-Gebäude**\n" +
                    "Wenn ein Überfall geplant ist oder sich ein Fraktionsmitglied in Gewahrsam befindet, darf das betroffene Mitglied befreit werden.\n\n" +
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                    "Verstöße jeglicher Art werden sanktioniert.");
            }

            log.info("Bot bereit – eingeloggt als {}.", jda.getSelfUser().getAsTag());
        }

        private static void postTicketPanel(Guild guild) {
            String key = "panel-ticket-" + guild.getId();
            TextChannel ch = guild.getTextChannelById(LoggingConfig.TICKET_PANEL_CHANNEL_ID);
            if (ch == null) { log.warn("[Ticket] Panel-Kanal nicht gefunden."); return; }

            String stored = DataStore.readString(key);
            if (stored != null && !stored.isBlank()) {
                ch.retrieveMessageById(stored.trim()).queue(
                    msg -> log.info("[Ticket] Panel aktiv (ID: {}), kein Neuversand.", stored.trim()),
                    err -> { DataStore.deleteKey(key); sendTicketPanel(ch, key); }
                );
            } else {
                sendTicketPanel(ch, key);
            }
        }

        private static void sendTicketPanel(TextChannel ch, String key) {
            ch.sendMessageEmbeds(
                EmbedFactory.create()
                    .setTitle("🎫 Ticket System — Paradise City Roleplay")
                    .setDescription(
                        "Wähle unten eine Kategorie aus, um ein Ticket zu erstellen.\n\n" +
                        "**📋 Verfügbare Kategorien**\n\n" +
                        "🔵 **Support** — Allgemeine Fragen & Hilfe\n" +
                        "🔴 **Beschwerde** — Meldung von Regelverstößen\n" +
                        "🟣 **Highteam** — Anliegen an das Highteam\n" +
                        "🟠 **Fraktions Bewerbung** — Bewerbung für eine Fraktion\n" +
                        "⚫ **Team Bewerbung** — Demnächst verfügbar\n\n" +
                        "ℹ️ Pro Person ist nur **1 offenes Ticket** erlaubt.\n" +
                        "Tickets können ausschließlich von Teammitgliedern geschlossen werden.")
                    .build()
            ).addActionRow(
                StringSelectMenu.create(TicketListener.SELECT_ID)
                    .setPlaceholder("Ticket-Kategorie auswählen…")
                    .addOption("Support",              "support",        "Allgemeine Fragen & Hilfe",       net.dv8tion.jda.api.entities.emoji.Emoji.fromUnicode("🔵"))
                    .addOption("Beschwerde",           "beschwerde",     "Meldung von Regelverstößen",      net.dv8tion.jda.api.entities.emoji.Emoji.fromUnicode("🔴"))
                    .addOption("Highteam",             "highteam",       "Anliegen an das Highteam",        net.dv8tion.jda.api.entities.emoji.Emoji.fromUnicode("🟣"))
                    .addOption("Fraktions Bewerbung",  "fraktion",       "Bewerbung für eine Fraktion",     net.dv8tion.jda.api.entities.emoji.Emoji.fromUnicode("🟠"))
                    .addOption("Team Bewerbung",       "team-bewerbung", "Demnächst verfügbar",             net.dv8tion.jda.api.entities.emoji.Emoji.fromUnicode("⚫"))
                    .build()
            ).queue(
                msg -> DataStore.writeString(key, msg.getId()),
                err -> log.error("[Ticket] Panel konnte nicht gepostet werden.", err)
            );
        }

        private static void postRegelwerkPanels(Guild guild) {
            TextChannel ch = guild.getTextChannelById(LoggingConfig.REGELWERK_CHANNEL_ID);
            if (ch == null) { log.warn("[Regelwerk] Panel-Kanal nicht gefunden."); return; }

            String key1 = "panel-regelwerk1-" + guild.getId();
            String key2 = "panel-regelwerk2-" + guild.getId();

            String desc1 =
                "**🔤 RP-Grundlagen & Begriffe**\n\n" +
                "Du übernimmst eine fiktive Rolle in einer realistischen Spielwelt und handelst als dein Charakter — realistisch und glaubwürdig.\n\n" +
                "`IC` — In Character | Alles innerhalb deiner Rolle\n" +
                "`OOC` — Out of Character | Alles außerhalb deines Charakters\n" +
                "`Metagaming` — Externe Infos im RP nutzen → **Verboten**\n" +
                "`PowerRP` — Zwangshandlungen ohne Reaktionsmöglichkeit → **Verboten**\n" +
                "`FearRP` — Angemessenes Angstverhalten bei Gefahr → **Pflicht**\n" +
                "`FailRP` — Unrealistisches Verhalten → **Verboten**\n" +
                "`RDM` — Töten ohne RP-Grund → **Verboten**\n" +
                "`VDM` — Fahrzeug als Waffe → **Verboten**\n" +
                "`Combat Log` — Verlassen einer RP-Situation → **Verboten**\n" +
                "`IC/OOC Mixing` — Vermischung von IC und OOC → **Verboten**\n\n" +
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                "**👤 Einreise & Charakter**\n" +
                "`§1` Discord-ID wird für die Dauer der Aktivität gespeichert.\n" +
                "`§1.1` Keine Whitelist — realistische Angaben Pflicht. Charakteränderung nur durch RP-Tod.\n" +
                "`§1.2` Einreisearten: Legal · Illegal · Gruppeneinreise (ab 5 Personen)\n" +
                "`§1.3` Gruppeneinreise: Nachweis im Support erforderlich.\n" +
                "`§1.4` Zweitcharaktere: Nur mit Support-Anmeldung erlaubt.\n\n" +
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                "**🤝 Verhalten auf dem Server**\n" +
                "`§2` Respekt ist Pflicht. Diskriminierung und Beleidigungen sind verboten.\n" +
                "`§2.1` Keine Werbung · keine Serverlinks · kein Spam.\n" +
                "`§2.2` Kein privater Kontakt zu Teammitgliedern.\n" +
                "`§2.3` Support: richtige Kategorie nutzen, kein Spam, Geduld zeigen.\n" +
                "`§2.4` Griefing und Sabotage sind verboten.\n\n" +
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                "**🎫 Support & Systeme**\n" +
                "`§3` Nur über Tickets oder Supportbereiche erreichbar.\n" +
                "`§3.1` Ingame-Support nur bei Team-Genehmigung — ausschließlich in einem CO.\n" +
                "`§3.2` Clips dürfen ausschließlich im Support verwendet werden.\n" +
                "`§3.3` Verwarnungen sind anfechtbar — Einspruch ist möglich.\n\n" +
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                "**🔒 Serversicherheit**\n" +
                "`§4` Bugs, Glitches und Exploits sind streng verboten.\n" +
                "`§4.1` Bot-Fehler sofort melden — Nutzung ist verboten.\n" +
                "`§4.2` Serverangriffe führen zum sofortigen Ausschluss.\n\n" +
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                "**📡 Kommunikation & UI**\n" +
                "`§5` Ausschließlich GTA-Ingame-Voice erlaubt.\n" +
                "`§5.1` Funk erlaubt, solange die Lobby nicht voll ist — bei voller Lobby auflösen.\n" +
                "`§5.2` Minimap & Spieleranzeige beim Betreten der Lobby deaktivieren.\n\n" +
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                "**🎮 Ingame-Regeln**\n" +
                "`§6` Alles muss realistisch gespielt werden.\n" +
                "`§6.1` Schusscall: Pflicht — 15 Minuten gültig.\n" +
                "`§6.2` Bewusstlosigkeit: maximal 10 Minuten.\n" +
                "`§6.3` Bewusstlosen Spieler: Dispatch absetzen oder Erstversorgung durchführen.\n" +
                "`§6.4` RP-Tod: Der Charakter verliert alle Items.";

            String desc2 =
                "**🎒 Inventar & Besitzsystem**\n" +
                "`§7` Nur verwenden, was im RP besessen wird.\n" +
                "`§7.1` Fahrzeuge müssen im RP erworben sein — Fahrzeugdiebstahl verboten.\n" +
                "`§7.2` Nur eigene Waffen und Items erlaubt.\n" +
                "`§7.3` Items im Lager dürfen nicht verwendet werden.\n" +
                "`§7.4` Immobilien nur mit RP-Besitz nutzbar.\n" +
                "`§7.5` Items anderer Spieler ohne RP-Hintergrund zu entwenden ist verboten und wird verwarnt.\n\n" +
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                "**🚔 Polizei & Medizin**\n" +
                "`§8` Kein grundloser Angriff auf die Polizei (PD).\n" +
                "`§8.1` Der Medizinische Dienst (MD) darf nicht ausgeraubt oder entführt werden.\n\n" +
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                "**💰 Wirtschaft & Aktivitäten**\n" +
                "`§9` Farmen nur nach Vorgabe erlaubt.\n" +
                "`§9.1` Minijobs: nur eine Aktivität gleichzeitig erlaubt.\n" +
                "`§9.2` Raubüberfälle: geltende Regeln sind einzuhalten.\n" +
                "`§9.3` Safezones: keine Gewalt erlaubt.";

            // Part 1
            String stored1 = DataStore.readString(key1);
            if (stored1 != null && !stored1.isBlank()) {
                ch.retrieveMessageById(stored1.trim()).queue(
                    msg -> log.info("[Regelwerk] Teil 1 aktiv (ID: {}), kein Neuversand.", stored1.trim()),
                    err -> { DataStore.deleteKey(key1); sendSimplePanel(ch, key1, "📋 Paradise City — Serverregelwerk (1/2)", desc1); }
                );
            } else {
                sendSimplePanel(ch, key1, "📋 Paradise City — Serverregelwerk (1/2)", desc1);
            }

            // Part 2
            String stored2 = DataStore.readString(key2);
            if (stored2 != null && !stored2.isBlank()) {
                ch.retrieveMessageById(stored2.trim()).queue(
                    msg -> log.info("[Regelwerk] Teil 2 aktiv (ID: {}), kein Neuversand.", stored2.trim()),
                    err -> { DataStore.deleteKey(key2); sendSimplePanel(ch, key2, "📋 Paradise City — Serverregelwerk (2/2)", desc2); }
                );
            } else {
                sendSimplePanel(ch, key2, "📋 Paradise City — Serverregelwerk (2/2)", desc2);
            }
        }

        private static void postMeldeamtPanel(Guild guild) {
            String key    = "panel-meldeamt-" + guild.getId();
            String webUrl = normalizeUrl(System.getenv().getOrDefault("WEB_URL", "https://example.com"));

            TextChannel ch = guild.getTextChannelById(LoggingConfig.MELDEAMT_CHANNEL_ID);
            if (ch == null) { log.warn("[Meldeamt] Panel-Kanal nicht gefunden."); return; }

            String stored    = DataStore.readString(key);
            String storedMsgId = null;
            if (stored != null && stored.contains("|")) {
                storedMsgId = stored.split("\\|", 2)[0];
            } else if (stored != null && !stored.isBlank()) {
                storedMsgId = stored.trim();
            }

            if (storedMsgId != null) {
                final String msgId = storedMsgId;
                ch.retrieveMessageById(msgId).queue(
                    msg -> {
                        log.info("[Meldeamt] Altes Panel gefunden (ID: {}), lösche und sende neu.", msgId);
                        msg.delete().queue(
                            v -> { DataStore.deleteKey(key); sendPanel(ch, key, webUrl); },
                            err -> { DataStore.deleteKey(key); sendPanel(ch, key, webUrl); }
                        );
                    },
                    err -> {
                        log.info("[Meldeamt] Panel wurde gelöscht, sende neu.");
                        DataStore.deleteKey(key);
                        sendPanel(ch, key, webUrl);
                    }
                );
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
                        "- Ab 5 Personen,\n" +
                        "- Mehr Startgeld,\n" +
                        "- Exklusives Starterfahrzeug")

                    .build()
            )
            .addActionRow(Button.link(webUrl, "🏛️ Jetzt Einreisen"))
            .queue(
                msg -> DataStore.writeString(key, msg.getId() + "|" + webUrl),
                err -> log.error("[Meldeamt] Panel konnte nicht gepostet werden.", err)
            );
        }

        private static void postSimplePanel(Guild guild, String panelKey, long channelId,
                                             String title, String description) {
            String key = "panel-" + panelKey + "-" + guild.getId();
            TextChannel ch = guild.getTextChannelById(channelId);
            if (ch == null) { log.warn("[Panel] Kanal für '{}' nicht gefunden.", panelKey); return; }

            String stored = DataStore.readString(key);
            if (stored != null && !stored.isBlank()) {
                ch.retrieveMessageById(stored.trim()).queue(
                    msg -> log.info("[Panel] '{}' aktiv (ID: {}), kein Neuversand.", panelKey, stored.trim()),
                    err -> {
                        DataStore.deleteKey(key);
                        sendSimplePanel(ch, key, title, description);
                    }
                );
            } else {
                sendSimplePanel(ch, key, title, description);
            }
        }

        private static void sendSimplePanel(TextChannel ch, String key, String title, String description) {
            ch.sendMessageEmbeds(
                EmbedFactory.create()
                    .setTitle(title)
                    .setDescription(description)

                    .build()
            ).queue(
                msg -> DataStore.writeString(key, msg.getId()),
                err -> log.error("[Panel] '{}' konnte nicht gesendet werden.", key, err)
            );
        }

        private static String normalizeUrl(String url) {
            if (url == null || url.isBlank()) return "https://example.com";
            url = url.trim();
            if (!url.startsWith("http://") && !url.startsWith("https://")) {
                url = "https://" + url;
            }
            return url;
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

                Commands.slash("abstimmung", "Erstellt eine Abstimmung im Abstimmungs-Kanal")
                    .addOption(OptionType.STRING, "titel", "Titel der Abstimmung",             true)
                    .addOption(OptionType.STRING, "text",  "Beschreibungstext der Abstimmung", true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MESSAGE_MANAGE)),

                Commands.slash("aktivitätscheck", "Sendet einen Aktivitätscheck in den zugehörigen Kanal")
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MESSAGE_MANAGE)),

                Commands.slash("event", "Sendet ein Event-Embed in den Event-Kanal")
                    .addOption(OptionType.STRING, "was",          "Name / Titel des Events",        true)
                    .addOption(OptionType.STRING, "beschreibung", "Beschreibung des Events",        true)
                    .addOption(OptionType.STRING, "wo",           "Wo findet das Event statt?",     true)
                    .addOption(OptionType.STRING, "wann",         "Wann beginnt das Event?",        true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MESSAGE_MANAGE)),

                Commands.slash("verwarnung", "Gibt einem Mitglied eine Verwarnung")
                    .addOption(OptionType.USER,   "mitglied",    "Das Mitglied, das verwarnt werden soll", true)
                    .addOption(OptionType.STRING,  "grund",       "Grund der Verwarnung",                   true)
                    .addOption(OptionType.STRING,  "konsequenz",  "Konsequenz / Maßnahme",                  true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("verwarn-liste", "Zeigt alle Verwarnungen eines Mitglieds")
                    .addOption(OptionType.USER, "mitglied", "Das Mitglied", true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("verwarnung-löschen", "Entfernt eine Verwarnung von einem Mitglied")
                    .addOption(OptionType.USER, "mitglied", "Das Mitglied", true)
                    .addOptions(new OptionData(OptionType.STRING, "warn-id",
                        "Welche Verwarnung soll entfernt werden?", true, true))
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("gewinnspiel", "Startet ein Gewinnspiel im Gewinnspiel-Kanal")
                    .addOption(OptionType.STRING, "titel", "Titel des Gewinnspiels",          true)
                    .addOption(OptionType.STRING, "was",   "Was kann man gewinnen?",           true)
                    .addOptions(new OptionData(OptionType.STRING, "dauer", "Dauer des Gewinnspiels", true)
                        .addChoice("10 Minuten",  "10m")
                        .addChoice("30 Minuten",  "30m")
                        .addChoice("1 Stunde",    "1h")
                        .addChoice("6 Stunden",   "6h")
                        .addChoice("12 Stunden",  "12h")
                        .addChoice("1 Tag",       "1d")
                        .addChoice("3 Tage",      "3d")
                        .addChoice("7 Tage",      "7d"))
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MESSAGE_MANAGE))

            );
        }
    }
}
