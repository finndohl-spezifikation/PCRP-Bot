package de.pcrp.bot.common;

import com.google.gson.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/** Bankkonto-Verwaltung: Kontostand + Transaktionshistorie. */
public final class BankManager {

    private static final Logger log     = LoggerFactory.getLogger(BankManager.class);
    private static final Gson   GSON    = new GsonBuilder().create();
    private static final int    MAX_TX  = 10;

    private BankManager() {}

    // ── Datenklasse ───────────────────────────────────────────────────────────

    public static class BankTx {
        public final String type;   // EINZAHLUNG | AUSZAHLUNG | ÜBERWEISUNG_RAUS | ÜBERWEISUNG_REIN | ADMIN_GABE | ADMIN_ENTZUG
        public final long   amount;
        public final String with;   // Gegenpartei-Name (nullable)
        public final long   ts;     // Unix-Sekunden

        public BankTx(String type, long amount, String with, long ts) {
            this.type = type; this.amount = amount; this.with = with; this.ts = ts;
        }
    }

    // ── Kontostand ────────────────────────────────────────────────────────────

    public static long getBalance(String guildId, String userId) {
        String raw = DataStore.readString(balKey(guildId, userId));
        if (raw == null || raw.isBlank()) return 0L;
        try { return Long.parseLong(raw.trim()); }
        catch (Exception e) { return 0L; }
    }

    public static void setBalance(String guildId, String userId, long amount) {
        DataStore.writeString(balKey(guildId, userId), String.valueOf(Math.max(0, amount)));
    }

    // ── Operationen ───────────────────────────────────────────────────────────

    /** Bargeld → Konto (Einzahlung). Gibt Fehlermeldung zurück, null bei Erfolg. */
    public static String deposit(String guildId, String userId, long amount) {
        if (amount <= 0) return "Betrag muss größer als 0 sein.";
        long cash = BargeldManager.get(guildId, userId);
        if (cash < amount)
            return "Du hast nur **" + formatAmount(cash) + "** Bargeld.";
        BargeldManager.remove(guildId, userId, amount);
        setBalance(guildId, userId, getBalance(guildId, userId) + amount);
        addTransaction(guildId, userId, "EINZAHLUNG", amount, null);
        return null;
    }

    /** Konto → Bargeld (Auszahlung). Gibt Fehlermeldung zurück, null bei Erfolg. */
    public static String withdraw(String guildId, String userId, long amount) {
        if (amount <= 0) return "Betrag muss größer als 0 sein.";
        long bal = getBalance(guildId, userId);
        if (bal < amount)
            return "Dein Kontostand (**" + formatAmount(bal) + "**) reicht nicht aus.";
        setBalance(guildId, userId, bal - amount);
        BargeldManager.add(guildId, userId, amount);
        addTransaction(guildId, userId, "AUSZAHLUNG", amount, null);
        return null;
    }

    /** Überweisung Sender → Empfänger. Gibt Fehlermeldung zurück, null bei Erfolg. */
    public static String transfer(String guildId,
                                   String senderId, String receiverId,
                                   long amount,
                                   String senderName, String receiverName) {
        if (amount <= 0) return "Betrag muss größer als 0 sein.";
        long senderBal = getBalance(guildId, senderId);
        if (senderBal < amount)
            return "Dein Kontostand (**" + formatAmount(senderBal) + "**) reicht nicht aus.";
        setBalance(guildId, senderId,   senderBal - amount);
        setBalance(guildId, receiverId, getBalance(guildId, receiverId) + amount);
        addTransaction(guildId, senderId,   "ÜBERWEISUNG_RAUS", amount, receiverName);
        addTransaction(guildId, receiverId, "ÜBERWEISUNG_REIN", amount, senderName);
        log.info("[Bank] Überweisung {} → {} : {}$", senderName, receiverName, amount);
        return null;
    }

    /** Admin: Geld hinzufügen. isBank=true → Kontogeld, false → Bargeld. */
    public static void adminAdd(String guildId, String userId, long amount, boolean isBank) {
        if (isBank) {
            setBalance(guildId, userId, getBalance(guildId, userId) + amount);
            addTransaction(guildId, userId, "ADMIN_GABE", amount, null);
        } else {
            BargeldManager.add(guildId, userId, amount);
        }
    }

    /** Admin: Geld entfernen. Gibt Fehlermeldung zurück, null bei Erfolg. */
    public static String adminRemove(String guildId, String userId, long amount, boolean isBank) {
        if (isBank) {
            long bal = getBalance(guildId, userId);
            if (bal < amount)
                return "Spieler hat nur **" + formatAmount(bal) + "** auf dem Konto.";
            setBalance(guildId, userId, bal - amount);
            addTransaction(guildId, userId, "ADMIN_ENTZUG", amount, null);
            return null;
        } else {
            long cash = BargeldManager.get(guildId, userId);
            if (cash < amount)
                return "Spieler hat nur **" + formatAmount(cash) + "** Bargeld.";
            BargeldManager.remove(guildId, userId, amount);
            return null;
        }
    }

    // ── Transaktionen ─────────────────────────────────────────────────────────

    public static void addTransaction(String guildId, String userId,
                                       String type, long amount, String with) {
        List<BankTx> txs = getTransactions(guildId, userId);
        txs.add(0, new BankTx(type, amount, with, System.currentTimeMillis() / 1000));
        if (txs.size() > MAX_TX) txs = txs.subList(0, MAX_TX);
        saveTx(guildId, userId, txs);
    }

    public static List<BankTx> getTransactions(String guildId, String userId) {
        String raw = DataStore.readString(txKey(guildId, userId));
        if (raw == null || raw.isBlank()) return new ArrayList<>();
        try {
            JsonArray arr = JsonParser.parseString(raw).getAsJsonArray();
            List<BankTx> list = new ArrayList<>();
            for (JsonElement el : arr) {
                JsonObject o = el.getAsJsonObject();
                String w = (o.has("with") && !o.get("with").isJsonNull())
                    ? o.get("with").getAsString() : null;
                list.add(new BankTx(
                    o.get("type").getAsString(),
                    o.get("amount").getAsLong(),
                    w,
                    o.get("ts").getAsLong()
                ));
            }
            return list;
        } catch (Exception e) {
            return new ArrayList<>();
        }
    }

    /** Formatiert eine Transaktion als einzeiligen Text. */
    public static String formatTx(BankTx tx) {
        String icon, label;
        switch (tx.type) {
            case "EINZAHLUNG"       -> { icon = "💳"; label = "Einzahlung"; }
            case "AUSZAHLUNG"       -> { icon = "💵"; label = "Auszahlung"; }
            case "ÜBERWEISUNG_RAUS" -> { icon = "📤"; label = "An " + (tx.with != null ? tx.with : "?"); }
            case "ÜBERWEISUNG_REIN" -> { icon = "📥"; label = "Von " + (tx.with != null ? tx.with : "?"); }
            case "ADMIN_GABE"       -> { icon = "⬆️"; label = "Gutschrift (Admin)"; }
            case "ADMIN_ENTZUG"     -> { icon = "⬇️"; label = "Abzug (Admin)"; }
            default                 -> { icon = "•";  label = tx.type; }
        }
        boolean isIn = tx.type.equals("EINZAHLUNG")
            || tx.type.equals("ÜBERWEISUNG_REIN")
            || tx.type.equals("ADMIN_GABE");
        String sign = isIn ? "+" : "-";
        return icon + " **" + label + "** — " + sign + formatAmount(tx.amount)
            + " <t:" + tx.ts + ":d>";
    }

    // ── Hilfsfunktionen ───────────────────────────────────────────────────────

    public static String formatAmount(long v) {
        return String.format("%,d", v).replace(',', '.') + "$";
    }

    /** Bargeld-Bestand lesen (aus BargeldManager). */
    private static long getCash(String guildId, String userId) {
        return BargeldManager.get(guildId, userId);
    }

    private static int safeInt(long v) {
        return (int) Math.min(v, Integer.MAX_VALUE);
    }

    private static void saveTx(String guildId, String userId, List<BankTx> txs) {
        JsonArray arr = new JsonArray();
        for (BankTx tx : txs) {
            JsonObject o = new JsonObject();
            o.addProperty("type",   tx.type);
            o.addProperty("amount", tx.amount);
            if (tx.with != null) o.addProperty("with", tx.with);
            else                 o.add("with", JsonNull.INSTANCE);
            o.addProperty("ts", tx.ts);
            arr.add(o);
        }
        DataStore.writeString(txKey(guildId, userId), GSON.toJson(arr));
    }

    private static String balKey(String guildId, String userId) {
        return "bank-bal-" + guildId + "-" + userId;
    }

    private static String txKey(String guildId, String userId) {
        return "bank-tx-" + guildId + "-" + userId;
    }
}
