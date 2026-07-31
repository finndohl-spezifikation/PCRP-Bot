package de.pcrp.bot.common;

import com.google.gson.*;
import net.dv8tion.jda.api.entities.Guild;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.*;

/**
 * PC-Coins Krypto-System.
 *
 * Der Kurs ist angebotsabhängig: Je mehr PC Coins im Umlauf sind, desto
 * höher der Kurs — je weniger, desto niedriger. Der Kurs reagiert sofort
 * auf jede Transaktion und wird zudem alle 15 Minuten als Preispunkt für
 * die 7-Tage-Historie gespeichert (Webseite: /krypto).
 *
 * DataStore-Keys:
 *   krypto-bal-{guildId}-{userId}  → long (String)
 *   krypto-supply-{guildId}        → long Gesamt-Umlauf
 *   krypto-history-{guildId}       → JSON [{ts,rate}, …] (max. 7 Tage)
 */
public final class KryptoManager {

    private static final Logger log = LoggerFactory.getLogger(KryptoManager.class);
    private static final Gson GSON = new GsonBuilder().create();

    /** Startkurs eines PC Coins in $ (Minimum). */
    public static final double BASE_RATE = 1.0;

    /** Jeder PC Coin im Umlauf erhöht den Kurs um diesen Betrag ($). */
    public static final double PRICE_STEP = 1.0 / 100_000.0;

    /** Historie: 7 Tage rückverfolgbar. */
    private static final long HISTORY_HOURS = 7L * 24L;

    private static boolean started = false;
    private static ScheduledExecutorService scheduler;

    private KryptoManager() {}

    /** Startet den Kurs-Snapshot-Scheduler (einmalig nach Bot-Start). */
    public static synchronized void init(Guild guild) {
        if (started) return;
        started = true;
        scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "krypto-scheduler");
            t.setDaemon(true);
            return t;
        });
        scheduler.scheduleAtFixedRate(() -> snapshot(guild.getId()), 15, 15, TimeUnit.MINUTES);
        log.info("[Krypto] Kurs-Snapshot-Scheduler gestartet (alle 15 Minuten).");
    }

    // ── Balance ────────────────────────────────────────────────────────────────

    private static String balKey(String guildId, String userId) {
        return "krypto-bal-" + guildId + "-" + userId;
    }

    private static String supplyKey(String guildId) {
        return "krypto-supply-" + guildId;
    }

    public static long getBalance(String guildId, String userId) {
        String raw = DataStore.readString(balKey(guildId, userId));
        if (raw == null || raw.isBlank()) return 0L;
        try { return Math.max(0L, Long.parseLong(raw.trim())); }
        catch (NumberFormatException e) { return 0L; }
    }

    private static void setBalance(String guildId, String userId, long coins) {
        DataStore.writeString(balKey(guildId, userId), String.valueOf(Math.max(0L, coins)));
    }

    /** Erhöht Balance UND Gesamt-Umlauf (Kurs steigt). */
    public static void add(String guildId, String userId, long coins) {
        if (coins <= 0) return;
        setBalance(guildId, userId, getBalance(guildId, userId) + coins);
        setSupply(guildId, getSupply(guildId) + coins);
    }

    /** Reduziert Balance UND Gesamt-Umlauf (Kurs sinkt). @return false wenn nicht genug vorhanden. */
    public static boolean remove(String guildId, String userId, long coins) {
        if (coins <= 0) return true;
        long bal = getBalance(guildId, userId);
        if (bal < coins) return false;
        setBalance(guildId, userId, bal - coins);
        setSupply(guildId, Math.max(0L, getSupply(guildId) - coins));
        return true;
    }

    // ── Umlauf / Kurs ─────────────────────────────────────────────────────────

    public static long getSupply(String guildId) {
        String raw = DataStore.readString(supplyKey(guildId));
        if (raw == null || raw.isBlank()) return 0L;
        try { return Math.max(0L, Long.parseLong(raw.trim())); }
        catch (NumberFormatException e) { return 0L; }
    }

    public static void setSupply(String guildId, long supply) {
        DataStore.writeString(supplyKey(guildId), String.valueOf(Math.max(0L, supply)));
    }

    /** Aktueller Kurs eines PC Coins in $ (angebotsabhängig). */
    public static double getRate(String guildId) {
        return BASE_RATE + getSupply(guildId) * PRICE_STEP;
    }

    // ── Operationen ───────────────────────────────────────────────────────────

    /**
     * Einzahlen: Zahlt {moneyAmount}$ vom Bankkonto und erhält PC Coins
     * zum aktuellen Kurs. Gibt Fehlermeldung zurück, null bei Erfolg.
     */
    public static String buy(String guildId, String userId, long moneyAmount) {
        if (moneyAmount <= 0) return "Betrag muss größer als 0 sein.";
        double rate = getRate(guildId);
        long coins = (long) (moneyAmount / rate);
        if (coins <= 0)
            return "Der Betrag reicht nicht für **1 PC Coin** (aktueller Kurs: " + formatRate(rate) + ").";
        long bank = BankManager.getBalance(guildId, userId);
        if (bank < moneyAmount)
            return "Dein Kontostand (**" + BankManager.formatAmount(bank) + "**) reicht nicht aus.";
        BankManager.setBalance(guildId, userId, bank - moneyAmount);
        BankManager.addTransaction(guildId, userId, "KRYPTO_KAUF", moneyAmount, formatRate(rate));
        add(guildId, userId, coins);
        snapshot(guildId);
        return null;
    }

    /**
     * Auszahlen: Wandelt {coins} PC Coins in Kontogeld um (Kurs × Menge).
     * Gibt Fehlermeldung zurück, null bei Erfolg.
     */
    public static String sell(String guildId, String userId, long coins) {
        if (coins <= 0) return "Menge muss größer als 0 sein.";
        long bal = getBalance(guildId, userId);
        if (bal < coins)
            return "Du hast nur **" + formatCoins(bal) + "** PC Coins.";
        double rate = getRate(guildId);
        long money = Math.round(coins * rate);
        remove(guildId, userId, coins);
        BankManager.setBalance(guildId, userId, BankManager.getBalance(guildId, userId) + money);
        BankManager.addTransaction(guildId, userId, "KRYPTO_VERKAUF", money, formatRate(rate));
        snapshot(guildId);
        return null;
    }

    /**
     * Überweist PC Coins von einem Krypto-Konto auf ein anderes
     * (Umlauf bleibt gleich, Kurs unverändert).
     * Gibt Fehlermeldung zurück, null bei Erfolg.
     */
    public static String transfer(String guildId, String fromId, String toId, long coins) {
        if (coins <= 0) return "Menge muss größer als 0 sein.";
        long bal = getBalance(guildId, fromId);
        if (bal < coins)
            return "Du hast nur **" + formatCoins(bal) + "** PC Coins.";
        remove(guildId, fromId, coins);
        add(guildId, toId, coins);
        return null;
    }

    /** Admin: PC Coins manuell gutschreiben (/geld-geben mit PC Coins). */
    public static void adminGive(String guildId, String userId, long coins) {
        if (coins <= 0) return;
        add(guildId, userId, coins);
        snapshot(guildId);
    }

    /** Admin: PC Coins manuell abziehen (/geld-entfernen mit PC Coins). Gibt Fehler oder null zurück. */
    public static String adminRemove(String guildId, String userId, long coins) {
        if (coins <= 0) return "Betrag muss größer als 0 sein.";
        if (!remove(guildId, userId, coins))
            return "Spieler hat nur **" + formatCoins(getBalance(guildId, userId)) + "** PC Coins.";
        snapshot(guildId);
        return null;
    }

    // ── Preishistorie (7 Tage) ────────────────────────────────────────────────

    public static class RatePoint {
        public final long ts;      // Unix-Sekunden
        public final double rate;  // Kurs in $
        public RatePoint(long ts, double rate) { this.ts = ts; this.rate = rate; }
    }

    private static String historyKey(String guildId) {
        return "krypto-history-" + guildId;
    }

    /** Fügt einen Kurs-Punkt hinzu und entfernt alles älter als 7 Tage. */
    public static synchronized void snapshot(String guildId) {
        List<RatePoint> pts = readHistory(guildId);
        pts.add(new RatePoint(System.currentTimeMillis() / 1000, getRate(guildId)));
        long cutoff = (System.currentTimeMillis() / 1000) - HISTORY_HOURS * 3600L;
        pts.removeIf(p -> p.ts < cutoff);
        if (pts.size() > 500) pts = new ArrayList<>(pts.subList(pts.size() - 500, pts.size()));
        JsonArray arr = new JsonArray();
        for (RatePoint p : pts) {
            JsonObject o = new JsonObject();
            o.addProperty("ts", p.ts);
            o.addProperty("rate", p.rate);
            arr.add(o);
        }
        DataStore.writeString(historyKey(guildId), GSON.toJson(arr));
    }

    /** Liest die Preishistorie (älteste zuerst, max. 7 Tage). */
    public static List<RatePoint> readHistory(String guildId) {
        List<RatePoint> pts = new ArrayList<>();
        String raw = DataStore.readString(historyKey(guildId));
        if (raw == null || raw.isBlank()) return pts;
        try {
            JsonArray arr = GSON.fromJson(raw, JsonArray.class);
            if (arr == null) return pts;
            for (JsonElement el : arr) {
                JsonObject o = el.getAsJsonObject();
                pts.add(new RatePoint(o.get("ts").getAsLong(), o.get("rate").getAsDouble()));
            }
        } catch (Exception ignored) {}
        pts.sort(Comparator.comparingLong(p -> p.ts));
        return pts;
    }

    // ── Formatierung ──────────────────────────────────────────────────────────

    public static String formatRate(double rate) {
        return String.format("$%,.4f", rate).replace(',', '.');
    }

    public static String formatCoins(long coins) {
        return String.format("%,d", coins).replace(',', '.') + " PC";
    }
}
