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

public class WebServer {

    private static final Logger log  = LoggerFactory.getLogger(WebServer.class);
    private static final Gson   GSON = new GsonBuilder().create();

    private WebServer() {}

    public static void start(int port) {
        Javalin app = Javalin.create(config -> {
            config.http.maxRequestSize = 60L * 1024 * 1024; // 60 MB (5 Personen × 10 MB)
            config.requestLogger.http((ctx, ms) ->
                log.debug("[Web] {} {} → {}", ctx.method(), ctx.path(), ctx.status()));
        });

        // Frontend
        app.get("/",                          WebServer::serveIndex);
        app.get("/ausweis/{userId}",           WebServer::serveAusweis);

        // API Status
        app.get("/api/einreise-status",        WebServer::handleEinreiseStatus);
        app.post("/api/einreise-notify",        WebServer::handleEinreiseNotify);

        // API Einzeleinreise
        app.post("/api/validate",              WebServer::handleValidate);
        app.post("/api/register/legal",        WebServer::handleLegal);
        app.post("/api/register/illegal",      WebServer::handleIllegal);
        app.get("/api/photo/{userId}",         WebServer::servePhoto);

        // API Gruppeneinreise
        app.post("/api/register/group/legal",   WebServer::handleGroupLegal);
        app.post("/api/register/group/illegal", WebServer::handleGroupIllegal);

        app.start(port);
        log.info("[WebServer] Einwohner-Meldeamt läuft auf Port {}.", port);
    }

    // ── /api/einreise-status ───────────────────────────────────

    private static void handleEinreiseStatus(Context ctx) {
        Guild guild = BotContext.getGuild();
        boolean active = false;
        if (guild != null) {
            String stored = DataStore.readString("einreise-sperre-" + guild.getId());
            active = stored != null && !stored.isBlank();
        }
        JsonObject r = new JsonObject();
        r.addProperty("sperre", active);
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    // ── /api/einreise-notify ───────────────────────────────────

    private static void handleEinreiseNotify(Context ctx) {
        Guild guild = BotContext.getGuild();
        JsonObject out = new JsonObject();
        if (guild == null) { out.addProperty("ok", false); out.addProperty("error", "Server nicht erreichbar."); ctx.contentType("application/json").result(GSON.toJson(out)); return; }

        JsonObject body;
        try { body = GSON.fromJson(ctx.body(), JsonObject.class); } catch (Exception e) { out.addProperty("ok", false); out.addProperty("error", "Ungültige Anfrage."); ctx.contentType("application/json").result(GSON.toJson(out)); return; }
        String username = body.has("username") ? body.get("username").getAsString().trim() : "";
        if (username.isEmpty()) { out.addProperty("ok", false); out.addProperty("error", "Kein Nutzername angegeben."); ctx.contentType("application/json").result(GSON.toJson(out)); return; }

        Member member = BotContext.findMemberByUsername(username);
        if (member == null) { out.addProperty("ok", false); out.addProperty("error", "Nutzername nicht gefunden. Stelle sicher, dass du auf dem Server bist."); ctx.contentType("application/json").result(GSON.toJson(out)); return; }

        String key = "einreise-notify-" + guild.getId();
        String raw = DataStore.readString(key);
        com.google.gson.JsonArray arr = new com.google.gson.JsonArray();
        if (raw != null && !raw.isBlank()) {
            try { arr = GSON.fromJson(raw, com.google.gson.JsonArray.class); } catch (Exception ignored) {}
        }
        // Duplikat vermeiden
        String userId = member.getId();
        boolean already = false;
        for (com.google.gson.JsonElement el : arr) if (el.getAsString().equals(userId)) { already = true; break; }
        if (!already) { arr.add(userId); DataStore.writeString(key, GSON.toJson(arr)); }

        out.addProperty("ok", true);
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    // ── index.html ─────────────────────────────────────────────

    private static void serveIndex(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/index.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── /api/validate ──────────────────────────────────────────

    private static void handleValidate(Context ctx) {
        if (!BotContext.isReady()) { json(ctx, 503, "error", "Bot noch nicht bereit."); return; }
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { json(ctx, 400, "error", "Ungültige JSON-Anfrage."); return; }

        String username = body.has("username") ? body.get("username").getAsString().trim() : "";
        if (username.isBlank()) { json(ctx, 400, "error", "Kein Nutzername angegeben."); return; }

        Guild  guild  = BotContext.getGuild();
        Member member = BotContext.findMemberByUsername(username);
        if (member == null) { json(ctx, 200, false, "Nutzer nicht auf dem Server gefunden."); return; }

        boolean hasAutoRole = member.getRoles().stream()
            .anyMatch(r -> r.getIdLong() == ModerationConfig.AUTO_ROLE_ID);
        if (!hasAutoRole) { json(ctx, 200, false, "Keine Berechtigung zur Einreise (Auto-Rolle fehlt)."); return; }

        if (CharacterStore.exists(guild.getIdLong(), member.getIdLong())) {
            json(ctx, 200, false, "Dieser Nutzer ist bereits eingereist."); return;
        }

        JsonObject ok = new JsonObject();
        ok.addProperty("valid",       true);
        ok.addProperty("userId",      member.getId());
        ok.addProperty("displayName", member.getUser().getName());
        ctx.contentType("application/json").result(GSON.toJson(ok));
    }

    // ── /api/register/legal ────────────────────────────────────

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
        if (photo == null) { json(ctx, 400, "error", "Bitte lade ein Foto deines Charakters hoch."); return; }

        Guild  guild  = BotContext.getGuild();
        Member member = guild.getMemberById(userId);
        if (member == null) { json(ctx, 400, "error", "Nutzer nicht mehr auf dem Server."); return; }
        if (CharacterStore.exists(guild.getIdLong(), member.getIdLong())) {
            json(ctx, 400, "error", "Dieser Nutzer ist bereits eingereist."); return;
        }

        savePhoto(photo, userId);
        String ext = photoExt(photo);

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

        EconomyStore.addCoins(guild.getIdLong(), member.getIdLong(), RoleConfig.REGISTRATION_REWARD);
        applyRoles(guild, member, RoleConfig.LEGAL_ROLES);
        String nick = firstName.trim() + " " + lastName.trim() + " | " + psn.trim();
        guild.modifyNickname(member, nick).queue(null, err ->
            log.warn("[Meldeamt] Nickname nicht gesetzt für {}.", member.getUser().getName()));

        log.info("[Meldeamt] Legale Einreise: {} ({}).", member.getUser().getName(), userId);
        jsonOk(ctx);
    }

    // ── /api/register/illegal ──────────────────────────────────

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

        JsonObject character = new JsonObject();
        character.addProperty("type",            "illegal");
        character.addProperty("discordUsername", member.getUser().getName());
        character.addProperty("discordUserId",   userId);
        character.addProperty("psnName",         psn.trim());
        character.addProperty("firstName",       firstName.trim());
        character.addProperty("lastName",        lastName.trim());
        character.addProperty("registeredAt",    Instant.now().toString());
        CharacterStore.save(guild.getIdLong(), member.getIdLong(), character);

        EconomyStore.addCoins(guild.getIdLong(), member.getIdLong(), RoleConfig.REGISTRATION_REWARD);
        applyRoles(guild, member, RoleConfig.ILLEGAL_ROLES);
        String nick = firstName.trim() + " " + lastName.trim() + " | " + psn.trim();
        guild.modifyNickname(member, nick).queue(null, err ->
            log.warn("[Meldeamt] Nickname nicht gesetzt für {}.", member.getUser().getName()));

        log.info("[Meldeamt] Illegale Einreise: {} ({}).", member.getUser().getName(), userId);
        jsonOk(ctx);
    }

    // ── /api/register/group/legal ──────────────────────────────

    private static void handleGroupLegal(Context ctx) {
        if (!BotContext.isReady()) { json(ctx, 503, "error", "Bot noch nicht bereit."); return; }

        Guild guild = BotContext.getGuild();
        int count = 5;
        List<String> errors = new ArrayList<>();

        for (int i = 0; i < count; i++) {
            String userId    = ctx.formParam("userId_" + i);
            String psn       = ctx.formParam("psnName_" + i);
            String firstName = ctx.formParam("firstName_" + i);
            String lastName  = ctx.formParam("lastName_" + i);
            String birthDate = ctx.formParam("birthDate_" + i);
            String birthPlace= ctx.formParam("birthPlace_" + i);
            String national  = ctx.formParam("nationality_" + i);
            String residence = ctx.formParam("residence_" + i);
            UploadedFile photo = ctx.uploadedFile("photo_" + i);

            if (isBlank(userId, psn, firstName, lastName, birthDate, birthPlace, national, residence)) {
                errors.add("Person " + (i + 1) + ": Fehlende Pflichtfelder."); continue;
            }
            if (photo == null) {
                errors.add("Person " + (i + 1) + ": Kein Foto hochgeladen."); continue;
            }

            Member member = guild.getMemberById(userId);
            if (member == null) { errors.add("Person " + (i + 1) + ": Nicht mehr auf dem Server."); continue; }
            if (CharacterStore.exists(guild.getIdLong(), member.getIdLong())) {
                errors.add("Person " + (i + 1) + " (" + member.getUser().getName() + "): Bereits eingereist."); continue;
            }

            savePhoto(photo, userId);
            String ext = photoExt(photo);

            JsonObject ch = new JsonObject();
            ch.addProperty("type",            "legal");
            ch.addProperty("discordUsername", member.getUser().getName());
            ch.addProperty("discordUserId",   userId);
            ch.addProperty("psnName",         psn.trim());
            ch.addProperty("firstName",       firstName.trim());
            ch.addProperty("lastName",        lastName.trim());
            ch.addProperty("birthDate",       birthDate.trim());
            ch.addProperty("birthPlace",      birthPlace.trim());
            ch.addProperty("nationality",     national.trim());
            ch.addProperty("residence",       residence.trim());
            ch.addProperty("photoExt",        ext);
            ch.addProperty("registeredAt",    Instant.now().toString());
            CharacterStore.save(guild.getIdLong(), member.getIdLong(), ch);

            EconomyStore.addCoins(guild.getIdLong(), member.getIdLong(), RoleConfig.GROUP_REGISTRATION_REWARD);
            applyRoles(guild, member, RoleConfig.LEGAL_ROLES);
            String nick = firstName.trim() + " " + lastName.trim() + " | " + psn.trim();
            guild.modifyNickname(member, nick).queue(null, e ->
                log.warn("[Gruppe] Nickname nicht gesetzt für {}.", member.getUser().getName()));

            log.info("[Gruppe/Legal] Einreise: {} ({}).", member.getUser().getName(), userId);
        }

        if (!errors.isEmpty()) {
            JsonObject resp = new JsonObject();
            resp.addProperty("success", true);
            resp.addProperty("warnings", String.join("\n", errors));
            ctx.contentType("application/json").result(GSON.toJson(resp));
        } else {
            jsonOk(ctx);
        }
    }

    // ── /api/register/group/illegal ────────────────────────────

    private static void handleGroupIllegal(Context ctx) {
        if (!BotContext.isReady()) { json(ctx, 503, "error", "Bot noch nicht bereit."); return; }

        Guild guild = BotContext.getGuild();
        int count = 5;
        List<String> errors = new ArrayList<>();

        for (int i = 0; i < count; i++) {
            String userId    = ctx.formParam("userId_" + i);
            String psn       = ctx.formParam("psnName_" + i);
            String firstName = ctx.formParam("firstName_" + i);
            String lastName  = ctx.formParam("lastName_" + i);

            if (isBlank(userId, psn, firstName, lastName)) {
                errors.add("Person " + (i + 1) + ": Fehlende Pflichtfelder."); continue;
            }

            Member member = guild.getMemberById(userId);
            if (member == null) { errors.add("Person " + (i + 1) + ": Nicht mehr auf dem Server."); continue; }
            if (CharacterStore.exists(guild.getIdLong(), member.getIdLong())) {
                errors.add("Person " + (i + 1) + " (" + member.getUser().getName() + "): Bereits eingereist."); continue;
            }

            JsonObject ch = new JsonObject();
            ch.addProperty("type",            "illegal");
            ch.addProperty("discordUsername", member.getUser().getName());
            ch.addProperty("discordUserId",   userId);
            ch.addProperty("psnName",         psn.trim());
            ch.addProperty("firstName",       firstName.trim());
            ch.addProperty("lastName",        lastName.trim());
            ch.addProperty("registeredAt",    Instant.now().toString());
            CharacterStore.save(guild.getIdLong(), member.getIdLong(), ch);

            EconomyStore.addCoins(guild.getIdLong(), member.getIdLong(), RoleConfig.GROUP_REGISTRATION_REWARD);
            applyRoles(guild, member, RoleConfig.ILLEGAL_ROLES);
            String nick = firstName.trim() + " " + lastName.trim() + " | " + psn.trim();
            guild.modifyNickname(member, nick).queue(null, e ->
                log.warn("[Gruppe] Nickname nicht gesetzt für {}.", member.getUser().getName()));

            log.info("[Gruppe/Illegal] Einreise: {} ({}).", member.getUser().getName(), userId);
        }

        if (!errors.isEmpty()) {
            JsonObject resp = new JsonObject();
            resp.addProperty("success", true);
            resp.addProperty("warnings", String.join("\n", errors));
            ctx.contentType("application/json").result(GSON.toJson(resp));
        } else {
            jsonOk(ctx);
        }
    }

    // ── /api/photo/{userId} ────────────────────────────────────

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
                    ctx.status(500).result("Fehler.");
                    return;
                }
            }
        }
        ctx.status(404).result("Kein Foto.");
    }

    // ── /ausweis/{userId} ──────────────────────────────────────

    private static void serveAusweis(Context ctx) {
        String userIdStr = ctx.pathParam("userId");
        Guild guild = BotContext.getGuild();
        if (guild == null) { ctx.status(503).html("<h1>Bot nicht bereit.</h1>"); return; }
        long userId;
        try { userId = Long.parseLong(userIdStr); }
        catch (NumberFormatException e) { ctx.status(400).html("<h1>Ungültige ID.</h1>"); return; }
        JsonObject ch = CharacterStore.get(guild.getIdLong(), userId);
        if (ch == null) { ctx.status(404).html("<h1>Kein Charakter gefunden.</h1>"); return; }
        ctx.contentType("text/html;charset=utf-8").result(buildIdCard(ch, userIdStr));
    }

    private static String buildIdCard(JsonObject ch, String userId) {
        boolean isLegal = "legal".equals(CharacterStore.str(ch, "type"));
        String fn  = CharacterStore.str(ch, "firstName");
        String ln  = CharacterStore.str(ch, "lastName");
        String bd  = CharacterStore.str(ch, "birthDate");
        String bp  = CharacterStore.str(ch, "birthPlace");
        String na  = CharacterStore.str(ch, "nationality");
        String re  = CharacterStore.str(ch, "residence");
        String ps  = CharacterStore.str(ch, "psnName");
        String idNum = "LA-" + userId.substring(Math.max(0, userId.length() - 8)).toUpperCase();

        return "<!DOCTYPE html><html lang=\"de\"><head>" +
            "<meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">" +
            "<title>Ausweis – " + esc(fn) + " " + esc(ln) + "</title>" +
            "<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;" +
            "background:linear-gradient(135deg,#0a0a0a 0%,#0f0f1a 100%);font-family:'Courier New',monospace;}" +
            ".card{width:680px;background:linear-gradient(135deg,#0d2346 0%,#081830 100%);" +
            "border:3px solid #c8a048;border-radius:14px;overflow:hidden;box-shadow:0 0 40px rgba(200,160,72,0.3);}" +
            ".header{background:linear-gradient(90deg,#0a1c38,#0d2550);border-bottom:3px solid #c8a048;" +
            "padding:14px 20px;display:flex;align-items:center;gap:16px;}" +
            ".header .bear{font-size:2.4rem;}.header-text{flex:1;}" +
            ".header-text .state{display:block;color:#c8a048;font-size:1.3rem;font-weight:700;letter-spacing:4px;}" +
            ".header-text .city{display:block;color:#a8c4e0;font-size:0.75rem;letter-spacing:2px;margin-top:2px;}" +
            ".type-badge{background:" + (isLegal ? "#1a5c2a" : "#5c1a1a") + ";color:" +
            (isLegal ? "#4ef07a" : "#f04e4e") + ";padding:4px 12px;border-radius:4px;font-size:0.7rem;" +
            "font-weight:700;letter-spacing:2px;border:1px solid " + (isLegal ? "#4ef07a" : "#f04e4e") + ";}" +
            ".body{display:flex;}.photo-col{width:180px;min-height:240px;background:#06111f;display:flex;" +
            "align-items:center;justify-content:center;border-right:2px solid #c8a04840;padding:16px;flex-shrink:0;}" +
            ".photo-col img{width:148px;height:180px;object-fit:cover;border:2px solid #c8a048;border-radius:4px;}" +
            ".no-photo{width:148px;height:180px;display:flex;align-items:center;justify-content:center;" +
            "background:#0a1825;border:2px solid #c8a04860;border-radius:4px;color:#445;font-size:0.7rem;text-align:center;}" +
            ".data-col{flex:1;padding:20px;}.id-num{color:#c8a048;font-size:0.7rem;letter-spacing:2px;margin-bottom:14px;}" +
            ".field{margin-bottom:12px;}.field label{display:block;color:#6a8fb0;font-size:0.6rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:2px;}" +
            ".field .val{color:#e8e8e8;font-size:0.95rem;font-weight:700;letter-spacing:1px;}" +
            ".fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;}" +
            ".footer{background:#06111f;border-top:2px solid #c8a04840;padding:10px 20px;" +
            "display:flex;justify-content:space-between;align-items:center;}" +
            ".footer .seal{color:#c8a04880;font-size:0.65rem;letter-spacing:1px;}" +
            ".footer .psn{color:#4a9eff;font-size:0.7rem;}</style></head><body>" +
            "<div class=\"card\"><div class=\"header\"><span class=\"bear\">🐻</span>" +
            "<div class=\"header-text\"><span class=\"state\">CALIFORNIA</span>" +
            "<span class=\"city\">CITY OF LOS ANGELES · PARADISE CITY ROLEPLAY</span></div>" +
            "<span class=\"type-badge\">" + (isLegal ? "LEGAL" : "ILLEGAL") + "</span></div>" +
            "<div class=\"body\"><div class=\"photo-col\">" +
            (isLegal ? "<img src=\"/api/photo/" + userId + "\" onerror=\"this.parentNode.innerHTML='<div class=no-photo>Kein Foto</div>'\">"
                     : "<div class=\"no-photo\">KEIN<br>AUSWEIS</div>") +
            "</div><div class=\"data-col\"><div class=\"id-num\">ID-NR: " + esc(idNum) + "</div>" +
            "<div class=\"fields-grid\">" +
            field("Vorname", fn) + field("Nachname", ln) +
            (isLegal ? field("Geburtsdatum", bd) + field("Geburtsort", bp) + field("Nationalität", na) + field("Wohnort", re) : "") +
            "</div></div></div>" +
            "<div class=\"footer\"><span class=\"seal\">STATE OF CALIFORNIA · OFFICIAL IDENTIFICATION</span>" +
            "<span class=\"psn\">PSN: " + esc(ps) + "</span></div></div></body></html>";
    }

    // ── Hilfsmethoden ──────────────────────────────────────────

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

    private static void savePhoto(UploadedFile photo, String userId) {
        if (photo == null) return;
        String ext = photoExt(photo);
        Path p = DataStore.getPath("photos").resolve(userId + ext);
        try {
            Files.createDirectories(p.getParent());
            Files.copy(photo.content(), p, StandardCopyOption.REPLACE_EXISTING);
        } catch (Exception e) {
            log.error("[Meldeamt] Foto konnte nicht gespeichert werden für {}.", userId, e);
        }
    }

    private static String photoExt(UploadedFile photo) {
        String ct = photo.contentType() != null ? photo.contentType() : "image/jpeg";
        return ct.contains("png") ? ".png" : ".jpg";
    }

    private static String field(String label, String value) {
        return "<div class=\"field\"><label>" + esc(label) + "</label><div class=\"val\">" + esc(value) + "</div></div>";
    }

    private static String esc(String s) {
        if (s == null) return "";
        return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\"","&quot;");
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
