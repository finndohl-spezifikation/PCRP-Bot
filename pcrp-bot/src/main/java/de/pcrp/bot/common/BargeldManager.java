package de.pcrp.bot.common;

/**
 * Verwaltet den Bargeld-Bestand der Spieler.
 * DataStore-Key: {@code bargeld-{guildId}-{userId}} → long (als String gespeichert)
 * Bargeld ist KEIN Inventar-Item mehr.
 */
public final class BargeldManager {

    private BargeldManager() {}

    private static String key(String guildId, String userId) {
        return "bargeld-" + guildId + "-" + userId;
    }

    /** Gibt den aktuellen Bargeld-Bestand zurück (0 wenn nicht vorhanden). */
    public static long get(String guildId, String userId) {
        String raw = DataStore.readString(key(guildId, userId));
        if (raw == null || raw.isBlank()) return 0L;
        try { return Math.max(0L, Long.parseLong(raw.trim())); }
        catch (NumberFormatException e) { return 0L; }
    }

    /** Setzt den Bargeld-Bestand direkt. */
    public static void set(String guildId, String userId, long amount) {
        DataStore.writeString(key(guildId, userId), String.valueOf(Math.max(0L, amount)));
    }

    /** Fügt Bargeld hinzu. */
    public static void add(String guildId, String userId, long amount) {
        if (amount <= 0) return;
        set(guildId, userId, get(guildId, userId) + amount);
    }

    /**
     * Zieht Bargeld ab.
     * @return false wenn nicht genug vorhanden, true bei Erfolg
     */
    public static boolean remove(String guildId, String userId, long amount) {
        if (amount <= 0) return true;
        long current = get(guildId, userId);
        if (current < amount) return false;
        set(guildId, userId, current - amount);
        return true;
    }

    /**
     * Überträgt Bargeld von {@code fromId} zu {@code toId}.
     * @return Fehlermeldung oder null bei Erfolg
     */
    public static String transfer(String guildId, String fromId, String toId, long amount) {
        if (amount <= 0) return "Betrag muss größer als 0 sein.";
        long from = get(guildId, fromId);
        if (from < amount)
            return "Spieler hat nur **" + format(from) + "** Bargeld.";
        set(guildId, fromId, from - amount);
        add(guildId, toId, amount);
        return null;
    }

    /** Formatiert einen Betrag als Anzeigestring (z. B. "1.500$"). */
    public static String format(long amount) {
        return String.format("%,d$", amount).replace(',', '.');
    }
}
