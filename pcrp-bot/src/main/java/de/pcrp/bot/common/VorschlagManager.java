package de.pcrp.bot.common;

import com.google.gson.*;
import net.dv8tion.jda.api.entities.MessageEmbed;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Verwaltet Vorschläge (Abstimmungen) via DataStore.
 * DataStore-Key: vorschlag-list-{guildId}
 */
public final class VorschlagManager {

    private static final Gson GSON = new GsonBuilder().create();
    private static final String UP   = "👍🏻";
    private static final String DOWN = "👎🏻";

    private static String listKey(String guildId) { return "vorschlag-list-" + guildId; }

    // ── CRUD ──────────────────────────────────────────────────────────────────

    public static List<Vorschlag> getAll(String guildId) {
        String raw = DataStore.readString(listKey(guildId));
        if (raw == null || raw.isBlank()) return new ArrayList<>();
        try {
            JsonArray arr = GSON.fromJson(raw, JsonArray.class);
            List<Vorschlag> list = new ArrayList<>();
            for (JsonElement el : arr) list.add(GSON.fromJson(el, Vorschlag.class));
            return list;
        } catch (Exception e) { return new ArrayList<>(); }
    }

    public static void saveAll(String guildId, List<Vorschlag> list) {
        DataStore.writeString(listKey(guildId), GSON.toJson(list));
    }

    public static void add(String guildId, Vorschlag v) {
        List<Vorschlag> list = getAll(guildId);
        list.add(v);
        saveAll(guildId, list);
    }

    public static Vorschlag getByMessageId(String guildId, String messageId) {
        return getAll(guildId).stream()
            .filter(v -> messageId.equals(v.messageId))
            .findFirst().orElse(null);
    }

    public static List<Vorschlag> getActive(String guildId) {
        return getAll(guildId).stream()
            .filter(v -> "active".equals(v.status))
            .collect(Collectors.toList());
    }

    /** Aktualisiert einen Vorschlag in der Liste anhand der messageId. */
    public static void update(String guildId, Vorschlag updated) {
        List<Vorschlag> list = getAll(guildId);
        for (int i = 0; i < list.size(); i++) {
            if (updated.messageId.equals(list.get(i).messageId)) {
                list.set(i, updated);
                break;
            }
        }
        saveAll(guildId, list);
    }

    // ── Voting ────────────────────────────────────────────────────────────────

    /**
     * Toggled den Upvote. Entfernt Downvote falls vorhanden.
     * @return true wenn der andere Vote entfernt werden muss (👎🏻 Reaction entfernen)
     */
    public static boolean upvote(String guildId, String messageId, String userId) {
        Vorschlag v = getByMessageId(guildId, messageId);
        if (v == null) return false;
        boolean removedDown = v.downvoters.remove(userId);
        if (!v.upvoters.contains(userId)) v.upvoters.add(userId);
        update(guildId, v);
        return removedDown;
    }

    /**
     * Toggled den Downvote. Entfernt Upvote falls vorhanden.
     * @return true wenn der andere Vote entfernt werden muss (👍🏻 Reaction entfernen)
     */
    public static boolean downvote(String guildId, String messageId, String userId) {
        Vorschlag v = getByMessageId(guildId, messageId);
        if (v == null) return false;
        boolean removedUp = v.upvoters.remove(userId);
        if (!v.downvoters.contains(userId)) v.downvoters.add(userId);
        update(guildId, v);
        return removedUp;
    }

    /** Entfernt einen Upvote (wenn Reaction entfernt wird). */
    public static void removeUpvote(String guildId, String messageId, String userId) {
        Vorschlag v = getByMessageId(guildId, messageId);
        if (v == null) return;
        v.upvoters.remove(userId);
        update(guildId, v);
    }

    /** Entfernt einen Downvote (wenn Reaction entfernt wird). */
    public static void removeDownvote(String guildId, String messageId, String userId) {
        Vorschlag v = getByMessageId(guildId, messageId);
        if (v == null) return;
        v.downvoters.remove(userId);
        update(guildId, v);
    }

    // ── Embed ─────────────────────────────────────────────────────────────────

    public static MessageEmbed buildVorschlagEmbed(Vorschlag v) {
        int up    = v.upvoters  != null ? v.upvoters.size()   : 0;
        int down  = v.downvoters != null ? v.downvoters.size() : 0;
        int total = up + down;

        String upBar   = bar(up,   total);
        String downBar = bar(down, total);

        String statusLine = "";
        if ("angenommen".equals(v.status)) statusLine = "\n\n✅ **Angenommen**";
        if ("abgelehnt".equals(v.status))  statusLine = "\n\n❌ **Abgelehnt**";

        return EmbedFactory.create()
            .setTitle(v.title)
            .setDescription(v.description + statusLine)
            .addField("Abstimmung",
                UP   + "  `" + upBar   + "`  **" + up   + "**\n" +
                DOWN + "  `" + downBar + "`  **" + down + "**", false)
            .build();
    }

    private static String bar(int votes, int total) {
        if (total == 0) return "░░░░░░░░░░";
        int filled = Math.round((float) votes / total * 10);
        filled = Math.max(0, Math.min(10, filled));
        return "▓".repeat(filled) + "░".repeat(10 - filled);
    }

    // ── Inner class ───────────────────────────────────────────────────────────

    public static class Vorschlag {
        public String       id;
        public String       title;
        public String       description;
        public String       messageId;
        public List<String> upvoters   = new ArrayList<>();
        public List<String> downvoters = new ArrayList<>();
        public String       status     = "active"; // active | angenommen | abgelehnt

        public Vorschlag(String id, String title, String description) {
            this.id          = id;
            this.title       = title;
            this.description = description;
        }
        public Vorschlag() {}
    }

    /** Emoji-Strings für externe Verwendung. */
    public static final String EMOJI_UP   = UP;
    public static final String EMOJI_DOWN = DOWN;

    private VorschlagManager() {}
}
