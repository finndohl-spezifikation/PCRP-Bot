package de.pcrp.bot.listeners;

import de.pcrp.bot.common.BotContext;
import de.pcrp.bot.common.EmbedFactory;
import de.pcrp.bot.common.LottoManager;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LottoListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(LottoListener.class);

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (!"lotto-get-link".equals(event.getComponentId())) return;
        if (event.getGuild() == null) return;

        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();

        // Bereits eingeschrieben?
        if (LottoManager.isParticipant(guildId, userId)) {
            event.replyEmbeds(EmbedFactory.build(
                "🎰 Bereits eingeschrieben",
                "Du nimmst bereits an der heutigen Ziehung teil.\n" +
                "Die Ziehung findet um **12:00 Uhr** statt. Viel Glück! 🍀"))
                .setEphemeral(true).queue();
            return;
        }

        // Einmal-Token generieren → Link zur Website
        String token = LottoManager.createToken(guildId, userId);
        String webUrl = System.getenv().getOrDefault("WEB_URL", "https://example.com");
        if (webUrl.endsWith("/")) webUrl = webUrl.substring(0, webUrl.length() - 1);

        event.replyEmbeds(EmbedFactory.build(
            "🎟️ Lottoschein abgeben",
            "Klicke auf den Button, um dein persönliches Lotto-Formular zu öffnen.\n\n" +
            "⚠️ Der Link ist **einmalig** und nur für dich gültig.\n" +
            "Die Ziehung findet täglich um **12:00 Uhr** statt."))
            .addActionRow(Button.link(webUrl + "/lotto/" + token, "🎟️ Lottoschein abgeben"))
            .setEphemeral(true).queue();

        log.info("[Lotto] Token für {} generiert.", event.getUser().getAsTag());
    }
}
