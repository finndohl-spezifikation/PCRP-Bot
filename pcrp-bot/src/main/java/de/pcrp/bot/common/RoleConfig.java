package de.pcrp.bot.common;

/**
 * Rollen-IDs für das Einreise-System.
 */
public final class RoleConfig {

    /** Rollen, die bei legaler Einreise vergeben werden. */
    public static final long[] LEGAL_ROLES = {
        1529636299563077734L,
        1529636300410454186L,
        1529636303304392807L,
        1529636307687440705L,
        1529636314398458039L,
        1529636320157237379L,
        1529636321948074155L,   // ← Legaler Bewohner (wichtig: für /ausweis-Prüfung)
        1529636327669371034L,
        1529636348426850520L,
        1529636350268149963L,
        1529636353879572663L
    };

    /** Rollen, die bei illegaler Einreise vergeben werden. */
    public static final long[] ILLEGAL_ROLES = {
        1529636299563077734L,
        1529636300410454186L,
        1529636303304392807L,
        1529636306190078113L,
        1529636307687440705L,
        1529636314398458039L,
        1529636320157237379L,
        1529636322568966156L,
        1529636353879572663L
    };

    /** Legaler-Bewohner-Rolle – Voraussetzung für /ausweis. */
    public static final long LEGAL_RESIDENT_ROLE_ID = 1529636321948074155L;

    /** Kanal, in dem /ausweis ausgeführt werden darf. */
    public static final long AUSWEIS_CHANNEL_ID = 1529636558628716586L;

    /** Registrations-Bonus in Münzen (Economy). */
    public static final long REGISTRATION_REWARD = 5_000L;

    private RoleConfig() {}
}
