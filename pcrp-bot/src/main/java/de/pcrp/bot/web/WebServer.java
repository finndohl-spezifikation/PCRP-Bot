package de.pcrp.bot.web;

import com.google.gson.*;
import de.pcrp.bot.common.*;
import io.javalin.Javalin;
import io.javalin.http.Context;
import io.javalin.http.UploadedFile;
import net.dv8tion.jda.api.entities.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;
import java.util.zip.*;

public class WebServer {

    private static final Logger log  = LoggerFactory.getLogger(WebServer.class);
    private static final Gson   GSON = new GsonBuilder().create();

    /** Letzter Fallback für API_BASE in HTML-Templates (wenn weder WEB_URL noch RAILWAY_PUBLIC_DOMAIN gesetzt sind). */
    private static final String DEFAULT_RAILWAY_URL = "pcrp-bot-production-3ad1.up.railway.app";

    private WebServer() {}

    public static void start(int port) {
        Javalin app = Javalin.create(config -> {
            config.http.maxRequestSize = 60L * 1024 * 1024; // 60 MB (5 Personen × 10 MB)
            config.requestLogger.http((ctx, ms) ->
                log.debug("[Web] {} {} → {}", ctx.method(), ctx.path(), ctx.status()));
        });

        // CORS — erlaubt Cloudflare-Workers-Domain API-Aufrufe direkt zum Railway-Backend
        app.before(ctx -> {
            String origin = ctx.header("Origin");
            if (origin != null && (origin.endsWith(".workers.dev") || origin.endsWith("railway.app"))) {
                ctx.header("Access-Control-Allow-Origin", origin);
                ctx.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
                ctx.header("Access-Control-Allow-Headers", "Content-Type, Authorization");
                ctx.header("Access-Control-Allow-Credentials", "false");
            }
        });
        app.options("/*", ctx -> ctx.status(204));

        // Public Ban-Check (CORS-enabled, von Cloudflare Worker + allen Seiten nutzbar)
        app.get("/api/web/check-banned", WebServer::handleCheckBanned);

        // Frontend
        app.get("/",                          WebServer::serveIndex);
        app.get("/ausweis/{userId}",           WebServer::serveAusweis);
        app.get("/ausweis-erstellen/{guildId}/{userId}", WebServer::serveAusweisErstellen);
        app.get("/fuehrerschein-erstellen/{guildId}/{userId}", WebServer::serveFuehrerscheinErstellen);
        app.get("/fuehrerschein/{userId}",     WebServer::serveFuehrerscheinViewer);
        app.post("/api/save-ausweis",          WebServer::handleSaveAusweis);
        app.post("/api/save-fuehrerschein",    WebServer::handleSaveFuehrerschein);
        app.get("/api/license-photo/{userId}",  ctx -> serveDocumentPhoto(ctx, "fuehrerschein"));
        app.get("/api/ausweis-photo/{userId}",  ctx -> serveDocumentPhoto(ctx, "ausweis"));

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

        // ── Penthouses (Marketing-Seite im R*-Diamond-Stil) ──────────────
        app.get( "/penthouses",                                   WebServer::servePenthouses);

        // ── Citygram / CityBuy / CityShip (statische Baustellen-Seiten) ───
        app.get( "/citygram",                                    WebServer::serveCitygram);
        app.get( "/citybuy",                                     WebServer::serveCityBuy);
        app.get( "/cityship",                                    WebServer::serveCityShip);

        // ── Regelwerk (externe Seite mit Edit-Modus) ───────────────────────
        app.get( "/regelwerk",                                  WebServer::serveRegelwerk);
        app.get( "/api/regelwerk",                              RegelwerkHandler::handleGet);
        app.post("/api/regelwerk/category",                     RegelwerkHandler::handleAddCategory);
        app.post("/api/regelwerk/category/edit",                RegelwerkHandler::handleEditCategory);
        app.post("/api/regelwerk/entry",                        RegelwerkHandler::handleAddEntry);
        app.post("/api/regelwerk/entry/edit",                   RegelwerkHandler::handleEditEntry);
        app.post("/api/regelwerk/delete",                       RegelwerkHandler::handleDelete);

        // ── LAPD (Webseite + Beamten-Dashboard) ────────────────────────────
        app.get( "/lapd",                                      WebServer::serveLapd);
        app.get( "/lapd/karriere",                             WebServer::serveLapdKarriere);
        app.get( "/lapd/anforderungen",                        WebServer::serveLapdAnforderungen);
        app.get( "/lapd/dashboard",                            WebServer::serveLapdDashboard);
        app.post("/api/lapd/create",           ctx -> LapdHandler.handleCreate(ctx));
        app.get( "/api/lapd/my",               ctx -> LapdHandler.handleMy(ctx));
        app.post("/api/lapd/reply",            ctx -> LapdHandler.handleReply(ctx));
        app.get( "/api/lapd/dashboard",        ctx -> LapdHandler.handleDashboard(ctx));
        app.post("/api/lapd/dashboard/reply",  ctx -> LapdHandler.handleDashReply(ctx));
        app.post("/api/lapd/dashboard/status", ctx -> LapdHandler.handleDashStatus(ctx));
        app.post("/api/lapd/dashboard/decide", ctx -> LapdHandler.handleDashDecide(ctx));
        app.post("/api/lapd/dashboard/delete", ctx -> LapdHandler.handleDashDelete(ctx));
        // Öffentliche LAPD-Daten (Webseite) + Einsatz-Eingang
        app.get( "/api/lapd/public",           ctx -> LapdDashHandler.handlePublic(ctx));
        app.post("/api/lapd/dispatch",         ctx -> LapdDashHandler.handleDispatchIngest(ctx));
        // LAPD-Beamten-Dashboard (extern)
        app.post("/api/lapd/dash/login",            ctx -> LapdDashHandler.handleLogin(ctx));
        app.post("/api/lapd/dash/logout",           ctx -> LapdDashHandler.handleLogout(ctx));
        app.get( "/api/lapd/dash/me",              ctx -> LapdDashHandler.handleMe(ctx));
        app.get( "/api/lapd/dash/access",          ctx -> LapdDashHandler.handleAccessList(ctx));
        app.post("/api/lapd/dash/access",          ctx -> LapdDashHandler.handleAccessAdd(ctx));
        app.post("/api/lapd/dash/access/delete",   ctx -> LapdDashHandler.handleAccessDelete(ctx));
        app.get( "/api/lapd/dash/banned",          ctx -> LapdDashHandler.handleBanList(ctx));
        app.post("/api/lapd/dash/ban",             ctx -> LapdDashHandler.handleBan(ctx));
        app.post("/api/lapd/dash/unban",           ctx -> LapdDashHandler.handleUnban(ctx));
        app.post("/api/lapd/dash/fleet",           ctx -> LapdDashHandler.handleFleetAdd(ctx));
        app.post("/api/lapd/dash/fleet/upload",    ctx -> LapdDashHandler.handleFleetUpload(ctx));
        app.post("/api/lapd/dash/fleet/delete",    ctx -> LapdDashHandler.handleFleetDelete(ctx));
        app.get( "/api/lapd/fleet-image/{id}",     WebServer::serveLapdFleetImage);
        app.get( "/api/lapd/equip-image/{id}",     WebServer::serveLapdEquipImage);
        app.get( "/api/lapd/dash/employees",       ctx -> LapdDashHandler.handleEmployeeList(ctx));
        app.post("/api/lapd/dash/employees",       ctx -> LapdDashHandler.handleEmployeeAdd(ctx));
        app.post("/api/lapd/dash/employees/edit",  ctx -> LapdDashHandler.handleEmployeeEdit(ctx));
        app.post("/api/lapd/dash/employees/delete",ctx -> LapdDashHandler.handleEmployeeDelete(ctx));
        app.post("/api/lapd/dash/warn",            ctx -> LapdDashHandler.handleWarn(ctx));
        app.post("/api/lapd/dash/warn/me",         ctx -> LapdDashHandler.handleWarnMe(ctx));
        app.post("/api/lapd/dash/fire",            ctx -> LapdDashHandler.handleFire(ctx));
        app.get( "/api/lapd/dash/vacations",       ctx -> LapdDashHandler.handleVacationList(ctx));
        app.post("/api/lapd/dash/vacation/request",ctx -> LapdDashHandler.handleVacationRequest(ctx));
        app.post("/api/lapd/dash/vacation/decide", ctx -> LapdDashHandler.handleVacationDecide(ctx));
        app.post("/api/lapd/dash/vacation/delete", ctx -> LapdDashHandler.handleVacationDelete(ctx));
        app.post("/api/lapd/dash/assign",          ctx -> LapdDashHandler.handleAssign(ctx));
        app.post("/api/lapd/dash/info",            ctx -> LapdDashHandler.handleInfoAdd(ctx));
        app.post("/api/lapd/dash/info/delete",     ctx -> LapdDashHandler.handleInfoDelete(ctx));
        app.get( "/api/lapd/dash/duty",            ctx -> LapdDashHandler.handleDutyList(ctx));
        app.post("/api/lapd/dash/duty/on",         ctx -> LapdDashHandler.handleDutyOn(ctx));
        app.post("/api/lapd/dash/duty/off",        ctx -> LapdDashHandler.handleDutyOff(ctx));
        app.get( "/api/lapd/dash/wanted",          ctx -> LapdDashHandler.handleWantedList(ctx));
        app.post("/api/lapd/dash/wanted",          ctx -> LapdDashHandler.handleWantedAdd(ctx));
        app.post("/api/lapd/dash/wanted/delete",   ctx -> LapdDashHandler.handleWantedDelete(ctx));
        app.get( "/api/lapd/dash/dispatches",      ctx -> LapdDashHandler.handleDispatchList(ctx));
        app.post("/api/lapd/dash/dispatch/accept", ctx -> LapdDashHandler.handleDispatchAccept(ctx));
        app.post("/api/lapd/dash/dispatch/report", ctx -> LapdDashHandler.handleDispatchReport(ctx));
        app.get( "/api/lapd/dash/akten",           ctx -> LapdDashHandler.handleAktenList(ctx));
        app.post("/api/lapd/dash/akte",            ctx -> LapdDashHandler.handleAkteAdd(ctx));
        app.post("/api/lapd/dash/akte/edit",       ctx -> LapdDashHandler.handleAkteEdit(ctx));
        app.post("/api/lapd/dash/akte/delete",     ctx -> LapdDashHandler.handleAkteDelete(ctx));
        app.get( "/api/lapd/dash/licenses",        ctx -> LapdDashHandler.handleLicenseList(ctx));
        app.post("/api/lapd/dash/license/revoke",  ctx -> LapdDashHandler.handleLicenseRevoke(ctx));
        app.post("/api/lapd/dash/license/return",  ctx -> LapdDashHandler.handleLicenseReturn(ctx));
        app.get( "/api/lapd/dash/equipment",       ctx -> LapdDashHandler.handleEquipmentList(ctx));
        app.post("/api/lapd/dash/equipment",       ctx -> LapdDashHandler.handleEquipmentAdd(ctx));
        app.post("/api/lapd/dash/equipment/delete",ctx -> LapdDashHandler.handleEquipmentDelete(ctx));
        app.post("/api/lapd/dash/panic",           ctx -> LapdDashHandler.handlePanic(ctx));

        // ── Krypto (PC Coins Kursseite) ────────────────────────────────────
        app.get( "/krypto",                                      WebServer::serveKrypto);
        app.get( "/api/krypto/rates",                            WebServer::handleKryptoRates);

        // ── Aktien (Aktienhandel mit PC Coins) ───────────────────────────
        app.get( "/aktien",                                      WebServer::serveAktien);
        app.post("/api/aktien/auth",                              WebServer::handleAktienAuth);
        app.get( "/api/aktien/rates",                            WebServer::handleAktienRates);
        app.post("/api/aktien/portfolio",                         WebServer::handleAktienPortfolio);
        app.post("/api/aktien/trade",                             WebServer::handleAktienTrade);

        // ── City Chat ──────────────────────────────────────────────────────
        app.get( "/city-chat",                         WebServer::serveCityChat);
        app.post("/api/city-chat/pin-verify",           ctx -> CityChatHandler.handlePinVerify(ctx));
        app.post("/api/city-chat/auth",                ctx -> CityChatHandler.handleAuth(ctx));
        app.get( "/api/city-chat/me",                  ctx -> CityChatHandler.handleGetMe(ctx));
        app.put( "/api/city-chat/me",                  ctx -> CityChatHandler.handleUpdateMe(ctx));
        app.get( "/api/city-chat/contacts",            ctx -> CityChatHandler.handleGetContacts(ctx));
        app.post("/api/city-chat/contacts",            ctx -> CityChatHandler.handleAddContact(ctx));
        app.delete("/api/city-chat/contacts/{number}", ctx -> CityChatHandler.handleDeleteContact(ctx));
        app.get( "/api/city-chat/chats",               ctx -> CityChatHandler.handleGetChats(ctx));
        app.get(   "/api/city-chat/messages/{chatId}",  ctx -> CityChatHandler.handleGetMessages(ctx));
        app.delete("/api/city-chat/messages/{chatId}", ctx -> CityChatHandler.handleClearChat(ctx));
        app.post(  "/api/city-chat/messages",          ctx -> CityChatHandler.handleSendMessage(ctx));
        app.post("/api/city-chat/block",               ctx -> CityChatHandler.handleBlock(ctx));
        app.delete("/api/city-chat/block/{number}",    ctx -> CityChatHandler.handleUnblock(ctx));
        app.get( "/api/city-chat/blocked",             ctx -> CityChatHandler.handleGetBlocked(ctx));
        app.get( "/api/city-chat/lookup",              ctx -> CityChatHandler.handleLookup(ctx));
        app.get( "/api/city-chat/statuses",            ctx -> CityChatHandler.handleGetStatuses(ctx));
        app.post("/api/city-chat/status",              ctx -> CityChatHandler.handleSetStatus(ctx));
        app.delete("/api/city-chat/status",            ctx -> CityChatHandler.handleDeleteStatus(ctx));
        // Push-Benachrichtigungen
        app.get( "/sw.js",                              WebServer::serveServiceWorker);
        app.get( "/ban-guard.js",                         ctx -> serveStaticBinary(ctx, "/static/ban-guard.js", "application/javascript"));
        app.get( "/pd-logo.webp",                       ctx -> serveStaticBinary(ctx, "/static/pd-logo.webp",      "image/webp"));
        app.get( "/lapd-logo.jpg",                      ctx -> serveStaticBinary(ctx, "/static/lapd-logo.jpg",     "image/jpeg"));
        app.get( "/pd-standort.jpg",                    ctx -> serveStaticBinary(ctx, "/static/pd-standort.jpg",   "image/jpeg"));
        app.get( "/manifest.json",                      WebServer::serveManifest);
        app.get( "/icon-192.png",                       ctx -> serveStaticBinary(ctx, "/static/icon-192.png",    "image/png"));
        app.get( "/icon-512.png",                       ctx -> serveStaticBinary(ctx, "/static/icon-512.png",    "image/png"));
        app.get( "/badge-72.png",                       ctx -> serveStaticBinary(ctx, "/static/badge-72.png",    "image/png"));
        app.get( "/cc-bg-dark.jpg",                     ctx -> serveStaticBinary(ctx, "/static/cc-bg-dark.jpg",  "image/jpeg"));
        app.get( "/cc-bg-light.jpg",                    ctx -> serveStaticBinary(ctx, "/static/cc-bg-light.jpg", "image/jpeg"));
        app.get( "/la-bg.jpg",                          ctx -> serveStaticBinary(ctx, "/static/la-bg.jpg",       "image/jpeg"));
        app.get( "/api/city-chat/vapid-public-key",     ctx -> ctx.contentType("application/json").result("{\"key\":\"" + PushService.VAPID_PUBLIC + "\"}"));
        app.post("/api/city-chat/push-subscribe",       ctx -> CityChatHandler.handlePushSubscribe(ctx));
        app.post("/api/city-chat/push-unsubscribe",     ctx -> CityChatHandler.handlePushUnsubscribe(ctx));
        app.get( "/api/city-chat/partner-profile",      ctx -> CityChatHandler.handleGetPartnerProfile(ctx));
        app.get( "/api/city-chat/firma-links",         ctx -> CityChatHandler.handleGetFirmaLinks(ctx));
        app.post("/api/city-chat/firma-links",         ctx -> CityChatHandler.handleAddFirmaLink(ctx));
        app.delete("/api/city-chat/firma-links/{id}",  ctx -> CityChatHandler.handleDeleteFirmaLink(ctx));
        app.post("/api/city-chat/call-signal",         ctx -> CityChatHandler.handleSendCallSignal(ctx));
        app.get( "/api/city-chat/call-signal",         ctx -> CityChatHandler.handleGetCallSignal(ctx));

        // Banned-Seite
        app.get("/banned", WebServer::serveBanned);

        // Admin-Backup
        app.get("/admin/backup", WebServer::handleBackup);

        // ── Premium Deluxe Motorsport (Autohaus-Webseite) ──────────────────
        app.get ("/premium-motorsport",                            PremiumMotorsportHandler::serveSite);
        app.get ("/premium-motorsport/admin",                      PremiumMotorsportHandler::serveAdmin);
        app.post("/api/pd/auth/login",                             PremiumMotorsportHandler::handleAuthLogin);
        app.get ("/api/pd/me",                                     PremiumMotorsportHandler::handleMe);
        app.get ("/api/pd/vehicles",                               PremiumMotorsportHandler::handleListVehicles);
        app.get ("/api/pd/vehicle/{id}",                           PremiumMotorsportHandler::handleGetVehicle);
        app.post("/api/pd/vehicles",                               PremiumMotorsportHandler::handleCreateVehicle);
        app.post("/api/pd/vehicles/{id}/delete",                   PremiumMotorsportHandler::handleDeleteVehicle);
        app.post("/api/pd/vehicle/{id}/buy",                       PremiumMotorsportHandler::handleBuyVehicle);
        app.get ("/api/pd/garage",                                 PremiumMotorsportHandler::handleGetGarage);
        app.post("/api/pd/garage/transfer",                        PremiumMotorsportHandler::handleTransferGarage);
        app.get ("/api/pd/info",                                   PremiumMotorsportHandler::handleListInfo);
        app.post("/api/pd/info",                                   PremiumMotorsportHandler::handleAddInfo);
        app.post("/api/pd/info/{id}/delete",                       PremiumMotorsportHandler::handleDeleteInfo);
        app.get ("/api/pd/offers",                                 PremiumMotorsportHandler::handleListOffers);
        app.post("/api/pd/offers",                                 PremiumMotorsportHandler::handleAddOffer);
        app.post("/api/pd/offers/{id}/delete",                     PremiumMotorsportHandler::handleDeleteOffer);
        app.get ("/api/pd/ticket-topics",                          PremiumMotorsportHandler::handleTicketTopics);
        app.post("/api/pd/tickets",                                PremiumMotorsportHandler::handleCreateTicket);
        app.get ("/api/pd/tickets/mine",                           PremiumMotorsportHandler::handleMyTickets);
        app.get ("/api/pd/tickets/all",                            PremiumMotorsportHandler::handleAllTickets);
        app.post("/api/pd/tickets/{id}/status",                    PremiumMotorsportHandler::handleSetTicketStatus);

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

    // ── Service Worker + Manifest + Icons ──────────────────────

    private static void serveServiceWorker(Context ctx) {
        try (var is = WebServer.class.getResourceAsStream("/static/sw.js")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            ctx.contentType("application/javascript")
               .header("Service-Worker-Allowed", "/")
               .header("Cache-Control", "no-cache")
               .result(is.readAllBytes());
        } catch (Exception e) { ctx.status(500).result("Fehler"); }
    }

    private static void serveManifest(Context ctx) {
        try (var is = WebServer.class.getResourceAsStream("/static/manifest.json")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            ctx.contentType("application/manifest+json").result(is.readAllBytes());
        } catch (Exception e) { ctx.status(500).result("Fehler"); }
    }

    private static void serveStaticBinary(Context ctx, String resourcePath, String contentType) {
        try (var is = WebServer.class.getResourceAsStream(resourcePath)) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            ctx.contentType(contentType).result(is.readAllBytes());
        } catch (Exception e) { ctx.status(500).result("Fehler"); }
    }

    // ── banned.html ────────────────────────────────────────────

    private static void serveBanned(Context ctx) {
        try (var is = WebServer.class.getResourceAsStream("/static/banned.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── citygram.html ──────────────────────────────────────────

    // ── penthouses.html ─────────────────────────────────────────────

    private static void servePenthouses(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/penthouses.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
            log.info("[Penthouses] Marketing-Seite ausgeliefert.");
        } catch (Exception e) {
            log.error("[Penthouses] Fehler beim Ausliefern.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    private static void serveCitygram(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/citygram.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            log.info("[Citygram] Baustellen-Seite ausgeliefert.");
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            log.error("[Citygram] Fehler beim Ausliefern.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    private static void serveCityBuy(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/citybuy.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            log.info("[CityBuy] Baustellen-Seite ausgeliefert.");
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            log.error("[CityBuy] Fehler beim Ausliefern.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    private static void serveCityShip(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/cityship.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            log.info("[CityShip] Baustellen-Seite ausgeliefert.");
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            log.error("[CityShip] Fehler beim Ausliefern.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── regelwerk.html (Serverregelwerk mit Edit-Modus) ────────

    private static void serveRegelwerk(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/regelwerk.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            log.info("[Regelwerk] Seite ausgeliefert.");
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            log.error("[Regelwerk] Fehler beim Ausliefern.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── krypto.html (PC Coins Kursseite) ───────────────────────

    private static void serveKrypto(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/krypto.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            log.info("[Krypto] Kursseite ausgeliefert.");
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(is.readAllBytes());
        } catch (Exception e) {
            log.error("[Krypto] Fehler beim Ausliefern.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    /** GET /api/krypto/rates – aktueller Kurs, Umlauf und 7-Tage-Historie. */
    private static void handleKryptoRates(Context ctx) {
        JsonObject out = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            out.addProperty("ok", false);
            out.addProperty("error", "Server nicht bereit.");
            ctx.contentType("application/json").result(GSON.toJson(out));
            return;
        }
        String guildId = guild.getId();
        out.addProperty("ok", true);
        out.addProperty("rate", KryptoManager.getRate(guildId));
        out.addProperty("supply", KryptoManager.getSupply(guildId));

        JsonArray hist = new JsonArray();
        for (KryptoManager.RatePoint p : KryptoManager.readHistory(guildId)) {
            JsonObject o = new JsonObject();
            o.addProperty("ts", p.ts);
            o.addProperty("rate", p.rate);
            hist.add(o);
        }
        out.add("history", hist);
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    // ── lapd.html (LAPD-Webseite) ───────────────────────────────

    private static void serveLapd(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/lapd.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            String base = System.getenv("WEB_URL");
            if (base == null || base.isBlank()) {
                base = System.getenv().getOrDefault("RAILWAY_PUBLIC_DOMAIN", DEFAULT_RAILWAY_URL);
                if (!base.startsWith("http")) base = "https://" + base;
            }
            base = base.replaceAll("/$", "");
            String html = new String(is.readAllBytes(), StandardCharsets.UTF_8)
                .replace("%%API_BASE%%", base);
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(html.getBytes(StandardCharsets.UTF_8));
            log.info("[LAPD] Webseite ausgeliefert.");
        } catch (Exception e) {
            log.error("[LAPD] Fehler beim Ausliefern.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── lapd-karriere.html (Bewerbungsportal) ──────────────────

    private static void serveLapdKarriere(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/lapd-karriere.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            String base = System.getenv("WEB_URL");
            if (base == null || base.isBlank()) {
                base = System.getenv().getOrDefault("RAILWAY_PUBLIC_DOMAIN", DEFAULT_RAILWAY_URL);
                if (!base.startsWith("http")) base = "https://" + base;
            }
            base = base.replaceAll("/$", "");
            String html = new String(is.readAllBytes(), StandardCharsets.UTF_8)
                .replace("%%API_BASE%%", base);
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(html.getBytes(StandardCharsets.UTF_8));
            log.info("[LAPD] Bewerbungsportal ausgeliefert.");
        } catch (Exception e) {
            log.error("[LAPD] Fehler beim Ausliefern des Bewerbungsportals.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── lapd-dashboard.html (Beamten-Dashboard, extern) ────────

    private static void serveLapdDashboard(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/lapd-dashboard.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            String base = System.getenv("WEB_URL");
            if (base == null || base.isBlank()) {
                base = System.getenv().getOrDefault("RAILWAY_PUBLIC_DOMAIN", DEFAULT_RAILWAY_URL);
                if (!base.startsWith("http")) base = "https://" + base;
            }
            base = base.replaceAll("/$", "");
            String html = new String(is.readAllBytes(), StandardCharsets.UTF_8)
                .replace("%%API_BASE%%", base);
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(html.getBytes(StandardCharsets.UTF_8));
            log.info("[LAPD] Beamten-Dashboard ausgeliefert.");
        } catch (Exception e) {
            log.error("[LAPD] Fehler beim Ausliefern des Dashboards.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── lapd-anforderungen.html (Karriere-Anforderungen) ───────

    private static void serveLapdAnforderungen(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/lapd-anforderungen.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            String base = System.getenv("WEB_URL");
            if (base == null || base.isBlank()) {
                base = System.getenv().getOrDefault("RAILWAY_PUBLIC_DOMAIN", DEFAULT_RAILWAY_URL);
                if (!base.startsWith("http")) base = "https://" + base;
            }
            base = base.replaceAll("/$", "");
            String html = new String(is.readAllBytes(), StandardCharsets.UTF_8)
                .replace("%%API_BASE%%", base);
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(html.getBytes(StandardCharsets.UTF_8));
            log.info("[LAPD] Anforderungsseite ausgeliefert.");
        } catch (Exception e) {
            log.error("[LAPD] Fehler beim Ausliefern der Anforderungsseite.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    // ── aktien.html (Aktienhandel) ─────────────────────────────

    private static void serveAktien(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/aktien.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            String base = System.getenv("WEB_URL");
            if (base == null || base.isBlank()) {
                base = System.getenv().getOrDefault("RAILWAY_PUBLIC_DOMAIN", DEFAULT_RAILWAY_URL);
                if (!base.startsWith("http")) base = "https://" + base;
            }
            base = base.replaceAll("/$", "");
            String html = new String(is.readAllBytes(), StandardCharsets.UTF_8)
                .replace("%%API_BASE%%", base);
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(html.getBytes(StandardCharsets.UTF_8));
            log.info("[Aktien] Aktien-Seite ausgeliefert.");
        } catch (Exception e) {
            log.error("[Aktien] Fehler beim Ausliefern.", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    /** POST /api/aktien/auth – Safe-PIN einloggen, Session-Token ausstellen. */
    private static void handleAktienAuth(Context ctx) {
        JsonObject out = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            out.addProperty("ok", false); out.addProperty("error", "Server nicht bereit.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        JsonObject body;
        try { body = GSON.fromJson(ctx.body(), JsonObject.class); }
        catch (Exception e) {
            out.addProperty("ok", false); out.addProperty("error", "Ungültige Anfrage.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        String pin = body != null && body.has("safePin") ? body.get("safePin").getAsString().trim() : "";
        if (pin.isEmpty()) {
            out.addProperty("ok", false); out.addProperty("error", "Bitte gib deine Safe-PIN ein.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        PhoneManager.Contract c = PhoneManager.getContractByPin(guild.getId(), pin);
        if (c == null) {
            out.addProperty("ok", false); out.addProperty("error", "Ungültige Safe-PIN.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        // Web-Bann prüfen – gesperrte Personen können sich nicht einloggen
        if (DataStore.isWebBanned(guild.getId(), c.userId)) {
            out.addProperty("ok", false); out.addProperty("banned", true);
            out.addProperty("error", "Dein Zugriff wurde von einem Administrator gesperrt. Sollte das ein Fehler sein, wende dich bitte an das High Team im Discord.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        String token = PhoneManager.createSession(guild.getId(), c.phoneNumber);
        out.addProperty("ok", true);
        out.addProperty("token", token);
        out.addProperty("name", c.displayName());
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    /** GET /api/aktien/rates – alle Aktien: Kurs, Umlauf, 7-Tage-Historie. */
    private static void handleAktienRates(Context ctx) {
        JsonObject out = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            out.addProperty("ok", false); out.addProperty("error", "Server nicht bereit.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        String guildId = guild.getId();
        JsonArray stocks = new JsonArray();
        for (AktienManager.Aktie a : AktienManager.STOCKS) {
            JsonObject o = new JsonObject();
            o.addProperty("id", a.id());
            o.addProperty("name", a.name());
            o.addProperty("emoji", a.emoji());
            o.addProperty("rate", AktienManager.getRate(a, guildId));
            o.addProperty("supply", AktienManager.getSupply(a.id(), guildId));
            JsonArray hist = new JsonArray();
            for (AktienManager.RatePoint p : AktienManager.readHistory(a.id(), guildId)) {
                JsonObject h = new JsonObject();
                h.addProperty("ts", p.ts);
                h.addProperty("rate", p.rate);
                hist.add(h);
            }
            o.add("history", hist);
            stocks.add(o);
        }
        out.addProperty("ok", true);
        out.add("stocks", stocks);
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    /** POST /api/aktien/portfolio – eigene Aktien, Gewinn/Verlust. */
    private static void handleAktienPortfolio(Context ctx) {
        JsonObject out = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            out.addProperty("ok", false); out.addProperty("error", "Server nicht bereit.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        JsonObject body;
        try { body = GSON.fromJson(ctx.body(), JsonObject.class); }
        catch (Exception e) {
            out.addProperty("ok", false); out.addProperty("error", "Ungültige Anfrage.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        String token = body != null && body.has("token") ? body.get("token").getAsString() : "";
        PhoneManager.Contract c = PhoneManager.validateSession(token);
        if (c == null || c.userId == null) {
            out.addProperty("ok", false); out.addProperty("error", "Ungültige Sitzung.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        String guildId = guild.getId();
        String userId  = c.userId;

        // Web-Bann prüfen
        if (DataStore.isWebBanned(guildId, userId)) {
            out.addProperty("ok", false); out.addProperty("banned", true);
            out.addProperty("error", "Dein Zugriff wurde von einem Administrator gesperrt. Sollte das ein Fehler sein, wende dich bitte an das High Team im Discord.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }

        long totalValue = 0, totalInvested = 0;
        JsonArray portfolio = new JsonArray();
        for (AktienManager.Aktie a : AktienManager.STOCKS) {
            long shares = AktienManager.getShares(a.id(), guildId, userId);
            long invested = AktienManager.getInvested(a.id(), guildId, userId);
            long value = Math.round(shares * AktienManager.getRate(a, guildId));
            totalValue += value;
            totalInvested += invested;
            JsonObject o = new JsonObject();
            o.addProperty("id", a.id());
            o.addProperty("shares", shares);
            o.addProperty("invested", invested);
            o.addProperty("value", value);
            portfolio.add(o);
        }
        out.addProperty("ok", true);
        out.addProperty("name", c.displayName());
        out.addProperty("wallet", KryptoManager.getBalance(guildId, userId));
        out.addProperty("totalValue", totalValue);
        out.addProperty("totalInvested", totalInvested);
        out.addProperty("totalProfit", totalValue - totalInvested);
        out.add("portfolio", portfolio);
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    /** POST /api/aktien/trade – Aktien kaufen/verkaufen mit PC Coins. */
    private static void handleAktienTrade(Context ctx) {
        JsonObject out = new JsonObject();
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            out.addProperty("ok", false); out.addProperty("error", "Server nicht bereit.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        JsonObject body;
        try { body = GSON.fromJson(ctx.body(), JsonObject.class); }
        catch (Exception e) {
            out.addProperty("ok", false); out.addProperty("error", "Ungültige Anfrage.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        String token   = body != null && body.has("token")   ? body.get("token").getAsString()   : "";
        String stockId = body != null && body.has("stockId") ? body.get("stockId").getAsString() : "";
        String action  = body != null && body.has("action")  ? body.get("action").getAsString()  : "";
        long amount    = body != null && body.has("amount")  ? body.get("amount").getAsLong()    : 0;

        PhoneManager.Contract c = PhoneManager.validateSession(token);
        if (c == null || c.userId == null) {
            out.addProperty("ok", false); out.addProperty("error", "Ungültige Sitzung.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }

        // Web-Bann prüfen – gesperrte Personen dürfen nicht handeln
        String guildId = guild.getId();
        if (DataStore.isWebBanned(guildId, c.userId)) {
            out.addProperty("ok", false); out.addProperty("banned", true);
            out.addProperty("error", "Dein Zugriff wurde von einem Administrator gesperrt. Sollte das ein Fehler sein, wende dich bitte an das High Team im Discord.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }

        AktienManager.Aktie stock = AktienManager.findStock(stockId);
        if (stock == null) {
            out.addProperty("ok", false); out.addProperty("error", "Unbekannte Aktie.");
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }

        String userId  = c.userId;
        String error   = null;
        if ("buy".equals(action)) {
            error = AktienManager.buy(guildId, userId, stockId, amount);
            if (error == null) {
                logTrade(guild, c, stock, "gekauft", amount + " PC", AktienManager.getShares(stockId, guildId, userId));
            }
        } else if ("sell".equals(action)) {
            error = AktienManager.sell(guildId, userId, stockId, amount);
            if (error == null) {
                logTrade(guild, c, stock, "verkauft", amount + " Aktien", AktienManager.getShares(stockId, guildId, userId));
            }
        } else {
            error = "Ungültige Aktion.";
        }

        if (error != null) {
            out.addProperty("ok", false); out.addProperty("error", error);
            ctx.contentType("application/json").result(GSON.toJson(out)); return;
        }
        out.addProperty("ok", true);
        out.addProperty("wallet", KryptoManager.getBalance(guildId, userId));
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    /** Loggt Aktien-Kauf/-Verkauf in den Geld-Log-Kanal (wie Konto/Bargeld/Krypto). */
    private static void logTrade(Guild guild, PhoneManager.Contract c,
                                 AktienManager.Aktie stock, String verb,
                                 String menge, long newShares) {
        try {
            net.dv8tion.jda.api.entities.Member m = guild.getMemberById(c.userId);
            String who = m != null ? m.getAsMention() : "<@" + c.userId + ">";
            BotLogger.logMoney(guild, stock.emoji() + " " + stock.name() + " — Aktie " + verb,
                "**Spieler:** " + who + "\n" +
                "**Menge:** " + menge + "\n" +
                "**Neuer Bestand:** " + AktienManager.formatShares(newShares));
        } catch (Exception e) {
            log.error("[Aktien] Log fehlgeschlagen.", e);
        }
    }

    // ── city-chat.html ─────────────────────────────────────────

    private static void serveCityChat(Context ctx) {
        try (InputStream is = WebServer.class.getResourceAsStream("/static/city-chat.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            // API_BASE = Cloudflare-URL (WEB_URL), damit alle API-Aufrufe über Cloudflare laufen
            String base = System.getenv("WEB_URL");
            if (base == null || base.isBlank()) {
                base = System.getenv().getOrDefault("RAILWAY_PUBLIC_DOMAIN",
                    "pcrp-bot-production-3ad1.up.railway.app");
                if (!base.startsWith("http")) base = "https://" + base;
            }
            base = base.replaceAll("/$", "");
            String html = new String(is.readAllBytes(), StandardCharsets.UTF_8)
                .replace("%%API_BASE%%", base);
            // Cache-Headers setzen, damit nach unseren UI-Fixes nichts gecacht wird
            ctx.header("Cache-Control", "no-cache, no-store, must-revalidate");
            ctx.header("Pragma", "no-cache");
            ctx.header("Expires", "0");
            ctx.contentType("text/html;charset=utf-8").result(html.getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            log.error("[CityChat] Fehler beim Ausliefern.", e);
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

    // ── LAPD-Dashboard-Bilder (Fahrzeug / Ausrüstung) ────────────────────────

    private static void serveLapdFleetImage(Context ctx) {
        serveLapdImage(ctx, "fleet-" + ctx.pathParam("id"));
    }

    private static void serveLapdEquipImage(Context ctx) {
        serveLapdImage(ctx, "equip-" + ctx.pathParam("id"));
    }

    private static void serveLapdImage(Context ctx, String base) {
        for (String ext : List.of(".jpg", ".png")) {
            Path p = DataStore.getPath("photos").resolve(base + ext);
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
        ctx.status(404).result("Kein Bild.");
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
          .append("<title>PCRP Lotto</title><script src='/ban-guard.js'></script><style>").append(CSS).append("</style></head><body>")
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
            "<script src='/ban-guard.js'></script>" +
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
            // Rubbellos-Scratch Verbesserungen (Layout)
            ".hint-strip{background:linear-gradient(90deg,#1a0d00,#3a2200,#1a0d00);" +
            "padding:9px 14px;display:flex;align-items:center;justify-content:space-between;" +
            "border-top:2px solid #6b3e00;border-bottom:1px solid #6b3e00;" +
            "background-image:radial-gradient(circle at 18% 50%,rgba(255,200,0,.10),transparent 70%)}" +
            ".hint-strip .hnt{color:#ffd34d;font-size:.78rem;font-weight:800;letter-spacing:1px;font-family:'Segoe UI',sans-serif;text-shadow:0 1px 0 rgba(0,0,0,.6)}" +
            ".hint-strip .p-text{color:#ffd34d;font-size:.66rem;letter-spacing:1.5px;font-family:'Segoe UI',sans-serif;font-weight:700;background:rgba(0,0,0,.45);padding:3px 9px;border-radius:11px;border:1px solid #6b3e00}" +
            ".tools{background:linear-gradient(180deg,#0c0700,#1a0f00);padding:8px 12px;display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #6b3e00}" +
            ".tools .prob{color:#b8860b;font-size:.62rem;letter-spacing:2px;font-weight:800;font-family:'Segoe UI',sans-serif}" +
            ".auto-rev{background:linear-gradient(180deg,#c07000 0%,#8b5e00 50%,#c07000 100%);border:1px solid #d49000;color:#fff5d3;" +
            "font-size:.6rem;font-weight:800;letter-spacing:1.5px;padding:7px 12px;border-radius:6px;cursor:pointer;" +
            "font-family:'Segoe UI',sans-serif;text-transform:uppercase;transition:transform .15s,opacity .15s,box-shadow .15s;" +
            "text-shadow:1px 1px 0 rgba(60,30,0,.6)}" +
            ".auto-rev:hover{transform:translateY(-1px);opacity:.95;box-shadow:0 3px 10px rgba(255,180,0,.3)}" +
            ".auto-rev:active{transform:translateY(0);opacity:.85}" +
            ".wl-glow{position:absolute;inset:0;border-radius:6px;pointer-events:none;" +
            "box-shadow:0 0 24px rgba(255,210,80,.7),inset 0 0 12px rgba(255,210,80,.4);" +
            "animation:glow 1.4s ease-in-out infinite}" +
            "@keyframes glow{0%,100%{opacity:.7}50%{opacity:1}}" +
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
            // Neue Rubbellos-Scratch UI: Hint-Strip + Tools (Aufdecken-Button)
            "<div class='hint-strip'><span class='hnt'>👉 Rubbel die Goldfolie mit Maus oder Finger frei 👈</span>" +
            "<span class='p-text' id='p-text'>0% freigerubbelt</span></div>" +
            "<div class='tools'><span class='prob'>3 GLEICHE BETRÄGE = SOFORTIGER GEWINN</span>" +
            "<button class='auto-rev' onclick='autoReveal()'>🎫 Schnell aufdecken</button></div>" +
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
            "const dpr0=window.devicePixelRatio||1;cv.width=Math.round(W*dpr0);cv.height=Math.round(H*dpr0);" +
            "const ctx=cv.getContext('2d');ctx.scale(dpr0,dpr0);" +
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
"const cv=document.getElementById('cc'+i);" +
"const d=ctx.getImageData(0,0,cv.width,cv.height).data;" +
            "let tot=0,clr=0;for(let j=3;j<d.length;j+=4){tot++;if(d[j]<64)clr++;}" +
"if(clr/tot>.32){rev[i]=true;cv.classList.add('rev');updateProgress();" +
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
            // Neue Rubbellos-Scratch Effekte: Audio + Haptik + Fortschritt + Auto-Aufdecken + Resize
            "let auctx=null;" +
            "function playSc(){try{if(navigator.vibrate)navigator.vibrate(6);" +
            "if(!auctx)auctx=new (window.AudioContext||window.webkitAudioContext)();" +
            "if(!auctx)return;if(auctx.state==='suspended')auctx.resume();" +
            "const len=auctx.sampleRate*0.012;const buf=auctx.createBuffer(1,len,auctx.sampleRate);" +
            "const dat=buf.getChannelData(0);for(let i=0;i<len;i++)dat[i]=Math.random()*2-1;" +
            "const src=auctx.createBufferSource();src.buffer=buf;" +
            "const lp=auctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=1800;" +
            "const gn=auctx.createGain();gn.gain.value=0.05;" +
            "src.connect(lp);lp.connect(gn);gn.connect(auctx.destination);src.start();}catch(e){}}" +
            "function updateProgress(){try{const cvs=document.querySelectorAll('.sc');" +
            "let pct=0;cvs.forEach(cv=>{if(cv.classList.contains('rev'))pct+=100/9;});" +
            "const txt=document.getElementById('p-text');if(txt)txt.textContent=Math.min(99,Math.round(pct))+'% freigerubbelt';}catch(e){}}" +
            "function autoReveal(){document.querySelectorAll('.sc').forEach(cv=>{" +
            "if(!cv.classList.contains('rev')){cv.classList.add('rev');cv.style.transition='opacity 0.5s';cv.style.opacity='0';" +
            "setTimeout(()=>{cv.style.display='none';},520);}});setTimeout(()=>{if(typeof checkAll==='function')checkAll();},620);}" +
            "addEventListener('resize',()=>{if(typeof initC==='function')document.querySelectorAll('.sc').forEach(cv=>{if(!cv.classList.contains('rev'))initC(parseInt(cv.id.slice(2)));});});" +
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
            "<script src='/ban-guard.js'></script>" +
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
            "<script src='/ban-guard.js'></script>" +
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
            // Rubbellos-Scratch Verbesserungen (Layout)
            ".hint-strip{background:linear-gradient(90deg,#1a0d00,#3a2200,#1a0d00);" +
            "padding:9px 14px;display:flex;align-items:center;justify-content:space-between;" +
            "border-top:2px solid #6b3e00;border-bottom:1px solid #6b3e00;" +
            "background-image:radial-gradient(circle at 18% 50%,rgba(255,200,0,.10),transparent 70%)}" +
            ".hint-strip .hnt{color:#ffd34d;font-size:.78rem;font-weight:800;letter-spacing:1px;font-family:'Segoe UI',sans-serif;text-shadow:0 1px 0 rgba(0,0,0,.6)}" +
            ".hint-strip .p-text{color:#ffd34d;font-size:.66rem;letter-spacing:1.5px;font-family:'Segoe UI',sans-serif;font-weight:700;background:rgba(0,0,0,.45);padding:3px 9px;border-radius:11px;border:1px solid #6b3e00}" +
            ".tools{background:linear-gradient(180deg,#0c0700,#1a0f00);padding:8px 12px;display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #6b3e00}" +
            ".tools .prob{color:#b8860b;font-size:.62rem;letter-spacing:2px;font-weight:800;font-family:'Segoe UI',sans-serif}" +
            ".auto-rev{background:linear-gradient(180deg,#c07000 0%,#8b5e00 50%,#c07000 100%);border:1px solid #d49000;color:#fff5d3;" +
            "font-size:.6rem;font-weight:800;letter-spacing:1.5px;padding:7px 12px;border-radius:6px;cursor:pointer;" +
            "font-family:'Segoe UI',sans-serif;text-transform:uppercase;transition:transform .15s,opacity .15s,box-shadow .15s;" +
            "text-shadow:1px 1px 0 rgba(60,30,0,.6)}" +
            ".auto-rev:hover{transform:translateY(-1px);opacity:.95;box-shadow:0 3px 10px rgba(255,180,0,.3)}" +
            ".auto-rev:active{transform:translateY(0);opacity:.85}" +
            ".wl-glow{position:absolute;inset:0;border-radius:6px;pointer-events:none;" +
            "box-shadow:0 0 24px rgba(255,210,80,.7),inset 0 0 12px rgba(255,210,80,.4);" +
            "animation:glow 1.4s ease-in-out infinite}" +
            "@keyframes glow{0%,100%{opacity:.7}50%{opacity:1}}" +
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
            // Neue Rubbellos-Scratch UI: Hint-Strip + Tools (Aufdecken-Button)
            "<div class='hint-strip'><span class='hnt'>👉 Rubbel die Goldfolie mit Maus oder Finger frei 👈</span>" +
            "<span class='p-text' id='p-text'>0% freigerubbelt</span></div>" +
            "<div class='tools'><span class='prob'>3 GLEICHE BETRÄGE = SOFORTIGER GEWINN</span>" +
            "<button class='auto-rev' onclick='autoReveal()'>🎫 Schnell aufdecken</button></div>" +
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
            "const dpr0=window.devicePixelRatio||1;cv.width=Math.round(W*dpr0);cv.height=Math.round(H*dpr0);" +
            "const ctx=cv.getContext('2d');ctx.scale(dpr0,dpr0);" +
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
"const cv=document.getElementById('cc'+i);" +
"const d=ctx.getImageData(0,0,cv.width,cv.height).data;" +
            "let tot=0,clr=0;for(let j=3;j<d.length;j+=4){tot++;if(d[j]<64)clr++;}" +
"if(clr/tot>.32){rev[i]=true;cv.classList.add('rev');updateProgress();" +
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
            "let auctx=null;" +
            "function playSc(){try{if(navigator.vibrate)navigator.vibrate(6);" +
            "if(!auctx)auctx=new (window.AudioContext||window.webkitAudioContext)();" +
            "if(!auctx)return;if(auctx.state==='suspended')auctx.resume();" +
            "const len=auctx.sampleRate*0.012;const buf=auctx.createBuffer(1,len,auctx.sampleRate);" +
            "const dat=buf.getChannelData(0);for(let i=0;i<len;i++)dat[i]=Math.random()*2-1;" +
            "const src=auctx.createBufferSource();src.buffer=buf;" +
            "const lp=auctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=1800;" +
            "const gn=auctx.createGain();gn.gain.value=0.05;" +
            "src.connect(lp);lp.connect(gn);gn.connect(auctx.destination);src.start();}catch(e){}}" +
            "function updateProgress(){try{const cvs=document.querySelectorAll('.sc');" +
            "let pct=0;cvs.forEach(cv=>{if(cv.classList.contains('rev'))pct+=100/9;});" +
            "const txt=document.getElementById('p-text');if(txt)txt.textContent=Math.min(99,Math.round(pct))+'% freigerubbelt';}catch(e){}}" +
            "function autoReveal(){document.querySelectorAll('.sc').forEach(cv=>{" +
            "if(!cv.classList.contains('rev')){cv.classList.add('rev');cv.style.transition='opacity 0.5s';cv.style.opacity='0';" +
            "setTimeout(()=>{cv.style.display='none';},520);}});setTimeout(()=>{if(typeof checkAll==='function')checkAll();},620);}" +
            "addEventListener('resize',()=>{if(typeof initC==='function')document.querySelectorAll('.sc').forEach(cv=>{if(!cv.classList.contains('rev'))initC(parseInt(cv.id.slice(2)));});});" +
            "</script></body></html>";
    }

    private static String fmtCell(int v) {
        if (v == 0) return "Niete";
        return String.format("%,d$", v).replace(',', '.');
    }

    // ── /api/web/check-banned?userId=X ───────────────────────
    // Öffentlicher CORS-Endpoint. Wird von Cloudflare-Worker-Seiten
    // und allen internen Seiten aufgerufen, um den Bann-Status zu prüfen.

    private static void handleCheckBanned(Context ctx) {
        ctx.header("Access-Control-Allow-Origin", "*");
        ctx.header("Access-Control-Allow-Headers", "*");
        String userId = ctx.queryParam("userId");
        String guildId = ctx.queryParam("guildId");
        JsonObject out = new JsonObject();
        out.addProperty("banned", false);
        if (userId != null && !userId.isBlank()) {
            Guild g = guildId != null ? BotContext.getJda().getGuildById(guildId) : BotContext.getGuild();
            if (g != null) {
                String key = "web-ban-" + g.getId() + "-" + userId.trim();
                String v = DataStore.readString(key);
                out.addProperty("banned", "1".equals(v));
            }
        }
        ctx.json(out);
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

    private static String buildLicenseRevokedPage(String name, String avatarUrl) {
        return "<!DOCTYPE html><html lang='de'><head><meta charset='UTF-8'>" +
            "<meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>Führerschein – " + esc(name) + "</title>" +
            "<style>*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:linear-gradient(135deg,#160a0a,#1a0f0f);" +
            "font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;padding:20px}" +
            ".card{width:100%;max-width:420px;background:#2a0d0d;border:2px solid #c0392b;" +
            "border-radius:14px;padding:40px;text-align:center;box-shadow:0 0 40px rgba(192,57,43,.3)}" +
            "img{width:80px;height:80px;border-radius:50%;border:3px solid #c0392b;margin-bottom:16px}" +
            "h2{color:#e74c3c;font-size:1.4rem;margin-bottom:10px}" +
            "p{color:#cbb;font-size:.9rem;line-height:1.6}" +
            "</style></head><body>" +
            "<div class='card'>" +
            (avatarUrl.isEmpty() ? "" : "<img src='" + esc(avatarUrl) + "' alt='Avatar'>") +
            "<h2>🚫 Führerschein entzogen</h2>" +
            "<p><b>" + esc(name) + "</b><br><br>" +
            "Der Führerschein dieser Person wurde entzogen und ist bis auf Weiteres ungültig.<br><br>" +
            "Bei Fragen wende dich bitte an das LAPD.</p>" +
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
        String idNum = "LA-" + userId.substring(Math.max(0, userId.length() - 8)).toUpperCase();

        return "<!DOCTYPE html><html lang=\"de\"><head>" +
            "<meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">" +
            "<title>Ausweis – " + esc(fn) + " " + esc(ln) + "</title>" +
            "<style>*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;display:flex;align-items:center;justify-content:center;" +
            "background:linear-gradient(135deg,#0a0a0a 0%,#0f0f1a 100%);" +
            "font-family:'Courier New',monospace;padding:16px;}" +
            ".card{width:100%;max-width:380px;background:linear-gradient(135deg,#0d2346 0%,#081830 100%);" +
            "border:3px solid #c8a048;border-radius:14px;overflow:hidden;box-shadow:0 0 40px rgba(200,160,72,0.3);}" +
            ".header{background:linear-gradient(90deg,#0a1c38,#0d2550);border-bottom:3px solid #c8a048;" +
            "padding:14px 20px;display:flex;align-items:center;gap:16px;}" +
            ".header-text{flex:1;}" +
            ".header-text .state{display:block;color:#c8a048;font-size:1.3rem;font-weight:700;letter-spacing:4px;}" +
            ".header-text .city{display:block;color:#a8c4e0;font-size:0.75rem;letter-spacing:2px;margin-top:2px;}" +
            ".body{display:flex;flex-direction:column;}" +
            ".photo-col{width:100%;min-height:auto;background:#06111f;display:flex;" +
            "align-items:center;justify-content:center;border-bottom:2px solid #c8a04840;padding:20px;}" +
            ".photo-col img{width:140px;height:175px;object-fit:cover;object-position:top center;" +
            "border:2px solid #c8a048;border-radius:4px;display:block;}" +
            ".no-photo{width:140px;height:175px;display:flex;align-items:center;justify-content:center;" +
            "background:#0a1825;border:2px solid #c8a04860;border-radius:4px;color:#445;font-size:0.7rem;text-align:center;}" +
            ".data-col{width:100%;padding:20px;}" +
            ".id-num{color:#c8a048;font-size:0.7rem;letter-spacing:2px;margin-bottom:14px;text-align:center;}" +
            ".field{margin-bottom:12px;}.field label{display:block;color:#6a8fb0;font-size:0.6rem;" +
            "letter-spacing:2px;text-transform:uppercase;margin-bottom:2px;}" +
            ".field .val{color:#e8e8e8;font-size:0.95rem;font-weight:700;letter-spacing:1px;}" +
            ".fields-grid{display:grid;grid-template-columns:1fr;gap:6px 0;}" +
            ".footer{background:#06111f;border-top:2px solid #c8a04840;padding:10px 20px;" +
            "display:flex;justify-content:center;align-items:center;}" +
            ".footer .seal{color:#c8a04880;font-size:0.65rem;letter-spacing:1px;text-align:center;}" +
            "</style></head><body>" +
            "<div class=\"card\"><div class=\"header\">" +
            "<div class=\"header-text\"><span class=\"state\">CALIFORNIA</span>" +
            "<span class=\"city\">CITY OF LOS ANGELES · PARADISE CITY ROLEPLAY</span></div>" +
            "</div>" +
            "<div class=\"body\"><div class=\"photo-col\">" +
            "<img src=\"/api/photo/" + userId + "\" onerror=\"this.outerHTML='<div class=no-photo>Kein Foto</div>'\">" +
            "</div><div class=\"data-col\"><div class=\"id-num\">ID-NR: " + esc(idNum) + "</div>" +
            "<div class=\"fields-grid\">" +
            field("Vorname", fn) + field("Nachname", ln) +
            (isLegal ? field("Geburtsdatum", bd) + field("Geburtsort", bp) + field("Nationalität", na) + field("Wohnort", re) : "") +
            "</div></div></div>" +
            "<div class=\"footer\"><span class=\"seal\">STATE OF CALIFORNIA · OFFICIAL IDENTIFICATION</span>" +
            "</div></div></body></html>";
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
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("\"", "&quot;").replace("'", "&#39;");
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

    // ── Admin-Backup (/admin/backup?key=…) ───────────────────────────────────

    private static void handleBackup(Context ctx) {
        String expected = System.getenv("SESSION_SECRET");
        String provided = ctx.queryParam("key");
        if (expected == null || !expected.equals(provided)) {
            ctx.status(403).result("Forbidden");
            return;
        }
        Path dataDir = Path.of("/app/data");
        if (!Files.exists(dataDir)) {
            ctx.status(404).result("Kein /app/data Verzeichnis gefunden.");
            return;
        }
        try {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            try (ZipOutputStream zip = new ZipOutputStream(baos)) {
                Files.walk(dataDir).filter(Files::isRegularFile).forEach(file -> {
                    try {
                        ZipEntry entry = new ZipEntry(dataDir.relativize(file).toString());
                        zip.putNextEntry(entry);
                        Files.copy(file, zip);
                        zip.closeEntry();
                    } catch (IOException e) {
                        log.warn("[Backup] Fehler beim Zippen von {}: {}", file, e.getMessage());
                    }
                });
            }
            byte[] zipBytes = baos.toByteArray();
            ctx.contentType("application/zip")
               .header("Content-Disposition", "attachment; filename=\"pcrp-backup.zip\"")
               .result(new ByteArrayInputStream(zipBytes));
            log.info("[Backup] Backup heruntergeladen — {} Bytes.", zipBytes.length);
        } catch (IOException e) {
            log.error("[Backup] Fehler: {}", e.getMessage());
            ctx.status(500).result("Fehler beim Erstellen des Backups.");
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    //  AUSWEIS + FUEHRERSCHEIN — Erstellen, Anzeigen, Speichern
    //  (Nutzt DocumentsManager; CharacterStore-Ausweis bleibt der alte Pfad)
    // ═══════════════════════════════════════════════════════════════════════════

    private static void serveAusweisErstellen(Context ctx) {
        Guild guild = BotContext.getGuild();
        if (guild == null) { ctx.status(503).html("<h1>Bot nicht bereit.</h1>"); return; }
        String guildId = ctx.pathParam("guildId");
        String userId  = ctx.pathParam("userId");
        if (!guildId.equals(guild.getId())) { ctx.status(403).html("<h1>Falscher Server.</h1>"); return; }
        if (DataStore.isWebBanned(guildId, userId)) { ctx.redirect("/banned"); return; }
        Member target = guild.getMemberById(userId);
        if (target == null) { ctx.status(404).html("<h1>Mitglied nicht gefunden.</h1>"); return; }
        ctx.contentType("text/html;charset=utf-8")
           .result(buildAusweisFormHtml(guildId, userId, target.getEffectiveName(), target.getUser().getEffectiveAvatarUrl()));
    }

    private static void serveFuehrerscheinErstellen(Context ctx) {
        Guild guild = BotContext.getGuild();
        if (guild == null) { ctx.status(503).html("<h1>Bot nicht bereit.</h1>"); return; }
        String guildId = ctx.pathParam("guildId");
        String userId  = ctx.pathParam("userId");
        if (!guildId.equals(guild.getId())) { ctx.status(403).html("<h1>Falscher Server.</h1>"); return; }
        if (DataStore.isWebBanned(guildId, userId)) { ctx.redirect("/banned"); return; }
        Member target = guild.getMemberById(userId);
        if (target == null) { ctx.status(404).html("<h1>Mitglied nicht gefunden.</h1>"); return; }
        ctx.contentType("text/html;charset=utf-8")
           .result(buildFuehrerscheinFormHtml(guildId, userId, target.getEffectiveName(), target.getUser().getEffectiveAvatarUrl()));
    }

    private static void serveFuehrerscheinViewer(Context ctx) {
        Guild guild = BotContext.getGuild();
        if (guild == null) { ctx.status(503).html("<h1>Bot nicht bereit.</h1>"); return; }
        String userId = ctx.pathParam("userId");
        try { Long.parseLong(userId); }
        catch (NumberFormatException e) { ctx.status(400).html("<h1>Ungültige ID.</h1>"); return; }
        Optional<DocumentsManager.Fuehrerschein> opt =
            DocumentsManager.getFuehrerschein(guild.getId(), userId);
        if (opt.isEmpty()) {
            Member m = guild.getMemberById(userId);
            ctx.contentType("text/html;charset=utf-8").result(buildNoCharacterPage(
                m != null ? m.getEffectiveName() : "Unbekannt",
                m != null ? m.getUser().getEffectiveAvatarUrl() : ""));
            return;
        }
        // Entzogene Führerscheine werden bis zur Rückgabe nicht mehr angezeigt
        if (de.pcrp.bot.common.LapdDashManager.isLicenseRevoked(guild.getIdLong(), userId)) {
            Member m = guild.getMemberById(userId);
            ctx.contentType("text/html;charset=utf-8").result(buildLicenseRevokedPage(
                m != null ? m.getEffectiveName() : "Unbekannt",
                m != null ? m.getUser().getEffectiveAvatarUrl() : ""));
            return;
        }
        Member m = guild.getMemberById(userId);
        ctx.contentType("text/html;charset=utf-8")
           .result(buildDocumentFuehrerscheinPage(opt.get(), m, userId));
    }

    private static void handleSaveAusweis(Context ctx) {
        if (!BotContext.isReady()) { json(ctx, 503, "error", "Bot noch nicht bereit."); return; }
        String guildId = nzp(ctx.formParam("guildId"));
        String userId  = nzp(ctx.formParam("userId"));
        if (guildId.isEmpty() || userId.isEmpty()) { json(ctx, 400, "error", "Fehlende Parameter."); return; }
        Guild guild = BotContext.getGuild();
        if (guild == null || !guild.getId().equals(guildId)) { json(ctx, 403, "error", "Falscher Server."); return; }
        // Web-Bann prüfen – gesperrte Personen dürfen keine Dokumente mehr erstellen
        if (DataStore.isWebBanned(guildId, userId)) {
            json(ctx, 403, "error", "Dein Zugriff wurde von einem Administrator gesperrt. Sollte das ein Fehler sein, wende dich bitte an das High Team im Discord.");
            return;
        }

        DocumentsManager.Ausweis a = new DocumentsManager.Ausweis();
        a.vorname      = nzp(ctx.formParam("vorname"));
        a.nachname     = nzp(ctx.formParam("nachname"));
        a.geburtsdatum = nzp(ctx.formParam("geburtsdatum"));
        a.staatsang    = nzp(ctx.formParam("staatsangehoerigkeit"));
        a.adresse      = nzp(ctx.formParam("adresse"));
        a.wohnort      = nzp(ctx.formParam("wohnort"));
        a.ausweisNr    = nzp(ctx.formParam("ausweisNr"));
        a.erstelltVon  = nzp(ctx.formParam("erstelltVon"));
        a.erstelltAm   = Instant.now().getEpochSecond();

        if (a.vorname.isEmpty() || a.nachname.isEmpty()) {
            json(ctx, 400, "error", "Vor- und Nachname sind Pflichtfelder."); return;
        }
        UploadedFile photo = ctx.uploadedFile("photo");
        if (photo == null) { json(ctx, 400, "error", "Passfoto ist erforderlich."); return; }
        DocumentsManager.saveAusweis(guildId, userId, a);
        saveAusweisDocPhoto(photo, userId);
        log.info("[Ausweis] Gespeichert für {} / {} durch {}.", userId, guildId, a.erstelltVon);
        JsonObject r = new JsonObject();
        r.addProperty("ok", true);
        r.addProperty("viewUrl", "/ausweis/" + userId);
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    private static void handleSaveFuehrerschein(Context ctx) {
        if (!BotContext.isReady()) { json(ctx, 503, "error", "Bot noch nicht bereit."); return; }
        String guildId = nzp(ctx.formParam("guildId"));
        String userId  = nzp(ctx.formParam("userId"));
        if (guildId.isEmpty() || userId.isEmpty()) { json(ctx, 400, "error", "Fehlende Parameter."); return; }
        Guild guild = BotContext.getGuild();
        if (guild == null || !guild.getId().equals(guildId)) { json(ctx, 403, "error", "Falscher Server."); return; }
        // Web-Bann prüfen – gesperrte Personen dürfen keine Dokumente mehr erstellen
        if (DataStore.isWebBanned(guildId, userId)) {
            json(ctx, 403, "error", "Dein Zugriff wurde von einem Administrator gesperrt. Sollte das ein Fehler sein, wende dich bitte an das High Team im Discord.");
            return;
        }

        DocumentsManager.Fuehrerschein f = new DocumentsManager.Fuehrerschein();
        f.vorname      = nzp(ctx.formParam("vorname"));
        f.nachname     = nzp(ctx.formParam("nachname"));
        f.geburtsdatum = nzp(ctx.formParam("geburtsdatum"));
        f.adresse      = nzp(ctx.formParam("adresse"));
        f.erstelltVon  = nzp(ctx.formParam("erstelltVon"));
        f.erstelltAm   = Instant.now().getEpochSecond();

        // Mehrfachauswahl Klassen (Checkbox-Gruppe liefert "B" ODER "B,C1" je nach Encoding)
        List<String> klassen = new ArrayList<>();
        for (String raw : ctx.formParams("klassen")) {
            for (String k : raw.split(",")) {
                String t = k.trim().toUpperCase();
                if (!t.isEmpty() && !klassen.contains(t)) klassen.add(t);
            }
        }
        f.klassen = klassen;

        String gueltigBisRaw = nzp(ctx.formParam("gueltigBis"));
        if (!gueltigBisRaw.isEmpty()) {
            try { f.gueltigBis = Long.parseLong(gueltigBisRaw); }
            catch (NumberFormatException ignore) { /* Tag-Monat-Jahr Format optional */ }
        }

        if (f.vorname.isEmpty() || f.nachname.isEmpty()) {
            json(ctx, 400, "error", "Vor- und Nachname sind Pflichtfelder."); return;
        }
        UploadedFile photo = ctx.uploadedFile("photo");
        if (photo == null) { json(ctx, 400, "error", "Passfoto ist erforderlich."); return; }
        DocumentsManager.saveFuehrerschein(guildId, userId, f);
        saveLicensePhoto(photo, userId);
        log.info("[Fuehrerschein] Gespeichert für {} / {} durch {}. Klassen: {}",
            userId, guildId, f.erstelltVon, String.join(",", klassen));
        JsonObject r = new JsonObject();
        r.addProperty("ok", true);
        r.addProperty("viewUrl", "/fuehrerschein/" + userId);
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    private static String nzp(String s) { return s == null ? "" : s.trim(); }

    private static void saveLicensePhoto(UploadedFile photo, String userId) {
        if (photo == null) return;
        String ext = photoExt(photo);
        Path p = DataStore.getPath("photos").resolve("fuehrerschein-" + userId + ext);
        try {
            Files.copy(photo.content(), p, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            log.warn("[License-Photo] Speichern fehlgeschlagen für {}: {}", userId, e.getMessage());
        }
    }

    private static void saveAusweisDocPhoto(UploadedFile photo, String userId) {
        if (photo == null) return;
        String ext = photoExt(photo);
        Path p = DataStore.getPath("photos").resolve("ausweis-" + userId + ext);
        try {
            Files.copy(photo.content(), p, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            log.warn("[Ausweis-DocPhoto] Speichern fehlgeschlagen für {}: {}", userId, e.getMessage());
        }
    }

    private static void serveDocumentPhoto(Context ctx, String prefix) {
        String userId = ctx.pathParam("userId");
        for (String ext : List.of(".jpg", ".png")) {
            Path p = DataStore.getPath("photos").resolve(prefix + "-" + userId + ext);
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

    // ═══════════════════════════════════════════════════════════════════════════
    //  Form-HTML (dynamisch gebaut — gleicher Stil wie buildIdCard)
    // ═══════════════════════════════════════════════════════════════════════════

    private static String buildAusweisFormHtml(String guildId, String userId, String displayName, String avatar) {
        String CSS =
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:linear-gradient(135deg,#0a0a0a 0%,#0f0f1a 100%);" +
            "font-family:'Segoe UI',sans-serif;padding:16px;color:#e8e8e8}" +
            "input,select{width:100%;padding:9px 12px;background:#06111f;border:1px solid #c8a04866;" +
            "border-radius:6px;color:#e8e8e8;font-size:.92rem;outline:none;font-family:inherit}" +
            "input:focus,select:focus{border-color:#c8a048;background:#081830}" +
            "label{display:block;color:#6a8fb0;font-size:.7rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px}" +
            ".field{margin-bottom:10px}" +
            ".wrap{max-width:680px;margin:0 auto;background:linear-gradient(135deg,#0d2346 0%,#081830 100%);" +
            "border:3px solid #c8a048;border-radius:14px;overflow:hidden;box-shadow:0 0 40px rgba(200,160,72,.25)}" +
            ".hdr{background:linear-gradient(90deg,#0a1c38,#0d2550);border-bottom:3px solid #c8a048;padding:14px 20px;display:flex;align-items:center;gap:16px}" +
            ".hdr .st{color:#c8a048;font-size:1.3rem;font-weight:700;letter-spacing:4px}" +
            ".hdr .ct{display:block;color:#a8c4e0;font-size:.75rem;letter-spacing:2px;margin-top:2px}" +
            ".photo{width:80px;height:80px;border-radius:50%;border:2px solid #c8a048}" +
            ".photo img{width:100%;height:100%;border-radius:50%;object-fit:cover}" +
            ".meta{padding:14px 20px 0;font-size:.85rem;color:#a8c4e0}" +
            ".meta b{color:#c8a048}" +
            "form{padding:18px 20px}" +
            ".row{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px}" +
            "@media(max-width:480px){.row{grid-template-columns:1fr}}" +
            ".submit{display:block;width:100%;margin-top:14px;padding:13px;background:linear-gradient(90deg,#c8a048,#e8c878);" +
            "border:none;border-radius:8px;color:#1a0800;font-size:.95rem;font-weight:700;letter-spacing:1px;cursor:pointer}" +
            ".submit:hover{opacity:.9}.submit:disabled{opacity:.4;cursor:not-allowed}" +
            ".msg{margin-top:10px;padding:10px;border-radius:8px;font-size:.85rem;text-align:center;display:none}" +
            ".msg.ok{background:#1a3a0d;border:1px solid #4a9930;color:#7ddd55}" +
            ".msg.err{background:#3a0d0d;border:1px solid #993030;color:#dd5555}" +
            ".nav{padding:0 20px 14px;text-align:center;font-size:.78rem;color:#6a8fb0}";
        String avatarHtml = avatar.isEmpty() ? "" : "<img src='" + esc(avatar) + "' alt='avatar'>";
        return "<!DOCTYPE html><html lang='de'><head>" +
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>🪪 Personalausweis erstellen — " + esc(displayName) + "</title>" +
            "<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.css'>" +
            "<script src='https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.js'></script>" +
            "<style>" + CSS +
            ".crop-wrap{position:relative;max-width:100%;margin-bottom:10px;background:#06111f;border:1px solid #c8a04866;border-radius:8px;padding:10px}" +
            ".crop-wrap img{display:block;max-width:100%;max-height:340px}" +
            ".crop-tools{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}" +
            ".crop-tools button{flex:1;padding:8px;background:#0a1c38;border:1px solid #c8a04866;border-radius:6px;color:#e8c878;font-weight:700;letter-spacing:1px;cursor:pointer;font-size:.78rem}" +
            ".crop-tools button:hover{background:#0d2550;border-color:#c8a048}" +
            ".crop-stage{display:none}.crop-stage.on{display:block}" +
            ".photo-field{display:flex;flex-direction:column;gap:6px;margin-bottom:14px;padding:14px;background:#06111f;border:2px dashed #c8a04866;border-radius:8px}" +
            ".photo-field label{margin-bottom:2px}" +
            ".photo-field input[type=file]{padding:8px;background:transparent;border:0;color:#a8c4e0}" +
            "</style></head><body>" +
            "<div class='wrap'>" +
            "<div class='hdr'>" +
            "<div class='photo'>" + avatarHtml + "</div>" +
            "<div><span class='st'>CALIFORNIA</span><span class='ct'>CITY OF LOS ANGELES · PERSONALAUSWEIS</span></div>" +
            "</div>" +
            "<div class='meta'>Ausweis für <b>" + esc(displayName) + "</b> · User-ID <b>" + esc(userId) + "</b></div>" +
            "<form id='f' enctype='multipart/form-data'>" +
            "<input type='hidden' name='guildId' value='" + esc(guildId) + "'>" +
            "<input type='hidden' name='userId'  value='" + esc(userId)  + "'>" +
            "<input type='hidden' name='erstelltVon' value='" + esc(displayName) + "'>" +
            "<div class='row'>" +
            fieldHtml("vorname",              "Vorname",                true)  +
            fieldHtml("nachname",             "Nachname",               true)  +
            fieldHtml("geburtsdatum",         "Geburtsdatum",           true, "date") +
            fieldHtml("staatsangehoerigkeit", "Staatsangehörigkeit",    true)  +
            "</div>" +
            fieldHtml("adresse",   "Adresse / Straße + Hausnummer", true) +
            "<div class='row'>" +
            fieldHtml("wohnort",   "Wohnort",          true) +
            fieldHtml("ausweisNr", "Ausweis-Nummer",   true) +
            "</div>" +
            "<div class='photo-field'>" +
            "<label>📷 Passfoto (JPG/PNG) — Bild auswählen, dann zuschneiden / drehen / zoomen</label>" +
            "<input type='file' id='cropFile' accept='image/png,image/jpeg'>" +
            "</div>" +
            "<div class='crop-stage' id='cropStage'>" +
            "<div class='crop-wrap'><img id='cropImg' alt='Vorschau'></div>" +
            "<div class='crop-tools'>" +
            "<button type='button' data-act='rotL'>↺ Links</button>" +
            "<button type='button' data-act='rotR'>↻ Rechts</button>" +
            "<button type='button' data-act='zoomIn'>+ Zoom</button>" +
            "<button type='button' data-act='zoomOut'>− Zoom</button>" +
            "<button type='button' data-act='reset'>⟲ Reset</button>" +
            "</div></div>" +
            "<button type='submit' class='submit' id='btn'>🪪 Ausweis speichern</button>" +
            "<div class='msg' id='m'></div></form>" +
            "<div class='nav'>Formular wird automatisch gespeichert — du wirst zum Ausweis weitergeleitet.</div>" +
            "</div>" +
            "<script>" +
            "let cropper=null;" +
            "const cropFile=document.getElementById('cropFile');" +
            "const cropImg=document.getElementById('cropImg');" +
            "const cropStage=document.getElementById('cropStage');" +
            "function show(t,c){const m=document.getElementById('m');m.textContent=t;m.className='msg '+c;m.style.display='block';}" +
            "cropFile.addEventListener('change',e=>{" +
            "  const file=e.target.files[0];if(!file)return;" +
            "  if(file.size>10*1024*1024){show('⚠️ Foto zu groß (max 10 MB).','err');cropFile.value='';return;}" +
            "  if(cropper){cropper.destroy();cropper=null;}" +
            "  const reader=new FileReader();" +
            "  reader.onload=ev=>{cropImg.src=ev.target.result;cropStage.classList.add('on');" +
            "    if(window.Cropper){cropper=new Cropper(cropImg,{aspectRatio:3/4,viewMode:1,autoCropArea:0.9,responsive:true,restore:true,background:false});}" +
            "    else{show('⚠️ Cropper konnte nicht geladen werden.','err');}" +
            "  };" +
            "  reader.readAsDataURL(file);" +
            "});" +
            "document.querySelectorAll('[data-act]').forEach(b=>b.addEventListener('click',()=>{" +
            "  if(!cropper)return;const a=b.dataset.act;" +
            "  if(a==='rotL')cropper.rotate(-90);else if(a==='rotR')cropper.rotate(90);" +
            "  else if(a==='zoomIn')cropper.zoom(0.15);else if(a==='zoomOut')cropper.zoom(-0.15);" +
            "  else if(a==='reset')cropper.reset();" +
            "}));" +
            "document.getElementById('f').addEventListener('submit',async e=>{" +
            "  e.preventDefault();" +
            "  if(!cropper){show('⚠️ Bitte zuerst ein Foto auswahlen & zuschneiden.','err');return;}" +
            "  const btn=document.getElementById('btn');btn.disabled=true;" +
            "  try{" +
            "    const canvas=cropper.getCroppedCanvas({width:600,height:800,minWidth:320,minHeight:420,maxWidth:1600,maxHeight:2000,fillColor:'#fff',imageSmoothingQuality:'high'});" +
            "    if(!canvas)throw new Error('crop-empty');" +
            "    const blob=await new Promise(res=>canvas.toBlob(res,'image/jpeg',0.92));" +
            "    if(!blob)throw new Error('blob-empty');" +
            "    const fd=new FormData(e.target);" +
            "    fd.delete('cropFile');" +
            "    fd.set('photo',blob,'cropped.jpg');" +
            "    const r=await fetch('/api/save-ausweis',{method:'POST',body:fd});" +
            "    const d=await r.json();" +
            "    if(d.ok){show('✅ Ausweis gespeichert!','ok');setTimeout(()=>location.href=d.viewUrl,900);}" +
            "    else{show(d.error||'Fehler.','err');btn.disabled=false;}" +
            "  }catch(err){show('Verbindungsfehler: '+(err.message||err),'err');btn.disabled=false;}" +
            "});" +
            "</script></body></html>";
    }

    private static String buildFuehrerscheinFormHtml(String guildId, String userId, String displayName, String avatar) {
        // === ORANGE-Theme Form (LA Driver License) ===
        String CSS =
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:linear-gradient(135deg,#1a0700 0%,#0a0300 100%);" +
            "font-family:'Segoe UI',sans-serif;padding:16px;color:#ffe4d6}" +
            "input,select{width:100%;padding:9px 12px;background:#2a0f00;border:1px solid #ff572266;" +
            "border-radius:6px;color:#ffe4d6;font-size:.92rem;outline:none;font-family:inherit}" +
            "input:focus,select:focus{border-color:#ff5722;background:#401500}" +
            "label{display:block;color:#ffab84;font-size:.7rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px}" +
            ".field{margin-bottom:10px}" +
            ".wrap{max-width:680px;margin:0 auto;background:linear-gradient(135deg,#4a1f00 0%,#2a0f00 100%);" +
            "border:3px solid #ff5722;border-radius:14px;overflow:hidden;box-shadow:0 0 40px rgba(255,87,34,.4)}" +
            ".hdr{background:linear-gradient(90deg,#d84315,#bf360c);border-bottom:3px solid #ff5722;padding:14px 20px;display:flex;align-items:center;gap:16px}" +
            ".hdr .st{color:#fff;font-size:1.3rem;font-weight:700;letter-spacing:4px;text-shadow:0 2px 4px rgba(0,0,0,.3)}" +
            ".hdr .ct{display:block;color:#ffab84;font-size:.75rem;letter-spacing:2px;margin-top:2px}" +
            ".photo{width:80px;height:80px;border-radius:50%;border:2px solid #ff5722}" +
            ".photo img{width:100%;height:100%;border-radius:50%;object-fit:cover}" +
            ".meta{padding:14px 20px 0;font-size:.85rem;color:#ffab84}" +
            ".meta b{color:#ff5722}" +
            "form{padding:18px 20px}" +
            ".row{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px}" +
            "@media(max-width:480px){.row{grid-template-columns:1fr}}" +
            ".photo-field{display:flex;flex-direction:column;gap:6px;margin-bottom:14px;padding:14px;background:#2a0f00;border:2px dashed #ff572266;border-radius:8px}" +
            ".photo-field label{margin-bottom:2px}" +
            ".photo-field input[type=file]{padding:8px;background:transparent;border:0;color:#ffab84}" +
            ".kbox{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-bottom:4px}" +
            ".kbox label{display:flex;align-items:center;justify-content:center;background:#2a0f00;border:1px solid #ff572266;" +
            "border-radius:6px;padding:8px 4px;cursor:pointer;font-weight:700;letter-spacing:1.5px;color:#ff5722;" +
            "font-size:.85rem;transition:all .15s}" +
            ".kbox input{display:none}" +
            ".kbox label:has(input:checked){background:#ff5722;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.3)}" +
            ".submit{display:block;width:100%;margin-top:14px;padding:13px;background:linear-gradient(90deg,#ff5722,#ff6b35);" +
            "border:none;border-radius:8px;color:#fff;font-size:.95rem;font-weight:700;letter-spacing:1px;cursor:pointer;text-shadow:0 1px 2px rgba(0,0,0,.25)}" +
            ".submit:hover{filter:brightness(1.05)}.submit:disabled{opacity:.4;cursor:not-allowed}" +
            ".msg{margin-top:10px;padding:10px;border-radius:8px;font-size:.85rem;text-align:center;display:none}" +
            ".msg.ok{background:#1a3a0d;border:1px solid #4a9930;color:#7ddd55}" +
            ".msg.err{background:#3a0d0d;border:1px solid #993030;color:#dd5555}" +
            ".nav{padding:0 20px 14px;text-align:center;font-size:.78rem;color:#ffab84}";
        String avatarHtml = avatar.isEmpty() ? "" : "<img src='" + esc(avatar) + "' alt='avatar'>";
        String klassen = "AM,A1,A2,A,B,B1,C,C1,CE,D,BE,M,L,T";
        StringBuilder kb = new StringBuilder("<div class='kbox'>");
        for (String k : klassen.split(",")) {
            kb.append("<label><input type='checkbox' name='klassen' value='").append(k).append("'>").append(k).append("</label>");
        }
        kb.append("</div><label>Führerschein-Klassen (Mehrfachauswahl)</label>");
        String avatarHtmlSafe = avatarHtml;
        return "<!DOCTYPE html><html lang='de'><head>" +
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>🚗 California Driver License — " + esc(displayName) + "</title>" +
            "<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.css'>" +
            "<script src='https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.js'></script>" +
            "<style>" + CSS + "</style></head><body>" +
            "<div class='wrap'>" +
            "<div class='hdr'>" +
            "<div class='photo'>" + avatarHtmlSafe + "</div>" +
            "<div><span class='st'>DRIVER LICENSE</span><span class='ct'>STATE OF CALIFORNIA · DMV · PCRP</span></div>" +
            "</div>" +
            "<div class='meta'>Führerschein für <b>" + esc(displayName) + "</b> · User-ID <b>" + esc(userId) + "</b></div>" +
            "<form id='f' enctype='multipart/form-data'>" +
            "<input type='hidden' name='guildId' value='" + esc(guildId) + "'>" +
            "<input type='hidden' name='userId'  value='" + esc(userId)  + "'>" +
            "<input type='hidden' name='erstelltVon' value='" + esc(displayName) + "'>" +
            "<div class='row'>" +
            fieldHtml("vorname",      "LN",   true) +
            fieldHtml("nachname",     "FN",   true) +
            fieldHtml("geburtsdatum", "DOB",  true, "date") +
            fieldHtml("gueltigBis",   "EXP (Unix-Sek)", false, "number") +
            "</div>" +
            fieldHtml("adresse", "ADDRESS", true) +
            kb.toString() +
            "<div class='photo-field'>" +
            "<label>📷 Passfoto (JPG/PNG) — Bild auswählen, dann zuschneiden / drehen / zoomen</label>" +
            "<input type='file' id='cropFile' accept='image/png,image/jpeg'>" +
            "</div>" +
            "<div class='crop-stage' id='cropStage'>" +
            "<div class='crop-wrap'><img id='cropImg' alt='Vorschau'></div>" +
            "<div class='crop-tools'>" +
            "<button type='button' data-act='rotL'>↺ Links</button>" +
            "<button type='button' data-act='rotR'>↻ Rechts</button>" +
            "<button type='button' data-act='zoomIn'>+ Zoom</button>" +
            "<button type='button' data-act='zoomOut'>− Zoom</button>" +
            "<button type='button' data-act='reset'>⟲ Reset</button>" +
            "</div></div>" +
            "<button type='submit' class='submit' id='btn'>🚗 Führerschein speichern</button>" +
            "<div class='msg' id='m'></div></form>" +
            "<div class='nav'>Formular wird automatisch gespeichert — du wirst zum Führerschein weitergeleitet.</div>" +
            "</div>" +
            "<script>" +
            "let cropper=null;function cls(){" +
            "  const ck=document.querySelectorAll('input[name=\\\"klassen\\\"]:checked');return Array.from(ck).map(c=>c.value);}" +
            "const cropFile=document.getElementById('cropFile');" +
            "const cropImg=document.getElementById('cropImg');" +
            "const cropStage=document.getElementById('cropStage');" +
            "function show(t,c){const m=document.getElementById('m');m.textContent=t;m.className='msg '+c;m.style.display='block';}" +
            "cropFile.addEventListener('change',e=>{" +
            "  const file=e.target.files[0];if(!file)return;" +
            "  if(file.size>10*1024*1024){show('⚠️ Foto zu groß (max 10 MB).','err');cropFile.value='';return;}" +
            "  if(cropper){cropper.destroy();cropper=null;}" +
            "  const reader=new FileReader();" +
            "  reader.onload=ev=>{cropImg.src=ev.target.result;cropStage.classList.add('on');" +
            "    if(window.Cropper){cropper=new Cropper(cropImg,{aspectRatio:3/4,viewMode:1,autoCropArea:0.9,responsive:true,restore:true,background:false});}" +
            "    else{show('⚠️ Cropper konnte nicht geladen werden.','err');}" +
            "  };" +
            "  reader.readAsDataURL(file);" +
            "});" +
            "document.querySelectorAll('[data-act]').forEach(b=>b.addEventListener('click',()=>{" +
            "  if(!cropper)return;const a=b.dataset.act;" +
            "  if(a==='rotL')cropper.rotate(-90);else if(a==='rotR')cropper.rotate(90);" +
            "  else if(a==='zoomIn')cropper.zoom(0.15);else if(a==='zoomOut')cropper.zoom(-0.15);" +
            "  else if(a==='reset')cropper.reset();" +
            "}));" +
            "document.getElementById('f').addEventListener('submit',async e=>{" +
            "  e.preventDefault();" +
            "  if(!cropper){show('⚠️ Bitte zuerst ein Foto auswahlen & zuschneiden.','err');return;}" +
            "  const btn=document.getElementById('btn');btn.disabled=true;" +
            "  try{" +
            "    const canvas=cropper.getCroppedCanvas({width:600,height:800,minWidth:320,minHeight:420,maxWidth:1600,maxHeight:2000,fillColor:'#fff',imageSmoothingQuality:'high'});" +
            "    if(!canvas)throw new Error('crop-empty');" +
            "    const blob=await new Promise(res=>canvas.toBlob(res,'image/jpeg',0.92));" +
            "    if(!blob)throw new Error('blob-empty');" +
            "    const fd=new FormData(e.target);" +
            "    fd.delete('cropFile');" +
            "    fd.delete('klassen');" +
            "    for(const k of cls())fd.append('klassen',k);" +
            "    fd.set('photo',blob,'cropped.jpg');" +
            "    const r=await fetch('/api/save-fuehrerschein',{method:'POST',body:fd});" +
            "    const d=await r.json();" +
            "    if(d.ok){show('✅ Führerschein gespeichert!','ok');setTimeout(()=>location.href=d.viewUrl,900);}" +
            "    else{show(d.error||'Fehler.','err');btn.disabled=false;}" +
            "  }catch(err){show('Verbindungsfehler: '+(err.message||err),'err');btn.disabled=false;}" +
            "});" +
            "</script></body></html>";
    }

    private static String fieldHtml(String name, String label, boolean required) {
        return fieldHtml(name, label, required, "text");
    }

    private static String fieldHtml(String name, String label, boolean required, String type) {
        return "<div class='field'><label>" + esc(label) + (required ? "" : " (optional)") + "</label>" +
            "<input type='" + type + "' name='" + esc(name) + "'" +
            (required ? " required" : "") + "></div>";
    }

    // ═══════════════════════════════════════════════════════════════════════════
    //  Viewer-Seiten (DocumentsManager-basiert) — analog zu buildIdCard
    // ═══════════════════════════════════════════════════════════════════════════

    private static String buildDocumentAusweisPage(DocumentsManager.Ausweis a, Member m, String userId) {
        String vorname = esc(a.vorname), nachname = esc(a.nachname);
        String idNum = a.ausweisNr.isBlank()
            ? "LA-" + userId.substring(Math.max(0, userId.length() - 8)).toUpperCase()
            : esc(a.ausweisNr);
        String photoSrc = "/api/ausweis-photo/" + esc(userId);
        String photoFallback = (m != null)
            ? m.getUser().getEffectiveAvatarUrl() + "?size=512"
            : "";
        String photoImg = "<img src='" + photoSrc + "'" +
            (photoFallback.isEmpty() ? "" : " data-fb='" + esc(photoFallback) + "'") +
            " onerror=\"if(this.dataset.fb){this.src=this.dataset.fb}else{this.outerHTML='<div style=color:#666;font-size:.7rem'>Kein Foto</div>'}\">";
        String addrText = esc(a.adresse.isBlank() ? a.wohnort : a.adresse);
        return "<!DOCTYPE html><html lang='de'><head>" +
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>🪪 California ID — " + vorname + " " + nachname + "</title>" +
            "<style>" +
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:#e8d9bf;display:flex;align-items:center;justify-content:center;padding:20px;font-family:'Courier New',Consolas,monospace;}" +
            ".id{width:100%;max-width:380px;background:repeating-linear-gradient(90deg,#f5e6c8 0,#f5e6c8 24px,#ecdcb3 24px,#ecdcb3 25px);border:2px solid #1c4587;border-radius:6px;overflow:hidden;box-shadow:0 6px 22px rgba(0,0,0,.4);color:#1a1a1a;}" +
            ".id-hdr{background:#1c4587;color:#fff;padding:8px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:3px solid #ffd641;}" +
            ".id-hdr .left{font-size:.66rem;letter-spacing:1.5px;line-height:1.35;}" +
            ".id-hdr .left b{font-size:.85rem;letter-spacing:3px;display:block;}" +
            ".id-hdr .star{color:#ffd641;font-size:1.8rem;line-height:1;font-family:serif;filter:drop-shadow(0 0 4px rgba(255,214,65,.6));}" +
            ".id-title{text-align:center;padding:5px 0;background:#fff8e0;border-bottom:1.5px solid #1c4587;}" +
            ".id-title h1{color:#8b1a1a;font-size:1.25rem;letter-spacing:6px;margin:0;font-weight:900;}" +
            ".id-title h2{color:#1c4587;font-size:.6rem;letter-spacing:3px;margin:2px 0 0 0;font-weight:700;}" +
            ".id-body{display:flex;flex-direction:column;padding:10px 14px;}" +
            ".id-photo-wrap{display:flex;flex-direction:column;align-items:center;border-bottom:1px solid #1c4587;padding-bottom:8px;margin-bottom:10px;}" +
            ".id-photo{width:140px;flex-shrink:0;border:2px solid #1c4587;padding:3px;background:#fff;position:relative;margin:0 auto;}" +
            ".id-photo img{width:100%;height:175px;object-fit:cover;object-position:top center;display:block;}" +
            ".id-photo .dd{position:absolute;top:2px;left:2px;background:#8b1a1a;color:#fff;font-size:.5rem;letter-spacing:1px;padding:1px 4px;border-radius:0 2px 0 0;font-weight:700;}" +
            ".id-sig{margin-top:8px;border-top:1px solid #444;width:100%;max-width:240px;height:30px;position:relative;background:#fff8e0;}" +
            ".id-sig span{position:absolute;bottom:2px;left:6px;font-size:.65rem;font-style:italic;color:#1c4587;}" +
            ".id-data{width:100%;padding-left:0;}" +
            ".id-data .row{display:block;margin-bottom:8px;}" +
            ".id-data .field{display:flex;flex-direction:column;width:100%;margin-bottom:6px;}" +
            ".id-data .label{font-size:.55rem;letter-spacing:1.5px;color:#1c4587;font-weight:700;text-transform:uppercase;}" +
            ".id-data .val{font-size:1rem;color:#1a1a1a;font-weight:700;border-bottom:1px dotted #555;padding-bottom:2px;letter-spacing:.5px;}" +
            ".id-data .addr{font-size:.85rem;color:#1a1a1a;font-weight:700;border-bottom:1px dotted #555;padding-bottom:2px;min-height:24px;}" +
            "</style></head><body>" +
            "<div class='id'>" +
            "<div class='id-hdr'><div class='left'><b>STATE OF CALIFORNIA</b>DEPARTMENT OF MOTOR VEHICLES · DMV</div><div class='star' title='REAL ID'>\u2605</div></div>" +
            "<div class='id-title'><h1>IDENTIFICATION CARD</h1><h2>ID " + idNum + "</h2></div>" +
            "<div class='id-body'>" +
            "<div class='id-photo-wrap'><div class='id-photo'>" + photoImg +
            "<div class='dd'>DD</div></div>" +
            "<div class='id-sig'><span>" + vorname + " " + nachname + "</span></div></div>" +
            "<div class='id-data'>" +
            "<div class='row'>" +
            "<div class='field'><div class='label'>LN · LAST NAME</div><div class='val'>" + nachname + "</div></div>" +
            "<div class='field'><div class='label'>FN · FIRST NAME</div><div class='val'>" + vorname + "</div></div>" +
            "</div>" +
            "<div class='row'>" +
            "<div class='field'><div class='label'>DOB</div><div class='val'>" + esc(a.geburtsdatum) + "</div></div>" +
            "<div class='field'><div class='label'>NATIONALITY</div><div class='val'>" + esc(a.staatsang) + "</div></div>" +
            "</div>" +
            "<div class='field' style='margin-bottom:8px'><div class='label'>ADDRESS</div><div class='addr'>" + addrText + "</div></div>" +
            (a.erstelltVon.isBlank() ? "" :
                "<div style='margin-top:8px;font-size:.55rem;color:#888'>Erstellt von: " + esc(a.erstelltVon) + "</div>") +
            "</div></div>" +
            "<div style='background:#1c4587;color:#fff;padding:6px 14px;text-align:center;font-size:.55rem;letter-spacing:1.5px;border-top:3px solid #ffd641;'>" +
            "STATE OF CALIFORNIA · IDENTIFICATION CARD</div>" +
            "</div></body></html>";
    }

    private static String buildDocumentFuehrerscheinPage(DocumentsManager.Fuehrerschein f, Member m, String userId) {
        // === ECHTES California Driver License Layout ===
        String vorname = esc(f.vorname), nachname = esc(f.nachname);
        String klassen  = (f.klassen == null || f.klassen.isEmpty()) ? "—" : esc(String.join("   ", f.klassen));
        String dl       = "D" + userId.substring(Math.max(0, userId.length() - 8)).toUpperCase();
        String expDate  = f.gueltigBis > 0
            ? "<t:" + f.gueltigBis + ":d>"
            : "—";
        String expText  = (f.gueltigBis > 0) ? esc(java.time.Instant.ofEpochSecond(f.gueltigBis)
                .atZone(java.time.ZoneId.systemDefault()).toLocalDate().toString()) : "—";
        String dobText  = esc(f.geburtsdatum);
        String addrText = esc(f.adresse);
        return "<!DOCTYPE html><html lang='de'><head>" +
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>California Driver License \u2014 " + vorname + " " + nachname + "</title>" +
            "<style>" +
            "*{box-sizing:border-box;margin:0;padding:0}" +
            "body{min-height:100vh;background:#e8d9bf;display:flex;align-items:center;justify-content:center;padding:20px;font-family:'Courier New',Consolas,monospace;}" +
            ".dl{width:100%;max-width:380px;background:linear-gradient(135deg,#f5f2e6,#e7ddc3);border-radius:8px;overflow:hidden;box-shadow:0 10px 25px rgba(0,0,0,.4),inset 0 0 0 1px rgba(255,255,255,.6);color:#111;position:relative;}" +
            ".dl::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent 40%,rgba(255,235,160,.3) 50%,transparent 60%);pointer-events:none;z-index:10;}" +
            ".dl-hdr{background:linear-gradient(180deg,#1c4587,#0e2e5e);color:#fff;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 4px rgba(0,0,0,.15);}" +
            ".dl-hdr-title{font-weight:900;font-size:1.15rem;letter-spacing:1px;}" +
            ".dl-hdr-star{color:#f1c40f;font-size:1.4rem;text-shadow:0 0 4px rgba(241,196,15,.6);}" +
            ".dl-body{display:flex;flex-direction:row;gap:12px;padding:14px;}" +
            ".dl-photo-wrap{display:flex;flex-direction:column;width:35%;}" +
            ".dl-photo{background:#fff;border:2px solid #1c4587;border-radius:4px;padding:2px;position:relative;box-shadow:0 2px 5px rgba(0,0,0,.15);margin-bottom:8px;}" +
            ".dl-photo img{width:100%;display:block;border-radius:2px;aspect-ratio:3/4;object-fit:cover;object-position:top center;}" +
            ".dd{position:absolute;top:-6px;left:-6px;background:#c0392b;color:#fff;font-size:.65rem;font-weight:900;padding:2px 5px;border-radius:3px;box-shadow:0 2px 4px rgba(0,0,0,.3);}" +
            ".dl-sig{position:relative;border-bottom:1.5px solid rgba(17,17,17,.7);height:30px;width:100%;margin-top:2px;background:rgba(255,248,224,.5);}" +
            ".dl-sig span{position:absolute;bottom:2px;left:4px;font-size:.55rem;font-style:italic;color:#1c4587;}" +
            ".dl-data-col{display:flex;flex-direction:column;width:65%;gap:8px;}" +
            ".dl-row{display:flex;gap:8px;width:100%;}" +
            ".dl-field{display:flex;flex-direction:column;flex:1;min-width:0;}" +
            ".dl-field.fw{flex:0 0 100%;}" +
            ".lbl{font-size:.52rem;color:#c0392b;font-weight:900;text-transform:uppercase;margin-bottom:1px;letter-spacing:1px;}" +
            ".val{font-size:.85rem;color:#1a1a1a;font-weight:700;text-shadow:0 1px 0 rgba(255,255,255,.5);overflow-wrap:anywhere;}" +
            ".val.addr{font-size:.78rem;}" +
            ".dl-class-box{background:rgba(28,69,135,.08);border-left:4px solid #1c4587;padding:5px 8px;border-radius:0 4px 4px 0;}" +
            ".dl-ftr{background:linear-gradient(180deg,#1c4587,#0e2e5e);border-top:3px solid #f1c40f;padding:6px 14px;font-size:.6rem;font-weight:700;color:#fff;text-align:center;letter-spacing:2px;}" +
            ".dl-ftr .legal{opacity:.85;font-size:.5rem;margin-top:2px;letter-spacing:2px;}" +
            "</style></head><body>" +
            "<div class='dl'>" +
            "<div class='dl-hdr'><span class='dl-hdr-title'>CALIFORNIA</span><span class='dl-hdr-star' title='REAL ID'>\u2605</span></div>" +
            "<div class='dl-body'>" +
            "<div class='dl-photo-wrap'>" +
            "<div class='dl-photo'>" +
            "<span class='dd'>DD</span>" +
            "<img src='/api/license-photo/" + esc(userId) + "' onerror=\"this.outerHTML='<div style=&quot;aspect-ratio:3/4;display:flex;align-items:center;justify-content:center;color:#888;font-size:.6rem;background:#eee&quot;>Kein Foto</div>'\">" +
            "</div>" +
            "<div class='dl-sig'><span>" + vorname + " " + nachname + "</span></div>" +
            "</div>" +
            "<div class='dl-data-col'>" +
            "<div class='dl-row'>" +
            "<div class='dl-field'><span class='lbl'>LN</span><span class='val'>" + nachname + "</span></div>" +
            "<div class='dl-field'><span class='lbl'>FN</span><span class='val'>" + vorname + "</span></div>" +
            "</div>" +
            "<div class='dl-row'>" +
            "<div class='dl-field'><span class='lbl'>DOB</span><span class='val'>" + dobText + "</span></div>" +
            "<div class='dl-field'><span class='lbl'>EXP " + expDate + "</span><span class='val'>" + expText + "</span></div>" +
            "</div>" +
            "<div class='dl-row'>" +
            "<div class='dl-field fw'><span class='lbl'>ADDRESS</span><span class='val addr'>" + addrText + "</span></div>" +
            "</div>" +
            "<div class='dl-row'>" +
            "<div class='dl-field fw dl-class-box'><span class='lbl'>CLASS</span><span class='val'>" + klassen + "</span></div>" +
            "</div>" +
            "</div>" +
            "</div>" +
            "<div class='dl-ftr'>DRIVER LICENSE \u00b7 " + esc(dl) + " \u00b7 CLASS " + esc(String.join("/", f.klassen != null ? f.klassen : List.of("C"))) +
            (f.erstelltVon.isBlank() ? "" : "<div class='legal'>Issued by: " + esc(f.erstelltVon) + "</div>") +
            "</div>" +
            "</div></body></html>";
    }

    private static String docField(String label, String value) {
        String v = value == null || value.isEmpty() ? "—" : value;
        return "<div class='field'><label>" + esc(label) + "</label><div class='val'>" + v + "</div></div>";
    }

}
