package de.pcrp.bot.common;

/**
 * Zentrale Statistik-Quelle für die Info-Seite (/info).
 *
 * commandCount wird automatisch gesetzt wenn buildCommands() aufgerufen wird.
 * Die anderen Werte müssen manuell aktualisiert werden wenn Systeme/Dashboards
 * hinzugefügt oder entfernt werden.
 */
public final class BotStats {

    private BotStats() {}

    /** Wird von Main.StartupListener gesetzt — immer aktuell */
    public static volatile int commandCount = 0;

    /**
     * Moderations-Systeme:
     * 1. Ban/Unban-System
     * 2. Timeout-System
     * 3. Verwarnungs-System
     * 4. Aktivitätscheck-System
     * 5. Server-Schutz (Anti-Raid/Anti-Spam)
     * 6. Logging-System
     * 7. Ticket-System
     * 8. Einreise-Sperre
     */
    public static final int MODERATION_SYSTEMS = 8;

    /**
     * Web-Dashboards:
     * 1. Einwohner-Meldeamt (/)
     * 2. Personalausweis (/ausweis)
     * 3. Lotto (/lotto)
     * 4. Rubbellos (/rubbellos)
     * 5. City Chat (/city-chat)
     */
    public static final int WEB_DASHBOARDS = 5;
}
