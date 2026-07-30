package de.pcrp.bot.common;

import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.entities.Role;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

/**
 * Stunden-Lohn-System: Zahlt automatisch Lohn an Spieler, die eine Lohn-Rolle besitzen,
 * solange die Lobby geöffnet ist.
 *
 * Lohn-Rollen:
 *   1529636350268149963 → Arbeitslos (1.000$)
 *   1529636351321051279 → Normal Angestellt (3.000$)
 *   1529636352432275616 → Befehlsposten (3.600$)
 *   1529636353204031609 → Leitungsebene (4.000$)
 */
public final class LohnManager {

    private static final Logger log = LoggerFactory.getLogger(LohnManager.class);

    /** Rolle → Stundenlohn */
    public static final Map<Long, Long> WAGE_ROLES = Map.of(
        1529636350268149963L, 1_000L,
        1529636351321051279L, 3_000L,
        1529636352432275616L, 3_600L,
        1529636353204031609L, 4_000L
    );

    /** Lohn-Panel-Kanal (Lohnliste). */
    public static final long LOHN_CHANNEL_ID = 1529636602349879366L;

    private static boolean lobbyOpen = false;
    private static ScheduledFuture<?> wageTask = null;
    private static final ScheduledExecutorService scheduler =
        Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "lohn-scheduler");
            t.setDaemon(true);
            return t;
        });

    private LohnManager() {}

    // ── Lobby-Steuerung ───────────────────────────────────────────────────────

    /** Wird aufgerufen wenn die Lobby geöffnet wird. Startet den Stunden-Lohn. */
    public static void onLobbyOpen() {
        lobbyOpen = true;
        // Stündliche Auszahlung starten
        if (wageTask == null || wageTask.isCancelled()) {
            wageTask = scheduler.scheduleAtFixedRate(
                LohnManager::payAllWages,
                1, 1, TimeUnit.HOURS);
            log.info("[Lohn] Lobby geöffnet – Lohn-Scheduler gestartet (stündlich).");
        }
    }

    /** Wird aufgerufen wenn die Lobby geschlossen wird. Stoppt den Lohn. */
    public static void onLobbyClose() {
        lobbyOpen = false;
        if (wageTask != null && !wageTask.isCancelled()) {
            wageTask.cancel(false);
            log.info("[Lohn] Lobby geschlossen – Lohn-Scheduler gestoppt.");
        }
    }

    /** Gibt zurück ob die Lobby aktuell offen ist. */
    public static boolean isLobbyOpen() {
        return lobbyOpen;
    }

    // ── Auszahlungen ──────────────────────────────────────────────────────────

    /** Zahlt ALLEN Mitgliedern mit Lohn-Rolle ihren Stundenlohn aus. */
    public static void payAllWages() {
        Guild guild = BotContext.getGuild();
        if (guild == null) {
            log.warn("[Lohn] Kein Guild verfügbar – Auszahlung übersprungen.");
            return;
        }
        if (!lobbyOpen) {
            log.debug("[Lohn] Lobby geschlossen – Auszahlung übersprungen.");
            return;
        }

        String guildId = guild.getId();
        int paid = 0;

        for (Map.Entry<Long, Long> entry : WAGE_ROLES.entrySet()) {
            long roleId = entry.getKey();
            long amount = entry.getValue();
            Role role = guild.getRoleById(roleId);
            if (role == null) continue;

            for (Member member : guild.getMembersWithRoles(role)) {
                if (member.getUser().isBot()) continue;
                // Nur die höchste Lohn-Rolle zahlen
                long wage = getWageForMember(member);
                if (wage == amount) {
                    BankManager.setBalance(guildId, member.getId(),
                        BankManager.getBalance(guildId, member.getId()) + amount);
                    BankManager.addTransaction(guildId, member.getId(), "LOHN", amount, null);
                    paid++;
                }
            }
        }

        log.info("[Lohn] Stündliche Auszahlung: {} Spieler bezahlt.", paid);
    }

    /** Zahlt EINEM Mitglied sofort seinen Lohn (für Erstauszahlung bei Rollen-Verteilung). */
    public static void payImmediate(Guild guild, Member member) {
        if (member.getUser().isBot()) return;
        long wage = getWageForMember(member);
        if (wage <= 0) return;

        String guildId = guild.getId();
        BankManager.setBalance(guildId, member.getId(),
            BankManager.getBalance(guildId, member.getId()) + wage);
        BankManager.addTransaction(guildId, member.getId(), "LOHN", wage, null);
        log.info("[Lohn] Sofort-Auszahlung an {} ({}): {} $", member.getEffectiveName(), member.getId(), wage);
    }

    /** Ermittelt den höchsten Lohn, der einem Mitglied zusteht (höchste Lohn-Rolle gewinnt). */
    public static long getWageForMember(Member member) {
        long highest = 0;
        for (Map.Entry<Long, Long> entry : WAGE_ROLES.entrySet()) {
            if (entry.getValue() > highest && member.getRoles().stream()
                    .anyMatch(r -> r.getIdLong() == entry.getKey())) {
                highest = entry.getValue();
            }
        }
        return highest;
    }

    /** Prüft ob eine Rolle eine Lohn-Rolle ist. */
    public static boolean isWageRole(long roleId) {
        return WAGE_ROLES.containsKey(roleId);
    }
}
