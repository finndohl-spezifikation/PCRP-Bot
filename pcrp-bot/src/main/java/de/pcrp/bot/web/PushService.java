package de.pcrp.bot.web;

import com.google.gson.*;
import de.pcrp.bot.common.DataStore;
import nl.martijndwars.webpush.Notification;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.security.Security;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Verwaltet Web-Push-Subscriptions und sendet Push-Nachrichten via VAPID.
 */
public final class PushService {

    private static final Logger log = LoggerFactory.getLogger(PushService.class);
    private static final Gson   GSON = new GsonBuilder().create();

    // VAPID-Schlüssel (P-256, base64url ohne Padding)
    static final String VAPID_PUBLIC  = "BApcDmdPsgHvUrlKGaeP0Gsfpe85LUXvaIJQ6bXD9JSXXM0scZb9HtGmH4coHgHtJygGKZ0BXlpJPKmXgveEMp8";
    private static final String VAPID_PRIVATE = "NUXXdnmuBI6MLfpmt4jmKgjN0QTw8OZTdqDx1Tuu--k";
    private static final String VAPID_SUBJECT = "mailto:admin@pcrp.de";

    private static final ExecutorService POOL = Executors.newCachedThreadPool(r -> {
        Thread t = new Thread(r, "push-worker");
        t.setDaemon(true);
        return t;
    });

    private static nl.martijndwars.webpush.PushService pushSvc;

    private PushService() {}

    public static void init() {
        try {
            if (Security.getProvider("BC") == null)
                Security.addProvider(new BouncyCastleProvider());
            pushSvc = new nl.martijndwars.webpush.PushService(VAPID_PUBLIC, VAPID_PRIVATE, VAPID_SUBJECT);
            log.info("[Push] Web-Push initialisiert.");
        } catch (Exception e) {
            log.warn("[Push] Initialisierung fehlgeschlagen: {}", e.getMessage());
        }
    }

    /** Speichert eine Push-Subscription für eine Rufnummer. */
    public static void subscribe(String guildId, String phone, String endpoint, String p256dh, String auth) {
        String key = subKey(guildId, phone);
        JsonArray subs = load(key);
        // Duplikat nach Endpoint entfernen
        JsonArray filtered = new JsonArray();
        for (JsonElement el : subs) {
            JsonObject o = el.getAsJsonObject();
            if (!endpoint.equals(str(o, "endpoint"))) filtered.add(o);
        }
        JsonObject sub = new JsonObject();
        sub.addProperty("endpoint", endpoint);
        sub.addProperty("p256dh",   p256dh);
        sub.addProperty("auth",     auth);
        filtered.add(sub);
        DataStore.writeString(key, GSON.toJson(filtered));
    }

    /** Entfernt eine Subscription. */
    public static void unsubscribe(String guildId, String phone, String endpoint) {
        String key = subKey(guildId, phone);
        JsonArray subs = load(key);
        JsonArray filtered = new JsonArray();
        for (JsonElement el : subs)
            if (!endpoint.equals(str(el.getAsJsonObject(), "endpoint"))) filtered.add(el);
        DataStore.writeString(key, GSON.toJson(filtered));
    }

    /**
     * Sendet eine Push-Nachricht an alle Subscriptions einer Rufnummer.
     * Wird im Hintergrund ausgeführt.
     */
    public static void push(String guildId, String toPhone, String senderName, String message, String chatUrl) {
        if (pushSvc == null) return;
        JsonArray subs = load(subKey(guildId, toPhone));
        if (subs.size() == 0) return;

        JsonObject payload = new JsonObject();
        payload.addProperty("title", senderName);
        payload.addProperty("body",  message.length() > 120 ? message.substring(0, 117) + "…" : message);
        payload.addProperty("url",   chatUrl);
        payload.addProperty("from",  toPhone);
        byte[] payloadBytes;
        try { payloadBytes = payload.toString().getBytes("UTF-8"); } catch (Exception e) { return; }

        for (JsonElement el : subs) {
            JsonObject sub = el.getAsJsonObject();
            String ep    = str(sub, "endpoint");
            String p256  = str(sub, "p256dh");
            String authS = str(sub, "auth");
            if (ep == null || p256 == null || authS == null) continue;
            final byte[] pl = payloadBytes;
            POOL.submit(() -> {
                try {
                    Notification n = new Notification(ep, p256, authS, pl);
                    pushSvc.send(n);
                } catch (Exception e) {
                    log.debug("[Push] Send fehlgeschlagen für {}: {}", ep.substring(0, Math.min(40, ep.length())), e.getMessage());
                }
            });
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static String subKey(String g, String p) {
        return "city-push-" + g + "-" + p.replaceAll("[^0-9]", "");
    }

    private static JsonArray load(String key) {
        String raw = DataStore.readString(key);
        if (raw == null) return new JsonArray();
        try { return JsonParser.parseString(raw).getAsJsonArray(); } catch (Exception e) { return new JsonArray(); }
    }

    private static String str(JsonObject o, String k) {
        return (o.has(k) && !o.get(k).isJsonNull()) ? o.get(k).getAsString() : null;
    }
}
