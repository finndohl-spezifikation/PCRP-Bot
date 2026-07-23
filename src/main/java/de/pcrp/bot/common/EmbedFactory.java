package de.pcrp.bot.common;

import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.entities.MessageEmbed;

import java.awt.Color;
import java.time.Instant;

/**
 * Zentrale Stelle für alle Embeds des Bots.
 * Regeln:
 *  - Jedes Embed ist IMMER dunkelorange (0xCC5500).
 *  - Niemals Footer-Texte. Embeds bleiben clean.
 *    Ausnahme: Bot-Neustart-Embed bekommt ein winzig-kleines Java-Logo unten links.
 * Alle Embeds müssen über diese Factory erstellt werden.
 */
public final class EmbedFactory {

    /** Dunkelorange – die einzige erlaubte Embed-Farbe. */
    public static final Color DARK_ORANGE = new Color(0xCC, 0x55, 0x00);

    private EmbedFactory() {}

    /** Leerer Builder in der Standardfarbe. */
    public static EmbedBuilder create() {
        return new EmbedBuilder().setColor(DARK_ORANGE);
    }

    /** Fertiges Embed aus Titel + Beschreibung. */
    public static MessageEmbed build(String title, String description) {
        return create()
                .setTitle(title)
                .setDescription(description)

                .build();
    }

    /**
     * Builder mit winzig-kleinem Icon unten links (Footer-Icon ohne sichtbaren Text).
     * Wird ausschließlich für das Bot-Neustart-Embed verwendet – die einzige Ausnahme
     * von der „kein Footer"-Regel, explizit für Bot-Neustarts gewünscht.
     */
    public static EmbedBuilder createWithFooterIcon(String iconUrl) {
        return create().setFooter("\u200b", iconUrl); // unsichtbares Zeichen als Text
    }
}
