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

        // Lotto
        app.get("/lotto",                              WebServer::serveLotto);
        app.get("/lotto/{token}",                      WebServer::serveLottoToken);
        app.get("/api/lotto/status",                   WebServer::handleLottoStatus);
        app.post("/api/lotto/enroll/{token}",          WebServer::handleLottoEnrollToken);

        // Rubbellos
        app.get("/rubbellos",                          WebServer::serveRubbellosGeneral);
        app.get("/rubbellos/{token}",                  WebServer::serveRubbellos);
        app.post("/api/rubbellos/create",              WebServer::handleRubbellosCreate);
        app.post("/api/rubbellos/claim/{token}",       WebServer::handleRubbellosClai);

        // Lotto (kein Token — direktes Einlösen per userId)
        app.post("/api/lotto/enroll",                  WebServer::handleLottoEnrollDirect);

        // User-Resolve (Username → User-ID)
        app.post("/api/resolve-user",                  WebServer::handleResolveUser);

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

    // ── /lotto ────────────────────────────────────────────────────────────────

    private static void serveLotto(Context ctx) {
        ctx.contentType("text/html;charset=utf-8").result(buildLottoPage());
    }

    private static void handleResolveUser(Context ctx) {
        JsonObject r = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            r.addProperty("ok", false); r.addProperty("error", "Bot nicht bereit.");
            ctx.status(503).contentType("application/json").result(GSON.toJson(r)); return;
        }
        JsonObject body;
        try { body = GSON.fromJson(ctx.body(), JsonObject.class); }
        catch (Exception e) {
            r.addProperty("ok", false); r.addProperty("error", "Ungültige Anfrage.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String username = body != null && body.has("username") ? body.get("username").getAsString().trim() : "";
        if (username.isEmpty()) {
            r.addProperty("ok", false); r.addProperty("error", "Kein Benutzername angegeben.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        net.dv8tion.jda.api.entities.Member member = BotContext.findMemberByUsername(username);
        if (member == null) {
            r.addProperty("ok", false); r.addProperty("error", "Kein Mitglied mit dem Namen **" + esc(username) + "** gefunden.");
            ctx.contentType("application/json").result(GSON.toJson(r)); return;
        }
        r.addProperty("ok", true);
        r.addProperty("userId", member.getId());
        r.addProperty("displayName", member.getEffectiveName());
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    private static void handleLottoEnrollDirect(Context ctx) {
        JsonObject r = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            r.addProperty("ok", false); r.addProperty("error", "Bot nicht bereit.");
            ctx.status(503).contentType("application/json").result(GSON.toJson(r)); return;
        }
        JsonObject body;
        try { body = GSON.fromJson(ctx.body(), JsonObject.class); }
        catch (Exception e) {
            r.addProperty("ok", false); r.addProperty("error", "Ungültige Anfrage.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String userId = body != null && body.has("userId") ? body.get("userId").getAsString().trim() : "";
        if (userId.isEmpty()) {
            r.addProperty("ok", false); r.addProperty("error", "Keine Discord User-ID angegeben.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        try { Long.parseLong(userId); } catch (NumberFormatException e) {
            r.addProperty("ok", false); r.addProperty("error", "Ungültige Discord User-ID.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String error = LottoManager.enroll(guild.getId(), userId);
        if (error != null) {
            r.addProperty("ok", false); r.addProperty("error", error);
            ctx.contentType("application/json").result(GSON.toJson(r)); return;
        }
        int jackpot = LottoManager.getCurrentJackpot(guild.getId());
        r.addProperty("ok", true);
        r.addProperty("jackpotFmt", LottoManager.formatAmount(jackpot));
        r.addProperty("participants", LottoManager.getParticipantCount(guild.getId()));
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    private static void serveLottoToken(Context ctx) {
        String token = ctx.pathParam("token");
        String[] info = LottoManager.lookupToken(token);
        if (info == null) {
            ctx.status(410).contentType("text/html;charset=utf-8")
                .result(buildLottoExpiredPage());
            return;
        }
        ctx.contentType("text/html;charset=utf-8").result(buildLottoTokenPage(token));
    }

    private static void handleLottoEnrollToken(Context ctx) {
        String token = ctx.pathParam("token");
        JsonObject r = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            r.addProperty("ok", false); r.addProperty("error", "Bot nicht bereit.");
            ctx.status(503).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String[] info = LottoManager.lookupToken(token);
        if (info == null) {
            r.addProperty("ok", false); r.addProperty("error", "Dieser Link ist bereits abgelaufen oder wurde schon verwendet.");
            ctx.status(410).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String guildId = info[0];
        String userId  = info[1];
        // Token sofort ungültig machen (Einmalverwendung)
        LottoManager.deleteToken(token);
        String error = LottoManager.enroll(guildId, userId);
        if (error != null) {
            r.addProperty("ok", false); r.addProperty("error", error);
            ctx.contentType("application/json").result(GSON.toJson(r)); return;
        }
        int jackpot = LottoManager.getCurrentJackpot(guildId);
        r.addProperty("ok", true);
        r.addProperty("jackpotFmt", LottoManager.formatAmount(jackpot));
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    private static void handleLottoStatus(Context ctx) {
        Guild guild = BotContext.getGuild();
        JsonObject r = new JsonObject();
        if (guild == null) {
            r.addProperty("ok", false);
            ctx.status(503).contentType("application/json").result(GSON.toJson(r));
            return;
        }
        int jackpot      = LottoManager.getCurrentJackpot(guild.getId());
        int participants = LottoManager.getParticipantCount(guild.getId());
        r.addProperty("ok",           true);
        r.addProperty("jackpot",      jackpot);
        r.addProperty("jackpotFmt",   LottoManager.formatAmount(jackpot));
        r.addProperty("participants", participants);
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    private static String buildLottoPage() {
        String CSS =
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:linear-gradient(135deg,#0d0600,#1a0900);" +
            "font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;padding:20px}" +
            ".card{width:100%;max-width:480px;background:rgba(255,255,255,.04);border:1px solid #CC5500;" +
            "border-radius:16px;overflow:hidden;box-shadow:0 0 40px rgba(204,85,0,.25)}" +
            ".hdr{background:linear-gradient(90deg,#CC5500,#993300);padding:24px;text-align:center}" +
            ".hdr h1{color:#fff;font-size:2rem;letter-spacing:3px;text-shadow:0 2px 8px rgba(0,0,0,.5)}" +
            ".hdr p{color:#ffd0a0;font-size:.85rem;margin-top:4px;letter-spacing:1px}" +
            ".bdy{padding:28px}" +
            ".jp{text-align:center;margin-bottom:22px}" +
            ".jp .lbl{color:#aaa;font-size:.72rem;letter-spacing:2px;text-transform:uppercase}" +
            ".jp .amt{color:#FF8800;font-size:2.8rem;font-weight:700;margin-top:6px;text-shadow:0 0 20px rgba(255,136,0,.4)}" +
            ".jp .pts{color:#888;font-size:.85rem;margin-top:6px}" +
            "hr{border:none;border-top:1px solid #CC550030;margin:0 0 22px}" +
            ".step{display:none;flex-direction:column;gap:14px}" +
            ".step.on{display:flex}" +
            ".slbl{color:#888;font-size:.72rem;letter-spacing:2px;text-transform:uppercase;text-align:center}" +
            "input{width:100%;padding:12px 14px;background:#0d0600;border:1px solid #CC5500;" +
            "border-radius:8px;color:#fff;font-size:.95rem;outline:none}" +
            "input::placeholder{color:#444}" +
            "btn,button{display:block;width:100%;padding:14px;background:linear-gradient(90deg,#CC5500,#FF6600);" +
            "border:none;border-radius:8px;color:#fff;font-size:1rem;font-weight:700;" +
            "letter-spacing:1px;cursor:pointer;transition:opacity .2s;margin-top:2px}" +
            "button:hover{opacity:.88}button:disabled{opacity:.4;cursor:not-allowed}" +
            ".msg{margin-top:12px;padding:12px;border-radius:8px;font-size:.88rem;text-align:center;display:none}" +
            ".msg.ok{background:#1a3a0d;border:1px solid #4a9930;color:#7ddd55}" +
            ".msg.err{background:#3a0d0d;border:1px solid #993030;color:#dd5555}" +
            ".win{background:rgba(255,136,0,.07);border:1px solid #CC550060;border-radius:12px;padding:22px;text-align:center}" +
            ".win .ic{font-size:2.4rem;margin-bottom:10px}" +
            ".win h2{color:#FF8800;font-size:1.2rem;margin-bottom:8px}" +
            ".win p{color:#bbb;font-size:.88rem;line-height:1.65}" +
            ".win strong{color:#FF8800}" +
            ".foot{text-align:center;color:#555;font-size:.72rem;margin-top:18px}";

        return "<!DOCTYPE html><html lang='de'><head>" +
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>PCRP Lotto</title><style>" + CSS + "</style></head><body>" +
            "<div class='card'>" +
            "<div class='hdr'><h1>🎰 PCRP LOTTO</h1><p>Paradise City Roleplay</p></div>" +
            "<div class='bdy'>" +
            "<div class='jp'><div class='lbl'>Heutiger Jackpot</div>" +
            "<div class='amt' id='jp'>Lädt…</div><div class='pts' id='pts'></div></div>" +
            "<hr>" +
            // Step 1 — Benutzername
            "<div class='step on' id='s1'>" +
            "<div class='slbl'>Discord-Benutzername eingeben</div>" +
            "<input id='uname' type='text' placeholder='z. B. max_mustermann' maxlength='40'>" +
            "<button id='nbtn' onclick='goStep2()'>➡️ Weiter zum Lotto</button>" +
            "<div class='msg' id='m1'></div>" +
            "</div>" +
            // Step 2 — Einlösen
            "<div class='step' id='s2'>" +
            "<div class='slbl'>Lottoschein einlösen</div>" +
            "<div style='color:#888;font-size:.82rem;text-align:center;margin-bottom:4px'>Angemeldet als <strong id='wname' style='color:#FF8800'></strong></div>" +
            "<button id='ebtn' onclick='enroll()'>🎟️ Lottoschein abgeben</button>" +
            "<div class='msg' id='m2'></div>" +
            "</div>" +
            // Step 3 — Bestätigung
            "<div class='step' id='s3'>" +
            "<div class='win'><div class='ic'>🎉</div>" +
            "<h2>Du bist dabei!</h2>" +
            "<p>Dein Lottoschein wurde eingelöst.<br>Jackpot: <strong id='j3'></strong><br>" +
            "Die Ziehung findet heute um <strong>12:00 Uhr</strong> statt.<br>Viel Glück! 🍀</p>" +
            "</div></div>" +
            "<div class='foot'>Täglich um 12:00 Uhr • Jackpot: 100.000$ – 3.000.000$</div>" +
            "</div></div>" +
            "<script>" +
            "const KN='pcrp_uname';const KI='pcrp_uid';" +
            "let uname=localStorage.getItem(KN)||'';let uid=localStorage.getItem(KI)||'';" +
            "function show(id){['s1','s2','s3'].forEach(s=>document.getElementById(s).className='step'+(s==id?' on':''));}" +
            "function msg(id,t,c){const m=document.getElementById(id);m.textContent=t;m.className='msg '+c;m.style.display='block';}" +
            "async function loadJp(){try{const r=await fetch('/api/lotto/status');const d=await r.json();" +
            "if(d.ok){document.getElementById('jp').textContent=d.jackpotFmt;" +
            "document.getElementById('pts').textContent='🎟️ Teilnehmer: '+d.participants;" +
            "document.getElementById('j3').textContent=d.jackpotFmt;}}catch(e){}}" +
            "async function goStep2(){const v=document.getElementById('uname').value.trim();" +
            "if(!v){msg('m1','Bitte gib deinen Discord-Benutzernamen ein.','err');return;}" +
            "const btn=document.getElementById('nbtn');btn.disabled=true;" +
            "try{const r=await fetch('/api/resolve-user',{method:'POST'," +
            "headers:{'Content-Type':'application/json'},body:JSON.stringify({username:v})});" +
            "const d=await r.json();" +
            "if(!d.ok){msg('m1',d.error,'err');btn.disabled=false;return;}" +
            "localStorage.setItem(KN,v);localStorage.setItem(KI,d.userId);" +
            "uname=v;uid=d.userId;" +
            "document.getElementById('wname').textContent=d.displayName;" +
            "show('s2');}catch(e){msg('m1','Verbindungsfehler.','err');btn.disabled=false;}}" +
            "async function enroll(){const btn=document.getElementById('ebtn');btn.disabled=true;" +
            "try{const r=await fetch('/api/lotto/enroll',{method:'POST'," +
            "headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:uid})});" +
            "const d=await r.json();" +
            "if(d.ok){document.getElementById('j3').textContent=d.jackpotFmt;show('s3');loadJp();}" +
            "else{msg('m2',d.error,'err');btn.disabled=false;}}" +
            "catch(e){msg('m2','Verbindungsfehler. Bitte erneut versuchen.','err');btn.disabled=false;}}" +
            "loadJp();" +
            // Gespeicherten Namen vorausfüllen, aber immer Step 1 zeigen (userId neu auflösen)
            "if(uname){document.getElementById('uname').value=uname;}" +
            "</script></body></html>";
    }

    private static String buildLottoExpiredPage() {
        return "<!DOCTYPE html><html lang=\"de\"><head><meta charset=\"UTF-8\">" +
            "<title>PCRP Lotto</title>" +
            "<style>*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:linear-gradient(135deg,#0d0600,#1a0900);" +
            "font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;padding:20px}" +
            ".card{width:100%;max-width:420px;background:rgba(255,255,255,0.04);border:1px solid #CC5500;" +
            "border-radius:16px;padding:40px;text-align:center;box-shadow:0 0 40px rgba(204,85,0,0.2)}" +
            "h2{color:#FF8800;font-size:1.6rem;margin-bottom:16px}" +
            "p{color:#aaa;font-size:.9rem;line-height:1.6}</style></head><body>" +
            "<div class=\"card\"><h2>🔗 Link abgelaufen</h2>" +
            "<p>Dieser Link wurde bereits verwendet oder ist nicht mehr gültig.<br><br>" +
            "Klicke im Discord-Kanal erneut auf <strong>🎟️ Jetzt Mitspielen</strong>, um einen neuen Link zu erhalten.</p>" +
            "</div></body></html>";
    }

    private static String buildLottoTokenPage(String token) {
        return "<!DOCTYPE html><html lang=\"de\"><head>" +
            "<meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">" +
            "<title>PCRP Lotto</title><style>" +
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:linear-gradient(135deg,#0d0600 0%,#1a0900 100%);" +
            "font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;padding:20px}" +
            ".card{width:100%;max-width:480px;background:rgba(255,255,255,0.04);border:1px solid #CC5500;" +
            "border-radius:16px;overflow:hidden;box-shadow:0 0 40px rgba(204,85,0,0.25)}" +
            ".header{background:linear-gradient(90deg,#CC5500,#993300);padding:24px;text-align:center}" +
            ".header h1{color:#fff;font-size:2rem;letter-spacing:3px;text-shadow:0 2px 8px rgba(0,0,0,.5)}" +
            ".header p{color:#ffd0a0;font-size:.85rem;margin-top:4px;letter-spacing:1px}" +
            ".body{padding:28px}" +
            ".jackpot{text-align:center;margin-bottom:28px}" +
            ".jackpot .label{color:#aaa;font-size:.75rem;letter-spacing:2px;text-transform:uppercase}" +
            ".jackpot .amount{color:#FF8800;font-size:2.8rem;font-weight:700;margin-top:6px;" +
            "text-shadow:0 0 20px rgba(255,136,0,.4)}" +
            ".jackpot .participants{color:#888;font-size:.85rem;margin-top:8px}" +
            ".divider{border:none;border-top:1px solid #CC550030;margin:0 0 24px}" +
            ".info{color:#ccc;font-size:.88rem;text-align:center;margin-bottom:24px;line-height:1.7}" +
            ".info strong{color:#FF8800}" +
            "button{width:100%;padding:15px;background:linear-gradient(90deg,#CC5500,#FF6600);" +
            "border:none;border-radius:10px;color:#fff;font-size:1.05rem;font-weight:700;" +
            "letter-spacing:1px;cursor:pointer;transition:opacity .2s}" +
            "button:hover{opacity:.88}button:disabled{opacity:.4;cursor:not-allowed}" +
            ".msg{margin-top:18px;padding:14px;border-radius:8px;font-size:.9rem;text-align:center;display:none}" +
            ".msg.ok{background:#1a3a0d;border:1px solid #4a9930;color:#7ddd55}" +
            ".msg.err{background:#3a0d0d;border:1px solid #993030;color:#dd5555}" +
            ".draw-info{text-align:center;color:#555;font-size:.75rem;margin-top:20px}" +
            "</style></head><body>" +
            "<div class=\"card\">" +
            "<div class=\"header\"><h1>🎰 PCRP LOTTO</h1><p>Paradise City Roleplay</p></div>" +
            "<div class=\"body\">" +
            "<div class=\"jackpot\">" +
            "<div class=\"label\">Heutiger Jackpot</div>" +
            "<div class=\"amount\" id=\"jackpot\">Lädt…</div>" +
            "<div class=\"participants\" id=\"participants\"></div>" +
            "</div>" +
            "<hr class=\"divider\">" +
            "<div class=\"info\">Klicke auf den Button, um deinen <strong>Lottoschein</strong> abzugeben.<br>" +
            "Die Ziehung findet täglich um <strong>12:00 Uhr</strong> statt.</div>" +
            "<button id=\"btn\" onclick=\"enroll()\">🎟️ Lottoschein abgeben</button>" +
            "<div class=\"msg\" id=\"msg\"></div>" +
            "<div class=\"draw-info\">Täglich um 12:00 Uhr • Jackpot: 100.000$ – 3.000.000$</div>" +
            "</div></div>" +
            "<script>" +
            "const TOKEN='" + token + "';" +
            "async function loadStatus(){" +
            "try{const r=await fetch('/api/lotto/status');const d=await r.json();" +
            "if(d.ok){document.getElementById('jackpot').textContent=d.jackpotFmt;" +
            "document.getElementById('participants').textContent='🎟️ Teilnehmer: '+d.participants;}}" +
            "catch(e){}}" +
            "async function enroll(){" +
            "const btn=document.getElementById('btn');" +
            "btn.disabled=true;" +
            "try{const r=await fetch('/api/lotto/enroll/'+TOKEN,{method:'POST'});" +
            "const d=await r.json();" +
            "if(d.ok){showMsg('✅ Du nimmst an der heutigen Ziehung teil! Jackpot: '+d.jackpotFmt+' – Viel Glück! 🍀','ok');loadStatus();}" +
            "else{showMsg(d.error,'err');btn.disabled=false;}}" +
            "catch(e){showMsg('Verbindungsfehler. Bitte versuche es erneut.','err');btn.disabled=false;}}" +
            "function showMsg(t,cls){const m=document.getElementById('msg');" +
            "m.textContent=t;m.className='msg '+cls;m.style.display='block';}" +
            "loadStatus();" +
            "</script></body></html>";
    }

    // ── /rubbellos (allgemeine Seite) ─────────────────────────────────────────

    private static void serveRubbellosGeneral(Context ctx) {
        ctx.contentType("text/html;charset=utf-8").result(buildRubbellosGeneralPage());
    }

    private static String buildRubbellosGeneralPage() {
        String CSS =
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:radial-gradient(ellipse at top,#1a1200,#0a0800);" +
            "font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;padding:20px}" +
            ".card{width:100%;max-width:400px;background:#111005;border:3px solid #b8860b;" +
            "border-radius:18px;overflow:hidden;box-shadow:0 0 60px rgba(184,134,11,.35)}" +
            ".top{background:linear-gradient(90deg,#8b6914,#ffd700,#8b6914);padding:20px;text-align:center}" +
            ".top h1{font-size:1.5rem;letter-spacing:4px;color:#1a1000;font-weight:900}" +
            ".top p{font-size:.7rem;letter-spacing:3px;color:#3a2800;margin-top:2px}" +
            ".bdy{padding:26px;display:flex;flex-direction:column;gap:16px}" +
            ".slbl{color:#b8860b88;font-size:.72rem;letter-spacing:2px;text-transform:uppercase;text-align:center}" +
            "input{width:100%;padding:12px 14px;background:#0a0800;border:2px solid #b8860b44;" +
            "border-radius:8px;color:#fff;font-size:.95rem;outline:none}" +
            "input:focus{border-color:#ffd700}input::placeholder{color:#444}" +
            "button{width:100%;padding:14px;background:linear-gradient(90deg,#8b6914,#ffd700,#8b6914);" +
            "border:none;border-radius:8px;color:#1a1000;font-size:1rem;font-weight:900;" +
            "letter-spacing:1px;cursor:pointer;transition:opacity .2s}" +
            "button:hover{opacity:.88}button:disabled{opacity:.4;cursor:not-allowed}" +
            ".msg{padding:12px;border-radius:8px;font-size:.88rem;text-align:center;display:none}" +
            ".msg.err{background:#2a0d0d;border:1px solid #993030;color:#dd5555}" +
            ".los{display:none;flex-direction:column;gap:12px}" +
            ".los.on{display:flex}" +
            ".cells{display:flex;gap:10px;justify-content:center}" +
            ".cw{position:relative;width:90px;height:90px}" +
            "canvas{position:absolute;top:0;left:0;border-radius:10px;cursor:crosshair;touch-action:none}" +
            ".cv{width:90px;height:90px;border-radius:10px;background:linear-gradient(135deg,#2a2000,#1a1500);" +
            "border:2px solid #b8860b44;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px}" +
            ".cv .sym{font-size:1.5rem}.cv .amt{color:#ffd700;font-size:.78rem;font-weight:700}" +
            ".hint{text-align:center;color:#b8860b66;font-size:.7rem;letter-spacing:1px}" +
            ".res{padding:18px;border-radius:12px;text-align:center;display:none}" +
            ".res.win{background:#1a2a00;border:1px solid #4a9930}" +
            ".res.lose{background:#1a1000;border:1px solid #b8860b33}" +
            ".res h2{font-size:1.3rem;margin-bottom:8px}" +
            ".res.win h2{color:#7ddd55}.res.lose h2{color:#b8860b}" +
            ".res p{color:#aaa;font-size:.85rem;line-height:1.6}" +
            ".foot{text-align:center;color:#b8860b44;font-size:.65rem;letter-spacing:1px;padding:0 0 10px}";

        return "<!DOCTYPE html><html lang='de'><head>" +
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>Goldene 7 – PCRP Rubbellos</title><style>" + CSS + "</style></head><body>" +
            "<div class='card'>" +
            "<div class='top'><h1>⭐ GOLDENE 7 ⭐</h1><p>PARADISE CITY ROLEPLAY</p></div>" +
            "<div class='bdy' id='bdy'>" +
            // Step 1 — ID
            "<div class='slbl' id='idlbl'>Discord-Benutzername</div>" +
            "<input id='uid' type='text' placeholder='z. B. max_mustermann' maxlength='40'>" +
            "<button id='sbtn' onclick='goScratch()'>🎰 Rubbellos einlösen</button>" +
            "<div class='msg err' id='emsg'></div>" +
            // Scratch-Karte (nach Einlösen eingeblendet)
            "<div class='los' id='los'>" +
            "<div class='slbl'>Rubbele alle 3 Felder frei!</div>" +
            "<div class='cells'>" +
            "<div class='cw'><div class='cv'><span class='sym'>🍀</span><span class='amt' id='v0'></span></div>" +
            "<canvas id='c0' width='90' height='90'></canvas></div>" +
            "<div class='cw'><div class='cv'><span class='sym'>⭐</span><span class='amt' id='v1'></span></div>" +
            "<canvas id='c1' width='90' height='90'></canvas></div>" +
            "<div class='cw'><div class='cv'><span class='sym'>💎</span><span class='amt' id='v2'></span></div>" +
            "<canvas id='c2' width='90' height='90'></canvas></div>" +
            "</div>" +
            "<div class='hint'>gedrückt halten und rubbeln</div>" +
            "<div class='res' id='res'><h2 id='rt'></h2><p id='rd'></p></div>" +
            "</div>" +
            "</div>" +
            "<div class='foot'>GOLDENE 7 • PCRP • GEWINN BIS 30.000$</div>" +
            "</div>" +
            "<script>" +
            "const KN='pcrp_uname';const KI='pcrp_uid';" +
            "let uname=localStorage.getItem(KN)||'';let uid=localStorage.getItem(KI)||'';" +
            "let claimToken=null;let claimed=false;const rev=[false,false,false];" +
            "if(uname)document.getElementById('uid').value=uname;" +
            "function err(t){const m=document.getElementById('emsg');m.textContent=t;m.style.display='block';}" +
            "async function goScratch(){" +
            "const v=document.getElementById('uid').value.trim();" +
            "if(!v){err('Bitte gib deinen Discord-Benutzernamen ein.');return;}" +
            "const btn=document.getElementById('sbtn');btn.disabled=true;" +
            "document.getElementById('emsg').style.display='none';" +
            "try{" +
            // Step 1: Resolve username → userId
            "const rr=await fetch('/api/resolve-user',{method:'POST'," +
            "headers:{'Content-Type':'application/json'},body:JSON.stringify({username:v})});" +
            "const dd=await rr.json();" +
            "if(!dd.ok){err(dd.error);btn.disabled=false;return;}" +
            "localStorage.setItem(KN,v);localStorage.setItem(KI,dd.userId);uname=v;uid=dd.userId;" +
            // Step 2: Create scratch session
            "const r=await fetch('/api/rubbellos/create',{method:'POST'," +
            "headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:uid})});" +
            "const d=await r.json();" +
            "if(!d.ok){err(d.error);btn.disabled=false;return;}" +
            "claimToken=d.token;" +
            "document.getElementById('v0').textContent=d.c0;" +
            "document.getElementById('v1').textContent=d.c1;" +
            "document.getElementById('v2').textContent=d.c2;" +
            "document.getElementById('idlbl').style.display='none';" +
            "document.getElementById('uid').style.display='none';" +
            "document.getElementById('sbtn').style.display='none';" +
            "document.getElementById('emsg').style.display='none';" +
            "document.getElementById('los').className='los on';" +
            "setupCards();" +
            "}catch(e){err('Verbindungsfehler. Bitte erneut versuchen.');btn.disabled=false;}}" +
            "function setupCards(){[0,1,2].forEach(i=>setup(i));}" +
            "function setup(i){const cv=document.getElementById('c'+i);" +
            "const cx=cv.getContext('2d');" +
            "cx.fillStyle='#c8a000';cx.beginPath();cx.roundRect(0,0,90,90,10);cx.fill();" +
            "cx.fillStyle='#8b6914';" +
            "for(let j=0;j<6;j++)cx.fillRect(8+j*14,36,10,14);" +
            "cx.fillStyle='#1a1000';cx.font='bold 11px Segoe UI';cx.textAlign='center';" +
            "cx.fillText('RUBBELN',45,22);cx.fillText('7',45,62);" +
            "let drag=false;" +
            "function sc(x,y){cx.globalCompositeOperation='destination-out';" +
            "cx.beginPath();cx.arc(x,y,18,0,Math.PI*2);cx.fill();check(cx,cv,i);}" +
            "cv.addEventListener('mousedown',e=>{drag=true;sc(e.offsetX,e.offsetY);});" +
            "cv.addEventListener('mousemove',e=>{if(drag)sc(e.offsetX,e.offsetY);});" +
            "cv.addEventListener('mouseup',()=>drag=false);" +
            "cv.addEventListener('mouseleave',()=>drag=false);" +
            "cv.addEventListener('touchstart',e=>{e.preventDefault();const t=e.touches[0];" +
            "const b=cv.getBoundingClientRect();sc(t.clientX-b.left,t.clientY-b.top);},{passive:false});" +
            "cv.addEventListener('touchmove',e=>{e.preventDefault();const t=e.touches[0];" +
            "const b=cv.getBoundingClientRect();sc(t.clientX-b.left,t.clientY-b.top);},{passive:false});}" +
            "function check(cx,cv,i){if(rev[i])return;" +
            "const d=cx.getImageData(0,0,90,90).data;let t=0,c=0;" +
            "for(let j=3;j<d.length;j+=4){t++;if(d[j]<128)c++;}" +
            "if(c/t>.6){rev[i]=true;cv.style.display='none';checkAll();}}" +
            "function checkAll(){if(rev[0]&&rev[1]&&rev[2]&&!claimed){claimed=true;claim();}}" +
            "async function claim(){try{const r=await fetch('/api/rubbellos/claim/'+claimToken,{method:'POST'});" +
            "const d=await r.json();const res=document.getElementById('res');" +
            "if(d.prize>0){res.className='res win';document.getElementById('rt').textContent='🎉 Gewonnen!';" +
            "document.getElementById('rd').textContent='Du hast '+d.prizeFmt+' gewonnen! Der Gewinn wurde sofort auf dein Bankkonto gutgeschrieben.';}" +
            "else{res.className='res lose';document.getElementById('rt').textContent='😔 Niete';" +
            "document.getElementById('rd').textContent='Kein Gewinn dieses Mal – beim nächsten Mal klappts!';}" +
            "res.style.display='block';}catch(e){}}" +
            "</script></body></html>";
    }

    private static void handleRubbellosCreate(Context ctx) {
        JsonObject r = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            r.addProperty("ok", false); r.addProperty("error", "Bot nicht bereit.");
            ctx.status(503).contentType("application/json").result(GSON.toJson(r)); return;
        }
        JsonObject body;
        try { body = GSON.fromJson(ctx.body(), JsonObject.class); }
        catch (Exception e) {
            r.addProperty("ok", false); r.addProperty("error", "Ungültige Anfrage.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String userId = body != null && body.has("userId") ? body.get("userId").getAsString().trim() : "";
        if (userId.isEmpty()) {
            r.addProperty("ok", false); r.addProperty("error", "Keine Discord User-ID angegeben.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        try { Long.parseLong(userId); } catch (NumberFormatException e) {
            r.addProperty("ok", false); r.addProperty("error", "Ungültige Discord User-ID.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        boolean hasTicket = InventoryManager.getInventory(guild.getId(), userId)
            .stream().anyMatch(it -> "Rubbellos".equalsIgnoreCase(it.name));
        if (!hasTicket) {
            r.addProperty("ok", false); r.addProperty("error", "Du hast kein Rubbellos in deinem Rucksack.");
            ctx.contentType("application/json").result(GSON.toJson(r)); return;
        }
        boolean removed = InventoryManager.removeItem(guild.getId(), userId, "Rubbellos", 1);
        if (!removed) {
            r.addProperty("ok", false); r.addProperty("error", "Rubbellos konnte nicht eingelöst werden. Bitte erneut versuchen.");
            ctx.contentType("application/json").result(GSON.toJson(r)); return;
        }
        int prize = RubbellosManager.rollPrize();
        String token = RubbellosManager.createToken(guild.getId(), userId, prize);
        int[] cells = RubbellosManager.buildCells(prize);
        r.addProperty("ok", true);
        r.addProperty("token", token);
        r.addProperty("c0", fmtCell(cells[0]));
        r.addProperty("c1", fmtCell(cells[1]));
        r.addProperty("c2", fmtCell(cells[2]));
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    // ── /rubbellos/{token} ────────────────────────────────────────────────────

    private static void serveRubbellos(Context ctx) {
        String token = ctx.pathParam("token");
        String[] info = RubbellosManager.lookupToken(token);
        if (info == null) {
            ctx.status(410).contentType("text/html;charset=utf-8")
                .result(buildRubbellosExpiredPage());
            return;
        }
        int prize = 0;
        try { prize = Integer.parseInt(info[2]); } catch (Exception ignored) {}
        int[] cells = RubbellosManager.buildCells(prize);
        ctx.contentType("text/html;charset=utf-8").result(buildRubbellosPage(token, cells, prize));
    }

    private static void handleRubbellosClai(Context ctx) {
        String token = ctx.pathParam("token");
        JsonObject r = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            r.addProperty("ok", false); r.addProperty("error", "Bot nicht bereit.");
            ctx.status(503).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String[] info = RubbellosManager.lookupToken(token);
        if (info == null) {
            r.addProperty("ok", false); r.addProperty("error", "Token bereits verwendet.");
            ctx.status(410).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String guildId = info[0];
        String userId  = info[1];
        int prize = 0;
        try { prize = Integer.parseInt(info[2]); } catch (Exception ignored) {}
        RubbellosManager.deleteToken(token);
        if (prize > 0) {
            long newBal = BankManager.getBalance(guildId, userId) + prize;
            BankManager.setBalance(guildId, userId, newBal);
            BankManager.addTransaction(guildId, userId, "RUBBELLOS_GEWINN", prize, null);
        }
        r.addProperty("ok", true);
        r.addProperty("prize", prize);
        r.addProperty("prizeFmt", RubbellosManager.formatAmount(prize));
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    private static String buildRubbellosExpiredPage() {
        return "<!DOCTYPE html><html lang=\"de\"><head><meta charset=\"UTF-8\">" +
            "<title>PCRP Rubbellos</title>" +
            "<style>*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:#0a0800;font-family:'Segoe UI',sans-serif;" +
            "display:flex;align-items:center;justify-content:center;padding:20px}" +
            ".card{width:100%;max-width:420px;background:#111005;border:2px solid #b8860b;" +
            "border-radius:16px;padding:40px;text-align:center;box-shadow:0 0 40px rgba(184,134,11,0.25)}" +
            "h2{color:#ffd700;font-size:1.6rem;margin-bottom:16px}" +
            "p{color:#aaa;font-size:.9rem;line-height:1.6}</style></head><body>" +
            "<div class=\"card\"><h2>🎰 Los bereits verwendet</h2>" +
            "<p>Dieses Rubbellos wurde bereits eingelöst oder der Link ist nicht mehr gültig.<br><br>" +
            "Klicke im Discord-Kanal erneut auf <strong>🎰 Rubbellos einlösen</strong>, um ein neues Los zu öffnen.</p>" +
            "</div></body></html>";
    }

    private static String buildRubbellosPage(String token, int[] cells, int prize) {
        String c0 = fmtCell(cells[0]);
        String c1 = fmtCell(cells[1]);
        String c2 = fmtCell(cells[2]);
        // embed prize values as dollar amounts for the cell labels
        String cv0 = (cells[0] == 0) ? "Niete" : (String.format("%,d", cells[0]).replace(',', '.') + "$");
        String cv1 = (cells[1] == 0) ? "Niete" : (String.format("%,d", cells[1]).replace(',', '.') + "$");
        String cv2 = (cells[2] == 0) ? "Niete" : (String.format("%,d", cells[2]).replace(',', '.') + "$");
        String prizeJs = String.valueOf(prize);
        boolean isWin = prize > 0;

        return "<!DOCTYPE html><html lang='de'><head>" +
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>Goldene 7 – PCRP Rubbellos</title>" +
            "<style>" +
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:radial-gradient(ellipse at center,#1a0f00,#0a0700);" +
            "font-family:'Arial Black','Arial',sans-serif;display:flex;align-items:center;" +
            "justify-content:center;padding:16px;overflow-x:hidden}" +
            "#pcanvas{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:999}" +
            ".ticket{width:100%;max-width:340px;border-radius:14px;overflow:hidden;" +
            "box-shadow:0 0 80px rgba(255,200,0,.3),0 20px 60px rgba(0,0,0,.8);" +
            "border:3px solid #b8860b;position:relative}" +
            /* top section – yellow gradient like the real ticket */
            ".tk-top{background:linear-gradient(135deg,#ffe000 0%,#ffa500 40%,#ffcc00 70%,#ff8c00 100%);" +
            "padding:10px 12px 8px;display:flex;align-items:flex-start;justify-content:space-between;" +
            "border-bottom:3px solid #8b5e00}" +
            ".tk-top-left{display:flex;flex-direction:column}" +
            ".tk-win-lbl{font-size:.55rem;font-weight:900;color:#3a1800;letter-spacing:2px;text-transform:uppercase}" +
            ".tk-win-amt{font-size:1.8rem;font-weight:900;color:#1a0800;line-height:1;" +
            "text-shadow:1px 1px 0 #fff9a0,-1px -1px 0 #8b5e00}" +
            ".tk-bars{display:flex;flex-direction:column;gap:3px;margin-top:2px}" +
            ".bar{width:48px;height:13px;border-radius:3px;border:1px solid #6b3e00;" +
            "background:linear-gradient(180deg,#fff8b0 0%,#e8a000 30%,#c07000 60%,#8b5000 100%);" +
            "box-shadow:0 1px 3px rgba(0,0,0,.4)}" +
            /* middle – main branding area */
            ".tk-mid{background:linear-gradient(135deg,#ffd000 0%,#ffb800 50%,#ff9500 100%);" +
            "display:flex;justify-content:space-between;align-items:center;padding:0 12px 0 14px}" +
            ".tk-brand{display:flex;flex-direction:column;justify-content:center;padding:4px 0}" +
            ".tk-goldene{font-size:1.8rem;font-weight:900;color:#1a0800;font-style:italic;line-height:1;" +
            "text-shadow:2px 2px 0 #8b5000,-1px -1px 0 #fff8a0;letter-spacing:3px}" +
            ".tk-seven{font-size:5.5rem;font-weight:900;color:#1a0800;font-style:italic;line-height:.9;" +
            "text-shadow:4px 4px 0 #6b3e00,2px 2px 0 #c07000,-2px -2px 0 #fff8a0}" +
            ".tk-bars-right{display:flex;flex-direction:column;gap:3px;align-self:stretch;justify-content:center}" +
            /* scratch section – dark background */
            ".tk-scratch{background:#1a1200;padding:10px 12px 8px;border-top:3px solid #8b5e00}" +
            ".scratch-lbl{text-align:center;color:#ffd700;font-size:.62rem;letter-spacing:3px;" +
            "text-transform:uppercase;margin-bottom:8px}" +
            ".cells-row{display:flex;gap:8px;justify-content:center}" +
            ".cell-wrap{position:relative;flex:1;max-width:96px}" +
            ".cell-back{width:100%;aspect-ratio:1;border-radius:8px;" +
            "background:linear-gradient(135deg,#2a1f00,#1a1400);" +
            "border:2px solid #b8860b55;" +
            "display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px}" +
            ".cell-back .c-sym{font-size:1.5rem;line-height:1}" +
            ".cell-back .c-amt{color:#ffd700;font-size:.82rem;font-weight:900;letter-spacing:.5px}" +
            "canvas.sc{position:absolute;top:0;left:0;width:100%;height:100%;border-radius:8px;" +
            "cursor:crosshair;touch-action:none}" +
            ".tk-info{background:#110d00;padding:8px 12px;" +
            "border-top:1px solid #b8860b33}" +
            ".tk-info-text{color:#b8860b99;font-size:.58rem;line-height:1.5;font-family:'Segoe UI',sans-serif}" +
            ".tk-chances{color:#b8860b;font-size:.65rem;font-weight:700;letter-spacing:2px;margin-top:4px}" +
            ".tk-result{margin:0;padding:14px 12px;text-align:center;display:none}" +
            ".tk-result.win{background:#0f1f05;border-top:2px solid #4a9930}" +
            ".tk-result.lose{background:#110d00;border-top:1px solid #b8860b33}" +
            ".tk-result h2{font-size:1.3rem;font-weight:900;margin-bottom:6px}" +
            ".tk-result.win h2{color:#7ddd55}" +
            ".tk-result.lose h2{color:#b8860b}" +
            ".tk-result p{color:#aaa;font-size:.8rem;line-height:1.6;font-family:'Segoe UI',sans-serif}" +
            ".tk-result .prize-big{color:#FFD700;font-size:1.6rem;font-weight:900;display:block;margin:6px 0}" +
            "@keyframes shine{0%{background-position:-200% center}100%{background-position:200% center}}" +
            ".shining{background:linear-gradient(90deg,#ffd700,#fff8a0,#ffa500,#ffd700);" +
            "background-size:200% auto;animation:shine 1.5s linear infinite;" +
            "-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}" +
            "</style></head><body>" +
            "<canvas id='pcanvas'></canvas>" +
            "<div class='ticket'>" +
            /* TOP */
            "<div class='tk-top'>" +
            "<div class='tk-top-left'>" +
            "<span class='tk-win-lbl'>Gewinne bis zu</span>" +
            "<span class='tk-win-amt'>30.000$</span>" +
            "</div>" +
            "<div class='tk-bars'><div class='bar'></div><div class='bar'></div><div class='bar'></div>" +
            "<div class='bar'></div><div class='bar'></div><div class='bar'></div></div>" +
            "</div>" +
            /* MID */
            "<div class='tk-mid'>" +
            "<div class='tk-brand'><div class='tk-goldene'>GOLDENE</div><div class='tk-seven'>7</div></div>" +
            "<div class='tk-bars-right'><div class='bar'></div><div class='bar'></div><div class='bar'></div>" +
            "<div class='bar'></div><div class='bar'></div><div class='bar'></div></div>" +
            "</div>" +
            /* SCRATCH */
            "<div class='tk-scratch'>" +
            "<div class='scratch-lbl'>↓ Alle 3 Felder freirubbeln ↓</div>" +
            "<div class='cells-row'>" +
            "<div class='cell-wrap'><div class='cell-back'>" +
            "<span class='c-sym'>7️⃣</span><span class='c-amt' id='v0'>" + cv0 + "</span></div>" +
            "<canvas class='sc' id='c0'></canvas></div>" +
            "<div class='cell-wrap'><div class='cell-back'>" +
            "<span class='c-sym'>7️⃣</span><span class='c-amt' id='v1'>" + cv1 + "</span></div>" +
            "<canvas class='sc' id='c1'></canvas></div>" +
            "<div class='cell-wrap'><div class='cell-back'>" +
            "<span class='c-sym'>7️⃣</span><span class='c-amt' id='v2'>" + cv2 + "</span></div>" +
            "<canvas class='sc' id='c2'></canvas></div>" +
            "</div>" +
            "</div>" +
            /* INFO */
            "<div class='tk-info'>" +
            "<div class='tk-info-text'>Finde eine <b style='color:#ffd700'>7</b> und gewinne den neben-" +
            "stehenden Betrag. Bei allen drei Feldern gleich hast du gewonnen!</div>" +
            "<div class='tk-chances'>10 GEWINNCHANCEN</div>" +
            "</div>" +
            /* RESULT */
            "<div class='tk-result' id='result'>" +
            "<h2 id='rtitle'></h2>" +
            "<span class='prize-big' id='ramt'></span>" +
            "<p id='rdesc'></p>" +
            "</div>" +
            "</div>" +
            "<script>" +
            "const TOKEN='" + token + "';" +
            "const PRIZE=" + prizeJs + ";" +
            "const rev=[false,false,false];" +
            "let claimed=false;" +
            /* ── Particle system ── */
            "const pc=document.getElementById('pcanvas');" +
            "const px=pc.getContext('2d');" +
            "let particles=[];" +
            "function resizePC(){pc.width=window.innerWidth;pc.height=window.innerHeight;}" +
            "resizePC();window.addEventListener('resize',resizePC);" +
            "const COLORS=['#FFD700','#FFA500','#FFEC00','#FFB800','#FFF0A0','#FF8C00'];" +
            "function spawnParticles(cx,cy,count){" +
            "for(let i=0;i<count;i++){" +
            "const angle=Math.random()*Math.PI*2;" +
            "const speed=Math.random()*3+1;" +
            "particles.push({x:cx,y:cy," +
            "vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed-2," +
            "life:1,size:Math.random()*4+2," +
            "color:COLORS[Math.floor(Math.random()*COLORS.length)]});}}" +
            "function burstParticles(cx,cy){" +
            "for(let i=0;i<80;i++){" +
            "const angle=Math.random()*Math.PI*2;" +
            "const speed=Math.random()*8+2;" +
            "particles.push({x:cx,y:cy," +
            "vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed-3," +
            "life:1,size:Math.random()*6+3," +
            "color:COLORS[Math.floor(Math.random()*COLORS.length)]});}}" +
            "function animateParticles(){" +
            "px.clearRect(0,0,pc.width,pc.height);" +
            "particles=particles.filter(p=>{" +
            "p.x+=p.vx;p.y+=p.vy;p.vy+=0.15;p.life-=0.018;" +
            "if(p.life<=0)return false;" +
            "px.globalAlpha=p.life;" +
            "px.fillStyle=p.color;" +
            "px.beginPath();px.arc(p.x,p.y,p.size,0,Math.PI*2);px.fill();" +
            "return true;});" +
            "px.globalAlpha=1;" +
            "requestAnimationFrame(animateParticles);}" +
            "animateParticles();" +
            /* ── Canvas setup ── */
            "function setupCanvas(id,idx){" +
            "const cv=document.getElementById(id);" +
            "const wrap=cv.parentElement;" +
            "const W=wrap.clientWidth||96,H=W;" +
            "cv.width=W;cv.height=H;" +
            "const ctx=cv.getContext('2d');" +
            /* gold gradient cover */
            "const grd=ctx.createLinearGradient(0,0,W,H);" +
            "grd.addColorStop(0,'#ffd000');" +
            "grd.addColorStop(0.4,'#ffb800');" +
            "grd.addColorStop(0.7,'#e89000');" +
            "grd.addColorStop(1,'#c07000');" +
            "ctx.fillStyle=grd;" +
            "ctx.beginPath();ctx.roundRect(0,0,W,H,8);ctx.fill();" +
            /* texture stripes */
            "ctx.fillStyle='rgba(0,0,0,0.08)';" +
            "for(let i=0;i<6;i++)ctx.fillRect(10+i*(W/7),H*0.35,W/9,H*0.2);" +
            /* text */
            "ctx.fillStyle='#1a0800';ctx.font='bold '+(W*0.13)+'px Arial Black,Arial';" +
            "ctx.textAlign='center';ctx.textBaseline='middle';" +
            "ctx.fillText('RUBBELN',W/2,H*0.28);" +
            "ctx.font='bold '+(W*0.35)+'px Arial Black,Arial';" +
            "ctx.fillStyle='#3a1800';" +
            "ctx.fillText('7',W/2,H*0.62);" +
            /* scratch shimmer dots */
            "ctx.fillStyle='rgba(255,255,200,0.3)';" +
            "for(let i=0;i<12;i++){" +
            "ctx.beginPath();" +
            "ctx.arc(Math.random()*W,Math.random()*H,Math.random()*2+1,0,Math.PI*2);" +
            "ctx.fill();}" +
            "let dragging=false;" +
            "function getPos(e,touch){" +
            "const r=cv.getBoundingClientRect();" +
            "const scaleX=cv.width/r.width,scaleY=cv.height/r.height;" +
            "if(touch){return{x:(touch.clientX-r.left)*scaleX,y:(touch.clientY-r.top)*scaleY};}" +
            "return{x:e.offsetX*scaleX,y:e.offsetY*scaleY};}" +
            "function scratch(p){" +
            "ctx.globalCompositeOperation='destination-out';" +
            "ctx.beginPath();ctx.arc(p.x,p.y,W*0.22,0,Math.PI*2);ctx.fill();" +
            "ctx.globalCompositeOperation='source-over';" +
            /* spawn particles at screen coords */
            "const r=cv.getBoundingClientRect();" +
            "const sx=r.left+p.x*(r.width/cv.width);" +
            "const sy=r.top+p.y*(r.height/cv.height);" +
            "spawnParticles(sx,sy,5);" +
            "checkReveal(ctx,cv,idx,W,H);}" +
            "cv.addEventListener('mousedown',e=>{dragging=true;scratch(getPos(e,null));});" +
            "cv.addEventListener('mousemove',e=>{if(dragging)scratch(getPos(e,null));});" +
            "cv.addEventListener('mouseup',()=>dragging=false);" +
            "cv.addEventListener('mouseleave',()=>dragging=false);" +
            "cv.addEventListener('touchstart',e=>{e.preventDefault();scratch(getPos(null,e.touches[0]));},{passive:false});" +
            "cv.addEventListener('touchmove',e=>{e.preventDefault();scratch(getPos(null,e.touches[0]));},{passive:false});}" +
            "function checkReveal(ctx,cv,idx,W,H){" +
            "if(rev[idx])return;" +
            "const d=ctx.getImageData(0,0,W,H).data;" +
            "let total=0,clear=0;" +
            "for(let i=3;i<d.length;i+=4){total++;if(d[i]<64)clear++;}" +
            "if(clear/total>0.58){" +
            "rev[idx]=true;" +
            /* fade out canvas */
            "cv.style.transition='opacity 0.4s';cv.style.opacity='0';" +
            "setTimeout(()=>cv.style.display='none',400);" +
            "checkAll();}}" +
            "function checkAll(){" +
            "if(rev[0]&&rev[1]&&rev[2]&&!claimed){claimed=true;claimPrize();}}" +
            "async function claimPrize(){" +
            "try{" +
            "const r=await fetch('/api/rubbellos/claim/'+TOKEN,{method:'POST'});" +
            "const d=await r.json();" +
            "const res=document.getElementById('result');" +
            "if(d.prize>0){" +
            "res.className='tk-result win';" +
            "document.getElementById('rtitle').textContent='🎉 Gewonnen!';" +
            "document.getElementById('ramt').textContent=d.prizeFmt;" +
            "document.getElementById('rdesc').textContent='Der Gewinn wurde sofort auf dein Bankkonto gutgeschrieben!';" +
            /* big burst celebration */
            "const tkt=document.querySelector('.ticket').getBoundingClientRect();" +
            "burstParticles(tkt.left+tkt.width/2,tkt.top+tkt.height/2);" +
            "setTimeout(()=>burstParticles(tkt.left+tkt.width*0.3,tkt.top+tkt.height*0.4),400);" +
            "setTimeout(()=>burstParticles(tkt.left+tkt.width*0.7,tkt.top+tkt.height*0.4),700);" +
            "}else{" +
            "res.className='tk-result lose';" +
            "document.getElementById('rtitle').textContent='😔 Leider keine 7...';" +
            "document.getElementById('ramt').textContent='';" +
            "document.getElementById('rdesc').textContent='Dieses Mal kein Gewinn. Kaufe ein neues Rubbellos und versuche dein Glück!';" +
            "}" +
            "res.style.display='block';" +
            "}catch(e){" +
            "const res=document.getElementById('result');" +
            "res.className='tk-result lose';" +
            "document.getElementById('rtitle').textContent='⚠️ Verbindungsfehler';" +
            "document.getElementById('rdesc').textContent='Bitte erneut versuchen.';" +
            "res.style.display='block';}}" +
            /* init all 3 canvases after layout */
            "window.addEventListener('load',()=>{" +
            "setupCanvas('c0',0);setupCanvas('c1',1);setupCanvas('c2',2);});" +
            "</script></body></html>";
    }

    private static String fmtCell(int v) {
        if (v == 0) return "Niete";
        return String.format("%,d$", v).replace(',', '.');
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
        if (ch == null) {
            // Kein Charakter — Discord-Profil als Fallback anzeigen
            net.dv8tion.jda.api.entities.Member member = guild.getMemberById(userId);
            String name = member != null ? member.getEffectiveName() : "Unbekannt";
            String avatar = member != null ? member.getUser().getEffectiveAvatarUrl() : "";
            ctx.status(200).contentType("text/html;charset=utf-8").result(buildNoCharacterPage(name, avatar));
            return;
        }
        ctx.contentType("text/html;charset=utf-8").result(buildIdCard(ch, userIdStr));
    }

    private static String buildNoCharacterPage(String name, String avatarUrl) {
        return "<!DOCTYPE html><html lang='de'><head><meta charset='UTF-8'>" +
            "<meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>Ausweis – " + esc(name) + "</title>" +
            "<style>*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);" +
            "font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;padding:20px}" +
            ".card{width:100%;max-width:420px;background:#0d1830;border:2px solid #c8a048;" +
            "border-radius:14px;padding:40px;text-align:center;box-shadow:0 0 40px rgba(200,160,72,.25)}" +
            "img{width:80px;height:80px;border-radius:50%;border:3px solid #c8a048;margin-bottom:16px}" +
            "h2{color:#c8a048;font-size:1.4rem;margin-bottom:10px}" +
            "p{color:#aaa;font-size:.9rem;line-height:1.6}" +
            "</style></head><body>" +
            "<div class='card'>" +
            (avatarUrl.isEmpty() ? "" : "<img src='" + esc(avatarUrl) + "' alt='Avatar'>") +
            "<h2>" + esc(name) + "</h2>" +
            "<p>Für diesen Spieler ist noch kein Charakter registriert.<br><br>" +
            "Ein Administrator kann den Charakter über das Meldeamt anlegen.</p>" +
            "</div></body></html>";
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
