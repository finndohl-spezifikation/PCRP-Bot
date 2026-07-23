package de.pcrp.bot;

import de.pcrp.bot.listeners.*;
import net.dv8tion.jda.api.*;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.events.session.ReadyEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.commands.DefaultMemberPermissions;
import net.dv8tion.jda.api.interactions.commands.OptionType;
import net.dv8tion.jda.api.interactions.commands.build.*;
import net.dv8tion.jda.api.requests.GatewayIntent;
import net.dv8tion.jda.api.utils.ChunkingFilter;
import net.dv8tion.jda.api.utils.MemberCachePolicy;
import net.dv8tion.jda.api.utils.cache.CacheFlag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

public class Main {

    private static final Logger log = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args) throws Exception {
        String token = System.getenv("DISCORD_TOKEN");
        if (token == null || token.isBlank()) {
            log.error("DISCORD_TOKEN ist nicht gesetzt. Bot kann nicht starten.");
            System.exit(1);
        }

        ModerationListener moderationListener = new ModerationListener();
        GuildProtectionListener protectionListener = new GuildProtectionListener();
        WelcomeListener welcomeListener = new WelcomeListener();

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

    // ─── Startup: globale Commands löschen + Server-Commands sofort registrieren ─

    public static class StartupListener extends ListenerAdapter {

        private static final Logger log = LoggerFactory.getLogger(StartupListener.class);

        @Override
        public void onReady(ReadyEvent event) {
            JDA jda = event.getJDA();

            // Alle globalen Commands entfernen (verhindert Doppelungen)
            jda.updateCommands().queue();

            // Slash-Commands definieren
            List<CommandData> commands = buildCommands();

            // Server-spezifisch registrieren → sofort sichtbar, kein 1-Stunden-Delay
            for (Guild guild : jda.getGuilds()) {
                guild.updateCommands()
                    .addCommands(commands)
                    .queue(
                        ok  -> log.info("Commands auf '{}' registriert.", guild.getName()),
                        err -> log.error("Fehler beim Registrieren auf '{}'.", guild.getName(), err)
                    );
            }

            log.info("Bot bereit – eingeloggt als {}.", jda.getSelfUser().getAsTag());
        }

        private List<CommandData> buildCommands() {
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
                        DefaultMemberPermissions.enabledFor(net.dv8tion.jda.api.Permission.MODERATE_MEMBERS))
            );
        }
    }
}
