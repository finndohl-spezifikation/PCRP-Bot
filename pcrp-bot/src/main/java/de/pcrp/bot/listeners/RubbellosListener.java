package de.pcrp.bot.listeners;

import de.pcrp.bot.common.EmbedFactory;
import de.pcrp.bot.common.InventoryManager;
import de.pcrp.bot.common.RubbellosManager;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RubbellosListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(RubbellosListener.class);

    private static String normalizeUrl(String url) {
        if (url == null || url.isBlank()) return "https://example.com";
        url = url.trim();
        if (url.endsWith("/")) url = url.substring(0, url.length() - 1);
        if (!url.startsWith("http://") && !url.startsWith("https://")) url = "https://" + url;
        return url;
    }

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (!"rubbellos-scratch".equals(event.getComponentId())) return;
        if (event.getGuild() == null) return;

        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();

        // Rubbellos im Inventar prüfen (auch mit Emoji-Präfix wie "🎫 | Rubbellos")
        boolean hasTicket = InventoryManager.getInventory(guildId, userId)
            .stream()
            .anyMatch(e -> InventoryManager.nameMatches(e.name, "Rubbellos"));

        if (!hasTicket) {
            event.replyEmbeds(EmbedFactory.build(
                "🎰 Kein Rubbellos",
                "Du hast kein **Rubbellos** in deinem Rucksack.\n" +
                "Kaufe ein Rubbellos, um zu spielen."))
                .setEphemeral(true).queue();
            return;
        }

        // Rubbellos entfernen
        boolean removed = InventoryManager.removeItem(guildId, userId, "Rubbellos", 1);
        if (!removed) {
            event.replyEmbeds(EmbedFactory.build(
                "❌ Fehler",
                "Das Rubbellos konnte nicht eingelöst werden. Bitte versuche es erneut."))
                .setEphemeral(true).queue();
            return;
        }

        // Gewinn vorab bestimmen + Token erstellen
        int prize = RubbellosManager.rollPrize();
        String token = RubbellosManager.createToken(guildId, userId, prize);
        String webUrl = normalizeUrl(System.getenv().getOrDefault("WEB_URL", "https://example.com"));

        try {
            event.replyEmbeds(EmbedFactory.build(
                "🎰 Dein Rubbellos ist bereit!",
                "Öffne die Seite und rubbele dein **Goldene 7** Rubbellos frei!\n\n" +
                "⚠️ Der Link ist **einmalig** und nur für dich gültig."))
                .addActionRow(Button.link(webUrl + "/rubbellos/" + token, "🎰 Jetzt Rubbeln!"))
                .setEphemeral(true).queue();
        } catch (Exception ex) {
            log.error("[Rubbellos] Fehler beim Senden der Antwort.", ex);
            event.replyEmbeds(EmbedFactory.build("❌ Fehler", "Interner Fehler. Bitte versuche es erneut."))
                .setEphemeral(true).queue();
        }

        log.info("[Rubbellos] Token für {} generiert. Gewinn: {}$.", event.getUser().getAsTag(), prize);
    }
}
