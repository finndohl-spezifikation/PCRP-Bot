package de.pcrp.bot.common;

import com.google.gson.*;
import net.dv8tion.jda.api.entities.Guild;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.*;

/**
 * Aktien-System.
 *
 * Jede Aktie hat einen eigenen Kurs, der angebotsabhängig ist:
 * Je mehr Aktien im Umlauf sind, desto höher der Kurs — je weniger, desto
 * niedriger. Der Kurs reagiert sofort auf jede Transaktion und wird zudem
 * alle 15 Minuten als Preispunkt für die 7-Tage-Historie gespeichert
 * (Webseite: /aktien).
 *
 * Gekauft wird mit PC Coins (Krypto-Wallet). Beim Verkauf fließen die
 * PC Coins zurück ins Krypto-Wallet.
 *
 * DataStore-Keys:
 *   aktie-bal-{stockId}-{guildId}-{userId}       → long (Aktien im Besitz)
 *   aktie-supply-{stockId}-{guildId}             → long Gesamt-Umlauf
 *   aktie-invested-{stockId}-{guildId}-{userId}  → long eingesetzte PC Coins (für Gewinn/Verlust)
 *   aktie-history-{stockId}-{guildId}            → JSON [{ts,rate}, …] (max. 7 Tage)
 */
public final class AktienManager {

    private static final Logger log = LoggerFactory.getLogger(AktienManager.class);
    private static final Gson GSON = new GsonBuilder().create();

    /** Historie: 7 Tage rückverfolgbar. */
    private static final long HISTORY_HOURS = 7L * 24L;

    /** Eine Aktien-Definition (ID, Name, Emoji, Startkurs, Preisschritt pro Aktie im Umlauf). */
    public record Aktie(String id, String name, String emoji, double baseRate, double priceStep) {}

    /** Alle verfügbaren Aktien. */
    public static final List<Aktie> STOCKS = List.of(
        new Aktie("maze",        "Maze Bank",     "🏦", 25.0,  25.0 / 100_000.0),
        new Aktie("benefactor",  "Benefactor",    "🚗", 100.0, 100.0 / 100_000.0),
        new Aktie("goldwand",    "Goldwand",      "🥇", 150.0, 150.0 / 100_000.0),
        new Aktie("diamond",     "The Diamond",   "💎", 250.0, 250.0 / 100_000.0)
    );

    private static boolean started = false;
    private static ScheduledExecutorService scheduler;

    private AktienManager() {}

    /** Startet den Kurs-Snapshot-Scheduler (einmalig nach Bot-Start). */
    public static synchronized void init(Guild guild) {
        if (started) return;
        started = true;
        scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "aktien-scheduler");
            t.setDaemon(true);
            return t;
        });
        scheduler.scheduleAtFixedRate(() -> {
            for (Aktie a : STOCKS) snapshot(guild.getId(), a.id());
        }, 15, 15, TimeUnit.MINUTES);
        log.info("[Aktien] Kurs-Snapshot-Scheduler gestartet (alle 15 Minuten, {} Aktien).", STOCKS.size());
    }

    public static Aktie findStock(String stockId) {
        for (Aktie a : STOCKS) if (a.id().equals(stockId)) return a;
        return null;
    }

    // ── Keys ──────────────────────────────────────────────────────────────────

    private static String balKey(String stockId, String guildId, String userId) {
        return "aktie-bal-" + stockId + "-" + guildId + "-" + userId;
    }

    private static String supplyKey(String stockId, String guildId) {
        return "aktie-supply-" + stockId + "-" + guildId;
    }

    private static String investedKey(String stockId, String guildId, String userId) {
        return "aktie-invested-" + stockId + "-" + guildId + "-" + userId;
    }

    // ── Balance ───────────────────────────────────────────────────────────────

    public static long getShares(String stockId, String guildId, String userId) {
        String raw = DataStore.readString(balKey(stockId, guildId, userId));
        if (raw == null || raw.isBlank()) return 0L;
        try { return Math.max(0L, Long.parseLong(raw.trim())); }
        catch (NumberFormatException e) { return 0L; }
    }

    private static void setShares(String stockId, String guildId, String userId, long shares) {
        DataStore.writeString(balKey(stockId, guildId, userId), String.valueOf(Math.max(0L, shares)));
    }

    /** Eingesetzte PC Coins (Summe aller Käufe abzgl. proportionaler Verkäufe). */
    public static long getInvested(String stockId, String guildId, String userId) {
        String raw = DataStore.readString(investedKey(stockId, guildId, userId));
        if (raw == null || raw.isBlank()) return 0L;
        try { return Math.max(0L, Long.parseLong(raw.trim())); }
        catch (NumberFormatException e) { return 0L; }
    }

    private static void setInvested(String stockId, String guildId, String userId, long invested) {
        DataStore.writeString(investedKey(stockId, guildId, userId), String.valueOf(Math.max(0L, invested)));
    }

    // ── Umlauf / Kurs ─────────────────────────────────────────────────────────

    public static long getSupply(String stockId, String guildId) {
        String raw = DataStore.readString(supplyKey(stockId, guildId));
        if (raw == null || raw.isBlank()) return 0L;
        try { return Math.max(0L, Long.parseLong(raw.trim())); }
        catch (NumberFormatException e) { return 0L; }
    }

    private static void setSupply(String stockId, String guildId, long supply) {
        DataStore.writeString(supplyKey(stockId, guildId), String.valueOf(Math.max(0L, supply)));
    }

    /** Aktueller Kurs einer Aktie in PC Coins (angebotsabhängig). */
    public static double getRate(Aktie stock, String guildId) {
        return stock.baseRate() + getSupply(stock.id(), guildId) * stock.priceStep();
    }

    // ── Operationen ───────────────────────────────────────────────────────────

    /**
     * Kauft Aktien mit {pcCoins} PC Coins aus dem Krypto-Wallet.
     * Gibt Fehlermeldung zurück, null bei Erfolg.
     */
    public static String buy(String guildId, String userId, String stockId, long pcCoins) {
        Aktie stock = findStock(stockId);
        if (stock == null) return "Unbekannte Aktie.";
        if (pcCoins <= 0) return "Betrag muss größer als 0 sein.";

        double rate = getRate(stock, guildId);
        long shares = (long) (pcCoins / rate);
        if (shares <= 0)
            return "Der Betrag reicht nicht für **1 Aktie** (aktueller Kurs: " + formatRate(rate) + ").";

        long wallet = KryptoManager.getBalance(guildId, userId);
        if (wallet < pcCoins)
            return "Dein PC Coin Guthaben (**" + KryptoManager.formatCoins(wallet) + "**) reicht nicht aus.";

        // PC Coins aus dem Krypto-Wallet abbuchen (Umlauf sinkt → Krypto-Kurs sinkt leicht)
        if (!KryptoManager.remove(guildId, userId, pcCoins))
            return "Dein PC Coin Guthaben reicht nicht aus.";

        setShares(stockId, guildId, userId, getShares(stockId, guildId, userId) + shares);
        setSupply(stockId, guildId, getSupply(stockId, guildId) + shares);
        setInvested(stockId, guildId, userId, getInvested(stockId, guildId, userId) + pcCoins);
        snapshot(guildId, stockId);
        return null;
    }

    /**
     * Verkauft {shares} Aktien und schreibt den Erlös in PC Coins ins Krypto-Wallet.
     * Gibt Fehlermeldung zurück, null bei Erfolg.
     */
    public static String sell(String guildId, String userId, String stockId, long shares) {
        Aktie stock = findStock(stockId);
        if (stock == null) return "Unbekannte Aktie.";
        if (shares <= 0) return "Menge muss größer als 0 sein.";

        long held = getShares(stockId, guildId, userId);
        if (held < shares)
            return "Du hast nur **" + formatShares(held) + "** dieser Aktie.";

        double rate = getRate(stock, guildId);
        long pcCoins = Math.round(shares * rate);

        // Eingesetztes Kapital proportional reduzieren
        long invested = getInvested(stockId, guildId, userId);
        long invReduce = Math.round((double) invested * shares / held);
        setInvested(stockId, guildId, userId, invested - invReduce);

        setShares(stockId, guildId, userId, held - shares);
        setSupply(stockId, guildId, Math.max(0L, getSupply(stockId, guildId) - shares));

        // Erlös als PC Coins ins Krypto-Wallet (Umlauf steigt → Krypto-Kurs steigt leicht)
        KryptoManager.add(guildId, userId, pcCoins);
        snapshot(guildId, stockId);
        return null;
    }

    // ── Preishistorie (7 Tage) ────────────────────────────────────────────────

    public static class RatePoint {
        public final long ts;      // Unix-Sekunden
        public final double rate;  // Kurs in PC Coins
        public RatePoint(long ts, double rate) { this.ts = ts; this.rate = rate; }
    }

    private static String historyKey(String stockId, String guildId) {
        return "aktie-history-" + stockId + "-" + guildId;
    }

    /** Fügt einen Kurs-Punkt hinzu und entfernt alles älter als 7 Tage. */
    public static synchronized void snapshot(String guildId, String stockId) {
        Aktie stock = findStock(stockId);
        if (stock == null) return;
        List<RatePoint> pts = readHistory(stockId, guildId);
        pts.add(new RatePoint(System.currentTimeMillis() / 1000, getRate(stock, guildId)));
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
        DataStore.writeString(historyKey(stockId, guildId), GSON.toJson(arr));
    }

    /** Liest die Preishistorie (älteste zuerst, max. 7 Tage). */
    public static List<RatePoint> readHistory(String stockId, String guildId) {
        List<RatePoint> pts = new ArrayList<>();
        String raw = DataStore.readString(historyKey(stockId, guildId));
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
        return String.format("%,.2f", rate).replace(',', '.');
    }

    public static String formatShares(long shares) {
        return String.format("%,d", shares).replace(',', '.') + " Aktien";
    }
}
