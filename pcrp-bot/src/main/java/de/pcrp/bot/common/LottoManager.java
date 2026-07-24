package de.pcrp.bot.common;

import com.google.gson.*;

import java.util.*;
import java.util.UUID;

/**
 * Verwaltet das tägliche Lotto.
 *
 * DataStore-Keys:
 *   lotto-jackpot-{guildId}      → Jackpot-Betrag als String
 *   lotto-participants-{guildId} → JSON-Array von User-IDs
 */
public final class LottoManager {

    private static final Gson   GSON   = new Gson();
    private static final Random RANDOM = new Random();

    // Gewichts-Stufen: {minBetrag, maxBetrag, Gewicht}
    private static final int[][] TIERS = {
        {100_000,   500_000,  45},
        {500_000, 1_000_000,  30},
        {1_000_000, 1_500_000, 15},
        {1_500_000, 2_000_000,  6},
        {2_000_000, 2_500_000,  3},
        {2_500_000, 3_000_000,  1},
    };

    // ── Keys ──────────────────────────────────────────────────────────────────

    private static String jackpotKey(String g)      { return "lotto-jackpot-"      + g; }
    private static String participantKey(String g)  { return "lotto-participants-"  + g; }

    // ── Token (Einmal-Links) ──────────────────────────────────────────────────

    public static String createToken(String guildId, String userId) {
        String token = UUID.randomUUID().toString().replace("-", "");
        DataStore.writeString("lotto-token-" + token, guildId + ":" + userId);
        return token;
    }

    /** @return [guildId, userId] oder null wenn ungültig/abgelaufen */
    public static String[] lookupToken(String token) {
        String raw = DataStore.readString("lotto-token-" + token);
        if (raw == null) return null;
        String[] parts = raw.split(":", 2);
        if (parts.length != 2) return null;
        return parts;
    }

    public static void deleteToken(String token) {
        DataStore.deleteKey("lotto-token-" + token);
    }

    // ── Jackpot ───────────────────────────────────────────────────────────────

    /** Wählt einen neuen Jackpot gewichtet zufällig und speichert ihn. */
    public static int generateAndSaveJackpot(String guildId) {
        int jackpot = weightedRandom();
        DataStore.writeString(jackpotKey(guildId), String.valueOf(jackpot));
        return jackpot;
    }

    /** Gibt den aktuellen Jackpot zurück. Generiert einen neuen falls keiner gespeichert. */
    public static int getCurrentJackpot(String guildId) {
        String raw = DataStore.readString(jackpotKey(guildId));
        if (raw == null || raw.isBlank()) return generateAndSaveJackpot(guildId);
        try { return Integer.parseInt(raw.trim()); }
        catch (NumberFormatException e) { return generateAndSaveJackpot(guildId); }
    }

    private static int weightedRandom() {
        int totalWeight = 0;
        for (int[] t : TIERS) totalWeight += t[2];
        int r = RANDOM.nextInt(totalWeight);
        int cum = 0;
        for (int[] tier : TIERS) {
            cum += tier[2];
            if (r < cum) {
                // Rundes Vielfaches von 50.000 innerhalb der Stufe
                int min   = tier[0] / 50_000;
                int max   = tier[1] / 50_000;
                int steps = max - min;
                return (min + RANDOM.nextInt(Math.max(steps, 1))) * 50_000;
            }
        }
        return 100_000;
    }

    // ── Teilnehmer ────────────────────────────────────────────────────────────

    public static List<String> getParticipants(String guildId) {
        String raw = DataStore.readString(participantKey(guildId));
        List<String> list = new ArrayList<>();
        if (raw == null || raw.isBlank()) return list;
        try {
            JsonArray arr = GSON.fromJson(raw, JsonArray.class);
            for (JsonElement el : arr) list.add(el.getAsString());
        } catch (Exception ignored) {}
        return list;
    }

    private static void saveParticipants(String guildId, List<String> ids) {
        JsonArray arr = new JsonArray();
        ids.forEach(arr::add);
        DataStore.writeString(participantKey(guildId), GSON.toJson(arr));
    }

    public static boolean isParticipant(String guildId, String userId) {
        return getParticipants(guildId).contains(userId);
    }

    public static int getParticipantCount(String guildId) {
        return getParticipants(guildId).size();
    }

    /**
     * Meldet einen Nutzer an. Prüft Lottoschein im Inventar und entfernt ihn.
     * @return Fehlermeldung oder null bei Erfolg
     */
    public static synchronized String enroll(String guildId, String userId) {
        if (isParticipant(guildId, userId)) {
            return "Du nimmst bereits an der heutigen Ziehung teil.";
        }
        boolean hadTicket = InventoryManager.removeItem(guildId, userId, "Lottoschein", 1);
        if (!hadTicket) {
            return "Du hast keinen Lottoschein in deinem Inventar.";
        }
        List<String> participants = getParticipants(guildId);
        participants.add(userId);
        saveParticipants(guildId, participants);
        return null; // Erfolg
    }

    // ── Ziehung ───────────────────────────────────────────────────────────────

    /**
     * Führt die Ziehung durch. Gibt die Gewinner-User-ID zurück, oder null wenn keine Teilnehmer.
     * Räumt Teilnehmerliste auf und generiert neuen Jackpot.
     */
    public static DrawResult draw(String guildId) {
        List<String> participants = getParticipants(guildId);
        int jackpot = getCurrentJackpot(guildId);

        String winner = null;
        if (!participants.isEmpty()) {
            winner = participants.get(RANDOM.nextInt(participants.size()));
            // Gewinn ins Inventar
            InventoryManager.addItem(guildId, winner, "Bargeld", jackpot);
        }

        // Zurücksetzen + neuer Jackpot für morgen
        DataStore.deleteKey(participantKey(guildId));
        int newJackpot = generateAndSaveJackpot(guildId);

        return new DrawResult(winner, jackpot, newJackpot, participants.size());
    }

    public record DrawResult(String winnerId, int jackpot, int nextJackpot, int participantCount) {}

    // ── Formatierung ──────────────────────────────────────────────────────────

    public static String formatAmount(int amount) {
        if (amount >= 1_000_000) {
            int m = amount / 1_000_000;
            int k = (amount % 1_000_000) / 1_000;
            return k > 0 ? m + "." + String.format("%03d", k) + ".000$" : m + ".000.000$";
        }
        return String.format("%,d$", amount).replace(',', '.');
    }

    private LottoManager() {}
}
