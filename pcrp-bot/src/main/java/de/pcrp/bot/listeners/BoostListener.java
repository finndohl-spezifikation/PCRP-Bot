package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.events.guild.member.update.GuildMemberUpdateBoostTimeEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BoostListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(BoostListener.class);

    @Override
    public void onGuildMemberUpdateBoostTime(GuildMemberUpdateBoostTimeEvent event) {
        // Nur neue Boosts abfangen (war null, ist jetzt gesetzt)
        if (event.getOldTimeBoosted() != null || event.getNewTimeBoosted() == null) return;

        Guild  guild  = event.getGuild();
        Member member = event.getMember();
        int    boosts = guild.getBoostCount();

        long reward;
        if      (boosts >= 10) reward = 100_000L;
        else if (boosts >= 5)  reward =  10_000L;
        else                   reward =   5_000L;

        String formatted = String.format("%,d", reward).replace(",", ".");

        // DM an den Booster
        BotLogger.tryDm(member.getUser(), EmbedFactory.create()
            .setTitle("💜 Vielen Dank für deinen Server Boost!")
            .setDescription(
                "Du hast **Paradise City Roleplay** mit einem Boost unterstützt!\n\n" +
                "🎁 **Deine Belohnung: " + formatted + " $**\n\n" +
                "Das Geld wird dir in Kürze in-game gutgeschrieben.\n" +
                "Bei Fragen wende dich an das Serverteam.")
            .build());

        // Mod-Log
        BotLogger.logModeration(guild,
            "💜 Server Boost",
            "**Mitglied:** " + member.getAsMention() + " (`" + member.getId() + "`)\n" +
            "**Belohnung:** " + formatted + " $\n" +
            "**Server-Boosts gesamt:** " + boosts);

        log.info("[Boost] {} hat geboostet – Belohnung: {} $", member.getUser().getName(), formatted);
    }
}
