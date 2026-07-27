package de.pcrp.bot.web;

import com.google.gson.*;
import de.pcrp.bot.common.DataStore;
import de.pcrp.bot.common.PhoneManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Arrays;
import java.util.List;
import java.util.UUID;

/**
 * Migriert alle City-Chat-Daten wenn ein Spieler seine Handynummer ändert.
 *
 * Was passiert:
 * - Profil, Kontakte, Blockliste, Status, Firma-Links → neuer Schlüssel
 * - Chat-Nachrichten → neues chatId-Format, Systemnachricht eingefügt
 * - Read-Keys beider Seiten → neues chatId-Format
 * - Alte Nummer in fremden Kontakt- und Blocklisten → ersetzt durch neue Nummer
 */
public final class CityChatMigration {

    private static final Logger log = LoggerFactory.getLogger(CityChatMigration.class);
    private static final Gson GSON = new GsonBuilder().create();

    private CityChatMigration() {}

    public static void migrate(String guildId, String oldPhone, String newPhone) {
        log.info("[CityChat] Nummernmigration {} → {} (Guild {})", oldPhone, newPhone, guildId);

        String oldNorm = oldPhone.replaceAll("[^0-9]", "");
        String newNorm = newPhone.replaceAll("[^0-9]", "");

        // ── 1. Eigene Datei-Schlüssel umbenennen ───────────────────────────────
        rename("city-profile-"  + guildId + "-" + oldNorm,  "city-profile-"  + guildId + "-" + newNorm);
        rename("city-contacts-" + guildId + "-" + oldNorm,  "city-contacts-" + guildId + "-" + newNorm);
        rename("city-blocked-"  + guildId + "-" + oldNorm,  "city-blocked-"  + guildId + "-" + newNorm);
        rename("city-firma-"    + guildId + "-" + oldNorm,  "city-firma-"    + guildId + "-" + newNorm);
        rename("city-status-"   + guildId + "-" + oldPhone, "city-status-"   + guildId + "-" + newPhone);
        rename("city-call-sig-" + guildId + "-" + oldNorm,  "city-call-sig-" + guildId + "-" + newNorm);

        // ── 2. Nachrichten + Read-Keys pro Chat-Partner ────────────────────────
        List<PhoneManager.Contract> all = PhoneManager.getAllContracts(guildId);
        for (PhoneManager.Contract partner : all) {
            if (partner.phoneNumber.equals(newPhone)) continue;

            String oldChatId = chatId(oldPhone, partner.phoneNumber);
            String newChatId = chatId(newPhone, partner.phoneNumber);
            if (oldChatId.equals(newChatId)) continue;

            // Nachrichten umbenennen + Systemnachricht anhängen
            String oldMsgKey = "city-msgs-" + guildId + "-" + oldChatId;
            String newMsgKey = "city-msgs-" + guildId + "-" + newChatId;
            String rawMsgs   = DataStore.readString(oldMsgKey);
            if (rawMsgs != null) {
                JsonArray arr;
                try { arr = JsonParser.parseString(rawMsgs).getAsJsonArray(); }
                catch (Exception e) { arr = new JsonArray(); }

                JsonObject sysMsg = new JsonObject();
                sysMsg.addProperty("id",      UUID.randomUUID().toString());
                sysMsg.addProperty("from",    "__system__");
                sysMsg.addProperty("content", "📞 " + oldPhone + " hat jetzt eine neue Nummer: " + newPhone);
                sysMsg.addProperty("type",    "system");
                sysMsg.addProperty("ts",      System.currentTimeMillis());
                arr.add(sysMsg);

                DataStore.writeString(newMsgKey, GSON.toJson(arr));
                DataStore.deleteKey(oldMsgKey);
            }

            // Read-Keys: eigene Seite
            rename("city-read-" + guildId + "-" + oldPhone + "-" + oldChatId,
                   "city-read-" + guildId + "-" + newPhone + "-" + newChatId);

            // Read-Keys: Partner-Seite
            rename("city-read-" + guildId + "-" + partner.phoneNumber + "-" + oldChatId,
                   "city-read-" + guildId + "-" + partner.phoneNumber + "-" + newChatId);
        }

        // ── 3. Alte Nummer in fremden Kontaktlisten ersetzen ──────────────────
        for (PhoneManager.Contract partner : all) {
            if (partner.phoneNumber.equals(newPhone)) continue;
            String key = "city-contacts-" + guildId + "-" + partner.phoneNumber.replaceAll("[^0-9]", "");
            String raw = DataStore.readString(key);
            if (raw == null) continue;
            try {
                JsonArray contacts = JsonParser.parseString(raw).getAsJsonArray();
                boolean changed = false;
                for (JsonElement el : contacts) {
                    JsonObject c = el.getAsJsonObject();
                    if (oldPhone.equals(c.has("number") ? c.get("number").getAsString() : null)) {
                        c.addProperty("number", newPhone);
                        changed = true;
                    }
                }
                if (changed) DataStore.writeString(key, GSON.toJson(contacts));
            } catch (Exception ignored) {}
        }

        // ── 4. Alte Nummer in fremden Blocklisten ersetzen ────────────────────
        for (PhoneManager.Contract partner : all) {
            if (partner.phoneNumber.equals(newPhone)) continue;
            String key = "city-blocked-" + guildId + "-" + partner.phoneNumber.replaceAll("[^0-9]", "");
            String raw = DataStore.readString(key);
            if (raw == null) continue;
            try {
                JsonArray blocked = JsonParser.parseString(raw).getAsJsonArray();
                boolean changed = false;
                JsonArray updated = new JsonArray();
                for (JsonElement el : blocked) {
                    String num = el.getAsString();
                    if (oldPhone.equals(num)) { updated.add(newPhone); changed = true; }
                    else updated.add(num);
                }
                if (changed) DataStore.writeString(key, GSON.toJson(updated));
            } catch (Exception ignored) {}
        }

        log.info("[CityChat] Migration abgeschlossen: {} → {}", oldPhone, newPhone);
    }

    // ── Hilfsmethoden ──────────────────────────────────────────────────────────

    private static void rename(String oldKey, String newKey) {
        String content = DataStore.readString(oldKey);
        if (content == null) return;
        DataStore.writeString(newKey, content);
        DataStore.deleteKey(oldKey);
    }

    /** Gleiche Logik wie CityChatHandler.chatId() */
    private static String chatId(String a, String b) {
        String[] sorted = {a, b};
        Arrays.sort(sorted);
        return (sorted[0] + "|" + sorted[1]).replace(" ", "_").replace("(", "").replace(")", "");
    }
}
