package de.pcrp.bot.listeners;

import de.pcrp.bot.common.DataStore;
import de.pcrp.bot.common.EmbedFactory;
import de.pcrp.bot.common.LoggingConfig;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.entities.Role;
import net.dv8tion.jda.api.events.message.MessageReceivedEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;

import java.util.concurrent.TimeUnit;

public class CounterListener extends ListenerAdapter {

    private static final int TARGET = 100;

    @Override
    public void onMessageReceived(MessageReceivedEvent event) {
        if (!event.isFromGuild()) return;
        if (event.getAuthor().isBot()) return;
        if (event.getChannel().getIdLong() != LoggingConfig.COUNTER_CHANNEL_ID) return;

        String content = event.getMessage().getContentRaw().trim();
        String guildId = event.getGuild().getId();

        // Nur Zahlen erlaubt
        int num;
        try {
            num = Integer.parseInt(content);
        } catch (NumberFormatException e) {
            event.getMessage().delete().queue(null, x -> {});
            event.getChannel()
                .sendMessage("❌ Bitte nur Zahlen schreiben!")
                .queue(msg -> msg.delete().queueAfter(5, TimeUnit.SECONDS, null, x -> {}));
            return;
        }

        // Doppelt hintereinander?
        String lastUserId = DataStore.readString("counter-last-user-" + guildId);
        if (event.getAuthor().getId().equals(lastUserId)) {
            event.getMessage().delete().queue(null, x -> {});
            event.getChannel()
                .sendMessageEmbeds(EmbedFactory.build(
                    "⛔ Nicht erlaubt",
                    "Du kannst nicht 2 Zahlen hintereinander schreiben."))
                .queue(msg -> msg.delete().queueAfter(6, TimeUnit.SECONDS, null, x -> {}));
            return;
        }

        // Aktuelle Zahl prüfen
        int current  = readCount(guildId);
        int expected = current + 1;

        if (num != expected) {
            // Falsche Zahl → Nachricht löschen + Reset
            event.getMessage().delete().queue(null, x -> {});
            resetCounter(guildId);
            event.getChannel()
                .sendMessage(event.getAuthor().getAsMention() +
                    " hat die falsche Zahl geschrieben! (**" + num + "** statt **" + expected +
                    "**) — Neustart bei **0**!")
                .queue();
            return;
        }

        // Richtige Zahl ✓
        DataStore.writeString("counter-value-"    + guildId, String.valueOf(num));
        DataStore.writeString("counter-last-user-" + guildId, event.getAuthor().getId());

        // Ziel erreicht?
        if (num == TARGET) {
            resetCounter(guildId);
            event.getChannel()
                .sendMessage("🎉 " + event.getAuthor().getAsMention() +
                    " hat **100** erreicht! Sehr gut — Neustart bei **0**!")
                .queue();

            // Zahlen-Rang-Rolle vergeben (falls konfiguriert)
            if (LoggingConfig.COUNTER_RANK_ROLE_ID != 0L) {
                Member member = event.getMember();
                Role   role   = event.getGuild().getRoleById(LoggingConfig.COUNTER_RANK_ROLE_ID);
                if (member != null && role != null) {
                    event.getGuild().addRoleToMember(member, role).queue(null, x -> {});
                }
            }
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static int readCount(String guildId) {
        String s = DataStore.readString("counter-value-" + guildId);
        if (s == null || s.isBlank()) return 0;
        try { return Integer.parseInt(s.trim()); }
        catch (NumberFormatException e) { return 0; }
    }

    private static void resetCounter(String guildId) {
        DataStore.writeString("counter-value-"     + guildId, "0");
        DataStore.writeString("counter-last-user-" + guildId, "");
    }
}
