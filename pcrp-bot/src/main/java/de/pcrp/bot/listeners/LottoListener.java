package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LottoListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(LottoListener.class);

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();

        switch (event.getComponentId()) {

            case "lotto-join" -> {
                // Direkt am Lotto teilnehmen: Lottoschein aus Inventar entnehmen + einschreiben
                String error = LottoManager.enroll(guildId, userId);
                if (error != null) {
                    event.replyEmbeds(EmbedFactory.build("❌ Fehler", error))
                        .setEphemeral(true).queue();
                    return;
                }
                int jackpot      = LottoManager.getCurrentJackpot(guildId);
                int participants = LottoManager.getParticipantCount(guildId);
                event.replyEmbeds(EmbedFactory.build(
                    "✅ Lottoschein abgegeben!",
                    "Du nimmst an der heutigen Ziehung teil!\n\n" +
                    "**💰 Jackpot:** " + LottoManager.formatAmount(jackpot) + "\n" +
                    "**👥 Teilnehmer:** " + participants + "\n\n" +
                    "Die Ziehung findet täglich um **12:00 Uhr** statt. Viel Glück! 🍀"))
                    .setEphemeral(true).queue();
                log.info("[Lotto] {} direkt eingeschrieben.", event.getUser().getAsTag());
            }

            case "lotto-get-link" -> {
                // Legacy: Einmal-Token → Link zur Website (für alte Panel-Nachrichten)
                if (LottoManager.isParticipant(guildId, userId)) {
                    event.replyEmbeds(EmbedFactory.build(
                        "🎰 Bereits eingeschrieben",
                        "Du nimmst bereits an der heutigen Ziehung teil.\n" +
                        "Die Ziehung findet um **12:00 Uhr** statt. Viel Glück! 🍀"))
                        .setEphemeral(true).queue();
                    return;
                }
                String token  = LottoManager.createToken(guildId, userId);
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
    }
}
