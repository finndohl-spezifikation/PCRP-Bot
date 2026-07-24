package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.text.TextInput;
import net.dv8tion.jda.api.interactions.components.text.TextInputStyle;
import net.dv8tion.jda.api.interactions.modals.Modal;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

public class RucksackListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(RucksackListener.class);

    // ── Buttons ───────────────────────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        String id = event.getComponentId();

        switch (id) {
            case "rucksack-open"     -> handleOwnRucksack(event);
            case "rucksack-other"    -> handleOtherRucksackPrompt(event);
            case "rucksack-transfer" -> handleTransferPrompt(event);
        }
    }

    /** Eigenen Rucksack anzeigen — ephemeral mit "Item Übergeben"-Button. */
    private void handleOwnRucksack(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();
        String name    = event.getMember() != null
            ? event.getMember().getEffectiveName()
            : event.getUser().getName();

        event.replyEmbeds(InventoryManager.buildEmbed(guildId, userId, name))
            .addActionRow(Button.primary("rucksack-transfer", "📦 Item Übergeben"))
            .setEphemeral(true)
            .queue();
    }

    /** "Anderen Rucksack Öffnen" — Modal zum Eingeben der User-ID. */
    private void handleOtherRucksackPrompt(ButtonInteractionEvent event) {
        Modal modal = Modal.create("rucksack-search-modal", "Anderen Rucksack öffnen")
            .addComponents(ActionRow.of(
                TextInput.create("spieler-id", "Discord User-ID", TextInputStyle.SHORT)
                    .setPlaceholder("z. B. 123456789012345678")
                    .setRequired(true)
                    .build()
            )).build();
        event.replyModal(modal).queue();
    }

    /** "Item Übergeben" — Modal mit Empfänger + Items. */
    private void handleTransferPrompt(ButtonInteractionEvent event) {
        Modal modal = Modal.create("rucksack-transfer-modal", "Items übergeben")
            .addComponents(
                ActionRow.of(
                    TextInput.create("empfaenger", "Empfänger (Discord User-ID)", TextInputStyle.SHORT)
                        .setPlaceholder("z. B. 123456789012345678")
                        .setRequired(true)
                        .build()),
                ActionRow.of(
                    TextInput.create("items", "Items (Format: ItemName: Menge, ItemName: Menge)", TextInputStyle.PARAGRAPH)
                        .setPlaceholder("Bargeld: 500\nWaffe: 1\nDrogen: 10")
                        .setRequired(true)
                        .build())
            ).build();
        event.replyModal(modal).queue();
    }

    // ── Modals ────────────────────────────────────────────────────────────────

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        switch (event.getModalId()) {
            case "rucksack-search-modal"   -> handleOtherRucksackView(event);
            case "rucksack-transfer-modal" -> handleTransferExecute(event);
        }
    }

    /** Fremden Rucksack anzeigen — ephemeral, kein Transfer-Button. */
    private void handleOtherRucksackView(ModalInteractionEvent event) {
        if (event.getGuild() == null) return;
        String spielerIdRaw = event.getValue("spieler-id") == null ? ""
            : event.getValue("spieler-id").getAsString().trim().replaceAll("[<@!>]", "");

        long targetId;
        try { targetId = Long.parseLong(spielerIdRaw); }
        catch (NumberFormatException e) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültige ID",
                "Bitte gib eine gültige Discord User-ID ein."))
                .setEphemeral(true).queue();
            return;
        }

        event.getGuild().retrieveMemberById(targetId).queue(member -> {
            String guildId  = event.getGuild().getId();
            String userId   = member.getId();
            String dispName = member.getEffectiveName();
            event.replyEmbeds(InventoryManager.buildEmbed(guildId, userId, dispName))
                .setEphemeral(true)
                .queue();
        }, err -> event.replyEmbeds(EmbedFactory.build("❌ Nicht gefunden",
            "Kein Mitglied mit dieser ID auf dem Server gefunden."))
            .setEphemeral(true).queue());
    }

    /** Transfer ausführen. */
    private void handleTransferExecute(ModalInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId   = event.getGuild().getId();
        String fromId    = event.getUser().getId();

        String empfRaw  = event.getValue("empfaenger") == null ? ""
            : event.getValue("empfaenger").getAsString().trim().replaceAll("[<@!>]", "");
        String itemsRaw = event.getValue("items") == null ? ""
            : event.getValue("items").getAsString().trim().replace("\n", ",");

        // Empfänger-ID parsen
        long toIdL;
        try { toIdL = Long.parseLong(empfRaw); }
        catch (NumberFormatException e) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültige Empfänger-ID",
                "Bitte gib eine gültige Discord User-ID ein."))
                .setEphemeral(true).queue();
            return;
        }
        if (String.valueOf(toIdL).equals(fromId)) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültig",
                "Du kannst dir selbst keine Items übergeben."))
                .setEphemeral(true).queue();
            return;
        }

        // Items parsen
        List<InventoryManager.Item> transfers;
        try { transfers = InventoryManager.parseTransferInput(itemsRaw); }
        catch (InventoryManager.TransferError te) {
            event.replyEmbeds(EmbedFactory.build("❌ Format-Fehler", te.getMessage()))
                .setEphemeral(true).queue();
            return;
        }

        final long toId = toIdL;
        final List<InventoryManager.Item> finalTransfers = transfers;

        event.getGuild().retrieveMemberById(toId).queue(toMember -> {
            try {
                InventoryManager.transfer(guildId, fromId, toMember.getId(), finalTransfers);
            } catch (InventoryManager.TransferError te) {
                event.replyEmbeds(EmbedFactory.build("❌ Transfer fehlgeschlagen", te.getMessage()))
                    .setEphemeral(true).queue();
                return;
            }

            // Zusammenfassung
            StringBuilder sb = new StringBuilder();
            for (InventoryManager.Item t : finalTransfers) {
                sb.append("• **").append(t.name).append("** × ").append(t.quantity).append("\n");
            }
            event.replyEmbeds(EmbedFactory.build("✅ Items übergeben",
                "Du hast folgende Items an **" + toMember.getEffectiveName() + "** übergeben:\n\n" + sb))
                .setEphemeral(true).queue();

            // Empfänger benachrichtigen (DM)
            BotLogger.tryDm(toMember.getUser(), EmbedFactory.build(
                "📦 Items erhalten",
                "**" + (event.getMember() != null ? event.getMember().getEffectiveName() : event.getUser().getName()) +
                "** hat dir folgende Items übergeben:\n\n" + sb));

        }, err -> event.replyEmbeds(EmbedFactory.build("❌ Nicht gefunden",
            "Kein Mitglied mit dieser ID auf dem Server gefunden."))
            .setEphemeral(true).queue());
    }
}
