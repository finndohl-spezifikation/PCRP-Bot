package de.pcrp.bot.listeners;

import de.pcrp.bot.common.Lockdown;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.command.CommandAutoCompleteInteractionEvent;
import net.dv8tion.jda.api.events.interaction.command.MessageContextInteractionEvent;
import net.dv8tion.jda.api.events.interaction.command.SlashCommandInteractionEvent;
import net.dv8tion.jda.api.events.interaction.command.UserContextInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.EntitySelectInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.StringSelectInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.callbacks.IReplyCallback;

import java.util.List;

/**
 * Fängt im Lockdown-Modus JEDE Interaktion ab (Slash-Command, Button, Select,
 * Modal, Kontext-Menü) und antwortet immer mit der Eigentumsübergabe-Fehlermeldung.
 * Die übrigen Funktions-Listener werden im Lockdown gar nicht erst registriert,
 * damit keinerlei Geschäftslogik mehr ausgeführt wird.
 */
public class LockdownListener extends ListenerAdapter {

    @Override
    public void onSlashCommandInteraction(SlashCommandInteractionEvent event) {
        block(event);
    }

    @Override
    public void onUserContextInteraction(UserContextInteractionEvent event) {
        block(event);
    }

    @Override
    public void onMessageContextInteraction(MessageContextInteractionEvent event) {
        block(event);
    }

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        block(event);
    }

    @Override
    public void onStringSelectInteraction(StringSelectInteractionEvent event) {
        block(event);
    }

    @Override
    public void onEntitySelectInteraction(EntitySelectInteractionEvent event) {
        block(event);
    }

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        block(event);
    }

    @Override
    public void onCommandAutoCompleteInteraction(CommandAutoCompleteInteractionEvent event) {
        if (!Lockdown.ACTIVE) return;
        // Autocomplete darf nur mit Choices antworten — leer antworten, damit keine Vorschläge kommen.
        event.replyChoices(List.of()).queue(null, err -> {});
    }

    /** Antwortet im Lockdown auf jede Interaktion mit der Eigentumsübergabe-Fehlermeldung. */
    private static void block(IReplyCallback event) {
        if (!Lockdown.ACTIVE) return;
        event.replyEmbeds(Lockdown.blockedEmbed())
            .setEphemeral(true)
            .queue(null, err -> {});
    }
}
