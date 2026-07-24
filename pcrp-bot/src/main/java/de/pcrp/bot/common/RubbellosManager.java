package de.pcrp.bot.common;

import java.util.Random;
import java.util.UUID;

/**
 * Verwaltet Rubbellose (Goldene 7).
 *
 * DataStore-Keys:
 *   rubbellos-token-{token} → guildId:userId:prizeAmount
 */
public final class RubbellosManager {

    private static final Random RANDOM = new Random();

    // Gewinn-Stufen: {betrag, Gewicht}
    // Gewicht 0 = Niete (kein Bargeld)
    private static final int[][] PRIZES = {
        {       0,  55 },   // Niete
        {     100,  20 },
        {     500,  12 },
        {   1_000,   7 },
        {   2_500,   3 },
        {   5_000,   2 },
        {  10_000,   1 },  // ~0.7 effektiv durch Rundung
        {  30_000,   1 },  // ~0.3
    };

    public static int rollPrize() {
        int total = 0;
        for (int[] p : PRIZES) total += p[1];
        int r = RANDOM.nextInt(total);
        int cum = 0;
        for (int[] prize : PRIZES) {
            cum += prize[1];
            if (r < cum) return prize[0];
        }
        return 0;
    }

    // ── Token ─────────────────────────────────────────────────────────────────

    public static String createToken(String guildId, String userId, int prize) {
        String token = UUID.randomUUID().toString().replace("-", "");
        DataStore.writeString("rubbellos-token-" + token, guildId + ":" + userId + ":" + prize);
        return token;
    }

    /** @return [guildId, userId, prizeStr] oder null wenn ungültig */
    public static String[] lookupToken(String token) {
        String raw = DataStore.readString("rubbellos-token-" + token);
        if (raw == null) return null;
        String[] parts = raw.split(":", 3);
        if (parts.length != 3) return null;
        return parts;
    }

    public static void deleteToken(String token) {
        DataStore.deleteKey("rubbellos-token-" + token);
    }

    // ── Hilfsmethoden ─────────────────────────────────────────────────────────

    public static String formatAmount(int amount) {
        if (amount == 0) return "Niete";
        return String.format("%,d$", amount).replace(',', '.');
    }

    /** Gibt drei Zellen-Werte zurück (für Anzeige auf Rubbellos). */
    public static int[] buildCells(int prize) {
        if (prize == 0) {
            // Niete: drei verschiedene Beträge, keiner doppelt
            int[] pool = {100, 500, 1_000, 2_500, 5_000, 10_000};
            int[] cells = new int[3];
            int used = -1, used2 = -1;
            for (int i = 0; i < 3; i++) {
                int pick;
                do { pick = pool[RANDOM.nextInt(pool.length)]; }
                while (pick == used || pick == used2);
                cells[i] = pick;
                if (i == 0) used = pick;
                if (i == 1) used2 = pick;
            }
            return cells;
        }
        // Gewinn: alle drei gleich
        return new int[]{prize, prize, prize};
    }

    private RubbellosManager() {}
}
