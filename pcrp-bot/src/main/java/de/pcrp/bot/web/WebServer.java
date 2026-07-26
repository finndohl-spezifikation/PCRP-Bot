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

        // Admin: Nachricht in Channel senden
        app.post("/api/admin/announce",                WebServer::handleAdminAnnounce);

        // ── Info / Stats ───────────────────────────────────────────────────
        app.get("/info",          WebServer::serveInfo);
        app.get("/api/stats",     WebServer::handleStats);

        // ── City Chat ──────────────────────────────────────────────────────
        app.get( "/city-chat",                         WebServer::serveCityChat);
        app.post("/api/city-chat/auth",                ctx -> CityChatHandler.handleAuth(ctx));
        app.get( "/api/city-chat/me",                  ctx -> CityChatHandler.handleGetMe(ctx));
        app.put( "/api/city-chat/me",                  ctx -> CityChatHandler.handleUpdateMe(ctx));
        app.get( "/api/city-chat/contacts",            ctx -> CityChatHandler.handleGetContacts(ctx));
        app.post("/api/city-chat/contacts",            ctx -> CityChatHandler.handleAddContact(ctx));
        app.delete("/api/city-chat/contacts/{number}", ctx -> CityChatHandler.handleDeleteContact(ctx));
        app.get( "/api/city-chat/chats",               ctx -> CityChatHandler.handleGetChats(ctx));
        app.get( "/api/city-chat/messages/{chatId}",   ctx -> CityChatHandler.handleGetMessages(ctx));
        app.post("/api/city-chat/messages",            ctx -> CityChatHandler.handleSendMessage(ctx));
        app.post("/api/city-chat/block",               ctx -> CityChatHandler.handleBlock(ctx));
        app.delete("/api/city-chat/block/{number}",    ctx -> CityChatHandler.handleUnblock(ctx));
        app.get( "/api/city-chat/blocked",             ctx -> CityChatHandler.handleGetBlocked(ctx));

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

    // ── city-chat.html ─────────────────────────────────────────

    private static void serveCityChat(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/city-chat.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── /info ──────────────────────────────────────────────────

    private static void serveInfo(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/info.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── /api/stats ─────────────────────────────────────────────

    private static void handleStats(Context ctx) {
        JsonObject j = new JsonObject();
        j.addProperty("commands",          BotStats.commandCount);
        j.addProperty("moderationSystems", BotStats.MODERATION_SYSTEMS);
        j.addProperty("webDashboards",     BotStats.WEB_DASHBOARDS);
        ctx.contentType("application/json").result(GSON.toJson(j));
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

    private static void handleAdminAnnounce(Context ctx) {
        JsonObject body;
        try { body = GSON.fromJson(ctx.body(), JsonObject.class); }
        catch (Exception e) { ctx.status(400).result("bad json"); return; }
        if (body == null) { ctx.status(400).result("empty body"); return; }

        String secret  = body.has("secret")    ? body.get("secret").getAsString()    : "";
        String chanId  = body.has("channelId") ? body.get("channelId").getAsString() : "";
        String title   = body.has("title")     ? body.get("title").getAsString()     : "";
        String desc    = body.has("desc")      ? body.get("desc").getAsString()       : "";

        String envSecret = System.getenv("ADMIN_SECRET");
        String expected  = (envSecret != null && !envSecret.isBlank()) ? envSecret : "pcrp-admin-2026";
        if (!expected.equals(secret)) {
            ctx.status(403).result("forbidden"); return;
        }

        Guild guild = BotContext.getGuild();
        if (guild == null) { ctx.status(503).result("bot not ready"); return; }

        net.dv8tion.jda.api.entities.channel.concrete.TextChannel ch =
            guild.getTextChannelById(chanId);
        if (ch == null) { ctx.status(404).result("channel not found"); return; }

        MessageEmbed embed = EmbedFactory.build(title, desc);
        ch.sendMessageEmbeds(embed).queue(
            ok  -> log.info("[Admin] Announce gesendet in {}", chanId),
            err -> log.error("[Admin] Announce fehlgeschlagen", err)
        );
        ctx.status(200).result("ok");
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
        int[] picks = parsePicks(body);
        if (picks == null) {
            r.addProperty("ok", false); r.addProperty("error", "Ungültige Zahlenauswahl.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String error = LottoManager.enroll(guild.getId(), userId, picks);
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
        JsonObject body;
        try { body = GSON.fromJson(ctx.body(), JsonObject.class); }
        catch (Exception e) { body = null; }
        int[] picks = parsePicks(body);
        if (picks == null) {
            r.addProperty("ok", false); r.addProperty("error", "Ungültige Zahlenauswahl.");
            ctx.status(400).contentType("application/json").result(GSON.toJson(r)); return;
        }
        String guildId = info[0];
        String userId  = info[1];
        LottoManager.deleteToken(token);
        String error = LottoManager.enroll(guildId, userId, picks);
        if (error != null) {
            r.addProperty("ok", false); r.addProperty("error", error);
            ctx.contentType("application/json").result(GSON.toJson(r)); return;
        }
        int jackpot = LottoManager.getCurrentJackpot(guildId);
        r.addProperty("ok", true);
        r.addProperty("jackpotFmt", LottoManager.formatAmount(jackpot));
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    /** Liest das "picks"-Array aus dem JSON-Body. Gibt null zurück wenn ungültig. */
    private static int[] parsePicks(JsonObject body) {
        if (body == null || !body.has("picks")) return null;
        try {
            JsonArray arr = body.getAsJsonArray("picks");
            if (arr.size() != LottoManager.PICK_COUNT) return null;
            int[] picks = new int[LottoManager.PICK_COUNT];
            for (int i = 0; i < arr.size(); i++) picks[i] = arr.get(i).getAsInt();
            return picks;
        } catch (Exception e) { return null; }
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
        return buildLottoUI(null);
    }

    /**
     * Baut die gemeinsame Lotto-Seite.
     * token == null → allgemeine Seite mit Benutzername-Schritt
     * token != null → persönlicher Link, direkt zur Zahlenwahl
     */
    private static String buildLottoUI(String token) {
        boolean tokenMode = token != null;
        String CSS =
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:linear-gradient(135deg,#0d0600,#1a0900);" +
            "font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;padding:16px}" +
            ".card{width:100%;max-width:500px;background:rgba(255,255,255,.04);border:1px solid #CC5500;" +
            "border-radius:16px;overflow:hidden;box-shadow:0 0 40px rgba(204,85,0,.25)}" +
            ".hdr{background:linear-gradient(90deg,#CC5500,#993300);padding:20px;text-align:center}" +
            ".hdr h1{color:#fff;font-size:1.8rem;letter-spacing:3px}" +
            ".hdr p{color:#ffd0a0;font-size:.8rem;margin-top:3px;letter-spacing:1px}" +
            ".bdy{padding:22px}" +
            ".jp{text-align:center;margin-bottom:18px}" +
            ".jp .lbl{color:#888;font-size:.7rem;letter-spacing:2px;text-transform:uppercase}" +
            ".jp .amt{color:#FF8800;font-size:2.4rem;font-weight:700;margin-top:4px;text-shadow:0 0 20px rgba(255,136,0,.4)}" +
            ".jp .pts{color:#777;font-size:.8rem;margin-top:4px}" +
            "hr{border:none;border-top:1px solid #CC550030;margin:0 0 18px}" +
            ".step{display:none;flex-direction:column;gap:12px}" +
            ".step.on{display:flex}" +
            ".slbl{color:#888;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;text-align:center}" +
            "input{width:100%;padding:11px 14px;background:#0d0600;border:1px solid #CC5500;" +
            "border-radius:8px;color:#fff;font-size:.95rem;outline:none}" +
            "input::placeholder{color:#444}" +
            "button{display:block;width:100%;padding:13px;background:linear-gradient(90deg,#CC5500,#FF6600);" +
            "border:none;border-radius:8px;color:#fff;font-size:.95rem;font-weight:700;" +
            "letter-spacing:1px;cursor:pointer;transition:opacity .2s}" +
            "button:hover{opacity:.88}button:disabled{opacity:.35;cursor:not-allowed}" +
            ".msg{padding:11px;border-radius:8px;font-size:.85rem;text-align:center;display:none}" +
            ".msg.ok{background:#1a3a0d;border:1px solid #4a9930;color:#7ddd55}" +
            ".msg.err{background:#3a0d0d;border:1px solid #993030;color:#dd5555}" +
            // Zahlen-Grid
            ".grid-wrap{background:rgba(0,0,0,.2);border-radius:10px;padding:14px}" +
            ".grid-info{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}" +
            ".grid-hint{color:#888;font-size:.75rem}" +
            ".grid-cnt{color:#FF8800;font-size:.82rem;font-weight:700}" +
            ".grid{display:grid;grid-template-columns:repeat(9,1fr);gap:5px}" +
            ".num{aspect-ratio:1;display:flex;align-items:center;justify-content:center;" +
            "border-radius:50%;background:#1a0800;border:1px solid #CC550055;" +
            "color:#CC8844;font-size:.72rem;font-weight:700;cursor:pointer;transition:all .12s;user-select:none}" +
            ".num:hover{border-color:#FF6600;color:#FF8800}" +
            ".num.sel{background:#CC5500;border-color:#FF6600;color:#fff;box-shadow:0 0 8px rgba(204,85,0,.5)}" +
            ".num.full{opacity:.35;pointer-events:none}" +
            // Quoten-Info
            ".quot{background:rgba(255,136,0,.06);border:1px solid #CC550030;border-radius:8px;padding:12px;margin-top:2px}" +
            ".quot-row{display:flex;justify-content:space-between;align-items:center;padding:3px 0;font-size:.78rem}" +
            ".quot-row:not(:last-child){border-bottom:1px solid #CC550020}" +
            ".quot-k{color:#aaa}" +
            ".quot-v{color:#FF8800;font-weight:700}" +
            // Ergebnis
            ".win{background:rgba(255,136,0,.07);border:1px solid #CC550060;border-radius:12px;padding:22px;text-align:center}" +
            ".win .ic{font-size:2.4rem;margin-bottom:10px}" +
            ".win h2{color:#FF8800;font-size:1.2rem;margin-bottom:8px}" +
            ".win p{color:#bbb;font-size:.85rem;line-height:1.65}" +
            ".win strong{color:#FF8800}" +
            ".foot{text-align:center;color:#555;font-size:.7rem;margin-top:16px}";

        String quotenHtml =
            "<div class='quot'>" +
            "<div class='quot-row'><span class='quot-k'>6 Richtige</span><span class='quot-v' id='qj'>Jackpot</span></div>" +
            "<div class='quot-row'><span class='quot-k'>5 Richtige</span><span class='quot-v'>50.000$</span></div>" +
            "<div class='quot-row'><span class='quot-k'>4 Richtige</span><span class='quot-v'>10.000$</span></div>" +
            "<div class='quot-row'><span class='quot-k'>3 oder weniger</span><span class='quot-v'>Niete</span></div>" +
            "</div>";

        String gridHtml =
            "<div class='grid-wrap'>" +
            "<div class='grid-info'>" +
            "<span class='grid-hint'>Wähle 6 Zahlen aus 1–45</span>" +
            "<span class='grid-cnt' id='cnt'>0 / 6</span>" +
            "</div>" +
            "<div class='grid' id='grid'></div>" +
            "</div>";

        String pickJs =
            "const sel=new Set();" +
            "const grid=document.getElementById('grid');" +
            "for(let i=1;i<=45;i++){const d=document.createElement('div');" +
            "d.className='num';d.textContent=i;d.dataset.n=i;" +
            "d.onclick=()=>toggle(d,i);grid.appendChild(d);}" +
            "function toggle(el,n){" +
            "if(el.classList.contains('sel')){el.classList.remove('sel');sel.delete(n);}" +
            "else{if(sel.size>=6)return;el.classList.add('sel');sel.add(n);}" +
            "document.getElementById('cnt').textContent=sel.size+' / 6';" +
            "const full=sel.size>=6;" +
            "document.querySelectorAll('.num:not(.sel)').forEach(e=>e.classList.toggle('full',full));" +
            "document.getElementById('sbtn').disabled=sel.size!==6;}" +
            "function getPicks(){return Array.from(sel).sort((a,b)=>a-b);}";

        StringBuilder sb = new StringBuilder();
        sb.append("<!DOCTYPE html><html lang='de'><head>")
          .append("<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>")
          .append("<title>PCRP Lotto</title><style>").append(CSS).append("</style></head><body>")
          .append("<div class='card'>")
          .append("<div class='hdr'><h1>🎰 PCRP LOTTO</h1><p>Paradise City Roleplay</p></div>")
          .append("<div class='bdy'>")
          .append("<div class='jp'><div class='lbl'>Aktueller Jackpot</div>")
          .append("<div class='amt' id='jp'>Lädt…</div><div class='pts' id='pts'></div></div>")
          .append("<hr>");

        if (!tokenMode) {
            // Step 1 — Benutzername
            sb.append("<div class='step on' id='s1'>")
              .append("<div class='slbl'>Discord-Benutzername</div>")
              .append("<input id='uname' type='text' placeholder='z. B. max_mustermann' maxlength='40'>")
              .append("<button id='nbtn' onclick='goStep2()'>➡️ Weiter zur Zahlenwahl</button>")
              .append("<div class='msg' id='m1'></div></div>");
        }

        // Step: Zahlenauswahl
        sb.append("<div class='step").append(tokenMode ? " on" : "").append("' id='s2'>")
          .append("<div class='slbl'>Deine ").append(LottoManager.PICK_COUNT).append(" Glückszahlen wählen</div>")
          .append(gridHtml)
          .append(quotenHtml)
          .append("<button id='sbtn' disabled onclick='enroll()'>🎟️ Lottoschein abgeben</button>")
          .append("<div class='msg' id='m2'></div></div>");

        // Step: Bestätigung
        sb.append("<div class='step' id='s3'>")
          .append("<div class='win'><div class='ic'>🎉</div><h2>Du bist dabei!</h2>")
          .append("<p>Deine Zahlen: <strong id='myNums'></strong><br>")
          .append("Jackpot: <strong id='j3'></strong><br>")
          .append("Ziehung heute um <strong>12:00 Uhr</strong>. Viel Gl&#252;ck! 🍀</p>")
          .append("</div></div>");

        sb.append("<div class='foot'>T&#228;glich um 12:00 Uhr • 6 aus 45 • Jackpot w&#228;chst bis 5.000.000$</div>")
          .append("</div></div><script>");

        if (!tokenMode) {
            sb.append("const KN='pcrp_uname';")
              .append("let uid='';")
              .append("const stored=localStorage.getItem(KN);")
              .append("if(stored)document.getElementById('uname').value=stored;")
              .append("function show(id){['s1','s2','s3'].forEach(s=>{const e=document.getElementById(s);if(e)e.className='step'+(s==id?' on':'');});}")
              .append("async function goStep2(){")
              .append("const v=document.getElementById('uname').value.trim();")
              .append("if(!v){showMsg('m1','Bitte gib deinen Discord-Benutzernamen ein.','err');return;}")
              .append("const btn=document.getElementById('nbtn');btn.disabled=true;")
              .append("try{const r=await fetch('/api/resolve-user',{method:'POST',")
              .append("headers:{'Content-Type':'application/json'},body:JSON.stringify({username:v})});")
              .append("const d=await r.json();")
              .append("if(!d.ok){showMsg('m1',d.error,'err');btn.disabled=false;return;}")
              .append("localStorage.setItem(KN,v);uid=d.userId;show('s2');")
              .append("}catch(e){showMsg('m1','Verbindungsfehler.','err');btn.disabled=false;}}")
              .append("async function enroll(){")
              .append("const btn=document.getElementById('sbtn');btn.disabled=true;")
              .append("const picks=getPicks();")
              .append("try{const r=await fetch('/api/lotto/enroll',{method:'POST',")
              .append("headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:uid,picks:picks})});")
              .append("const d=await r.json();")
              .append("if(d.ok){document.getElementById('myNums').textContent=picks.join(' – ');")
              .append("document.getElementById('j3').textContent=d.jackpotFmt;show('s3');loadJp();}")
              .append("else{showMsg('m2',d.error,'err');btn.disabled=false;}}")
              .append("catch(e){showMsg('m2','Verbindungsfehler.','err');btn.disabled=false;}}");
        } else {
            sb.append("function show(id){['s2','s3'].forEach(s=>{const e=document.getElementById(s);if(e)e.className='step'+(s==id?' on':'');});}")
              .append("const TOKEN='").append(token).append("';")
              .append("async function enroll(){")
              .append("const btn=document.getElementById('sbtn');btn.disabled=true;")
              .append("const picks=getPicks();")
              .append("try{const r=await fetch('/api/lotto/enroll/'+TOKEN,{method:'POST',")
              .append("headers:{'Content-Type':'application/json'},body:JSON.stringify({picks:picks})});")
              .append("const d=await r.json();")
              .append("if(d.ok){document.getElementById('myNums').textContent=picks.join(' – ');")
              .append("document.getElementById('j3').textContent=d.jackpotFmt;show('s3');loadJp();}")
              .append("else{showMsg('m2',d.error,'err');btn.disabled=false;}}")
              .append("catch(e){showMsg('m2','Verbindungsfehler.','err');btn.disabled=false;}}");
        }

        sb.append("function showMsg(id,t,c){const m=document.getElementById(id);m.textContent=t;m.className='msg '+c;m.style.display='block';}")
          .append("async function loadJp(){try{const r=await fetch('/api/lotto/status');const d=await r.json();")
          .append("if(d.ok){document.getElementById('jp').textContent=d.jackpotFmt;")
          .append("document.getElementById('pts').textContent='🎟️ Teilnehmer: '+d.participants;")
          .append("document.getElementById('j3').textContent=d.jackpotFmt;")
          .append("if(document.getElementById('qj'))document.getElementById('qj').textContent=d.jackpotFmt;")
          .append("}}catch(e){}}")
          .append(pickJs)
          .append("loadJp();")
          .append("</script></body></html>");

        return sb.toString();
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
        return buildLottoUI(token);
    }

    // ── /rubbellos (allgemeine Seite) ─────────────────────────────────────────

    private static void serveRubbellosGeneral(Context ctx) {
        ctx.contentType("text/html;charset=utf-8").result(buildRubbellosGeneralPage());
    }

    private static String buildRubbellosGeneralPage() {
        // General /rubbellos page – same ticket design but asks for username first,
        // then loads the 3×3 grid via /api/rubbellos/create and shows it inline.
        return "<!DOCTYPE html><html lang='de'><head>" +
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>Goldene 7 – PCRP Rubbellos</title>" +
            "<style>" +
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:#0a0700;font-family:'Arial Black',Arial,sans-serif;" +
            "display:flex;align-items:center;justify-content:center;padding:14px;overflow:hidden}" +
            "#pcanvas{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:999}" +
            ".ticket{width:100%;max-width:360px;border-radius:14px;overflow:hidden;" +
            "box-shadow:0 0 60px rgba(255,200,0,.2),0 16px 48px rgba(0,0,0,.7);border:3px solid #8b6000}" +
            ".tk-hdr{background:#1a0f00;padding:5px;text-align:center;border-bottom:1px solid #b8860b22}" +
            ".tk-hdr span{color:#b8860b;font-size:.55rem;letter-spacing:4px;font-family:'Segoe UI',sans-serif}" +
            ".tk-top{background:linear-gradient(90deg,#d49000,#ffe040,#ffc800,#c07000);" +
            "padding:8px 12px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #6b3e00}" +
            ".tk-prize{display:flex;flex-direction:column}" +
            ".tk-plbl{font-size:.52rem;font-weight:900;color:#2a1000;letter-spacing:2px;text-transform:uppercase}" +
            ".tk-pamt{font-size:1.65rem;font-weight:900;color:#1a0800;line-height:1;text-shadow:1px 1px 0 rgba(255,248,160,.7)}" +
            ".tk-bars{display:flex;flex-direction:column;gap:3px}" +
            ".tk-bar{width:46px;height:12px;border-radius:3px;border:1px solid #5a3000;" +
            "background:linear-gradient(180deg,#fffbb0 0%,#e8a000 40%,#aa6800 75%,#7a4800 100%);" +
            "box-shadow:0 2px 4px rgba(0,0,0,.25),inset 0 1px 0 rgba(255,255,200,.35)}" +
            // login area
            ".tk-login{background:linear-gradient(160deg,#ffe040,#ffb800,#ff9500);padding:20px}" +
            ".tk-login label{display:block;font-size:.58rem;color:#2a1000;letter-spacing:2px;" +
            "font-weight:900;margin-bottom:8px;text-transform:uppercase}" +
            "input{width:100%;padding:11px 14px;background:rgba(0,0,0,.15);border:2px solid rgba(30,15,0,.3);" +
            "border-radius:8px;color:#1a0800;font-size:.95rem;font-family:'Segoe UI',sans-serif;outline:none;font-weight:700}" +
            "input::placeholder{color:rgba(30,15,0,.4);font-weight:400}" +
            "input:focus{border-color:rgba(30,15,0,.6)}" +
            ".tk-btn{margin-top:10px;width:100%;padding:13px;background:linear-gradient(90deg,#8b5e00,#c07000,#8b5e00);" +
            "border:none;border-radius:8px;color:#fff8e0;font-size:.95rem;font-weight:900;" +
            "letter-spacing:1px;cursor:pointer;transition:opacity .15s}" +
            ".tk-btn:hover{opacity:.88}.tk-btn:disabled{opacity:.4;cursor:not-allowed}" +
            ".tk-err{margin-top:8px;padding:10px;border-radius:7px;font-size:.8rem;" +
            "font-family:'Segoe UI',sans-serif;background:#3a0d0d;border:1px solid #993030;" +
            "color:#dd5555;display:none}" +
            // body with grid (hidden initially)
            ".tk-body{background:linear-gradient(160deg,#ffe040,#ffb800,#ff9500);" +
            "display:none;flex:1;border-bottom:2px solid #7a4800}" +
            ".tk-body.on{display:flex}" +
            ".tk-brand{width:37%;padding:10px 4px 10px 10px;display:flex;flex-direction:column;" +
            "justify-content:center;border-right:1px solid #8b5e0050}" +
            ".tk-g{font-size:1.05rem;font-weight:900;color:#1a0800;font-style:italic;letter-spacing:2px;line-height:1;" +
            "text-shadow:1px 1px 0 rgba(80,40,0,.4),-1px -1px 0 rgba(255,250,180,.3)}" +
            ".tk-7{font-size:4.8rem;font-weight:900;color:#1a0800;font-style:italic;line-height:.85;" +
            "text-shadow:4px 4px 0 rgba(80,40,0,.55),2px 2px 0 #b07000,-2px -2px 0 rgba(255,250,180,.25)}" +
            ".tk-grid{flex:1;padding:8px;display:flex;flex-direction:column;gap:5px;justify-content:center}" +
            ".tk-row{display:flex;gap:5px}" +
            ".cw{flex:1;position:relative;aspect-ratio:1}" +
            ".cb{width:100%;height:100%;border-radius:6px;background:linear-gradient(135deg,#2a1e00,#1e1600);" +
            "border:1.5px solid rgba(184,134,11,.35);display:flex;align-items:center;justify-content:center}" +
            ".cl{color:#ffd700;font-size:.68rem;font-weight:900;text-align:center;line-height:1.2;padding:2px}" +
            "canvas.sc{position:absolute;top:0;left:0;width:100%;height:100%;border-radius:6px;" +
            "cursor:crosshair;touch-action:none;-webkit-user-select:none;user-select:none}" +
            "@keyframes pulse{0%,100%{box-shadow:0 0 6px rgba(255,215,0,.3)}50%{box-shadow:0 0 16px rgba(255,215,0,.7)}}" +
            ".cw.wl .cb{border-color:#ffd700;animation:pulse 1.2s ease-in-out infinite}" +
            ".tk-info{background:#110d00;padding:7px 12px;display:none}" +
            ".tk-info.on{display:block}" +
            ".tk-itxt{color:#b8860b88;font-size:.57rem;line-height:1.5;font-family:'Segoe UI',sans-serif}" +
            ".tk-ich{color:#b8860b;font-size:.6rem;font-weight:700;letter-spacing:2px;margin-top:3px}" +
            ".tk-res{padding:14px 12px;text-align:center;display:none}" +
            ".tk-res.win{background:#081500;border-top:2px solid #3a8020}" +
            ".tk-res.lose{background:#110d00;border-top:1px solid #b8860b22}" +
            ".tk-res h2{font-size:1.15rem;font-weight:900;margin-bottom:4px}" +
            ".tk-res.win h2{color:#7ddd55}.tk-res.lose h2{color:#b8860b}" +
            ".tk-ra{color:#FFD700;font-size:1.5rem;font-weight:900;display:block;margin:4px 0}" +
            ".tk-rd{color:#999;font-size:.77rem;font-family:'Segoe UI',sans-serif;line-height:1.6}" +
            "</style></head><body>" +
            "<canvas id='pcanvas'></canvas>" +
            "<div class='ticket'>" +
            "<div class='tk-hdr'><span>★ PARADISE CITY ROLEPLAY ★</span></div>" +
            "<div class='tk-top'>" +
            "<div class='tk-prize'><span class='tk-plbl'>Gewinne bis zu</span><span class='tk-pamt'>30.000$</span></div>" +
            "<div class='tk-bars'>" +
            "<div class='tk-bar'></div><div class='tk-bar'></div><div class='tk-bar'></div>" +
            "<div class='tk-bar'></div><div class='tk-bar'></div><div class='tk-bar'></div>" +
            "</div></div>" +
            // Login form
            "<div class='tk-login' id='loginArea'>" +
            "<label>Discord-Benutzername</label>" +
            "<input id='uname' type='text' placeholder='z. B. max_mustermann' maxlength='40'>" +
            "<button class='tk-btn' id='sbtn' onclick='goScratch()'>🎰 Rubbellos einl&#246;sen</button>" +
            "<div class='tk-err' id='emsg'></div>" +
            "</div>" +
            // Grid (hidden initially)
            "<div class='tk-body' id='gridArea'>" +
            "<div class='tk-brand'><div class='tk-g'>GOLDENE</div><div class='tk-7'>7</div></div>" +
            "<div class='tk-grid'>" +
            "<div class='tk-row'>" +
            "<div class='cw' id='cw0'><div class='cb'><span class='cl' id='cv0'></span></div><canvas class='sc' id='cc0'></canvas></div>" +
            "<div class='cw' id='cw1'><div class='cb'><span class='cl' id='cv1'></span></div><canvas class='sc' id='cc1'></canvas></div>" +
            "<div class='cw' id='cw2'><div class='cb'><span class='cl' id='cv2'></span></div><canvas class='sc' id='cc2'></canvas></div>" +
            "</div><div class='tk-row'>" +
            "<div class='cw' id='cw3'><div class='cb'><span class='cl' id='cv3'></span></div><canvas class='sc' id='cc3'></canvas></div>" +
            "<div class='cw' id='cw4'><div class='cb'><span class='cl' id='cv4'></span></div><canvas class='sc' id='cc4'></canvas></div>" +
            "<div class='cw' id='cw5'><div class='cb'><span class='cl' id='cv5'></span></div><canvas class='sc' id='cc5'></canvas></div>" +
            "</div><div class='tk-row'>" +
            "<div class='cw' id='cw6'><div class='cb'><span class='cl' id='cv6'></span></div><canvas class='sc' id='cc6'></canvas></div>" +
            "<div class='cw' id='cw7'><div class='cb'><span class='cl' id='cv7'></span></div><canvas class='sc' id='cc7'></canvas></div>" +
            "<div class='cw' id='cw8'><div class='cb'><span class='cl' id='cv8'></span></div><canvas class='sc' id='cc8'></canvas></div>" +
            "</div></div></div>" +
            "<div class='tk-info' id='infoArea'>" +
            "<div class='tk-itxt'>3 gleiche Betr&#228;ge waagerecht, senkrecht oder diagonal = Gewinn!</div>" +
            "<div class='tk-ich'>8 GEWINNCHANCEN</div></div>" +
            "<div class='tk-res' id='tres'><h2 id='trt'></h2><span class='tk-ra' id='tra'></span><div class='tk-rd' id='trd'></div></div>" +
            "</div>" +
            "<script>" +
            "let G=null,claimToken=null,claimed=false;" +
            "const rev=new Array(9).fill(false);" +
            "const LINES=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];" +
            "function fmt(v){if(!v)return'Niete';return v.toLocaleString('de-DE')+'$';}" +
            // Particles
            "const pc=document.getElementById('pcanvas');" +
            "const px=pc.getContext('2d');let ptcl=[];" +
            "const COLS=['#FFD700','#FFA500','#FFEC00','#FFB800','#FFF0A0','#FF8C00'];" +
            "function rsz(){pc.width=innerWidth;pc.height=innerHeight;}rsz();addEventListener('resize',rsz);" +
            "function spawn(sx,sy,n){for(let i=0;i<n;i++){" +
            "const a=Math.random()*Math.PI*2,sp=Math.random()*2.5+.8;" +
            "ptcl.push({x:sx,y:sy,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-1.2,life:1," +
            "sz:Math.random()*3+1.5,c:COLS[Math.random()*COLS.length|0]});}}" +
            "function burst(sx,sy){for(let i=0;i<90;i++){" +
            "const a=Math.random()*Math.PI*2,sp=Math.random()*7+2;" +
            "ptcl.push({x:sx,y:sy,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-3,life:1," +
            "sz:Math.random()*6+2,c:COLS[Math.random()*COLS.length|0]});}}" +
            "function animP(){px.clearRect(0,0,pc.width,pc.height);" +
            "ptcl=ptcl.filter(p=>{p.x+=p.vx;p.y+=p.vy;p.vy+=.12;p.life-=.02;" +
            "if(p.life<=0)return false;px.globalAlpha=p.life;px.fillStyle=p.c;" +
            "px.beginPath();px.arc(p.x,p.y,p.sz,0,Math.PI*2);px.fill();return true;});" +
            "px.globalAlpha=1;requestAnimationFrame(animP);}animP();" +
            // Login flow
            "const KN='pcrp_uname';" +
            "const stored=localStorage.getItem(KN);" +
            "if(stored)document.getElementById('uname').value=stored;" +
            "function showErr(t){const m=document.getElementById('emsg');m.textContent=t;m.style.display='block';}" +
            "async function goScratch(){" +
            "const v=document.getElementById('uname').value.trim();" +
            "if(!v){showErr('Bitte gib deinen Discord-Benutzernamen ein.');return;}" +
            "const btn=document.getElementById('sbtn');btn.disabled=true;" +
            "document.getElementById('emsg').style.display='none';" +
            "try{" +
            "const r1=await fetch('/api/resolve-user',{method:'POST'," +
            "headers:{'Content-Type':'application/json'},body:JSON.stringify({username:v})});" +
            "const d1=await r1.json();" +
            "if(!d1.ok){showErr(d1.error);btn.disabled=false;return;}" +
            "localStorage.setItem(KN,v);" +
            "const r2=await fetch('/api/rubbellos/create',{method:'POST'," +
            "headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:d1.userId})});" +
            "const d2=await r2.json();" +
            "if(!d2.ok){showErr(d2.error);btn.disabled=false;return;}" +
            "claimToken=d2.token;" +
            "G=Array.from({length:9},(_,i)=>d2['g'+i]);" +
            "for(let i=0;i<9;i++)document.getElementById('cv'+i).textContent=fmt(G[i]);" +
            "document.getElementById('loginArea').style.display='none';" +
            "document.getElementById('gridArea').classList.add('on');" +
            "document.getElementById('infoArea').classList.add('on');" +
            "requestAnimationFrame(()=>requestAnimationFrame(()=>{for(let i=0;i<9;i++)initC(i);}));" +
            "}catch(e){showErr('Verbindungsfehler. Bitte erneut versuchen.');btn.disabled=false;}}" +
            // Canvas init (same as token page)
            "function initC(i){" +
            "const cv=document.getElementById('cc'+i);" +
            "const wr=document.getElementById('cw'+i);" +
            "const rc=wr.getBoundingClientRect();" +
            "const W=Math.round(rc.width),H=Math.round(rc.height);" +
            "if(!W||!H)return;" +
            "cv.width=W;cv.height=H;" +
            "const ctx=cv.getContext('2d');" +
            "const gd=ctx.createLinearGradient(0,0,W,H);" +
            "gd.addColorStop(0,'#ffe050');gd.addColorStop(.35,'#ffbe00');" +
            "gd.addColorStop(.7,'#e89400');gd.addColorStop(1,'#c07000');" +
            "ctx.fillStyle=gd;" +
            "ctx.beginPath();if(ctx.roundRect)ctx.roundRect(0,0,W,H,6);else ctx.rect(0,0,W,H);ctx.fill();" +
            "ctx.fillStyle='rgba(0,0,0,.07)';" +
            "const sw=W/10;for(let j=0;j<10;j+=2)ctx.fillRect(j*sw,0,sw,H);" +
            "ctx.fillStyle='rgba(255,255,200,.22)';" +
            "for(let j=0;j<5;j++){ctx.beginPath();" +
            "ctx.arc(Math.random()*W,Math.random()*H,Math.random()*1.8+.4,0,Math.PI*2);ctx.fill();}" +
            "ctx.fillStyle='rgba(30,14,0,.72)';" +
            "ctx.font='bold '+(W*.12|0)+'px Arial Black,Arial';" +
            "ctx.textAlign='center';ctx.textBaseline='middle';" +
            "ctx.fillText('RUBBELN',W/2,H*.28);" +
            "ctx.font='bold '+(W*.36|0)+'px Arial Black,Arial';" +
            "ctx.fillStyle='rgba(40,18,0,.78)';" +
            "ctx.fillText('7',W/2,H*.66);" +
            "let drag=false;" +
            "function gp(cx,cy){const r=cv.getBoundingClientRect();" +
            "return{x:(cx-r.left)/r.width*W,y:(cy-r.top)/r.height*H};}" +
            "function sc(cx,cy){if(rev[i])return;" +
            "const p=gp(cx,cy),R=W*.24;" +
            "ctx.globalCompositeOperation='destination-out';" +
            "const rg=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,R);" +
            "rg.addColorStop(0,'rgba(0,0,0,1)');" +
            "rg.addColorStop(.65,'rgba(0,0,0,.9)');" +
            "rg.addColorStop(1,'rgba(0,0,0,0)');" +
            "ctx.fillStyle=rg;ctx.beginPath();ctx.arc(p.x,p.y,R,0,Math.PI*2);ctx.fill();" +
            "ctx.globalCompositeOperation='source-over';" +
            "const rc2=cv.getBoundingClientRect();" +
            "spawn(rc2.left+p.x/W*rc2.width,rc2.top+p.y/H*rc2.height,4);" +
            "chkRev(ctx,i,W,H);}" +
            "cv.addEventListener('mousedown',e=>{drag=true;sc(e.clientX,e.clientY);});" +
            "cv.addEventListener('mousemove',e=>{if(drag)sc(e.clientX,e.clientY);});" +
            "cv.addEventListener('mouseup',()=>drag=false);" +
            "cv.addEventListener('mouseleave',()=>drag=false);" +
            "cv.addEventListener('touchstart',e=>{e.preventDefault();sc(e.touches[0].clientX,e.touches[0].clientY);},{passive:false});" +
            "cv.addEventListener('touchmove',e=>{e.preventDefault();sc(e.touches[0].clientX,e.touches[0].clientY);},{passive:false});}" +
            "function chkRev(ctx,i,W,H){if(rev[i])return;" +
            "const d=ctx.getImageData(0,0,W,H).data;" +
            "let tot=0,clr=0;for(let j=3;j<d.length;j+=4){tot++;if(d[j]<64)clr++;}" +
            "if(clr/tot>.54){rev[i]=true;" +
            "const cv=document.getElementById('cc'+i);" +
            "cv.style.transition='opacity .3s';cv.style.opacity='0';" +
            "setTimeout(()=>cv.style.display='none',320);checkAll();}}" +
            "function checkAll(){if(G&&rev.every(r=>r)&&!claimed){claimed=true;claimPrize();}}" +
            "async function claimPrize(){" +
            "let wl=null;" +
            "for(const l of LINES){const[a,b,c]=l;if(G[a]&&G[a]===G[b]&&G[b]===G[c]){wl=l;break;}}" +
            "if(wl)wl.forEach(i=>document.getElementById('cw'+i).classList.add('wl'));" +
            "try{const rs=await fetch('/api/rubbellos/claim/'+claimToken,{method:'POST'});" +
            "const d=await rs.json();" +
            "const el=document.getElementById('tres');" +
            "if(d.prize>0){el.className='tk-res win';" +
            "document.getElementById('trt').textContent='\\ud83c\\udf89 Gewonnen!';" +
            "document.getElementById('tra').textContent=d.prizeFmt;" +
            "document.getElementById('trd').textContent='Der Gewinn wurde sofort auf dein Bankkonto gutgeschrieben!';" +
            "const t=document.querySelector('.ticket').getBoundingClientRect();" +
            "const cx=t.left+t.width/2,cy=t.top+t.height/2;" +
            "burst(cx,cy);setTimeout(()=>burst(cx-55,cy-25),350);setTimeout(()=>burst(cx+55,cy-25),650);" +
            "}else{el.className='tk-res lose';" +
            "document.getElementById('trt').textContent='\\ud83d\\ude14 Leider keine 7...';" +
            "document.getElementById('tra').textContent='';" +
            "document.getElementById('trd').textContent='Kein Treffer – beim n\\u00e4chsten Rubbellos klappts bestimmt!';}" +
            "el.style.display='block';" +
            "}catch(e){}}" +
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
        int[] grid = RubbellosManager.buildGrid(prize);
        r.addProperty("ok", true);
        r.addProperty("token", token);
        for (int i = 0; i < 9; i++) r.addProperty("g" + i, grid[i]);
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
        int[] grid = RubbellosManager.buildGrid(prize);
        ctx.contentType("text/html;charset=utf-8").result(buildRubbellosPage(token, grid, prize));
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

    private static String buildRubbellosPage(String token, int[] grid, int prize) {
        // Build JS array literal for the 9-cell grid
        StringBuilder gjs = new StringBuilder("[");
        for (int i = 0; i < 9; i++) { gjs.append(grid[i]); if (i < 8) gjs.append(","); }
        gjs.append("]");
        String gridJs = gjs.toString();

        return "<!DOCTYPE html><html lang='de'><head>" +
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>Goldene 7 – PCRP Rubbellos</title>" +
            "<style>" +
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:#0a0700;font-family:'Arial Black',Arial,sans-serif;" +
            "display:flex;align-items:center;justify-content:center;padding:14px;overflow:hidden}" +
            "#pcanvas{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:999}" +
            ".ticket{width:100%;max-width:360px;border-radius:14px;overflow:hidden;" +
            "box-shadow:0 0 60px rgba(255,200,0,.2),0 16px 48px rgba(0,0,0,.7);border:3px solid #8b6000}" +
            // ── CSS rest ──
            ".tk-hdr{background:#1a0f00;padding:5px;text-align:center;border-bottom:1px solid #b8860b22}" +
            ".tk-hdr span{color:#b8860b;font-size:.55rem;letter-spacing:4px;font-family:'Segoe UI',sans-serif}" +
            ".tk-top{background:linear-gradient(90deg,#d49000,#ffe040,#ffc800,#c07000);" +
            "padding:8px 12px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #6b3e00}" +
            ".tk-prize{display:flex;flex-direction:column}" +
            ".tk-plbl{font-size:.52rem;font-weight:900;color:#2a1000;letter-spacing:2px;text-transform:uppercase}" +
            ".tk-pamt{font-size:1.65rem;font-weight:900;color:#1a0800;line-height:1;text-shadow:1px 1px 0 rgba(255,248,160,.7)}" +
            ".tk-bars{display:flex;flex-direction:column;gap:3px}" +
            ".tk-bar{width:46px;height:12px;border-radius:3px;border:1px solid #5a3000;" +
            "background:linear-gradient(180deg,#fffbb0 0%,#e8a000 40%,#aa6800 75%,#7a4800 100%);" +
            "box-shadow:0 2px 4px rgba(0,0,0,.25),inset 0 1px 0 rgba(255,255,200,.35)}" +
            ".tk-body{background:linear-gradient(160deg,#ffe040 0%,#ffb800 55%,#ff9500 100%);" +
            "display:flex;border-bottom:2px solid #7a4800}" +
            ".tk-brand{width:37%;padding:10px 4px 10px 10px;display:flex;flex-direction:column;" +
            "justify-content:center;border-right:1px solid #8b5e0050}" +
            ".tk-g{font-size:1.05rem;font-weight:900;color:#1a0800;font-style:italic;letter-spacing:2px;line-height:1;" +
            "text-shadow:1px 1px 0 rgba(80,40,0,.4),-1px -1px 0 rgba(255,250,180,.3)}" +
            ".tk-7{font-size:4.8rem;font-weight:900;color:#1a0800;font-style:italic;line-height:.85;" +
            "text-shadow:4px 4px 0 rgba(80,40,0,.55),2px 2px 0 #b07000,-2px -2px 0 rgba(255,250,180,.25)}" +
            ".tk-grid{flex:1;padding:8px;display:flex;flex-direction:column;gap:5px;justify-content:center}" +
            ".tk-row{display:flex;gap:5px}" +
            ".cw{flex:1;position:relative;aspect-ratio:1}" +
            ".cb{width:100%;height:100%;border-radius:6px;" +
            "background:linear-gradient(135deg,#2a1e00,#1e1600);" +
            "border:1.5px solid rgba(184,134,11,.35);" +
            "display:flex;align-items:center;justify-content:center}" +
            ".cl{color:#ffd700;font-size:.68rem;font-weight:900;text-align:center;line-height:1.2;padding:2px}" +
            "canvas.sc{position:absolute;top:0;left:0;width:100%;height:100%;border-radius:6px;" +
            "cursor:crosshair;touch-action:none;-webkit-user-select:none;user-select:none}" +
            "@keyframes pulse{0%,100%{box-shadow:0 0 6px rgba(255,215,0,.3)}50%{box-shadow:0 0 16px rgba(255,215,0,.7)}}" +
            ".cw.wl .cb{border-color:#ffd700;animation:pulse 1.2s ease-in-out infinite}" +
            ".tk-info{background:#110d00;padding:7px 12px}" +
            ".tk-itxt{color:#b8860b88;font-size:.57rem;line-height:1.5;font-family:'Segoe UI',sans-serif}" +
            ".tk-ich{color:#b8860b;font-size:.6rem;font-weight:700;letter-spacing:2px;margin-top:3px}" +
            ".tk-res{padding:14px 12px;text-align:center;display:none}" +
            ".tk-res.win{background:#081500;border-top:2px solid #3a8020}" +
            ".tk-res.lose{background:#110d00;border-top:1px solid #b8860b22}" +
            ".tk-res h2{font-size:1.15rem;font-weight:900;margin-bottom:4px}" +
            ".tk-res.win h2{color:#7ddd55}.tk-res.lose h2{color:#b8860b}" +
            ".tk-ra{color:#FFD700;font-size:1.5rem;font-weight:900;display:block;margin:4px 0}" +
            ".tk-rd{color:#999;font-size:.77rem;font-family:'Segoe UI',sans-serif;line-height:1.6}" +
            "</style></head><body>" +
            "<canvas id='pcanvas'></canvas>" +
            "<div class='ticket'>" +
            "<div class='tk-hdr'><span>★ PARADISE CITY ROLEPLAY ★</span></div>" +
            "<div class='tk-top'>" +
            "<div class='tk-prize'><span class='tk-plbl'>Gewinne bis zu</span><span class='tk-pamt'>30.000$</span></div>" +
            "<div class='tk-bars'>" +
            "<div class='tk-bar'></div><div class='tk-bar'></div><div class='tk-bar'></div>" +
            "<div class='tk-bar'></div><div class='tk-bar'></div><div class='tk-bar'></div>" +
            "</div></div>" +
            "<div class='tk-body'>" +
            "<div class='tk-brand'><div class='tk-g'>GOLDENE</div><div class='tk-7'>7</div></div>" +
            "<div class='tk-grid'>" +
            "<div class='tk-row'>" +
            "<div class='cw' id='cw0'><div class='cb'><span class='cl' id='cv0'></span></div><canvas class='sc' id='cc0'></canvas></div>" +
            "<div class='cw' id='cw1'><div class='cb'><span class='cl' id='cv1'></span></div><canvas class='sc' id='cc1'></canvas></div>" +
            "<div class='cw' id='cw2'><div class='cb'><span class='cl' id='cv2'></span></div><canvas class='sc' id='cc2'></canvas></div>" +
            "</div><div class='tk-row'>" +
            "<div class='cw' id='cw3'><div class='cb'><span class='cl' id='cv3'></span></div><canvas class='sc' id='cc3'></canvas></div>" +
            "<div class='cw' id='cw4'><div class='cb'><span class='cl' id='cv4'></span></div><canvas class='sc' id='cc4'></canvas></div>" +
            "<div class='cw' id='cw5'><div class='cb'><span class='cl' id='cv5'></span></div><canvas class='sc' id='cc5'></canvas></div>" +
            "</div><div class='tk-row'>" +
            "<div class='cw' id='cw6'><div class='cb'><span class='cl' id='cv6'></span></div><canvas class='sc' id='cc6'></canvas></div>" +
            "<div class='cw' id='cw7'><div class='cb'><span class='cl' id='cv7'></span></div><canvas class='sc' id='cc7'></canvas></div>" +
            "<div class='cw' id='cw8'><div class='cb'><span class='cl' id='cv8'></span></div><canvas class='sc' id='cc8'></canvas></div>" +
            "</div></div></div>" +
            "<div class='tk-info'>" +
            "<div class='tk-itxt'>Rubbele alle 9 Felder frei! 3 gleiche Betr&#228;ge waagerecht, senkrecht oder diagonal = Gewinn!</div>" +
            "<div class='tk-ich'>8 GEWINNCHANCEN</div></div>" +
            "<div class='tk-res' id='tres'><h2 id='trt'></h2><span class='tk-ra' id='tra'></span><div class='tk-rd' id='trd'></div></div>" +
            "</div>" +
            "<script>" +
            "const TOKEN='" + token + "';" +
            "const PRIZE=" + prize + ";" +
            "const G=" + gridJs + ";" +
            "const LINES=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];" +
            "const rev=new Array(9).fill(false);let claimed=false;" +
            "function fmt(v){if(!v)return'Niete';return v.toLocaleString('de-DE')+'$';}" +
            "for(let i=0;i<9;i++)document.getElementById('cv'+i).textContent=fmt(G[i]);" +
            // Particle system
            "const pc=document.getElementById('pcanvas');" +
            "const px=pc.getContext('2d');let ptcl=[];" +
            "const COLS=['#FFD700','#FFA500','#FFEC00','#FFB800','#FFF0A0','#FF8C00','#FFDD44'];" +
            "function rsz(){pc.width=innerWidth;pc.height=innerHeight;}rsz();addEventListener('resize',rsz);" +
            "function spawn(sx,sy,n){for(let i=0;i<n;i++){" +
            "const a=Math.random()*Math.PI*2,sp=Math.random()*2.5+.8;" +
            "ptcl.push({x:sx,y:sy,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-1.2,life:1," +
            "sz:Math.random()*3+1.5,c:COLS[Math.random()*COLS.length|0]});}}" +
            "function burst(sx,sy){for(let i=0;i<90;i++){" +
            "const a=Math.random()*Math.PI*2,sp=Math.random()*7+2;" +
            "ptcl.push({x:sx,y:sy,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-3,life:1," +
            "sz:Math.random()*6+2,c:COLS[Math.random()*COLS.length|0]});}}" +
            "function animP(){px.clearRect(0,0,pc.width,pc.height);" +
            "ptcl=ptcl.filter(p=>{p.x+=p.vx;p.y+=p.vy;p.vy+=.12;p.life-=.02;" +
            "if(p.life<=0)return false;px.globalAlpha=p.life;px.fillStyle=p.c;" +
            "px.beginPath();px.arc(p.x,p.y,p.sz,0,Math.PI*2);px.fill();return true;});" +
            "px.globalAlpha=1;requestAnimationFrame(animP);}animP();" +
            // Canvas init
            "function initC(i){" +
            "const cv=document.getElementById('cc'+i);" +
            "const wr=document.getElementById('cw'+i);" +
            "const rc=wr.getBoundingClientRect();" +
            "const W=Math.round(rc.width),H=Math.round(rc.height);" +
            "if(!W||!H)return;" +
            "cv.width=W;cv.height=H;" +
            "const ctx=cv.getContext('2d');" +
            // gold gradient
            "const gd=ctx.createLinearGradient(0,0,W,H);" +
            "gd.addColorStop(0,'#ffe050');gd.addColorStop(.35,'#ffbe00');" +
            "gd.addColorStop(.7,'#e89400');gd.addColorStop(1,'#c07000');" +
            "ctx.fillStyle=gd;" +
            "ctx.beginPath();" +
            "if(ctx.roundRect)ctx.roundRect(0,0,W,H,6);else ctx.rect(0,0,W,H);" +
            "ctx.fill();" +
            // stripe texture
            "ctx.fillStyle='rgba(0,0,0,.07)';" +
            "const sw=W/10;for(let j=0;j<10;j+=2)ctx.fillRect(j*sw,0,sw,H);" +
            // shimmer
            "ctx.fillStyle='rgba(255,255,200,.22)';" +
            "for(let j=0;j<5;j++){ctx.beginPath();" +
            "ctx.arc(Math.random()*W,Math.random()*H,Math.random()*1.8+.4,0,Math.PI*2);ctx.fill();}" +
            // RUBBELN label
            "ctx.fillStyle='rgba(30,14,0,.72)';" +
            "ctx.font='bold '+(W*.12|0)+'px Arial Black,Arial';" +
            "ctx.textAlign='center';ctx.textBaseline='middle';" +
            "ctx.fillText('RUBBELN',W/2,H*.28);" +
            // big 7
            "ctx.font='bold '+(W*.36|0)+'px Arial Black,Arial';" +
            "ctx.fillStyle='rgba(40,18,0,.78)';" +
            "ctx.fillText('7',W/2,H*.66);" +
            // events
            "let drag=false;" +
            "function gp(cx,cy){const r=cv.getBoundingClientRect();" +
            "return{x:(cx-r.left)/r.width*W,y:(cy-r.top)/r.height*H};}" +
            "function sc(cx,cy){if(rev[i])return;" +
            "const p=gp(cx,cy),R=W*.24;" +
            "ctx.globalCompositeOperation='destination-out';" +
            "const rg=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,R);" +
            "rg.addColorStop(0,'rgba(0,0,0,1)');" +
            "rg.addColorStop(.65,'rgba(0,0,0,.9)');" +
            "rg.addColorStop(1,'rgba(0,0,0,0)');" +
            "ctx.fillStyle=rg;ctx.beginPath();ctx.arc(p.x,p.y,R,0,Math.PI*2);ctx.fill();" +
            "ctx.globalCompositeOperation='source-over';" +
            "const rc2=cv.getBoundingClientRect();" +
            "spawn(rc2.left+p.x/W*rc2.width,rc2.top+p.y/H*rc2.height,4);" +
            "chkRev(ctx,i,W,H);}" +
            "cv.addEventListener('mousedown',e=>{drag=true;sc(e.clientX,e.clientY);});" +
            "cv.addEventListener('mousemove',e=>{if(drag)sc(e.clientX,e.clientY);});" +
            "cv.addEventListener('mouseup',()=>drag=false);" +
            "cv.addEventListener('mouseleave',()=>drag=false);" +
            "cv.addEventListener('touchstart',e=>{e.preventDefault();sc(e.touches[0].clientX,e.touches[0].clientY);},{passive:false});" +
            "cv.addEventListener('touchmove',e=>{e.preventDefault();sc(e.touches[0].clientX,e.touches[0].clientY);},{passive:false});}" +
            "function chkRev(ctx,i,W,H){if(rev[i])return;" +
            "const d=ctx.getImageData(0,0,W,H).data;" +
            "let tot=0,clr=0;for(let j=3;j<d.length;j+=4){tot++;if(d[j]<64)clr++;}" +
            "if(clr/tot>.54){rev[i]=true;" +
            "const cv=document.getElementById('cc'+i);" +
            "cv.style.transition='opacity .3s';cv.style.opacity='0';" +
            "setTimeout(()=>cv.style.display='none',320);" +
            "checkAll();}}" +
            "function checkAll(){if(rev.every(r=>r)&&!claimed){claimed=true;claimPrize();}}" +
            "async function claimPrize(){" +
            // highlight win line client-side (using pre-embedded GRID values)
            "let wl=null;" +
            "for(const l of LINES){const[a,b,c]=l;if(G[a]&&G[a]===G[b]&&G[b]===G[c]){wl=l;break;}}" +
            "if(wl)wl.forEach(i=>document.getElementById('cw'+i).classList.add('wl'));" +
            "try{const rs=await fetch('/api/rubbellos/claim/'+TOKEN,{method:'POST'});" +
            "const d=await rs.json();" +
            "const el=document.getElementById('tres');" +
            "if(d.prize>0){el.className='tk-res win';" +
            "document.getElementById('trt').textContent='🎉 Gewonnen!';" +
            "document.getElementById('tra').textContent=d.prizeFmt;" +
            "document.getElementById('trd').textContent='Der Gewinn wurde sofort auf dein Bankkonto gutgeschrieben!';" +
            "const t=document.querySelector('.ticket').getBoundingClientRect();" +
            "const cx=t.left+t.width/2,cy=t.top+t.height/2;" +
            "burst(cx,cy);setTimeout(()=>burst(cx-55,cy-25),350);setTimeout(()=>burst(cx+55,cy-25),650);" +
            "}else{el.className='tk-res lose';" +
            "document.getElementById('trt').textContent='😔 Leider keine 7...';" +
            "document.getElementById('tra').textContent='';" +
            "document.getElementById('trd').textContent='Kein Treffer dieses Mal – beim n\\u00e4chsten Rubbellos klappts bestimmt!';}" +
            "el.style.display='block';" +
            "}catch(e){const el=document.getElementById('tres');el.className='tk-res lose';" +
            "document.getElementById('trt').textContent='\\u26a0\\ufe0f Fehler';" +
            "document.getElementById('trd').textContent='Bitte erneut versuchen.';el.style.display='block';}}" +
            // init canvases after full layout render
            "requestAnimationFrame(()=>requestAnimationFrame(()=>{for(let i=0;i<9;i++)initC(i);}));" +
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
