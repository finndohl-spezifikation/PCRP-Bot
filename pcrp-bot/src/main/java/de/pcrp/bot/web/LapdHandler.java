package de.pcrp.bot.web;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import de.pcrp.bot.common.BotContext;
import de.pcrp.bot.common.LapdDashManager;
import de.pcrp.bot.common.LapdManager;
import io.javalin.http.Context;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * HTTP-Routes für die LAPD-Webseite.
 *
 * Routes:
 *   POST /api/lapd/create           {type, uid, name, message, fields} → neuen Eintrag anlegen
 *   GET  /api/lapd/my?uid=…          → eigene Mails/Beschwerden/Anzeigen/Bewerbungen
 *   POST /api/lapd/reply             {type, id, uid, name, text} → als Bürger antworten
 *   GET  /api/lapd/dashboard         → alle Einträge (LAPD-Dashboard)
 *   POST /api/lapd/dashboard/reply   {type, id, text} → als LAPD antworten (+ DM an den Bürger)
 *   POST /api/lapd/dashboard/status  {type, id, status} → offen/gelöst/geschlossen
 *   POST /api/lapd/dashboard/decide  {type:"bewerbung", id, action} → annehmen / ablehnen (+ DM)
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
        return "mail".equals(type) || "anzeige".equals(type)
                || "bewerbung".equals(type) || "beschwerde".equals(type);
    }

    private static void respond(Context ctx, JsonObject out) {
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    private static void err(Context ctx, JsonObject out, String msg) {
        out.addProperty("ok", false);
        out.addProperty("error", msg);
        respond(ctx, out);
    }

    /** Zentrale Web-URL (WEB_URL → Railway-Fallback) für Links in DMs. */
    private static String webUrl() {
        String url = System.getenv("WEB_URL");
        if (url == null || url.isBlank()) {
            url = System.getenv().getOrDefault("RAILWAY_PUBLIC_DOMAIN",
                    "https://dashboards.paradisecity-roleplay-85a.workers.dev");
            if (!url.startsWith("http")) url = "https://" + url;
        }
        return url.replaceAll("/$", "");
    }

    /** Postfach-Link je Typ (öffnet die richtige Ansicht direkt). */
    private static String postfachLink(String type) {
        String base = webUrl();
        return switch (type) {
            case "mail"       -> base + "/lapd";
            case "beschwerde" -> base + "/lapd#beschwerde";
            case "anzeige"    -> base + "/lapd#anzeige";
            case "bewerbung"  -> base + "/lapd/karriere#meine";
            default           -> base + "/lapd";
        };
    }

    // ── Bann-Prüfung (gilt auch für die LAPD-Webseite) ───────────────────────

    /** Alle Namen, unter denen gebannte Personen auf der Webseite erkannt werden (case-insensitive). */
    private static Set<String> bannedNames(long gid) {
        Set<String> names = new HashSet<>();
        Guild guild = BotContext.getGuild();
        for (LapdDashManager.Ban b : LapdDashManager.bannedList(gid)) {
            if (b.name != null && !b.name.isBlank()) names.add(b.name.trim().toLowerCase());
            if (guild != null) {
                Member m = guild.getMemberById(b.discordId);
                if (m != null) {
                    names.add(m.getEffectiveName().trim().toLowerCase());
                    names.add(m.getUser().getName().trim().toLowerCase());
                }
            }
        }
        return names;
    }

    /** Prüft, ob einer der eingegebenen Namen zu einer gebannten Person gehört. */
    private static boolean isBannedName(long gid, String... names) {
        Set<String> banned = bannedNames(gid);
        if (banned.isEmpty()) return false;
        for (String n : names) {
            if (n != null && !n.isBlank() && banned.contains(n.trim().toLowerCase())) return true;
        }
        return false;
    }

    /** Discord-Feld eines Eintrags (Schlüssel „Discord“ oder „discord“). */
    private static String discordField(LapdManager.Item i) {
        if (i == null || i.data == null) return "";
        String v = i.data.get("Discord");
        if (v == null || v.isBlank()) v = i.data.get("discord");
        return v == null ? "" : v;
    }

    /** Filtert Einträge von gebannten Personen heraus. */
    private static List<LapdManager.Item> filterBanned(long gid, List<LapdManager.Item> items) {
        List<LapdManager.Item> out = new ArrayList<>();
        for (LapdManager.Item i : items) {
            if (!isBannedName(gid, i.name, discordField(i))) out.add(i);
        }
        return out;
    }

    /**
     * Sendet eine DM an den Bürger, falls wir einen Discord-Nutzer auflösen können.
     * Bevorzugt das Feld „discord” aus den Formularfeldern, sonst der eingegebene Name.
     */
    private static void sendDm(LapdManager.Item item, String content) {
        if (item == null || content == null || content.isBlank()) return;
        String discordName = discordField(item);
        if (discordName.isEmpty()) discordName = item.name;
        if (discordName.isEmpty()) return;

        Member m = BotContext.findMemberByUsername(discordName);
        if (m == null) {
            log.info("[LAPD] DM nicht gesendet – Discord-Nutzer '{}' nicht gefunden (Eintrag {}/{})",
                    discordName, item.id, item.status);
            return;
        }
        m.getUser().openPrivateChannel().queue(
            pc -> pc.sendMessage(content).queue(null, e -> log.warn("[LAPD] DM-Zustellung fehlgeschlagen: {}", e.getMessage())),
            e  -> log.warn("[LAPD] DM-Kanal konnte nicht geöffnet werden: {}", e.getMessage())
        );
    }

    // ── Eintrag erstellen ────────────────────────────────────────────────────

    /** POST /api/lapd/create – neuen Eintrag anlegen (mail / anzeige / bewerbung / beschwerde). */
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
        if (message.isEmpty()) { err(ctx, out, "Bitte fülle das Formular vollständig aus."); return; }

        // Gebannte Personen können auf der Webseite nichts mehr einreichen
        if (b != null && b.has("fields") && b.get("fields").isJsonObject()) {
            JsonObject fo = b.getAsJsonObject("fields");
            String discord = fo.has("Discord") ? fo.get("Discord").getAsString() :
                             (fo.has("discord") ? fo.get("discord").getAsString() : "");
            if (isBannedName(gid, name, discord)) {
                out.addProperty("banned", true);
                err(ctx, out, "Dein Zugriff wurde von einem Administrator gesperrt. Sollte das ein Fehler sein, wende dich bitte an das High Team im Discord.");
                return;
            }
        } else if (isBannedName(gid, name)) {
            out.addProperty("banned", true);
            err(ctx, out, "Dein Zugriff wurde von einem Administrator gesperrt. Sollte das ein Fehler sein, wende dich bitte an das High Team im Discord.");
            return;
        }

        Map<String, String> fields = new LinkedHashMap<>();
        if (b != null && b.has("fields") && b.get("fields").isJsonObject()) {
            JsonObject fo = b.getAsJsonObject("fields");
            for (Map.Entry<String, JsonElement> e : fo.entrySet()) {
                if (e.getValue() != null && !e.getValue().isJsonNull()) {
                    fields.put(e.getKey(), e.getValue().getAsString().trim());
                }
            }
        }

        LapdManager.Item item = LapdManager.create(gid, type, uid, name, message, fields);
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
        out.add("mails",       GSON.toJsonTree(filterBanned(gid, mine.mails)));
        out.add("anzeigen",    GSON.toJsonTree(filterBanned(gid, mine.anzeigen)));
        out.add("bewerbungen", GSON.toJsonTree(filterBanned(gid, mine.bewerbungen)));
        out.add("beschwerden", GSON.toJsonTree(filterBanned(gid, mine.beschwerden)));
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
        out.add("mails",       GSON.toJsonTree(filterBanned(gid, all.mails)));
        out.add("anzeigen",    GSON.toJsonTree(filterBanned(gid, all.anzeigen)));
        out.add("bewerbungen", GSON.toJsonTree(filterBanned(gid, all.bewerbungen)));
        out.add("beschwerden", GSON.toJsonTree(filterBanned(gid, all.beschwerden)));
        respond(ctx, out);
    }

    /** POST /api/lapd/dashboard/reply – Antwort als LAPD schreiben (+ DM an den Bürger). */
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

        // DM-Benachrichtigung an den Bürger
        LapdManager.Item item = LapdManager.find(gid, type, id);
        if (item != null) {
            if ("bewerbung".equals(type)) {
                sendDm(item, "📨 **Antwort auf Ihre Bewerbung beim LAPD**\n\n" + text
                        + "\n\n🔗 **Zum Bewerbungsportal:** " + postfachLink(type));
            } else {
                sendDm(item, "📬 **Sie haben eine neue Nachricht in Ihrem Postfach beim LAPD.**\n\n" + text
                        + "\n\n🔗 **Postfach öffnen:** " + postfachLink(type));
            }
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

    /** POST /api/lapd/dashboard/delete – Eintrag endgültig löschen. */
    public static void handleDashDelete(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        JsonObject b = body(ctx);
        String type = str(b, "type");
        String id   = str(b, "id");

        if (!isType(type) || id.isEmpty()) { err(ctx, out, "Ungültige Anfrage."); return; }
        if (!LapdManager.delete(gid, type, id)) {
            err(ctx, out, "Eintrag nicht gefunden.");
            return;
        }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    /** POST /api/lapd/dashboard/decide – Bewerbung annehmen / ablehnen (+ automatische DM). */
    public static void handleDashDecide(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        JsonObject b = body(ctx);
        String type   = str(b, "type");
        String id     = str(b, "id");
        String action = str(b, "action");

        if (!"bewerbung".equals(type) || id.isEmpty()) { err(ctx, out, "Ungültige Anfrage."); return; }

        LapdManager.Item item = LapdManager.find(gid, type, id);
        if (item == null) { err(ctx, out, "Bewerbung nicht gefunden."); return; }

        switch (action) {
            case "annehmen" -> {
                if (!LapdManager.setStatus(gid, type, id, LapdManager.STATUS_ANGENOMMEN)) {
                    err(ctx, out, "Status konnte nicht gesetzt werden."); return;
                }
                sendDm(item, "🎉 **Herzlichen Glückwunsch!** Sie haben den ersten Teil Ihrer Bewerbung bestanden. "
                        + "Bitte folgen Sie nun Ihrer zuständigen Führungsebene.\n\n"
                        + "🔗 **Zum Bewerbungsportal:** " + postfachLink(type));
            }
            case "ablehnen" -> {
                if (!LapdManager.setStatus(gid, type, id, LapdManager.STATUS_ABGELEHNT)) {
                    err(ctx, out, "Status konnte nicht gesetzt werden."); return;
                }
                sendDm(item, "❌ **Leider hat es dieses Mal nicht geklappt.** Ihre Bewerbung kann daher nicht "
                        + "länger berücksichtigt werden. Wir danken Ihnen dennoch für Ihr Interesse und wünschen "
                        + "Ihnen alles Gute bei Ihrem weiteren Bewerbungsweg.\n\n"
                        + "🔗 **Zum Bewerbungsportal:** " + postfachLink(type));
            }
            case "offen" -> {
                if (!LapdManager.setStatus(gid, type, id, LapdManager.STATUS_OFFEN)) {
                    err(ctx, out, "Status konnte nicht gesetzt werden."); return;
                }
            }
            default -> { err(ctx, out, "Unbekannte Aktion."); return; }
        }

        out.addProperty("ok", true);
        respond(ctx, out);
    }
}
