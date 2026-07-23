package de.pcrp.bot.common;

import net.dv8tion.jda.api.JDA;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;

/**
 * Gemeinsamer JDA-Kontext für Web-Server und Bot.
 * Wird beim ReadyEvent gesetzt.
 */
public final class BotContext {

    private static volatile JDA jda;

    private BotContext() {}

    public static void setJda(JDA jda) {
        BotContext.jda = jda;
    }

    public static JDA getJda() {
        return jda;
    }

    public static boolean isReady() {
        return jda != null;
    }

    /** Gibt den ersten (und einzigen) Server zurück, oder null wenn JDA noch nicht ready. */
    public static Guild getGuild() {
        if (jda == null || jda.getGuilds().isEmpty()) return null;
        return jda.getGuilds().get(0);
    }

    /**
     * Sucht ein Mitglied anhand des Discord-Nutzernamens (case-insensitiv).
     * Kompatibel mit alten (Name#0000) und neuen Nutzernamen (name).
     */
    public static Member findMemberByUsername(String username) {
        Guild guild = getGuild();
        if (guild == null || username == null) return null;
        String lower = username.toLowerCase().trim();
        return guild.getMembers().stream()
            .filter(m -> !m.getUser().isBot())
            .filter(m -> m.getUser().getName().equalsIgnoreCase(lower)
                      || m.getUser().getAsTag().equalsIgnoreCase(username.trim()))
            .findFirst().orElse(null);
    }
}
