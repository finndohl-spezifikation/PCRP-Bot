package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.MessageReaction;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.entities.emoji.Emoji;
import net.dv8tion.jda.api.events.message.react.MessageReactionAddEvent;
import net.dv8tion.jda.api.events.message.react.MessageReactionRemoveEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

/**
 * Verwaltet Abstimmungen (/abstimmung) und Aktivitätschecks (/aktivitätscheck).
 *
 * DataStore-Keys:
 *   poll-{messageId}  →  Zeilenformat:
 *       Zeile 0: POLL oder ACTIVITY
 *       Zeile 1: Base64(titel)
 *       Zeile 2: Base64(text)          [nur POLL]
 *       Zeile 3: Base64(optionen)      [nur POLL, kann leer sein]
 */
public class PollListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(PollListener.class);

    public static final String THUMB_UP   = "👍";
    public static final String THUMB_DOWN = "👎";
    public static final String CHECK      = "✅";

    private static final int BAR_LEN      = 20;
    private static final int ACTIVITY_MAX = 30;   // ab 30 Stimmen ist der Balken voll

    // ════════════════════════════════════════════════════════════
    //  REACTION ADD  – exklusive Abstimmung + Embed-Update
    // ════════════════════════════════════════════════════════════

    @Override
    public void onMessageReactionAdd(MessageReactionAddEvent event) {
        if (event.getUserIdLong() == event.getJDA().getSelfUser().getIdLong()) return;
        String msgId = event.getMessageId();
        String raw   = DataStore.readString("poll-" + msgId);
        if (raw == null) return;

        String type = raw.split("\n", 2)[0];
        TextChannel ch = event.getChannel().asTextChannel();

        if ("POLL".equals(type)) {
            // Immer nur eine Reaktion erlaubt – die andere entfernen
            String emojiName = event.getEmoji().getName();
            String other     = THUMB_UP.equals(emojiName) ? THUMB_DOWN : THUMB_UP;
            event.getJDA().retrieveUserById(event.getUserIdLong()).queue(user -> {
                ch.removeReactionById(msgId, Emoji.fromUnicode(other), user)
                  .queue(
                    v -> refreshEmbed(msgId, ch, raw),
                    e -> refreshEmbed(msgId, ch, raw)
                  );
            }, e -> refreshEmbed(msgId, ch, raw));
        } else if ("ACTIVITY".equals(type)) {
            refreshEmbed(msgId, ch, raw);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  REACTION REMOVE  – Embed-Update
    // ════════════════════════════════════════════════════════════

    @Override
    public void onMessageReactionRemove(MessageReactionRemoveEvent event) {
        if (event.getUserIdLong() == event.getJDA().getSelfUser().getIdLong()) return;
        String msgId = event.getMessageId();
        String raw   = DataStore.readString("poll-" + msgId);
        if (raw == null) return;

        String type = raw.split("\n", 2)[0];
        if ("POLL".equals(type) || "ACTIVITY".equals(type)) {
            refreshEmbed(msgId, event.getChannel().asTextChannel(), raw);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  Embed aktualisieren
    // ════════════════════════════════════════════════════════════

    private void refreshEmbed(String msgId, TextChannel ch, String raw) {
        ch.retrieveMessageById(msgId).queue(msg -> {
            String[] lines = raw.split("\n", 4);
            String type = lines[0];

            if ("POLL".equals(type)) {
                String title   = decode(lines.length > 1 ? lines[1] : "");
                String text    = decode(lines.length > 2 ? lines[2] : "");
                String options = decode(lines.length > 3 ? lines[3] : "");

                int yes = 0, no = 0;
                for (MessageReaction r : msg.getReactions()) {
                    String name  = r.getEmoji().getName();
                    int    count = Math.max(0, r.getCount() - (r.isSelf() ? 1 : 0));
                    if      (THUMB_UP.equals(name))   yes = count;
                    else if (THUMB_DOWN.equals(name)) no  = count;
                }
                msg.editMessageEmbeds(buildPollEmbed(title, text, options, yes, no))
                   .queue(null, e -> log.warn("[Poll] Embed-Update fehlgeschlagen: {}", e.getMessage()));

            } else if ("ACTIVITY".equals(type)) {
                String title = decode(lines.length > 1 ? lines[1] : "Aktivitätscheck");
                int count = 0;
                for (MessageReaction r : msg.getReactions()) {
                    if (CHECK.equals(r.getEmoji().getName())) {
                        count = Math.max(0, r.getCount() - (r.isSelf() ? 1 : 0));
                    }
                }
                msg.editMessageEmbeds(buildActivityEmbed(title, count))
                   .queue(null, e -> log.warn("[Aktivität] Embed-Update fehlgeschlagen: {}", e.getMessage()));
            }
        }, e -> log.warn("[Poll] Nachricht {} nicht gefunden.", msgId));
    }

    // ════════════════════════════════════════════════════════════
    //  Embed-Builder (statisch, für Nutzung aus CommandListener)
    // ════════════════════════════════════════════════════════════

    /** Baut das Abstimmungs-Embed mit je einem Balken für Dafür und Dagegen. */
    public static net.dv8tion.jda.api.entities.MessageEmbed buildPollEmbed(
            String title, String text, String options, int yes, int no) {

        int total = yes + no;

        int filledYes = total == 0 ? 0 : (int) Math.round((double) yes / total * BAR_LEN);
        int filledNo  = total == 0 ? 0 : (int) Math.round((double) no  / total * BAR_LEN);

        String barYes = "█".repeat(filledYes) + "░".repeat(BAR_LEN - filledYes);
        String barNo  = "█".repeat(filledNo)  + "░".repeat(BAR_LEN - filledNo);

        String yesPercent = total == 0 ? "0%" : Math.round((double) yes / total * 100) + "%";
        String noPercent  = total == 0 ? "0%" : Math.round((double) no  / total * 100) + "%";

        String labelYes = yes == 1 ? "1 Stimme" : yes + " Stimmen";
        String labelNo  = no  == 1 ? "1 Stimme" : no  + " Stimmen";

        StringBuilder desc = new StringBuilder();
        desc.append(text).append("\n\n");
        desc.append("━━━━━━━━━━━━━━━━━━━━━━\n\n");
        desc.append("👍 **Dafür** — ").append(labelYes).append(" (").append(yesPercent).append(")\n");
        desc.append("`").append(barYes).append("`\n\n");
        desc.append("👎 **Dagegen** — ").append(labelNo).append(" (").append(noPercent).append(")\n");
        desc.append("`").append(barNo).append("`");

        return EmbedFactory.create()
            .setTitle("🗳️ " + title)
            .setDescription(desc.toString())
            .build();
    }

    /** Baut das Aktivitätscheck-Embed mit wachsendem Balken. */
    public static net.dv8tion.jda.api.entities.MessageEmbed buildActivityEmbed(String title, int count) {
        int filled = Math.min(BAR_LEN, (int) Math.round((double) count / ACTIVITY_MAX * BAR_LEN));
        String bar = "█".repeat(filled) + "░".repeat(BAR_LEN - filled);

        String mitglieder = count == 1 ? "**1 Mitglied**" : "**" + count + " Mitglieder**";
        String verb       = count == 1 ? "hat" : "haben";

        String desc =
            "Bitte meldet euch mit ✅, um eure Aktivität zu bestätigen. " +
            "Eure Rückmeldung hilft uns, aktive Mitglieder zu erkennen und den Server besser zu planen.\n\n" +
            "━━━━━━━━━━━━━━━━━━━━━━\n\n" +
            "✅ " + mitglieder + " " + verb + " sich gemeldet\n" +
            "`" + bar + "`";

        return EmbedFactory.create()
            .setTitle("📊 " + title)
            .setDescription(desc)
            .build();
    }

    // ════════════════════════════════════════════════════════════
    //  Base64-Hilfen
    // ════════════════════════════════════════════════════════════

    public static String encode(String s) {
        return Base64.getEncoder().encodeToString(
            (s == null ? "" : s).getBytes(StandardCharsets.UTF_8));
    }

    public static String decode(String s) {
        try {
            return new String(Base64.getDecoder().decode(s == null ? "" : s.trim()),
                StandardCharsets.UTF_8);
        } catch (Exception e) {
            return s == null ? "" : s;
        }
    }
}
