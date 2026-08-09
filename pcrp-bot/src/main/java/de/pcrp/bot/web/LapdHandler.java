package de.pcrp.bot.web;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import de.pcrp.bot.common.BotContext;
import de.pcrp.bot.common.LapdManager;
import io.javalin.http.Context;
import net.dv8tion.jda.api.entities.Guild;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * HTTP-Routes für die LAPD-Webseite (Grundstein).
 *
 * Routes:
 *   POST /api/lapd/create           {type, uid, name, message} → neuen Eintrag anlegen
 *   GET  /api/lapd/my?uid=…          → eigene Mails/Anzeigen/Bewerbungen
 *   POST /api/lapd/reply             {type, id, uid, name, text} → als Bürger antworten
 *   GET  /api/lapd/dashboard         → alle Einträge (LAPD-Dashboard)
 *   POST /api/lapd/dashboard/reply   {type, id, text} → als LAPD antworten
 *   POST /api/lapd/dashboard/status  {type, id, status} → offen/gelöst/geschlossen
 */
public class LapdHandler {

    private static final Logger log  = LoggerFactory.getLogger(LapdHandler.class);
    private static final Gson   GSON = new GsonBuilder().create();

    private LapdHandler() {}

    // ── Helfer ───────────────────────────────────────────────────────────────

    private static Long guildId(Context ctx, JsonObject out) {
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            out.addProperty("ok", false);
            out.addProperty("error", "Server nicht bereit.");
            respond(ctx, out);
            return null;
        }
        return guild.getIdLong();
    }

    private static JsonObject body(Context ctx) {
        try {
            return JsonParser.parseString(ctx.body()).getAsJsonObject();
        } catch (Exception e) {
            return null;
        }
    }

    private static String str(JsonObject o, String key) {
        return o != null && o.has(key) && !o.get(key).isJsonNull() ? o.get(key).getAsString().trim() : "";
    }

    private static boolean isType(String type) {
        return "mail".equals(type) || "anzeige".equals(type) || "bewerbung".equals(type);
    }

    private static void respond(Context ctx, JsonObject out) {
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    private static void err(Context ctx, JsonObject out, String msg) {
        out.addProperty("ok", false);
        out.addProperty("error", msg);
        respond(ctx, out);
    }

    // ── Eintrag erstellen ────────────────────────────────────────────────────

    /** POST /api/lapd/create – neuen Eintrag anlegen (mail / anzeige / bewerbung). */
    public static void handleCreate(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        JsonObject b = body(ctx);
        String type = str(b, "type");
        String uid  = str(b, "uid");
        String name = str(b, "name");
        String message = str(b, "message");

        if (!isType(type)) { err(ctx, out, "Ungültiger Typ."); return; }
        if (uid.isEmpty()) { err(ctx, out, "Kennung fehlt – bitte Seite neu laden."); return; }
        if (name.isEmpty()) { err(ctx, out, "Bitte gib deinen Namen ein."); return; }
        if (message.isEmpty()) { err(ctx, out, "Bitte gib eine Nachricht ein."); return; }

        LapdManager.Item item = LapdManager.create(gid, type, uid, name, message);
        if (item == null) { err(ctx, out, "Ungültiger Typ."); return; }

        out.addProperty("ok", true);
        out.add("item", GSON.toJsonTree(item));
        respond(ctx, out);
    }

    /** GET /api/lapd/my?uid=… – eigene Einträge. */
    public static void handleMy(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        String uid = ctx.queryParam("uid");
        if (uid == null || uid.isEmpty()) { err(ctx, out, "Kennung fehlt."); return; }

        LapdManager.Store mine = LapdManager.my(gid, uid);
        out.addProperty("ok", true);
        out.add("mails",       GSON.toJsonTree(mine.mails));
        out.add("anzeigen",    GSON.toJsonTree(mine.anzeigen));
        out.add("bewerbungen", GSON.toJsonTree(mine.bewerbungen));
        respond(ctx, out);
    }

    /** POST /api/lapd/reply – Bürger antwortet auf eigenen offenen Eintrag. */
    public static void handleReply(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        JsonObject b = body(ctx);
        String type = str(b, "type");
        String id   = str(b, "id");
        String uid  = str(b, "uid");
        String name = str(b, "name");
        String text = str(b, "text");

        if (!isType(type) || id.isEmpty() || text.isEmpty()) { err(ctx, out, "Ungültige Anfrage."); return; }
        if (!LapdManager.reply(gid, type, id, uid, name, text)) {
            err(ctx, out, "Antwort nicht möglich – Eintrag nicht gefunden, nicht deiner oder nicht mehr offen.");
            return;
        }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── LAPD-Dashboard ───────────────────────────────────────────────────────

    /** GET /api/lapd/dashboard – alle Einträge (LAPD-Dashboard). */
    public static void handleDashboard(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        LapdManager.Store all = LapdManager.all(gid);
        out.addProperty("ok", true);
        out.add("mails",       GSON.toJsonTree(all.mails));
        out.add("anzeigen",    GSON.toJsonTree(all.anzeigen));
        out.add("bewerbungen", GSON.toJsonTree(all.bewerbungen));
        respond(ctx, out);
    }

    /** POST /api/lapd/dashboard/reply – Antwort als LAPD schreiben. */
    public static void handleDashReply(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        JsonObject b = body(ctx);
        String type = str(b, "type");
        String id   = str(b, "id");
        String text = str(b, "text");

        if (!isType(type) || id.isEmpty() || text.isEmpty()) { err(ctx, out, "Ungültige Anfrage."); return; }
        if (!LapdManager.dashReply(gid, type, id, text)) {
            err(ctx, out, "Eintrag nicht gefunden.");
            return;
        }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    /** POST /api/lapd/dashboard/status – Status setzen (offen / gelöst / geschlossen). */
    public static void handleDashStatus(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        JsonObject b = body(ctx);
        String type   = str(b, "type");
        String id     = str(b, "id");
        String status = str(b, "status");

        if (!isType(type) || id.isEmpty() || status.isEmpty()) { err(ctx, out, "Ungültige Anfrage."); return; }
        if (!LapdManager.setStatus(gid, type, id, status)) {
            err(ctx, out, "Status konnte nicht gesetzt werden.");
            return;
        }
        out.addProperty("ok", true);
        respond(ctx, out);
    }
}
