package de.pcrp.bot.web;

import com.google.gson.*;
import de.pcrp.bot.common.*;
import io.javalin.http.Context;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * HTTP-Routes für "Premium Deluxe Motorsport" — die Autohaus-Webseite.
 *
 * Routes:
 *   GET  /premium-motorsport                       → public HTML (statisch)
 *   GET  /premium-motorsport/admin?token=…        → admin HTML nur wenn employee
 *   GET  /api/pd/vehicles?token=…                 → alle Fahrzeuge (Array)
 *   GET  /api/pd/vehicles?token=…&category=…      → nach Kategorie gefiltert
 *   GET  /api/pd/vehicle/{id}?token=…             → einzelnes Fahrzeug
 *   POST /api/pd/vehicles (employee)               → Fahrzeug anlegen
 *   POST /api/pd/vehicles/{id}/delete (employee)   → Fahrzeug löschen
 *   POST /api/pd/vehicle/{id}/buy (user)           → kaufen (Bargeld → Garage)
 *   GET  /api/pd/garage?token=…                    → eigene Garage
 *   POST /api/pd/garage/transfer (user)            → Garagen-Fahrzeug übertragen
 *   GET  /api/pd/info                              → Info-Meldungen (Array)
 *   POST /api/pd/info (employee)                   → Info hinzufügen
 *   POST /api/pd/info/{id}/delete (employee)       → Info löschen
 *   GET  /api/pd/offers                            → Angebote (Array)
 *   POST /api/pd/offers (employee)                → Angebot anlegen
 *   POST /api/pd/offers/{id}/delete (employee)    → Angebot löschen
 */
public class PremiumMotorsportHandler {

    private static final Logger log  = LoggerFactory.getLogger(PremiumMotorsportHandler.class);
    private static final Gson   GSON = new GsonBuilder().create();

    private PremiumMotorsportHandler() {}

    // ── Schnellprüfung ─────────────────────────────────────────────────────────

    private static PremiumMotorsportManager.AuthInfo auth(Context ctx) {
        String token = ctx.queryParam("token");
        PremiumMotorsportManager.AuthInfo info = PremiumMotorsportManager.validateToken(token);
        if (info == null) {
            ctx.status(401).contentType("application/json")
                .result(GSON.toJson(errObj("Nicht authentifiziert. Token fehlt oder ungültig.")));
            return null;
        }
        return info;
    }

    private static boolean requireEmployee(Context ctx, PremiumMotorsportManager.AuthInfo info) {
        if (!info.employee) {
            ctx.status(403).contentType("application/json")
                .result(GSON.toJson(errObj("Nur Mitarbeiter dürfen diese Aktion ausführen.")));
            return false;
        }
        return true;
    }

    private static JsonObject errObj(String msg) {
        JsonObject o = new JsonObject();
        o.addProperty("ok", false);
        o.addProperty("error", msg);
        return o;
    }

    private static JsonObject okObj() {
        JsonObject o = new JsonObject();
        o.addProperty("ok", true);
        return o;
    }

    private static void ok(Context ctx) {
        ctx.contentType("application/json").result(GSON.toJson(okObj()));
    }

    private static void err(Context ctx, int status, String msg) {
        ctx.status(status).contentType("application/json").result(GSON.toJson(errObj(msg)));
    }

    private static String safeTrim(String s) {
        return s == null ? "" : s.trim();
    }

    // ── Auth (Phone-Login → Session-Token) ─────────────────────────────────────

    /** POST /api/pd/auth/login — Body: {phone} → erzeugt eine PhoneManager-Session und liefert {token, displayName, employee}. */
    public static void handleAuthLogin(Context ctx) {
        if (!BotContext.isReady()) { err(ctx, 503, "Bot noch nicht bereit."); return; }
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { err(ctx, 400, "Ungültige JSON-Anfrage."); return; }
        String phone = safeTrim(body.has("phone") ? body.get("phone").getAsString() : "");
        if (phone.isEmpty()) { err(ctx, 400, "Telefonnummer erforderlich."); return; }

        Guild guild = BotContext.getGuild();
        if (guild == null) { err(ctx, 503, "Guild nicht verfügbar."); return; }

        PhoneManager.Contract contract = PhoneManager.getContractByNumber(guild.getId(), phone);
        if (contract == null || contract.userId == null) { err(ctx, 404, "Diese Nummer ist unbekannt."); return; }

        String token = PhoneManager.createSession(guild.getId(), phone);
        if (token == null || token.isBlank()) { err(ctx, 500, "Session konnte nicht erstellt werden."); return; }

        Member member = guild.getMemberById(contract.userId);
        boolean employee = false;
        if (member != null) {
            long empRoleId = LoggingConfig.PD_EMPLOYEE_ROLE_ID;
            if (empRoleId == 0L) {
                employee = member.hasPermission(net.dv8tion.jda.api.Permission.ADMINISTRATOR);
            } else {
                employee = member.getRoles().stream().anyMatch(r -> r.getIdLong() == empRoleId);
            }
        }

        JsonObject out = new JsonObject();
        out.addProperty("ok", true);
        out.addProperty("token", token);
        out.addProperty("userId", contract.userId);
        out.addProperty("displayName", member != null ? member.getEffectiveName() : contract.firstName + " " + contract.lastName);
        out.addProperty("employee", employee);
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    /** GET /api/pd/me?token=… → gibt aktuelle Auth-Info zurück (für Session-Check). */
    public static void handleMe(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        JsonObject out = new JsonObject();
        out.addProperty("ok", true);
        out.addProperty("userId", info.userId);
        out.addProperty("displayName", info.displayName);
        out.addProperty("employee", info.employee);
        out.addProperty("guildId", info.guildId);
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    // ── Public HTML ────────────────────────────────────────────────────────────
    public static void serveSite(Context ctx) {
        try (var is = WebServer.class.getResourceAsStream("/static/premium-motorsport.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            String base = apiBase();
            String html = new String(is.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8)
                .replace("%%API_BASE%%", base);
            ctx.contentType("text/html;charset=utf-8").result(html);
            log.info("[PD] Marketing-Seite ausgeliefert.");
        } catch (Exception e) {
            log.error("[PD] Fehler serveSite", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    public static void serveAdmin(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        if (!requireEmployee(ctx, info)) return;
        try (var is = WebServer.class.getResourceAsStream("/static/premium-motorsport-admin.html")) {
            if (is == null) { ctx.status(404).result("Not found"); return; }
            String base = apiBase();
            String html = new String(is.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8)
                .replace("%%API_BASE%%", base)
                .replace("%%EMPLOYEE_NAME%%", info.displayName);
            ctx.contentType("text/html;charset=utf-8").result(html);
            log.info("[PD] Admin-Dashboard ausgeliefert für Mitarbeiter {}.", info.displayName);
        } catch (Exception e) {
            log.error("[PD] Fehler serveAdmin", e);
            ctx.status(500).result("Interner Fehler");
        }
    }

    private static String apiBase() {
        String base = System.getenv("WEB_URL");
        if (base == null || base.isBlank()) {
            base = System.getenv().getOrDefault("RAILWAY_PUBLIC_DOMAIN",
                "pcrp-bot-production-3ad1.up.railway.app");
            if (!base.startsWith("http")) base = "https://" + base;
        }
        return base.replaceAll("/$", "");
    }

    // ── Vehicles ───────────────────────────────────────────────────────────────

    public static void handleListVehicles(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        String category = ctx.queryParam("category");
        List<PremiumMotorsportManager.Vehicle> list =
            category == null || category.isBlank()
                ? PremiumMotorsportManager.getAllVehicles(info.guildId)
                : PremiumMotorsportManager.getVehiclesByCategory(info.guildId, category);

        JsonArray arr = new JsonArray();
        for (PremiumMotorsportManager.Vehicle v : list) {
            JsonObject o = vToJson(v);
            arr.add(o);
        }
        JsonObject resp = new JsonObject();
        resp.addProperty("ok", true);
        resp.add("vehicles", arr);
        ctx.contentType("application/json").result(GSON.toJson(resp));
    }

    public static void handleGetVehicle(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        String id = ctx.pathParam("id");
        PremiumMotorsportManager.Vehicle v = PremiumMotorsportManager.getVehicleById(info.guildId, id);
        if (v == null) { err(ctx, 404, "Fahrzeug nicht gefunden."); return; }
        ctx.contentType("application/json").result(GSON.toJson(vToJson(v)));
    }

    public static void handleCreateVehicle(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        if (!requireEmployee(ctx, info)) return;

        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { err(ctx, 400, "Ungültige JSON-Anfrage."); return; }

        String name = safeTrim(body.has("name") ? body.get("name").getAsString() : "");
        String category = safeTrim(body.has("category") ? body.get("category").getAsString() : "");
        String desc = safeTrim(body.has("description") ? body.get("description").getAsString() : "");
        String img  = safeTrim(body.has("imageUrl") ? body.get("imageUrl").getAsString() : "");
        long price = body.has("price") ? body.get("price").getAsLong() : 0;
        int stock  = body.has("stock") ? body.get("stock").getAsInt() : 1;

        if (name.isEmpty() || category.isEmpty() || price <= 0) {
            err(ctx, 400, "Name, Kategorie und Preis (> 0) sind erforderlich.");
            return;
        }

        PremiumMotorsportManager.Vehicle v = PremiumMotorsportManager.createVehicle(
            info.guildId, name, category, desc, price, img, stock);
        ctx.contentType("application/json").result(GSON.toJson(vToJson(v)));
    }

    public static void handleDeleteVehicle(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        if (!requireEmployee(ctx, info)) return;
        String id = ctx.pathParam("id");
        boolean deleted = PremiumMotorsportManager.deleteVehicle(info.guildId, id);
        if (!deleted) { err(ctx, 404, "Fahrzeug nicht gefunden."); return; }
        ok(ctx);
    }

    public static void handleBuyVehicle(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        String id = ctx.pathParam("id");
        String error = PremiumMotorsportManager.purchaseVehicle(info.guildId, info.userId, id);
        if (error != null) { err(ctx, 400, error); return; }

        PremiumMotorsportManager.Vehicle v = PremiumMotorsportManager.getVehicleById(info.guildId, id);
        JsonObject resp = new JsonObject();
        resp.addProperty("ok", true);
        resp.addProperty("message", "Fahrzeug gekauft: " + v.name);
        resp.addProperty("pricePaid", v.price);
        resp.add("vehicle", vToJson(v));
        ctx.contentType("application/json").result(GSON.toJson(resp));
        log.info("[PD] {} kaufte {}.", info.displayName, v.name);
    }

    // ── Garage ─────────────────────────────────────────────────────────────────

    public static void handleGetGarage(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        List<PremiumMotorsportManager.GarageEntry> list =
            PremiumMotorsportManager.getGarage(info.guildId, info.userId);
        JsonArray arr = new JsonArray();
        for (PremiumMotorsportManager.GarageEntry e : list) {
            JsonObject o = new JsonObject();
            o.addProperty("vin", e.vin);
            o.addProperty("name", e.name);
            o.addProperty("category", e.category);
            o.addProperty("pricePaid", e.pricePaid);
            o.addProperty("purchasedAt", e.purchasedAt);
            o.addProperty("displayName", e.displayName());
            arr.add(o);
        }
        JsonObject resp = new JsonObject();
        resp.addProperty("ok", true);
        resp.add("garage", arr);
        ctx.contentType("application/json").result(GSON.toJson(resp));
    }

    public static void handleTransferGarage(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { err(ctx, 400, "Ungültige JSON-Anfrage."); return; }

        String vin = safeTrim(body.has("vin") ? body.get("vin").getAsString() : "");
        String toUsername = safeTrim(body.has("toUsername") ? body.get("toUsername").getAsString() : "");
        if (vin.isEmpty() || toUsername.isEmpty()) {
            err(ctx, 400, "vin und toUsername erforderlich."); return;
        }

        // toUsername → User ID via BotContext
        var toMember = BotContext.findMemberByUsername(toUsername);
        if (toMember == null) { err(ctx, 404, "Empfänger nicht auf dem Server."); return; }

        String error = PremiumMotorsportManager.transferGarageVehicle(info.guildId, info.userId, toMember.getId(), vin);
        if (error != null) { err(ctx, 400, error); return; }
        ok(ctx);
    }

    // ── Info ───────────────────────────────────────────────────────────────────

    public static void handleListInfo(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        List<PremiumMotorsportManager.InfoMessage> list = PremiumMotorsportManager.getInfo(info.guildId);
        JsonArray arr = new JsonArray();
        for (PremiumMotorsportManager.InfoMessage m : list) {
            JsonObject o = new JsonObject();
            o.addProperty("id", m.id);
            o.addProperty("title", m.title);
            o.addProperty("text", m.text);
            o.addProperty("author", m.author);
            o.addProperty("createdAt", m.createdAt);
            arr.add(o);
        }
        JsonObject resp = new JsonObject();
        resp.addProperty("ok", true);
        resp.add("messages", arr);
        ctx.contentType("application/json").result(GSON.toJson(resp));
    }

    public static void handleAddInfo(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        if (!requireEmployee(ctx, info)) return;
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { err(ctx, 400, "Ungültige JSON-Anfrage."); return; }
        String title = safeTrim(body.has("title") ? body.get("title").getAsString() : "Info");
        String text  = safeTrim(body.has("text")  ? body.get("text").getAsString()  : "");
        if (text.isEmpty()) { err(ctx, 400, "Text erforderlich."); return; }
        PremiumMotorsportManager.InfoMessage m = PremiumMotorsportManager.addInfo(
            info.guildId, title, text, info.displayName);
        ok(ctx);
        log.info("[PD] Info-Message '{}' hinzugefügt von {}.", title, info.displayName);
    }

    public static void handleDeleteInfo(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        if (!requireEmployee(ctx, info)) return;
        if (!PremiumMotorsportManager.deleteInfo(info.guildId, ctx.pathParam("id"))) {
            err(ctx, 404, "Info nicht gefunden."); return;
        }
        ok(ctx);
    }

    // ── Offers ─────────────────────────────────────────────────────────────────

    public static void handleListOffers(Context ctx) {
        // Öffentlich: Angebote werden auf der Startseite anonymen Besuchern angezeigt — kein Auth-Check.
        Guild guild = BotContext.getGuild();
        if (guild == null) { err(ctx, 503, "Guild nicht verfügbar."); return; }
        List<PremiumMotorsportManager.Offer> list = PremiumMotorsportManager.getOffers(guild.getId());
        JsonArray arr = new JsonArray();
        for (PremiumMotorsportManager.Offer o : list) {
            JsonObject j = new JsonObject();
            j.addProperty("id", o.id);
            j.addProperty("title", o.title);
            j.addProperty("description", o.description);
            j.addProperty("discountPercent", o.discountPercent);
            if (o.vehicleId != null) j.addProperty("vehicleId", o.vehicleId);
            j.addProperty("validUntil", o.validUntil);
            arr.add(j);
        }
        JsonObject resp = new JsonObject();
        resp.addProperty("ok", true);
        resp.add("offers", arr);
        ctx.contentType("application/json").result(GSON.toJson(resp));
    }

    public static void handleAddOffer(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        if (!requireEmployee(ctx, info)) return;
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { err(ctx, 400, "Ungültige JSON-Anfrage."); return; }
        String title = safeTrim(body.has("title") ? body.get("title").getAsString() : "");
        String desc  = safeTrim(body.has("description") ? body.get("description").getAsString() : "");
        long discount = body.has("discountPercent") ? body.get("discountPercent").getAsLong() : 0;
        String vehicleId = body.has("vehicleId") && !body.get("vehicleId").isJsonNull()
            ? body.get("vehicleId").getAsString() : null;
        long validUntil  = body.has("validUntil") ? body.get("validUntil").getAsLong() : 0;
        if (title.isEmpty()) { err(ctx, 400, "Titel erforderlich."); return; }
        PremiumMotorsportManager.addOffer(info.guildId, title, desc, discount, vehicleId, validUntil);
        ok(ctx);
    }

    public static void handleDeleteOffer(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        if (!requireEmployee(ctx, info)) return;
        if (!PremiumMotorsportManager.deleteOffer(info.guildId, ctx.pathParam("id"))) {
            err(ctx, 404, "Angebot nicht gefunden."); return;
        }
        ok(ctx);
    }

    // ── Contact Tickets ──────────────────────────────────────────────────────────────────────────

    /** Liefert die Standard-Themen für das Kontakt-Dropdown. Public, ohne Auth. */
    public static void handleTicketTopics(Context ctx) {
        JsonArray arr = new JsonArray();
        for (String t : PremiumMotorsportManager.TICKET_TOPICS) arr.add(t);
        JsonObject r = new JsonObject();
        r.addProperty("ok", true);
        r.add("topics", arr);
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    /** POST /api/pd/tickets — Body: {topic, message}. Erstellt ein Ticket für den eingeloggten User. */
    public static void handleCreateTicket(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { err(ctx, 400, "Ungültige JSON-Anfrage."); return; }
        String topic = safeTrim(body.has("topic") ? body.get("topic").getAsString() : "");
        String msg = safeTrim(body.has("message") ? body.get("message").getAsString() : "");
        if (topic.isEmpty() || msg.isEmpty()) {
            err(ctx, 400, "Thema und Nachricht erforderlich.");
            return;
        }
        if (msg.length() > 2000) { err(ctx, 400, "Nachricht zu lang (max. 2000 Zeichen)."); return; }

        PremiumMotorsportManager.ContactTicket t = PremiumMotorsportManager.createTicket(
            info.guildId, info.userId, info.displayName, topic, msg);

        JsonObject resp = new JsonObject();
        resp.addProperty("ok", true);
        resp.addProperty("id", t.id);
        resp.addProperty("topic", t.topic);
        resp.addProperty("message", t.message);
        resp.add("ticket", ticketToJson(t));
        ctx.contentType("application/json").result(GSON.toJson(resp));
    }

    /** GET /api/pd/tickets/mine — eigene Tickets. */
    public static void handleMyTickets(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        JsonArray arr = new JsonArray();
        for (PremiumMotorsportManager.ContactTicket t : PremiumMotorsportManager.getMyTickets(info.guildId, info.userId))
            arr.add(ticketToJson(t));
        JsonObject r = new JsonObject();
        r.addProperty("ok", true);
        r.add("tickets", arr);
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    /** GET /api/pd/tickets/all?status=open|resolved|closed — Mitarbeiter-Liste. */
    public static void handleAllTickets(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        if (!requireEmployee(ctx, info)) return;
        String filter = ctx.queryParam("status");
        JsonArray arr = new JsonArray();
        List<PremiumMotorsportManager.ContactTicket> all = PremiumMotorsportManager.getAllTickets(info.guildId);
        // neuste zuerst
        all.sort((a, b) -> Long.compare(b.createdAt, a.createdAt));
        for (PremiumMotorsportManager.ContactTicket t : all) {
            if (filter != null && !filter.isBlank() && !filter.equalsIgnoreCase(t.status)) continue;
            arr.add(ticketToJson(t));
        }
        JsonObject r = new JsonObject();
        r.addProperty("ok", true);
        r.add("tickets", arr);
        ctx.contentType("application/json").result(GSON.toJson(r));
    }

    /** POST /api/pd/tickets/{id}/status — Body: {status}. Setzt Status auf resolved/closed. */
    public static void handleSetTicketStatus(Context ctx) {
        PremiumMotorsportManager.AuthInfo info = auth(ctx);
        if (info == null) return;
        if (!requireEmployee(ctx, info)) return;
        JsonObject body;
        try { body = JsonParser.parseString(ctx.body()).getAsJsonObject(); }
        catch (Exception e) { err(ctx, 400, "Ungültige JSON-Anfrage."); return; }
        String status = safeTrim(body.has("status") ? body.get("status").getAsString() : "");
        if (!status.equals("open") && !status.equals("resolved") && !status.equals("closed")) {
            err(ctx, 400, "Status muss open|resolved|closed sein."); return;
        }
        if (!PremiumMotorsportManager.setTicketStatus(info.guildId, ctx.pathParam("id"), status)) {
            err(ctx, 404, "Ticket nicht gefunden.");
            return;
        }
        ok(ctx);
    }

    private static JsonObject ticketToJson(PremiumMotorsportManager.ContactTicket t) {
        JsonObject o = new JsonObject();
        o.addProperty("id", t.id);
        o.addProperty("userId", t.userId);
        o.addProperty("displayName", t.displayName);
        o.addProperty("topic", t.topic);
        o.addProperty("message", t.message);
        o.addProperty("status", t.status);
        o.addProperty("createdAt", t.createdAt);
        if (t.resolvedAt != null) o.addProperty("resolvedAt", t.resolvedAt);
        return o;
    }

    // ── Util ───────────────────────────────────────────────────────────────────

    private static JsonObject vToJson(PremiumMotorsportManager.Vehicle v) {
        JsonObject o = new JsonObject();
        o.addProperty("id", v.id);
        o.addProperty("name", v.name);
        o.addProperty("category", v.category);
        o.addProperty("description", v.description);
        o.addProperty("price", v.price);
        o.addProperty("priceFmt", ShopManager.formatPrice(v.price));
        o.addProperty("imageUrl", v.imageUrl);
        o.addProperty("stock", v.stock);
        o.addProperty("createdAt", v.createdAt);
        return o;
    }
}
