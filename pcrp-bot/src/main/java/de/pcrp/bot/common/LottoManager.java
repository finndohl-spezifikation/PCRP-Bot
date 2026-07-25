package de.pcrp.bot.common;

import com.google.gson.*;

import java.util.*;

/**
 * Verwaltet das tägliche Lotto mit Zahlenwahl (6 aus 45) und wachsendem Jackpot.
 *
 * DataStore-Keys:
 *   lotto-jackpot-{guildId}           → aktueller Jackpot
 *   lotto-participants-{guildId}      → JSON-Array von User-IDs
 *   lotto-picks-{guildId}-{userId}    → JSON-Array der gewählten Zahlen
 */
public final class LottoManager {

    private static final Gson   GSON   = new Gson();
    private static final Random RANDOM = new Random();

    // Jackpot-Konfiguration
    public static final int JACKPOT_BASE      = 250_000;   // Startwert nach Gewinn
    public static final int JACKPOT_INCREMENT = 100_000;   // Zuwachs pro Tag ohne Gewinner
    public static final int JACKPOT_MAX       = 5_000_000; // Maximaler Jackpot

    // Lotto-Konfiguration
    public static final int PICK_COUNT = 6;   // Anzahl zu wählender Zahlen
    public static final int PICK_MAX   = 45;  // Höchste wählbare Zahl

    // Fixe Preise für Teiltreffer
    private static final int PRIZE_5 = 50_000;
    private static final int PRIZE_4 = 10_000;

    // ── Keys ──────────────────────────────────────────────────────────────────

    private static String jackpotKey(String g)            { return "lotto-jackpot-"     + g; }
    private static String participantKey(String g)        { return "lotto-participants-" + g; }
    private static String picksKey(String g, String u)    { return "lotto-picks-" + g + "-" + u; }

    // ── Token ─────────────────────────────────────────────────────────────────

    public static String createToken(String guildId, String userId) {
        String token = UUID.randomUUID().toString().replace("-", "");
        DataStore.writeString("lotto-token-" + token, guildId + ":" + userId);
        return token;
    }

    public static String[] lookupToken(String token) {
        String raw = DataStore.readString("lotto-token-" + token);
        if (raw == null) return null;
        String[] parts = raw.split(":", 2);
        return parts.length == 2 ? parts : null;
    }

    public static void deleteToken(String token) {
        DataStore.deleteKey("lotto-token-" + token);
    }

    // ── Jackpot ───────────────────────────────────────────────────────────────

    public static int getCurrentJackpot(String guildId) {
        String raw = DataStore.readString(jackpotKey(guildId));
        if (raw == null || raw.isBlank()) {
            DataStore.writeString(jackpotKey(guildId), String.valueOf(JACKPOT_BASE));
            return JACKPOT_BASE;
        }
        try { return Integer.parseInt(raw.trim()); }
        catch (NumberFormatException e) {
            DataStore.writeString(jackpotKey(guildId), String.valueOf(JACKPOT_BASE));
            return JACKPOT_BASE;
        }
    }

    /** Jackpot um INCREMENT erhöhen (täglich wenn kein Gewinner). */
    public static int increaseJackpot(String guildId) {
        int next = Math.min(getCurrentJackpot(guildId) + JACKPOT_INCREMENT, JACKPOT_MAX);
        DataStore.writeString(jackpotKey(guildId), String.valueOf(next));
        return next;
    }

    /** Jackpot nach Jackpot-Gewinn auf BASE zurücksetzen. */
    public static int resetJackpot(String guildId) {
        DataStore.writeString(jackpotKey(guildId), String.valueOf(JACKPOT_BASE));
        return JACKPOT_BASE;
    }

    // ── Picks ─────────────────────────────────────────────────────────────────

    public static void savePicks(String guildId, String userId, int[] picks) {
        JsonArray arr = new JsonArray();
        for (int p : picks) arr.add(p);
        DataStore.writeString(picksKey(guildId, userId), GSON.toJson(arr));
    }

    public static int[] getPicks(String guildId, String userId) {
        String raw = DataStore.readString(picksKey(guildId, userId));
        if (raw == null) return new int[0];
        try {
            JsonArray arr = GSON.fromJson(raw, JsonArray.class);
            int[] picks = new int[arr.size()];
            for (int i = 0; i < arr.size(); i++) picks[i] = arr.get(i).getAsInt();
            return picks;
        } catch (Exception e) { return new int[0]; }
    }

    /** Picks validieren: genau PICK_COUNT Zahlen, im Bereich [1, PICK_MAX], keine Duplikate. */
    public static String validatePicks(int[] picks) {
        if (picks == null || picks.length != PICK_COUNT)
            return "Du musst genau " + PICK_COUNT + " Zahlen auswählen.";
        Set<Integer> seen = new HashSet<>();
        for (int p : picks) {
            if (p < 1 || p > PICK_MAX)
                return "Alle Zahlen müssen zwischen 1 und " + PICK_MAX + " liegen.";
            if (!seen.add(p))
                return "Keine doppelten Zahlen erlaubt.";
        }
        return null;
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
     * Meldet einen Nutzer an. Validiert Zahlen, prüft Lottoschein, speichert Picks.
     * @return Fehlermeldung oder null bei Erfolg
     */
    public static synchronized String enroll(String guildId, String userId, int[] picks) {
        String err = validatePicks(picks);
        if (err != null) return err;
        if (isParticipant(guildId, userId))
            return "Du nimmst bereits an der heutigen Ziehung teil.";
        if (!InventoryManager.removeItem(guildId, userId, "Lottoschein", 1))
            return "Du hast keinen Lottoschein in deinem Inventar.";
        savePicks(guildId, userId, picks);
        List<String> participants = getParticipants(guildId);
        participants.add(userId);
        saveParticipants(guildId, participants);
        return null;
    }

    // ── Ziehung ───────────────────────────────────────────────────────────────

    /** Zieht PICK_COUNT einzigartige Gewinnzahlen aus [1, PICK_MAX] (sortiert). */
    public static int[] drawWinningNumbers() {
        List<Integer> pool = new ArrayList<>();
        for (int i = 1; i <= PICK_MAX; i++) pool.add(i);
        Collections.shuffle(pool, RANDOM);
        int[] nums = new int[PICK_COUNT];
        for (int i = 0; i < PICK_COUNT; i++) nums[i] = pool.get(i);
        Arrays.sort(nums);
        return nums;
    }

    public static int countMatches(int[] picks, int[] winning) {
        Set<Integer> ws = new HashSet<>();
        for (int w : winning) ws.add(w);
        int count = 0;
        for (int p : picks) if (ws.contains(p)) count++;
        return count;
    }

    /**
     * Führt die Ziehung durch:
     *   6/6 → voller Jackpot → Jackpot wird zurückgesetzt
     *   5/6 → 50.000$ (fix)
     *   4/6 → 10.000$ (fix)
     * Räumt Teilnehmerliste und Picks auf.
     */
    public static DrawResult draw(String guildId) {
        List<String> participants = getParticipants(guildId);
        int jackpot  = getCurrentJackpot(guildId);
        int[] winning = drawWinningNumbers();

        List<String> jackpotWinners = new ArrayList<>();
        List<String> tier5Winners   = new ArrayList<>();
        List<String> tier4Winners   = new ArrayList<>();

        for (String uid : participants) {
            int[] picks = getPicks(guildId, uid);
            if (picks.length == 0) continue;
            int matches = countMatches(picks, winning);
            if      (matches == 6) jackpotWinners.add(uid);
            else if (matches == 5) tier5Winners.add(uid);
            else if (matches == 4) tier4Winners.add(uid);
        }

        // Auszahlung über Bank
        for (String uid : jackpotWinners) {
            long bal = BankManager.getBalance(guildId, uid);
            BankManager.setBalance(guildId, uid, bal + jackpot);
            BankManager.addTransaction(guildId, uid, "LOTTO_GEWINN", jackpot, null);
        }
        for (String uid : tier5Winners) {
            long bal = BankManager.getBalance(guildId, uid);
            BankManager.setBalance(guildId, uid, bal + PRIZE_5);
            BankManager.addTransaction(guildId, uid, "LOTTO_GEWINN", PRIZE_5, null);
        }
        for (String uid : tier4Winners) {
            long bal = BankManager.getBalance(guildId, uid);
            BankManager.setBalance(guildId, uid, bal + PRIZE_4);
            BankManager.addTransaction(guildId, uid, "LOTTO_GEWINN", PRIZE_4, null);
        }

        // Jackpot wachsen oder zurücksetzen
        boolean jackpotWon = !jackpotWinners.isEmpty();
        int nextJackpot = jackpotWon ? resetJackpot(guildId) : increaseJackpot(guildId);

        // Aufräumen
        for (String uid : participants) DataStore.deleteKey(picksKey(guildId, uid));
        DataStore.deleteKey(participantKey(guildId));

        return new DrawResult(winning, jackpot, nextJackpot, participants.size(),
                jackpotWinners, tier5Winners, tier4Winners);
    }

    public record DrawResult(
        int[] winningNumbers,
        int jackpot,
        int nextJackpot,
        int participantCount,
        List<String> jackpotWinners,
        List<String> tier5Winners,
        List<String> tier4Winners
    ) {}

    // ── Formatierung ──────────────────────────────────────────────────────────

    public static String formatAmount(int amount) {
        if (amount >= 1_000_000) {
            int m = amount / 1_000_000;
            int k = (amount % 1_000_000) / 1_000;
            return k > 0 ? m + "." + String.format("%03d", k) + ".000$" : m + ".000.000$";
        }
        return String.format("%,d$", amount).replace(',', '.');
    }

    public static String formatNumbers(int[] nums) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < nums.length; i++) {
            if (i > 0) sb.append(" – ");
            sb.append(String.format("%02d", nums[i]));
        }
        return sb.toString();
    }

    private LottoManager() {}
}
