package de.pcrp.bot.web;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import de.pcrp.bot.common.BotContext;
import de.pcrp.bot.common.DataStore;
import de.pcrp.bot.common.DocumentsManager;
import de.pcrp.bot.common.LapdDashManager;
import de.pcrp.bot.common.LoggingConfig;
import de.pcrp.bot.common.ModerationConfig;
import io.javalin.http.Context;
import io.javalin.http.UploadedFile;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

/**
 * HTTP-Routes für das LAPD-Beamten-Dashboard (externe Seite /lapd/dashboard).
 *
 * Login läuft über Dienstgrad + Passwort (vorerst LAPD_2026). Der Bot prüft bei
 * jedem Login nur noch: Ist die Person auf dem Discord-Server UND wurde sie von
 * einem Administrator eingetragen (Zugriffs-Verwaltung)? Der Inhaber und
 * Administratoren (High-Team-Rolle) haben automatisch vollen Zugriff.
 */
public class LapdDashHandler {

    private static final Logger log  = LoggerFactory.getLogger(LapdDashHandler.class);
    private static final Gson   GSON = new GsonBuilder().create();

    private LapdDashHandler() {}

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

    private static void respond(Context ctx, JsonObject out) {
        ctx.contentType("application/json").result(GSON.toJson(out));
    }

    private static void err(Context ctx, JsonObject out, String msg) {
        out.addProperty("ok", false);
        out.addProperty("error", msg);
        respond(ctx, out);
    }

    private static boolean hasRole(Member m, long roleId) {
        return m != null && m.getRoles().stream().anyMatch(r -> r.getIdLong() == roleId);
    }

    /**
     * Auth-Guard: prüft das Session-Token und die benötigte Berechtigung.
     * Gibt die Session zurück oder null (Fehler wurde bereits geschrieben).
     */
    private static LapdDashManager.Session check(Context ctx, JsonObject out, Long gid, boolean admin, boolean leader) {
        JsonObject b = body(ctx);
        String token = str(b, "token");
        if (token.isEmpty()) token = ctx.queryParam("token"); // GET-Aufrufe transportieren das Token im Query
        LapdDashManager.Session s = LapdDashManager.validateSession(gid, token);
        if (s == null) {
            err(ctx, out, "Sitzung abgelaufen – bitte neu einloggen.");
            return null;
        }
        if (admin && !s.admin) {
            err(ctx, out, "Nur für Administratoren.");
            return null;
        }
        if (leader && !s.leader && !s.admin) {
            err(ctx, out, "Nur für die Leitungs-Ebene.");
            return null;
        }
        return s;
    }

    // ── Login / Logout / Me ──────────────────────────────────────────────────

    /** POST /api/lapd/dash/login – Dienstgrad + Passwort + Discord-Name/ID. */
    public static void handleLogin(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        Guild guild = BotContext.getGuild();

        JsonObject b = body(ctx);
        String discord = str(b, "discord");
        String rank    = str(b, "rank");
        String pass    = str(b, "password");

        if (discord.isEmpty()) { err(ctx, out, "Bitte gib deinen Discord-Namen oder deine Discord-ID ein."); return; }
        if (rank.isEmpty())    { err(ctx, out, "Bitte wähle deinen Dienstgrad."); return; }
        if (pass.isEmpty())    { err(ctx, out, "Bitte gib das Passwort ein."); return; }
        if (!LoggingConfig.LAPD_DASHBOARD_PASSWORD.equals(pass)) {
            err(ctx, out, "Falsches Passwort.");
            return;
        }
        if (!LapdDashManager.isValidRank(rank)) {
            err(ctx, out, "Ungültiger Dienstgrad.");
            return;
        }

        // Nur Discord-Username – keine ID
        Member m = BotContext.findMemberByUsername(discord);
        if (m == null) {
            err(ctx, out, "Person nicht auf dem Discord-Server gefunden – Login nicht möglich.");
            return;
        }

        // Der Inhaber hat automatisch Administrator-Zugriff und kann nie gesperrt werden
        boolean owner = m.getIdLong() == ModerationConfig.OWNER_ID;
        boolean admin = owner || hasRole(m, LoggingConfig.LAPD_ADMIN_ROLE_ID);

        // Bann-Prüfung: vor dem Login rot pulsierende Sperr-Anzeige
        if (!owner && LapdDashManager.isBanned(gid, m.getId())) {
            out.addProperty("ok", false);
            out.addProperty("banned", true);
            out.addProperty("error", "Dein Zugriff wurde von einem Administrator gesperrt. Sollte das ein Fehler sein, wende dich bitte an das High Team im Discord.");
            respond(ctx, out);
            return;
        }

        // Der Inhaber wird im Dashboard als „Inhaber“ mit Dienstgrad „Administrator“ geführt
        String displayName = m.getEffectiveName();
        String displayRank = rank;
        if (owner) {
            displayName = "Inhaber";
            displayRank = "Administrator";
        }

        // Inhaber/Administratoren werden dauerhaft registriert, damit sie z. B. in den
        // Auswahlen (Abmahnen/Kündigen/Zuweisen) erscheinen.
        if (owner) {
            LapdDashManager.addAccess(gid, m.getId(), displayRank, displayName); // upsert
        } else if (admin && LapdDashManager.findAccess(gid, m.getId()) == null) {
            LapdDashManager.addAccess(gid, m.getId(), displayRank, displayName);
        }

        // Administratoren können sich mit jedem Dienstgrad einloggen.
        // Alle anderen nur, wenn sie von einem Administrator eingetragen wurden
        // (Zugriffs-Verwaltung) – und nur mit dem dort zugewiesenen Dienstgrad.
        if (!admin) {
            LapdDashManager.AccessEntry a = LapdDashManager.findAccess(gid, m.getId());
            if (a == null) {
                err(ctx, out, "Kein Zugriff – deine Discord-ID wurde noch nicht von einem Administrator freigeschaltet.");
                return;
            }
            if (!a.rank.equals(rank)) {
                err(ctx, out, "Kein Zugriff mit diesem Dienstgrad – dein freigeschalteter Dienstgrad ist „" + a.rank + "“.");
                return;
            }
        }

        boolean leader = LapdDashManager.isLeaderRank(displayRank);
        String token = LapdDashManager.createSession(gid, m.getId(), displayName, displayRank, admin, leader);

        out.addProperty("ok", true);
        out.addProperty("token", token);
        out.addProperty("name", displayName);
        out.addProperty("rank", displayRank);
        out.addProperty("admin", admin);
        out.addProperty("leader", leader);
        respond(ctx, out);
    }

    /** POST /api/lapd/dash/logout. */
    public static void handleLogout(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        JsonObject b = body(ctx);
        LapdDashManager.destroySession(gid, str(b, "token"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    /** GET /api/lapd/dash/me?token=… – Session-Infos + Dienst-Status. */
    public static void handleMe(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = LapdDashManager.validateSession(gid, ctx.queryParam("token"));
        if (s == null) { err(ctx, out, "Sitzung abgelaufen – bitte neu einloggen."); return; }
        out.addProperty("ok", true);
        out.addProperty("name", s.name);
        out.addProperty("rank", s.rank);
        out.addProperty("admin", s.admin);
        out.addProperty("leader", s.leader);
        out.addProperty("onDuty", LapdDashManager.isOnDuty(gid, s.discordId));
        respond(ctx, out);
    }

    // ── Zugriff Verwalten (Administrator) ────────────────────────────────────

    public static void handleAccessList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, false);
        if (s == null) return;
        out.addProperty("ok", true);
        out.add("access", GSON.toJsonTree(LapdDashManager.accessList(gid)));
        respond(ctx, out);
    }

    public static void handleAccessAdd(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String discordId = str(b, "discordId");
        String rank      = str(b, "rank");
        String name = "";
        Member m = BotContext.getGuild().getMemberById(discordId);
        if (m != null) name = m.getEffectiveName();

        String error = LapdDashManager.addAccess(gid, discordId, rank, name);
        if (error != null) { err(ctx, out, error); return; }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleAccessDelete(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, false);
        if (s == null) return;
        JsonObject b = body(ctx);
        LapdDashManager.removeAccess(gid, str(b, "discordId"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Nutzer Bannen (Administrator) ────────────────────────────────────────

    public static void handleBanList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, false);
        if (s == null) return;
        out.addProperty("ok", true);
        out.add("banned", GSON.toJsonTree(LapdDashManager.bannedList(gid)));
        respond(ctx, out);
    }

    public static void handleBan(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String discordId = str(b, "discordId");
        if (discordId.isEmpty()) { err(ctx, out, "Discord-ID fehlt."); return; }
        if (discordId.equals(s.discordId)) { err(ctx, out, "Du kannst dich nicht selbst bannen."); return; }
        if (discordId.equals(String.valueOf(ModerationConfig.OWNER_ID))) { err(ctx, out, "Der Inhaber kann nicht gebannt werden."); return; }
        String name = "";
        Member m = BotContext.getGuild().getMemberById(discordId);
        if (m != null) name = m.getEffectiveName();
        LapdDashManager.ban(gid, discordId, name, str(b, "reason"), s.name);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleUnban(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, false);
        if (s == null) return;
        JsonObject b = body(ctx);
        LapdDashManager.unban(gid, str(b, "discordId"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Fuhrpark Verwalten (Administrator) ───────────────────────────────────

    public static void handleFleetAdd(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String title = str(b, "title");
        if (title.isEmpty()) { err(ctx, out, "Titel fehlt."); return; }
        LapdDashManager.addVehicle(gid, title, str(b, "image"), str(b, "description"), s.name);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    /** POST /api/lapd/dash/fleet/upload – Fahrzeug mit Bild-Datei (multipart). */
    public static void handleFleetUpload(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        String token = ctx.formParam("token");
        LapdDashManager.Session s = LapdDashManager.validateSession(gid, token);
        if (s == null) { err(ctx, out, "Sitzung abgelaufen – bitte neu einloggen."); return; }
        if (!s.admin) { err(ctx, out, "Nur für Administratoren."); return; }

        String title = ctx.formParam("title");
        String desc  = ctx.formParam("description");
        UploadedFile photo = ctx.uploadedFile("image");
        if (title == null || title.isBlank()) { err(ctx, out, "Titel fehlt."); return; }
        if (photo == null) { err(ctx, out, "Bitte lade eine Bilddatei hoch."); return; }

        String fid = UUID.randomUUID().toString().replace("-", "").substring(0, 10);
        String ext = photo.contentType() != null && photo.contentType().contains("png") ? ".png" : ".jpg";
        Path p = DataStore.getPath("photos").resolve("fleet-" + fid + ext);
        try {
            Files.createDirectories(p.getParent());
            Files.copy(photo.content(), p, StandardCopyOption.REPLACE_EXISTING);
        } catch (Exception e) {
            log.error("[LAPD-Dash] Fahrzeugbild konnte nicht gespeichert werden.", e);
            err(ctx, out, "Bild konnte nicht gespeichert werden.");
            return;
        }

        LapdDashManager.addVehicle(gid, title, "/api/lapd/fleet-image/" + fid, desc == null ? "" : desc, s.name);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleFleetDelete(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, false);
        if (s == null) return;
        JsonObject b = body(ctx);
        LapdDashManager.deleteVehicle(gid, str(b, "id"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Mitarbeiter Liste (Leitung) ──────────────────────────────────────────

    public static void handleEmployeeList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;
        out.addProperty("ok", true);
        out.add("employees", GSON.toJsonTree(LapdDashManager.employees(gid)));
        respond(ctx, out);
    }

    public static void handleEmployeeAdd(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;

        JsonObject b = body(ctx);
        String name = str(b, "name");
        String rank = str(b, "rank");
        if (name.isEmpty() || rank.isEmpty()) { err(ctx, out, "Name und Rang sind Pflichtfelder."); return; }
        LapdDashManager.addEmployee(gid, name, rank, str(b, "discordId"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleEmployeeEdit(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;

        JsonObject b = body(ctx);
        if (!LapdDashManager.editEmployee(gid, str(b, "id"), str(b, "name"), str(b, "rank"))) {
            err(ctx, out, "Mitarbeiter nicht gefunden.");
            return;
        }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleEmployeeDelete(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;
        JsonObject b = body(ctx);
        LapdDashManager.deleteEmployee(gid, str(b, "id"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Abmahnen (Leitung) ───────────────────────────────────────────────────

    public static void handleWarn(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;

        JsonObject b = body(ctx);
        String discordId = str(b, "discordId");
        if (discordId.isEmpty()) { err(ctx, out, "Wähle einen Mitarbeiter aus."); return; }
        if (discordId.equals(s.discordId)) { err(ctx, out, "Du kannst dich nicht selbst abmahnen."); return; }
        if (discordId.equals(String.valueOf(ModerationConfig.OWNER_ID))) { err(ctx, out, "Der Inhaber kann nicht abgemahnt werden."); return; }
        // Admins sind unantastbar
        Member target = BotContext.getGuild().getMemberById(discordId);
        if (target != null && hasRole(target, LoggingConfig.LAPD_ADMIN_ROLE_ID)) {
            err(ctx, out, "Administratoren können nicht abgemahnt werden.");
            return;
        }
        String reason = str(b, "reason");
        if (reason.isEmpty()) { err(ctx, out, "Bitte gib einen Grund an."); return; }
        String name = target != null ? target.getEffectiveName() : discordId;
        LapdDashManager.warn(gid, discordId, name, reason, s.name);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    /** POST /api/lapd/dash/warn/me – eigene Abmahnungen der eingeloggten Person. */
    public static void handleWarnMe(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        out.addProperty("ok", true);
        out.add("warnings", GSON.toJsonTree(LapdDashManager.warningsOf(gid, s.discordId)));
        respond(ctx, out);
    }

    // ── Kündigen (Leitung) ───────────────────────────────────────────────────

    public static void handleFire(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;

        JsonObject b = body(ctx);
        String discordId = str(b, "discordId");
        if (discordId.isEmpty()) { err(ctx, out, "Wähle einen Mitarbeiter aus."); return; }
        if (discordId.equals(s.discordId)) { err(ctx, out, "Du kannst dich nicht selbst kündigen."); return; }
        if (discordId.equals(String.valueOf(ModerationConfig.OWNER_ID))) { err(ctx, out, "Der Inhaber kann nicht gekündigt werden."); return; }
        Member target = BotContext.getGuild().getMemberById(discordId);
        if (target != null && hasRole(target, LoggingConfig.LAPD_ADMIN_ROLE_ID)) {
            err(ctx, out, "Administratoren können nicht gekündigt werden.");
            return;
        }
        String reason = str(b, "reason");
        String name = target != null ? target.getEffectiveName() : discordId;
        LapdDashManager.fire(gid, discordId);
        // DM an die gekündigte Person
        String msg = "⚠️ **Sie wurden aus dem LAPD entlassen.**\n\n**Grund:** " + (reason.isEmpty() ? "Keine Angabe" : reason)
                   + "\n\nIhr Dashboard-Zugriff wurde entzogen.";
        LapdDashManager.sendDm(BotContext.getGuild(), discordId, msg);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Urlaub ───────────────────────────────────────────────────────────────

    public static void handleVacationList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        out.addProperty("ok", true);
        // ?all=1 → alle Anträge (nur Leitung), sonst nur die eigenen
        if ((s.leader || s.admin) && ctx.queryParam("all") != null) {
            out.add("vacations", GSON.toJsonTree(LapdDashManager.vacations(gid)));
        } else {
            out.add("vacations", GSON.toJsonTree(LapdDashManager.vacationsOf(gid, s.discordId)));
        }
        respond(ctx, out);
    }

    public static void handleVacationRequest(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String from = str(b, "from");
        String to   = str(b, "to");
        if (from.isEmpty() || to.isEmpty()) { err(ctx, out, "Bitte Zeitraum angeben."); return; }
        LapdDashManager.requestVacation(gid, s.discordId, s.name, from, to, str(b, "reason"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    /** POST /api/lapd/dash/vacation/delete – Urlaubsantrag endgültig löschen. */
    public static void handleVacationDelete(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String id = str(b, "id");
        if (id.isEmpty()) { err(ctx, out, "Antrag fehlt."); return; }

        // Nur Leitung darf fremde Anträge löschen – alle anderen nur ihre eigenen.
        boolean allowed = s.leader || s.admin;
        if (!allowed) {
            LapdDashManager.Vacation v = null;
            for (LapdDashManager.Vacation x : LapdDashManager.vacationsOf(gid, s.discordId)) {
                if (x.id.equals(id)) { v = x; break; }
            }
            if (v == null) { err(ctx, out, "Antrag nicht gefunden."); return; }
        }
        if (!LapdDashManager.deleteVacation(gid, id)) { err(ctx, out, "Antrag nicht gefunden."); return; }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleVacationDecide(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;

        JsonObject b = body(ctx);
        String action = str(b, "action");
        String status = "genehmigt".equals(action) ? "genehmigt" : ("abgelehnt".equals(action) ? "abgelehnt" : "");
        if (status.isEmpty()) { err(ctx, out, "Unbekannte Aktion."); return; }

        // DM an den Antragsteller
        LapdDashManager.Vacation v = null;
        for (LapdDashManager.Vacation x : LapdDashManager.vacations(gid)) {
            if (x.id.equals(str(b, "id"))) { v = x; break; }
        }
        if (v == null) { err(ctx, out, "Antrag nicht gefunden."); return; }
        if (!LapdDashManager.decideVacation(gid, v.id, status)) { err(ctx, out, "Antrag konnte nicht aktualisiert werden."); return; }

        String msg = "🏖️ **Urlaubsantrag " + ("genehmigt".equals(status) ? "genehmigt" : "abgelehnt") + "**\n\n"
                   + "**Zeitraum:** " + v.from + " bis " + v.to + "\n"
                   + ("genehmigt".equals(status)
                       ? "Viel Erholung!"
                       : "Dein Urlaubsantrag wurde leider abgelehnt.");
        LapdDashManager.sendDm(BotContext.getGuild(), v.discordId, msg);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Zuweisen (Leitung) ───────────────────────────────────────────────────

    public static void handleAssign(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;

        JsonObject b = body(ctx);
        String discordId = str(b, "discordId");
        String shift     = str(b, "shift");
        if (discordId.isEmpty() || shift.isEmpty()) { err(ctx, out, "Mitarbeiter und Schicht auswählen."); return; }
        String name = "";
        Member m = BotContext.getGuild().getMemberById(discordId);
        if (m != null) name = m.getEffectiveName();
        LapdDashManager.assign(gid, discordId, name.isEmpty() ? discordId : name, shift);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Information Schreiben (Leitung) ──────────────────────────────────────

    public static void handleInfoAdd(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;

        JsonObject b = body(ctx);
        String target = str(b, "target");
        String title  = str(b, "title");
        String text   = str(b, "text");
        if (!"website".equals(target) && !"lapd".equals(target) && !"discord".equals(target)) {
            err(ctx, out, "Ungültiges Ziel.");
            return;
        }
        if (title.isEmpty() || text.isEmpty()) { err(ctx, out, "Titel und Text sind Pflichtfelder."); return; }
        LapdDashManager.InfoPost info = LapdDashManager.addInfo(gid, target, title, text, s.name);
        if ("discord".equals(target)) {
            LapdDashManager.postInfoToDiscord(BotContext.getGuild(), info);
        }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleInfoDelete(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;
        JsonObject b = body(ctx);
        LapdDashManager.deleteInfo(gid, str(b, "id"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Dienst ───────────────────────────────────────────────────────────────

    public static void handleDutyList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        out.addProperty("ok", true);
        out.add("duty", GSON.toJsonTree(LapdDashManager.duty(gid)));
        respond(ctx, out);
    }

    public static void handleDutyOn(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        LapdDashManager.dutyOn(gid, s.discordId, s.name, s.rank);
        LapdDashManager.refreshDutyEmbed(BotContext.getGuild());
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleDutyOff(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        LapdDashManager.dutyOff(gid, s.discordId);
        LapdDashManager.refreshDutyEmbed(BotContext.getGuild());
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Fahndungen ───────────────────────────────────────────────────────────

    public static void handleWantedList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        out.addProperty("ok", true);
        out.add("wanted", GSON.toJsonTree(LapdDashManager.wanted(gid)));
        respond(ctx, out);
    }

    public static void handleWantedAdd(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        JsonObject b = body(ctx);
        String title = str(b, "title");
        if (title.isEmpty()) { err(ctx, out, "Titel fehlt."); return; }
        LapdDashManager.addWanted(gid, title, str(b, "description"), s.name);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleWantedDelete(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;
        JsonObject b = body(ctx);
        LapdDashManager.deleteWanted(gid, str(b, "id"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Einsätze / Dispatches ────────────────────────────────────────────────

    public static void handleDispatchList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        out.addProperty("ok", true);
        out.add("dispatches", GSON.toJsonTree(LapdDashManager.dispatches(gid)));
        out.add("reports", GSON.toJsonTree(LapdDashManager.reports(gid)));
        respond(ctx, out);
    }

    public static void handleDispatchAccept(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        LapdDashManager.Dispatch d = LapdDashManager.acceptDispatch(gid, str(b, "id"), s.name);
        if (d == null) { err(ctx, out, "Einsatz ist nicht mehr offen – er wurde bereits angenommen."); return; }

        // Sofort DM an den Absender
        String msg = "🚨 **Ihr Einsatz wurde angenommen!**\n\n"
                   + "Die Einsatzkräfte sind auf dem Weg. Bleiben Sie bitte an Ihrem Standort.\n\n"
                   + "**Einsatz:** " + (d.type.isEmpty() ? "—" : d.type) + "\n"
                   + "**Ort:** " + (d.location.isEmpty() ? "—" : d.location);
        LapdDashManager.sendDm(BotContext.getGuild(), d.senderId, msg);

        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleDispatchReport(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String text = str(b, "text");
        if (text.isEmpty()) { err(ctx, out, "Bitte schreibe einen Einsatzbericht."); return; }
        LapdDashManager.DispatchReport r = LapdDashManager.completeDispatch(gid, str(b, "id"), text, s.name);
        if (r == null) { err(ctx, out, "Einsatz nicht gefunden."); return; }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    /** POST /api/lapd/dispatch – Eingang neuer Einsätze (aus Discord / Smartphone). */
    public static void handleDispatchIngest(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        JsonObject b = body(ctx);
        String senderName = str(b, "senderName");
        String type       = str(b, "type");
        if (senderName.isEmpty() || type.isEmpty()) { err(ctx, out, "Absender und Einsatztyp fehlen."); return; }
        LapdDashManager.addDispatch(gid, senderName, str(b, "senderId"), type, str(b, "location"), str(b, "details"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Akten (Personen + Strafakten) ────────────────────────────────────────

    public static void handleAktenList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        out.addProperty("ok", true);
        out.add("personAkten", GSON.toJsonTree(LapdDashManager.personAkten(gid)));
        out.add("strafAkten",  GSON.toJsonTree(LapdDashManager.strafAkten(gid)));
        respond(ctx, out);
    }

    private static Map<String, String> fieldsOf(JsonObject b) {
        Map<String, String> fields = new LinkedHashMap<>();
        if (b != null && b.has("fields") && b.get("fields").isJsonObject()) {
            JsonObject fo = b.getAsJsonObject("fields");
            for (Map.Entry<String, JsonElement> e : fo.entrySet()) {
                if (e.getValue() != null && !e.getValue().isJsonNull()) {
                    fields.put(e.getKey(), e.getValue().getAsString().trim());
                }
            }
        }
        return fields;
    }

    public static void handleAkteAdd(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String kind = str(b, "kind");
        String name = str(b, "name");
        if (name.isEmpty()) { err(ctx, out, "Name fehlt."); return; }
        if ("person".equals(kind)) {
            LapdDashManager.addPersonAkte(gid, name, str(b, "discordId"), fieldsOf(b), s.name);
        } else if ("straf".equals(kind)) {
            LapdDashManager.addStrafakte(gid, name, str(b, "discordId"), fieldsOf(b), s.name);
        } else {
            err(ctx, out, "Unbekannte Aktenart.");
            return;
        }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleAkteEdit(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String kind = str(b, "kind");
        String id   = str(b, "id");
        boolean ok;
        if ("person".equals(kind)) {
            ok = LapdDashManager.editPersonAkte(gid, id, fieldsOf(b));
        } else if ("straf".equals(kind)) {
            ok = LapdDashManager.editStrafakte(gid, id, fieldsOf(b));
        } else {
            err(ctx, out, "Unbekannte Aktenart.");
            return;
        }
        if (!ok) { err(ctx, out, "Akte nicht gefunden."); return; }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleAkteDelete(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;

        JsonObject b = body(ctx);
        String kind = str(b, "kind");
        String id   = str(b, "id");
        if ("person".equals(kind)) {
            LapdDashManager.deletePersonAkte(gid, id);
        } else if ("straf".equals(kind)) {
            LapdDashManager.deleteStrafakte(gid, id);
        } else {
            err(ctx, out, "Unbekannte Aktenart.");
            return;
        }
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Führerscheine ────────────────────────────────────────────────────────

    public static void handleLicenseList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;

        String prefix = "fuehrerschein-" + gid + "-";
        com.google.gson.JsonArray arr = new com.google.gson.JsonArray();
        for (String file : DataStore.listFiles(prefix)) {
            String userId = file.substring(prefix.length());
            if (userId.isEmpty()) continue;
            var opt = DocumentsManager.getFuehrerschein(gid.toString(), userId);
            if (opt.isEmpty()) continue;
            DocumentsManager.Fuehrerschein f = opt.get();
            JsonObject o = new JsonObject();
            o.addProperty("userId", userId);
            o.addProperty("vorname", f.vorname);
            o.addProperty("nachname", f.nachname);
            o.addProperty("geburtsdatum", f.geburtsdatum);
            o.addProperty("adresse", f.adresse);
            if (f.klassen != null) o.add("klassen", GSON.toJsonTree(f.klassen));
            o.addProperty("gueltigBis", f.gueltigBis);
            o.addProperty("revoked", LapdDashManager.isLicenseRevoked(gid, userId));
            Member m = BotContext.getGuild().getMemberById(userId);
            o.addProperty("discordName", m != null ? m.getEffectiveName() : userId);
            arr.add(o);
        }
        out.addProperty("ok", true);
        out.add("licenses", arr);
        out.add("revokes", GSON.toJsonTree(LapdDashManager.licenseRevokes(gid)));
        respond(ctx, out);
    }

    public static void handleLicenseRevoke(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String userId = str(b, "userId");
        if (userId.isEmpty()) { err(ctx, out, "Nutzer-ID fehlt."); return; }
        String name = "";
        Member m = BotContext.getGuild().getMemberById(userId);
        if (m != null) name = m.getEffectiveName();
        LapdDashManager.revokeLicense(gid, userId, name.isEmpty() ? userId : name, str(b, "reason"), s.name);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    public static void handleLicenseReturn(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        JsonObject b = body(ctx);
        LapdDashManager.returnLicense(gid, str(b, "userId"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Ausrüstung (Leitung schreibt, alle sehen) ────────────────────────────

    /** GET /api/lapd/dash/equipment?token=… – Liste + canManage-Flag. */
    public static void handleEquipmentList(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;
        out.addProperty("ok", true);
        out.add("equipment", GSON.toJsonTree(LapdDashManager.equipment(gid)));
        out.addProperty("canManage", s.leader || s.admin);
        respond(ctx, out);
    }

    /** POST /api/lapd/dash/equipment – Ausrüstung hinzufügen (multipart, nur Leitung). */
    public static void handleEquipmentAdd(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;

        String token = ctx.formParam("token");
        LapdDashManager.Session s = LapdDashManager.validateSession(gid, token);
        if (s == null) { err(ctx, out, "Sitzung abgelaufen – bitte neu einloggen."); return; }
        if (!s.leader && !s.admin) { err(ctx, out, "Nur für die Leitungs-Ebene."); return; }

        String title = ctx.formParam("title");
        String desc  = ctx.formParam("description");
        String access = ctx.formParam("access");
        UploadedFile photo = ctx.uploadedFile("image");
        if (title == null || title.isBlank()) { err(ctx, out, "Titel fehlt."); return; }
        if (access == null || access.isBlank()) access = "alle";

        String image = "";
        if (photo != null) {
            String eid = UUID.randomUUID().toString().replace("-", "").substring(0, 10);
            String ext = photo.contentType() != null && photo.contentType().contains("png") ? ".png" : ".jpg";
            Path p = DataStore.getPath("photos").resolve("equip-" + eid + ext);
            try {
                Files.createDirectories(p.getParent());
                Files.copy(photo.content(), p, StandardCopyOption.REPLACE_EXISTING);
                image = "/api/lapd/equip-image/" + eid;
            } catch (Exception e) {
                log.error("[LAPD-Dash] Ausrüstungsbild konnte nicht gespeichert werden.", e);
                err(ctx, out, "Bild konnte nicht gespeichert werden.");
                return;
            }
        }

        LapdDashManager.addEquipment(gid, title, desc == null ? "" : desc, access, image, s.name);
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    /** POST /api/lapd/dash/equipment/delete – Ausrüstung löschen (nur Leitung). */
    public static void handleEquipmentDelete(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, true, true);
        if (s == null) return;
        JsonObject b = body(ctx);
        LapdDashManager.deleteEquipment(gid, str(b, "id"));
        out.addProperty("ok", true);
        respond(ctx, out);
    }

    // ── Panic Button ──────────────────────────────────────────────────────────

    /** POST /api/lapd/dash/panic – Alarm an alle Beamten im Dienst (DM). */
    public static void handlePanic(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        LapdDashManager.Session s = check(ctx, out, gid, false, false);
        if (s == null) return;

        JsonObject b = body(ctx);
        String location = str(b, "location");
        if (location.isEmpty()) { err(ctx, out, "Bitte gib deinen Standort (PSN) an."); return; }

        Guild guild = BotContext.getGuild();
        java.util.List<LapdDashManager.Duty> duty = LapdDashManager.duty(gid);
        if (duty.isEmpty()) {
            err(ctx, out, "Derzeit ist niemand im Dienst – der Alarm konnte nicht übermittelt werden.");
            return;
        }

        int sent = 0;
        for (LapdDashManager.Duty d : duty) {
            if (d.discordId.equals(s.discordId)) continue; // nicht sich selbst
            String msg = "🚨 **PANIC ALARM!**\n\n"
                       + "**" + s.name + "** (" + s.rank + ") hat den **Panic Button** ausgelöst und benötigt sofort Unterstützung!\n\n"
                       + "📍 **Standort (PSN):** `" + location + "`\n\n"
                       + "Bitte umgehend Hilfe leisten.";
            LapdDashManager.sendDm(guild, d.discordId, msg);
            sent++;
        }

        out.addProperty("ok", true);
        out.addProperty("sent", sent);
        respond(ctx, out);
    }

    // ── Öffentliche Daten für die Webseite ───────────────────────────────────

    /** GET /api/lapd/public – Infos (Webseite), Mitarbeiter, Fuhrpark, Dienst. */
    public static void handlePublic(Context ctx) {
        JsonObject out = new JsonObject();
        Long gid = guildId(ctx, out);
        if (gid == null) return;
        out.addProperty("ok", true);
        out.add("infos", GSON.toJsonTree(LapdDashManager.infosByTarget(gid, "website")));
        out.add("employees", GSON.toJsonTree(LapdDashManager.employees(gid)));
        out.add("fleet", GSON.toJsonTree(LapdDashManager.fleet(gid)));
        out.add("duty", GSON.toJsonTree(LapdDashManager.duty(gid)));
        respond(ctx, out);
    }
}
