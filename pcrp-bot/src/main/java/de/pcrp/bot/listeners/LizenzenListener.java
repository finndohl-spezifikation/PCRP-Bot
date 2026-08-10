package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.EntitySelectInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.EntitySelectMenu;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

/**
 * Lizenzen vorzeigen: Festes Panel-Embed im Ausweis-Kanal mit zwei Buttons
 * (🪪 Ausweis anzeigen / 🚗 Führerschein anzeigen). Ein Button öffnet im Kanal
 * eine EPHEMERE Nachricht mit einer Suchleiste (Discord-User-Suche) — kein
 * Modal-Popup. Man sucht/tippt den Namen der Person ein, wählt sie aus und
 * bestätigt; danach wird die ephemere Nachricht mit dem Lizenz-Link aktualisiert
 * (nur der Link, keine Daten).
 */
public class LizenzenListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(LizenzenListener.class);

    private static final String BTN_AUSWEIS       = "liz-show-ausweis";
    private static final String BTN_FUEHRERSCHEIN = "liz-show-fuehrerschein";
    private static final String SELECT_AUSWEIS     = "liz-select-ausweis";
    private static final String SELECT_FUEHRERSCHEIN = "liz-select-fuehrerschein";

    /** Panel-Beschreibung — als Konstante, damit Duplikat-Check und Sendetext nie auseinanderdriften. */
    private static final String PANEL_DESC =
        "Wähle unten aus, welche Lizenz du vorzeigen möchtest.\n" +
        "Anschließend öffnet sich eine Suchleiste — gib den Charakternamen ein und du erhältst den Anzeige-Link.";

    /** Postet das Panel-Embed einmalig nach Bot-Start (Duplikat-Schutz via DataStore). */
    public static void postPanel(Guild guild) {
        String key = "panel-lizenzen-v2-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(RoleConfig.AUSWEIS_CHANNEL_ID);
        if (ch == null) { log.warn("[Lizenzen] Ausweis-Kanal nicht gefunden."); return; }
        // Beschreibung mitgeben: Der Duplikat-Check erkennt nur ein Embed mit gleichem
        // Titel UND gleichem Text als "schon vorhanden" — das alte v1-Embed (gleicher
        // Titel, alter Text) blockt das frische Panel also nicht.
        PanelHelper.post(ch, key, "🪪 Lizenzen anzeigen", PANEL_DESC, () -> sendPanel(ch, key));
    }

    private static void sendPanel(TextChannel ch, String key) {
        ch.sendMessageEmbeds(EmbedFactory.build("🪪 Lizenzen anzeigen", PANEL_DESC))
            .addActionRow(
                Button.primary(BTN_AUSWEIS,       "🪪 Ausweis Anzeigen"),
                Button.primary(BTN_FUEHRERSCHEIN, "🚗 Führerschein Anzeigen"))
            .queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Lizenzen] Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
    }

    // ── Buttons: ephemere Kanal-Nachricht mit Suchleiste öffnen ───────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        String cid = event.getComponentId();
        switch (cid) {
            case BTN_AUSWEIS -> {
                event.replyEmbeds(EmbedFactory.build(
                    "🪪 Ausweis anzeigen",
                    "Suche den Spieler unten über die Suchleiste und wähle ihn aus."))
                    .addActionRow(
                        EntitySelectMenu.create(SELECT_AUSWEIS, EntitySelectMenu.SelectTarget.USER)
                            .setPlaceholder("Spieler suchen und auswählen…")
                            .setMinValues(1).setMaxValues(1).build())
                    .setEphemeral(true).queue();
            }
            case BTN_FUEHRERSCHEIN -> {
                event.replyEmbeds(EmbedFactory.build(
                    "🚗 Führerschein anzeigen",
                    "Suche den Spieler unten über die Suchleiste und wähle ihn aus."))
                    .addActionRow(
                        EntitySelectMenu.create(SELECT_FUEHRERSCHEIN, EntitySelectMenu.SelectTarget.USER)
                            .setPlaceholder("Spieler suchen und auswählen…")
                            .setMinValues(1).setMaxValues(1).build())
                    .setEphemeral(true).queue();
            }
        }
    }

    // ── Auswahl bestätigt: ephemere Nachricht mit dem Link aktualisieren ──────

    @Override
    public void onEntitySelectInteraction(EntitySelectInteractionEvent event) {
        String cid = event.getComponentId();
        boolean ausweis;
        if (SELECT_AUSWEIS.equals(cid))             ausweis = true;
        else if (SELECT_FUEHRERSCHEIN.equals(cid))  ausweis = false;
        else return;
        if (event.getGuild() == null) return;

        List<Member> selected = event.getMentions().getMembers();
        if (selected.isEmpty()) { event.deferEdit().queue(); return; }

        Member target = selected.get(0);
        String guildId = event.getGuild().getId();
        String userId  = target.getId();
        String displayName = target.getEffectiveName();

        if (ausweis) {
            if (DocumentsManager.getAusweis(guildId, userId).isEmpty()) {
                event.editMessageEmbeds(EmbedFactory.build("ℹ️ Kein Ausweis",
                    "**" + displayName + "** hat aktuell keinen im Bot gespeicherten Ausweis."))
                    .setComponents().queue();
                return;
            }
            String url = DocumentsManager.ausweisViewUrl(userId);
            event.editMessageEmbeds(EmbedFactory.build("🪪 Ausweis anzeigen",
                "**" + displayName + "**\n\n[Lizenz hier Öffnen](" + url + ")"))
                .setComponents().queue();
        } else {
            if (DocumentsManager.getFuehrerschein(guildId, userId).isEmpty()) {
                event.editMessageEmbeds(EmbedFactory.build("ℹ️ Kein Führerschein",
                    "**" + displayName + "** hat aktuell keinen im Bot gespeicherten Führerschein."))
                    .setComponents().queue();
                return;
            }
            // Entzogene Führerscheine werden nicht mehr angezeigt, bis sie zurückgegeben werden
            if (LapdDashManager.isLicenseRevoked(event.getGuild().getIdLong(), userId)) {
                event.editMessageEmbeds(EmbedFactory.build("🚫 Führerschein entzogen",
                    "Der Führerschein von **" + displayName + "** wurde entzogen und ist bis auf Weiteres ungültig."))
                    .setComponents().queue();
                return;
            }
            String url = DocumentsManager.fuehrerscheinViewUrl(userId);
            event.editMessageEmbeds(EmbedFactory.build("🚗 Führerschein anzeigen",
                "**" + displayName + "**\n\n[Lizenz hier Öffnen](" + url + ")"))
                .setComponents().queue();
        }
    }
}
