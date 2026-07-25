package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LottoListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(LottoListener.class);

    private static String normalizeUrl(String url) {
        if (url == null || url.isBlank()) return "https://example.com";
        url = url.trim();
        if (url.endsWith("/")) url = url.substring(0, url.length() - 1);
        if (!url.startsWith("http://") && !url.startsWith("https://")) url = "https://" + url;
        return url;
    }

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();

        switch (event.getComponentId()) {

            case "lotto-get-link" -> {
                if (LottoManager.isParticipant(guildId, userId)) {
                    event.replyEmbeds(EmbedFactory.build(
                        "🎰 Bereits eingeschrieben",
                        "Du nimmst bereits an der heutigen Ziehung teil.\n" +
                        "Die Ziehung findet um **12:00 Uhr** statt. Viel Glück! 🍀"))
                        .setEphemeral(true).queue();
                    return;
                }
                String token  = LottoManager.createToken(guildId, userId);
                String webUrl = "https://dashboards.paradisecity-roleplay-85a.workers.dev";
                try {
                    event.replyEmbeds(EmbedFactory.build(
                        "🎟️ Lottoschein abgeben",
                        "Klicke auf den Button, um dein persönliches Lotto-Formular zu öffnen.\n\n" +
                        "⚠️ Der Link ist **einmalig** und nur für dich gültig.\n" +
                        "Die Ziehung findet täglich um **12:00 Uhr** statt."))
                        .addActionRow(Button.link(webUrl + "/lotto/" + token, "🎟️ Lottoschein abgeben"))
                        .setEphemeral(true).queue();
                } catch (Exception ex) {
                    log.error("[Lotto] Fehler beim Senden der Antwort.", ex);
                    event.replyEmbeds(EmbedFactory.build("❌ Fehler", "Interner Fehler. Bitte versuche es erneut."))
                        .setEphemeral(true).queue();
                }
                log.info("[Lotto] Token für {} generiert.", event.getUser().getAsTag());
            }
        }
    }
}
