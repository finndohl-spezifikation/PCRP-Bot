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
import java.util.stream.Collectors;

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

        // Lotto-Scheduler starten (zieht täglich um 12:00 Uhr)
        new LottoScheduler().start();

        // Handy-Abrechnungs-Scheduler (monatlich 1.000$)
        new PhoneScheduler().start();

        ModerationListener      moderationListener  = new ModerationListener();
        GuildProtectionListener protectionListener  = new GuildProtectionListener();
        WelcomeListener         welcomeListener     = new WelcomeListener();
        TicketListener          ticketListener      = new TicketListener();
        PollListener            pollListener        = new PollListener();
        GiveawayListener        giveawayListener    = new GiveawayListener();
        RoleMenuListener        roleMenuListener    = new RoleMenuListener();
        BoostListener           boostListener       = new BoostListener();

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
                roleMenuListener,
                boostListener,
                new VorschlagListener(),
                new CounterListener(),
                new LobbyListener(),
                new RucksackListener(),
                new LottoListener(),
                new RubbellosListener(),
                new ShopListener(),
                new BankListener(),
                new BargeldListener(),
                new HandyCentraleListener(),
                new FirmaLinkListener()
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
            de.pcrp.bot.web.PushService.init();

            // Globale Commands entfernen (kein 1h-Delay)
            jda.updateCommands().queue();

            List<CommandData> commands = buildCommands();
            BotStats.commandCount = commands.size();
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
                postBoostPanel(guild);
                postFrakListPanel(guild);
                postRucksackPanel(guild);
                postLottoPanel(guild);
                postRubbellosPanel(guild);
                ShopListener.postPanelIfNeeded(guild);
                BankListener.postPanelIfNeeded(guild);
                HandyCentraleListener.postPanel(guild);
                initShopItems(guild);

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
            PanelHelper.post(ch, key, "🎫 Ticket System — Paradise City Roleplay",
                () -> sendTicketPanel(ch, key));
        }

        private static void sendTicketPanel(TextChannel ch, String key) {
            ch.sendMessageEmbeds(
                EmbedFactory.create()
                    .setTitle("🎫 Ticket System — Paradise City Roleplay")
                    .setDescription(
                        "Wähle unten eine Kategorie aus, um ein Ticket zu erstellen.\n\n" +
                        "**📋 Verfügbare Kategorien**\n\n" +
                        "- **Support** — Allgemeine Fragen & Hilfe\n" +
                        "- **Beschwerde** — Meldung von Regelverstößen\n" +
                        "- **Highteam** — Anliegen an das Highteam\n" +
                        "- **Fraktions Bewerbung** — Bewerbung für eine Fraktion\n" +
                        "- **Team Bewerbung** — Demnächst verfügbar")
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
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Ticket] Panel konnte nicht gepostet werden.", err); PanelHelper.onFailed(key); }
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

            PanelHelper.post(ch, key1, "📋 Paradise City — Serverregelwerk (1/2)",
                () -> sendSimplePanel(ch, key1, "📋 Paradise City — Serverregelwerk (1/2)", desc1));
            PanelHelper.post(ch, key2, "📋 Paradise City — Serverregelwerk (2/2)",
                () -> sendSimplePanel(ch, key2, "📋 Paradise City — Serverregelwerk (2/2)", desc2));
        }

        private static void postMeldeamtPanel(Guild guild) {
            String key    = "panel-meldeamt-v3-" + guild.getId();
            String webUrl = "https://dashboards.paradisecity-roleplay-85a.workers.dev";
            TextChannel ch = guild.getTextChannelById(LoggingConfig.MELDEAMT_CHANNEL_ID);
            if (ch == null) { log.warn("[Meldeamt] Panel-Kanal nicht gefunden."); return; }
            PanelHelper.post(ch, key, "🏛️ Paradise City Einwohner Meldeamt",
                () -> sendMeldeamtPanel(ch, key, webUrl));
        }

        private static void sendMeldeamtPanel(TextChannel ch, String key, String webUrl) {
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
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Meldeamt] Panel konnte nicht gepostet werden.", err); PanelHelper.onFailed(key); }
            );
        }

        private static void postSimplePanel(Guild guild, String panelKey, long channelId,
                                             String title, String description) {
            String key = "panel-" + panelKey + "-" + guild.getId();
            TextChannel ch = guild.getTextChannelById(channelId);
            if (ch == null) { log.warn("[Panel] Kanal für '{}' nicht gefunden.", panelKey); return; }
            PanelHelper.post(ch, key, title, () -> sendSimplePanel(ch, key, title, description));
        }

        private static void sendSimplePanel(TextChannel ch, String key, String title, String description) {
            ch.sendMessageEmbeds(
                EmbedFactory.create()
                    .setTitle(title)
                    .setDescription(description)
                    .build()
            ).queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Panel] '{}' konnte nicht gesendet werden.", key, err); PanelHelper.onFailed(key); }
            );
        }

        // ── Boost-Belohnungen Panel ─────────────────────────────────────────────

        private static void postBoostPanel(Guild guild) {
            String key = "panel-boost-" + guild.getId();
            TextChannel ch = guild.getTextChannelById(LoggingConfig.BOOST_CHANNEL_ID);
            if (ch == null) { log.warn("[Boost] Kanal nicht gefunden."); return; }
            PanelHelper.post(ch, key, "🚀 Server Boost Belohnungen — Paradise City Roleplay",
                () -> sendBoostPanel(ch, key));
        }

        private static void sendBoostPanel(TextChannel ch, String key) {
            ch.sendMessageEmbeds(EmbedFactory.create()
                .setTitle("🚀 Server Boost Belohnungen — Paradise City Roleplay")
                .setDescription(
                    "Unterstütze den Server mit einem Boost und erhalte eine Belohnung!\n\n" +
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +
                    "💜 **Pro Boost**\n" +
                    "→ 5.000 $ pro Boost\n\n" +
                    "🔶 **Ab 5 Server-Boosts**\n" +
                    "→ 10.000 $ pro Boost\n\n" +
                    "🔷 **Ab 10 Server-Boosts**\n" +
                    "→ 100.000 $ pro Boost")
                .build()
            ).queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Boost] Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
        }

        // ── Fraktions-Liste Panel ───────────────────────────────────────────────

        private static void postLottoPanel(Guild guild) {
            String key = "panel-lotto-v7-" + guild.getId();
            TextChannel ch = guild.getTextChannelById(LoggingConfig.LOTTO_CHANNEL_ID);
            if (ch == null) { log.warn("[Lotto] Panel-Kanal nicht gefunden."); return; }
            PanelHelper.post(ch, key, "🎰 Paradise City Lotto",
                () -> sendLottoPanel(ch, key, guild));
        }

        private static void sendLottoPanel(TextChannel ch, String key, Guild guild) {
            String webUrl = "https://dashboards.paradisecity-roleplay-85a.workers.dev";
            int jackpot = LottoManager.getCurrentJackpot(guild.getId());
            ch.sendMessageEmbeds(EmbedFactory.build(
                "🎰 Paradise City Lotto",
                "**Heutiger Jackpot: " + LottoManager.formatAmount(jackpot) + "**\n\n" +
                "Kaufe einen Lottoschein und löse ihn täglich ein.\n" +
                "Die Ziehung findet jeden Tag um **12:00 Uhr** statt.\n\n" +
                "💰 Gewinne: **100.000$ – 3.000.000$**\n" +
                "🎟️ Pro Ziehung wird **1 Lottoschein** eingelöst."))
                .addActionRow(
                    Button.primary("lotto-get-link", "🎟️ Lottoschein abgeben"))
                .queue(
                    msg -> PanelHelper.onSent(key, msg.getId()),
                    err -> { log.error("[Lotto] Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
        }

        private static void postRubbellosPanel(Guild guild) {
            String key = "panel-rubbellos-v5-" + guild.getId();
            TextChannel ch = guild.getTextChannelById(LoggingConfig.RUBBELLOS_CHANNEL_ID);
            if (ch == null) { log.warn("[Rubbellos] Kanal nicht gefunden."); return; }
            PanelHelper.post(ch, key, "🎰 Goldene 7 – Rubbellos",
                () -> sendRubbellosPanel(ch, key));
        }

        private static void sendRubbellosPanel(TextChannel ch, String key) {
            ch.sendMessageEmbeds(EmbedFactory.build(
                "🎰 Goldene 7 – Rubbellos",
                "Kaufe ein **Rubbellos** und versuche dein Glück!\n\n" +
                "Rubbele alle **3 Felder** frei — findest du drei gleiche Beträge, gewinnst du!\n\n" +
                "💰 Gewinne: **Niete bis 30.000$**\n" +
                "🎟️ Pro Rubbellos wird **1 Los** aus deinem Rucksack eingelöst."))
                .addActionRow(Button.primary("rubbellos-scratch", "🎰 Rubbellos spielen"))
                .queue(
                    msg -> PanelHelper.onSent(key, msg.getId()),
                    err -> { log.error("[Rubbellos] Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
        }

        private static void postRucksackPanel(Guild guild) {
            String key = "panel-rucksack-" + guild.getId();
            TextChannel ch = guild.getTextChannelById(LoggingConfig.RUCKSACK_CHANNEL_ID);
            if (ch == null) { log.warn("[Rucksack] Kanal nicht gefunden."); return; }
            PanelHelper.post(ch, key, "🎒 Rucksack", () -> sendRucksackPanel(ch, key));
        }

        private static void sendRucksackPanel(TextChannel ch, String key) {
            ch.sendMessageEmbeds(EmbedFactory.build(
                "🎒 Rucksack",
                "Hier kannst du deinen Rucksack öffnen und dein Inventar einsehen.\n\n" +
                "Über **Anderen Rucksack Öffnen** kannst du das Inventar anderer Spieler einsehen."))
                .addActionRow(
                    Button.primary("rucksack-open",  "🎒 Rucksack Öffnen"),
                    Button.secondary("rucksack-other", "🔍 Anderen Rucksack Öffnen"))
                .queue(
                    msg -> PanelHelper.onSent(key, msg.getId()),
                    err -> { log.error("[Rucksack] Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
        }

        private static void postFrakListPanel(Guild guild) {
            TextChannel ch = guild.getTextChannelById(LoggingConfig.FRAK_LIST_CHANNEL_ID);
            if (ch == null) { log.warn("[FrakList] Kanal nicht gefunden."); return; }
            String msgId = de.pcrp.bot.common.FraktionManager.getPanelMsgId(guild.getId());
            if (msgId != null && !msgId.isBlank()) {
                // Nachricht noch vorhanden → nur Embed aktualisieren, kein Neuversand
                ch.retrieveMessageById(msgId.trim()).queue(
                    existing -> de.pcrp.bot.common.FraktionManager.updatePanelEmbed(guild),
                    err      -> sendFrakListPanel(ch, guild)  // Nachricht weg → neu senden
                );
            } else {
                sendFrakListPanel(ch, guild);
            }
        }

        private static void sendFrakListPanel(TextChannel ch, Guild guild) {
            ch.sendMessageEmbeds(de.pcrp.bot.common.FraktionManager.buildFrakEmbed(guild.getId()))
                .queue(
                    msg -> de.pcrp.bot.common.FraktionManager.setPanelMsgId(guild.getId(), msg.getId()),
                    err -> log.error("[FrakList] Panel konnte nicht gesendet werden.", err));
        }

        // ── Shop-Items Einmal-Initialisierung ──────────────────────────────────

        private static void initShopItems(Guild guild) {
            String guildId = guild.getId();
            List<ShopManager.ShopItem> items =
                ShopManager.getItemsForShop(guildId, ShopListener.SHOP_KWIKE);

            boolean hasRubbellos   = items.stream().anyMatch(it -> InventoryManager.nameMatches(it.name, "Rubbellos"));
            boolean hasLottoschein = items.stream().anyMatch(it -> InventoryManager.nameMatches(it.name, "Lottoschein"));

            if (!hasRubbellos) {
                ShopManager.addItem(guildId, "🎫 | Rubbellos",   2500, ShopListener.SHOP_KWIKE);
                log.info("[Init] '🎫 | Rubbellos' (2500$) zum Kwik-E-Markt hinzugefügt.");
            }
            if (!hasLottoschein) {
                ShopManager.addItem(guildId, "🎫 | Lottoschein", 3200, ShopListener.SHOP_KWIKE);
                log.info("[Init] '🎫 | Lottoschein' (3200$) zum Kwik-E-Markt hinzugefügt.");
            }
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
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MESSAGE_MANAGE)),

                Commands.slash("einreise-sperre", "Aktiviert den Einreise-Stopp")
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("einreise-entsperren", "Hebt den Einreise-Stopp wieder auf")
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("frak-erstellen", "Erstellt eine neue Fraktion in der Fraktions-Liste")
                    .addOption(OptionType.STRING, "fraktion", "Name der neuen Fraktion", true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("frak-löschen", "Entfernt eine Fraktion aus der Fraktions-Liste")
                    .addOption(OptionType.STRING, "fraktion", "Name der Fraktion", true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("frakwarn", "Gibt einer Fraktion eine Verwarnung")
                    .addOptions(new OptionData(OptionType.STRING, "fraktion",   "Name der Fraktion",  true, true))
                    .addOption(OptionType.STRING, "grund",      "Grund",              true)
                    .addOption(OptionType.STRING, "konsequenz", "Konsequenz",         true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("frakwarn-entfernen", "Entfernt alle Verwarnungen einer Fraktion")
                    .addOptions(new OptionData(OptionType.STRING, "fraktion", "Name der Fraktion", true, true))
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("frak-sperren", "Sperrt eine Fraktion direkt")
                    .addOptions(new OptionData(OptionType.STRING, "fraktion", "Name der Fraktion", true, true))
                    .addOption(OptionType.STRING, "grund",    "Grund der Sperre",  true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("frak-entsperren", "Entsperrt eine gesperrte Fraktion")
                    .addOptions(new OptionData(OptionType.STRING, "fraktion", "Name der Fraktion", true, true))
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("item-geben", "Gibt einem Spieler ein Item")
                    .addOption(OptionType.USER,    "mitglied", "Das Mitglied", true)
                    .addOptions(new OptionData(OptionType.STRING, "item", "Item-Name", true, true))
                    .addOption(OptionType.INTEGER,  "menge",    "Menge",        true)
                    .setDefaultPermissions(DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("item-erstellen", "Erstellt einen neuen Artikel in einem Shop")
                    .addOption(OptionType.STRING,  "name",   "Artikelname",                      true)
                    .addOption(OptionType.INTEGER, "preis",  "Preis in $",                       true)
                    .addOptions(new OptionData(OptionType.STRING, "shop", "Shop", true)
                        .addChoice("Kwik-E-Markt", "kwik-e-markt"))
                    .setDefaultPermissions(DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("item-bearbeiten", "Bearbeitet einen bestehenden Artikel")
                    .addOptions(new OptionData(OptionType.STRING, "item", "Artikel auswählen", true, true))
                    .addOption(OptionType.STRING,  "neuer-name",  "Neuer Artikelname (optional)",  false)
                    .addOption(OptionType.INTEGER, "neuer-preis", "Neuer Preis in $ (optional)",    false)
                    .addOptions(new OptionData(OptionType.STRING, "neuer-shop", "Neuer Shop (optional)", false)
                        .addChoice("Kwik-E-Markt", "kwik-e-markt"))
                    .setDefaultPermissions(DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("item-löschen", "Löscht einen Artikel aus einem Shop")
                    .addOptions(new OptionData(OptionType.STRING, "item", "Artikel auswählen", true, true))
                    .setDefaultPermissions(DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("item-entnehmen", "Entfernt ein Item aus dem Inventar eines Spielers")
                    .addOption(OptionType.USER,   "mitglied", "Das Mitglied",                    true)
                    .addOptions(new OptionData(OptionType.STRING, "item", "Item-Name", true, true))
                    .addOption(OptionType.INTEGER, "menge",   "Menge",                            true)
                    .setDefaultPermissions(DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("geld-geben", "Gibt einem Spieler Bargeld oder Kontogeld")
                    .addOption(OptionType.USER,    "mitglied", "Das Mitglied", true)
                    .addOptions(new OptionData(OptionType.STRING, "typ", "Geldart", true)
                        .addChoice("Bargeld",   "bargeld")
                        .addChoice("Kontogeld", "kontogeld"))
                    .addOption(OptionType.INTEGER, "betrag", "Betrag in $",    true)
                    .setDefaultPermissions(DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("geld-entfernen", "Entfernt Bargeld oder Kontogeld von einem Spieler")
                    .addOption(OptionType.USER,    "mitglied", "Das Mitglied", true)
                    .addOptions(new OptionData(OptionType.STRING, "typ", "Geldart", true)
                        .addChoice("Bargeld",   "bargeld")
                        .addChoice("Kontogeld", "kontogeld"))
                    .addOption(OptionType.INTEGER, "betrag", "Betrag in $",    true)
                    .setDefaultPermissions(DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("bargeld", "Barbestand anzeigen")
                    .addOption(OptionType.USER, "mitglied", "Spieler (optional — nur für Admins)", false),

                Commands.slash("lobby-abstimmung", "Startet eine Lobby-Abstimmung")
                    .addOption(OptionType.STRING, "uhrzeit", "RP-Startzeit (z. B. 20:00 Uhr)", true),
                Commands.slash("lobby-öffnen", "Öffnet die Lobby und benachrichtigt die Community")
                    .addOption(OptionType.STRING, "lobbyhost", "Name des Lobby Hosts", true),
                Commands.slash("lobby-schließen", "Schließt die Lobby und benachrichtigt die Community")
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("vorschlag", "Erstellt einen Vorschlag (nur im Vorschlag-Kanal)")
                    .addOption(OptionType.STRING, "titel",       "Titel des Vorschlags",       true)
                    .addOption(OptionType.STRING, "beschreibung","Beschreibung des Vorschlags", true),

                Commands.slash("vorschlag-annehmen", "Nimmt einen aktiven Vorschlag an")
                    .addOptions(new OptionData(OptionType.STRING, "vorschlag", "Vorschlag auswählen", true, true))
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("vorschlag-ablehnen", "Lehnt einen aktiven Vorschlag ab")
                    .addOptions(new OptionData(OptionType.STRING, "vorschlag", "Vorschlag auswählen", true, true))
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS)),

                Commands.slash("bannen-dashboard", "Sperrt ein Mitglied von allen PCRP-Webseiten")
                    .addOption(OptionType.USER, "mitglied", "Das Mitglied", true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.BAN_MEMBERS)),

                Commands.slash("entbannen-dashboard", "Hebt den Web-Bann eines Mitglieds auf")
                    .addOption(OptionType.USER, "mitglied", "Das Mitglied", true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.BAN_MEMBERS)),

                Commands.slash("bewohner-information", "Sendet eine Regierungs-Nachricht an alle City-Chat-Nutzer")
                    .addOption(OptionType.STRING, "nachricht", "Inhalt der Nachricht (max. 500 Zeichen)", true)
                    .setDefaultPermissions(
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS))

            );
        }
    }
}
