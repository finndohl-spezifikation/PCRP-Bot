package de.pcrp.bot.listeners;

import de.pcrp.bot.common.VorschlagManager;
import de.pcrp.bot.common.VorschlagManager.Vorschlag;
import net.dv8tion.jda.api.entities.emoji.Emoji;
import net.dv8tion.jda.api.events.message.react.MessageReactionAddEvent;
import net.dv8tion.jda.api.events.message.react.MessageReactionRemoveEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class VorschlagListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(VorschlagListener.class);

    @Override
    public void onMessageReactionAdd(MessageReactionAddEvent event) {
        if (!event.isFromGuild()) return;
        if (event.getUser() == null || event.getUser().isBot()) return;

        String emojiName = event.getEmoji().getName();
        boolean isUp   = emojiName.startsWith("👍");
        boolean isDown = emojiName.startsWith("👎");
        if (!isUp && !isDown) return;

        String guildId   = event.getGuild().getId();
        String messageId = event.getMessageId();

        Vorschlag v = VorschlagManager.getByMessageId(guildId, messageId);
        if (v == null || !"active".equals(v.status)) {
            // Nicht bekannte Vorschlag-Nachricht → eigene Reaction entfernen
            event.getReaction().removeReaction(event.getUser()).queue(null, e -> {});
            return;
        }

        String userId  = event.getUserId();
        String removeEmoji = isUp ? VorschlagManager.EMOJI_DOWN : VorschlagManager.EMOJI_UP;
        boolean removedOther = isUp
            ? VorschlagManager.upvote(guildId, messageId, userId)
            : VorschlagManager.downvote(guildId, messageId, userId);

        // Nachricht abrufen um ggf. die andere Reaction zu entfernen + Embed updaten
        event.getChannel().retrieveMessageById(messageId).queue(msg -> {
            if (removedOther) {
                msg.removeReaction(Emoji.fromUnicode(removeEmoji), event.getUser())
                    .queue(null, e -> {});
            }
            Vorschlag updated = VorschlagManager.getByMessageId(guildId, messageId);
            if (updated != null) {
                msg.editMessageEmbeds(VorschlagManager.buildVorschlagEmbed(updated))
                    .queue(null, e -> log.warn("[Vorschlag] Embed-Update fehlgeschlagen: {}", e.getMessage()));
            }
        }, e -> {});
    }

    @Override
    public void onMessageReactionRemove(MessageReactionRemoveEvent event) {
        if (!event.isFromGuild()) return;

        String emojiName = event.getEmoji().getName();
        boolean isUp   = emojiName.startsWith("👍");
        boolean isDown = emojiName.startsWith("👎");
        if (!isUp && !isDown) return;

        String guildId   = event.getGuild().getId();
        String messageId = event.getMessageId();

        Vorschlag v = VorschlagManager.getByMessageId(guildId, messageId);
        if (v == null || !"active".equals(v.status)) return;

        String userId = event.getUserId();
        if (isUp) VorschlagManager.removeUpvote(guildId, messageId, userId);
        else      VorschlagManager.removeDownvote(guildId, messageId, userId);

        Vorschlag updated = VorschlagManager.getByMessageId(guildId, messageId);
        if (updated != null) {
            event.getChannel().editMessageEmbedsById(messageId,
                VorschlagManager.buildVorschlagEmbed(updated)).queue(null, e -> {});
        }
    }
}
