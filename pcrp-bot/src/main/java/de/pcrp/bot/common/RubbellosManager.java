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
    private static final int[][] PRIZES = {
        {       0,  55 },   // Niete
        {     100,  20 },
        {     500,  12 },
        {   1_000,   7 },
        {   2_500,   3 },
        {   5_000,   2 },
        {  10_000,   1 },
        {  30_000,   1 },
    };

    // Mögliche Beträge die auf dem Spielfeld erscheinen
    private static final int[] POOL = {100, 500, 1_000, 2_500, 5_000, 10_000, 30_000};

    // Alle 8 Gewinnlinien im 3×3 Feld (Index 0-8, Zeilenmajor)
    static final int[][] LINES = {
        {0,1,2},{3,4,5},{6,7,8},   // Reihen
        {0,3,6},{1,4,7},{2,5,8},   // Spalten
        {0,4,8},{2,4,6}             // Diagonalen
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

    // ── Spielfeld ─────────────────────────────────────────────────────────────

    /**
     * Baut ein 3×3-Spielfeld (9 Felder, Index 0-8 zeilenweise).
     * Gewinn: eine zufällige der 8 Linien enthält dreimal den Gewinnbetrag,
     *         alle anderen Felder haben keine weitere 3er-Kombination.
     * Niete:  keine Linie hat drei gleiche Beträge.
     */
    public static int[] buildGrid(int prize) {
        int[] grid = new int[9];

        if (prize > 0) {
            // Gewinnlinie zufällig wählen und mit Gewinnbetrag belegen
            int[] winLine = LINES[RANDOM.nextInt(LINES.length)];
            boolean[] isWin = new boolean[9];
            for (int idx : winLine) { grid[idx] = prize; isWin[idx] = true; }

            // Restliche Felder füllen: kein prize-Wert, keine weitere 3er-Kombination
            int[] filtered = java.util.Arrays.stream(POOL).filter(v -> v != prize).toArray();
            for (int attempt = 0; attempt < 300; attempt++) {
                for (int i = 0; i < 9; i++) {
                    if (!isWin[i]) grid[i] = filtered[RANDOM.nextInt(filtered.length)];
                }
                if (!hasExtraLine(grid, winLine)) break;
            }
        } else {
            // Niete: keine Linie mit drei gleichen Werten
            for (int attempt = 0; attempt < 300; attempt++) {
                for (int i = 0; i < 9; i++) grid[i] = POOL[RANDOM.nextInt(POOL.length)];
                if (!hasAnyLine(grid)) break;
            }
        }
        return grid;
    }

    /** Prüft ob irgendeine Linie drei gleiche Werte hat. */
    private static boolean hasAnyLine(int[] g) {
        for (int[] l : LINES) if (g[l[0]] == g[l[1]] && g[l[1]] == g[l[2]]) return true;
        return false;
    }

    /** Prüft ob eine andere als die Gewinnlinie drei gleiche Werte hat. */
    private static boolean hasExtraLine(int[] g, int[] winLine) {
        for (int[] l : LINES) {
            if (l == winLine) continue;  // Referenz-Vergleich – selbes Array-Objekt
            if (g[l[0]] == g[l[1]] && g[l[1]] == g[l[2]]) return true;
        }
        return false;
    }

    // ── Hilfsmethoden ─────────────────────────────────────────────────────────

    public static String formatAmount(int amount) {
        if (amount == 0) return "Niete";
        return String.format("%,d$", amount).replace(',', '.');
    }

    private RubbellosManager() {}
}
