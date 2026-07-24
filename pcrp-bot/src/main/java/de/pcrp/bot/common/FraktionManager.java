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

    // ── Content ────────────────────────────────────────────────────────────────

    public static String getContent(String guildId) {
        String s = DataStore.readString(contentKey(guildId));
        return (s != null && !s.isBlank()) ? s : "";
    }

    public static void setContent(String guildId, String content) {
        DataStore.writeString(contentKey(guildId), content == null ? "" : content);
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

    /** Baut das Fraktionslisten-Embed mit Strikethrough für gesperrte Fraktionen. */
    public static net.dv8tion.jda.api.entities.MessageEmbed buildFrakEmbed(String guildId) {
        String raw = getContent(guildId);
        Set<String> locked = getLockedSet(guildId);

        String display = raw.isBlank() ? "*Noch keine Fraktionen eingetragen.*" : raw;
        for (String name : locked) {
            display = display.replace(name, "~~" + name + "~~");
        }

        return EmbedFactory.create()
            .setTitle("⚔️ Fraktions Liste — Paradise City Roleplay")
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
