package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.Permission;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.command.SlashCommandInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.commands.OptionMapping;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.text.TextInput;
import net.dv8tion.jda.api.interactions.components.text.TextInputStyle;
import net.dv8tion.jda.api.interactions.modals.Modal;

/**
 * Behandelt den /bargeld-Befehl und die zugehörigen Bargeld-Abnehmen-Buttons.
 * Nur erlaubt im Bargeld-Kanal (1529636557038817361).
 */
public class BargeldListener extends ListenerAdapter {

    private static final long BARGELD_CHANNEL_ID = 1529636557038817361L;

    // ── Slash-Command ─────────────────────────────────────────────────────────

    @Override
    public void onSlashCommandInteraction(SlashCommandInteractionEvent event) {
        if (!"bargeld".equals(event.getName())) return;
        if (event.getGuild() == null) return;

        // Kanal-Beschränkung
        if (event.getChannel().getIdLong() != BARGELD_CHANNEL_ID) {
            event.replyEmbeds(EmbedFactory.build("❌ Falscher Kanal",
                "Dieser Befehl ist nur im <#" + BARGELD_CHANNEL_ID + "> erlaubt."))
                .setEphemeral(true).queue();
            return;
        }

        Member target = event.getOption("mitglied", OptionMapping::getAsMember);

        if (target == null) {
            // Eigener Barbestand
            long cash = BargeldManager.get(event.getGuild().getId(), event.getUser().getId());
            event.replyEmbeds(EmbedFactory.build(
                "💵 Dein Barbestand",
                "**Bargeld:** " + BargeldManager.format(cash)))
                .setEphemeral(true).queue();
        } else {
            // Barbestand eines anderen (nur mit MODERATE_MEMBERS)
            if (!event.getMember().hasPermission(Permission.MODERATE_MEMBERS)) {
                event.replyEmbeds(EmbedFactory.build("❌ Keine Berechtigung",
                    "Du hast keine Berechtigung, den Barbestand anderer Spieler einzusehen."))
                    .setEphemeral(true).queue();
                return;
            }
            long cash = BargeldManager.get(event.getGuild().getId(), target.getId());
            event.replyEmbeds(EmbedFactory.build(
                "💵 Barbestand — " + target.getEffectiveName(),
                "**Bargeld:** " + BargeldManager.format(cash)))
                .addComponents(ActionRow.of(
                    Button.danger("bargeld-take-" + target.getId(),
                        "💸 Bargeld abnehmen von " + target.getEffectiveName())))
                .setEphemeral(true).queue();
        }
    }

    // ── Button: Bargeld abnehmen ──────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String cid = event.getComponentId();
        if (!cid.startsWith("bargeld-take-")) return;
        if (!event.getMember().hasPermission(Permission.MODERATE_MEMBERS)) {
            event.replyEmbeds(EmbedFactory.build("❌ Keine Berechtigung",
                "Du hast keine Berechtigung, Bargeld abzunehmen."))
                .setEphemeral(true).queue();
            return;
        }

        String targetId = cid.substring("bargeld-take-".length());
        Member target   = event.getGuild().getMemberById(targetId);
        String name     = target != null ? target.getEffectiveName() : targetId;
        long   cash     = BargeldManager.get(event.getGuild().getId(), targetId);

        Modal modal = Modal.create("bargeld-modal-take-" + targetId,
                "💸 Bargeld abnehmen von " + name)
            .addComponents(ActionRow.of(
                TextInput.create("betrag", "Betrag in $ (Verfügbar: " + BargeldManager.format(cash) + ")",
                        TextInputStyle.SHORT)
                    .setPlaceholder("z. B. 500")
                    .setMinLength(1).setMaxLength(12)
                    .setRequired(true).build()))
            .build();
        event.replyModal(modal).queue();
    }

    // ── Modal: Betrag bestätigen ──────────────────────────────────────────────

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        if (event.getGuild() == null) return;
        String mid = event.getModalId();
        if (!mid.startsWith("bargeld-modal-take-")) return;

        if (!event.getMember().hasPermission(Permission.MODERATE_MEMBERS)) {
            event.replyEmbeds(EmbedFactory.build("❌ Keine Berechtigung",
                "Du hast keine Berechtigung.")).setEphemeral(true).queue(); return;
        }

        String targetId  = mid.substring("bargeld-modal-take-".length());
        String adminId   = event.getUser().getId();
        String guildId   = event.getGuild().getId();
        Member target    = event.getGuild().getMemberById(targetId);
        String targetName = target != null ? target.getEffectiveName() : targetId;

        long amount;
        try { amount = Long.parseLong(event.getValue("betrag").getAsString().trim().replace(".", "").replace(",", "")); }
        catch (NumberFormatException e) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültiger Betrag",
                "Bitte gib eine gültige Zahl ein.")).setEphemeral(true).queue(); return;
        }
        if (amount <= 0) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültiger Betrag",
                "Der Betrag muss größer als 0 sein.")).setEphemeral(true).queue(); return;
        }

        String err = BargeldManager.transfer(guildId, targetId, adminId, amount);
        if (err != null) {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler", err)).setEphemeral(true).queue(); return;
        }

        String adminName = event.getMember() != null ? event.getMember().getEffectiveName() : event.getUser().getName();
        event.replyEmbeds(EmbedFactory.build("✅ Bargeld abgenommen",
            "**" + BargeldManager.format(amount) + "** wurden von **" + targetName
            + "** auf deinen Barbestand übertragen.\n\n"
            + "💵 Dein neuer Barbestand: **" + BargeldManager.format(BargeldManager.get(guildId, adminId)) + "**"))
            .setEphemeral(true).queue();

        // Log
        BotLogger.logMoney(event.getGuild(), "💸 Bargeld abgenommen",
            "**Admin:** " + event.getUser().getAsMention() + "\n" +
            "**Von:** " + targetName + "\n" +
            "**Betrag:** " + BargeldManager.format(amount));

        // DM an Ziel
        if (target != null) {
            BotLogger.tryDm(target.getUser(), EmbedFactory.build(
                "💸 Bargeld abgenommen",
                "**" + adminName + "** hat **" + BargeldManager.format(amount)
                + "** Bargeld von dir abgenommen."));
        }
    }
}
