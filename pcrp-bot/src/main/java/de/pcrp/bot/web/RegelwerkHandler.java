package de.pcrp.bot.web;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import de.pcrp.bot.common.DataStore;
import io.javalin.http.Context;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Backend für die externe Regelwerk-Seite (/regelwerk).
 *
 * Persistenz: eine JSON-Datei "regelwerk.json" im DataStore.
 * Struktur: { "categories": [ { "id": "...", "title": "...", "texts": ["...", ...] } ] }
 */
public final class RegelwerkHandler {

    private static final Logger log = LoggerFactory.getLogger(RegelwerkHandler.class);
    private static final String FILE = "regelwerk.json";

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
        JsonArray cats = data.getAsJsonArray("categories");
        JsonObject cat = new JsonObject();
        cat.addProperty("id", newId());
        cat.addProperty("title", title);
        cat.add("texts", new JsonArray());
        cats.add(cat);
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
            JsonArray cats = data.getAsJsonArray("categories");
            JsonArray keep = new JsonArray();
            for (JsonElement el : cats) {
                if (!el.getAsJsonObject().get("id").getAsString().equals(categoryId)) keep.add(el);
            }
            data.add("categories", keep);
        }
        save(data);

        respondOk(ctx, data);
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
