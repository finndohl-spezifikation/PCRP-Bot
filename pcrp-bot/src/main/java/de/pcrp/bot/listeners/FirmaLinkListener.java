package de.pcrp.bot.listeners;

import de.pcrp.bot.common.ModerationConfig;
import de.pcrp.bot.web.CityChatHandler;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;

/**
 * Verarbeitet Approve/Reject-Buttons für City-Chat-Firma-Link-Anfragen.
 * Button-IDs: cfl-a:{guildId}:{phone}:{linkId}  und  cfl-r:{guildId}:{phone}:{linkId}
 */
public class FirmaLinkListener extends ListenerAdapter {

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        String cid = event.getComponentId();
        if (!cid.startsWith("cfl-a:") && !cid.startsWith("cfl-r:")) return;

        // Nur der Admin darf entscheiden
        if (event.getUser().getIdLong() != ModerationConfig.OWNER_ID) {
            event.reply("❌ Du bist nicht berechtigt, diese Anfrage zu bearbeiten.")
                 .setEphemeral(true).queue();
            return;
        }

        boolean approve = cid.startsWith("cfl-a:");
        String payload  = cid.substring(6); // entferne "cfl-a:" oder "cfl-r:"
        String[] parts  = payload.split(":", 3);
        if (parts.length < 3) { event.reply("⚠️ Ungültige Button-ID.").setEphemeral(true).queue(); return; }

        String guildId = parts[0];
        String phone   = parts[1];
        String linkId  = parts[2];

        if (approve) {
            CityChatHandler.approveFirmaLink(guildId, phone, linkId);
            event.editMessage("✅ Link von `" + phone + "` wurde **genehmigt**.")
                 .setComponents().queue();
        } else {
            CityChatHandler.rejectFirmaLink(guildId, phone, linkId);
            event.editMessage("❌ Link von `" + phone + "` wurde **abgelehnt** und gelöscht.")
                 .setComponents().queue();
        }
    }
}
