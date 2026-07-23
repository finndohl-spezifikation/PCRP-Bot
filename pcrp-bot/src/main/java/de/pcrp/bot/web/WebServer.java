package de.pcrp.bot.web;

import com.google.gson.*;
import de.pcrp.bot.common.*;
import io.javalin.Javalin;
import io.javalin.http.Context;
import io.javalin.http.UploadedFile;
import net.dv8tion.jda.api.entities.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.InputStream;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Eingebetteter Web-Server für das Einwohner-Meldeamt.
 * Läuft im gleichen Prozess wie der Bot.
 * Railway setzt die PORT-Umgebungsvariable automatisch.
 */
public class WebServer {

    private static final Logger log  = LoggerFactory.getLogger(WebServer.class);
    private static final Gson   GSON = new GsonBuilder().create();

    private WebServer() {}

    public static void start(int port) {
        Javalin app = Javalin.create(config -> {
            config.http.maxRequestSize = 12L * 1024 * 1024; // 12 MB
            config.requestLogger.http((ctx, ms) ->
                log.debug("[Web] {} {} → {}", ctx.method(), ctx.path(), ctx.status()));
        });

        // ── Frontend ──────────────────────────────────────────────
        app.get("/",                     WebServer::serveIndex);
        app.get("/ausweis/{userId}",      WebServer::serveAusweis);

        // ── API ───────────────────────────────────────────────────
        app.post("/api/validate",         WebServer::handleValidate);
        app.post("/api/register/legal",   WebServer::handleLegal);
        app.post("/api/register/illegal", WebServer::handleIllegal);
        app.get("/api/photo/{userId}",    WebServer::servePhoto);

        app.start(port);
        log.info("[WebServer] Einwohner-Meldeamt läuft auf Port {}.", port);
    }

    // ════════════════════════════════════════════════════════════
    //  STATIC: index.html
    // ════════════════════════════════════════════════════════════

    private static void serveIndex(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/index.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ════════════════════════════════════════════════════════════
    //  API: Discord-Nutzername prüfen
    // ════════════════════════════════════════════════════════════

    private static void handleValidate(Context ctx) {
        if (!BotContext.isReady()) { json(ctx, 503, "error", "Bot noch nicht bereit."); return; }
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { json(ctx, 400, "error", "Ungültige JSON-Anfrage."); return; }

        String username = body.has("username") ? body.get("username").getAsString().trim() : "";
        if (username.isBlank()) { json(ctx, 400, "error", "Kein Nutzername angegeben."); return; }

        Guild guild = BotContext.getGuild();
        Member member = BotContext.findMemberByUsername(username);
        if (member == null) {
            json(ctx, 200, false, "Nutzer nicht auf dem Server gefunden.");
            return;
        }

        // Auto-Rolle prüfen
        boolean hasAutoRole = member.getRoles().stream()
            .anyMatch(r -> r.getIdLong() == ModerationConfig.AUTO_ROLE_ID);
        if (!hasAutoRole) {
            json(ctx, 200, false, "Keine Berechtigung zur Einreise (Auto-Rolle fehlt).");
            return;
        }

        // Bereits registriert?
        if (CharacterStore.exists(guild.getIdLong(), member.getIdLong())) {
            json(ctx, 200, false, "Dieser Nutzer ist bereits eingereist.");
            return;
        }

        JsonObject ok = new JsonObject();
        ok.addProperty("valid",       true);
        ok.addProperty("userId",      member.getId());
        ok.addProperty("displayName", member.getUser().getName());
        ctx.contentType("application/json").result(GSON.toJson(ok));
    }

    // ════════════════════════════════════════════════════════════
    //  API: Legale Einreise
    // ════════════════════════════════════════════════════════════

    private static void handleLegal(Context ctx) {
        if (!BotContext.isReady()) { json(ctx, 503, "error", "Bot noch nicht bereit."); return; }

        String userId    = ctx.formParam("userId");
        String psn       = ctx.formParam("psnName");
        String firstName = ctx.formParam("firstName");
        String lastName  = ctx.formParam("lastName");
        String birthDate = ctx.formParam("birthDate");
        String birthPlace= ctx.formParam("birthPlace");
        String national  = ctx.formParam("nationality");
        String residence = ctx.formParam("residence");
        UploadedFile photo = ctx.uploadedFile("photo");

        if (isBlank(userId, psn, firstName, lastName, birthDate, birthPlace, national, residence)) {
            json(ctx, 400, "error", "Alle Felder müssen ausgefüllt sein."); return;
        }
        if (photo == null) {
            json(ctx, 400, "error", "Bitte lade ein Foto deines Charakters hoch."); return;
        }

        Guild  guild  = BotContext.getGuild();
        Member member = guild.getMemberById(userId);
        if (member == null) { json(ctx, 400, "error", "Nutzer nicht mehr auf dem Server."); return; }

        if (CharacterStore.exists(guild.getIdLong(), member.getIdLong())) {
            json(ctx, 400, "error", "Dieser Nutzer ist bereits eingereist."); return;
        }

        // Foto speichern
        String contentType = photo.contentType() != null ? photo.contentType() : "image/jpeg";
        String ext = contentType.contains("png") ? ".png" : ".jpg";
        Path photoPath = DataStore.getPath("photos").resolve(userId + ext);
        try {
            Files.createDirectories(photoPath.getParent());
            Files.copy(photo.content(), photoPath, StandardCopyOption.REPLACE_EXISTING);
        } catch (Exception e) {
            log.error("[Meldeamt] Foto konnte nicht gespeichert werden.", e);
            json(ctx, 500, "error", "Foto-Upload fehlgeschlagen."); return;
        }

        // Charakter speichern
        JsonObject character = new JsonObject();
        character.addProperty("type",            "legal");
        character.addProperty("discordUsername", member.getUser().getName());
        character.addProperty("discordUserId",   userId);
        character.addProperty("psnName",         psn.trim());
        character.addProperty("firstName",       firstName.trim());
        character.addProperty("lastName",        lastName.trim());
        character.addProperty("birthDate",       birthDate.trim());
        character.addProperty("birthPlace",      birthPlace.trim());
        character.addProperty("nationality",     national.trim());
        character.addProperty("residence",       residence.trim());
        character.addProperty("photoExt",        ext);
        character.addProperty("registeredAt",    Instant.now().toString());
        CharacterStore.save(guild.getIdLong(), member.getIdLong(), character);

        // Economy
        EconomyStore.addCoins(guild.getIdLong(), member.getIdLong(), RoleConfig.REGISTRATION_REWARD);

        // Rollen + Nickname (async, non-blocking)
        applyRoles(guild, member, RoleConfig.LEGAL_ROLES);
        String nick = firstName.trim() + " " + lastName.trim() + " / " + psn.trim();
        guild.modifyNickname(member, nick).queue(
            ok -> log.info("[Meldeamt] Nickname für {} gesetzt: {}", member.getUser().getName(), nick),
            err -> log.warn("[Meldeamt] Nickname konnte nicht gesetzt werden.", err)
        );

        log.info("[Meldeamt] Legale Einreise: {} ({}).", member.getUser().getName(), userId);
        jsonOk(ctx);
    }

    // ════════════════════════════════════════════════════════════
    //  API: Illegale Einreise
    // ════════════════════════════════════════════════════════════

    private static void handleIllegal(Context ctx) {
        if (!BotContext.isReady()) { json(ctx, 503, "error", "Bot noch nicht bereit."); return; }

        String userId    = ctx.formParam("userId");
        String psn       = ctx.formParam("psnName");
        String firstName = ctx.formParam("firstName");
        String lastName  = ctx.formParam("lastName");

        if (isBlank(userId, psn, firstName, lastName)) {
            json(ctx, 400, "error", "Alle Felder müssen ausgefüllt sein."); return;
        }

        Guild  guild  = BotContext.getGuild();
        Member member = guild.getMemberById(userId);
        if (member == null) { json(ctx, 400, "error", "Nutzer nicht mehr auf dem Server."); return; }

        if (CharacterStore.exists(guild.getIdLong(), member.getIdLong())) {
            json(ctx, 400, "error", "Dieser Nutzer ist bereits eingereist."); return;
        }

        // Charakter speichern
        JsonObject character = new JsonObject();
        character.addProperty("type",            "illegal");
        character.addProperty("discordUsername", member.getUser().getName());
        character.addProperty("discordUserId",   userId);
        character.addProperty("psnName",         psn.trim());
        character.addProperty("firstName",       firstName.trim());
        character.addProperty("lastName",        lastName.trim());
        character.addProperty("registeredAt",    Instant.now().toString());
        CharacterStore.save(guild.getIdLong(), member.getIdLong(), character);

        // Economy
        EconomyStore.addCoins(guild.getIdLong(), member.getIdLong(), RoleConfig.REGISTRATION_REWARD);

        // Rollen + Nickname
        applyRoles(guild, member, RoleConfig.ILLEGAL_ROLES);
        String nick = firstName.trim() + " " + lastName.trim() + " / " + psn.trim();
        guild.modifyNickname(member, nick).queue(
            ok -> log.info("[Meldeamt] Nickname für {} gesetzt: {}", member.getUser().getName(), nick),
            err -> log.warn("[Meldeamt] Nickname konnte nicht gesetzt werden.", err)
        );

        log.info("[Meldeamt] Illegale Einreise: {} ({}).", member.getUser().getName(), userId);
        jsonOk(ctx);
    }

    // ════════════════════════════════════════════════════════════
    //  API: Foto abrufen
    // ════════════════════════════════════════════════════════════

    private static void servePhoto(Context ctx) {
        String userId = ctx.pathParam("userId");
        for (String ext : List.of(".jpg", ".png")) {
            Path p = DataStore.getPath("photos").resolve(userId + ext);
            if (Files.exists(p)) {
                try {
                    ctx.contentType(ext.equals(".png") ? "image/png" : "image/jpeg")
                       .result(Files.readAllBytes(p));
                    return;
                } catch (Exception e) {
                    ctx.status(500).result("Fehler beim Lesen des Fotos.");
                    return;
                }
            }
        }
        ctx.status(404).result("Kein Foto vorhanden.");
    }

    // ════════════════════════════════════════════════════════════
    //  AUSWEIS – HTML-Seite (California-Style)
    // ════════════════════════════════════════════════════════════

    private static void serveAusweis(Context ctx) {
        String userIdStr = ctx.pathParam("userId");
        Guild guild = BotContext.getGuild();
        if (guild == null) { ctx.status(503).html("<h1>Bot noch nicht bereit.</h1>"); return; }

        long userId;
        try { userId = Long.parseLong(userIdStr); }
        catch (NumberFormatException e) { ctx.status(400).html("<h1>Ungültige ID.</h1>"); return; }

        JsonObject ch = CharacterStore.get(guild.getIdLong(), userId);
        if (ch == null) { ctx.status(404).html("<h1>Kein Charakter gefunden.</h1>"); return; }

        ctx.contentType("text/html;charset=utf-8").result(buildIdCard(ch, userIdStr));
    }

    private static String buildIdCard(JsonObject ch, String userId) {
        boolean isLegal = "legal".equals(CharacterStore.str(ch, "type"));
        String photoUrl = "/api/photo/" + userId;
        String fn = CharacterStore.str(ch, "firstName");
        String ln = CharacterStore.str(ch, "lastName");
        String bd = CharacterStore.str(ch, "birthDate");
        String bp = CharacterStore.str(ch, "birthPlace");
        String na = CharacterStore.str(ch, "nationality");
        String re = CharacterStore.str(ch, "residence");
        String ps = CharacterStore.str(ch, "psnName");
        String idNum = "LA-" + userId.substring(Math.max(0, userId.length() - 8)).toUpperCase();

        return "<!DOCTYPE html><html lang=\"de\"><head>" +
            "<meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">" +
            "<title>Ausweis – " + esc(fn) + " " + esc(ln) + "</title>" +
            "<style>" +
            "body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;" +
            "background:linear-gradient(135deg,#0a0a0a 0%,#0f0f1a 100%);font-family:'Courier New',monospace;}" +
            ".card{width:680px;background:linear-gradient(135deg,#0d2346 0%,#081830 100%);" +
            "border:3px solid #c8a048;border-radius:14px;overflow:hidden;box-shadow:0 0 40px rgba(200,160,72,0.3);}" +
            ".header{background:linear-gradient(90deg,#0a1c38,#0d2550);border-bottom:3px solid #c8a048;" +
            "padding:14px 20px;display:flex;align-items:center;gap:16px;}" +
            ".header .bear{font-size:2.4rem;}" +
            ".header-text{flex:1;}" +
            ".header-text .state{display:block;color:#c8a048;font-size:1.3rem;font-weight:700;letter-spacing:4px;}" +
            ".header-text .city{display:block;color:#a8c4e0;font-size:0.75rem;letter-spacing:2px;margin-top:2px;}" +
            ".header .type-badge{background:" + (isLegal ? "#1a5c2a" : "#5c1a1a") + ";" +
            "color:" + (isLegal ? "#4ef07a" : "#f04e4e") + ";padding:4px 12px;border-radius:4px;" +
            "font-size:0.7rem;font-weight:700;letter-spacing:2px;border:1px solid " +
            (isLegal ? "#4ef07a" : "#f04e4e") + ";}" +
            ".body{display:flex;gap:0;}" +
            ".photo-col{width:180px;min-height:240px;background:#06111f;display:flex;align-items:center;" +
            "justify-content:center;border-right:2px solid #c8a04840;padding:16px;flex-shrink:0;}" +
            ".photo-col img{width:148px;height:180px;object-fit:cover;border:2px solid #c8a048;border-radius:4px;}" +
            ".no-photo{width:148px;height:180px;display:flex;align-items:center;justify-content:center;" +
            "background:#0a1825;border:2px solid #c8a04860;border-radius:4px;color:#445;font-size:0.7rem;text-align:center;}" +
            ".data-col{flex:1;padding:20px;}" +
            ".id-num{color:#c8a048;font-size:0.7rem;letter-spacing:2px;margin-bottom:14px;}" +
            ".field{margin-bottom:12px;}" +
            ".field label{display:block;color:#6a8fb0;font-size:0.6rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:2px;}" +
            ".field .val{color:#e8e8e8;font-size:0.95rem;font-weight:700;letter-spacing:1px;}" +
            ".fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;}" +
            ".footer{background:#06111f;border-top:2px solid #c8a04840;padding:10px 20px;" +
            "display:flex;justify-content:space-between;align-items:center;}" +
            ".footer .seal{color:#c8a04880;font-size:0.65rem;letter-spacing:1px;}" +
            ".footer .psn{color:#4a9eff;font-size:0.7rem;}" +
            "</style></head><body>" +
            "<div class=\"card\">" +
            "<div class=\"header\">" +
            "<span class=\"bear\">🐻</span>" +
            "<div class=\"header-text\">" +
            "<span class=\"state\">CALIFORNIA</span>" +
            "<span class=\"city\">CITY OF LOS ANGELES · PARADISE CITY ROLEPLAY</span>" +
            "</div>" +
            "<span class=\"type-badge\">" + (isLegal ? "LEGAL" : "ILLEGAL") + "</span>" +
            "</div>" +
            "<div class=\"body\">" +
            "<div class=\"photo-col\">" +
            (isLegal
                ? "<img src=\"" + photoUrl + "\" alt=\"Charakter-Foto\" onerror=\"this.parentNode.innerHTML='<div class=no-photo>Kein Foto</div>'\">"
                : "<div class=\"no-photo\">KEIN<br>AUSWEIS</div>") +
            "</div>" +
            "<div class=\"data-col\">" +
            "<div class=\"id-num\">ID-NR: " + esc(idNum) + "</div>" +
            "<div class=\"fields-grid\">" +
            field("Vorname",   fn) +
            field("Nachname",  ln) +
            (isLegal ? field("Geburtsdatum", bd) + field("Geburtsort", bp) : "") +
            (isLegal ? field("Nationalität", na) + field("Wohnort", re) : "") +
            "</div>" +
            "</div></div>" +
            "<div class=\"footer\">" +
            "<span class=\"seal\">STATE OF CALIFORNIA · OFFICIAL IDENTIFICATION</span>" +
            "<span class=\"psn\">PSN: " + esc(ps) + "</span>" +
            "</div></div></body></html>";
    }

    // ════════════════════════════════════════════════════════════
    //  HILFSMETHODEN
    // ════════════════════════════════════════════════════════════

    private static void applyRoles(Guild guild, Member member, long[] roleIds) {
        List<Role> toAdd = Arrays.stream(roleIds)
            .mapToObj(id -> guild.getRoleById(id))
            .filter(Objects::nonNull)
            .collect(Collectors.toList());
        Role autoRole = guild.getRoleById(ModerationConfig.AUTO_ROLE_ID);
        List<Role> toRemove = autoRole != null ? List.of(autoRole) : List.of();

        guild.modifyMemberRoles(member, toAdd, toRemove)
            .reason("Einwohner-Meldeamt Einreise")
            .queue(
                ok  -> log.info("[Meldeamt] Rollen für {} aktualisiert.", member.getUser().getName()),
                err -> log.error("[Meldeamt] Rollen-Update fehlgeschlagen für {}.", member.getUser().getName(), err)
            );
    }

    private static String field(String label, String value) {
        return "<div class=\"field\"><label>" + esc(label) + "</label><div class=\"val\">" + esc(value) + "</div></div>";
    }

    private static String esc(String s) {
        if (s == null) return "";
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;");
    }

    private static boolean isBlank(String... values) {
        for (String v : values) if (v == null || v.isBlank()) return true;
        return false;
    }

    private static void jsonOk(Context ctx) {
        JsonObject r = new JsonObject(); r.addProperty("success", true);
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    private static void json(Context ctx, int status, String key, String value) {
        JsonObject r = new JsonObject(); r.addProperty(key, value);
        ctx.status(status).contentType("application/json").result(GSON.toJson(r));
    }

    private static void json(Context ctx, int status, boolean valid, String reason) {
        JsonObject r = new JsonObject();
        r.addProperty("valid", valid);
        r.addProperty("reason", reason);
        ctx.status(status).contentType("application/json").result(GSON.toJson(r));
    }
}
