package de.pcrp.bot.common;

import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.Set;

/**
 * Verwaltet per /embed-schreiben erstellte Custom-Embeds (DataStore-basiert,
 * überlebt also Bot-Neustarts).
 *
 * Diese Embeds sind vom Embed-Lösch-Schutz ausgenommen und können jederzeit
 * manuell oder per /löschen entfernt werden – in jedem Kanal.
 */
public final class CustomEmbedManager {

    private static String key(long guildId) {
        return "custom-embeds-" + guildId;
    }

    private static Set<String> read(long guildId) {
        String raw = DataStore.readString(key(guildId));
        if (raw == null || raw.isBlank()) return new LinkedHashSet<>();
        return new LinkedHashSet<>(Arrays.asList(raw.split(",")));
    }

    private static void write(long guildId, Set<String> ids) {
        DataStore.writeString(key(guildId), String.join(",", ids));
    }

    /** Markiert eine Nachricht als frei löschbares Custom-Embed. */
    public static synchronized void mark(long guildId, String messageId) {
        Set<String> ids = read(guildId);
        ids.add(messageId);
        write(guildId, ids);
    }

    /** Gibt zurück, ob die Nachricht ein frei löschbares Custom-Embed ist. */
    public static synchronized boolean isCustom(long guildId, String messageId) {
        return read(guildId).contains(messageId);
    }

    /** Entfernt die Markierung (wenn die Nachricht gelöscht wird). */
    public static synchronized void unmark(long guildId, String messageId) {
        Set<String> ids = read(guildId);
        if (ids.remove(messageId)) write(guildId, ids);
    }

    private CustomEmbedManager() {}
}
