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
    private static final String PANEL_KEY      = "panel-handy-zentrale-v5-";
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
        String guildId = guild.getId();
        String key = PANEL_KEY + guildId;

        // Alte DataStore-Keys aller Vorgängerversionen löschen
        DataStore.deleteKey("panel-handy-zentrale-" + guildId);
        DataStore.deleteKey("panel-handy-zentrale-v2-" + guildId);
        DataStore.deleteKey("panel-handy-zentrale-v3-" + guildId);
        DataStore.deleteKey("panel-handy-zentrale-v4-" + guildId);

        // Alle vorhandenen Bot-Nachrichten mit Titel "📱 Handy-Zentrale" im Kanal löschen,
        // dann frisch posten
        ch.getHistory().retrievePast(50).queue(
            messages -> {
                messages.stream()
                    .filter(m -> m.getAuthor().isBot()
                        && !m.getEmbeds().isEmpty()
                        && "📱 Handy-Zentrale".equals(m.getEmbeds().get(0).getTitle()))
                    .forEach(m -> m.delete().queue(
                        ok  -> log.info("[Handy] Altes Panel {} gelöscht.", m.getId()),
                        err -> log.warn("[Handy] Konnte altes Panel nicht löschen: {}", err.getMessage())
                    ));
                PanelHelper.post(ch, key, "📱 Handy-Zentrale", () -> sendHandyPanel(ch, key));
            },
            err -> PanelHelper.post(ch, key, "📱 Handy-Zentrale", () -> sendHandyPanel(ch, key))
        );
    }

    private static void sendHandyPanel(TextChannel ch, String key) {
        StringSelectMenu menu = StringSelectMenu.create("handy:select")
            .setPlaceholder("Was möchtest du tun?")
            .addOption("📱 Handy Einschalten",   "einschalten", "Schalte dein Handy ein")
            .addOption("📴 Handy Ausschalten",   "ausschalten", "Schalte dein Handy aus")
            .addOption("📞 Handy Einstellungen", "nummer",      "Rufnummer & City Chat aktivieren")
            .addOption("💬 City Chat",           "citychat",    "City Chat aktivieren & öffnen")
            .addOption("📸 Citygram",            "citygram",    "Citygram aktivieren & öffnen")
            .build();

        ch.sendMessageEmbeds(
            EmbedFactory.create()
                .setTitle("📱 Handy-Zentrale")
                .setDescription(
                    "Willkommen in der **Handy-Zentrale** von Paradise City Roleplay.\n\n" +
                    "**📱 Handy Einschalten** — Aktiviert dein Handy (Handy im Inventar erforderlich)\n" +
                    "**📴 Handy Ausschalten** — Deaktiviert dein Handy\n" +
                    "**📞 Handy Einstellungen** — Rufnummer, City Chat & Citygram\n" +
                    "**💬 City Chat** — City Chat aktivieren & öffnen\n" +
                    "**📸 Citygram** — Citygram aktivieren & öffnen")
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
            case "citychat"     -> handleCityChatActivate(event, guild, member, userId, guildId);
            case "citygram"     -> handleCitygramSelect(event, guild, member, userId, guildId);
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

    // ── Telefonnummer / City Chat Aktivierung ────────────────────────────────

    private void handleNummer(StringSelectInteractionEvent event,
                              Guild guild, Member member, String userId, String guildId) {
        PhoneManager.Contract c = PhoneManager.getContract(guildId, userId);

        if (c == null) {
            event.replyEmbeds(
                EmbedFactory.create()
                    .setTitle("📞 Telefonnummer")
                    .setDescription(
                        "📵 **Noch keine SIM-Karte aktiviert.**\n\n" +
                        "Du hast noch keinen Handy-Vertrag. Schließe jetzt einen Vertrag ab und erhalte:\n\n" +
                        "• Eine **Los Angeles Rufnummer**\n" +
                        "• Zugang zum **City Chat**\n\n" +
                        "💳 Monatliche Gebühr: **1.000$** (wird automatisch abgebucht)")
                    .build()
            ).addComponents(ActionRow.of(
                Button.success("handy:vertrag_start", "📋 Vertrag abschließen")
            )).setEphemeral(true).queue();
            return;
        }

        // City-Chat-Rolle direkt vergeben
        Role cityChatRole = guild.getRoleById(CITY_CHAT_ROLE_ID);
        boolean alreadyActive = cityChatRole != null && member.getRoles().contains(cityChatRole);
        if (!alreadyActive && cityChatRole != null) {
            guild.addRoleToMember(member, cityChatRole).queue(
                ok  -> log.info("[CityChat] Rolle an {} vergeben.", userId),
                err -> log.warn("[CityChat] Rolle konnte nicht vergeben werden: {}", err.getMessage())
            );
        }

        // Citygram-Rolle prüfen
        Role citygramRole   = guild.getRoleById(CITYGRAM_ROLE_ID);
        boolean cgActive    = citygramRole != null && member.getRoles().contains(citygramRole);

        String cityChatLine = alreadyActive
            ? "✅ **City Chat:** aktiviert"
            : "✅ **City Chat:** soeben aktiviert!";
        String citygramLine = cgActive
            ? "✅ **Citygram:** aktiviert"
            : "📸 **Citygram:** noch nicht aktiviert";

        java.util.List<net.dv8tion.jda.api.interactions.components.ActionRow> rows = new java.util.ArrayList<>();
        if (!cgActive) {
            rows.add(ActionRow.of(Button.success("handy:citygram_activate", "📸 Citygram aktivieren")));
        }
        rows.add(ActionRow.of(Button.danger("handy:neue_nummer", "🔄 Neue Nummer (500$)")));

        event.replyEmbeds(
            EmbedFactory.create()
                .setTitle("📞 Handy-Einstellungen")
                .setDescription(
                    "**Name:** " + c.displayName() + "\n" +
                    "**Rufnummer:** `" + c.phoneNumber + "`\n\n" +
                    cityChatLine + "\n" +
                    citygramLine + "\n\n" +
                    "🔄 Neue Nummer kostet **500$** (Service-Gebühr)")
                .build()
        ).addComponents(rows).setEphemeral(true).queue();
    }

    private static final long CITY_CHAT_ROLE_ID  = 1529636364201627660L;
    private static final long CITYGRAM_ROLE_ID   = 1529636363119624293L;

    private static String webUrl() {
        String url = System.getenv("WEB_URL");
        if (url == null || url.isBlank()) {
            String domain = System.getenv("RAILWAY_PUBLIC_DOMAIN");
            url = (domain != null && !domain.isBlank())
                ? (domain.startsWith("http") ? domain : "https://" + domain)
                : "https://pcrp-bot-production-3ad1.up.railway.app";
        }
        return url.replaceAll("/$", "");
    }

    // ── City Chat Aktivierung (altes Panel, kein Nummern-Button) ──────────────

    private void handleCityChatActivate(StringSelectInteractionEvent event,
                                        Guild guild, Member member, String userId, String guildId) {
        Role roleAn = guild.getRoleById(ROLE_HANDY_AN);
        if (roleAn == null || !member.getRoles().contains(roleAn)) {
            event.replyEmbeds(EmbedFactory.build("💬 City Chat",
                "❌ Dein Handy ist **ausgeschaltet**.\nSchalte zuerst dein Handy ein."))
                .setEphemeral(true).queue();
            return;
        }

        PhoneManager.Contract c = PhoneManager.getContract(guildId, userId);
        if (c == null) {
            event.replyEmbeds(EmbedFactory.build("💬 City Chat",
                "❌ Du hast noch keine **Rufnummer**.\nSchließe zuerst einen Vertrag ab."))
                .setEphemeral(true).queue();
            return;
        }

        Role cityChatRole = guild.getRoleById(CITY_CHAT_ROLE_ID);
        boolean alreadyActive = cityChatRole != null && member.getRoles().contains(cityChatRole);
        if (!alreadyActive && cityChatRole != null) {
            guild.addRoleToMember(member, cityChatRole).queue(
                ok  -> log.info("[CityChat] Rolle an {} vergeben.", userId),
                err -> log.warn("[CityChat] Rolle konnte nicht vergeben werden: {}", err.getMessage())
            );
        }

        event.replyEmbeds(
            EmbedFactory.create()
                .setTitle("💬 City Chat")
                .setDescription(alreadyActive
                    ? "✅ City Chat ist bereits aktiviert."
                    : "✅ City Chat wurde aktiviert!\n\nDu hast die City Chat Rolle erhalten.")
                .build()
        ).setEphemeral(true).queue();
    }

    // ── Citygram Aktivierung (Select-Menü) ───────────────────────────────────

    private void handleCitygramSelect(StringSelectInteractionEvent event,
                                      Guild guild, Member member, String userId, String guildId) {
        Role roleAn = guild.getRoleById(ROLE_HANDY_AN);
        if (roleAn == null || !member.getRoles().contains(roleAn)) {
            event.replyEmbeds(EmbedFactory.build("📸 Citygram",
                "❌ Dein Handy ist **ausgeschaltet**.\nSchalte zuerst dein Handy ein."))
                .setEphemeral(true).queue();
            return;
        }

        PhoneManager.Contract c = PhoneManager.getContract(guildId, userId);
        if (c == null) {
            event.replyEmbeds(EmbedFactory.build("📸 Citygram",
                "❌ Du hast noch keine **Rufnummer**.\nSchließe zuerst einen Vertrag ab."))
                .setEphemeral(true).queue();
            return;
        }

        Role cgRole = guild.getRoleById(CITYGRAM_ROLE_ID);
        boolean alreadyActive = cgRole != null && member.getRoles().contains(cgRole);
        if (!alreadyActive && cgRole != null) {
            guild.addRoleToMember(member, cgRole).queue(
                ok  -> log.info("[Citygram] Rolle an {} vergeben.", userId),
                err -> log.warn("[Citygram] Rolle konnte nicht vergeben werden: {}", err.getMessage())
            );
        }

        String token = PhoneManager.createSession(guildId, c.phoneNumber);
        String link  = webUrl() + "/citygram?token=" + token;

        event.replyEmbeds(
            EmbedFactory.create()
                .setTitle("📸 Citygram")
                .setDescription(alreadyActive
                    ? "✅ Citygram ist bereits aktiviert."
                    : "✅ Citygram wurde aktiviert!\n\nDu hast die Citygram-Rolle erhalten.")
                .build()
        ).addComponents(ActionRow.of(
            Button.link(link, "📸 Citygram öffnen")
        )).setEphemeral(true).queue();
    }

    // ── City Chat (legacy) ────────────────────────────────────────────────────

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

        // Session-Token für persönlichen Link
        String token = PhoneManager.createSession(guildId, c.phoneNumber);
        String personalLink = webUrl() + "/city-chat?token=" + token;

        // City-Chat-Rolle vergeben falls noch nicht vorhanden
        Role cityChatRole = guild.getRoleById(CITY_CHAT_ROLE_ID);
        boolean alreadyActivated = cityChatRole != null && member.getRoles().contains(cityChatRole);

        if (!alreadyActivated && cityChatRole != null) {
            guild.addRoleToMember(member, cityChatRole).queue(
                ok -> log.info("[CityChat] Rolle an {} vergeben.", userId),
                err -> log.warn("[CityChat] Rolle konnte nicht vergeben werden: {}", err.getMessage())
            );
        }

        // Ephemere Antwort mit persönlichem Link
        event.replyEmbeds(
            EmbedFactory.create()
                .setTitle("💬 City Chat")
                .setDescription(
                    (alreadyActivated ? "✅ City Chat bereits aktiviert.\n\n" : "✅ City Chat wurde aktiviert!\n\n") +
                    "**Rufnummer:** `" + c.phoneNumber + "`\n\n" +
                    "Dein persönlicher Link ist **7 Tage** gültig.\n" +
                    "⚠️ Teile diesen Link mit **niemandem**.")
                .build()
        ).addComponents(ActionRow.of(
            Button.link(personalLink, "💬 City Chat öffnen")
        )).setEphemeral(true).queue();

        log.info("[CityChat] {} hat City Chat geöffnet (aktiviert={})", userId, !alreadyActivated);
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

        if ("handy:citygram_activate".equals(cid)) {
            Guild guild    = event.getGuild();
            Member member  = event.getMember();
            String userId  = event.getUser().getId();
            Role cgRole    = guild.getRoleById(CITYGRAM_ROLE_ID);
            if (cgRole != null && member != null && !member.getRoles().contains(cgRole)) {
                guild.addRoleToMember(member, cgRole).queue(
                    ok  -> log.info("[Citygram] Rolle an {} vergeben.", userId),
                    err -> log.warn("[Citygram] Rolle Fehler: {}", err.getMessage())
                );
            }
            event.replyEmbeds(EmbedFactory.build("📸 Citygram",
                "✅ **Citygram wurde aktiviert!**\n\nÖffne Citygram über den Kanal-Link."))
                .setEphemeral(true).queue();
            return;
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

            // Alte Nummer vor der Änderung merken (für City-Chat-Migration)
            PhoneManager.Contract oldContract = PhoneManager.getContract(guildId, userId);
            String oldPhone = oldContract != null ? oldContract.phoneNumber : null;

            PhoneManager.Contract c = PhoneManager.regenerateNumber(guildId, userId);
            if (c == null) {
                event.replyEmbeds(EmbedFactory.build("🔄 Neue Nummer",
                    "❌ Fehler — kein aktiver Vertrag gefunden."))
                    .setEphemeral(true).queue();
                return;
            }

            // City-Chat-Daten auf neue Nummer migrieren
            if (oldPhone != null && !oldPhone.equals(c.phoneNumber)) {
                de.pcrp.bot.web.CityChatMigration.migrate(guildId, oldPhone, c.phoneNumber);
            }

            BankManager.setBalance(guildId, userId, balance - NEUE_NR_PREIS);
            BankManager.addTransaction(guildId, userId, "HANDY_NUMMER_WECHSEL", NEUE_NR_PREIS, null);

            event.replyEmbeds(
                EmbedFactory.create()
                    .setTitle("🔄 Neue Nummer generiert")
                    .setDescription(
                        "✅ Deine alte Nummer wurde gelöscht.\n\n" +
                        "**Neue Rufnummer:** `" + c.phoneNumber + "`\n\n" +
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
                    "📞 **Deine Rufnummer:** `" + c.phoneNumber + "`\n\n" +
                    "💰 **Erstgebühr:** 1.000$ (sofort abgezogen)\n" +
                    "💳 **Monatliche Gebühr:** 1.000$ (automatisch)")
                .build()
        ).setEphemeral(true).queue();
        log.info("[Handy] {} hat Vertrag abgeschlossen: {}", userId, c.phoneNumber);
    }
}
