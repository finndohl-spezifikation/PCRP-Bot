package de.pcrp.bot.common;

import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Führt täglich um 12:00 Uhr Berliner Zeit die Lotto-Ziehung durch
 * und postet das Ergebnis als normale Nachricht im Ziehungs-Kanal.
 */
public final class LottoScheduler {

    private static final Logger log = LoggerFactory.getLogger(LottoScheduler.class);
    private static final ZoneId ZONE = ZoneId.of("Europe/Berlin");
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("dd.MM.yyyy");

    private static final long DRAW_CHANNEL_ID = 1490890318214860890L;

    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "lotto-scheduler");
        t.setDaemon(true);
        return t;
    });

    public void start() {
        long delaySeconds = secondsUntilNoon();
        log.info("[Lotto] Erste Ziehung in {} Minuten.", delaySeconds / 60);
        scheduler.scheduleAtFixedRate(this::runDraw, delaySeconds, 86_400, TimeUnit.SECONDS);
    }

    private long secondsUntilNoon() {
        ZonedDateTime now  = ZonedDateTime.now(ZONE);
        ZonedDateTime noon = now.toLocalDate().atTime(12, 0).atZone(ZONE);
        if (!now.isBefore(noon)) noon = noon.plusDays(1);
        return Duration.between(now, noon).getSeconds();
    }

    private void runDraw() {
        try {
            Guild guild = BotContext.getGuild();
            if (guild == null) { log.warn("[Lotto] Guild nicht verfügbar."); return; }

            LottoManager.DrawResult result = LottoManager.draw(guild.getId());
            String date = LocalDate.now(ZONE).format(DATE_FMT);

            TextChannel ch = guild.getTextChannelById(DRAW_CHANNEL_ID);
            if (ch == null) { log.warn("[Lotto] Ziehungs-Kanal nicht gefunden."); return; }

            String msg;
            if (result.winnerId() == null) {
                msg = "🎰 **Lotto-Ziehung | " + date + "**\n\n" +
                      "Heute hat niemand einen Lottoschein eingelöst — kein Gewinner.\n" +
                      "💰 Neuer Jackpot: **" + LottoManager.formatAmount(result.nextJackpot()) + "**";
            } else {
                String mention = "<@" + result.winnerId() + ">";
                msg = "🎰 **Lotto-Ziehung | " + date + "**\n\n" +
                      "🏆 Gewinner: " + mention + "\n" +
                      "💰 Gewinn: **" + LottoManager.formatAmount(result.jackpot()) + "**\n" +
                      "🎟️ Teilnehmer: " + result.participantCount() + "\n\n" +
                      "Herzlichen Glückwunsch! 🎉 Der Gewinn wurde deinem Inventar gutgeschrieben.\n" +
                      "💰 Neuer Jackpot morgen: **" + LottoManager.formatAmount(result.nextJackpot()) + "**";
            }

            ch.sendMessage(msg).queue(
                ok  -> log.info("[Lotto] Ziehungsergebnis gepostet."),
                err -> log.error("[Lotto] Fehler beim Posten.", err)
            );
        } catch (Exception e) {
            log.error("[Lotto] Fehler bei der Ziehung.", e);
        }
    }

    public void stop() { scheduler.shutdownNow(); }
}
