package de.pcrp.bot.common;

import com.google.gson.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Optional;

/**
 * Verwaltet Ausweise und Führerscheine.
 * DataStore-Keys:
 *   ausweis-{guildId}-{userId}        → JSON (Ausweis-Datensatz)
 *   fuehrerschein-{guildId}-{userId}  → JSON (Fuehrerschein-Datensatz)
 *
 * Worker-/Web-Links zeigen auf das Paradise-City-Dashboard (Cloudflare Worker).
 */
public final class DocumentsManager {

    private static final Logger log = LoggerFactory.getLogger(DocumentsManager.class);
    private static final Gson   GSON = new Gson();

    // ── Datenklassen ──────────────────────────────────────────────────────────

    public static class Ausweis {
        public String vorname      = "";
        public String nachname     = "";
        public String geburtsdatum = "";
        public String staatsang    = "";
        public String adresse      = "";
        public String wohnort      = "";
        public String ausweisNr    = "";
        public long   erstelltAm;          // epoch seconds
        public String erstelltVon = "";    // UserName des Erstellers
    }

    public static class Fuehrerschein {
        public String       vorname      = "";
        public String       nachname     = "";
        public String       geburtsdatum = "";
        public String       adresse      = "";
        public List<String> klassen;       // z. B. ["B", "C1"]
        public long         erstelltAm;
        public long         gueltigBis;
        public String       erstelltVon = "";
    }

    // ── Schlüssel ─────────────────────────────────────────────────────────────

    private static String ausweisKey(String guildId, String userId) {
        return "ausweis-" + guildId + "-" + userId;
    }

    private static String fuehrerscheinKey(String guildId, String userId) {
        return "fuehrerschein-" + guildId + "-" + userId;
    }

    // ── Ausweis ───────────────────────────────────────────────────────────────

    public static boolean hasAusweis(String guildId, String userId) {
        String raw = DataStore.readString(ausweisKey(guildId, userId));
        return raw != null && !raw.isBlank();
    }

    public static Optional<Ausweis> getAusweis(String guildId, String userId) {
        String raw = DataStore.readString(ausweisKey(guildId, userId));
        if (raw == null || raw.isBlank()) return Optional.empty();
        try {
            return Optional.of(GSON.fromJson(raw, Ausweis.class));
        } catch (Exception e) {
            log.warn("[Ausweis] Konnte JSON nicht parsen für {}-{}: {}", guildId, userId, e.getMessage());
            return Optional.empty();
        }
    }

    public static void saveAusweis(String guildId, String userId, Ausweis a) {
        DataStore.writeString(ausweisKey(guildId, userId), GSON.toJson(a));
    }

    public static void deleteAusweis(String guildId, String userId) {
        DataStore.deleteKey(ausweisKey(guildId, userId));
    }

    // ── Führerschein ──────────────────────────────────────────────────────────

    public static boolean hasFuehrerschein(String guildId, String userId) {
        String raw = DataStore.readString(fuehrerscheinKey(guildId, userId));
        return raw != null && !raw.isBlank();
    }

    public static Optional<Fuehrerschein> getFuehrerschein(String guildId, String userId) {
        String raw = DataStore.readString(fuehrerscheinKey(guildId, userId));
        if (raw == null || raw.isBlank()) return Optional.empty();
        try {
            return Optional.of(GSON.fromJson(raw, Fuehrerschein.class));
        } catch (Exception e) {
            log.warn("[Fuehrerschein] Konnte JSON nicht parsen für {}-{}: {}", guildId, userId, e.getMessage());
            return Optional.empty();
        }
    }

    public static void saveFuehrerschein(String guildId, String userId, Fuehrerschein f) {
        DataStore.writeString(fuehrerscheinKey(guildId, userId), GSON.toJson(f));
    }

    public static void deleteFuehrerschein(String guildId, String userId) {
        DataStore.deleteKey(fuehrerscheinKey(guildId, userId));
    }

    // ── Web-URL-Helper (Worker-Routen) ────────────────────────────────────────

    public static String ausweisCreateUrl(String guildId, String targetUserId) {
        return webUrl() + "/ausweis-erstellen/" + guildId + "/" + targetUserId + "?orient=landscape";
    }

    public static String ausweisViewUrl(String userId) {
        return webUrl() + "/ausweis/" + userId + "?orient=landscape";
    }

    public static String fuehrerscheinCreateUrl(String guildId, String targetUserId) {
        return webUrl() + "/fuehrerschein-erstellen/" + guildId + "/" + targetUserId;
    }

    public static String fuehrerscheinViewUrl(String userId) {
        return webUrl() + "/fuehrerschein/" + userId;
    }

    private static String webUrl() {
        String url = System.getenv("WEB_URL");
        if (url == null || url.isBlank()) {
            String domain = System.getenv("RAILWAY_PUBLIC_DOMAIN");
            url = (domain != null && !domain.isBlank())
                ? (domain.startsWith("http") ? domain : "https://" + domain)
                : "https://dashboards.paradisecity-roleplay-85a.workers.dev";
        }
        return url.replaceAll("/$", "");
    }

    private DocumentsManager() {}
}
