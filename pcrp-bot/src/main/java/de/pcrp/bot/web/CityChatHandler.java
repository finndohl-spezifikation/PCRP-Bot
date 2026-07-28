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
 *   POST /api/city-chat/auth                 → Login mit Rufnummer
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
        if (phone == null || pin == null) { ctx.status(400).json(err("Rufnummer erforderlich")); return; }

        String guildId = guildId();
        PhoneManager.Contract c = PhoneManager.getContractByNumber(guildId, phone);
        if (c == null || !c.safePin.equals(pin)) {
            ctx.status(401).json(err("Ungültige Zugangsdaten"));
            return;
        }

        // Web-Ban prüfen
        String webBan = DataStore.readString("web-ban-" + guildId + "-" + c.userId);
        if (webBan != null && !webBan.isBlank()) {
            ctx.status(403).json("{\"error\":\"WEB_BANNED\",\"banned\":true}");
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
        res.addProperty("avatar",      profileStr(profile, "avatar", ""));
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
        if (body.has("avatar"))      profile.addProperty("avatar",      str(body, "avatar"));
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

        // Existiert die Nummer? (exakt oder normalisiert)
        PhoneManager.Contract found = PhoneManager.getContractByNumber(guildId, number);
        if (found == null) {
            String normalized = number.replaceAll("[^0-9]", "");
            for (PhoneManager.Contract other : PhoneManager.getAllContracts(guildId)) {
                if (other.phoneNumber.replaceAll("[^0-9]", "").equals(normalized)) {
                    found = other; break;
                }
            }
        }
        if (found == null) { ctx.status(404).json(err("Rufnummer nicht gefunden")); return; }
        // Immer das gespeicherte Format verwenden
        number = found.phoneNumber;

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
            JsonObject partnerProfile = loadProfile(guildId, other.phoneNumber);
            chat.addProperty("chatId",      chatId);
            chat.addProperty("phoneNumber", other.phoneNumber);
            chat.addProperty("displayName", displayName);
            chat.addProperty("lastMessage", last.get("content").getAsString());
            chat.addProperty("lastType",    last.get("type").getAsString());
            chat.addProperty("lastTs",      last.get("ts").getAsLong());
            chat.addProperty("unread",      unread);
            chat.addProperty("avatar",      profileStr(partnerProfile, "avatar", ""));
            result.add(chat);
        }

        // Nach lastTs sortieren (neueste zuerst)
        List<JsonObject> chatList = new ArrayList<>();
        for (JsonElement el : result) chatList.add(el.getAsJsonObject());
        chatList.sort((a, b) -> Long.compare(
            b.get("lastTs").getAsLong(), a.get("lastTs").getAsLong()));

        JsonArray sorted = new JsonArray();
        for (JsonObject o : chatList) sorted.add(o);
        ctx.json(GSON.toJson(sorted));
    }

    // ── Nachrichten ───────────────────────────────────────────────────────────

    public static void handleGetMessages(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String chatId  = ctx.pathParam("chatId");
        String guildId = guildId();

        JsonArray msgs = loadMessages(guildId, chatId);

        // Partner-Rufnummer aus chatId extrahieren (Format: phone1|phone2)
        String[] chatParts = chatId.split("\\|");
        long partnerReadTs = 0;
        if (chatParts.length == 2) {
            String partnerPhone = chatParts[0].equals(c.phoneNumber) ? chatParts[1] : chatParts[0];
            String partnerRead  = DataStore.readString("city-read-" + guildId + "-" + partnerPhone + "-" + chatId);
            if (partnerRead != null) {
                try { partnerReadTs = Long.parseLong(partnerRead); } catch (Exception ignored) {}
            }
        }

        // read-Flag pro Nachricht hinzufügen
        JsonArray result = new JsonArray();
        for (JsonElement el : msgs) {
            JsonObject m = el.getAsJsonObject().deepCopy();
            if (m.has("from") && m.get("from").getAsString().equals(c.phoneNumber)) {
                long ts = m.has("ts") ? m.get("ts").getAsLong() : 0;
                m.addProperty("read", partnerReadTs > 0 && partnerReadTs >= ts);
            }
            result.add(m);
        }

        ctx.json(GSON.toJson(result));

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
        msg.addProperty("type",    type);   // text | emoji
        msg.addProperty("ts",      System.currentTimeMillis());
        msgs.add(msg);

        // Max 200 Nachrichten pro Chat
        while (msgs.size() > 200) msgs.remove(0);

        saveMessages(guildId, chatId, msgs);
        ctx.json("{\"ok\":true}");

        // Push-Benachrichtigung an Empfänger (im Hintergrund)
        final String senderName;
        JsonObject recipientProfile = loadProfile(guildId, to);
        // Empfänger-Name für die Notification: Sender-Name aus Empfänger-Kontaktbuch oder displayName
        String contactKey = contactKey(guildId, to);
        String contactsRaw = DataStore.readString(contactKey);
        String senderDisplayName = c.displayName();
        if (contactsRaw != null) {
            try {
                for (JsonElement el : JsonParser.parseString(contactsRaw).getAsJsonArray()) {
                    JsonObject co = el.getAsJsonObject();
                    if (c.phoneNumber.equals(str(co, "number"))) {
                        senderDisplayName = str(co, "name");
                        break;
                    }
                }
            } catch (Exception ignored) {}
        }
        senderName = senderDisplayName;
        final String finalContent = "voice".equals(type) ? "🎤 Sprachnachricht" : content;
        final String finalGuildId = guildId;
        final String finalTo = to;
        String railwayUrl = System.getenv().getOrDefault("RAILWAY_PUBLIC_DOMAIN", "pcrp-bot-production-3ad1.up.railway.app");
        if (!railwayUrl.startsWith("http")) railwayUrl = "https://" + railwayUrl;
        final String chatUrl = railwayUrl.replaceAll("/$", "") + "/city-chat";
        new Thread(() -> PushService.push(finalGuildId, finalTo, senderName, finalContent, chatUrl), "push-send").start();
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
        // Ban-Check bei jedem Request → sofortige Wirkung (nur wenn userId bekannt)
        if (c.userId != null) {
            String webBan = DataStore.readString("web-ban-" + guildId() + "-" + c.userId);
            if (webBan != null && !webBan.isBlank()) {
                ctx.status(403).json("{\"error\":\"WEB_BANNED\",\"banned\":true}");
                return null;
            }
        }
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

    /** DELETE /api/city-chat/messages/{chatId}  – eigenen Chat-Verlauf löschen */
    public static void handleClearChat(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String chatId  = ctx.pathParam("chatId");
        String guildId = guildId();
        // Sicherheitscheck: Nutzer muss Teil des Chats sein
        // chatId() normalisiert: Leerzeichen→_, Klammern entfernt
        String normPhone = c.phoneNumber.replace(" ", "_").replace("(", "").replace(")", "");
        boolean isMember = false;
        for (String part : chatId.split("\\|")) { if (part.equals(normPhone)) { isMember = true; break; } }
        if (!isMember) { ctx.status(403).json(err("Kein Zugriff auf diesen Chat")); return; }
        DataStore.writeString(msgKey(guildId, chatId), "[]");
        ctx.json("{\"ok\":true}");
    }

    private static JsonArray loadContacts(String guildId, String phone) {
        String raw = DataStore.readString(contactKey(guildId, phone));
        if (raw == null) return new JsonArray();
        try { return JsonParser.parseString(raw).getAsJsonArray(); } catch (Exception e) { return new JsonArray(); }
    }

    // ── Status (WhatsApp-Style) ───────────────────────────────────────────────

    public static void handleGetStatuses(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String guildId = guildId();
        JsonArray result = new JsonArray();
        long now   = System.currentTimeMillis();
        long limit = 24L * 3600 * 1000;

        // Nur eigene Kontakte und sich selbst anzeigen
        JsonArray myContacts = loadContacts(guildId, c.phoneNumber);
        Set<String> visibleNumbers = new HashSet<>();
        visibleNumbers.add(c.phoneNumber);
        for (JsonElement el : myContacts) {
            visibleNumbers.add(el.getAsJsonObject().get("number").getAsString());
        }

        for (PhoneManager.Contract other : PhoneManager.getAllContracts(guildId)) {
            if (!visibleNumbers.contains(other.phoneNumber)) continue;
            String raw = DataStore.readString("city-status-" + guildId + "-" + other.phoneNumber);
            if (raw == null) continue;
            try {
                JsonObject s = JsonParser.parseString(raw).getAsJsonObject();
                if (now - s.get("ts").getAsLong() > limit) continue;
                s.addProperty("phoneNumber", other.phoneNumber);
                // Anzeigename aus Kontakten
                String displayName = other.phoneNumber;
                for (JsonElement el : myContacts) {
                    if (other.phoneNumber.equals(el.getAsJsonObject().get("number").getAsString())) {
                        displayName = el.getAsJsonObject().get("name").getAsString(); break;
                    }
                }
                // Eigener Anzeigename
                if (other.phoneNumber.equals(c.phoneNumber)) displayName = c.displayName();
                // Avatar aus Profil
                JsonObject profile = loadProfile(guildId, other.phoneNumber);
                s.addProperty("displayName", displayName);
                s.addProperty("avatar",      profileStr(profile, "avatar", ""));
                result.add(s);
            } catch (Exception ignored) {}
        }
        ctx.json(GSON.toJson(result));
    }

    public static void handleSetStatus(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).json(err("Ungültiger Body")); return; }
        JsonObject s = new JsonObject();
        if (body.has("text"))  s.addProperty("text",  str(body, "text"));
        if (body.has("emoji")) s.addProperty("emoji", str(body, "emoji"));
        if (body.has("color")) s.addProperty("color", str(body, "color"));
        s.addProperty("ts", System.currentTimeMillis());
        DataStore.writeString("city-status-" + guildId() + "-" + c.phoneNumber, GSON.toJson(s));
        ctx.json("{\"ok\":true}");
    }

    public static void handleDeleteStatus(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        DataStore.deleteKey("city-status-" + guildId() + "-" + c.phoneNumber);
        ctx.json("{\"ok\":true}");
    }

    // ── Firma-Links ───────────────────────────────────────────────────────────

    /** Öffentliches Profil eines anderen Nutzers: displayName, avatar, bio, firmaLinks. */
    public static void handleGetPartnerProfile(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String phone = ctx.queryParam("phone");
        if (phone == null || phone.isBlank()) { ctx.status(400).json(err("phone fehlt")); return; }
        String guildId  = guildId();
        String normPhone = phone.replaceAll("[^0-9]", "");
        JsonObject profile = loadProfile(guildId, normPhone);

        // displayName: aus Profil oder Vertrag
        PhoneManager.Contract found = PhoneManager.getContractByNumber(guildId, phone);
        if (found == null) {
            for (PhoneManager.Contract other : PhoneManager.getAllContracts(guildId)) {
                if (other.phoneNumber.replaceAll("[^0-9]", "").equals(normPhone)) { found = other; break; }
            }
        }
        String displayName = profileStr(profile, "displayName", found != null ? found.displayName() : phone);

        JsonObject res = new JsonObject();
        res.addProperty("phoneNumber", phone);
        res.addProperty("displayName", displayName);
        res.addProperty("bio",    profileStr(profile, "status", ""));
        res.addProperty("avatar", profileStr(profile, "avatar", ""));

        // nur genehmigte Firma-Links
        JsonArray allLinks = loadFirmaLinks(guildId, normPhone);
        JsonArray approved = new JsonArray();
        for (JsonElement el : allLinks) {
            JsonObject o = el.getAsJsonObject();
            if ("approved".equals(str(o, "status"))) approved.add(o);
        }
        res.add("firmaLinks", approved);
        ctx.json(res.toString());
    }

    /** Gibt eigene Links zurück (alle Status). Mit ?phone=X nur genehmigte eines anderen. */
    // ── Push-Subscriptions ────────────────────────────────────────────────────

    public static void handlePushSubscribe(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).json(err("Ungültiger Body")); return; }
        String endpoint = str(body, "endpoint");
        String p256dh   = str(body, "p256dh");
        String auth     = str(body, "auth");
        if (endpoint == null || p256dh == null || auth == null) {
            ctx.status(400).json(err("endpoint, p256dh und auth erforderlich")); return;
        }
        PushService.subscribe(guildId(), c.phoneNumber, endpoint, p256dh, auth);
        ctx.json("{\"ok\":true}");
    }

    public static void handlePushUnsubscribe(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).json(err("Ungültiger Body")); return; }
        String endpoint = str(body, "endpoint");
        if (endpoint != null) PushService.unsubscribe(guildId(), c.phoneNumber, endpoint);
        ctx.json("{\"ok\":true}");
    }

    public static void handleGetFirmaLinks(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String phone   = ctx.queryParam("phone");
        String guildId = guildId();
        if (phone != null && !phone.isBlank()) {
            JsonArray all = loadFirmaLinks(guildId, phone.replaceAll("[^0-9]", ""));
            JsonArray approved = new JsonArray();
            for (JsonElement el : all) {
                JsonObject o = el.getAsJsonObject();
                if ("approved".equals(str(o, "status"))) approved.add(o);
            }
            ctx.json(approved.toString());
        } else {
            ctx.json(loadFirmaLinks(guildId, c.phoneNumber).toString());
        }
    }

    /** Sendet eine neue Link-Anfrage → DM an Admin. */
    public static void handleAddFirmaLink(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).json(err("Ungültiger Body")); return; }
        String url   = str(body, "url");
        String label = str(body, "label");
        if (url == null || url.isBlank() || label == null || label.isBlank()) {
            ctx.status(400).json(err("url und label erforderlich")); return;
        }
        if (!url.startsWith("https://discord.gg/") && !url.startsWith("http://discord.gg/")) {
            ctx.status(400).json(err("Nur discord.gg-Links erlaubt")); return;
        }
        String guildId = guildId();
        JsonArray links = loadFirmaLinks(guildId, c.phoneNumber);
        if (links.size() >= 5) { ctx.status(400).json(err("Maximal 5 Links erlaubt")); return; }

        String id = UUID.randomUUID().toString().replace("-", "").substring(0, 8);
        JsonObject link = new JsonObject();
        link.addProperty("id",    id);
        link.addProperty("label", label.length() > 32 ? label.substring(0, 32) : label);
        link.addProperty("url",   url);
        link.addProperty("status", "pending");
        link.addProperty("ts",    System.currentTimeMillis());
        links.add(link);
        saveFirmaLinks(guildId, c.phoneNumber, links);

        sendFirmaLinkDm(guildId, c.phoneNumber, c.displayName(), id, label, url);
        ctx.json("{\"ok\":true,\"id\":\"" + id + "\"}");
    }

    /** Löscht einen eigenen Link. */
    public static void handleDeleteFirmaLink(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String id      = ctx.pathParam("id");
        String guildId = guildId();
        saveFirmaLinks(guildId, c.phoneNumber, removeWhere(loadFirmaLinks(guildId, c.phoneNumber), "id", id));
        ctx.json("{\"ok\":true}");
    }

    /** Wird vom FirmaLinkListener aufgerufen. */
    public static void approveFirmaLink(String guildId, String phone, String id) {
        JsonArray links = loadFirmaLinks(guildId, phone);
        for (JsonElement el : links) {
            JsonObject o = el.getAsJsonObject();
            if (id.equals(str(o, "id"))) { o.addProperty("status", "approved"); break; }
        }
        saveFirmaLinks(guildId, phone, links);
    }

    public static void rejectFirmaLink(String guildId, String phone, String id) {
        saveFirmaLinks(guildId, phone, removeWhere(loadFirmaLinks(guildId, phone), "id", id));
    }

    private static JsonArray loadFirmaLinks(String guildId, String phone) {
        String raw = DataStore.readString("city-firma-" + guildId + "-" + phone.replaceAll("[^0-9]", ""));
        if (raw == null) return new JsonArray();
        try { return JsonParser.parseString(raw).getAsJsonArray(); } catch (Exception e) { return new JsonArray(); }
    }

    private static void saveFirmaLinks(String guildId, String phone, JsonArray arr) {
        DataStore.writeString("city-firma-" + guildId + "-" + phone.replaceAll("[^0-9]", ""), GSON.toJson(arr));
    }

    private static void sendFirmaLinkDm(String guildId, String phone, String displayName, String id, String label, String url) {
        net.dv8tion.jda.api.JDA jda = de.pcrp.bot.common.BotContext.getJda();
        if (jda == null) return;
        jda.retrieveUserById(ModerationConfig.OWNER_ID).queue(admin -> {
            net.dv8tion.jda.api.EmbedBuilder eb = de.pcrp.bot.common.EmbedFactory.create()
                .setTitle("🔗 Neue Firma-Link-Anfrage")
                .setDescription(
                    "**Spieler:** " + displayName + " (`" + phone + "`)\n" +
                    "**Button-Text:** " + label + "\n" +
                    "**Link:** " + url)
                .setFooter("GuildID: " + guildId + " | Phone: " + phone + " | ID: " + id);
            net.dv8tion.jda.api.interactions.components.buttons.Button approve =
                net.dv8tion.jda.api.interactions.components.buttons.Button.success(
                    "cfl-a:" + guildId + ":" + phone + ":" + id, "✅ Genehmigen");
            net.dv8tion.jda.api.interactions.components.buttons.Button reject =
                net.dv8tion.jda.api.interactions.components.buttons.Button.danger(
                    "cfl-r:" + guildId + ":" + phone + ":" + id, "❌ Ablehnen");
            admin.openPrivateChannel().queue(ch ->
                ch.sendMessageEmbeds(eb.build())
                  .addActionRow(approve, reject)
                  .queue(null, err -> {}),
                err -> {});
        }, err -> {});
    }

    // ── Lookup ────────────────────────────────────────────────────────────────

    public static void handleLookup(Context ctx) {
        PhoneManager.Contract c = auth(ctx);
        if (c == null) return;
        String number = ctx.queryParam("number");
        if (number == null || number.isBlank()) { ctx.status(400).json(err("Nummer fehlt")); return; }
        String guildId = guildId();
        // Exakter Treffer zuerst
        PhoneManager.Contract found = PhoneManager.getContractByNumber(guildId, number);
        // Fallback: normalisiert vergleichen (nur Ziffern)
        if (found == null) {
            String normalized = number.replaceAll("[^0-9]", "");
            for (PhoneManager.Contract other : PhoneManager.getAllContracts(guildId)) {
                if (other.phoneNumber.replaceAll("[^0-9]", "").equals(normalized)) {
                    found = other; break;
                }
            }
        }
        if (found == null) { ctx.status(404).json(err("Nummer nicht gefunden")); return; }
        JsonObject res = new JsonObject();
        res.addProperty("phoneNumber", found.phoneNumber);
        ctx.json(GSON.toJson(res));
    }

    private static void saveContacts(String guildId, String phone, JsonArray contacts) {
        DataStore.writeString(contactKey(guildId, phone), GSON.toJson(contacts));
    }

    private static JsonArray loadBlocked(String guildId, String phone) {
        String raw = DataStore.readString(blockKey(guildId, phone));
        if (raw == null) return new JsonArray();
        try { return JsonParser.parseString(raw).getAsJsonArray(); } catch (Exception e) { return new JsonArray(); }
    }

    // ── WebRTC Call Signaling ─────────────────────────────────────────────────

    /** POST /api/city-chat/call-signal  – Signal an einen anderen Nutzer senden */
    public static void handleSendCallSignal(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = JsonParser.parseString(ctx.body()).getAsJsonObject();
        String to       = str(body, "to");
        String type     = str(body, "type");   // offer|answer|ice|end|reject
        String data     = body.has("data")     ? body.get("data").getAsString()     : "";
        String callType = body.has("callType") ? body.get("callType").getAsString() : "";
        if (to == null || to.isBlank()) { ctx.status(400).json("{\"error\":\"missing to\"}"); return; }
        String guildId = guildId();

        String key = "city-call-sig-" + guildId + "-" + to.replaceAll("[^0-9]", "");
        String raw = DataStore.readString(key);
        JsonArray arr = (raw != null && !raw.isBlank())
            ? JsonParser.parseString(raw).getAsJsonArray() : new JsonArray();

        JsonObject sig = new JsonObject();
        sig.addProperty("from",     c.phoneNumber);
        sig.addProperty("type",     type);
        sig.addProperty("data",     data);
        if (!callType.isEmpty()) sig.addProperty("callType", callType);
        sig.addProperty("ts",       System.currentTimeMillis());
        arr.add(sig);
        DataStore.writeString(key, GSON.toJson(arr));
        ctx.status(204);
    }

    /** GET /api/city-chat/call-signal  – Eigene Signale abrufen und löschen */
    public static void handleGetCallSignal(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String guildId = guildId();
        String key = "city-call-sig-" + guildId + "-" + c.phoneNumber.replaceAll("[^0-9]", "");
        String raw = DataStore.readString(key);
        if (raw == null || raw.isBlank()) { ctx.json("[]"); return; }
        DataStore.deleteKey(key);
        ctx.contentType("application/json").result(raw);
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
