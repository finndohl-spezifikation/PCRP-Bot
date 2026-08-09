package de.pcrp.bot.common;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

/**
 * Datenhaltung für die LAPD-Webseite: Mails (Kontakt), Anzeigen und Bewerbungen.
 * Persistenz pro Guild in einer JSON-Datei (lapd-&lt;guildId&gt;.json).
 *
 * Jeder Eintrag hat eine Client-UID (aus localStorage) + den eingegebenen Namen,
 * einen Status (offen/gelöst/geschlossen) und einen Verlauf aus Antworten
 * (Bürger und LAPD).
 */
public final class LapdManager {

    private static final Logger log = LoggerFactory.getLogger(LapdManager.class);
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    public static final String STATUS_OFFEN       = "offen";
    public static final String STATUS_GELOEST     = "gelöst";
    public static final String STATUS_GESCHLOSSEN = "geschlossen";

    /** Ein Bürger-/LAPD-Eintrag (Mail / Anzeige / Bewerbung). */
    public static class Item {
        public String id;
        public String uid;       // Client-Kennung des Absenders (localStorage)
        public String name;      // Eingegebener Name
        public String message;   // Text
        public String status = STATUS_OFFEN;
        public long createdAt;
        public List<Reply> replies = new ArrayList<>();
    }

    public static class Reply {
        public String author;    // "LAPD" oder der Bürger-Name
        public String text;
        public long ts;
    }

    /** Kompletter Datenbestand einer Guild. */
    public static class Store {
        public List<Item> mails       = new ArrayList<>();
        public List<Item> anzeigen    = new ArrayList<>();
        public List<Item> bewerbungen = new ArrayList<>();
    }

    private LapdManager() {}

    private static String file(long guildId) {
        return "lapd-" + guildId + ".json";
    }

    private static synchronized Store load(long guildId) {
        String raw = DataStore.readString(file(guildId));
        if (raw == null || raw.isBlank()) return new Store();
        try {
            Store s = GSON.fromJson(raw, Store.class);
            if (s == null) return new Store();
            if (s.mails == null)       s.mails       = new ArrayList<>();
            if (s.anzeigen == null)    s.anzeigen    = new ArrayList<>();
            if (s.bewerbungen == null) s.bewerbungen = new ArrayList<>();
            return s;
        } catch (Exception e) {
            log.warn("[LAPD] Datenbestand konnte nicht gelesen werden: {}", e.getMessage());
            return new Store();
        }
    }

    private static synchronized void save(long guildId, Store s) {
        DataStore.writeString(file(guildId), GSON.toJson(s));
    }

    private static List<Item> listOf(Store s, String type) {
        return switch (type) {
            case "mail"      -> s.mails;
            case "anzeige"   -> s.anzeigen;
            case "bewerbung" -> s.bewerbungen;
            default          -> null;
        };
    }

    private static String newId() {
        return Long.toHexString(System.nanoTime()) + "-"
             + Integer.toHexString((int) (Math.random() * 0xFFFFFF));
    }

    /** Legt einen neuen Eintrag an (Typ: mail / anzeige / bewerbung). */
    public static synchronized Item create(long guildId, String type, String uid, String name, String message) {
        Store store = load(guildId);
        List<Item> list = listOf(store, type);
        if (list == null) return null;
        Item item = new Item();
        item.id = newId();
        item.uid = uid == null ? "" : uid;
        item.name = name == null ? "" : name.trim();
        item.message = message == null ? "" : message.trim();
        item.createdAt = System.currentTimeMillis();
        list.add(item);
        save(guildId, store);
        return item;
    }

    /** Kompletter Datenbestand (für das LAPD-Dashboard). */
    public static synchronized Store all(long guildId) {
        return load(guildId);
    }

    /** Alle Einträge eines Bürgers (über seine UID). */
    public static synchronized Store my(long guildId, String uid) {
        Store all = load(guildId);
        Store mine = new Store();
        mine.mails       = filter(all.mails, uid);
        mine.anzeigen    = filter(all.anzeigen, uid);
        mine.bewerbungen = filter(all.bewerbungen, uid);
        return mine;
    }

    private static List<Item> filter(List<Item> items, String uid) {
        List<Item> out = new ArrayList<>();
        for (Item i : items) {
            if (uid != null && uid.equals(i.uid)) out.add(i);
        }
        return out;
    }

    /** Bürger antwortet auf den eigenen Eintrag (nur solange er offen ist). */
    public static synchronized boolean reply(long guildId, String type, String id,
                                             String uid, String name, String text) {
        Store store = load(guildId);
        List<Item> list = listOf(store, type);
        if (list == null) return false;
        for (Item i : list) {
            if (i.id.equals(id)) {
                if (uid == null || !uid.equals(i.uid)) return false;
                if (!STATUS_OFFEN.equals(i.status)) return false;
                Reply r = new Reply();
                r.author = (name == null || name.isBlank()) ? "Bürger" : name.trim();
                r.text = text == null ? "" : text.trim();
                r.ts = System.currentTimeMillis();
                i.replies.add(r);
                save(guildId, store);
                return true;
            }
        }
        return false;
    }

    /** LAPD-Dashboard: Antwort als LAPD schreiben. */
    public static synchronized boolean dashReply(long guildId, String type, String id, String text) {
        Store store = load(guildId);
        List<Item> list = listOf(store, type);
        if (list == null) return false;
        for (Item i : list) {
            if (i.id.equals(id)) {
                Reply r = new Reply();
                r.author = "LAPD";
                r.text = text == null ? "" : text.trim();
                r.ts = System.currentTimeMillis();
                i.replies.add(r);
                save(guildId, store);
                return true;
            }
        }
        return false;
    }

    /** LAPD-Dashboard: Status setzen (offen / gelöst / geschlossen). */
    public static synchronized boolean setStatus(long guildId, String type, String id, String status) {
        if (!STATUS_OFFEN.equals(status)
                && !STATUS_GELOEST.equals(status)
                && !STATUS_GESCHLOSSEN.equals(status)) return false;
        Store store = load(guildId);
        List<Item> list = listOf(store, type);
        if (list == null) return false;
        for (Item i : list) {
            if (i.id.equals(id)) {
                i.status = status;
                save(guildId, store);
                return true;
            }
        }
        return false;
    }
}
