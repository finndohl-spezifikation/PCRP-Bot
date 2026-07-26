package de.pcrp.bot.web;

import com.google.gson.*;
import de.pcrp.bot.common.*;
import io.javalin.http.Context;

import java.time.Instant;
import java.util.*;

/**
 * City-Chat API-Endpunkte für den WebServer.
 * Authentifizierung: Bearer-Token oder Query-Param "token" (Session aus PhoneManager).
 *
 * Routen (werden in WebServer.start() registriert):
 *   POST /api/city-chat/auth                 → Login mit Rufnummer + Safe-Pin
 *   GET  /api/city-chat/me                   → Eigenes Profil
 *   PUT  /api/city-chat/me                   → Profil bearbeiten (status, displayName)
 *   GET  /api/city-chat/contacts             → Kontaktliste
 *   POST /api/city-chat/contacts             → Kontakt speichern {number, name}
 *   DELETE /api/city-chat/contacts/{number}  → Kontakt löschen
 *   GET  /api/city-chat/chats               → Übersicht aller Chats
 *   GET  /api/city-chat/messages/{chatId}   → Nachrichten laden
 *   POST /api/city-chat/messages            → Nachricht senden {to, content, type}
 *   POST /api/city-chat/block               → Blockieren {number}
 *   DELETE /api/city-chat/block/{number}    → Entblockieren
 *   GET  /api/city-chat/blocked             → Blockliste
 */
public final class CityChatHandler {

    private static final Gson GSON = new GsonBuilder().create();

    private CityChatHandler() {}

    // ── Auth ──────────────────────────────────────────────────────────────────

    public static void handleAuth(Context ctx) {
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).json(err("Ungültiger Body")); return; }

        String phone = str(body, "phoneNumber");
        String pin   = str(body, "safePin");
        if (phone == null || pin == null) { ctx.status(400).json(err("Rufnummer und Safe-Pin erforderlich")); return; }

        String guildId = guildId();
        PhoneManager.Contract c = PhoneManager.getContractByNumber(guildId, phone);
        if (c == null || !c.safePin.equals(pin)) {
            ctx.status(401).json(err("Ungültige Zugangsdaten"));
            return;
        }

        String token = PhoneManager.createSession(guildId, phone);
        JsonObject res = new JsonObject();
        res.addProperty("token",       token);
        res.addProperty("phoneNumber", c.phoneNumber);
        res.addProperty("displayName", c.displayName());
        ctx.json(res.toString());
    }

    // ── Profil ────────────────────────────────────────────────────────────────

    public static void handleGetMe(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String guildId = guildId();
        JsonObject profile = loadProfile(guildId, c.phoneNumber);
        JsonObject res = new JsonObject();
        res.addProperty("phoneNumber", c.phoneNumber);
        res.addProperty("displayName", profileStr(profile, "displayName", c.displayName()));
        res.addProperty("status",      profileStr(profile, "status", ""));
        ctx.json(res.toString());
    }

    public static void handleUpdateMe(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).json(err("Ungültiger Body")); return; }
        String guildId = guildId();
        JsonObject profile = loadProfile(guildId, c.phoneNumber);
        if (body.has("status"))      profile.addProperty("status",      str(body, "status"));
        if (body.has("displayName")) profile.addProperty("displayName", str(body, "displayName"));
        saveProfile(guildId, c.phoneNumber, profile);
        ctx.json("{\"ok\":true}");
    }

    // ── Kontakte ──────────────────────────────────────────────────────────────

    public static void handleGetContacts(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        ctx.json(DataStore.readString(contactKey(guildId(), c.phoneNumber)) != null
            ? DataStore.readString(contactKey(guildId(), c.phoneNumber)) : "[]");
    }

    public static void handleAddContact(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).json(err("Ungültiger Body")); return; }
        String number = str(body, "number");
        String name   = str(body, "name");
        if (number == null || name == null) { ctx.status(400).json(err("number und name erforderlich")); return; }
        String guildId = guildId();

        // Existiert die Nummer?
        if (PhoneManager.getContractByNumber(guildId, number) == null) {
            ctx.status(404).json(err("Rufnummer nicht gefunden")); return;
        }

        JsonArray contacts = loadContacts(guildId, c.phoneNumber);
        // Duplikat prüfen
        for (JsonElement el : contacts) {
            if (number.equals(el.getAsJsonObject().get("number").getAsString())) {
                el.getAsJsonObject().addProperty("name", name);
                saveContacts(guildId, c.phoneNumber, contacts);
                ctx.json("{\"ok\":true}"); return;
            }
        }
        JsonObject contact = new JsonObject();
        contact.addProperty("number", number);
        contact.addProperty("name",   name);
        contacts.add(contact);
        saveContacts(guildId, c.phoneNumber, contacts);
        ctx.json("{\"ok\":true}");
    }

    public static void handleDeleteContact(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String number = ctx.pathParam("number");
        String guildId = guildId();
        JsonArray contacts = loadContacts(guildId, c.phoneNumber);
        contacts = removeWhere(contacts, "number", number);
        saveContacts(guildId, c.phoneNumber, contacts);
        ctx.json("{\"ok\":true}");
    }

    // ── Chats ─────────────────────────────────────────────────────────────────

    public static void handleGetChats(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String guildId = guildId();
        List<PhoneManager.Contract> all = PhoneManager.getAllContracts(guildId);
        JsonArray result = new JsonArray();

        for (PhoneManager.Contract other : all) {
            if (other.phoneNumber.equals(c.phoneNumber)) continue;
            String chatId = chatId(c.phoneNumber, other.phoneNumber);
            JsonArray msgs = loadMessages(guildId, chatId);
            if (msgs.size() == 0) continue;

            JsonObject last = msgs.get(msgs.size() - 1).getAsJsonObject();
            // Ungelesen?
            int unread = 0;
            String readKey = "city-read-" + guildId + "-" + c.phoneNumber + "-" + chatId;
            String lastRead = DataStore.readString(readKey);
            long lastReadTs = lastRead != null ? Long.parseLong(lastRead) : 0;
            for (int i = msgs.size() - 1; i >= 0; i--) {
                JsonObject m = msgs.get(i).getAsJsonObject();
                if (!m.get("from").getAsString().equals(c.phoneNumber)) {
                    long ts = m.get("ts").getAsLong();
                    if (ts > lastReadTs) unread++;
                }
            }

            // Kontaktname?
            JsonArray contacts = loadContacts(guildId, c.phoneNumber);
            String displayName = other.phoneNumber;
            for (JsonElement el : contacts) {
                if (other.phoneNumber.equals(el.getAsJsonObject().get("number").getAsString())) {
                    displayName = el.getAsJsonObject().get("name").getAsString();
                    break;
                }
            }

            JsonObject chat = new JsonObject();
            chat.addProperty("chatId",      chatId);
            chat.addProperty("phoneNumber", other.phoneNumber);
            chat.addProperty("displayName", displayName);
            chat.addProperty("lastMessage", last.get("content").getAsString());
            chat.addProperty("lastType",    last.get("type").getAsString());
            chat.addProperty("lastTs",      last.get("ts").getAsLong());
            chat.addProperty("unread",      unread);
            result.add(chat);
        }

        ctx.json(GSON.toJson(result));
    }

    // ── Nachrichten ───────────────────────────────────────────────────────────

    public static void handleGetMessages(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String chatId  = ctx.pathParam("chatId");
        String guildId = guildId();

        JsonArray msgs = loadMessages(guildId, chatId);
        ctx.json(GSON.toJson(msgs));

        // Als gelesen markieren
        DataStore.writeString("city-read-" + guildId + "-" + c.phoneNumber + "-" + chatId,
            String.valueOf(System.currentTimeMillis()));
    }

    public static void handleSendMessage(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).json(err("Ungültiger Body")); return; }

        String to      = str(body, "to");
        String content = str(body, "content");
        String type    = body.has("type") ? str(body, "type") : "text";
        if (to == null || content == null) { ctx.status(400).json(err("to und content erforderlich")); return; }

        String guildId = guildId();

        // Empfänger existiert?
        PhoneManager.Contract recipient = PhoneManager.getContractByNumber(guildId, to);
        if (recipient == null) { ctx.status(404).json(err("Rufnummer nicht gefunden")); return; }

        // Blockiert?
        JsonArray blocked = loadBlocked(guildId, to);
        for (JsonElement el : blocked) {
            if (c.phoneNumber.equals(el.getAsString())) {
                ctx.status(403).json(err("Du wurdest von diesem Nutzer blockiert")); return;
            }
        }

        String chatId = chatId(c.phoneNumber, to);
        JsonArray msgs = loadMessages(guildId, chatId);

        JsonObject msg = new JsonObject();
        msg.addProperty("id",      UUID.randomUUID().toString().substring(0, 8));
        msg.addProperty("from",    c.phoneNumber);
        msg.addProperty("content", content);
        msg.addProperty("type",    type);   // text | voice | emoji
        msg.addProperty("ts",      System.currentTimeMillis());
        msgs.add(msg);

        // Max 200 Nachrichten pro Chat
        while (msgs.size() > 200) msgs.remove(0);

        saveMessages(guildId, chatId, msgs);
        ctx.json("{\"ok\":true}");
    }

    // ── Blockieren ────────────────────────────────────────────────────────────

    public static void handleBlock(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).json(err("Ungültiger Body")); return; }
        String number = str(body, "number");
        if (number == null) { ctx.status(400).json(err("number erforderlich")); return; }
        String guildId = guildId();
        JsonArray blocked = loadBlocked(guildId, c.phoneNumber);
        boolean exists = false;
        for (JsonElement el : blocked) if (number.equals(el.getAsString())) { exists = true; break; }
        if (!exists) blocked.add(number);
        DataStore.writeString(blockKey(guildId, c.phoneNumber), GSON.toJson(blocked));
        ctx.json("{\"ok\":true}");
    }

    public static void handleUnblock(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String number  = ctx.pathParam("number");
        String guildId = guildId();
        JsonArray blocked = loadBlocked(guildId, c.phoneNumber);
        JsonArray updated = new JsonArray();
        for (JsonElement el : blocked) if (!number.equals(el.getAsString())) updated.add(el);
        DataStore.writeString(blockKey(guildId, c.phoneNumber), GSON.toJson(updated));
        ctx.json("{\"ok\":true}");
    }

    public static void handleGetBlocked(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String raw = DataStore.readString(blockKey(guildId(), c.phoneNumber));
        ctx.json(raw != null ? raw : "[]");
    }

    // ── Hilfsmethoden ─────────────────────────────────────────────────────────

    /** Liest Session-Token aus Authorization-Header oder Query-Param. */
    private static PhoneManager.Contract auth(Context ctx) {
        String token = ctx.queryParam("token");
        if (token == null) {
            String header = ctx.header("Authorization");
            if (header != null && header.startsWith("Bearer ")) token = header.substring(7);
        }
        PhoneManager.Contract c = PhoneManager.validateSession(token);
        if (c == null) { ctx.status(401).json(err("Nicht authentifiziert")); return null; }
        return c;
    }

    private static String guildId() {
        var guild = de.pcrp.bot.common.BotContext.getGuild();
        return guild != null ? guild.getId() : "default";
    }

    private static String chatId(String a, String b) {
        String[] sorted = {a, b};
        Arrays.sort(sorted);
        return (sorted[0] + "|" + sorted[1]).replace(" ", "_").replace("(", "").replace(")", "");
    }

    private static JsonObject parseBody(Context ctx) {
        try { return JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { return null; }
    }

    private static String str(JsonObject o, String key) {
        return o.has(key) && !o.get(key).isJsonNull() ? o.get(key).getAsString() : null;
    }

    private static String err(String msg) {
        return "{\"error\":\"" + msg + "\"}";
    }

    private static String contactKey(String guildId, String phone) {
        return "city-contacts-" + guildId + "-" + phone.replaceAll("[^0-9]", "");
    }

    private static String blockKey(String guildId, String phone) {
        return "city-blocked-" + guildId + "-" + phone.replaceAll("[^0-9]", "");
    }

    private static String msgKey(String guildId, String chatId) {
        return "city-msgs-" + guildId + "-" + chatId;
    }

    private static JsonArray loadMessages(String guildId, String chatId) {
        String raw = DataStore.readString(msgKey(guildId, chatId));
        if (raw == null) return new JsonArray();
        try { return JsonParser.parseString(raw).getAsJsonArray(); } catch (Exception e) { return new JsonArray(); }
    }

    private static void saveMessages(String guildId, String chatId, JsonArray msgs) {
        DataStore.writeString(msgKey(guildId, chatId), GSON.toJson(msgs));
    }

    private static JsonArray loadContacts(String guildId, String phone) {
        String raw = DataStore.readString(contactKey(guildId, phone));
        if (raw == null) return new JsonArray();
        try { return JsonParser.parseString(raw).getAsJsonArray(); } catch (Exception e) { return new JsonArray(); }
    }

    private static void saveContacts(String guildId, String phone, JsonArray contacts) {
        DataStore.writeString(contactKey(guildId, phone), GSON.toJson(contacts));
    }

    private static JsonArray loadBlocked(String guildId, String phone) {
        String raw = DataStore.readString(blockKey(guildId, phone));
        if (raw == null) return new JsonArray();
        try { return JsonParser.parseString(raw).getAsJsonArray(); } catch (Exception e) { return new JsonArray(); }
    }

    private static JsonObject loadProfile(String guildId, String phone) {
        String raw = DataStore.readString("city-profile-" + guildId + "-" + phone.replaceAll("[^0-9]", ""));
        if (raw == null) return new JsonObject();
        try { return JsonParser.parseString(raw).getAsJsonObject(); } catch (Exception e) { return new JsonObject(); }
    }

    private static void saveProfile(String guildId, String phone, JsonObject profile) {
        DataStore.writeString("city-profile-" + guildId + "-" + phone.replaceAll("[^0-9]", ""), GSON.toJson(profile));
    }

    private static String profileStr(JsonObject p, String key, String def) {
        return p.has(key) && !p.get(key).isJsonNull() ? p.get(key).getAsString() : def;
    }

    private static JsonArray removeWhere(JsonArray arr, String key, String value) {
        JsonArray result = new JsonArray();
        for (JsonElement el : arr) {
            JsonObject o = el.getAsJsonObject();
            if (!value.equals(o.has(key) ? o.get(key).getAsString() : null)) result.add(o);
        }
        return result;
    }
}
