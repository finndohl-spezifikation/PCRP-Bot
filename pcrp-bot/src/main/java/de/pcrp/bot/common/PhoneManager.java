package de.pcrp.bot.common;

import com.google.gson.*;

import java.util.*;

/**
 * Verwaltet Handy-Verträge (Rufnummer + Safe-Pin) und City-Chat-Sessions.
 * DataStore-Key: {@code phone-{guildId}-{userId}} → JSON-Objekt
 */
public final class PhoneManager {

    private static final Gson GSON = new GsonBuilder().create();

    // LA-Vorwahlen
    private static final int[] LA_CODES = {213, 310, 323, 424, 747};

    private PhoneManager() {}

    // ── Datenklassen ──────────────────────────────────────────────────────────

    public static class Contract {
        public String userId;
        public String firstName;
        public String lastName;
        public String phoneNumber;
        public String safePin;
        public long   createdAt;

        public String displayName() { return firstName + " " + lastName; }
    }

    // ── Schlüssel ─────────────────────────────────────────────────────────────

    private static String key(String guildId, String userId) {
        return "phone-" + guildId + "-" + userId;
    }

    private static String allKey(String guildId) {
        return "phone-index-" + guildId;
    }

    // ── Lesen ─────────────────────────────────────────────────────────────────

    public static Contract getContract(String guildId, String userId) {
        String raw = DataStore.readString(key(guildId, userId));
        if (raw == null || raw.isBlank()) return null;
        try {
            JsonObject o = JsonParser.parseString(raw).getAsJsonObject();
            return fromJson(o);
        } catch (Exception e) { return null; }
    }

    public static Contract getContractByNumber(String guildId, String phoneNumber) {
        for (String uid : getUserIds(guildId)) {
            Contract c = getContract(guildId, uid);
            if (c != null && c.phoneNumber.equals(phoneNumber)) return c;
        }
        return null;
    }

    public static List<Contract> getAllContracts(String guildId) {
        List<Contract> list = new ArrayList<>();
        for (String uid : getUserIds(guildId)) {
            Contract c = getContract(guildId, uid);
            if (c != null) list.add(c);
        }
        return list;
    }

    // ── Erstellen / Aktualisieren ─────────────────────────────────────────────

    public static synchronized Contract createContract(
            String guildId, String userId, String firstName, String lastName) {
        Contract c = new Contract();
        c.userId      = userId;
        c.firstName   = firstName;
        c.lastName    = lastName;
        c.phoneNumber = generateUniqueNumber(guildId);
        c.safePin     = generatePin();
        c.createdAt   = System.currentTimeMillis();
        save(guildId, userId, c);
        addToIndex(guildId, userId);
        return c;
    }

    public static synchronized Contract regenerateNumber(String guildId, String userId) {
        Contract c = getContract(guildId, userId);
        if (c == null) return null;
        c.phoneNumber = generateUniqueNumber(guildId);
        c.safePin     = generatePin();
        save(guildId, userId, c);
        return c;
    }

    // ── Nummern-Generierung ───────────────────────────────────────────────────

    private static String generateUniqueNumber(String guildId) {
        Set<String> used = new HashSet<>();
        for (Contract c : getAllContracts(guildId)) used.add(c.phoneNumber);
        Random rnd = new Random();
        String number;
        int tries = 0;
        do {
            int code   = LA_CODES[rnd.nextInt(LA_CODES.length)];
            int middle = 200 + rnd.nextInt(800);
            int last   = 1000 + rnd.nextInt(9000);
            number = "(" + code + ") " + middle + "-" + last;
            if (++tries > 10_000) throw new IllegalStateException("Keine freie Nummer gefunden.");
        } while (used.contains(number));
        return number;
    }

    public static String generatePin() {
        return String.format("%04d", 1000 + new Random().nextInt(9000));
    }

    // ── Session (City Chat Login) ─────────────────────────────────────────────

    public static String createSession(String guildId, String phoneNumber) {
        String token = UUID.randomUUID().toString().replace("-", "");
        JsonObject o = new JsonObject();
        o.addProperty("guildId",     guildId);
        o.addProperty("phoneNumber", phoneNumber);
        o.addProperty("created",     System.currentTimeMillis());
        DataStore.writeString("city-session-" + token, GSON.toJson(o));
        return token;
    }

    /** Gibt Vertrag zurück wenn Session gültig (max 7 Tage), sonst null. */
    public static Contract validateSession(String token) {
        if (token == null || token.isBlank()) return null;
        String raw = DataStore.readString("city-session-" + token);
        if (raw == null) return null;
        try {
            JsonObject o = JsonParser.parseString(raw).getAsJsonObject();
            long created = o.get("created").getAsLong();
            if (System.currentTimeMillis() - created > 7L * 24 * 3600 * 1000) {
                DataStore.deleteKey("city-session-" + token);
                return null;
            }
            String guildId     = o.get("guildId").getAsString();
            String phoneNumber = o.get("phoneNumber").getAsString();
            return getContractByNumber(guildId, phoneNumber);
        } catch (Exception e) { return null; }
    }

    // ── Intern ────────────────────────────────────────────────────────────────

    private static void save(String guildId, String userId, Contract c) {
        JsonObject o = new JsonObject();
        o.addProperty("userId",      c.userId);
        o.addProperty("firstName",   c.firstName);
        o.addProperty("lastName",    c.lastName);
        o.addProperty("phoneNumber", c.phoneNumber);
        o.addProperty("safePin",     c.safePin);
        o.addProperty("createdAt",   c.createdAt);
        DataStore.writeString(key(guildId, userId), GSON.toJson(o));
    }

    private static Contract fromJson(JsonObject o) {
        Contract c = new Contract();
        c.userId      = o.get("userId").getAsString();
        c.firstName   = o.get("firstName").getAsString();
        c.lastName    = o.get("lastName").getAsString();
        c.phoneNumber = o.get("phoneNumber").getAsString();
        c.safePin     = o.get("safePin").getAsString();
        c.createdAt   = o.get("createdAt").getAsLong();
        return c;
    }

    // ── Index (alle User-IDs mit Vertrag) ─────────────────────────────────────

    private static List<String> getUserIds(String guildId) {
        String raw = DataStore.readString(allKey(guildId));
        if (raw == null || raw.isBlank()) return new ArrayList<>();
        try {
            JsonArray arr = JsonParser.parseString(raw).getAsJsonArray();
            List<String> ids = new ArrayList<>();
            arr.forEach(el -> ids.add(el.getAsString()));
            return ids;
        } catch (Exception e) { return new ArrayList<>(); }
    }

    private static synchronized void addToIndex(String guildId, String userId) {
        List<String> ids = getUserIds(guildId);
        if (!ids.contains(userId)) {
            ids.add(userId);
            JsonArray arr = new JsonArray();
            ids.forEach(arr::add);
            DataStore.writeString(allKey(guildId), GSON.toJson(arr));
        }
    }
}
