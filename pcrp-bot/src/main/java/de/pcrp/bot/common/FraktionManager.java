package de.pcrp.bot.common;

import com.google.gson.*;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;

import java.util.*;

/**
 * Verwaltet Fraktionsliste, -verwarnungen und -sperren via DataStore.
 */
public final class FraktionManager {

    private static final Gson GSON = new Gson();

    // ── DataStore-Keys ─────────────────────────────────────────────────────────

    private static String contentKey(String guildId)  { return "frak-list-content-" + guildId; }
    private static String panelKey(String guildId)    { return "frak-list-panel-"   + guildId; }
    private static String warnsKey(String guildId)    { return "frak-warns-"        + guildId; }
    private static String lockedKey(String guildId)   { return "frak-locked-"       + guildId; }

    // ── Strukturierte Fraktionsliste ───────────────────────────────────────────

    private static String namesKey(String guildId) { return "frak-names-" + guildId; }

    public static List<String> getFrakList(String guildId) {
        String raw = DataStore.readString(namesKey(guildId));
        List<String> list = new ArrayList<>();
        if (raw == null || raw.isBlank()) return list;
        try {
            JsonArray arr = GSON.fromJson(raw, JsonArray.class);
            for (JsonElement el : arr) list.add(el.getAsString());
        } catch (Exception ignored) {}
        return list;
    }

    public static boolean frakExists(String guildId, String name) {
        return getFrakList(guildId).stream().anyMatch(f -> f.equalsIgnoreCase(name));
    }

    /** Fügt eine Fraktion hinzu. Gibt false zurück wenn sie bereits existiert. */
    public static boolean addFrak(String guildId, String name) {
        List<String> list = getFrakList(guildId);
        if (list.stream().anyMatch(f -> f.equalsIgnoreCase(name))) return false;
        list.add(name);
        saveFrakNames(guildId, list);
        return true;
    }

    /** Entfernt eine Fraktion (case-insensitive). Gibt false zurück wenn nicht gefunden. */
    public static boolean removeFrak(String guildId, String name) {
        List<String> list = getFrakList(guildId);
        boolean removed = list.removeIf(f -> f.equalsIgnoreCase(name));
        if (removed) saveFrakNames(guildId, list);
        return removed;
    }

    private static void saveFrakNames(String guildId, List<String> list) {
        JsonArray arr = new JsonArray();
        for (String s : list) arr.add(s);
        DataStore.writeString(namesKey(guildId), GSON.toJson(arr));
    }

    // ── Panel-Nachrichten-ID ───────────────────────────────────────────────────

    public static String getPanelMsgId(String guildId) {
        return DataStore.readString(panelKey(guildId));
    }

    public static void setPanelMsgId(String guildId, String msgId) {
        DataStore.writeString(panelKey(guildId), msgId);
    }

    // ── Locked-Set ────────────────────────────────────────────────────────────

    private static Set<String> getLockedSet(String guildId) {
        String raw = DataStore.readString(lockedKey(guildId));
        Set<String> set = new LinkedHashSet<>();
        if (raw != null && !raw.isBlank()) {
            try {
                JsonArray arr = GSON.fromJson(raw, JsonArray.class);
                for (JsonElement el : arr) set.add(el.getAsString());
            } catch (Exception ignored) {}
        }
        return set;
    }

    private static void saveLockedSet(String guildId, Set<String> set) {
        JsonArray arr = new JsonArray();
        for (String s : set) arr.add(s);
        DataStore.writeString(lockedKey(guildId), GSON.toJson(arr));
    }

    public static boolean isLocked(String guildId, String frakName) {
        return getLockedSet(guildId).contains(frakName);
    }

    public static void lock(String guildId, String frakName) {
        Set<String> set = getLockedSet(guildId);
        set.add(frakName);
        saveLockedSet(guildId, set);
    }

    public static void unlock(String guildId, String frakName) {
        Set<String> set = getLockedSet(guildId);
        set.remove(frakName);
        saveLockedSet(guildId, set);
    }

    // ── Verwarnungen ──────────────────────────────────────────────────────────

    /** Liefert alle Verwarnungen einer Fraktion. */
    public static List<FrakWarn> getWarns(String guildId, String frakName) {
        Map<String, List<FrakWarn>> map = readWarnsMap(guildId);
        return map.getOrDefault(frakName, new ArrayList<>());
    }

    /** Fügt eine Verwarnung hinzu und gibt die neue Anzahl zurück. */
    public static int addWarn(String guildId, String frakName, String grund, String konsequenz, String modName) {
        Map<String, List<FrakWarn>> map = readWarnsMap(guildId);
        List<FrakWarn> list = map.computeIfAbsent(frakName, k -> new ArrayList<>());
        list.add(new FrakWarn(grund, konsequenz, modName, System.currentTimeMillis()));
        saveWarnsMap(guildId, map);
        return list.size();
    }

    /** Entfernt alle Verwarnungen einer Fraktion. */
    public static void clearWarns(String guildId, String frakName) {
        Map<String, List<FrakWarn>> map = readWarnsMap(guildId);
        map.remove(frakName);
        saveWarnsMap(guildId, map);
    }

    private static Map<String, List<FrakWarn>> readWarnsMap(String guildId) {
        String raw = DataStore.readString(warnsKey(guildId));
        Map<String, List<FrakWarn>> map = new LinkedHashMap<>();
        if (raw == null || raw.isBlank()) return map;
        try {
            JsonObject obj = GSON.fromJson(raw, JsonObject.class);
            for (Map.Entry<String, JsonElement> entry : obj.entrySet()) {
                List<FrakWarn> list = new ArrayList<>();
                for (JsonElement el : entry.getValue().getAsJsonArray()) {
                    list.add(GSON.fromJson(el, FrakWarn.class));
                }
                map.put(entry.getKey(), list);
            }
        } catch (Exception ignored) {}
        return map;
    }

    private static void saveWarnsMap(String guildId, Map<String, List<FrakWarn>> map) {
        JsonObject obj = new JsonObject();
        for (Map.Entry<String, List<FrakWarn>> entry : map.entrySet()) {
            obj.add(entry.getKey(), GSON.toJsonTree(entry.getValue()));
        }
        DataStore.writeString(warnsKey(guildId), GSON.toJson(obj));
    }

    // ── Embed-Rendering ───────────────────────────────────────────────────────

    /** Baut das Fraktionslisten-Embed aus der strukturierten Fraktionsliste. */
    public static net.dv8tion.jda.api.entities.MessageEmbed buildFrakEmbed(String guildId) {
        List<String> fraks  = getFrakList(guildId);
        Set<String>  locked = getLockedSet(guildId);

        String display;
        if (fraks.isEmpty()) {
            display = "\u200b";
        } else {
            StringBuilder sb = new StringBuilder();
            for (String name : fraks) {
                if (locked.contains(name)) sb.append("~~").append(name).append("~~\n");
                else                       sb.append(name).append("\n");
            }
            display = sb.toString().trim();
        }

        return EmbedFactory.create()
            .setDescription(display)
            .build();
    }

    /** Aktualisiert die bestehende Fraktionslisten-Nachricht. */
    public static void updatePanelEmbed(Guild guild) {
        String msgId = getPanelMsgId(guild.getId());
        if (msgId == null || msgId.isBlank()) return;
        TextChannel ch = guild.getTextChannelById(LoggingConfig.FRAK_LIST_CHANNEL_ID);
        if (ch == null) return;
        ch.editMessageEmbedsById(msgId, buildFrakEmbed(guild.getId())).queue(
            ok -> {}, err -> {}
        );
    }

    // ── Inner class ───────────────────────────────────────────────────────────

    public static class FrakWarn {
        public String grund;
        public String konsequenz;
        public String mod;
        public long   timestamp;
        public FrakWarn(String grund, String konsequenz, String mod, long timestamp) {
            this.grund = grund; this.konsequenz = konsequenz;
            this.mod = mod;     this.timestamp = timestamp;
        }
    }

    private FraktionManager() {}
}
