package de.pcrp.bot.common;

/**
 * Kanal-IDs für das Log-System.
 */
public final class LoggingConfig {

    /** Alles rund um den Server (Guild, Kanäle, Einladungen, Voice). */
    public static final long SERVER_LOG_CHANNEL_ID     = 1529636412628930723L;

    /** Alles rund um Moderation (Bans, Timeouts, Wortfilter, Spam…). */
    public static final long MODERATION_LOG_CHANNEL_ID = 1529636417636929707L;

    /** Bot-Neustarts (Neustart-Embed). */
    public static final long PLAYER_LOG_CHANNEL_ID     = 1529636419071639735L;

    /** Servermitglieder-Logs: Beitritt, Verlassen, Nickname-Änderung. */
    public static final long MEMBER_LOG_CHANNEL_ID     = 1529636422389076039L;

    /** Alles rund um Nachrichten (gelöscht, bearbeitet, Massenlöschung). */
    public static final long MESSAGE_LOG_CHANNEL_ID    = 1529636425337667714L;

    /** Alles rund um Rollen (erstellt, gelöscht, geändert, vergeben/entzogen). */
    public static final long ROLE_LOG_CHANNEL_ID       = 1529636428370280509L;

    /** Alles rund um Gelder/Wirtschaft (für spätere Implementierung). */
    public static final long MONEY_LOG_CHANNEL_ID      = 1529636430362574968L;

    /** Alles rund um Tickets und Transkripte (für spätere Implementierung). */
    public static final long TICKET_LOG_CHANNEL_ID     = 1529636431784317019L;

    /** Einwohner-Meldeamt Panel (Charakter-Erstellung). */
    public static final long MELDEAMT_CHANNEL_ID           = 1529636473035292832L;

    /** Startpunkt-Panel (Flughafen / Hafen). */
    public static final long STARTPUNKT_CHANNEL_ID         = 1529636476038414386L;

    /** Starter-Paket-Panel (Fahrzeuge & Startgeld). */
    public static final long STARTER_PAKET_CHANNEL_ID      = 1529636476961161277L;

    /** RP-Spiel-Einstellungen-Panel (Spieleranzeige, Minimap). */
    public static final long RP_EINSTELLUNGEN_CHANNEL_ID   = 1529636478236495983L;

    /** Serverregelwerk-Panel (2 Embeds). */
    public static final long REGELWERK_CHANNEL_ID           = 1529636481117851692L;

    /** Fraktionsregelwerk-Panel. */
    public static final long FRAKTIONSREGELWERK_CHANNEL_ID  = 1529636484070772868L;

    /** Safe-Zones-Panel. */
    public static final long SAFEZONES_CHANNEL_ID           = 1529636485454889111L;

    /** Willkommensnachrichten bei Serverbeitritt. */
    public static final long WELCOME_CHANNEL_ID        = 1529636467096293586L;

    /** Abschiedsnachrichten beim Verlassen. */
    public static final long GOODBYE_CHANNEL_ID        = 1529636469524791296L;

    /** Einladungs-Tracker (Beitritt und Verlassen). */
    public static final long INVITE_LOG_CHANNEL_ID     = 1529636468476088480L;

    /**
     * Java-Logo URL – winzig-kleines Icon unten links im Bot-Neustart-Embed.
     * (Ausnahme von der „kein Footer"-Regel, explizit für Bot-Neustarts gewünscht.)
     */
    public static final String JAVA_LOGO_URL =
        "https://upload.wikimedia.org/wikipedia/en/thumb/3/30/Java_programming_language_logo.svg/121px-Java_programming_language_logo.svg.png";

    private LoggingConfig() {}
}
