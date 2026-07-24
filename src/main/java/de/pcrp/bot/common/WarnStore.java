package de.pcrp.bot.common;

import com.google.gson.*;
import com.google.gson.reflect.TypeToken;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Type;
import java.util.*;

/**
 * Persistenter Warn-Speicher (DataStore-Key: warns-{guildId}-{userId}).
 * JSON-Array aus WarnEntry-Objekten.
 */
public final class WarnStore {

    private static final Logger log  = LoggerFactory.getLogger(WarnStore.class);
    private static final Gson   GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final Type   LIST_TYPE = new TypeToken<List<WarnEntry>>() {}.getType();

    private WarnStore() {}

    // ─── Lesen ───────────────────────────────────────────────────────────────

    public static List<WarnEntry> getWarns(long guildId, long userId) {
        String raw = DataStore.readString(key(guildId, userId));
        if (raw == null || raw.isBlank()) return new ArrayList<>();
        try {
            List<WarnEntry> list = GSON.fromJson(raw, LIST_TYPE);
            return list == null ? new ArrayList<>() : list;
        } catch (JsonSyntaxException e) {
            log.warn("[WarnStore] JSON-Fehler für {}/{}: {}", guildId, userId, e.getMessage());
            return new ArrayList<>();
        }
    }

    // ─── Schreiben ────────────────────────────────────────────────────────────

    /** Fügt einen Warn hinzu und gibt die neue Gesamt-Anzahl zurück. */
    public static int addWarn(long guildId, long userId, WarnEntry warn) {
        List<WarnEntry> list = getWarns(guildId, userId);
        list.add(warn);
        save(guildId, userId, list);
        return list.size();
    }

    /** Entfernt einen Warn anhand seiner ID. Gibt true zurück, wenn gefunden. */
    public static boolean removeWarn(long guildId, long userId, String warnId) {
        List<WarnEntry> list = getWarns(guildId, userId);
        boolean removed = list.removeIf(w -> warnId.equals(w.id));
        if (removed) save(guildId, userId, list);
        return removed;
    }

    /** Löscht alle Warnungen eines Nutzers. */
    public static void clearWarns(long guildId, long userId) {
        DataStore.deleteKey(key(guildId, userId));
    }

    // ─── Intern ──────────────────────────────────────────────────────────────

    private static void save(long guildId, long userId, List<WarnEntry> list) {
        DataStore.writeString(key(guildId, userId), GSON.toJson(list));
    }

    private static String key(long guildId, long userId) {
        return "warns-" + guildId + "-" + userId;
    }

    // ─── Datenklasse ─────────────────────────────────────────────────────────

    public static class WarnEntry {
        public String id;
        public String reason;
        public String consequence;
        public String byId;
        public String byName;
        public long   timestamp;

        public WarnEntry(String reason, String consequence, String byId, String byName) {
            this.id          = UUID.randomUUID().toString();
            this.reason      = reason;
            this.consequence = consequence;
            this.byId        = byId;
            this.byName      = byName;
            this.timestamp   = System.currentTimeMillis() / 1000;
        }

        /** Formatiertes Datum: dd.MM.yyyy */
        public String dateString() {
            java.time.LocalDate d = java.time.Instant.ofEpochSecond(timestamp)
                .atZone(java.time.ZoneId.of("Europe/Berlin")).toLocalDate();
            return String.format("%02d.%02d.%d", d.getDayOfMonth(), d.getMonthValue(), d.getYear());
        }
    }
}
