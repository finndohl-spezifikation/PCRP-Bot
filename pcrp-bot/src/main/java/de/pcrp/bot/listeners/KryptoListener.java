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
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.EntitySelectMenu;
import net.dv8tion.jda.api.interactions.components.text.TextInput;
import net.dv8tion.jda.api.interactions.components.text.TextInputStyle;
import net.dv8tion.jda.api.interactions.modals.Modal;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * PC-Coins Krypto-Wallet: Einzahlen (Bank → Coins), Auszahlen (Coins → Bank),
 * Überweisen (Coins → anderes Krypto-Konto). Panel im Krypto-Kanal mit
 * Link-Button zur Kurs-Webseite (/krypto).
 */
public class KryptoListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(KryptoListener.class);

    /** Zwischenspeicher: userId → receiverId (zwischen EntitySelect und Modal-Submit). */
    private static final Map<String, String> PENDING_TRANSFER = new ConcurrentHashMap<>();

    /** Wallet-Panel-Beschreibung – als Konstante, damit Duplikat-Check und Sendetext nie auseinanderdriften. */
    private static final String WALLET_PANEL_DESC = "Öffne hier dein PC Coin Krypto wallet";

    // ── Button-Handler ────────────────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String cid     = event.getComponentId();
        String userId  = event.getUser().getId();
        String guildId = event.getGuild().getId();

        switch (cid) {
            case "krypto-wallet" -> {
                event.replyEmbeds(buildWalletEmbed(guildId, userId))
                    .addComponents(walletRow())
                    .setEphemeral(true).queue();
            }
            case "krypto-deposit" -> {
                Modal modal = Modal.create("krypto-modal-deposit", "💹 PC Coins kaufen")
                    .addComponents(ActionRow.of(
                        TextInput.create("betrag", "Betrag in $ (vom Bankkonto)", TextInputStyle.SHORT)
                            .setPlaceholder("z. B. 5000")
                            .setMinLength(1).setMaxLength(12)
                            .setRequired(true).build()))
                    .build();
                event.replyModal(modal).queue();
            }
            case "krypto-withdraw" -> {
                Modal modal = Modal.create("krypto-modal-withdraw", "💱 PC Coins verkaufen")
                    .addComponents(ActionRow.of(
                        TextInput.create("menge", "Anzahl PC Coins", TextInputStyle.SHORT)
                            .setPlaceholder("z. B. 100")
                            .setMinLength(1).setMaxLength(12)
                            .setRequired(true).build()))
                    .build();
                event.replyModal(modal).queue();
            }
            case "krypto-transfer" -> {
                EntitySelectMenu select = EntitySelectMenu
                    .create("krypto-transfer-select", EntitySelectMenu.SelectTarget.USER)
                    .setPlaceholder("Spieler suchen und auswählen…")
                    .setMinValues(1).setMaxValues(1)
                    .build();
                event.editMessageEmbeds(EmbedFactory.build(
                    "📤 PC Coins überweisen — Empfänger wählen",
                    "Wähle den Spieler aus, an den du PC Coins überweisen möchtest."))
                    .setComponents(
                        ActionRow.of(select),
                        ActionRow.of(Button.secondary("krypto-wallet", "← Zurück")))
                    .queue();
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
            case "krypto-modal-deposit"         -> handleDeposit(event, guildId, userId);
            case "krypto-modal-withdraw"        -> handleWithdraw(event, guildId, userId);
            case "krypto-modal-transfer-amount" -> handleTransferAmount(event, guildId, userId);
        }
    }

    // ── Einzahlen (Bank → Coins) ──────────────────────────────────────────────

    private void handleDeposit(ModalInteractionEvent event, String guildId, String userId) {
        long amount = parseLong(event.getValue("betrag").getAsString());
        if (amount <= 0) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültiger Betrag",
                "Bitte gib einen gültigen Betrag ein (z. B. `5000`)."))
                .setEphemeral(true).queue(); return;
        }
        String err = KryptoManager.buy(guildId, userId, amount);
        if (err != null) {
            event.replyEmbeds(EmbedFactory.build("❌ Kauf fehlgeschlagen", err))
                .setEphemeral(true).queue(); return;
        }
        long coins = KryptoManager.getBalance(guildId, userId);
        event.replyEmbeds(buildResultEmbed("✅ PC Coins gekauft",
            "**" + BankManager.formatAmount(amount) + "** wurden in PC Coins umgewandelt.",
            guildId, userId))
            .addComponents(walletRow()).setEphemeral(true).queue();
        BotLogger.logMoney(event.getGuild(), "💹 PC Coins gekauft",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Betrag:** -" + BankManager.formatAmount(amount) + "\n" +
            "**Neuer Bestand:** " + KryptoManager.formatCoins(coins));
        log.info("[Krypto] Kauf {} : {}$ → {} PC", event.getUser().getAsTag(), amount, coins);
    }

    // ── Auszahlen (Coins → Bank) ──────────────────────────────────────────────

    private void handleWithdraw(ModalInteractionEvent event, String guildId, String userId) {
        long coins = parseLong(event.getValue("menge").getAsString());
        if (coins <= 0) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültige Menge",
                "Bitte gib eine gültige Anzahl PC Coins ein (z. B. `100`)."))
                .setEphemeral(true).queue(); return;
        }
        String err = KryptoManager.sell(guildId, userId, coins);
        if (err != null) {
            event.replyEmbeds(EmbedFactory.build("❌ Verkauf fehlgeschlagen", err))
                .setEphemeral(true).queue(); return;
        }
        event.replyEmbeds(buildResultEmbed("✅ PC Coins verkauft",
            "**" + KryptoManager.formatCoins(coins) + "** wurden in Kontogeld umgewandelt.",
            guildId, userId))
            .addComponents(walletRow()).setEphemeral(true).queue();
        BotLogger.logMoney(event.getGuild(), "💱 PC Coins verkauft",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Menge:** -" + KryptoManager.formatCoins(coins));
        log.info("[Krypto] Verkauf {} : {} PC → Konto", event.getUser().getAsTag(), coins);
    }

    // ── Überweisen: Empfänger-Auswahl per Discord-Suchleiste ─────────────────

    @Override
    public void onEntitySelectInteraction(EntitySelectInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (!"krypto-transfer-select".equals(event.getComponentId())) return;

        List<Member> selected = event.getMentions().getMembers();
        if (selected.isEmpty()) { event.deferEdit().queue(); return; }

        Member receiver = selected.get(0);
        String userId   = event.getUser().getId();

        if (receiver.getId().equals(userId)) {
            event.editMessageEmbeds(EmbedFactory.build(
                "❌ Nicht erlaubt", "Du kannst nicht an dich selbst überweisen."))
                .setComponents(ActionRow.of(Button.secondary("krypto-wallet", "← Zurück")))
                .queue();
            return;
        }

        PENDING_TRANSFER.put(userId, receiver.getId());

        Modal modal = Modal.create("krypto-modal-transfer-amount",
                "📤 PC Coins an " + receiver.getEffectiveName())
            .addComponents(ActionRow.of(
                TextInput.create("menge", "Anzahl PC Coins", TextInputStyle.SHORT)
                    .setPlaceholder("z. B. 50")
                    .setMinLength(1).setMaxLength(12)
                    .setRequired(true).build()))
            .build();
        event.replyModal(modal).queue();
    }

    // ── Überweisen: Menge-Modal verarbeiten ───────────────────────────────────

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
        long coins = parseLong(event.getValue("menge").getAsString());
        if (coins <= 0) {
            event.replyEmbeds(EmbedFactory.build("❌ Ungültige Menge",
                "Bitte gib eine gültige Anzahl PC Coins ein (z. B. `50`)."))
                .setEphemeral(true).queue(); return;
        }
        String err = KryptoManager.transfer(guildId, userId, receiverId, coins);
        if (err != null) {
            event.replyEmbeds(EmbedFactory.build("❌ Überweisung fehlgeschlagen", err))
                .setEphemeral(true).queue(); return;
        }
        String senderName = event.getMember() != null
            ? event.getMember().getEffectiveName() : event.getUser().getName();
        event.replyEmbeds(buildResultEmbed("✅ Überweisung erfolgreich",
            "**" + KryptoManager.formatCoins(coins) + "** wurden an **"
                + receiver.getEffectiveName() + "** überwiesen.",
            guildId, userId))
            .addComponents(walletRow()).setEphemeral(true).queue();
        BotLogger.tryDm(receiver.getUser(), EmbedFactory.build(
            "📥 PC Coins erhalten",
            "**" + senderName + "** hat dir **" + KryptoManager.formatCoins(coins)
                + "** überwiesen."));
        BotLogger.logMoney(event.getGuild(), "📤 PC Coins überwiesen",
            "**Von:** " + event.getUser().getAsMention() + "\n" +
            "**An:** " + receiver.getAsMention() + " (" + receiver.getEffectiveName() + ")\n" +
            "**Menge:** " + KryptoManager.formatCoins(coins));
        log.info("[Krypto] Überweisung {} → {} : {} PC",
            event.getUser().getAsTag(), receiver.getUser().getAsTag(), coins);
    }

    // ── Embeds ────────────────────────────────────────────────────────────────

    public static MessageEmbed buildWalletEmbed(String guildId, String userId) {
        long coins = KryptoManager.getBalance(guildId, userId);

        EmbedBuilder eb = EmbedFactory.create()
            .setTitle("🪙 PC Coins Wallet")
            .setDescription("💰 Dein Krypto-Konto");

        eb.addField("🪙 Bestand", "**" + KryptoManager.formatCoins(coins) + "**", false);
        return eb.build();
    }

    private static MessageEmbed buildResultEmbed(String title, String desc,
                                                  String guildId, String userId) {
        long coins = KryptoManager.getBalance(guildId, userId);

        EmbedBuilder eb = EmbedFactory.create()
            .setTitle(title)
            .setDescription(desc + "\n\n" +
                "**Neuer Bestand:** " + KryptoManager.formatCoins(coins));
        return eb.build();
    }

    private static ActionRow walletRow() {
        return ActionRow.of(
            Button.primary("krypto-deposit",   "💹 Einzahlen"),
            Button.primary("krypto-withdraw",  "💱 Auszahlen"),
            Button.primary("krypto-transfer",  "📤 Überweisen")
        );
    }

    // ── Panel Posting ──────────────────────────────────────────────────────────

    /** Postet das WALLET-Panel (mit Wallet-öffnen-Button) in den Wallet-Kanal. */
    public static void postWalletPanelIfNeeded(Guild guild) {
        String key = "panel-krypto-wallet-v4-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(LoggingConfig.KRYPTO_CHANNEL_ID);
        if (ch == null) { log.warn("[Krypto] Wallet-Kanal nicht gefunden."); return; }
        // Beschreibung mitgeben: Der Duplikat-Schutz erkennt nur ein Embed mit gleichem
        // Titel UND gleichem Text als "schon vorhanden" – sonst blockt das alte v2-Embed
        // (gleicher Titel, anderer Text) das neue Panel dauerhaft.
        PanelHelper.post(ch, key, "🪙 PC Coins — Wallet",
            WALLET_PANEL_DESC,
            () -> sendWalletPanel(ch, key));
    }

    /** Postet das KURS-Panel (nur Kurse + Webseiten-Link) in den Kurs-Kanal. */
    public static void postRatesPanelIfNeeded(Guild guild) {
        String key = "panel-krypto-rates-v1-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(LoggingConfig.KRYPTO_RATES_CHANNEL_ID);
        if (ch == null) { log.warn("[Krypto] Kurs-Kanal nicht gefunden."); return; }
        PanelHelper.post(ch, key, "📈 PC Coins — Kurse", () -> sendRatesPanel(ch, key));
    }

    private static String kryptoUrl() {
        String webUrl = System.getenv("WEB_URL");
        if (webUrl == null || webUrl.isBlank()) {
            String domain = System.getenv("RAILWAY_PUBLIC_DOMAIN");
            webUrl = (domain != null && !domain.isBlank())
                ? (domain.startsWith("http") ? domain : "https://" + domain)
                : "https://dashboards.paradisecity-roleplay-85a.workers.dev";
        }
        return webUrl.replaceAll("/$", "") + "/krypto";
    }

    private static void sendWalletPanel(TextChannel ch, String key) {
        ch.sendMessageEmbeds(EmbedFactory.build(
            "🪙 PC Coins — Wallet",
            WALLET_PANEL_DESC))
            .addActionRow(
                Button.primary("krypto-wallet", "🪙 Wallet öffnen"))
            .queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Krypto] Wallet-Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
    }

    private static void sendRatesPanel(TextChannel ch, String key) {
        String guildId = ch.getGuild().getId();
        ch.sendMessageEmbeds(EmbedFactory.build(
            "📈 PC Coins — Kurse",
            "Aktueller Kurs: **" + KryptoManager.formatRate(KryptoManager.getRate(guildId)) + "**\\n" +
            "Im Umlauf: **" + KryptoManager.formatCoins(KryptoManager.getSupply(guildId)) + "**\\n\\n" +
            "Auf der Webseite siehst du den Kursverlauf der letzten **7 Tage**."))
            .addActionRow(
                Button.link(kryptoUrl(), "📈 Kurse ansehen"))
            .queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Krypto] Kurs-Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
    }

    // ── Utils ──────────────────────────────────────────────────────────────────

    private static long parseLong(String s) {
        if (s == null) return -1;
        try { return Long.parseLong(s.trim().replace(".", "").replace(",", "").replace("$", "")); }
        catch (NumberFormatException e) { return -1; }
    }
}
