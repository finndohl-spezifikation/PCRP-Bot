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
 * Struktur: { "sections": [ { "id": "...", "title": "...", "categories": [ ... ] } ] }
 * Kategorien: { "id": "...", "title": "§1.0 Allgemeine Regeln", "texts": ["...", ...] }
 */
public final class RegelwerkHandler {

    private static final Logger log = LoggerFactory.getLogger(RegelwerkHandler.class);
    private static final String FILE = "regelwerk.json";

    /** Feste Sektionen — oben als Buttons auf der Seite. */
    private static final String[][] SECTIONS = {
        {"allgemein", "Allgemeines Regelwerk"},
        {"team",      "Team Regeln"},
        {"faq",       "Server FAQ"}
    };

    private RegelwerkHandler() {}

    private static JsonArray defaultSections() {
        JsonArray arr = new JsonArray();
        for (String[] s : SECTIONS) {
            JsonObject sec = new JsonObject();
            sec.addProperty("id", s[0]);
            sec.addProperty("title", s[1]);
            sec.add("categories", new JsonArray());
            arr.add(sec);
        }
        return arr;
    }

    /** Lädt die Regelwerk-Daten (migriert bei Bedarf das alte flache Format). */
    private static synchronized JsonObject load() {
        String raw = DataStore.readString(FILE);
        if (raw == null || raw.isBlank()) {
            JsonObject fresh = new JsonObject();
            fresh.add("sections", defaultSections());
            return fresh;
        }
        try {
            JsonObject o = JsonParser.parseString(raw).getAsJsonObject();
            if (o.has("sections") && o.get("sections").isJsonArray()) {
                // Fehlende Sektionen nachrüsten
                for (String[] s : SECTIONS) {
                    if (findSection(o, s[0]) == null) {
                        JsonObject sec = new JsonObject();
                        sec.addProperty("id", s[0]);
                        sec.addProperty("title", s[1]);
                        sec.add("categories", new JsonArray());
                        o.getAsJsonArray("sections").add(sec);
                    }
                }
                return o;
            }
            // Altes flaches Format { categories: [...] } → in "allgemein" übernehmen
            JsonObject migrated = new JsonObject();
            JsonArray secs = defaultSections();
            if (o.has("categories") && o.get("categories").isJsonArray()) {
                secs.get(0).getAsJsonObject().add("categories", o.getAsJsonArray("categories"));
            }
            migrated.add("sections", secs);
            save(migrated);
            return migrated;
        } catch (Exception e) {
            log.warn("[Regelwerk] Daten beschädigt, starte leer.", e);
            JsonObject fresh = new JsonObject();
            fresh.add("sections", defaultSections());
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
        out.add("sections", load().getAsJsonArray("sections"));
        ctx.contentType("application/json").result(out.toString());
    }

    /** POST /api/regelwerk/category  body: { "sectionId": "...", "title": "..." } */
    public static void handleAddCategory(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String sectionId = body.has("sectionId") ? body.get("sectionId").getAsString() : "";
        String title = body.has("title") ? body.get("title").getAsString().trim() : "";
        if (sectionId.isEmpty() || title.isEmpty()) { respondError(ctx, "Sektion und Titel sind erforderlich."); return; }

        JsonObject data = load();
        JsonObject sec = findSection(data, sectionId);
        if (sec == null) { respondError(ctx, "Sektion nicht gefunden."); return; }

        JsonArray cats = sec.getAsJsonArray("categories");
        if (!title.startsWith("§")) {
            title = "§" + (cats.size() + 1) + ".0 " + title;
        }
        JsonObject cat = new JsonObject();
        cat.addProperty("id", newId());
        cat.addProperty("title", title);
        cat.add("texts", new JsonArray());
        cats.add(cat);
        save(data);

        respondOk(ctx, data);
    }

    /** POST /api/regelwerk/category/edit  body: { "sectionId", "categoryId", "title" } */
    public static void handleEditCategory(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String sectionId = body.has("sectionId") ? body.get("sectionId").getAsString() : "";
        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        String title = body.has("title") ? body.get("title").getAsString().trim() : "";
        if (sectionId.isEmpty() || categoryId.isEmpty() || title.isEmpty()) {
            respondError(ctx, "Sektion, Kategorie und Titel sind erforderlich.");
            return;
        }

        JsonObject data = load();
        JsonObject cat = findCategory(data, sectionId, categoryId);
        if (cat == null) { respondError(ctx, "Kategorie nicht gefunden."); return; }
        cat.addProperty("title", title);
        save(data);

        respondOk(ctx, data);
    }

    /**
     * POST /api/regelwerk/category/move  body: { "sectionId", "categoryId", "direction": "up"|"down" }
     * Verschiebt eine Kategorie nach oben/unten und nummeriert § neu durch.
     */
    public static void handleMoveCategory(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String sectionId = body.has("sectionId") ? body.get("sectionId").getAsString() : "";
        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        String direction = body.has("direction") ? body.get("direction").getAsString() : "";
        if (sectionId.isEmpty() || categoryId.isEmpty()) { respondError(ctx, "Sektion und Kategorie fehlen."); return; }

        JsonObject data = load();
        JsonObject sec = findSection(data, sectionId);
        if (sec == null) { respondError(ctx, "Sektion nicht gefunden."); return; }

        JsonArray cats = sec.getAsJsonArray("categories");
        int idx = -1;
        for (int i = 0; i < cats.size(); i++) {
            if (cats.get(i).getAsJsonObject().get("id").getAsString().equals(categoryId)) { idx = i; break; }
        }
        if (idx < 0) { respondError(ctx, "Kategorie nicht gefunden."); return; }

        int target = "up".equals(direction) ? idx - 1 : ("down".equals(direction) ? idx + 1 : -1);
        if (target < 0 || target >= cats.size()) { respondError(ctx, "Verschieben nicht möglich."); return; }

        JsonElement tmp = cats.get(idx);
        cats.set(idx, cats.get(target));
        cats.set(target, tmp);
        renumber(cats);
        save(data);

        respondOk(ctx, data);
    }

    /** POST /api/regelwerk/entry  body: { "sectionId", "categoryId", "text" } */
    public static void handleAddEntry(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String sectionId = body.has("sectionId") ? body.get("sectionId").getAsString() : "";
        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        String text = body.has("text") ? body.get("text").getAsString().trim() : "";
        if (sectionId.isEmpty() || categoryId.isEmpty() || text.isEmpty()) {
            respondError(ctx, "Sektion, Kategorie und Text sind erforderlich.");
            return;
        }

        JsonObject data = load();
        JsonObject cat = findCategory(data, sectionId, categoryId);
        if (cat == null) { respondError(ctx, "Kategorie nicht gefunden."); return; }
        cat.getAsJsonArray("texts").add(text);
        save(data);

        respondOk(ctx, data);
    }

    /** POST /api/regelwerk/entry/edit  body: { "sectionId", "categoryId", "index", "text" } */
    public static void handleEditEntry(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String sectionId = body.has("sectionId") ? body.get("sectionId").getAsString() : "";
        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        String text = body.has("text") ? body.get("text").getAsString().trim() : "";
        if (sectionId.isEmpty() || categoryId.isEmpty()) { respondError(ctx, "Sektion und Kategorie fehlen."); return; }

        JsonObject data = load();
        JsonObject cat = findCategory(data, sectionId, categoryId);
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

    /**
     * POST /api/regelwerk/delete
     * body: { "sectionId", "categoryId" }                 → ganze Kategorie löschen
     *       { "sectionId", "categoryId", "index" }        → einzelnen Text löschen
     */
    public static void handleDelete(Context ctx) {
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { respondError(ctx, "Ungültige Anfrage."); return; }

        String sectionId = body.has("sectionId") ? body.get("sectionId").getAsString() : "";
        String categoryId = body.has("categoryId") ? body.get("categoryId").getAsString() : "";
        if (sectionId.isEmpty() || categoryId.isEmpty()) { respondError(ctx, "Sektion und Kategorie fehlen."); return; }

        JsonObject data = load();
        JsonObject sec = findSection(data, sectionId);
        if (sec == null) { respondError(ctx, "Sektion nicht gefunden."); return; }

        JsonArray cats = sec.getAsJsonArray("categories");
        JsonObject cat = null;
        for (JsonElement el : cats) {
            if (el.getAsJsonObject().get("id").getAsString().equals(categoryId)) { cat = el.getAsJsonObject(); break; }
        }
        if (cat == null) { respondError(ctx, "Kategorie nicht gefunden."); return; }

        if (body.has("index")) {
            int idx = body.get("index").getAsInt();
            JsonArray texts = cat.getAsJsonArray("texts");
            if (idx < 0 || idx >= texts.size()) { respondError(ctx, "Ungültiger Index."); return; }
            texts.remove(idx);
        } else {
            JsonArray keep = new JsonArray();
            for (JsonElement el : cats) {
                if (!el.getAsJsonObject().get("id").getAsString().equals(categoryId)) keep.add(el);
            }
            sec.add("categories", keep);
            renumber(sec.getAsJsonArray("categories"));
        }
        save(data);

        respondOk(ctx, data);
    }

    /** Nummeriert die §-Präfixe aller Kategorien einer Sektion nach Position neu durch. */
    private static void renumber(JsonArray cats) {
        for (int i = 0; i < cats.size(); i++) {
            JsonObject c = cats.get(i).getAsJsonObject();
            String t = c.has("title") ? c.get("title").getAsString() : "";
            t = t.replaceFirst("^§[0-9]+(\\.[0-9]+)?\\s*", "");
            c.addProperty("title", "§" + (i + 1) + ".0 " + t);
        }
    }

    private static JsonObject findSection(JsonObject data, String sectionId) {
        for (JsonElement el : data.getAsJsonArray("sections")) {
            JsonObject s = el.getAsJsonObject();
            if (s.get("id").getAsString().equals(sectionId)) return s;
        }
        return null;
    }

    private static JsonObject findCategory(JsonObject data, String sectionId, String categoryId) {
        JsonObject sec = findSection(data, sectionId);
        if (sec == null) return null;
        for (JsonElement el : sec.getAsJsonArray("categories")) {
            JsonObject c = el.getAsJsonObject();
            if (c.get("id").getAsString().equals(categoryId)) return c;
        }
        return null;
    }

    private static void respondOk(Context ctx, JsonObject data) {
        JsonObject out = new JsonObject();
        out.addProperty("ok", true);
        out.add("sections", data.getAsJsonArray("sections"));
        ctx.contentType("application/json").result(out.toString());
    }

    private static void respondError(Context ctx, String msg) {
        JsonObject out = new JsonObject();
        out.addProperty("ok", false);
        out.addProperty("error", msg);
        ctx.contentType("application/json").result(out.toString());
    }
}
