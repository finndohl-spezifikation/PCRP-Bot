package de.pcrp.bot.common;

import com.google.gson.*;
import net.dv8tion.jda.api.entities.MessageEmbed;

import java.util.*;

/**
 * Verwaltet Lobby-Abstimmungen: Votes pro Nachricht.
 * DataStore-Keys:
 *   lobby-votes-{messageId}   → JSON map userId→emoji
 *   lobby-uhrzeit-{messageId} → Uhrzeit-String
 */
public final class LobbyManager {

    private static final Gson GSON = new Gson();

    public static final String E_JA       = "✅";
    public static final String E_SPAETER  = "🕒";
    public static final String E_MAYBE    = "🤔";
    public static final String E_NEIN     = "❌";
    public static final List<String> EMOJIS = List.of(E_JA, E_SPAETER, E_MAYBE, E_NEIN);

    private static String votesKey(String messageId)   { return "lobby-votes-"   + messageId; }
    private static String uhrzeitKey(String messageId) { return "lobby-uhrzeit-" + messageId; }

    // ── Persistenz ────────────────────────────────────────────────────────────

    public static void storeUhrzeit(String messageId, String uhrzeit) {
        DataStore.writeString(uhrzeitKey(messageId), uhrzeit);
    }

    public static String getUhrzeit(String messageId) {
        String s = DataStore.readString(uhrzeitKey(messageId));
        return s != null ? s : "?";
    }

    private static Map<String, String> readVotes(String messageId) {
        String raw = DataStore.readString(votesKey(messageId));
        Map<String, String> map = new LinkedHashMap<>();
        if (raw == null || raw.isBlank()) return map;
        try {
            JsonObject obj = GSON.fromJson(raw, JsonObject.class);
            for (Map.Entry<String, JsonElement> e : obj.entrySet())
                map.put(e.getKey(), e.getValue().getAsString());
        } catch (Exception ignored) {}
        return map;
    }

    private static void saveVotes(String messageId, Map<String, String> votes) {
        JsonObject obj = new JsonObject();
        votes.forEach(obj::addProperty);
        DataStore.writeString(votesKey(messageId), GSON.toJson(obj));
    }

    /**
     * Setzt den Vote. Gibt das alte Emoji zurück (oder null wenn neu).
     */
    public static String setVote(String messageId, String userId, String emoji) {
        Map<String, String> votes = readVotes(messageId);
        String old = votes.put(userId, emoji);
        saveVotes(messageId, votes);
        return old;
    }

    public static void removeVote(String messageId, String userId) {
        Map<String, String> votes = readVotes(messageId);
        votes.remove(userId);
        saveVotes(messageId, votes);
    }

    public static String getCurrentVote(String messageId, String userId) {
        return readVotes(messageId).get(userId);
    }

    public static int getCount(String messageId, String emoji) {
        Map<String, String> votes = readVotes(messageId);
        return (int) votes.values().stream().filter(e -> e.equals(emoji)).count();
    }

    public static boolean isLobbyMessage(String messageId) {
        return DataStore.readString(uhrzeitKey(messageId)) != null;
    }

    // ── Embed ─────────────────────────────────────────────────────────────────

    /** Initialer Embed beim Erstellen (alle Votes = 0, GIF noch als Attachment). */
    public static MessageEmbed buildInitialEmbed(String uhrzeit) {
        return buildDescription(uhrzeit, 0, 0, 0, 0)
            .setImage("attachment://lobby-anim.gif")
            .build();
    }

    /** Aktualisiertes Embed nach einem Vote (ohne Attachment, Bild bleibt via URL). */
    public static MessageEmbed buildEmbed(String messageId) {
        String uhrzeit = getUhrzeit(messageId);
        int ja      = getCount(messageId, E_JA);
        int spaeter = getCount(messageId, E_SPAETER);
        int maybe   = getCount(messageId, E_MAYBE);
        int nein    = getCount(messageId, E_NEIN);
        return buildDescription(uhrzeit, ja, spaeter, maybe, nein).build();
    }

    private static net.dv8tion.jda.api.EmbedBuilder buildDescription(
            String uhrzeit, int ja, int spaeter, int maybe, int nein) {
        return EmbedFactory.create()
            .setDescription(
                "────── ⋆⋅☆⋅⋆ ──────\n" +
                "📋 **LOBBY-ABSTIMMUNG** 📋\n\n" +
                "🕒 **RP-START** 🕒\n" +
                uhrzeit + "\n\n" +
                "🗳️ **OPTIONEN** 🗳️\n" +
                E_JA      + " ── Ich komme **(" + ja      + ")**\n" +
                E_SPAETER + " ── Ich komme später **(" + spaeter + ")**\n" +
                E_MAYBE   + " ── Ich komme vielleicht **(" + maybe   + ")**\n" +
                E_NEIN    + " ── Ich komme nicht **(" + nein    + ")**");
    }

    private LobbyManager() {}
}
