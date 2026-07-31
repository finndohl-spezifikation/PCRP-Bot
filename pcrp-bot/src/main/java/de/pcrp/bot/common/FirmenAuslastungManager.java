package de.pcrp.bot.common;

import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.entities.MessageEmbed;
import net.dv8tion.jda.api.entities.Role;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Firmen-Auslastung: Festes Panel-Embed im Firmen-Kanal. Zeigt für jede Firmen-Rolle
 * einen Balken mit der Anzahl der angestellten Mitglieder (Rollen-Träger, ohne Bots).
 *
 * Das Panel wird nach Bot-Start einmalig gepostet (Duplikat-Schutz via PanelHelper)
 * und aktualisiert sich danach automatisch alle 30 Minuten in-place.
 */
public final class FirmenAuslastungManager {

    private static final Logger log = LoggerFactory.getLogger(FirmenAuslastungManager.class);

    /** Kanal für das Firmen-Auslastungs-Panel. */
    public static final long PANEL_CHANNEL_ID = 1529636620310020096L;

    /** Alle Firmen-Rollen — Auslastung = Mitglieder mit dieser Rolle. */
    private static final long[] FIRMEN_ROLLEN = {
        1529636326264279072L, 1529636328847708282L, 1529636330127233124L,
        1529636330810642464L, 1529636332077318315L, 1529636333633667173L,
        1529636334526926890L, 1529636335462121514L, 1529636337307619480L,
        1529636338515841168L, 1529636340411662446L, 1529636346086555792L,
        1529636347650904308L
    };

    private static final String TITLE = "🏢 Firmen-Auslastung — Paradise City Roleplay";

    private static final ScheduledExecutorService scheduler =
        Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "firmen-auslastung-scheduler");
            t.setDaemon(true);
            return t;
        });

    private static volatile boolean refreshStarted = false;

    private FirmenAuslastungManager() {}

    /** Nach Bot-Start: Panel einmalig posten + Auto-Refresh starten. */
    public static void init(Guild guild) {
        String guildId = guild.getId();
        String key = panelKey(guildId);
        TextChannel ch = guild.getTextChannelById(PANEL_CHANNEL_ID);
        if (ch == null) { log.warn("[FirmenAuslastung] Kanal nicht gefunden."); return; }
        PanelHelper.post(ch, key, TITLE, () -> sendPanel(ch, key, guild));

        if (!refreshStarted) {
            refreshStarted = true;
            scheduler.scheduleAtFixedRate(() -> refreshPanel(guild), 30, 30, TimeUnit.MINUTES);
            log.info("[FirmenAuslastung] Auto-Refresh gestartet (alle 30 Min).");
        }
    }

    private static String panelKey(String guildId) {
        return "panel-firmen-auslastung-v1-" + guildId;
    }

    private static void sendPanel(TextChannel ch, String key, Guild guild) {
        ch.sendMessageEmbeds(buildEmbed(guild))
            .queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[FirmenAuslastung] Panel konnte nicht gesendet werden.", err); PanelHelper.onFailed(key); });
    }

    /** Aktualisiert das bestehende Panel in-place (oder sendet neu, falls gelöscht). */
    private static void refreshPanel(Guild guild) {
        String key = panelKey(guild.getId());
        String stored = DataStore.readString(key);
        if (stored == null || stored.isBlank()) return;
        String msgId = stored.trim();
        if (msgId.contains("|")) msgId = msgId.split("\\|", 2)[0].trim();

        TextChannel ch = guild.getTextChannelById(PANEL_CHANNEL_ID);
        if (ch == null) return;
        ch.retrieveMessageById(msgId).queue(
            msg -> msg.editMessageEmbeds(buildEmbed(guild)).queue(
                ok -> log.debug("[FirmenAuslastung] Panel aktualisiert."),
                err -> log.warn("[FirmenAuslastung] Embed-Update fehlgeschlagen.", err)),
            err -> {
                log.info("[FirmenAuslastung] Panel-Nachricht nicht mehr vorhanden – sende neu.");
                sendPanel(ch, key, guild);
            }
        );
    }

    private static MessageEmbed buildEmbed(Guild guild) {
        int max = 0;
        int[] counts = new int[FIRMEN_ROLLEN.length];
        for (int i = 0; i < FIRMEN_ROLLEN.length; i++) {
            Role role = guild.getRoleById(FIRMEN_ROLLEN[i]);
            int c = 0;
            if (role != null) {
                for (Member m : guild.getMembersWithRoles(role)) {
                    if (!m.getUser().isBot()) c++;
                }
            }
            counts[i] = c;
            if (c > max) max = c;
        }

        StringBuilder desc = new StringBuilder("__**Aktuelle Firmen-Auslastung**__\n\n");
        for (int i = 0; i < FIRMEN_ROLLEN.length; i++) {
            desc.append("<@&").append(FIRMEN_ROLLEN[i]).append(">\n");
            desc.append("`").append(bar(counts[i], max)).append("` **")
                .append(counts[i]).append("** Angestellte\n\n");
        }
        desc.append("━━━━━━━━━━━━━━━━━━━━━━\n\n");
        desc.append("🔄 Aktualisiert automatisch alle 30 Minuten.");

        return EmbedFactory.create()
            .setTitle(TITLE)
            .setDescription(desc.toString())
            .build();
    }

    /** Balken-Darstellung — Länge relativ zur höchsten Rolle (max 12 Blöcke). */
    private static String bar(int count, int max) {
        final int WIDTH = 12;
        int filled = max > 0 ? Math.round((float) count * WIDTH / max) : 0;
        return "█".repeat(filled) + "░".repeat(WIDTH - filled);
    }
}
