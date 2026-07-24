package de.pcrp.bot.listeners;

import de.pcrp.bot.common.LobbyManager;
import de.pcrp.bot.common.LoggingConfig;
import net.dv8tion.jda.api.entities.emoji.Emoji;
import net.dv8tion.jda.api.events.message.react.MessageReactionAddEvent;
import net.dv8tion.jda.api.events.message.react.MessageReactionRemoveEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LobbyListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(LobbyListener.class);

    @Override
    public void onMessageReactionAdd(MessageReactionAddEvent event) {
        if (!event.isFromGuild()) return;
        if (event.getUser() == null || event.getUser().isBot()) return;
        if (event.getChannel().getIdLong() != LoggingConfig.LOBBY_ABSTIMMUNG_CHANNEL_ID) return;

        String emoji     = event.getEmoji().getName();
        String messageId = event.getMessageId();
        String userId    = event.getUserId();

        // Keine bekannte Lobby-Nachricht → ignorieren
        if (!LobbyManager.isLobbyMessage(messageId)) return;

        // Nicht erlaubte Reaction entfernen
        if (!LobbyManager.EMOJIS.contains(emoji)) {
            event.getReaction().removeReaction(event.getUser()).queue(null, e -> {});
            return;
        }

        String oldEmoji = LobbyManager.setVote(messageId, userId, emoji);

        if (oldEmoji != null && !oldEmoji.equals(emoji)) {
            // Alten Vote-Reaction via Message-Objekt entfernen (einzige JDA5-API dafür)
            final String toRemove = oldEmoji;
            event.getChannel().retrieveMessageById(messageId).queue(msg -> {
                msg.removeReaction(Emoji.fromUnicode(toRemove), event.getUser())
                    .queue(null, e -> {});
                msg.editMessageEmbeds(LobbyManager.buildEmbed(messageId))
                    .queue(null, e -> log.warn("[Lobby] Embed-Update fehlgeschlagen: {}", e.getMessage()));
            }, e -> {});
        } else {
            updateEmbed(event, messageId);
        }
    }

    @Override
    public void onMessageReactionRemove(MessageReactionRemoveEvent event) {
        if (!event.isFromGuild()) return;
        if (event.getChannel().getIdLong() != LoggingConfig.LOBBY_ABSTIMMUNG_CHANNEL_ID) return;

        String emoji     = event.getEmoji().getName();
        String messageId = event.getMessageId();
        String userId    = event.getUserId();

        if (!LobbyManager.isLobbyMessage(messageId)) return;
        if (!LobbyManager.EMOJIS.contains(emoji)) return;

        // Nur entfernen wenn aktueller Vote
        String current = LobbyManager.getCurrentVote(messageId, userId);
        if (emoji.equals(current)) {
            LobbyManager.removeVote(messageId, userId);
            event.getChannel().editMessageEmbedsById(messageId, LobbyManager.buildEmbed(messageId))
                .queue(null, e -> log.warn("[Lobby] Embed-Update fehlgeschlagen: {}", e.getMessage()));
        }
    }

    private void updateEmbed(MessageReactionAddEvent event, String messageId) {
        event.getChannel().editMessageEmbedsById(messageId, LobbyManager.buildEmbed(messageId))
            .queue(null, e -> log.warn("[Lobby] Embed-Update fehlgeschlagen: {}", e.getMessage()));
    }
}
