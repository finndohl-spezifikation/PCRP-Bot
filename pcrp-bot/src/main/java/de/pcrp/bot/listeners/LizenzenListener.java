package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
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

import java.util.Optional;

/**
 * Lizenzen vorzeigen: Festes Panel-Embed im Ausweis-Kanal mit zwei Buttons
 * (🪪 Ausweis anzeigen / 🚗 Führerschein anzeigen). Ein Button öffnet eine
 * Suchleiste (Modal), dort gibt man einen Namen ein — anschließend wird der
 * passende Lizenz-Link (nur der Link, keine Daten) angezeigt.
 */
public class LizenzenListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(LizenzenListener.class);

    private static final String BTN_AUSWEIS       = "liz-show-ausweis";
    private static final String BTN_FUEHRERSCHEIN = "liz-show-fuehrerschein";
    private static final String MODAL_AUSWEIS     = "liz-modal-ausweis";
    private static final String MODAL_FUEHRERSCHEIN = "liz-modal-fuehrerschein";
    private static final String INPUT_NAME        = "liz-name";

    /** Postet das Panel-Embed einmalig nach Bot-Start (Duplikat-Schutz via DataStore). */
    public static void postPanel(Guild guild) {
        String key = "panel-lizenzen-v1-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(RoleConfig.AUSWEIS_CHANNEL_ID);
        if (ch == null) { log.warn("[Lizenzen] Ausweis-Kanal nicht gefunden."); return; }
        PanelHelper.post(ch, key, "🪪 Lizenzen anzeigen", () -> sendPanel(ch, key));
    }

    private static void sendPanel(TextChannel ch, String key) {
        ch.sendMessageEmbeds(EmbedFactory.build(
            "🪪 Lizenzen anzeigen",
            "Wähle unten aus, welche Lizenz du vorzeigen möchtest.\n" +
            "Anschließend gibst du den Namen der Person ein und erhältst den Anzeige-Link."))
            .addActionRow(
                Button.primary(BTN_AUSWEIS,       "🪪 Ausweis Anzeigen"),
                Button.primary(BTN_FUEHRERSCHEIN, "🚗 Führerschein Anzeigen"))
            .queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Lizenzen] Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
    }

    // ── Buttons: Modal mit Suchleiste öffnen ─────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        String cid = event.getComponentId();
        switch (cid) {
            case BTN_AUSWEIS -> {
                Modal modal = Modal.create(MODAL_AUSWEIS, "🪪 Ausweis anzeigen")
                    .addComponents(ActionRow.of(
                        TextInput.create(INPUT_NAME, "Name der Person", TextInputStyle.SHORT)
                            .setPlaceholder("Charaktername, z. B. Max Mustermann")
                            .setMinLength(1).setMaxLength(64)
                            .setRequired(true).build()))
                    .build();
                event.replyModal(modal).queue();
            }
            case BTN_FUEHRERSCHEIN -> {
                Modal modal = Modal.create(MODAL_FUEHRERSCHEIN, "🚗 Führerschein anzeigen")
                    .addComponents(ActionRow.of(
                        TextInput.create(INPUT_NAME, "Name der Person", TextInputStyle.SHORT)
                            .setPlaceholder("Charaktername, z. B. Max Mustermann")
                            .setMinLength(1).setMaxLength(64)
                            .setRequired(true).build()))
                    .build();
                event.replyModal(modal).queue();
            }
        }
    }

    // ── Modal-Submit: Namen auflösen → Link anzeigen ─────────────────────────

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        String mid = event.getModalId();
        if (!MODAL_AUSWEIS.equals(mid) && !MODAL_FUEHRERSCHEIN.equals(mid)) return;
        if (event.getGuild() == null) return;

        boolean ausweis = MODAL_AUSWEIS.equals(mid);
        String name = event.getValue(INPUT_NAME) != null
            ? event.getValue(INPUT_NAME).getAsString().trim() : "";

        if (name.isEmpty()) {
            event.replyEmbeds(EmbedFactory.build("❌ Kein Name",
                "Bitte gib einen Namen ein.")).setEphemeral(true).queue();
            return;
        }

        // deferReply: Die Namenssuche liest pro Mitglied Dokumente — mehr Zeitfenster als 3s
        event.deferReply(true).queue();

        Member target = resolveMember(event.getGuild(), name);
        if (target == null) {
            event.getHook().sendMessageEmbeds(EmbedFactory.build("❌ Nicht gefunden",
                "Es wurde kein Spieler mit dem Namen **" + name + "** gefunden."))
                .setEphemeral(true).queue();
            return;
        }

        String guildId = event.getGuild().getId();
        String userId  = target.getId();
        String displayName = target.getEffectiveName();

        if (ausweis) {
            if (DocumentsManager.getAusweis(guildId, userId).isEmpty()) {
                event.getHook().sendMessageEmbeds(EmbedFactory.build("ℹ️ Kein Ausweis",
                    "**" + displayName + "** hat aktuell keinen im Bot gespeicherten Ausweis."))
                    .setEphemeral(true).queue();
                return;
            }
            String url = DocumentsManager.ausweisViewUrl(userId);
            event.getHook().sendMessage("🪪 Ausweis – [Lizenz hier Öffnen](" + url + ")").setEphemeral(true).queue();
        } else {
            if (DocumentsManager.getFuehrerschein(guildId, userId).isEmpty()) {
                event.getHook().sendMessageEmbeds(EmbedFactory.build("ℹ️ Kein Führerschein",
                    "**" + displayName + "** hat aktuell keinen im Bot gespeicherten Führerschein."))
                    .setEphemeral(true).queue();
                return;
            }
            String url = DocumentsManager.fuehrerscheinViewUrl(userId);
            event.getHook().sendMessage("🚗 Führerschein – [Lizenz hier Öffnen](" + url + ")").setEphemeral(true).queue();
        }
    }

    /**
     * Sucht einen Spieler über seinen CHARAKTERNAMEN (Vorname + Nachname aus
     * Ausweis/Führerschein) — keine Discord-Namen. Exakt oder Teil-Treffer
     * (Suchleisten-Verhalten). Spieler ohne gespeichertes Dokument haben
     * keinen Charakternamen und werden nicht gefunden.
     */
    private static Member resolveMember(Guild guild, String name) {
        String q = norm(name);
        if (q.isEmpty()) return null;
        for (Member m : guild.getMembers()) {
            if (m.getUser().isBot()) continue;
            String userId = m.getId();

            String first = null, last = null;
            Optional<DocumentsManager.Ausweis> a =
                DocumentsManager.getAusweis(guild.getId(), userId);
            if (a.isPresent()) {
                first = norm(a.get().vorname);
                last  = norm(a.get().nachname);
            } else {
                Optional<DocumentsManager.Fuehrerschein> f =
                    DocumentsManager.getFuehrerschein(guild.getId(), userId);
                if (f.isPresent()) {
                    first = norm(f.get().vorname);
                    last  = norm(f.get().nachname);
                }
            }
            if (first == null) continue;

            String full = (first + " " + last).trim();
            if (full.equals(q)) return m;                       // exakt
            if (full.startsWith(q) || full.contains(q)) return m; // Teil-Treffer
            if (first.startsWith(q) || last.startsWith(q)) return m;
            String[] parts = q.split("\\s+");
            if (parts.length >= 2
                    && first.startsWith(parts[0])
                    && last.startsWith(parts[parts.length - 1])) return m; // "Max Must"
        }
        return null;
    }

    private static String norm(String s) {
        return s == null ? "" : s.toLowerCase().trim();
    }
}
