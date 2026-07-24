package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.JDA;
import net.dv8tion.jda.api.entities.*;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.entities.emoji.Emoji;
import net.dv8tion.jda.api.events.message.react.MessageReactionAddEvent;
import net.dv8tion.jda.api.events.message.react.MessageReactionRemoveEvent;
import net.dv8tion.jda.api.events.session.ReadyEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/**
 * Verwaltet Gewinnspiele (/gewinnspiel).
 *
 * DataStore-Keys:
 *   giveaway-{messageId}  →  Zeilenformat:
 *       Zeile 0: GIVEAWAY
 *       Zeile 1: Base64(titel)
 *       Zeile 2: Base64(preis)
 *       Zeile 3: end_epoch (Sekunden seit Epoch)
 *       Zeile 4: channelId
 *       Zeile 5: guildId
 *
 *   giveaway-list  →  kommagetrennte MessageIDs aktiver Gewinnspiele
 */
public class GiveawayListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(GiveawayListener.class);

    public static final String PARTY = "🎉";

    private static final ScheduledExecutorService SCHEDULER =
        Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "giveaway-scheduler");
            t.setDaemon(true);
            return t;
        });

    // ════════════════════════════════════════════════════════════
    //  STARTUP – aktive Gewinnspiele wiederherstellen
    // ════════════════════════════════════════════════════════════

    @Override
    public void onReady(ReadyEvent event) {
        JDA jda = event.getJDA();
        String listRaw = DataStore.readString("giveaway-list");
        if (listRaw == null || listRaw.isBlank()) return;

        for (String msgId : listRaw.split(",")) {
            msgId = msgId.trim();
            if (msgId.isBlank()) continue;
            String raw = DataStore.readString("giveaway-" + msgId);
            if (raw == null) continue;

            String[] lines = raw.split("\n", 6);
            if (lines.length < 6) continue;

            long endEpoch   = parseLong(lines[3]);
            long channelId  = parseLong(lines[4]);
            long guildId    = parseLong(lines[5]);
            long nowEpoch   = System.currentTimeMillis() / 1000;
            long delaySec   = endEpoch - nowEpoch;

            final String fMsgId = msgId;
            if (delaySec <= 0) {
                // Bereits abgelaufen → sofort auflösen
                SCHEDULER.schedule(() -> endGiveaway(jda, fMsgId, channelId, guildId), 2, TimeUnit.SECONDS);
            } else {
                SCHEDULER.schedule(() -> endGiveaway(jda, fMsgId, channelId, guildId), delaySec, TimeUnit.SECONDS);
                log.info("[Gewinnspiel] {} wird in {} Sekunden beendet.", fMsgId, delaySec);
            }
        }
    }

    // ════════════════════════════════════════════════════════════
    //  REACTION ADD / REMOVE – Live-Zähler
    // ════════════════════════════════════════════════════════════

    @Override
    public void onMessageReactionAdd(MessageReactionAddEvent event) {
        if (event.getUserIdLong() == event.getJDA().getSelfUser().getIdLong()) return;
        if (!PARTY.equals(event.getEmoji().getName())) return;
        String msgId = event.getMessageId();
        String raw   = DataStore.readString("giveaway-" + msgId);
        if (raw == null) return;
        refreshEmbed(msgId, event.getChannel().asTextChannel(), raw);
    }

    @Override
    public void onMessageReactionRemove(MessageReactionRemoveEvent event) {
        if (event.getUserIdLong() == event.getJDA().getSelfUser().getIdLong()) return;
        if (!PARTY.equals(event.getEmoji().getName())) return;
        String msgId = event.getMessageId();
        String raw   = DataStore.readString("giveaway-" + msgId);
        if (raw == null) return;
        refreshEmbed(msgId, event.getChannel().asTextChannel(), raw);
    }

    // ════════════════════════════════════════════════════════════
    //  Embed aktualisieren
    // ════════════════════════════════════════════════════════════

    private void refreshEmbed(String msgId, TextChannel ch, String raw) {
        ch.retrieveMessageById(msgId).queue(msg -> {
            String[] lines = raw.split("\n", 6);
            String titel = decode(lines.length > 1 ? lines[1] : "");
            String preis = decode(lines.length > 2 ? lines[2] : "");
            long endEpoch = parseLong(lines.length > 3 ? lines[3] : "0");

            int count = countParty(msg);
            msg.editMessageEmbeds(buildEmbed(titel, preis, endEpoch, count))
               .queue(null, e -> log.warn("[Gewinnspiel] Embed-Update fehlgeschlagen: {}", e.getMessage()));
        }, e -> log.warn("[Gewinnspiel] Nachricht {} nicht gefunden.", msgId));
    }

    // ════════════════════════════════════════════════════════════
    //  Gewinnspiel beenden – Gewinner ziehen
    // ════════════════════════════════════════════════════════════

    private void endGiveaway(JDA jda, String msgId, long channelId, long guildId) {
        String raw = DataStore.readString("giveaway-" + msgId);
        if (raw == null) {
            log.info("[Gewinnspiel] {} – keine Daten mehr, überspringe.", msgId);
            return;
        }

        TextChannel ch = jda.getTextChannelById(channelId);
        if (ch == null) {
            log.warn("[Gewinnspiel] Kanal {} nicht gefunden.", channelId);
            return;
        }

        String[] lines = raw.split("\n", 6);
        String titel = decode(lines.length > 1 ? lines[1] : "Gewinnspiel");
        String preis = decode(lines.length > 2 ? lines[2] : "");

        ch.retrieveMessageById(msgId).queue(msg -> {
            // Alle 🎉-Reaktionen abrufen
            msg.getReaction(Emoji.fromUnicode(PARTY)).retrieveUsers().queue(users -> {
                List<User> teilnehmer = users.stream()
                    .filter(u -> !u.isBot())
                    .toList();

                if (teilnehmer.isEmpty()) {
                    // Kein Gewinner
                    msg.editMessageEmbeds(buildEndedEmbed(titel, preis, "Kein Gewinner — niemand hat teilgenommen.", msg.getReactions()))
                       .queue();
                    ch.sendMessage("🎉 Das Gewinnspiel **" + titel + "** ist abgelaufen — leider hat niemand teilgenommen.")
                       .queue();
                } else {
                    User winner = teilnehmer.get(new Random().nextInt(teilnehmer.size()));
                    msg.editMessageEmbeds(buildEndedEmbed(titel, preis,
                        "🏆 Gewinner: " + winner.getAsMention(), msg.getReactions()))
                       .queue();
                    ch.sendMessage("🎉 Herzlichen Glückwunsch " + winner.getAsMention() +
                        "! Du hast das Gewinnspiel **" + titel + "** gewonnen!")
                       .queue();
                }

                // Aus Liste entfernen
                DataStore.deleteKey("giveaway-" + msgId);
                removeFromList(msgId);
            }, e -> log.error("[Gewinnspiel] Reaktionen für {} konnten nicht abgerufen werden.", msgId, e));
        }, e -> {
            log.warn("[Gewinnspiel] Nachricht {} nicht gefunden, bereinige.", msgId);
            DataStore.deleteKey("giveaway-" + msgId);
            removeFromList(msgId);
        });
    }

    // ════════════════════════════════════════════════════════════
    //  Embed-Builder (statisch, für CommandListener)
    // ════════════════════════════════════════════════════════════

    /** Aktives Gewinnspiel-Embed. */
    public static net.dv8tion.jda.api.entities.MessageEmbed buildEmbed(
            String titel, String preis, long endEpoch, int count) {

        String teilnehmer = count == 1 ? "1 Teilnehmer" : count + " Teilnehmer";

        return EmbedFactory.create()
            .setTitle("🎉 " + titel)
            .setDescription(
                "━━━━━━━━━━━━━━━━━━━━━━\n\n" +
                "🏆 **Preis:** " + preis + "\n" +
                "⏰ **Endet:** <t:" + endEpoch + ":R> (<t:" + endEpoch + ":f>)\n" +
                "🎉 **Eingetragen:** " + teilnehmer + "\n\n" +
                "━━━━━━━━━━━━━━━━━━━━━━\n\n" +
                "Drücke auf 🎉 um teilzunehmen!")
            .build();
    }

    /** Abgelaufenes Gewinnspiel-Embed. */
    private static net.dv8tion.jda.api.entities.MessageEmbed buildEndedEmbed(
            String titel, String preis, String winnerLine,
            List<MessageReaction> reactions) {

        int count = 0;
        for (MessageReaction r : reactions) {
            if (PARTY.equals(r.getEmoji().getName())) {
                count = Math.max(0, r.getCount() - (r.isSelf() ? 1 : 0));
            }
        }
        String teilnehmer = count == 1 ? "1 Teilnehmer" : count + " Teilnehmer";

        return EmbedFactory.create()
            .setTitle("🎉 " + titel + " — Beendet")
            .setDescription(
                "━━━━━━━━━━━━━━━━━━━━━━\n\n" +
                "🏆 **Preis:** " + preis + "\n" +
                "🎉 **Teilnehmer:** " + teilnehmer + "\n\n" +
                "━━━━━━━━━━━━━━━━━━━━━━\n\n" +
                winnerLine)
            .build();
    }

    // ════════════════════════════════════════════════════════════
    //  Listenverwaltung
    // ════════════════════════════════════════════════════════════

    /** Fügt eine MessageId zur persistenten Liste aktiver Gewinnspiele hinzu. */
    public static synchronized void addToList(String msgId) {
        String raw = DataStore.readString("giveaway-list");
        Set<String> ids = new LinkedHashSet<>();
        if (raw != null && !raw.isBlank()) {
            for (String s : raw.split(",")) {
                String t = s.trim();
                if (!t.isBlank()) ids.add(t);
            }
        }
        ids.add(msgId);
        DataStore.writeString("giveaway-list", String.join(",", ids));
    }

    private static synchronized void removeFromList(String msgId) {
        String raw = DataStore.readString("giveaway-list");
        if (raw == null) return;
        List<String> ids = new ArrayList<>();
        for (String s : raw.split(",")) {
            String t = s.trim();
            if (!t.isBlank() && !t.equals(msgId)) ids.add(t);
        }
        DataStore.writeString("giveaway-list", String.join(",", ids));
    }

    /** Plant den Ablauf eines Gewinnspiels. */
    public static void schedule(JDA jda, String msgId, long channelId, long guildId, long delaySeconds) {
        GiveawayListener self = new GiveawayListener();
        SCHEDULER.schedule(() -> self.endGiveaway(jda, msgId, channelId, guildId), delaySeconds, TimeUnit.SECONDS);
    }

    // ════════════════════════════════════════════════════════════
    //  Hilfsmethoden
    // ════════════════════════════════════════════════════════════

    private static int countParty(Message msg) {
        for (MessageReaction r : msg.getReactions()) {
            if (PARTY.equals(r.getEmoji().getName())) {
                return Math.max(0, r.getCount() - (r.isSelf() ? 1 : 0));
            }
        }
        return 0;
    }

    public static String encode(String s) {
        return java.util.Base64.getEncoder().encodeToString(
            (s == null ? "" : s).getBytes(StandardCharsets.UTF_8));
    }

    public static String decode(String s) {
        try {
            return new String(java.util.Base64.getDecoder().decode(s == null ? "" : s.trim()),
                StandardCharsets.UTF_8);
        } catch (Exception e) {
            return s == null ? "" : s;
        }
    }

    private static long parseLong(String s) {
        try { return Long.parseLong(s == null ? "0" : s.trim()); }
        catch (NumberFormatException e) { return 0L; }
    }
}
