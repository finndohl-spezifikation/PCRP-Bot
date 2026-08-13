package de.pcrp.bot.web;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import de.pcrp.bot.common.DataStore;
import io.javalin.http.Context;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Backend für die externe Regelwerk-Seite (/regelwerk).
 *
 * Persistenz: eine JSON-Datei "regelwerk.json" im DataStore.
 * Struktur: { "categories": [ { "id": "...", "title": "...", "texts": ["...", ...] } ] }
 */
public final class RegelwerkHandler {

    private static final Logger log = LoggerFactory.getLogger(RegelwerkHandler.class);
    private static final String FILE = "regelwerk.json";

    /** LanguageTool (kostenlos, ohne Key) für die Rechtschreib-Korrektur. */
    private static final String LANGTOOL_URL = "https://api.languagetool.org/v2/check";
    private static final HttpClient HTTP = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10)).build();

    private RegelwerkHandler() {}

    /** Lädt die Regelwerk-Daten (erzeugt bei Bedarf eine leere Struktur). */
    private static synchronized JsonObject load() {
        String raw = DataStore.readString(FILE);
        if (raw == null || raw.isBlank()) {
            JsonObject fresh = new JsonObject();
            fresh.add("categories", new JsonArray());
            return fresh;
        }
        try {
            JsonObject o = JsonParser.parseString(raw).getAsJsonObject();
            if (!o.has("categories") || !o.get("categories").isJsonArray()) {
                o.add("categories", new JsonArray());
            }
            return o;
        } catch (Exception e) {
            log.warn("[Regelwerk] Daten beschädigt, starte leer.", e);
            JsonObject fresh = new JsonObject();
            fresh.add("categories", new JsonArray());
            return fresh;
        }
    }

    private static void save(JsonObject data) {
        DataStore.writeString(FILE, data.toString());
    }

    private static String newId() {
        return "c-" + Long.toHexString(System.nanoTime());
    }

    /** GET /api/regelwerk */
    public static void handleGet(Context ctx) {
        JsonObject out = new JsonObject();
        out.addProperty("ok", true);
        out.add("categories", load().getAsJsonArray("categories"));
        ctx.contentType("application/json").result(out.toString());
    }

    /** POST /api/regelwerk/category  body: { "title": "..." } */
    public static void handleAddCategory(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String title = body.has("title") ? body.get("title").getAsString().trim() : "";
        if (title.isEmpty()) { respondError(ctx, "Titel darf nicht leer sein."); return; }

        JsonObject data = load();
        JsonObject cat = new JsonObject();
        cat.addProperty("id", newId());
        cat.addProperty("title", title);
        cat.add("texts", new JsonArray());
        data.getAsJsonArray("categories").add(cat);
        save(data);

        respondOk(ctx, data);
    }

    /** POST /api/regelwerk/category/edit  body: { "categoryId": "...", "title": "..." } */
    public static void handleEditCategory(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        String title = body.has("title") ? body.get("title").getAsString().trim() : "";
        if (categoryId.isEmpty() || title.isEmpty()) { respondError(ctx, "Kategorie und Titel sind erforderlich."); return; }

        JsonObject data = load();
        JsonObject cat = findCategory(data, categoryId);
        if (cat == null) { respondError(ctx, "Kategorie nicht gefunden."); return; }
        cat.addProperty("title", title);
        save(data);

        respondOk(ctx, data);
    }

    /** POST /api/regelwerk/entry  body: { "categoryId": "...", "text": "..." } */
    public static void handleAddEntry(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        String text = body.has("text") ? body.get("text").getAsString().trim() : "";
        if (categoryId.isEmpty() || text.isEmpty()) {
            respondError(ctx, "Kategorie und Text sind erforderlich.");
            return;
        }

        JsonObject data = load();
        JsonObject cat = findCategory(data, categoryId);
        if (cat == null) { respondError(ctx, "Kategorie nicht gefunden."); return; }
        cat.getAsJsonArray("texts").add(text);
        save(data);

        respondOk(ctx, data);
    }

    /** POST /api/regelwerk/entry/edit  body: { "categoryId": "...", "index": 0, "text": "..." } */
    public static void handleEditEntry(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        String text = body.has("text") ? body.get("text").getAsString().trim() : "";
        if (categoryId.isEmpty()) { respondError(ctx, "Kategorie fehlt."); return; }

        JsonObject data = load();
        JsonObject cat = findCategory(data, categoryId);
        if (cat == null) { respondError(ctx, "Kategorie nicht gefunden."); return; }

        JsonArray texts = cat.getAsJsonArray("texts");
        if (!body.has("index")) { respondError(ctx, "Index fehlt."); return; }
        int idx = body.get("index").getAsInt();
        if (idx < 0 || idx >= texts.size()) { respondError(ctx, "Ungültiger Index."); return; }
        if (text.isEmpty()) { respondError(ctx, "Text darf nicht leer sein."); return; }
        texts.set(idx, new com.google.gson.JsonPrimitive(text));
        save(data);

        respondOk(ctx, data);
    }

    /** POST /api/regelwerk/category/texts  body: { "categoryId": "...", "texts": ["..."] } — ersetzt alle Texte. */
    public static void handleSetTexts(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        if (categoryId.isEmpty() || !body.has("texts") || !body.get("texts").isJsonArray()) {
            respondError(ctx, "Kategorie und Texte sind erforderlich.");
            return;
        }

        JsonObject data = load();
        JsonObject cat = findCategory(data, categoryId);
        if (cat == null) { respondError(ctx, "Kategorie nicht gefunden."); return; }

        JsonArray texts = new JsonArray();
        for (JsonElement el : body.getAsJsonArray("texts")) {
            String t = el.getAsString().trim();
            if (!t.isEmpty()) texts.add(t);
        }
        cat.add("texts", texts);
        save(data);

        respondOk(ctx, data);
    }

    /**
     * POST /api/regelwerk/korrektur  body: { "texts": ["..."] } → { "ok":true, "texts":["..."] }
     * Korrigiert Rechtschreibung über LanguageTool (de-DE).
     */
    public static void handleKorrektur(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        if (!body.has("texts") || !body.get("texts").isJsonArray()) {
            respondError(ctx, "texts erforderlich.");
            return;
        }

        JsonArray in = body.getAsJsonArray("texts");
        JsonArray out = new JsonArray();
        for (JsonElement el : in) {
            String t = el.getAsString();
            out.add(correct(t));
        }

        JsonObject res = new JsonObject();
        res.addProperty("ok", true);
        res.add("texts", out);
        ctx.contentType("application/json").result(res.toString());
    }

    /**
     * POST /api/regelwerk/delete
     * body: { "categoryId": "..." }                     → ganze Kategorie löschen
     *       { "categoryId": "...", "index": 0 }         → einzelnen Text löschen
     */
    public static void handleDelete(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        if (categoryId.isEmpty()) { respondError(ctx, "Kategorie fehlt."); return; }

        JsonObject data = load();
        JsonObject cat = findCategory(data, categoryId);
        if (cat == null) { respondError(ctx, "Kategorie nicht gefunden."); return; }

        if (body.has("index")) {
            int idx = body.get("index").getAsInt();
            JsonArray texts = cat.getAsJsonArray("texts");
            if (idx < 0 || idx >= texts.size()) { respondError(ctx, "Ungültiger Index."); return; }
            texts.remove(idx);
        } else {
            JsonArray keep = new JsonArray();
            for (JsonElement el : data.getAsJsonArray("categories")) {
                if (!el.getAsJsonObject().get("id").getAsString().equals(categoryId)) keep.add(el);
            }
            data.add("categories", keep);
        }
        save(data);

        respondOk(ctx, data);
    }

    /** Korrigiert einen Text über LanguageTool. Fallback: Originaltext bei Fehler. */
    private static String correct(String text) {
        if (text == null || text.isBlank()) return text;
        try {
            String form = "language=de-DE&text=" + URLEncoder.encode(text, StandardCharsets.UTF_8);
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(LANGTOOL_URL))
                    .timeout(Duration.ofSeconds(15))
                    .header("Content-Type", "application/x-www-form-urlencoded")
                    .header("User-Agent", "PCRP-Bot-Regelwerk/1.0")
                    .POST(HttpRequest.BodyPublishers.ofString(form))
                    .build();
            HttpResponse<String> resp = HTTP.send(req, HttpResponse.BodyHandlers.ofString());
            if (resp.statusCode() != 200) return text;

            JsonObject json = JsonParser.parseString(resp.body()).getAsJsonObject();
            if (!json.has("matches")) return text;

            List<int[]> repl = new ArrayList<>(); // {offset, length, replacementOffset}
            List<String> values = new ArrayList<>();
            for (JsonElement m : json.getAsJsonArray("matches")) {
                JsonObject mo = m.getAsJsonObject();
                if (!mo.has("offset") || !mo.has("length")) continue;
                if (!mo.has("replacements") || !mo.get("replacements").isJsonArray()) continue;
                JsonArray reps = mo.getAsJsonArray("replacements");
                if (reps.size() == 0) continue;
                String value = reps.get(0).getAsJsonObject().get("value").getAsString();
                int off = mo.get("offset").getAsInt();
                int len = mo.get("length").getAsInt();
                repl.add(new int[]{off, len});
                values.add(value);
            }

            if (repl.isEmpty()) return text;

            // Nach Offset absteigend anwenden, damit frühere Offsets gültig bleiben
            List<Integer> order = new ArrayList<>();
            for (int i = 0; i < repl.size(); i++) order.add(i);
            order.sort(Comparator.comparingInt((Integer i) -> repl.get(i)[0]).reversed());

            StringBuilder sb = new StringBuilder(text);
            for (int idx : order) {
                int off = repl.get(idx)[0];
                int len = repl.get(idx)[1];
                if (off < 0 || off + len > sb.length()) continue;
                sb.replace(off, off + len, values.get(idx));
            }
            return sb.toString();
        } catch (Exception e) {
            log.warn("[Regelwerk] Rechtschreib-Korrektur fehlgeschlagen: {}", e.getMessage());
            return text;
        }
    }

    private static JsonObject findCategory(JsonObject data, String categoryId) {
        for (JsonElement el : data.getAsJsonArray("categories")) {
            JsonObject c = el.getAsJsonObject();
            if (c.get("id").getAsString().equals(categoryId)) return c;
        }
        return null;
    }

    private static void respondOk(Context ctx, JsonObject data) {
        JsonObject out = new JsonObject();
        out.addProperty("ok", true);
        out.add("categories", data.getAsJsonArray("categories"));
        ctx.contentType("application/json").result(out.toString());
    }

    private static void respondError(Context ctx, String msg) {
        JsonObject out = new JsonObject();
        out.addProperty("ok", false);
        out.addProperty("error", msg);
        ctx.contentType("application/json").result(out.toString());
    }
}
