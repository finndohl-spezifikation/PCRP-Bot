package de.pcrp.bot.common;

import net.dv8tion.jda.api.entities.MessageEmbed;

/**
 * Globaler Lockdown-Schalter.
 * <p>
 * Wenn {@code ACTIVE = true}:
 *  - Alle Slash-Commands, Buttons, Selects, Modals und Webseiten sind blockiert
 *    und zeigen immer die Fehlermeldung „Eigentumsrechte noch nicht übergeben".
 * <p>
 * Zum Beenden des Lockdowns: {@code ACTIVE} auf {@code false} setzen und neu deployen.
 */
public final class Lockdown {

    /** true = Lockdown aktiv (Eigentumsrechte wurden noch nicht übergeben). */
    public static volatile boolean ACTIVE = true;

    public static final String ERROR_TITLE = "❌ Fehler";
    public static final String ERROR_TEXT =
        "Die Eigentumsrechte wurden noch nicht von **Walther der Möse** übergeben.";

    /** Embed für Discord-Interaktionen (Commands, Buttons, Selects, Modals). */
    public static MessageEmbed blockedEmbed() {
        return EmbedFactory.create()
            .setTitle(ERROR_TITLE)
            .setDescription(ERROR_TEXT)
            .build();
    }

    /** Einfache HTML-Fehlerseite für alle Webseiten-Aufrufe im Lockdown. */
    public static String webPage() {
        return "<!DOCTYPE html><html lang=\"de\"><head><meta charset=\"utf-8\">"
            + "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            + "<title>" + ERROR_TITLE + "</title><style>"
            + "body{background:#141414;color:#fff;font-family:'Segoe UI',Arial,sans-serif;"
            + "display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center}"
            + ".box{max-width:480px;padding:44px;border:1px solid #2a2a2a;border-radius:14px;background:#1c1c1c}"
            + "h1{color:#cc5500;font-size:26px;margin-bottom:14px}"
            + "p{color:#bbb;font-size:16px;line-height:1.6}"
            + "</style></head><body><div class=\"box\"><h1>" + ERROR_TITLE + "</h1>"
            + "<p>Die Eigentumsrechte wurden noch nicht von <strong>Walther der Möse</strong> übergeben.</p>"
            + "</div></body></html>";
    }

    /** JSON-Antwort für API-Aufrufe im Lockdown. */
    public static String apiJson() {
        return "{\"error\":\"Eigentumsrechte wurden noch nicht von Walther der Möse übergeben.\"}";
    }

    private Lockdown() {}
}
