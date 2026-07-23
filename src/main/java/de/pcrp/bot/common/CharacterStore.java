package de.pcrp.bot.common;

import com.google.gson.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Persistente Speicherung von Charakter-Daten.
 *
 * Datei: /app/data/characters-{guildId}.json
 * Schlüssel: Discord-User-ID (als String)
 *
 * Charakter-Felder (legal):
 *   type, discordUsername, discordUserId, psnName,
 *   firstName, lastName, birthDate, birthPlace, nationality, residence,
 *   photoContentType, registeredAt
 *
 * Charakter-Felder (illegal):
 *   type, discordUsername, discordUserId, psnName,
 *   firstName, lastName, registeredAt
 */
public final class CharacterStore {

    private static final Logger log  = LoggerFactory.getLogger(CharacterStore.class);
    private static final Gson   GSON = new GsonBuilder().setPrettyPrinting().create();

    private CharacterStore() {}

    // ── Speichern ──────────────────────────────────────────────────

    public static void save(long guildId, long userId, JsonObject data) {
        JsonObject root = loadAll(guildId);
        root.add(String.valueOf(userId), data);
        DataStore.writeString(file(guildId), GSON.toJson(root));
    }

    // ── Lesen ──────────────────────────────────────────────────────

    /** Gibt null zurück, wenn kein Charakter für diesen Nutzer vorhanden ist. */
    public static JsonObject get(long guildId, long userId) {
        JsonElement el = loadAll(guildId).get(String.valueOf(userId));
        if (el == null || !el.isJsonObject()) return null;
        return el.getAsJsonObject();
    }

    public static boolean exists(long guildId, long userId) {
        return loadAll(guildId).has(String.valueOf(userId));
    }

    public static JsonObject loadAll(long guildId) {
        String raw = DataStore.readString(file(guildId));
        if (raw == null || raw.isBlank()) return new JsonObject();
        try {
            return JsonParser.parseString(raw).getAsJsonObject();
        } catch (Exception e) {
            log.warn("[CharacterStore] Datei konnte nicht gelesen werden für Guild {}.", guildId, e);
            return new JsonObject();
        }
    }

    // ── Intern ────────────────────────────────────────────────────

    private static String file(long guildId) {
        return "characters-" + guildId + ".json";
    }

    /** Hilfsmethode: String sicher aus JsonObject lesen. */
    public static String str(JsonObject obj, String key) {
        JsonElement el = obj.get(key);
        return (el != null && !el.isJsonNull()) ? el.getAsString() : "-";
    }
}
