package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.entities.MessageEmbed;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.EntitySelectInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.StringSelectInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.EntitySelectMenu;
import net.dv8tion.jda.api.interactions.components.selections.SelectOption;
import net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu;
import net.dv8tion.jda.api.interactions.components.text.TextInput;
import net.dv8tion.jda.api.interactions.components.text.TextInputStyle;
import net.dv8tion.jda.api.interactions.modals.Modal;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;

/** Online-Banking Panel und Transaktionen (Einzahlen, Auszahlen, Überweisen). */
public class BankListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(BankListener.class);

    /** Zwischenspeicher: userId → receiverId (zwischen EntitySelect und Modal-Submit). */
    private static final Map<String, String> PENDING_TRANSFER = new ConcurrentHashMap<>();

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
                EntitySelectMenu select = EntitySelectMenu
                    .create("bank-transfer-select", EntitySelectMenu.SelectTarget.USER)
                    .setPlaceholder("Spieler suchen und auswählen…")
                    .setMinValues(1).setMaxValues(1)
                    .build();
                event.editMessageEmbeds(EmbedFactory.build(
                    "📤 Überweisen — Empfänger wählen",
                    "Wähle den Spieler aus, an den du Geld überweisen möchtest."))
                    .setComponents(
                        ActionRow.of(select),
                        ActionRow.of(Button.secondary("bank-open", "← Zurück")))
                    .queue();
            }
            case "bank-btn-bills" -> {
                List<RechnungManager.Rechnung> offene = RechnungManager.getOffene(guildId, userId);
                if (offene.isEmpty()) {
                    event.replyEmbeds(EmbedFactory.build(
                        "🧾 Offene Rechnungen",
                        "Du hast aktuell **keine offenen Rechnungen**.\n\n" +
                        "Bezahlte Rechnungen werden hier nicht mehr angezeigt."))
                        .setEphemeral(true).queue();
                    return;
                }
                StringBuilder sb = new StringBuilder();
                long total = 0;
                for (RechnungManager.Rechnung r : offene) {
                    sb.append(RechnungManager.formatRechnung(r)).append("\n");
                    total += r.amount;
                }
                SelectOption[] options = offene.stream()
                    .limit(25)
                    .map(r -> {
                        String label = r.beschreibung + " — " + BankManager.formatAmount(r.amount);
                        if (label.length() > 100) label = label.substring(0, 97) + "…";
                        return SelectOption.of(label, r.id);
                    })
                    .toArray(SelectOption[]::new);

                event.replyEmbeds(
                    EmbedFactory.create()
                        .setTitle("🧾 Offene Rechnungen")
                        .setDescription(
                            "Folgende Rechnungen sind noch offen:\n\n" +
                            sb.toString() + "\n" +
                            "━━━━━━━━━━━━━━━━━━━━━━\n\n" +
                            "**Gesamt: " + BankManager.formatAmount(total) + "**")
                        .build()
                ).addComponents(
                    ActionRow.of(
                        StringSelectMenu.create("bank-bill-select")
                            .setPlaceholder("Rechnung einzeln bezahlen…")
                            .setMinValues(1).setMaxValues(1)
                            .addOptions(options)
                            .build()
                    ),
                    ActionRow.of(
                        Button.success("bank-bill-payall", "✅ Alle bezahlen (" + BankManager.formatAmount(total) + ")")
                    )
                ).setEphemeral(true).queue();
            }
            case "bank-bill-payall" -> {
                String err = RechnungManager.payAll(guildId, userId);
                if (err != null) {
                    event.replyEmbeds(EmbedFactory.build("❌ Bezahlung fehlgeschlagen", err))
                        .setEphemeral(true).queue();
                    return;
                }
                long balance = BankManager.getBalance(guildId, userId);
                event.replyEmbeds(
                    EmbedFactory.create()
                        .setTitle("✅ Alle Rechnungen bezahlt")
                        .setDescription(
                            "Alle offenen Rechnungen wurden beglichen.\n\n" +
                            "**Neuer Kontostand:** " + BankManager.formatAmount(balance))
                        .build()
                ).addComponents(ActionRow.of(
                    Button.primary("bank-btn-bills", "🧾 Offene Rechnungen")
                )).setEphemeral(true).queue();
                BotLogger.logMoney(event.getGuild(), "🧾 Alle Rechnungen bezahlt",
                    "**Spieler:** " + event.getUser().getAsMention());
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
            case "bank-modal-deposit"          -> handleDeposit(event, guildId, userId);
            case "bank-modal-withdraw"         -> handleWithdraw(event, guildId, userId);
            case "bank-modal-transfer-amount"  -> handleTransferAmount(event, guildId, userId);
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
        BotLogger.logMoney(event.getGuild(), "💳 Einzahlung",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Betrag:** +" + BankManager.formatAmount(amount));
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
        BotLogger.logMoney(event.getGuild(), "💵 Auszahlung",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Betrag:** -" + BankManager.formatAmount(amount));
        log.info("[Bank] Auszahlung {} : {}$", event.getUser().getAsTag(), amount);
    }

    // ── Überweisen: Empfänger-Auswahl per Discord-Suchleiste ─────────────────

    @Override
    public void onEntitySelectInteraction(EntitySelectInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (!"bank-transfer-select".equals(event.getComponentId())) return;

        List<Member> selected = event.getMentions().getMembers();
        if (selected.isEmpty()) { event.deferEdit().queue(); return; }

        Member receiver = selected.get(0);
        String userId   = event.getUser().getId();

        if (receiver.getId().equals(userId)) {
            event.editMessageEmbeds(EmbedFactory.build(
                "❌ Nicht erlaubt", "Du kannst nicht an dich selbst überweisen."))
                .setComponents(ActionRow.of(Button.secondary("bank-open", "← Zurück")))
                .queue();
            return;
        }

        PENDING_TRANSFER.put(userId, receiver.getId());

        Modal modal = Modal.create("bank-modal-transfer-amount",
                "📤 Überweisen an " + receiver.getEffectiveName())
            .addComponents(ActionRow.of(
                TextInput.create("betrag", "Betrag in $", TextInputStyle.SHORT)
                    .setPlaceholder("z. B. 5000")
                    .setMinLength(1).setMaxLength(12)
                    .setRequired(true).build()))
            .build();
        event.replyModal(modal).queue();
    }

    // ── Überweisen: Betrag-Modal verarbeiten ──────────────────────────────────

    private void handleTransferAmount(ModalInteractionEvent event, String guildId, String userId) {
        String receiverId = PENDING_TRANSFER.remove(userId);
        if (receiverId == null) {
            event.replyEmbeds(EmbedFactory.build("❌ Fehler",
                "Kein Empfänger ausgewählt. Bitte erneut auf **Überweisen** klicken."))
                .setEphemeral(true).queue(); return;
        }
        Member receiver = event.getGuild().getMemberById(receiverId);
        if (receiver == null) {
            event.replyEmbeds(EmbedFactory.build("❌ Empfänger nicht gefunden",
                "Der ausgewählte Spieler ist nicht mehr auf dem Server."))
                .setEphemeral(true).queue(); return;
        }
        long amount = parseAmount(event.getValue("betrag").getAsString());
        if (amount <= 0) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültiger Betrag",
                "Bitte gib einen gültigen Betrag ein (z. B. `5000`)."))
                .setEphemeral(true).queue(); return;
        }
        String senderName = event.getMember() != null
            ? event.getMember().getEffectiveName() : event.getUser().getName();
        String err = BankManager.transfer(guildId, userId, receiverId,
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
        BotLogger.tryDm(receiver.getUser(), EmbedFactory.build(
            "📥 Überweisung erhalten",
            "**" + senderName + "** hat dir **+" + BankManager.formatAmount(amount)
                + "** auf dein Bankkonto überwiesen."));
        BotLogger.logMoney(event.getGuild(), "📤 Überweisung",
            "**Von:** " + event.getUser().getAsMention() + "\n" +
            "**An:** " + receiver.getAsMention() + " (" + receiver.getEffectiveName() + ")\n" +
            "**Betrag:** " + BankManager.formatAmount(amount));
        log.info("[Bank] Überweisung {} → {} : {}$",
            event.getUser().getAsTag(), receiver.getUser().getAsTag(), amount);
    }

    // ── Embeds ────────────────────────────────────────────────────────────────

    public static MessageEmbed buildBankEmbed(String guildId, String userId) {
        long balance = BankManager.getBalance(guildId, userId);
        List<BankManager.BankTx> txList = BankManager.getTransactions(guildId, userId);

        EmbedBuilder eb = EmbedFactory.create()
            .setTitle("🏦 Paradise City — Online Banking")
            .setDescription("💰 Kontoübersicht");

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

    // ── Rechnungen: StringSelect (einzelne Rechnung bezahlen) ────────────────

    @Override
    public void onStringSelectInteraction(StringSelectInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (!"bank-bill-select".equals(event.getComponentId())) return;

        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();
        String billId  = event.getValues().get(0);

        String err = RechnungManager.payRechnung(guildId, userId, billId);
        if (err != null) {
            event.editMessageEmbeds(EmbedFactory.build("❌ Bezahlung fehlgeschlagen", err))
                .queue();
            return;
        }

        long balance = BankManager.getBalance(guildId, userId);
        List<RechnungManager.Rechnung> remaining = RechnungManager.getOffene(guildId, userId);

        String desc = "✅ **Rechnung wurde bezahlt!**\n\n" +
            "**Neuer Kontostand:** " + BankManager.formatAmount(balance);

        if (!remaining.isEmpty()) {
            desc += "\n\nEs sind noch **" + remaining.size() + "** Rechnung(en) offen.";
        }

        event.editMessageEmbeds(EmbedFactory.build("✅ Rechnung bezahlt", desc))
            .setComponents(ActionRow.of(
                Button.primary("bank-btn-bills", "🧾 Offene Rechnungen")
            )).queue();

        BotLogger.logMoney(event.getGuild(), "🧾 Rechnung bezahlt",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Betrag:** -" + BankManager.formatAmount(
                RechnungManager.getAll(guildId, userId).stream()
                    .filter(r -> r.id.equals(billId))
                    .findFirst().map(r -> r.amount).orElse(0L)));
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
        String key = "panel-bank-v2-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(LoggingConfig.BANK_CHANNEL_ID);
        if (ch == null) { log.warn("[Bank] Bank-Kanal nicht gefunden."); return; }
        PanelHelper.post(ch, key, "🏦 Paradise City — Online Banking", () -> sendPanel(ch, key));
    }

    private static void sendPanel(TextChannel ch, String key) {
        ch.sendMessageEmbeds(EmbedFactory.build(
            "🏦 Paradise City — Online Banking",
            "💳 **Einzahlen** — Bargeld auf das Konto einzahlen\n" +
            "💵 **Auszahlen** — Geld abheben und als Bargeld erhalten\n" +
            "📤 **Überweisen** — Geld an andere Spieler senden\n\n" +
            "Klicke auf **Online Banking**, um dein Konto zu öffnen.\n" +
            "Oder prüfe deine **offenen Rechnungen** direkt."))
            .addActionRow(
                Button.primary("bank-open", "🏦 Online Banking"),
                Button.secondary("bank-btn-bills", "🧾 Offene Rechnungen"))
            .queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Bank] Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
    }

    // ── Utils ──────────────────────────────────────────────────────────────────

    private static long parseAmount(String s) {
        if (s == null) return -1;
        try { return Long.parseLong(s.trim().replace(".", "").replace(",", "").replace("$", "")); }
        catch (NumberFormatException e) { return -1; }
    }
}
