package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.EntitySelectInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.StringSelectInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.EntitySelectMenu;
import net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu;
import net.dv8tion.jda.api.interactions.components.text.TextInput;
import net.dv8tion.jda.api.interactions.components.text.TextInputStyle;
import net.dv8tion.jda.api.interactions.modals.Modal;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

public class RucksackListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(RucksackListener.class);

    // ── Buttons ───────────────────────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        String id = event.getComponentId();

        // Paginierung: rucksack-own-page:<userId>:<page>
        if (id.startsWith("rucksack-own-page:")) {
            handleOwnRucksackPage(event);
            return;
        }

        // Paginierung für fremde Rucksäcke: rucksack-other-page:<userId>:<page>
        if (id.startsWith("rucksack-other-page:")) {
            handleOtherRucksackPage(event);
            return;
        }

        if (id.startsWith("rucksack-unhide-prompt:")) {
            handleUnhidePrompt(event);
            return;
        }

        switch (id) {
            case "rucksack-open"     -> handleOwnRucksack(event);
            case "rucksack-other"    -> handleOtherRucksackPrompt(event);
            case "rucksack-transfer" -> handleTransferUserPrompt(event);
        }
    }

    /** Eigenen Rucksack — Seite 1, ephemeral, mit "Item Übergeben"-Button und optional "Aus Versteck holen". */
    private void handleOwnRucksack(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();
        String name    = event.getMember() != null
            ? event.getMember().getEffectiveName()
            : event.getUser().getName();

        sendOwnRucksackPage(event, guildId, userId, name, 1, false);
    }

    /** Seite eines eigenen Rucksacks anzeigen (über Paginierungs-Button). */
    private void handleOwnRucksackPage(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String[] parts = event.getComponentId().split(":");
        if (parts.length < 3) return;
        String userId  = parts[1];
        int page       = Integer.parseInt(parts[2]);
        String guildId = event.getGuild().getId();
        String name    = event.getMember() != null
            ? event.getMember().getEffectiveName()
            : event.getUser().getName();

        // Prüfen ob der Button dem richtigen User gehört
        if (!userId.equals(event.getUser().getId())) {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler", "Diese Seite gehört nicht dir."))
                .setEphemeral(true).queue();
            return;
        }

        sendOwnRucksackPage(event, guildId, userId, name, page, true);
    }

    /** Hilfsmethode: Eigenen Rucksack mit Page-Buttons senden. */
    private void sendOwnRucksackPage(ButtonInteractionEvent event, String guildId, String userId,
                                      String name, int page, boolean edit) {
        var result = InventoryManager.buildEmbedWithHiddenPaged(guildId, userId, name, page);

        var hiddenItems = InventoryManager.getHiddenItems(guildId, userId);
        boolean hasHidden = !hiddenItems.isEmpty();

        // ActionRow 1: Aktionen
        List<Button> actionButtons = new ArrayList<>();
        actionButtons.add(Button.primary("rucksack-transfer", "📦 Item Übergeben"));
        if (hasHidden) {
            actionButtons.add(Button.secondary("rucksack-unhide-prompt:" + userId,
                "🗝️ Aus Versteck holen (" + hiddenItems.size() + ")"));
        }
        ActionRow actionRow = ActionRow.of(actionButtons);

        // ActionRow 2: Paginierung (nur bei mehreren Seiten)
        ActionRow pageRow = buildPageRow("rucksack-own-page", userId, result.totalPages(), result.currentPage());

        if (edit) {
            // Bestehende Nachricht bearbeiten
            event.editMessageEmbeds(result.embed())
                .setComponents(pageRow != null ? List.of(actionRow, pageRow) : List.of(actionRow))
                .queue();
        } else {
            // Neue Nachricht
            event.replyEmbeds(result.embed())
                .addComponents(pageRow != null ? List.of(actionRow, pageRow) : List.of(actionRow))
                .setEphemeral(true)
                .queue();
        }
    }

    /** Baut die Paginierungs-Buttons (← / Seite / →). */
    private ActionRow buildPageRow(String prefix, String userId, int totalPages, int currentPage) {
        if (totalPages <= 1) return null;
        List<Button> pageBtns = new ArrayList<>();
        if (currentPage > 1) {
            pageBtns.add(Button.primary(prefix + ":" + userId + ":" + (currentPage - 1), "◀ Zurück"));
        }
        pageBtns.add(Button.secondary(prefix + ":" + userId + ":current", "📄 " + currentPage + "/" + totalPages).asDisabled());
        if (currentPage < totalPages) {
            pageBtns.add(Button.primary(prefix + ":" + userId + ":" + (currentPage + 1), "Weiter ▶"));
        }
        return ActionRow.of(pageBtns);
    }

    /** "Aus Versteck holen" — öffnet eine Auswahl mit den aktuell versteckten Items. */
    private void handleUnhidePrompt(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String[] parts = event.getComponentId().split(":", 2);
        String userId  = parts.length > 1 ? parts[1] : event.getUser().getId();

        if (!userId.equals(event.getUser().getId())) {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler",
                "Du kannst nur deine eigenen Items aus dem Versteck holen."))
                .setEphemeral(true).queue();
            return;
        }

        List<InventoryManager.Item> hidden = InventoryManager.getHiddenItems(guildId, userId);
        if (hidden.isEmpty()) {
            event.replyEmbeds(EmbedFactory.build("🗝️ Kein Versteck",
                "Du hast aktuell keine versteckten Items."))
                .setEphemeral(true).queue();
            return;
        }

        StringSelectMenu.Builder menu = StringSelectMenu.create("rucksack-unhide-select:" + userId)
            .setPlaceholder("Items auswählen, die wieder sichtbar sein sollen…")
            .setMinValues(1)
            .setMaxValues(Math.min(hidden.size(), 25));
        for (InventoryManager.Item it : hidden) {
            menu.addOption(it.name + " × " + it.quantity, it.name);
        }

        event.replyEmbeds(EmbedFactory.build("🗝️ Aus Versteck holen",
            "Wähle unten die Items, die wieder im Inventar normal erscheinen sollen."))
            .addActionRow(menu.build())
            .setEphemeral(true).queue();
    }

    /** "Anderen Rucksack Öffnen" → User-Suchleiste (EntitySelectMenu). */
    private void handleOtherRucksackPrompt(ButtonInteractionEvent event) {
        EntitySelectMenu menu = EntitySelectMenu
            .create("rucksack-search-select", EntitySelectMenu.SelectTarget.USER)
            .setPlaceholder("Spieler suchen und auswählen…")
            .setMinValues(1).setMaxValues(1)
            .build();

        event.replyEmbeds(EmbedFactory.build("🔍 Anderen Rucksack öffnen",
            "Wähle einen Spieler aus der Liste aus."))
            .addActionRow(menu)
            .setEphemeral(true)
            .queue();
    }

    /** "Item Übergeben" → User-Suchleiste für Empfänger. */
    private void handleTransferUserPrompt(ButtonInteractionEvent event) {
        EntitySelectMenu menu = EntitySelectMenu
            .create("rucksack-transfer-select", EntitySelectMenu.SelectTarget.USER)
            .setPlaceholder("Empfänger suchen und auswählen…")
            .setMinValues(1).setMaxValues(1)
            .build();

        event.replyEmbeds(EmbedFactory.build("📦 Item Übergeben",
            "Wähle zuerst den Empfänger aus."))
            .addActionRow(menu)
            .setEphemeral(true)
            .queue();
    }

    // ── Entity-Select ─────────────────────────────────────────────────────────

    @Override
    public void onEntitySelectInteraction(EntitySelectInteractionEvent event) {
        String id = event.getComponentId();

        if (id.equals("rucksack-search-select")) {
            handleOtherRucksackView(event);
        } else if (id.equals("rucksack-transfer-select")) {
            handleTransferItemsPrompt(event);
        }
    }

    // ── String-Select (Aus-Versteck-Auswahl) ───────────────────────────────────

    @Override
    public void onStringSelectInteraction(StringSelectInteractionEvent event) {
        String id = event.getComponentId();
        if (id.startsWith("rucksack-unhide-select:")) {
            handleUnhideExecute(event);
        }
        // IDs der CommandListener-Hierarchie (lizenzen/verbrauchen/verstecken) laufen separat
    }

    /** Auswahl-Ende: setze hidden=false für die gewählten Items, KEIN Info-Embed im Kanal. */
    private void handleUnhideExecute(StringSelectInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String[] parts = event.getComponentId().split(":", 2);
        String userId  = parts.length > 1 ? parts[1] : event.getUser().getId();

        if (!userId.equals(event.getUser().getId())) {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler",
                "Du kannst nur deine eigenen Items aus dem Versteck holen."))
                .setEphemeral(true).queue();
            return;
        }

        List<String> picked = event.getValues();
        StringBuilder sb = new StringBuilder();
        for (String name : picked) {
            InventoryManager.setHidden(guildId, userId, name, false);
            sb.append("• **").append(name).append("**\\n");
        }

        event.replyEmbeds(EmbedFactory.build(
            "🗝️ Wieder im Inventar",
            "Folgende Items sind wieder normal sichtbar:\\n\\n" + sb))
            .setEphemeral(true).queue();
    }

    /** Nach Spieler-Auswahl: Fremden Rucksack anzeigen (Seite 1, ohne Verstecktes). */
    private void handleOtherRucksackView(EntitySelectInteractionEvent event) {
        if (event.getGuild() == null) return;
        List<Member> members = event.getMentions().getMembers();
        if (members.isEmpty()) {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler", "Kein Mitglied ausgewählt."))
                .setEphemeral(true).queue();
            return;
        }
        Member target = members.get(0);
        String guildId = event.getGuild().getId();

        var result = InventoryManager.buildEmbedPaged(guildId, target.getId(), target.getEffectiveName(), 1);

        if (result.totalPages() > 1) {
            ActionRow pageRow = buildPageRow("rucksack-other-page", target.getId(),
                result.totalPages(), result.currentPage());
            event.replyEmbeds(result.embed())
                .addComponents(pageRow)
                .setEphemeral(true)
                .queue();
        } else {
            event.replyEmbeds(result.embed())
                .setEphemeral(true)
                .queue();
        }
    }

    /** Paginierung für fremde Rucksäcke. */
    private void handleOtherRucksackPage(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String[] parts = event.getComponentId().split(":");
        if (parts.length < 3) return;
        String targetId = parts[1];
        int page        = Integer.parseInt(parts[2]);
        String guildId  = event.getGuild().getId();

        // Ziel-Member holen
        event.getGuild().retrieveMemberById(targetId).queue(target -> {
            var result = InventoryManager.buildEmbedPaged(guildId, target.getId(), target.getEffectiveName(), page);
            ActionRow pageRow = buildPageRow("rucksack-other-page", target.getId(),
                result.totalPages(), result.currentPage());

            event.editMessageEmbeds(result.embed())
                .setComponents(pageRow != null ? List.of(pageRow) : List.of())
                .queue();
        }, err -> {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler", "Spieler nicht mehr auf dem Server."))
                .setEphemeral(true).queue();
        });
    }

    /** Nach Empfänger-Auswahl: Modal mit Items-Feld öffnen. */
    private void handleTransferItemsPrompt(EntitySelectInteractionEvent event) {
        if (event.getGuild() == null) return;
        List<Member> members = event.getMentions().getMembers();
        if (members.isEmpty()) {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler", "Kein Mitglied ausgewählt."))
                .setEphemeral(true).queue();
            return;
        }
        Member target = members.get(0);

        if (target.getId().equals(event.getUser().getId())) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültig",
                "Du kannst dir selbst keine Items übergeben."))
                .setEphemeral(true).queue();
            return;
        }

        // Modal mit Empfänger-ID im Modal-ID encodiert
        Modal modal = Modal.create("rucksack-transfer-items:" + target.getId(), "Items übergeben an " + target.getEffectiveName())
            .addComponents(ActionRow.of(
                TextInput.create("items", "Items (Format: ItemName: Menge)", TextInputStyle.PARAGRAPH)
                    .setPlaceholder("Bargeld: 500\\nWaffe: 1\\nDrogen: 10")
                    .setRequired(true)
                    .build()
            )).build();
        event.replyModal(modal).queue();
    }

    // ── Modal (Items-Eingabe nach User-Select) ────────────────────────────────

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        String modalId = event.getModalId();
        if (modalId.startsWith("rucksack-transfer-items:")) {
            String targetId = modalId.substring("rucksack-transfer-items:".length());
            handleTransferExecute(event, targetId);
        }
    }

    private void handleTransferExecute(ModalInteractionEvent event, String toId) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String fromId  = event.getUser().getId();
        String itemsRaw = event.getValue("items") == null ? ""
            : event.getValue("items").getAsString().trim().replace("\\n", ",");

        List<InventoryManager.Item> transfers;
        try { transfers = InventoryManager.parseTransferInput(itemsRaw); }
        catch (InventoryManager.TransferError te) {
            event.replyEmbeds(EmbedFactory.build("❌ Format-Fehler", te.getMessage()))
                .setEphemeral(true).queue();
            return;
        }

        final List<InventoryManager.Item> finalTransfers = transfers;

        event.getGuild().retrieveMemberById(toId).queue(toMember -> {
            try {
                InventoryManager.transfer(guildId, fromId, toMember.getId(), finalTransfers);
            } catch (InventoryManager.TransferError te) {
                event.replyEmbeds(EmbedFactory.build("❌ Transfer fehlgeschlagen", te.getMessage()))
                    .setEphemeral(true).queue();
                return;
            }

            StringBuilder sb = new StringBuilder();
            for (InventoryManager.Item t : finalTransfers)
                sb.append("• **").append(t.name).append("** × ").append(t.quantity).append("\\n");

            event.replyEmbeds(EmbedFactory.build("✅ Items übergeben",
                "Du hast folgende Items an **" + toMember.getEffectiveName() + "** übergeben:\\n\\n" + sb))
                .setEphemeral(true).queue();

            BotLogger.tryDm(toMember.getUser(), EmbedFactory.build(
                "📦 Items erhalten",
                "**" + (event.getMember() != null ? event.getMember().getEffectiveName() : event.getUser().getName()) +
                "** hat dir folgende Items übergeben:\\n\\n" + sb));

        }, err -> event.replyEmbeds(EmbedFactory.build("❌ Nicht gefunden",
            "Der ausgewählte Spieler ist nicht mehr auf dem Server."))
            .setEphemeral(true).queue());
    }
}
