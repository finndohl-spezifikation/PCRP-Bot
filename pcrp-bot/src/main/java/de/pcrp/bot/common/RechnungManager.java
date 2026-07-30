package de.pcrp.bot.common;

import com.google.gson.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Verwaltet offene Rechnungen für Spieler.
 * Rechnungen können über das Online-Banking eingesehen und bezahlt werden.
 */
public final class RechnungManager {

    private static final Logger log = LoggerFactory.getLogger(RechnungManager.class);
    private static final Gson GSON = new GsonBuilder().create();

    private RechnungManager() {}

    /** Eine einzelne Rechnung. */
    public static class Rechnung {
        public final String id;
        public final long   amount;
        public final String beschreibung;
        public final long   ts;      // Unix-Sekunden
        public final boolean bezahlt;

        public Rechnung(String id, long amount, String beschreibung, long ts, boolean bezahlt) {
            this.id = id;
            this.amount = amount;
            this.beschreibung = beschreibung;
            this.ts = ts;
            this.bezahlt = bezahlt;
        }

        public Rechnung mitBezahlt() {
            return new Rechnung(id, amount, beschreibung, ts, true);
        }
    }

    // ── Keys ──────────────────────────────────────────────────────────────────

    private static String key(String guildId, String userId) {
        return "rechnungen-" + guildId + "-" + userId;
    }

    // ── Rechnung hinzufügen ───────────────────────────────────────────────────

    /** Fügt eine neue offene Rechnung für einen Spieler hinzu. */
    public static void addRechnung(String guildId, String userId,
                                    long amount, String beschreibung) {
        List<Rechnung> list = getAll(guildId, userId);
        String id = UUID.randomUUID().toString().substring(0, 8);
        list.add(new Rechnung(id, amount, beschreibung, System.currentTimeMillis() / 1000, false));
        save(guildId, userId, list);
        log.info("[Rechnung] Rechnung {} für {} ({}): {} $ - {}", id, userId, guildId, amount, beschreibung);
    }

    // ── Alle Rechnungen (offen + bezahlt) ─────────────────────────────────────

    public static List<Rechnung> getAll(String guildId, String userId) {
        String raw = DataStore.readString(key(guildId, userId));
        if (raw == null || raw.isBlank()) return new ArrayList<>();
        try {
            JsonArray arr = JsonParser.parseString(raw).getAsJsonArray();
            List<Rechnung> list = new ArrayList<>();
            for (JsonElement el : arr) {
                JsonObject o = el.getAsJsonObject();
                list.add(new Rechnung(
                    o.get("id").getAsString(),
                    o.get("amount").getAsLong(),
                    o.get("beschreibung").getAsString(),
                    o.get("ts").getAsLong(),
                    o.has("bezahlt") && o.get("bezahlt").getAsBoolean()
                ));
            }
            return list;
        } catch (Exception e) {
            return new ArrayList<>();
        }
    }

    /** Nur offene (unbezahlte) Rechnungen. */
    public static List<Rechnung> getOffene(String guildId, String userId) {
        return getAll(guildId, userId).stream()
            .filter(r -> !r.bezahlt)
            .collect(Collectors.toList());
    }

    /** Nur bezahlte Rechnungen. */
    public static List<Rechnung> getBezahlte(String guildId, String userId) {
        return getAll(guildId, userId).stream()
            .filter(r -> r.bezahlt)
            .collect(Collectors.toList());
    }

    // ── Bezahlen ──────────────────────────────────────────────────────────────

    /**
     * Bezahlt EINE Rechnung. Gibt null bei Erfolg, Fehlermeldung bei Fehler zurück.
     * Das Geld wird vom Bankkonto abgezogen.
     */
    public static String payRechnung(String guildId, String userId, String rechnungId) {
        List<Rechnung> list = getAll(guildId, userId);
        for (int i = 0; i < list.size(); i++) {
            Rechnung r = list.get(i);
            if (r.id.equals(rechnungId) && !r.bezahlt) {
                long balance = BankManager.getBalance(guildId, userId);
                if (balance < r.amount) {
                    return "Nicht genug Geld auf dem Konto. Benötigt: **"
                        + BankManager.formatAmount(r.amount) + "**, hast: **"
                        + BankManager.formatAmount(balance) + "**.";
                }
                BankManager.setBalance(guildId, userId, balance - r.amount);
                BankManager.addTransaction(guildId, userId, "RECHNUNG", r.amount, r.beschreibung);
                list.set(i, r.mitBezahlt());
                save(guildId, userId, list);
                log.info("[Rechnung] Rechnung {} von {} bezahlt ({} $).", rechnungId, userId, r.amount);
                return null;
            }
        }
        return "Rechnung mit der ID `" + rechnungId + "` wurde nicht gefunden oder ist bereits bezahlt.";
    }

    /**
     * Bezahlt ALLE offenen Rechnungen. Gibt null bei Erfolg, Fehlermeldung bei Fehler zurück.
     */
    public static String payAll(String guildId, String userId) {
        List<Rechnung> offene = getOffene(guildId, userId);
        if (offene.isEmpty()) return "Du hast keine offenen Rechnungen.";

        long total = offene.stream().mapToLong(r -> r.amount).sum();
        long balance = BankManager.getBalance(guildId, userId);
        if (balance < total) {
            return "Nicht genug Geld. Benötigt: **" + BankManager.formatAmount(total)
                + "**, hast: **" + BankManager.formatAmount(balance) + "**.";
        }

        BankManager.setBalance(guildId, userId, balance - total);
        for (Rechnung r : offene) {
            BankManager.addTransaction(guildId, userId, "RECHNUNG", r.amount, r.beschreibung);
        }

        List<Rechnung> all = getAll(guildId, userId);
        List<Rechnung> updated = new ArrayList<>();
        for (Rechnung r : all) {
            updated.add(r.bezahlt ? r : r.mitBezahlt());
        }
        save(guildId, userId, updated);

        log.info("[Rechnung] Alle {} Rechnungen von {} bezahlt ({} $).", offene.size(), userId, total);
        return null;
    }

    // ── Hilfsmethoden ─────────────────────────────────────────────────────────

    private static void save(String guildId, String userId, List<Rechnung> list) {
        JsonArray arr = new JsonArray();
        for (Rechnung r : list) {
            JsonObject o = new JsonObject();
            o.addProperty("id", r.id);
            o.addProperty("amount", r.amount);
            o.addProperty("beschreibung", r.beschreibung);
            o.addProperty("ts", r.ts);
            o.addProperty("bezahlt", r.bezahlt);
            arr.add(o);
        }
        DataStore.writeString(key(guildId, userId), GSON.toJson(arr));
    }

    /** Formatiert eine Rechnung als einzeiligen Text. */
    public static String formatRechnung(Rechnung r) {
        String status = r.bezahlt ? "✅" : "🔴";
        return status + " `" + r.id + "` — **" + BankManager.formatAmount(r.amount)
            + "** — " + r.beschreibung + " (<t:" + r.ts + ":d>)";
    }
}
