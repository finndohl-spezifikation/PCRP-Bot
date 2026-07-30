package de.pcrp.bot.listeners;

import de.pcrp.bot.common.EmbedFactory;
import de.pcrp.bot.common.LoggingConfig;
import de.pcrp.bot.common.PremiumMotorsportManager;
import de.pcrp.bot.common.PanelHelper;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.entities.emoji.Emoji;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.EntitySelectInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.EntitySelectMenu;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

public class GarageListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(GarageListener.class);
    private static final int PER_PAGE = 10;

    // ── Panel posten ──────────────────────────────────────────────────────────

    /** Postet das Garage-Panel-Embed im Garage-Kanal (einmalig beim Bot-Start). */
    public static void postPanel(Guild guild) {
        String key = "panel-garage-v1-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(LoggingConfig.GARAGE_CHANNEL_ID);
        if (ch == null) { log.warn("[Garage] Panel-Kanal nicht gefunden."); return; }
        PanelHelper.post(ch, key, "🚘 Premium Deluxe Motorsport — Garage",
            () -> sendPanel(ch, key));
    }

    private static void sendPanel(TextChannel ch, String key) {
        ch.sendMessageEmbeds(
            EmbedFactory.create()
                .setTitle("🚘 Premium Deluxe Motorsport — Garage")
                .setDescription(
                    "Hier kannst du deine gekauften Fahrzeuge einsehen und verwalten.\\n\\n" +
                    "Klicke auf **🚘 Garage öffnen**, um deine aktuellen Fahrzeuge anzuzeigen.\\n\\n" +
                    "**Fahrzeuge übergeben:** Wähle ein Fahrzeug aus deiner Garage und gib es an einen anderen Spieler weiter.\\n\\n" +
                    "---\\n" +
                    "Fahrzeuge, die du über die Webseite kaufst, landen automatisch in deiner Garage – " +
                    "hier auf Discord.")
                .build()
        ).addActionRow(
            Button.primary("garage-open", "🚘 Garage öffnen")
        ).queue(
            msg -> PanelHelper.onSent(key, msg.getId()),
            err -> { log.error("[Garage] Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); }
        );
    }

    // ── Button-Interaktion ────────────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        String id = event.getComponentId();

        // Paginierung: garage-page:<userId>:<page>
        if (id.startsWith("garage-page:")) {
            handleGaragePage(event);
            return;
        }

        // Zurück zur Übersicht: garage-back:<userId>:<page>
        if (id.startsWith("garage-back:")) {
            handleGarageBack(event);
            return;
        }

        switch (id) {
            case "garage-open"          -> handleGarageOpen(event);
            case "garage-transfer"      -> handleTransferPrompt(event);
        }
    }

    /** 🚘 Garage öffnen — zeigt alle Fahrzeuge des Users als Discord-Embed. */
    private void handleGarageOpen(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();
        String name    = event.getMember() != null
            ? event.getMember().getEffectiveName()
            : event.getUser().getName();

        sendGarageView(event, guildId, userId, name, 1, false);
    }

    /** Paginierung für die Garage-Ansicht. */
    private void handleGaragePage(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String[] parts = event.getComponentId().split(":");
        if (parts.length < 3) return;
        String targetId = parts[1];
        int page        = Integer.parseInt(parts[2]);
        String guildId  = event.getGuild().getId();

        String name = targetId.equals(event.getUser().getId()) && event.getMember() != null
            ? event.getMember().getEffectiveName()
            : "Spieler";

        // Wenn es ein fremder Transfer-Empfänger ist, holen wir den Namen
        if (!targetId.equals(event.getUser().getId())) {
            String finalName = name;
            event.getGuild().retrieveMemberById(targetId).queue(
                member -> sendGarageView(event, guildId, targetId, member.getEffectiveName(), page, true),
                err -> sendGarageView(event, guildId, targetId, finalName, page, true)
            );
            return;
        }

        sendGarageView(event, guildId, targetId, name, page, true);
    }

    /** Hilfsmethode: Garage-Embed + Buttons senden/bearbeiten. */
    private void sendGarageView(ButtonInteractionEvent event, String guildId, String userId,
                                 String displayName, int page, boolean edit) {
        List<PremiumMotorsportManager.GarageEntry> garage = PremiumMotorsportManager.getGarage(guildId, userId);

        if (garage.isEmpty()) {
            if (edit) {
                event.editMessageEmbeds(EmbedFactory.build("🚘 Leere Garage",
                    "Du hast aktuell keine Fahrzeuge in deiner Garage.\\n\\n" +
                    "Besuche **Premium Deluxe Motorsport** auf der Webseite, um Fahrzeuge zu kaufen."))
                    .setComponents()
                    .queue();
            } else {
                event.replyEmbeds(EmbedFactory.build("🚘 Leere Garage",
                    "Du hast aktuell keine Fahrzeuge in deiner Garage.\\n\\n" +
                    "Besuche **Premium Deluxe Motorsport** auf der Webseite, um Fahrzeuge zu kaufen."))
                    .setEphemeral(true).queue();
            }
            return;
        }

        int totalItems = garage.size();
        int totalPages = Math.max(1, (int) Math.ceil((double) totalItems / PER_PAGE));
        if (page < 1) page = 1;
        if (page > totalPages) page = totalPages;

        int start = (page - 1) * PER_PAGE;
        int end = Math.min(start + PER_PAGE, garage.size());

        StringBuilder sb = new StringBuilder();
        for (int i = start; i < end; i++) {
            PremiumMotorsportManager.GarageEntry entry = garage.get(i);
            String catEmoji = PremiumMotorsportManager.categoryEmojis()
                .getOrDefault(entry.category, "🚘");
            sb.append(catEmoji).append(" **").append(entry.name).append("**\\n");
            sb.append("  └ Kategorie: ").append(entry.category).append(" · Bezahlt: ")
                .append(String.format("%,d", entry.pricePaid)).append("$\\n");
        }

        var embed = EmbedFactory.create()
            .setTitle("🚘 Garage — " + displayName)
            .setDescription(sb.toString());

        if (totalPages > 1) {
            embed.setFooter("Seite " + page + " von " + totalPages + " · " + totalItems + " Fahrzeuge");
        }

        // Buttons
        List<Button> buttons = new ArrayList<>();
        if (page > 1) {
            buttons.add(Button.primary("garage-page:" + userId + ":" + (page - 1), "◀ Zurück"));
        }
        buttons.add(Button.secondary("garage-page:" + userId + ":current", "📄 " + page + "/" + totalPages).asDisabled());
        if (page < totalPages) {
            buttons.add(Button.primary("garage-page:" + userId + ":" + (page + 1), "Weiter ▶"));
        }
        buttons.add(Button.success("garage-transfer", "📦 Fahrzeug übergeben"));

        if (edit) {
            event.editMessageEmbeds(embed.build())
                .setComponents(ActionRow.of(buttons))
                .queue();
        } else {
            event.replyEmbeds(embed.build())
                .addComponents(ActionRow.of(buttons))
                .setEphemeral(true)
                .queue();
        }
    }

    /** 📦 Fahrzeug übergeben — Auswahl des Fahrzeugs via EntitySelect (User-Auswahl). */
    private void handleTransferPrompt(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();

        List<PremiumMotorsportManager.GarageEntry> garage = PremiumMotorsportManager.getGarage(guildId, userId);
        if (garage.isEmpty()) {
            event.replyEmbeds(EmbedFactory.build("❌ Keine Fahrzeuge",
                "Du hast keine Fahrzeuge in deiner Garage, die du übergeben könntest."))
                .setEphemeral(true).queue();
            return;
        }

        // User-Auswahl für den Empfänger
        EntitySelectMenu menu = EntitySelectMenu
            .create("garage-transfer-user-select", EntitySelectMenu.SelectTarget.USER)
            .setPlaceholder("Empfänger auswählen…")
            .setMinValues(1).setMaxValues(1)
            .build();

        event.replyEmbeds(EmbedFactory.build("📦 Fahrzeug übergeben",
            "Wähle zuerst den **Empfänger** aus. Danach wählst du das Fahrzeug aus deiner Garage."))
            .addActionRow(menu)
            .setEphemeral(true).queue();
    }

    @Override
    public void onEntitySelectInteraction(EntitySelectInteractionEvent event) {
        String id = event.getComponentId();

        if (id.equals("garage-transfer-user-select")) {
            handleTransferVehicleSelect(event);
        }
    }

    /** Nach Empfänger-Auswahl: Fahrzeug-Auswahl via select menu. */
    private void handleTransferVehicleSelect(EntitySelectInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();

        var members = event.getMentions().getMembers();
        if (members.isEmpty()) {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler", "Kein Mitglied ausgewählt."))
                .setEphemeral(true).queue();
            return;
        }
        String toId = members.get(0).getId();

        if (toId.equals(userId)) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültig",
                "Du kannst dir selbst keine Fahrzeuge übergeben."))
                .setEphemeral(true).queue();
            return;
        }

        List<PremiumMotorsportManager.GarageEntry> garage = PremiumMotorsportManager.getGarage(guildId, userId);
        if (garage.isEmpty()) {
            event.replyEmbeds(EmbedFactory.build("❌ Keine Fahrzeuge",
                "Du hast keine Fahrzeuge in deiner Garage."))
                .setEphemeral(true).queue();
            return;
        }

        // Select-Menü mit Fahrzeugen (Discord-Limit: max 25 Optionen)
        net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu.Builder menu =
            net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu
                .create("garage-transfer-exec:" + toId)
                .setPlaceholder("Fahrzeug auswählen…")
                .setMinValues(1).setMaxValues(1);

        int count = 0;
        for (PremiumMotorsportManager.GarageEntry entry : garage) {
            if (count >= 25) break;
            String label = entry.name.length() > 100 ? entry.name.substring(0, 97) + "…" : entry.name;
            menu.addOption(label, entry.vin,
                entry.category + " · " + String.format("%,d", entry.pricePaid) + "$",
                Emoji.fromUnicode("🚘"));
            count++;
        }

        event.replyEmbeds(EmbedFactory.build("📦 Fahrzeug übergeben",
            "Wähle das Fahrzeug aus, das du an **" + members.get(0).getEffectiveName() + "** übergeben möchtest."))
            .addActionRow(menu.build())
            .setEphemeral(true).queue();
    }

    @Override
    public void onStringSelectInteraction(net.dv8tion.jda.api.events.interaction.component.StringSelectInteractionEvent event) {
        String id = event.getComponentId();
        if (id.startsWith("garage-transfer-exec:")) {
            handleTransferExecute(event);
        }
    }

    /** Führt die Fahrzeug-Übergabe aus. */
    private void handleTransferExecute(net.dv8tion.jda.api.events.interaction.component.StringSelectInteractionEvent event) {
        if (event.getGuild() == null) return;
        String guildId = event.getGuild().getId();
        String fromId  = event.getUser().getId();
        String[] parts = event.getComponentId().split(":", 2);
        String toId    = parts.length > 1 ? parts[1] : "";
        String vin     = event.getValues().isEmpty() ? "" : event.getValues().get(0);

        if (vin.isEmpty() || toId.isEmpty()) {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler", "Ungültige Auswahl."))
                .setEphemeral(true).queue();
            return;
        }

        // Empfänger-Namen holen
        event.getGuild().retrieveMemberById(toId).queue(toMember -> {
            String error = PremiumMotorsportManager.transferGarageVehicle(guildId, fromId, toMember.getId(), vin);
            if (error != null) {
                event.replyEmbeds(EmbedFactory.build("❌ Übergabe fehlgeschlagen", error))
                    .setEphemeral(true).queue();
                return;
            }

            // Fahrzeugname aus Garage holen
            String vehicleName = vin;
            for (var entry : PremiumMotorsportManager.getGarage(guildId, fromId)) {
                if (entry.vin.equals(vin)) vehicleName = entry.name;
            }

            event.replyEmbeds(EmbedFactory.build("✅ Fahrzeug übergeben",
                "Du hast **" + vehicleName + "** erfolgreich an **" + toMember.getEffectiveName() + "** übergeben.\\n\\n" +
                "Das Fahrzeug befindet sich jetzt in der Garage des Empfängers."))
                .setEphemeral(true).queue();

        }, err -> event.replyEmbeds(EmbedFactory.build("❌ Fehler",
            "Empfänger nicht gefunden.")).setEphemeral(true).queue());
    }

    /** Zurück zur Übersicht (nach Fahrzeug-Übergabe-Abbruch — wird aktuell nicht verwendet, aber vorbereitet). */
    private void handleGarageBack(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String[] parts = event.getComponentId().split(":");
        if (parts.length < 3) return;
        String userId = parts[1];
        int page      = Integer.parseInt(parts[2]);
        String guildId = event.getGuild().getId();
        String name = userId.equals(event.getUser().getId()) && event.getMember() != null
            ? event.getMember().getEffectiveName()
            : "Spieler";

        sendGarageView(event, guildId, userId, name, page, true);
    }

}
