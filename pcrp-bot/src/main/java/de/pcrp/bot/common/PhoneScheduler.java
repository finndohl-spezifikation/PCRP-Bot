package de.pcrp.bot.common;

import net.dv8tion.jda.api.entities.Guild;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.*;
import java.util.List;
import java.util.concurrent.*;

/**
 * Zieht monatlich 1.000$ von allen aktiven Handy-Vertragshaltern ab.
 * Läuft jeden Monat am 1. um 08:00 Uhr.
 */
public class PhoneScheduler {

    private static final Logger log = LoggerFactory.getLogger(PhoneScheduler.class);
    private static final long   MONTHLY_FEE = 1_000L;

    private final ScheduledExecutorService scheduler =
        Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "phone-billing");
            t.setDaemon(true);
            return t;
        });

    public void start() {
        long initialDelay = secondsUntilNextBilling();
        long period       = 30L * 24 * 3600; // 30 Tage in Sekunden

        scheduler.scheduleAtFixedRate(this::runBilling, initialDelay, period, TimeUnit.SECONDS);
        log.info("[PhoneScheduler] Nächste Abrechnung in {} Stunden.",
            initialDelay / 3600);
    }

    private void runBilling() {
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            log.warn("[PhoneScheduler] Kein Guild verfügbar — Abrechnung übersprungen.");
            return;
        }

        String guildId = guild.getId();
        List<PhoneManager.Contract> contracts = PhoneManager.getAllContracts(guildId);
        log.info("[PhoneScheduler] Starte monatliche Abrechnung — {} Verträge.", contracts.size());

        int charged = 0;
        for (PhoneManager.Contract c : contracts) {
            long balance = BankManager.getBalance(guildId, c.userId);
            if (balance >= MONTHLY_FEE) {
                BankManager.setBalance(guildId, c.userId, balance - MONTHLY_FEE);
                BankManager.addTransaction(guildId, c.userId, "HANDY_MONATSGEBÜHR", MONTHLY_FEE, null);
                charged++;
                log.debug("[PhoneScheduler] 1.000$ von {} ({}) abgezogen.", c.displayName(), c.userId);

                // Nutzer im Log informieren
                try {
                    guild.retrieveMemberById(c.userId).queue(member -> {
                        member.getUser().openPrivateChannel().queue(dm ->
                            dm.sendMessageEmbeds(EmbedFactory.build(
                                "📱 Handy-Abrechnung",
                                "Deine monatliche Handyrechnung von **1.000$** wurde von deinem Konto abgezogen.\n\n" +
                                "📞 Rufnummer: **" + c.phoneNumber + "**"
                            )).queue(null, ignored -> {})
                        , ignored -> {});
                    }, ignored -> {});
                } catch (Exception ignored) {}
            } else {
                log.warn("[PhoneScheduler] {} hat nicht genug Geld für die Monatsgebühr.", c.userId);
            }
        }

        log.info("[PhoneScheduler] Abrechnung abgeschlossen — {} von {} Verträgen bezahlt.",
            charged, contracts.size());
    }

    /** Sekunden bis zum nächsten 1. des Monats, 08:00 Uhr (Europe/Berlin). */
    private static long secondsUntilNextBilling() {
        ZoneId zone = ZoneId.of("Europe/Berlin");
        ZonedDateTime now  = ZonedDateTime.now(zone);
        ZonedDateTime next = now.withDayOfMonth(1)
            .withHour(8).withMinute(0).withSecond(0).withNano(0);
        if (!next.isAfter(now)) next = next.plusMonths(1);
        return Duration.between(now, next).getSeconds();
    }
}
