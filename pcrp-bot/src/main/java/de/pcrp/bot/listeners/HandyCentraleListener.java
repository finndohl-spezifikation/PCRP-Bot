package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.entities.Role;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.StringSelectInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu;
import net.dv8tion.jda.api.interactions.components.text.TextInput;
import net.dv8tion.jda.api.interactions.components.text.TextInputStyle;
import net.dv8tion.jda.api.interactions.modals.Modal;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Handy-Zentrale — Haupt-Panel im Kanal 1529636579826729140.
 *
 * Optionen:
 *  1. Handy Einschalten  → Inventarprüfung, Rolle Handy-An vergeben
 *  2. Handy Ausschalten  → Rolle Handy-An entfernen, Handy-Aus vergeben
 *  3. Telefonnummer      → Vertrag anlegen oder anzeigen
 *  4. City Chat          → Link zur Chat-Webseite senden (ephemeral)
 */
public class HandyCentraleListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(HandyCentraleListener.class);

    // ── IDs ───────────────────────────────────────────────────────────────────
    public  static final long   CHANNEL_ID    = 1529636579826729140L;
    private static final long   ROLE_HANDY_AN  = 1529636356333244608L;
    private static final long   ROLE_HANDY_AUS = 1529636359944405114L;
    private static final String PANEL_KEY      = "panel-handy-zentrale-";
    private static final String ITEM_HANDY     = "Handy";
    private static final int    ITEM_PRICE     = 1000;
    private static final int    NEUE_NR_PREIS  = 500;
    private static final int    ERSTGEBÜHR     = 1000;

    // ── Panel posten ──────────────────────────────────────────────────────────

    public static void postPanel(Guild guild) {
        TextChannel ch = guild.getTextChannelById(CHANNEL_ID);
        if (ch == null) {
            log.warn("[Handy] Kanal {} nicht gefunden.", CHANNEL_ID);
            return;
        }
        String key = PANEL_KEY + guild.getId();
        PanelHelper.post(ch, key, "📱 Handy-Zentrale", () -> sendHandyPanel(ch, key));
    }

    private static void sendHandyPanel(TextChannel ch, String key) {
        StringSelectMenu menu = StringSelectMenu.create("handy:select")
            .setPlaceholder("Was möchtest du tun?")
            .addOption("📱 Handy Einschalten",   "einschalten", "Schalte dein Handy ein")
            .addOption("📴 Handy Ausschalten",   "ausschalten", "Schalte dein Handy aus")
            .addOption("📞 Handy Einstellungen", "nummer",      "Rufnummer, Safe-Pin & City Chat Link")
            .addOption("💬 City Chat",            "citychat",    "Direkt in den City Chat")
            .build();

        ch.sendMessageEmbeds(
            EmbedFactory.create()
                .setTitle("📱 Handy-Zentrale")
                .setDescription(
                    "Willkommen in der **Handy-Zentrale** von Paradise City Roleplay.\n\n" +
                    "**📱 Handy Einschalten** — Aktiviert dein Handy (Handy im Inventar erforderlich)\n" +
                    "**📴 Handy Ausschalten** — Deaktiviert dein Handy\n" +
                    "**📞 Handy Einstellungen** — Rufnummer, Safe-Pin & City Chat Link\n" +
                    "**💬 City Chat** — Öffnet den City Chat direkt (Handy + Vertrag erforderlich)")
                .build()
        ).addComponents(ActionRow.of(menu)).queue(
            msg -> PanelHelper.onSent(key, msg.getId()),
            err -> log.error("[Handy] Panel-Post fehlgeschlagen.", err)
        );
    }

    // ── SelectMenu ────────────────────────────────────────────────────────────

    @Override
    public void onStringSelectInteraction(StringSelectInteractionEvent event) {
        if (!"handy:select".equals(event.getComponentId())) return;
        if (event.getGuild() == null) return;

        String option  = event.getValues().get(0);
        String userId  = event.getUser().getId();
        String guildId = event.getGuild().getId();
        Member member  = event.getMember();
        Guild  guild   = event.getGuild();

        switch (option) {
            case "einschalten"  -> handleEinschalten(event, guild, member, userId, guildId);
            case "ausschalten"  -> handleAusschalten(event, guild, member, userId, guildId);
            case "nummer"       -> handleNummer(event, guild, member, userId, guildId);
            case "citychat"     -> handleCityChat(event, guild, member, userId, guildId);
        }
    }

    // ── Einschalten ───────────────────────────────────────────────────────────

    private void handleEinschalten(StringSelectInteractionEvent event,
                                   Guild guild, Member member, String userId, String guildId) {
        // Bereits an?
        Role roleAn = guild.getRoleById(ROLE_HANDY_AN);
        if (roleAn != null && member.getRoles().contains(roleAn)) {
            event.replyEmbeds(EmbedFactory.build("📱 Handy-Zentrale",
                "Dein Handy ist bereits **eingeschaltet**."))
                .setEphemeral(true).queue();
            return;
        }

        // Handy im Inventar?
        boolean hasHandy = InventoryManager.getInventory(guildId, userId).stream()
            .anyMatch(it -> InventoryManager.nameMatches(it.name, ITEM_HANDY));

        if (!hasHandy) {
            event.replyEmbeds(EmbedFactory.build("📱 Handy-Zentrale",
                "❌ Du hast kein **Handy** in deinem Inventar.\n\n" +
                "Kaufe ein Handy für **" + ShopManager.formatPrice(ITEM_PRICE) + "** im Shop."))
                .setEphemeral(true).queue();
            return;
        }

        // Rollen setzen
        if (roleAn != null) guild.addRoleToMember(member, roleAn).queue();
        Role roleAus = guild.getRoleById(ROLE_HANDY_AUS);
        if (roleAus != null) guild.removeRoleFromMember(member, roleAus).queue();

        event.replyEmbeds(EmbedFactory.build("📱 Handy-Zentrale",
            "✅ Dein Handy wurde **eingeschaltet**."))
            .setEphemeral(true).queue();
        log.info("[Handy] {} hat Handy eingeschaltet.", userId);
    }

    // ── Ausschalten ───────────────────────────────────────────────────────────

    private void handleAusschalten(StringSelectInteractionEvent event,
                                   Guild guild, Member member, String userId, String guildId) {
        Role roleAn  = guild.getRoleById(ROLE_HANDY_AN);
        Role roleAus = guild.getRoleById(ROLE_HANDY_AUS);

        if (roleAn != null && !member.getRoles().contains(roleAn)) {
            event.replyEmbeds(EmbedFactory.build("📱 Handy-Zentrale",
                "Dein Handy ist bereits **ausgeschaltet**."))
                .setEphemeral(true).queue();
            return;
        }

        if (roleAn  != null) guild.removeRoleFromMember(member, roleAn).queue();
        if (roleAus != null) guild.addRoleToMember(member, roleAus).queue();

        event.replyEmbeds(EmbedFactory.build("📱 Handy-Zentrale",
            "📴 Dein Handy wurde **ausgeschaltet**."))
            .setEphemeral(true).queue();
        log.info("[Handy] {} hat Handy ausgeschaltet.", userId);
    }

    // ── Telefonnummer ─────────────────────────────────────────────────────────

    private void handleNummer(StringSelectInteractionEvent event,
                              Guild guild, Member member, String userId, String guildId) {
        PhoneManager.Contract c = PhoneManager.getContract(guildId, userId);

        if (c == null) {
            // Kein Vertrag — Angebot
            event.replyEmbeds(
                EmbedFactory.create()
                    .setTitle("📞 Telefonnummer")
                    .setDescription(
                        "📵 **Noch keine SIM-Karte aktiviert.**\n\n" +
                        "Du hast noch keinen Handy-Vertrag. Schließe jetzt einen Vertrag ab und erhalte:\n\n" +
                        "• Eine **Los Angeles Rufnummer**\n" +
                        "• Einen persönlichen **Safe-Pin** (4 Ziffern)\n" +
                        "• Zugang zum **City Chat**\n\n" +
                        "💳 Monatliche Gebühr: **1.000$** (wird automatisch abgebucht)")
                    .build()
            ).addComponents(ActionRow.of(
                Button.success("handy:vertrag_start", "📋 Vertrag abschließen")
            )).setEphemeral(true).queue();
        } else {
            // Vertrag vorhanden — anzeigen + City Chat Link direkt generieren
            String token    = PhoneManager.createSession(guildId, c.phoneNumber);
            String chatLink = "https://pcrp-bot-production-3ad1.up.railway.app/city-chat?token=" + token;

            event.replyEmbeds(
                EmbedFactory.create()
                    .setTitle("📞 Deine Handy-Einstellungen")
                    .setDescription(
                        "**Name:** " + c.displayName() + "\n" +
                        "**Rufnummer:** `" + c.phoneNumber + "`\n" +
                        "**Safe-Pin:** `" + c.safePin + "`\n\n" +
                        "⚠️ Gib deinen Safe-Pin **niemals** weiter!\n\n" +
                        "💬 Klicke auf **City Chat öffnen** um direkt in den Chat zu gelangen.\n" +
                        "🔄 Neue Nummer kostet **500$** (Service-Gebühr)")
                    .build()
            ).addComponents(ActionRow.of(
                Button.link(chatLink, "💬 City Chat öffnen"),
                Button.danger("handy:neue_nummer", "🔄 Neue Nummer (500$)")
            )).setEphemeral(true).queue();
        }
    }

    // ── City Chat ─────────────────────────────────────────────────────────────

    private void handleCityChat(StringSelectInteractionEvent event,
                                Guild guild, Member member, String userId, String guildId) {
        // Handy an?
        Role roleAn = guild.getRoleById(ROLE_HANDY_AN);
        if (roleAn == null || !member.getRoles().contains(roleAn)) {
            event.replyEmbeds(EmbedFactory.build("💬 City Chat",
                "❌ Dein Handy ist **ausgeschaltet**.\nSchalte zuerst dein Handy ein."))
                .setEphemeral(true).queue();
            return;
        }

        // Vertrag?
        PhoneManager.Contract c = PhoneManager.getContract(guildId, userId);
        if (c == null) {
            event.replyEmbeds(EmbedFactory.build("💬 City Chat",
                "❌ Du hast noch keine **Rufnummer**.\nSchließe zuerst einen Vertrag ab (Telefonnummer → Vertrag abschließen)."))
                .setEphemeral(true).queue();
            return;
        }

        // Session-Token generieren und Link senden
        String token = PhoneManager.createSession(guildId, c.phoneNumber);
        String link  = "https://pcrp-bot-production-3ad1.up.railway.app/city-chat?token=" + token;

        event.replyEmbeds(
            EmbedFactory.create()
                .setTitle("💬 City Chat")
                .setDescription(
                    "📲 Dein persönlicher City Chat Link ist bereit.\n\n" +
                    "**Rufnummer:** `" + c.phoneNumber + "`\n\n" +
                    "Klicke auf den Button um den Chat zu öffnen. Der Link ist **7 Tage** gültig.\n\n" +
                    "⚠️ Teile diesen Link mit **niemandem** — er gibt vollen Zugang zu deinem Account.")
                .build()
        ).addComponents(ActionRow.of(
            Button.link(link, "💬 City Chat öffnen")
        )).setEphemeral(true).queue();
    }

    // ── Button: Vertrag starten ───────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String cid = event.getComponentId();

        if ("handy:vertrag_start".equals(cid)) {
            Modal modal = Modal.create("handy:vertrag_modal", "Vertrag abschließen")
                .addComponents(
                    ActionRow.of(TextInput.create("vorname", "Vorname (Ingame)", TextInputStyle.SHORT)
                        .setPlaceholder("z.B. Max").setMinLength(2).setMaxLength(32).setRequired(true).build()),
                    ActionRow.of(TextInput.create("nachname", "Nachname (Ingame)", TextInputStyle.SHORT)
                        .setPlaceholder("z.B. Müller").setMinLength(2).setMaxLength(32).setRequired(true).build())
                ).build();
            event.replyModal(modal).queue();
        }

        if ("handy:neue_nummer".equals(cid)) {
            String userId  = event.getUser().getId();
            String guildId = event.getGuild().getId();

            long balance = BankManager.getBalance(guildId, userId);
            if (balance < NEUE_NR_PREIS) {
                event.replyEmbeds(EmbedFactory.build("🔄 Neue Nummer",
                    "❌ Nicht genug Geld. Du benötigst **500$**.\nDein Kontostand: **" +
                    ShopManager.formatPrice(balance) + "**"))
                    .setEphemeral(true).queue();
                return;
            }

            PhoneManager.Contract c = PhoneManager.regenerateNumber(guildId, userId);
            if (c == null) {
                event.replyEmbeds(EmbedFactory.build("🔄 Neue Nummer",
                    "❌ Fehler — kein aktiver Vertrag gefunden."))
                    .setEphemeral(true).queue();
                return;
            }

            BankManager.setBalance(guildId, userId, balance - NEUE_NR_PREIS);
            BankManager.addTransaction(guildId, userId, "HANDY_NUMMER_WECHSEL", NEUE_NR_PREIS, null);

            event.replyEmbeds(
                EmbedFactory.create()
                    .setTitle("🔄 Neue Nummer generiert")
                    .setDescription(
                        "✅ Deine alte Nummer wurde gelöscht.\n\n" +
                        "**Neue Rufnummer:** `" + c.phoneNumber + "`\n" +
                        "**Neuer Safe-Pin:** `" + c.safePin + "`\n\n" +
                        "**500$** wurden als Service-Gebühr abgezogen.")
                    .build()
            ).setEphemeral(true).queue();
            log.info("[Handy] {} hat neue Nummer generiert: {}", userId, c.phoneNumber);
        }
    }

    // ── Modal: Vertrag bestätigen ─────────────────────────────────────────────

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        if (!"handy:vertrag_modal".equals(event.getModalId())) return;
        if (event.getGuild() == null) return;

        String userId    = event.getUser().getId();
        String guildId   = event.getGuild().getId();
        String firstName = event.getValue("vorname") != null
            ? event.getValue("vorname").getAsString().trim() : "";
        String lastName  = event.getValue("nachname") != null
            ? event.getValue("nachname").getAsString().trim() : "";

        if (firstName.isEmpty() || lastName.isEmpty()) {
            event.replyEmbeds(EmbedFactory.build("📋 Vertrag",
                "❌ Bitte gib Vor- und Nachnamen an."))
                .setEphemeral(true).queue();
            return;
        }

        // Bereits Vertrag?
        if (PhoneManager.getContract(guildId, userId) != null) {
            event.replyEmbeds(EmbedFactory.build("📋 Vertrag",
                "❌ Du hast bereits einen aktiven Vertrag."))
                .setEphemeral(true).queue();
            return;
        }

        // Erstgebühr sofort abziehen
        long balance = BankManager.getBalance(guildId, userId);
        if (balance < ERSTGEBÜHR) {
            event.replyEmbeds(EmbedFactory.build("📋 Vertrag",
                "❌ Nicht genug Geld für die Erstgebühr.\nBenötigt: **1.000$** — Dein Kontostand: **" +
                ShopManager.formatPrice(balance) + "**"))
                .setEphemeral(true).queue();
            return;
        }

        PhoneManager.Contract c = PhoneManager.createContract(guildId, userId, firstName, lastName);
        BankManager.setBalance(guildId, userId, balance - ERSTGEBÜHR);
        BankManager.addTransaction(guildId, userId, "HANDY_VERTRAG", ERSTGEBÜHR, null);

        event.replyEmbeds(
            EmbedFactory.create()
                .setTitle("✅ Vertrag abgeschlossen!")
                .setDescription(
                    "Willkommen im PCRP-Handynetz, **" + c.displayName() + "**!\n\n" +
                    "📞 **Deine Rufnummer:** `" + c.phoneNumber + "`\n" +
                    "🔐 **Dein Safe-Pin:** `" + c.safePin + "`\n\n" +
                    "⚠️ Merke dir deinen Safe-Pin — du brauchst ihn für den City Chat.\n\n" +
                    "💰 **Erstgebühr:** 1.000$ (sofort abgezogen)\n" +
                    "💳 **Monatliche Gebühr:** 1.000$ (automatisch)")
                .build()
        ).setEphemeral(true).queue();
        log.info("[Handy] {} hat Vertrag abgeschlossen: {}", userId, c.phoneNumber);
    }
}
