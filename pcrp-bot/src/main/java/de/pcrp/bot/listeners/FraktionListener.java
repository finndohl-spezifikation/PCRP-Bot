package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.text.TextInput;
import net.dv8tion.jda.api.interactions.components.text.TextInputStyle;
import net.dv8tion.jda.api.interactions.modals.Modal;

public class FraktionListener extends ListenerAdapter {

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (!"frak-edit".equals(event.getComponentId())) return;

        // Interaction sofort deferren – verhindert "Interaktion fehlgeschlagen"
        // falls irgendwo ein Problem auftritt
        Member member = event.getMember();
        if (member == null) {
            event.reply("❌ Konnte Mitglied nicht abrufen.").setEphemeral(true).queue();
            return;
        }

        // Rollen-Check
        boolean hasRole = member.getRoles().stream()
            .anyMatch(r -> r.getIdLong() == LoggingConfig.FRAK_MANAGER_ROLE_ID);
        if (!hasRole) {
            event.replyEmbeds(EmbedFactory.build(
                "Kein Zugriff",
                "Du benötigst die Fraktions-Manager Rolle um die Liste zu bearbeiten."))
                .setEphemeral(true).queue();
            return;
        }

        String guildId = member.getGuild().getId();
        String current = FraktionManager.getContent(guildId);

        TextInput.Builder inputBuilder = TextInput
            .create("frak-content", "Fraktions Liste", TextInputStyle.PARAGRAPH)
            .setPlaceholder("Eine Fraktion pro Zeile eintragen…")
            .setRequired(false)
            .setMaxLength(3900);

        // setValue darf in JDA 5 nicht mit einem leeren String aufgerufen werden
        if (!current.isBlank()) {
            inputBuilder.setValue(current);
        }

        event.replyModal(
            Modal.create("frak-edit-modal", "Fraktions Liste bearbeiten")
                .addComponents(ActionRow.of(inputBuilder.build()))
                .build()
        ).queue();
    }

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        if (!"frak-edit-modal".equals(event.getModalId())) return;
        if (event.getGuild() == null) {
            event.reply("❌ Kein Guild-Kontext.").setEphemeral(true).queue();
            return;
        }

        String newContent = event.getValue("frak-content") != null
            ? event.getValue("frak-content").getAsString()
            : "";

        String guildId = event.getGuild().getId();
        FraktionManager.setContent(guildId, newContent);
        FraktionManager.updatePanelEmbed(event.getGuild());

        event.replyEmbeds(EmbedFactory.build(
            "✅ Fraktions Liste aktualisiert",
            "Die Liste wurde erfolgreich bearbeitet."))
            .setEphemeral(true).queue();
    }
}
