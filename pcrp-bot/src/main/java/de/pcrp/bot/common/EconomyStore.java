package de.pcrp.bot.common;

import com.google.gson.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Persistente Münzverwaltung pro Nutzer und Server.
 *
 * Datei: /app/data/economy-{guildId}.json
 * Format: { "userId": balance_long, ... }
 *
 * Wird aktuell vom Invite-System verwendet:
 *  +1.000 Münzen wenn jemand über den eigenen Invite beitritt.
 *  −1.000 Münzen wenn diese Person den Server wieder verlässt.
 */
public final class EconomyStore {

    private static final Logger log  = LoggerFactory.getLogger(EconomyStore.class);
    private static final Gson   GSON = new GsonBuilder().setPrettyPrinting().create();
    public  static final long   INVITE_REWARD = 1_000L;

    private EconomyStore() {}

    // ── Lesen ─────────────────────────────────────────────────────

    public static long getBalance(long guildId, long userId) {
        JsonElement el = load(guildId).get(String.valueOf(userId));
        return el != null && !el.isJsonNull() ? el.getAsLong() : 0L;
    }

    // ── Schreiben ──────────────────────────────────────────────────

    public static void addCoins(long guildId, long userId, long amount) {
        long newBal = getBalance(guildId, userId) + amount;
        setBalance(guildId, userId, newBal);
        log.debug("[Economy] +{} für {} → Guthaben: {}", amount, userId, newBal);
    }

    /** Zieht ab, aber nie unter 0. */
    public static void subtractCoins(long guildId, long userId, long amount) {
        long newBal = Math.max(0, getBalance(guildId, userId) - amount);
        setBalance(guildId, userId, newBal);
        log.debug("[Economy] -{} für {} → Guthaben: {}", amount, userId, newBal);
    }

    public static void setBalance(long guildId, long userId, long balance) {
        JsonObject root = load(guildId);
        root.addProperty(String.valueOf(userId), balance);
        DataStore.writeString(file(guildId), GSON.toJson(root));
    }

    // ── Intern ────────────────────────────────────────────────────

    private static JsonObject load(long guildId) {
        String raw = DataStore.readString(file(guildId));
        if (raw == null || raw.isBlank()) return new JsonObject();
        try {
            return JsonParser.parseString(raw).getAsJsonObject();
        } catch (Exception e) {
            log.warn("[Economy] Datei konnte nicht gelesen werden für Guild {}.", guildId, e);
            return new JsonObject();
        }
    }

    private static String file(long guildId) {
        return "economy-" + guildId + ".json";
    }
}
