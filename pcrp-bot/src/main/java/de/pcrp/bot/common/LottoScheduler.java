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
            String date       = LocalDate.now(ZONE).format(DATE_FMT);
            String numStr     = LottoManager.formatNumbers(result.winningNumbers());

            TextChannel ch = guild.getTextChannelById(DRAW_CHANNEL_ID);
            if (ch == null) { log.warn("[Lotto] Ziehungs-Kanal nicht gefunden."); return; }

            StringBuilder sb = new StringBuilder();
            sb.append("🎰 **Lotto-Ziehung | ").append(date).append("**\n\n");
            sb.append("🔢 **Gewinnzahlen:** `").append(numStr).append("`\n");
            sb.append("🎟️ **Teilnehmer:** ").append(result.participantCount()).append("\n\n");

            boolean anyWin = !result.jackpotWinners().isEmpty()
                          || !result.tier5Winners().isEmpty()
                          || !result.tier4Winners().isEmpty();

            if (!anyWin) {
                sb.append("😔 Kein Gewinner heute.\n");
                sb.append("📈 Jackpot steigt auf: **")
                  .append(LottoManager.formatAmount(result.nextJackpot())).append("**");
            } else {
                if (!result.jackpotWinners().isEmpty()) {
                    sb.append("🏆 **JACKPOT (6/6):** ");
                    result.jackpotWinners().forEach(uid -> sb.append("<@").append(uid).append("> "));
                    sb.append("\n💰 Gewinn: **")
                      .append(LottoManager.formatAmount(result.jackpot())).append("** pro Person\n");
                    sb.append("🔄 Jackpot zurückgesetzt auf **")
                      .append(LottoManager.formatAmount(result.nextJackpot())).append("**\n");
                }
                if (!result.tier5Winners().isEmpty()) {
                    sb.append("\n🥈 **5/6 Treffer:** ");
                    result.tier5Winners().forEach(uid -> sb.append("<@").append(uid).append("> "));
                    sb.append("→ **50.000$**\n");
                }
                if (!result.tier4Winners().isEmpty()) {
                    sb.append("\n🥉 **4/6 Treffer:** ");
                    result.tier4Winners().forEach(uid -> sb.append("<@").append(uid).append("> "));
                    sb.append("→ **10.000$**\n");
                }
                if (result.jackpotWinners().isEmpty()) {
                    sb.append("\n💰 Jackpot morgen: **")
                      .append(LottoManager.formatAmount(result.nextJackpot())).append("**");
                }
            }

            ch.sendMessage(sb.toString()).queue(
                ok  -> log.info("[Lotto] Ziehungsergebnis gepostet."),
                err -> log.error("[Lotto] Fehler beim Posten.", err)
            );
        } catch (Exception e) {
            log.error("[Lotto] Fehler bei der Ziehung.", e);
        }
    }

    public void stop() { scheduler.shutdownNow(); }
}
