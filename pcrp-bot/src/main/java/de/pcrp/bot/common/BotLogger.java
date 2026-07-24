package de.pcrp.bot.common;

import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.MessageEmbed;
import net.dv8tion.jda.api.entities.User;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.utils.messages.MessageCreateData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.EnumSet;

import net.dv8tion.jda.api.entities.Message;

/**
 * Statische Hilfsmethoden zum Schreiben in die Log-Kanäle und zum Senden von
 * Aktivitätswarnungen. Wird von allen Listenern genutzt.
 */
public final class BotLogger {

    private static final Logger log = LoggerFactory.getLogger(BotLogger.class);

    private BotLogger() {}

    /** Schreibt ein Embed in einen bestimmten Log-Kanal. Fehler werden stillschweigend ignoriert. */
    public static void log(Guild guild, long channelId, MessageEmbed embed) {
        TextChannel ch = guild.getTextChannelById(channelId);
        if (ch != null) ch.sendMessageEmbeds(embed).queue(null, err -> {});
    }

    /** Schreibt einen Eintrag in den Moderations-Log-Kanal. */
    public static void logModeration(Guild guild, String title, String description) {
        log(guild, LoggingConfig.MODERATION_LOG_CHANNEL_ID, EmbedFactory.build(title, description));
    }

    /**
     * Sendet eine Aktivitätswarnung in den konfigurierten Alert-Kanal
     * und pingt den Inhaber.
     */
    public static void sendAlert(Guild guild, String title, String description) {
        TextChannel ch = guild.getTextChannelById(ModerationConfig.ALERT_CHANNEL_ID);
        if (ch == null) return;
        ch.sendMessage(ModerationConfig.ownerMention())
            .setEmbeds(EmbedFactory.build(title, description))
            .setAllowedMentions(EnumSet.of(Message.MentionType.USER))
            .queue(null, err -> {});
    }

    /**
     * Versucht, einem Nutzer eine DM zu schicken.
     * Schlägt fehl wenn der Nutzer DMs von Servermitgliedern deaktiviert hat.
     */
    public static void tryDm(User user, MessageEmbed embed) {
        user.openPrivateChannel().queue(
            ch -> ch.sendMessageEmbeds(embed).queue(
                null,
                err -> log.warn("[DM] Nachricht an {} ({}) konnte nicht gesendet werden: {}",
                    user.getName(), user.getId(), err.getMessage())
            ),
            err -> log.warn("[DM] Privat-Kanal zu {} ({}) konnte nicht geöffnet werden: {}",
                user.getName(), user.getId(), err.getMessage())
        );
    }
}
