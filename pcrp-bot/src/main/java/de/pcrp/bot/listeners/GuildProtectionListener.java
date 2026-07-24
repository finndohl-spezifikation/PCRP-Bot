package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.audit.ActionType;
import net.dv8tion.jda.api.audit.AuditLogEntry;
import net.dv8tion.jda.api.entities.*;
import net.dv8tion.jda.api.entities.channel.concrete.*;
import net.dv8tion.jda.api.entities.channel.middleman.GuildChannel;
import net.dv8tion.jda.api.events.channel.ChannelDeleteEvent;
import net.dv8tion.jda.api.events.guild.member.GuildMemberJoinEvent;
import net.dv8tion.jda.api.events.role.RoleDeleteEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.awt.Color;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Anti-Nuke-Schutz:
 *  - Fremde Bots werden beim Beitritt sofort permanent gebannt
 *    (DM an Einladenden + Aktivitätswarnung + Moderations-Log)
 *  - Massenhaftes Löschen von Kanälen/Kategorien/Rollen →
 *    14 Tage Timeout, DM, Alert, Log und automatische Wiederherstellung
 * Der Inhaber ist von allen Einschränkungen ausgenommen.
 */
public class GuildProtectionListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(GuildProtectionListener.class);

    // Lösch-Tracking pro Nutzer: userId → Liste von Zeitstempeln (ms)
    private final ConcurrentHashMap<Long, List<Long>> deletions = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<Long, Long>       flagged   = new ConcurrentHashMap<>();

    // ── Fremde Bots ───────────────────────────────────────────────────────────

    @Override
    public void onGuildMemberJoin(GuildMemberJoinEvent event) {
        Member member = event.getMember();
        if (!member.getUser().isBot()) return;
        if (member.getIdLong() == event.getJDA().getSelfUser().getIdLong()) return;

        Guild guild = event.getGuild();

        // Einladenden via Audit-Log ermitteln
        guild.retrieveAuditLogs().type(ActionType.BOT_ADD).limit(5).queue(entries -> {
            AuditLogEntry entry = recentEntry(entries);
            User inviter = entry != null ? entry.getUser() : null;

            // Bot permanent bannen
            guild.ban(member.getUser(), 0, TimeUnit.SECONDS).reason("Anti-Nuke: Fremde Bots sind nicht erlaubt.").queue(
                ok -> {
                    if (inviter != null && inviter.getIdLong() != ModerationConfig.OWNER_ID) {
                        BotLogger.tryDm(inviter, EmbedFactory.build(
                            "Anti-Nuke-Schutz aktiv",
                            "Auf **PCRP** ist der Anti-Nuke-Schutz aktiv – **keine fremden Bots** erlaubt.\n\n" +
                            "Der Bot **" + member.getUser().getName() + "** wurde **permanent gebannt**."));
                    }

                    String inviterInfo = inviter != null
                        ? inviter.getAsMention() + " | " + inviter.getName() + " (`" + inviter.getId() + "`)"
                        : "Unbekannt";

                    BotLogger.sendAlert(guild,
                        "Aktivitätswarnung – Anti-Nuke (Fremder Bot)",
                        "**Bot:** " + member.getUser().getName() + " (`" + member.getId() + "`) – **permanent gebannt**.\n" +
                        "**Eingeladen von:** " + inviterInfo);

                    BotLogger.logModeration(guild,
                        "🤖 Anti-Nuke – Fremder Bot gebannt",
                        "**Bot:** " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                        "**Eingeladen von:** " + inviterInfo + "\n" +
                        "**Aktionen:** Permanenter Bann · DM an Einladenden · Aktivitätswarnung");
                },
                err -> log.error("Fremder Bot konnte nicht gebannt werden.", err));
        });
    }

    // ── Kanallöschung – sofortige Reaktion ───────────────────────────────────

    @Override
    public void onChannelDelete(ChannelDeleteEvent event) {
        if (!(event.getChannel() instanceof GuildChannel)) return;
        GuildChannel channel = (GuildChannel) event.getChannel();
        Guild guild = channel.getGuild();

        guild.retrieveAuditLogs().type(ActionType.CHANNEL_DELETE).limit(1).queue(entries -> {
            AuditLogEntry entry = recentEntry(entries);
            if (entry == null) return;
            long executorId = entry.getUserIdLong();
            if (executorId == ModerationConfig.OWNER_ID) return;
            if (executorId == guild.getSelfMember().getIdLong()) return;

            // Kanal immer sofort wiederherstellen
            restoreChannel(channel);

            // Nur einmal pro 10-Minuten-Fenster bestrafen (verhindert Spam bei Massenl.)
            boolean alreadyFlagged = isFlagged(executorId);
            flagged.put(executorId, Instant.now().toEpochMilli());
            registerDeletion(executorId);

            if (!alreadyFlagged) {
                punish(guild, entry.getUser(), "Kanäle/Kategorien");
            }
        });
    }

    // ── Massenlöschung – Rollen ───────────────────────────────────────────────

    @Override
    public void onRoleDelete(RoleDeleteEvent event) {
        Role  role  = event.getRole();
        Guild guild = event.getGuild();

        guild.retrieveAuditLogs().type(ActionType.ROLE_DELETE).limit(1).queue(entries -> {
            AuditLogEntry entry = recentEntry(entries);
            if (entry == null) return;
            long executorId = entry.getUserIdLong();
            if (executorId == ModerationConfig.OWNER_ID) return;
            if (executorId == guild.getSelfMember().getIdLong()) return;

            boolean triggered = registerDeletion(executorId);
            if (triggered || isFlagged(executorId)) {
                if (triggered) punish(guild, entry.getUser(), "Rollen");
                restoreRole(guild, role);
            }
        });
    }

    // ── Wiederherstellen ──────────────────────────────────────────────────────

    private void restoreChannel(GuildChannel channel) {
        Guild guild = channel.getGuild();

        if (channel instanceof Category cat) {
            guild.createCategory(cat.getName())
                .setPosition(cat.getPosition())
                .queue(null, err -> log.warn("Kategorie konnte nicht wiederhergestellt werden.", err));

        } else if (channel instanceof VoiceChannel voice) {
            guild.createVoiceChannel(voice.getName())
                .setPosition(voice.getPosition())
                .setParent(voice.getParentCategory())
                .setBitrate(voice.getBitrate())
                .setUserlimit(voice.getUserLimit())
                .queue(null, err -> log.warn("Sprachkanal konnte nicht wiederhergestellt werden.", err));

        } else if (channel instanceof TextChannel text) {
            guild.createTextChannel(text.getName())
                .setPosition(text.getPosition())
                .setParent(text.getParentCategory())
                .setTopic(text.getTopic())
                .setNSFW(text.isNSFW())
                .setSlowmode(text.getSlowmode())
                .queue(null, err -> log.warn("Textkanal konnte nicht wiederhergestellt werden.", err));
        }
    }

    private void restoreRole(Guild guild, Role role) {
        Color color = role.getColor(); // null = Standardfarbe
        guild.createRole()
            .setName(role.getName())
            .setPermissions(role.getPermissionsRaw())
            .setColor(color)
            .setHoisted(role.isHoisted())
            .setMentionable(role.isMentionable())
            .queue(null, err -> log.warn("Rolle konnte nicht wiederhergestellt werden.", err));
    }

    // ── Bestrafung ────────────────────────────────────────────────────────────

    private void punish(Guild guild, User executor, String whatWasDeleted) {
        Member member = guild.getMemberById(executor.getIdLong());
        if (member != null)
            guild.timeoutFor(member, Duration.ofDays(ModerationConfig.PROTECTION_TIMEOUT_DAYS)).queue();

        BotLogger.tryDm(executor, EmbedFactory.build(
            "Serverschutz aktiv",
            "Auf **PCRP** ist der Serverschutz aktiv.\n\n" +
            "Du hast in kürzester Zeit mehrere **" + whatWasDeleted + "** gelöscht und daher " +
            "einen **14-tägigen Timeout** erhalten, bis entschieden wurde, ob dies legitim war.\n\n" +
            "Wenn alles passt, wird der Timeout **sofort aufgehoben**."));

        BotLogger.sendAlert(guild,
            "Aktivitätswarnung – Anti-Nuke (Massenlöschung)",
            "**Nutzer:** " + executor.getAsMention() + " (`" + executor.getId() + "`)\n" +
            "**Versuch:** Mehrere **" + whatWasDeleted + "** in kürzester Zeit gelöscht.\n" +
            "**Maßnahmen:** 14 Tage Timeout · DM gesendet · Inhalte werden wiederhergestellt.");

        BotLogger.logModeration(guild,
            "💣 Anti-Nuke – Massenlöschung gestoppt",
            "**Nutzer:** " + executor.getAsMention() + " | " + executor.getName() + " (`" + executor.getId() + "`)\n" +
            "**Gelöschte Objekte:** " + whatWasDeleted + "\n" +
            "**Aktionen:** 14 Tage Timeout · DM gesendet · Wiederherstellung gestartet · Alert gesendet");
    }

    // ── Hilfs-Methoden ────────────────────────────────────────────────────────

    /** Registriert eine Löschung und gibt true zurück, wenn die Schwelle überschritten wurde. */
    private boolean registerDeletion(long userId) {
        long now  = Instant.now().toEpochMilli();
        List<Long> list = deletions.computeIfAbsent(userId, k -> Collections.synchronizedList(new ArrayList<>()));
        synchronized (list) {
            list.add(now);
            list.removeIf(t -> now - t > ModerationConfig.MASS_DELETE_WINDOW_MS);
            if (list.size() >= ModerationConfig.MASS_DELETE_LIMIT && !isFlagged(userId)) {
                flagged.put(userId, now);
                return true;
            }
        }
        return false;
    }

    private boolean isFlagged(long userId) {
        Long since = flagged.get(userId);
        return since != null && Instant.now().toEpochMilli() - since < 10 * 60 * 1000L;
    }

    /** Gibt den ersten Audit-Log-Eintrag zurück, der jünger als 30 Sekunden ist. */
    private static AuditLogEntry recentEntry(List<AuditLogEntry> entries) {
        Instant cutoff = Instant.now().minusSeconds(30);
        return entries.stream()
            .filter(e -> e.getTimeCreated().toInstant().isAfter(cutoff))
            .findFirst()
            .orElse(null);
    }
}
