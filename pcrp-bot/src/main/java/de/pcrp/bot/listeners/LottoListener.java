package de.pcrp.bot.listeners;

import de.pcrp.bot.common.EmbedFactory;
import de.pcrp.bot.common.InventoryManager;
import de.pcrp.bot.common.LottoManager;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LottoListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(LottoListener.class);

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (!"lotto-enroll".equals(event.getComponentId())) return;
        if (event.getGuild() == null) return;

        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();

        // Prüfen ob Lottoschein im Inventar
        boolean hasTicket = InventoryManager.getInventory(guildId, userId)
            .stream()
            .anyMatch(e -> "Lottoschein".equalsIgnoreCase(e.name));

        if (!hasTicket) {
            event.replyEmbeds(EmbedFactory.build(
                "🎟️ Kein Lottoschein",
                "Du hast keinen **Lottoschein** in deinem Rucksack.\n" +
                "Kaufe einen Lottoschein, um an der Ziehung teilzunehmen."))
                .setEphemeral(true).queue();
            return;
        }

        // Lottoschein entfernen
        boolean removed = InventoryManager.removeItem(guildId, userId, "Lottoschein", 1);
        if (!removed) {
            event.replyEmbeds(EmbedFactory.build(
                "❌ Fehler",
                "Dein Lottoschein konnte nicht eingelöst werden. Bitte versuche es erneut."))
                .setEphemeral(true).queue();
            return;
        }

        // Einschreiben
        String enrollError = LottoManager.enroll(guildId, userId);
        if (enrollError != null) {
            // Lottoschein zurückgeben wenn Einschreibung scheitert
            InventoryManager.addItem(guildId, userId, "Lottoschein", 1);
            event.replyEmbeds(EmbedFactory.build(
                "❌ Nicht möglich",
                enrollError))
                .setEphemeral(true).queue();
            return;
        }

        int jackpot = LottoManager.getCurrentJackpot(guildId);
        event.replyEmbeds(EmbedFactory.build(
            "🎰 Erfolgreich eingeschrieben!",
            "Dein **Lottoschein** wurde eingelöst.\n\n" +
            "**Jackpot:** " + LottoManager.formatAmount(jackpot) + "\n" +
            "Die Ziehung findet heute um **12:00 Uhr** statt.\n\n" +
            "Viel Glück! 🍀"))
            .setEphemeral(true).queue();

        log.info("[Lotto] {} hat sich für die Ziehung eingeschrieben.", event.getUser().getAsTag());
    }
}
