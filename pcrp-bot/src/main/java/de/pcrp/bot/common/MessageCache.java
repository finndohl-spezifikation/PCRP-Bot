package de.pcrp.bot.common;

import java.util.*;

/**
 * Einfacher In-Memory-Cache für gesendete Nachrichten.
 * Wird von ModerationListener befüllt (MessageReceivedEvent) und
 * vom LoggingListener ausgelesen (MessageDeleteEvent / MessageBulkDeleteEvent),
 * um Nachrichteninhalte auch nach der Löschung noch loggen zu können.
 */
public final class MessageCache {

    private static final int MAX_SIZE = 1000;

    /** Gecachte Nachrichtendaten (unveränderlicher Snapshot zum Zeitpunkt des Empfangs). */
    public record CachedMessage(
        String authorId,
        String authorName,
        String authorAvatar,
        String content,
        String channelMention,
        List<String> attachments,
        long timestampEpoch
    ) {}

    @SuppressWarnings("serial")
    private static final Map<Long, CachedMessage> CACHE = Collections.synchronizedMap(
        new LinkedHashMap<>(256, 0.75f, false) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<Long, CachedMessage> eldest) {
                return size() > MAX_SIZE;
            }
        }
    );

    private MessageCache() {}

    public static void put(long messageId, CachedMessage message) {
        CACHE.put(messageId, message);
    }

    public static CachedMessage get(long messageId) {
        return CACHE.get(messageId);
    }

    public static void remove(long messageId) {
        CACHE.remove(messageId);
    }
}
