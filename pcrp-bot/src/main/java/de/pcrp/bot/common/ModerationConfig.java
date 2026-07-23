package de.pcrp.bot.common;

/**
 * Zentrale Konfiguration für das Moderationssystem.
 */
public final class ModerationConfig {

    /** Inhaber – hat keinerlei Einschränkungen und wird bei Aktivitätswarnungen gepingt. */
    public static final long OWNER_ID = 1259265007791636540L;

    /** Auto-Rolle – wird jedem neuen Mitglied beim Beitritt zugewiesen. */
    public static final long AUTO_ROLE_ID = 1529636301907689486L;

    /** Kanal für Aktivitätswarnungen (Anti-Nuke, Eigenwerbung usw.). */
    public static final long ALERT_CHANNEL_ID = 1529636455079608431L;

    // ── Spamschutz ────────────────────────────────────────────────────────────
    /** Mehr als X Nachrichten in SpamWindowMs → Spamverdacht. */
    public static final int SPAM_MESSAGE_LIMIT = 7;
    /** Zeitfenster in Millisekunden für den Spamschutz. */
    public static final long SPAM_WINDOW_MS = 10_000L;
    /** Timeout-Dauer beim 2. Spam-Verstoß. */
    public static final long SPAM_TIMEOUT_MINUTES = 10L;

    // ── Anti-Nuke (Massenlöschung) ────────────────────────────────────────────
    /** Ab so vielen Löschungen innerhalb von MassDeleteWindowMs gilt es als Nuke-Versuch. */
    public static final int MASS_DELETE_LIMIT = 3;
    /** Zeitfenster in Millisekunden für die Massenlöschungs-Erkennung. */
    public static final long MASS_DELETE_WINDOW_MS = 60_000L;

    /** 14 Tage Timeout bei Nuke-Verdacht und Eigenwerbung. */
    public static final long PROTECTION_TIMEOUT_DAYS = 14L;

    /** Ping des Inhabers für Aktivitätswarnungen. */
    public static String ownerMention() {
        return "<@" + OWNER_ID + ">";
    }

    private ModerationConfig() {}
}
