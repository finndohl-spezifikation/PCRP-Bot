package de.pcrp.bot.common;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.entities.Message;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Datenhaltung für das LAPD-Beamten-Dashboard (externe Seite /lapd/dashboard).
 * Persistenz pro Guild in einer JSON-Datei (lapd-dash-&lt;guildId&gt;.json).
 *
 * Enthält: Zugriffsliste (Discord-ID → Dienstgrad), Bann-Liste, Fuhrpark,
 * Mitarbeiter, Abmahnungen, Kündigungen, Urlaubsanträge, Schicht-Zuweisungen,
 * Informationen, Dienst-Schicht (wer ist im Dienst), Fahndungen, Einsätze,
 * Einsatzberichte, Personen-Akten, Strafakten, Führerschein-Entzüge und
 * Login-Sessions.
 */
public final class LapdDashManager {

    private static final Logger log = LoggerFactory.getLogger(LapdDashManager.class);
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    /** Alle Dienstgrade in der festen Reihenfolge der Auswahl. */
    public static final List<String> RANKS = List.of(
        "Chief Of Police", "Deputy Chief", "Assistant Chief", "Commander", "Captain",
        "Lieutenant", "Sergeant", "Detective", "Officer", "Rooky");

    /** Dienstgrade mit Zugriff auf die Kategorie „Leitungs Ebene". */
    public static final Set<String> LEADER_RANKS = Set.of(
        "Chief Of Police", "Deputy Chief", "Assistant Chief", "Commander", "Captain", "Lieutenant");

    /** Gültigkeitsdauer einer Login-Session. */
    public static final long SESSION_TTL_MS = 12L * 60 * 60 * 1000;

    // ── Datenklassen ──────────────────────────────────────────────────────────

    public static class AccessEntry {
        public String discordId;
        public String rank;
        public String name;
        public long   ts;
    }

    public static class Ban {
        public String discordId;
        public String name;
        public String webName;   // optionaler Name auf der LAPD-Webseite (wird dort geblockt)
        public String reason;
        public String by;
        public long   ts;
    }

    public static class Vehicle {
        public String id;
        public String title;
        public String image;
        public String description;
        public String by;
        public long   ts;
    }

    public static class Employee {
        public String id;
        public String name;
        public String rank;
        public String discordId;
        public long   ts;
    }

    public static class Warning {
        public String id;
        public String discordId;
        public String name;
        public String reason;
        public String by;
        public long   ts;
    }

    public static class Vacation {
        public String id;
        public String discordId;
        public String name;
        public String from;
        public String to;
        public String reason;
        public String status = "offen"; // offen / genehmigt / abgelehnt
        public long   ts;
    }

    public static class Assignment {
        public String id;
        public String discordId;
        public String name;
        public String shift;
        public long   ts;
    }

    public static class InfoPost {
        public String id;
        public String target;   // website | lapd | discord
        public String title;
        public String text;
        public String by;
        public long   ts;
        public String discordMsgId; // gesetzt wenn in Discord gepostet
    }

    public static class Duty {
        public String discordId;
        public String name;
        public String rank;
        public long   startedAt;
    }

    public static class Wanted {
        public String id;
        public String title;
        public String description;
        public String by;
        public long   ts;
    }

    public static class Dispatch {
        public String id;
        public String senderName;
        public String senderId;
        public String type;
        public String location;
        public String details;
        public String status = "offen"; // offen / angenommen / abgeschlossen
        public String acceptedBy;
        public long   acceptedAt;
        public long   ts;
    }

    public static class DispatchReport {
        public String id;
        public String dispatchId;
        public String text;
        public String by;
        public long   ts;
    }

    public static class PersonAkte {
        public String id;
        public String name;
        public String discordId;
        public Map<String, String> data = new LinkedHashMap<>();
        public String createdBy;
        public long   ts;
    }

    public static class Strafakte {
        public String id;
        public String name;
        public String discordId;
        public Map<String, String> data = new LinkedHashMap<>();
        public String createdBy;
        public long   ts;
    }

    public static class LicenseRevoke {
        public String userId;
        public String name;
        public String reason;
        public String by;
        public long   ts;
    }

    public static class Equipment {
        public String id;
        public String category; // kleidung | waffen | fahrzeuge
        public String title;
        public String description;
        public String access;   // alle | beamte | leitung | admin
        public String image;    // URL zum Bild
        public String by;
        public long   ts;
    }

    public static class Session {
        public String discordId;
        public String name;
        public String rank;
        public boolean admin;
        public boolean leader;
        public long expiresAt;
    }

    /** Kompletter Datenbestand einer Guild. */
    public static class Store {
        public List<AccessEntry>   access       = new ArrayList<>();
        public List<Ban>           banned       = new ArrayList<>();
        public List<Vehicle>       fleet        = new ArrayList<>();
        public List<Employee>      employees    = new ArrayList<>();
        public List<Warning>       warnings     = new ArrayList<>();
        public List<Vacation>      vacations    = new ArrayList<>();
        public List<Assignment>    assignments  = new ArrayList<>();
        public List<InfoPost>      infos        = new ArrayList<>();
        public List<Duty>          duty         = new ArrayList<>();
        public List<Wanted>        wanted       = new ArrayList<>();
        public List<Dispatch>      dispatches   = new ArrayList<>();
        public List<DispatchReport> reports     = new ArrayList<>();
        public List<PersonAkte>    personAkten  = new ArrayList<>();
        public List<Strafakte>     strafAkten   = new ArrayList<>();
        public List<LicenseRevoke> licenseRevokes = new ArrayList<>();
        public List<Equipment>     equipment    = new ArrayList<>();
        public Map<String, Session> sessions    = new LinkedHashMap<>();
    }

    private LapdDashManager() {}

    // ── Laden / Speichern ─────────────────────────────────────────────────────

    private static String file(long guildId) {
        return "lapd-dash-" + guildId + ".json";
    }

    private static synchronized Store load(long guildId) {
        String raw = DataStore.readString(file(guildId));
        if (raw == null || raw.isBlank()) return new Store();
        try {
            Store s = GSON.fromJson(raw, Store.class);
            if (s == null) return new Store();
            if (s.access == null)          s.access          = new ArrayList<>();
            if (s.banned == null)          s.banned          = new ArrayList<>();
            if (s.fleet == null)           s.fleet           = new ArrayList<>();
            if (s.employees == null)       s.employees       = new ArrayList<>();
            if (s.warnings == null)        s.warnings        = new ArrayList<>();
            if (s.vacations == null)       s.vacations       = new ArrayList<>();
            if (s.assignments == null)     s.assignments     = new ArrayList<>();
            if (s.infos == null)           s.infos           = new ArrayList<>();
            if (s.duty == null)            s.duty            = new ArrayList<>();
            if (s.wanted == null)          s.wanted          = new ArrayList<>();
            if (s.dispatches == null)      s.dispatches      = new ArrayList<>();
            if (s.reports == null)         s.reports         = new ArrayList<>();
            if (s.personAkten == null)     s.personAkten     = new ArrayList<>();
            if (s.strafAkten == null)      s.strafAkten      = new ArrayList<>();
            if (s.licenseRevokes == null)  s.licenseRevokes  = new ArrayList<>();
            if (s.equipment == null)       s.equipment       = new ArrayList<>();
            if (s.sessions == null)        s.sessions        = new LinkedHashMap<>();
            return s;
        } catch (Exception e) {
            log.warn("[LAPD-Dash] Datenbestand konnte nicht gelesen werden: {}", e.getMessage());
            return new Store();
        }
    }

    private static synchronized void save(long guildId, Store s) {
        DataStore.writeString(file(guildId), GSON.toJson(s));
    }

    private static String newId() {
        return UUID.randomUUID().toString().replace("-", "").substring(0, 10);
    }

    // ── Dienstgrad-Helfer ─────────────────────────────────────────────────────

    public static boolean isValidRank(String rank) {
        return RANKS.contains(rank);
    }

    public static boolean isLeaderRank(String rank) {
        return rank != null && LEADER_RANKS.contains(rank);
    }

    // ── Zugriffsliste (Administrator) ─────────────────────────────────────────

    public static synchronized List<AccessEntry> accessList(long guildId) {
        return load(guildId).access;
    }

    public static synchronized String addAccess(long guildId, String discordId, String rank, String name) {
        if (!isValidRank(rank)) return "Ungültiger Dienstgrad.";
        if (discordId == null || discordId.isBlank()) return "Discord-ID fehlt.";
        Store s = load(guildId);
        for (AccessEntry a : s.access) {
            if (a.discordId.equals(discordId)) {
                a.rank = rank;
                if (name != null && !name.isBlank()) a.name = name;
                save(guildId, s);
                return null;
            }
        }
        AccessEntry a = new AccessEntry();
        a.discordId = discordId;
        a.rank = rank;
        a.name = name == null ? "" : name;
        a.ts = System.currentTimeMillis();
        s.access.add(a);
        save(guildId, s);
        return null;
    }

    public static synchronized void removeAccess(long guildId, String discordId) {
        Store s = load(guildId);
        s.access.removeIf(a -> a.discordId.equals(discordId));
        save(guildId, s);
    }

    public static synchronized AccessEntry findAccess(long guildId, String discordId) {
        for (AccessEntry a : load(guildId).access) {
            if (a.discordId.equals(discordId)) return a;
        }
        return null;
    }

    // ── Bannliste (Administrator) ─────────────────────────────────────────────

    public static synchronized List<Ban> bannedList(long guildId) {
        return load(guildId).banned;
    }

    public static synchronized boolean isBanned(long guildId, String discordId) {
        for (Ban b : load(guildId).banned) {
            if (b.discordId.equals(discordId)) return true;
        }
        return false;
    }

    public static synchronized void ban(long guildId, String discordId, String name, String webName, String reason, String by) {
        Store s = load(guildId);
        s.banned.removeIf(b -> b.discordId.equals(discordId));
        Ban b = new Ban();
        b.discordId = discordId;
        b.name = name == null ? "" : name;
        b.webName = webName == null ? "" : webName.trim();
        b.reason = reason == null ? "" : reason;
        b.by = by == null ? "" : by;
        b.ts = System.currentTimeMillis();
        s.banned.add(b);
        save(guildId, s);
    }

    public static synchronized void unban(long guildId, String discordId) {
        Store s = load(guildId);
        s.banned.removeIf(b -> b.discordId.equals(discordId));
        save(guildId, s);
    }

    // ── Fuhrpark (Administrator) ──────────────────────────────────────────────

    public static synchronized List<Vehicle> fleet(long guildId) {
        return load(guildId).fleet;
    }

    public static synchronized Vehicle addVehicle(long guildId, String title, String image, String description, String by) {
        Store s = load(guildId);
        Vehicle v = new Vehicle();
        v.id = newId();
        v.title = title == null ? "" : title.trim();
        v.image = image == null ? "" : image.trim();
        v.description = description == null ? "" : description.trim();
        v.by = by == null ? "" : by;
        v.ts = System.currentTimeMillis();
        s.fleet.add(v);
        save(guildId, s);
        return v;
    }

    public static synchronized void deleteVehicle(long guildId, String id) {
        Store s = load(guildId);
        s.fleet.removeIf(v -> v.id.equals(id));
        save(guildId, s);
    }

    // ── Mitarbeiter (Leitung) ─────────────────────────────────────────────────

    public static synchronized List<Employee> employees(long guildId) {
        return load(guildId).employees;
    }

    public static synchronized Employee addEmployee(long guildId, String name, String rank, String discordId) {
        Store s = load(guildId);
        Employee e = new Employee();
        e.id = newId();
        e.name = name == null ? "" : name.trim();
        e.rank = rank == null ? "" : rank;
        e.discordId = discordId == null ? "" : discordId;
        e.ts = System.currentTimeMillis();
        s.employees.add(e);
        save(guildId, s);
        return e;
    }

    public static synchronized boolean editEmployee(long guildId, String id, String name, String rank) {
        Store s = load(guildId);
        for (Employee e : s.employees) {
            if (e.id.equals(id)) {
                e.name = name == null ? "" : name.trim();
                e.rank = rank == null ? "" : rank;
                save(guildId, s);
                return true;
            }
        }
        return false;
    }

    public static synchronized void deleteEmployee(long guildId, String id) {
        Store s = load(guildId);
        s.employees.removeIf(e -> e.id.equals(id));
        save(guildId, s);
    }

    // ── Abmahnungen (Leitung) ─────────────────────────────────────────────────

    public static synchronized List<Warning> warnings(long guildId) {
        return load(guildId).warnings;
    }

    public static synchronized List<Warning> warningsOf(long guildId, String discordId) {
        List<Warning> out = new ArrayList<>();
        for (Warning w : load(guildId).warnings) {
            if (w.discordId.equals(discordId)) out.add(w);
        }
        return out;
    }

    public static synchronized Warning warn(long guildId, String discordId, String name, String reason, String by) {
        Store s = load(guildId);
        Warning w = new Warning();
        w.id = newId();
        w.discordId = discordId;
        w.name = name == null ? "" : name;
        w.reason = reason == null ? "" : reason;
        w.by = by == null ? "" : by;
        w.ts = System.currentTimeMillis();
        s.warnings.add(w);
        save(guildId, s);
        return w;
    }

    /** Kündigt einen Mitarbeiter: Zugriff entfernt + Mitarbeiter-Eintrag gelöscht. */
    public static synchronized boolean fire(long guildId, String discordId) {
        Store s = load(guildId);
        s.access.removeIf(a -> a.discordId.equals(discordId));
        s.employees.removeIf(e -> discordId.equals(e.discordId));
        s.duty.removeIf(d -> d.discordId.equals(discordId));
        save(guildId, s);
        return true;
    }

    // ── Urlaub (alle) ─────────────────────────────────────────────────────────

    public static synchronized List<Vacation> vacations(long guildId) {
        return load(guildId).vacations;
    }

    public static synchronized List<Vacation> vacationsOf(long guildId, String discordId) {
        List<Vacation> out = new ArrayList<>();
        for (Vacation v : load(guildId).vacations) {
            if (v.discordId.equals(discordId)) out.add(v);
        }
        return out;
    }

    public static synchronized Vacation requestVacation(long guildId, String discordId, String name,
                                                        String from, String to, String reason) {
        Store s = load(guildId);
        Vacation v = new Vacation();
        v.id = newId();
        v.discordId = discordId;
        v.name = name == null ? "" : name;
        v.from = from == null ? "" : from;
        v.to = to == null ? "" : to;
        v.reason = reason == null ? "" : reason;
        v.ts = System.currentTimeMillis();
        s.vacations.add(v);
        save(guildId, s);
        return v;
    }

    public static synchronized boolean decideVacation(long guildId, String id, String status) {
        if (!"genehmigt".equals(status) && !"abgelehnt".equals(status)) return false;
        Store s = load(guildId);
        for (Vacation v : s.vacations) {
            if (v.id.equals(id)) {
                v.status = status;
                save(guildId, s);
                return true;
            }
        }
        return false;
    }

    /** Löscht einen Urlaubsantrag endgültig (nirgendwo mehr sichtbar). */
    public static synchronized boolean deleteVacation(long guildId, String id) {
        Store s = load(guildId);
        boolean removed = s.vacations.removeIf(v -> v.id.equals(id));
        if (removed) save(guildId, s);
        return removed;
    }

    // ── Zuweisungen (Leitung) ─────────────────────────────────────────────────

    public static synchronized List<Assignment> assignments(long guildId) {
        return load(guildId).assignments;
    }

    public static synchronized Assignment assign(long guildId, String discordId, String name, String shift) {
        Store s = load(guildId);
        Assignment a = new Assignment();
        a.id = newId();
        a.discordId = discordId;
        a.name = name == null ? "" : name;
        a.shift = shift == null ? "" : shift;
        a.ts = System.currentTimeMillis();
        s.assignments.add(a);
        save(guildId, s);
        return a;
    }

    // ── Informationen (Leitung) ───────────────────────────────────────────────

    public static synchronized List<InfoPost> infos(long guildId) {
        return load(guildId).infos;
    }

    public static synchronized List<InfoPost> infosByTarget(long guildId, String target) {
        List<InfoPost> out = new ArrayList<>();
        for (InfoPost i : load(guildId).infos) {
            if (i.target.equals(target)) out.add(i);
        }
        return out;
    }

    public static synchronized InfoPost addInfo(long guildId, String target, String title, String text, String by) {
        Store s = load(guildId);
        InfoPost i = new InfoPost();
        i.id = newId();
        i.target = target == null ? "website" : target;
        i.title = title == null ? "" : title.trim();
        i.text = text == null ? "" : text.trim();
        i.by = by == null ? "" : by;
        i.ts = System.currentTimeMillis();
        s.infos.add(i);
        save(guildId, s);
        return i;
    }

    public static synchronized void deleteInfo(long guildId, String id) {
        Store s = load(guildId);
        s.infos.removeIf(i -> i.id.equals(id));
        save(guildId, s);
    }

    // ── Dienst (alle) ─────────────────────────────────────────────────────────

    public static synchronized List<Duty> duty(long guildId) {
        return load(guildId).duty;
    }

    public static synchronized boolean isOnDuty(long guildId, String discordId) {
        for (Duty d : load(guildId).duty) {
            if (d.discordId.equals(discordId)) return true;
        }
        return false;
    }

    public static synchronized Duty dutyOn(long guildId, String discordId, String name, String rank) {
        Store s = load(guildId);
        for (Duty d : s.duty) {
            if (d.discordId.equals(discordId)) return d;
        }
        Duty d = new Duty();
        d.discordId = discordId;
        d.name = name == null ? "" : name;
        d.rank = rank == null ? "" : rank;
        d.startedAt = System.currentTimeMillis();
        s.duty.add(d);
        save(guildId, s);
        return d;
    }

    public static synchronized boolean dutyOff(long guildId, String discordId) {
        Store s = load(guildId);
        boolean removed = s.duty.removeIf(d -> d.discordId.equals(discordId));
        if (removed) save(guildId, s);
        return removed;
    }

    // ── Fahndungen (alle erstellen, nur Leitung löschen) ──────────────────────

    public static synchronized List<Wanted> wanted(long guildId) {
        return load(guildId).wanted;
    }

    public static synchronized Wanted addWanted(long guildId, String title, String description, String by) {
        Store s = load(guildId);
        Wanted w = new Wanted();
        w.id = newId();
        w.title = title == null ? "" : title.trim();
        w.description = description == null ? "" : description.trim();
        w.by = by == null ? "" : by;
        w.ts = System.currentTimeMillis();
        s.wanted.add(w);
        save(guildId, s);
        return w;
    }

    public static synchronized void deleteWanted(long guildId, String id) {
        Store s = load(guildId);
        s.wanted.removeIf(w -> w.id.equals(id));
        save(guildId, s);
    }

    // ── Einsätze / Dispatches ─────────────────────────────────────────────────

    public static synchronized List<Dispatch> dispatches(long guildId) {
        return load(guildId).dispatches;
    }

    public static synchronized Dispatch addDispatch(long guildId, String senderName, String senderId,
                                                    String type, String location, String details) {
        Store s = load(guildId);
        Dispatch d = new Dispatch();
        d.id = newId();
        d.senderName = senderName == null ? "" : senderName;
        d.senderId = senderId == null ? "" : senderId;
        d.type = type == null ? "" : type;
        d.location = location == null ? "" : location;
        d.details = details == null ? "" : details;
        d.ts = System.currentTimeMillis();
        s.dispatches.add(d);
        save(guildId, s);
        return d;
    }

    /** Nimmt einen offenen Einsatz an — liefert den Einsatz oder null (nicht mehr offen). */
    public static synchronized Dispatch acceptDispatch(long guildId, String id, String acceptedBy) {
        Store s = load(guildId);
        for (Dispatch d : s.dispatches) {
            if (d.id.equals(id)) {
                if (!"offen".equals(d.status)) return null;
                d.status = "angenommen";
                d.acceptedBy = acceptedBy;
                d.acceptedAt = System.currentTimeMillis();
                save(guildId, s);
                return d;
            }
        }
        return null;
    }

    /** Schließt einen Einsatz mit Bericht ab. */
    public static synchronized DispatchReport completeDispatch(long guildId, String id, String text, String by) {
        Store s = load(guildId);
        for (Dispatch d : s.dispatches) {
            if (d.id.equals(id)) {
                d.status = "abgeschlossen";
                DispatchReport r = new DispatchReport();
                r.id = newId();
                r.dispatchId = id;
                r.text = text == null ? "" : text.trim();
                r.by = by == null ? "" : by;
                r.ts = System.currentTimeMillis();
                s.reports.add(r);
                save(guildId, s);
                return r;
            }
        }
        return null;
    }

    public static synchronized List<DispatchReport> reports(long guildId) {
        return load(guildId).reports;
    }

    // ── Akten (Personen + Strafakten) ─────────────────────────────────────────

    public static synchronized List<PersonAkte> personAkten(long guildId) {
        return load(guildId).personAkten;
    }

    public static synchronized PersonAkte addPersonAkte(long guildId, String name, String discordId,
                                                        Map<String, String> data, String by) {
        Store s = load(guildId);
        PersonAkte a = new PersonAkte();
        a.id = newId();
        a.name = name == null ? "" : name.trim();
        a.discordId = discordId == null ? "" : discordId;
        a.data = data == null ? new LinkedHashMap<>() : new LinkedHashMap<>(data);
        a.createdBy = by == null ? "" : by;
        a.ts = System.currentTimeMillis();
        s.personAkten.add(a);
        save(guildId, s);
        return a;
    }

    public static synchronized boolean editPersonAkte(long guildId, String id, Map<String, String> data) {
        Store s = load(guildId);
        for (PersonAkte a : s.personAkten) {
            if (a.id.equals(id)) {
                if (data != null) a.data = new LinkedHashMap<>(data);
                save(guildId, s);
                return true;
            }
        }
        return false;
    }

    public static synchronized void deletePersonAkte(long guildId, String id) {
        Store s = load(guildId);
        s.personAkten.removeIf(a -> a.id.equals(id));
        save(guildId, s);
    }

    public static synchronized List<Strafakte> strafAkten(long guildId) {
        return load(guildId).strafAkten;
    }

    public static synchronized Strafakte addStrafakte(long guildId, String name, String discordId,
                                                      Map<String, String> data, String by) {
        Store s = load(guildId);
        Strafakte a = new Strafakte();
        a.id = newId();
        a.name = name == null ? "" : name.trim();
        a.discordId = discordId == null ? "" : discordId;
        a.data = data == null ? new LinkedHashMap<>() : new LinkedHashMap<>(data);
        a.createdBy = by == null ? "" : by;
        a.ts = System.currentTimeMillis();
        s.strafAkten.add(a);
        save(guildId, s);
        return a;
    }

    public static synchronized boolean editStrafakte(long guildId, String id, Map<String, String> data) {
        Store s = load(guildId);
        for (Strafakte a : s.strafAkten) {
            if (a.id.equals(id)) {
                if (data != null) a.data = new LinkedHashMap<>(data);
                save(guildId, s);
                return true;
            }
        }
        return false;
    }

    public static synchronized void deleteStrafakte(long guildId, String id) {
        Store s = load(guildId);
        s.strafAkten.removeIf(a -> a.id.equals(id));
        save(guildId, s);
    }

    // ── Führerscheine / Entzug ────────────────────────────────────────────────

    public static synchronized boolean isLicenseRevoked(long guildId, String userId) {
        for (LicenseRevoke r : load(guildId).licenseRevokes) {
            if (r.userId.equals(userId)) return true;
        }
        return false;
    }

    public static synchronized LicenseRevoke revokeLicense(long guildId, String userId, String name,
                                                           String reason, String by) {
        Store s = load(guildId);
        s.licenseRevokes.removeIf(r -> r.userId.equals(userId));
        LicenseRevoke r = new LicenseRevoke();
        r.userId = userId;
        r.name = name == null ? "" : name;
        r.reason = reason == null ? "" : reason;
        r.by = by == null ? "" : by;
        r.ts = System.currentTimeMillis();
        s.licenseRevokes.add(r);
        save(guildId, s);
        return r;
    }

    public static synchronized void returnLicense(long guildId, String userId) {
        Store s = load(guildId);
        s.licenseRevokes.removeIf(r -> r.userId.equals(userId));
        save(guildId, s);
    }

    public static synchronized List<LicenseRevoke> licenseRevokes(long guildId) {
        return load(guildId).licenseRevokes;
    }

    // ── Ausrüstung (Leitung schreibt, alle sehen) ────────────────────────────

    public static synchronized List<Equipment> equipment(long guildId) {
        return load(guildId).equipment;
    }

    public static synchronized List<Equipment> equipmentByCategory(long guildId, String category) {
        List<Equipment> out = new ArrayList<>();
        for (Equipment e : load(guildId).equipment) {
            if (category == null || category.isBlank() || category.equals(e.category)) out.add(e);
        }
        return out;
    }

    public static synchronized Equipment addEquipment(long guildId, String category, String title, String description,
                                                      String access, String image, String by) {
        Store s = load(guildId);
        Equipment e = new Equipment();
        e.id = newId();
        e.category = category == null ? "" : category.trim();
        e.title = title == null ? "" : title.trim();
        e.description = description == null ? "" : description.trim();
        e.access = access == null ? "alle" : access;
        e.image = image == null ? "" : image.trim();
        e.by = by == null ? "" : by;
        e.ts = System.currentTimeMillis();
        s.equipment.add(e);
        save(guildId, s);
        return e;
    }

    public static synchronized void deleteEquipment(long guildId, String id) {
        Store s = load(guildId);
        s.equipment.removeIf(e -> e.id.equals(id));
        save(guildId, s);
    }

    // ── Sessions ──────────────────────────────────────────────────────────────

    public static synchronized String createSession(long guildId, String discordId, String name,
                                                    String rank, boolean admin, boolean leader) {
        Store s = load(guildId);
        Session sess = new Session();
        sess.discordId = discordId;
        sess.name = name;
        sess.rank = rank;
        sess.admin = admin;
        sess.leader = leader;
        sess.expiresAt = System.currentTimeMillis() + SESSION_TTL_MS;
        String token = UUID.randomUUID().toString().replace("-", "");
        s.sessions.put(token, sess);
        save(guildId, s);
        return token;
    }

    /** Validiert ein Session-Token — liefert die Session oder null. */
    public static synchronized Session validateSession(long guildId, String token) {
        if (token == null || token.isBlank()) return null;
        Store s = load(guildId);
        Session sess = s.sessions.get(token);
        if (sess == null) return null;
        if (System.currentTimeMillis() > sess.expiresAt) {
            s.sessions.remove(token);
            save(guildId, s);
            return null;
        }
        return sess;
    }

    public static synchronized void destroySession(long guildId, String token) {
        Store s = load(guildId);
        if (token != null) {
            s.sessions.remove(token);
            save(guildId, s);
        }
    }

    // ── Dienst-Embed (festes Embed im Dienst-Kanal) ───────────────────────────

    private static final String DUTY_EMBED_KEY_PREFIX = "lapd-dash-duty-embed-";

    /** Postet das feste Dienst-Embed einmal (Duplikat-Schutz) und aktualisiert es sofort. */
    public static void init(Guild guild) {
        refreshDutyEmbed(guild);
    }

    /** Baut die Beschreibung für das Dienst-Embed aus der aktuellen Dienst-Liste. */
    public static String dutyEmbedDescription(long guildId) {
        List<Duty> duty = duty(guildId);
        StringBuilder sb = new StringBuilder();
        sb.append("**Aktuell im Dienst:** ").append(duty.size()).append("\n\n");
        if (duty.isEmpty()) {
            sb.append("Derzeit ist niemand im Dienst.");
            return sb.toString();
        }
        for (Duty d : duty) {
            String since = java.time.Instant.ofEpochMilli(d.startedAt)
                .atZone(java.time.ZoneId.systemDefault())
                .format(java.time.format.DateTimeFormatter.ofPattern("HH:mm"));
            sb.append("👮 **").append(d.name).append("** — ").append(d.rank)
              .append(" · seit ").append(since).append("\n");
        }
        return sb.toString();
    }

    /** Erstellt/aktualisiert das feste Dienst-Embed im Kanal. */
    public static synchronized void refreshDutyEmbed(Guild guild) {
        if (guild == null) return;
        String key = DUTY_EMBED_KEY_PREFIX + guild.getId();
        TextChannel ch = guild.getTextChannelById(LoggingConfig.LAPD_DUTY_CHANNEL_ID);
        if (ch == null) {
            log.warn("[LAPD-Dash] Dienst-Kanal {} nicht gefunden.", LoggingConfig.LAPD_DUTY_CHANNEL_ID);
            return;
        }
        long gid = guild.getIdLong();
        String msgId = DataStore.readString(key);
        var embed = EmbedFactory.create()
            .setTitle("🚔 LAPD — Dienstübersicht")
            .setDescription(dutyEmbedDescription(gid))
            .build();
        if (msgId != null && !msgId.isBlank()) {
            ch.editMessageEmbedsById(msgId, embed).queue(
                ok -> {}, err -> DataStore.deleteKey(key));
        } else {
            ch.sendMessageEmbeds(embed).queue(
                msg -> DataStore.writeString(key, msg.getId()),
                err -> log.error("[LAPD-Dash] Dienst-Embed konnte nicht gesendet werden.", err));
        }
    }

    // ── DM-Helfer ─────────────────────────────────────────────────────────────

    public static void sendDm(Guild guild, String userId, String content) {
        if (guild == null || userId == null || userId.isBlank() || content == null || content.isBlank()) return;
        Member m = guild.getMemberById(userId);
        if (m == null) {
            log.info("[LAPD-Dash] DM nicht gesendet – Nutzer {} nicht auf dem Server.", userId);
            return;
        }
        m.getUser().openPrivateChannel().queue(
            pc -> pc.sendMessage(content).queue(null, e -> log.warn("[LAPD-Dash] DM-Zustellung fehlgeschlagen: {}", e.getMessage())),
            e  -> log.warn("[LAPD-Dash] DM-Kanal konnte nicht geöffnet werden: {}", e.getMessage())
        );
    }

    /** Sendet eine Information als normale Nachricht (kein Embed) in den LAPD-Info-Discord-Kanal. */
    public static void postInfoToDiscord(Guild guild, InfoPost info) {
        if (guild == null || info == null) return;
        TextChannel ch = guild.getTextChannelById(LoggingConfig.LAPD_INFO_DISCORD_CHANNEL_ID);
        if (ch == null) {
            log.warn("[LAPD-Dash] Info-Kanal {} nicht gefunden.", LoggingConfig.LAPD_INFO_DISCORD_CHANNEL_ID);
            return;
        }
        String content = "**📢 (LAPD) — " + info.title + "**\n\n" + info.text;
        ch.sendMessage(content).queue(
                msg -> {
                    // Message-ID persistieren (für eventuelles Löschen)
                    Store s = load(guild.getIdLong());
                    for (InfoPost i : s.infos) {
                        if (i.id.equals(info.id)) { i.discordMsgId = msg.getId(); break; }
                    }
                    save(guild.getIdLong(), s);
                },
                err -> log.error("[LAPD-Dash] Info-Nachricht konnte nicht gesendet werden.", err));
    }
}
