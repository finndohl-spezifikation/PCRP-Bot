package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.MessageEmbed;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
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

/** Online-Banking Panel und Transaktionen (Einzahlen, Auszahlen, Überweisen). */
public class BankListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(BankListener.class);

    // ── Button-Handler ────────────────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String cid     = event.getComponentId();
        String userId  = event.getUser().getId();
        String guildId = event.getGuild().getId();

        switch (cid) {
            case "bank-open" -> {
                event.replyEmbeds(buildBankEmbed(guildId, userId))
                    .addComponents(bankRow())
                    .setEphemeral(true).queue();
            }
            case "bank-btn-deposit" -> {
                Modal modal = Modal.create("bank-modal-deposit", "💳 Einzahlen")
                    .addComponents(ActionRow.of(
                        TextInput.create("betrag", "Betrag in $", TextInputStyle.SHORT)
                            .setPlaceholder("z. B. 5000")
                            .setMinLength(1).setMaxLength(12)
                            .setRequired(true).build()))
                    .build();
                event.replyModal(modal).queue();
            }
            case "bank-btn-withdraw" -> {
                Modal modal = Modal.create("bank-modal-withdraw", "💵 Auszahlen")
                    .addComponents(ActionRow.of(
                        TextInput.create("betrag", "Betrag in $", TextInputStyle.SHORT)
                            .setPlaceholder("z. B. 5000")
                            .setMinLength(1).setMaxLength(12)
                            .setRequired(true).build()))
                    .build();
                event.replyModal(modal).queue();
            }
            case "bank-btn-transfer" -> {
                Modal modal = Modal.create("bank-modal-transfer", "📤 Überweisen")
                    .addComponents(
                        ActionRow.of(TextInput.create("empfaenger", "Empfänger (Discord-Benutzername)", TextInputStyle.SHORT)
                            .setPlaceholder("z. B. max_mustermann")
                            .setMinLength(1).setMaxLength(40)
                            .setRequired(true).build()),
                        ActionRow.of(TextInput.create("betrag", "Betrag in $", TextInputStyle.SHORT)
                            .setPlaceholder("z. B. 5000")
                            .setMinLength(1).setMaxLength(12)
                            .setRequired(true).build()))
                    .build();
                event.replyModal(modal).queue();
            }
        }
    }

    // ── Modal-Handler ─────────────────────────────────────────────────────────

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        if (event.getGuild() == null) return;
        String mid     = event.getModalId();
        String userId  = event.getUser().getId();
        String guildId = event.getGuild().getId();

        switch (mid) {
            case "bank-modal-deposit"  -> handleDeposit(event, guildId, userId);
            case "bank-modal-withdraw" -> handleWithdraw(event, guildId, userId);
            case "bank-modal-transfer" -> handleTransfer(event, guildId, userId);
        }
    }

    // ── Einzahlen ─────────────────────────────────────────────────────────────

    private void handleDeposit(ModalInteractionEvent event, String guildId, String userId) {
        long amount = parseAmount(event.getValue("betrag").getAsString());
        if (amount <= 0) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültiger Betrag",
                "Bitte gib einen gültigen Betrag ein (z. B. `5000`)."))
                .setEphemeral(true).queue(); return;
        }
        String err = BankManager.deposit(guildId, userId, amount);
        if (err != null) {
            event.replyEmbeds(EmbedFactory.build("❌ Einzahlung fehlgeschlagen", err))
                .setEphemeral(true).queue(); return;
        }
        event.replyEmbeds(buildResultEmbed(
            "✅ Einzahlung erfolgreich",
            "**+" + BankManager.formatAmount(amount) + "** wurden auf dein Konto eingezahlt.",
            guildId, userId))
            .addComponents(bankRow()).setEphemeral(true).queue();
        log.info("[Bank] Einzahlung {} : {}$", event.getUser().getAsTag(), amount);
    }

    // ── Auszahlen ─────────────────────────────────────────────────────────────

    private void handleWithdraw(ModalInteractionEvent event, String guildId, String userId) {
        long amount = parseAmount(event.getValue("betrag").getAsString());
        if (amount <= 0) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültiger Betrag",
                "Bitte gib einen gültigen Betrag ein (z. B. `5000`)."))
                .setEphemeral(true).queue(); return;
        }
        String err = BankManager.withdraw(guildId, userId, amount);
        if (err != null) {
            event.replyEmbeds(EmbedFactory.build("❌ Auszahlung fehlgeschlagen", err))
                .setEphemeral(true).queue(); return;
        }
        event.replyEmbeds(buildResultEmbed(
            "✅ Auszahlung erfolgreich",
            "**-" + BankManager.formatAmount(amount) + "** wurden als Bargeld ausgezahlt.",
            guildId, userId))
            .addComponents(bankRow()).setEphemeral(true).queue();
        log.info("[Bank] Auszahlung {} : {}$", event.getUser().getAsTag(), amount);
    }

    // ── Überweisen ────────────────────────────────────────────────────────────

    private void handleTransfer(ModalInteractionEvent event, String guildId, String userId) {
        String empfaengerName = event.getValue("empfaenger").getAsString().trim();
        long   amount         = parseAmount(event.getValue("betrag").getAsString());
        if (amount <= 0) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültiger Betrag",
                "Bitte gib einen gültigen Betrag ein (z. B. `5000`)."))
                .setEphemeral(true).queue(); return;
        }
        net.dv8tion.jda.api.entities.Member receiver = BotContext.findMemberByUsername(empfaengerName);
        if (receiver == null) {
            event.replyEmbeds(EmbedFactory.build("❌ Empfänger nicht gefunden",
                "Kein Mitglied mit dem Namen **" + empfaengerName + "** gefunden."))
                .setEphemeral(true).queue(); return;
        }
        if (receiver.getId().equals(userId)) {
            event.replyEmbeds(EmbedFactory.build("❌ Nicht erlaubt",
                "Du kannst nicht an dich selbst überweisen."))
                .setEphemeral(true).queue(); return;
        }
        String senderName = event.getMember() != null
            ? event.getMember().getEffectiveName() : event.getUser().getName();
        String err = BankManager.transfer(guildId, userId, receiver.getId(),
            amount, senderName, receiver.getEffectiveName());
        if (err != null) {
            event.replyEmbeds(EmbedFactory.build("❌ Überweisung fehlgeschlagen", err))
                .setEphemeral(true).queue(); return;
        }
        event.replyEmbeds(buildResultEmbed(
            "✅ Überweisung erfolgreich",
            "**-" + BankManager.formatAmount(amount) + "** wurden an **"
                + receiver.getEffectiveName() + "** überwiesen.",
            guildId, userId))
            .addComponents(bankRow()).setEphemeral(true).queue();
        // Empfänger per DM benachrichtigen
        BotLogger.tryDm(receiver.getUser(), EmbedFactory.build(
            "📥 Überweisung erhalten",
            "**" + senderName + "** hat dir **+" + BankManager.formatAmount(amount)
                + "** auf dein Bankkonto überwiesen."));
        log.info("[Bank] Überweisung {} → {} : {}$",
            event.getUser().getAsTag(), receiver.getUser().getAsTag(), amount);
    }

    // ── Embeds ────────────────────────────────────────────────────────────────

    public static MessageEmbed buildBankEmbed(String guildId, String userId) {
        long balance = BankManager.getBalance(guildId, userId);
        List<BankManager.BankTx> txList = BankManager.getTransactions(guildId, userId);

        EmbedBuilder eb = EmbedFactory.create()
            .setTitle("🏦 Paradise City — Online Banking")
            .setDescription("Verwalte dein Bankkonto sicher und bequem.");

        eb.addField("💰 Kontostand", "**" + BankManager.formatAmount(balance) + "**", false);

        if (txList.isEmpty()) {
            eb.addField("📋 Letzte Transaktionen", "*Keine Transaktionen vorhanden.*", false);
        } else {
            StringBuilder txStr = new StringBuilder();
            int show = Math.min(5, txList.size());
            for (int i = 0; i < show; i++)
                txStr.append(BankManager.formatTx(txList.get(i))).append("\n");
            eb.addField("📋 Letzte Transaktionen", txStr.toString(), false);
        }
        return eb.build();
    }

    private static MessageEmbed buildResultEmbed(String title, String desc,
                                                  String guildId, String userId) {
        long balance = BankManager.getBalance(guildId, userId);
        List<BankManager.BankTx> txList = BankManager.getTransactions(guildId, userId);

        EmbedBuilder eb = EmbedFactory.create()
            .setTitle(title)
            .setDescription(desc + "\n\n**Neuer Kontostand: " + BankManager.formatAmount(balance) + "**");

        if (!txList.isEmpty()) {
            StringBuilder txStr = new StringBuilder();
            int show = Math.min(5, txList.size());
            for (int i = 0; i < show; i++)
                txStr.append(BankManager.formatTx(txList.get(i))).append("\n");
            eb.addField("📋 Letzte Transaktionen", txStr.toString(), false);
        }
        return eb.build();
    }

    private static ActionRow bankRow() {
        return ActionRow.of(
            Button.primary("bank-btn-deposit",  "💳 Einzahlen"),
            Button.primary("bank-btn-withdraw", "💵 Auszahlen"),
            Button.primary("bank-btn-transfer", "📤 Überweisen")
        );
    }

    // ── Panel Posting ──────────────────────────────────────────────────────────

    public static void postPanelIfNeeded(Guild guild) {
        String key = "panel-bank-v1-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(LoggingConfig.BANK_CHANNEL_ID);
        if (ch == null) { log.warn("[Bank] Bank-Kanal nicht gefunden."); return; }
        String stored = DataStore.readString(key);
        if (stored != null && !stored.isBlank()) {
            ch.retrieveMessageById(stored).queue(
                msg -> { /* vorhanden */ },
                err -> { DataStore.deleteKey(key); sendPanel(ch, key); });
        } else {
            sendPanel(ch, key);
        }
    }

    private static void sendPanel(TextChannel ch, String key) {
        ch.sendMessageEmbeds(EmbedFactory.build(
            "🏦 Paradise City — Online Banking",
            "Verwalte dein Bankkonto bequem direkt über Discord.\n\n" +
            "💳 **Einzahlen** — Bargeld auf das Konto einzahlen\n" +
            "💵 **Auszahlen** — Geld abheben und als Bargeld erhalten\n" +
            "📤 **Überweisen** — Geld an andere Spieler senden\n\n" +
            "Klicke auf **Online Banking**, um dein Konto zu öffnen."))
            .addActionRow(Button.primary("bank-open", "🏦 Online Banking"))
            .queue(
                msg -> DataStore.writeString(key, msg.getId()),
                err -> log.error("[Bank] Panel konnte nicht gesendet werden.", err));
    }

    // ── Utils ──────────────────────────────────────────────────────────────────

    private static long parseAmount(String s) {
        if (s == null) return -1;
        try { return Long.parseLong(s.trim().replace(".", "").replace(",", "").replace("$", "")); }
        catch (NumberFormatException e) { return -1; }
    }
}
