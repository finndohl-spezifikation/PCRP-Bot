package de.pcrp.bot.common;

import com.google.gson.*;
import com.google.gson.reflect.TypeToken;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Type;
import java.util.*;

/**
 * Persistenter Team-Warn-Speicher (DataStore-Key: team-warns-{guildId}-{userId}).
 * Paralles Datenmodell zu WarnStore — wird verwendet, wenn ein
 * Teammitglied (Rolle RoleConfig.TEAMMITGLIED_ROLE_ID) eine Verwarnung an
 * ein anderes Teammitglied ausspricht. Embeds landen in LoggingConfig.TEAM_WARN_CHANNEL_ID.
 *
 * Datenklasse {@link WarnEntry} wird 1:1 von WarnStore übernommen, damit das
 * Frontend (Discord-Embeds in CommandListener) gleich aussehen kann.
 */
public final class TeamWarnStore {

    private static final Logger log  = LoggerFactory.getLogger(TeamWarnStore.class);
    private static final Gson   GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final Type   LIST_TYPE = new TypeToken<List<WarnStore.WarnEntry>>() {}.getType();

    private TeamWarnStore() {}

    // ─── Lesen ───────────────────────────────────────────────────────────────

    public static List<WarnStore.WarnEntry> getWarns(long guildId, long userId) {
        String raw = DataStore.readString(key(guildId, userId));
        if (raw == null || raw.isBlank()) return new ArrayList<>();
        try {
            List<WarnStore.WarnEntry> list = GSON.fromJson(raw, LIST_TYPE);
            return list == null ? new ArrayList<>() : list;
        } catch (JsonSyntaxException e) {
            log.warn("[TeamWarnStore] JSON-Fehler für {}/{}: {}", guildId, userId, e.getMessage());
            return new ArrayList<>();
        }
    }

    // ─── Schreiben ───────────────────────────────────────────────────────────

    /** Fügt einen Team-Warn hinzu und gibt die neue Gesamt-Anzahl zurück. */
    public static int addWarn(long guildId, long userId, WarnStore.WarnEntry warn) {
        List<WarnStore.WarnEntry> list = getWarns(guildId, userId);
        list.add(warn);
        save(guildId, userId, list);
        return list.size();
    }

    /** Entfernt einen Team-Warn anhand seiner ID. Gibt true zurück, wenn gefunden. */
    public static boolean removeWarn(long guildId, long userId, String warnId) {
        List<WarnStore.WarnEntry> list = getWarns(guildId, userId);
        boolean removed = list.removeIf(w -> warnId.equals(w.id));
        if (removed) save(guildId, userId, list);
        return removed;
    }

    /** Löscht alle Team-Warnungen eines Nutzers. */
    public static void clearWarns(long guildId, long userId) {
        DataStore.deleteKey(key(guildId, userId));
    }

    // ─── Intern ──────────────────────────────────────────────────────────────

    private static void save(long guildId, long userId, List<WarnStore.WarnEntry> list) {
        DataStore.writeString(key(guildId, userId), GSON.toJson(list));
    }

    private static String key(long guildId, long userId) {
        return "team-warns-" + guildId + "-" + userId;
    }
}
