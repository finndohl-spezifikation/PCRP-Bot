package de.pcrp.bot.listeners;

import com.google.gson.*;
import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.*;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.guild.GuildReadyEvent;
import net.dv8tion.jda.api.events.guild.invite.*;
import net.dv8tion.jda.api.events.guild.member.*;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Willkommen, Verabschiedung und Einladungs-Tracker.
 *
 * Invite-Tracker-Logik:
 *  - Beim Startup alle Einladungen cachen (uses-Anzahl pro Code).
 *  - Beim Beitritt: neuen Stand abrufen, geänderten Code = benutzte Einladung.
 *  - Einlader wird gepingt; bekommt +1.000 Münzen.
 *  - Mapping "wer hat wen eingeladen" wird persistent gespeichert.
 *  - Beim Verlassen: Einlader wird im Invite-Log genannt.
 *    Die 1.000 Münzen werden dem Einlader wieder abgezogen.
 */
public class WelcomeListener extends ListenerAdapter {

    private static final Logger log  = LoggerFactory.getLogger(WelcomeListener.class);
    private static final Gson   GSON = new GsonBuilder().setPrettyPrinting().create();

    // Invite-Cache: guildId → (inviteCode → InviteData)
    private final Map<Long, Map<String, InviteData>> cache = new ConcurrentHashMap<>();

    // ════════════════════════════════════════════════════════════
    //  STARTUP – Invite-Cache befüllen
    // ════════════════════════════════════════════════════════════

    @Override
    public void onGuildReady(GuildReadyEvent event) {
        refreshCache(event.getGuild());
    }

    private void refreshCache(Guild guild) {
        guild.retrieveInvites().queue(invites -> {
            Map<String, InviteData> map = new ConcurrentHashMap<>();
            for (Invite inv : invites) {
                User inviter = inv.getInviter();
                map.put(inv.getCode(), new InviteData(
                    inv.getUses(),
                    inviter != null ? inviter.getIdLong()    : 0L,
                    inviter != null ? inviter.getName()      : "Unbekannt",
                    inviter != null ? inviter.getAsMention() : "Unbekannt"
                ));
            }
            cache.put(guild.getIdLong(), map);
            log.info("[Invite-Cache] '{}' – {} Einladungen geladen.", guild.getName(), map.size());
        }, err -> log.warn("[Invite-Cache] Konnte nicht geladen werden für '{}'.", guild.getName(), err));
    }

    // ════════════════════════════════════════════════════════════
    //  INVITE EVENTS – Cache aktuell halten
    // ════════════════════════════════════════════════════════════

    @Override
    public void onGuildInviteCreate(GuildInviteCreateEvent event) {
        Invite inv   = event.getInvite();
        User inviter = inv.getInviter();
        cache.computeIfAbsent(event.getGuild().getIdLong(), k -> new ConcurrentHashMap<>())
             .put(inv.getCode(), new InviteData(
                 inv.getUses(),
                 inviter != null ? inviter.getIdLong()    : 0L,
                 inviter != null ? inviter.getName()      : "Unbekannt",
                 inviter != null ? inviter.getAsMention() : "Unbekannt"
             ));
    }

    @Override
    public void onGuildInviteDelete(GuildInviteDeleteEvent event) {
        Map<String, InviteData> map = cache.get(event.getGuild().getIdLong());
        if (map != null) map.remove(event.getCode());
    }

    // ════════════════════════════════════════════════════════════
    //  BEITRITT
    // ════════════════════════════════════════════════════════════

    @Override
    public void onGuildMemberJoin(GuildMemberJoinEvent event) {
        Guild  guild  = event.getGuild();
        Member member = event.getMember();
        User   user   = member.getUser();
        if (user.isBot()) return;

        // ── Auto-Rolle ────────────────────────────────────────────
        Role autoRole = guild.getRoleById(ModerationConfig.AUTO_ROLE_ID);
        if (autoRole != null) {
            guild.addRoleToMember(member, autoRole).queue(
                ok  -> log.info("[AutoRole] {} → Rolle vergeben.", user.getName()),
                err -> log.warn("[AutoRole] Konnte Rolle nicht vergeben an {}.", user.getName(), err)
            );
        } else {
            log.warn("[AutoRole] Rolle {} nicht gefunden auf '{}'.", ModerationConfig.AUTO_ROLE_ID, guild.getName());
        }

        // ── Mitgliederanzahl ohne Bots ────────────────────────────
        long memberCount = guild.getMembers().stream().filter(m -> !m.getUser().isBot()).count();

        // ── Willkommens-Embed ─────────────────────────────────────
        TextChannel welcomeChannel = guild.getTextChannelById(LoggingConfig.WELCOME_CHANNEL_ID);
        if (welcomeChannel != null) {
            welcomeChannel.sendMessageEmbeds(
                EmbedFactory.create()
                    .setTitle("👋 Neues Mitglied")
                    .setDescription(
                        user.getAsMention() + "\n\n" +
                        "Willkommen auf **Paradise City Roleplay**,\n" +
                        "du bist unser **" + memberCount + ".** Mitglied! 🎉")
                    .setThumbnail(user.getEffectiveAvatarUrl())
                    .setTimestamp(Instant.now())
                    .build()
            ).queue();
        }

        // ── Invite-Tracker: welcher Invite wurde benutzt ──────────
        guild.retrieveInvites().queue(currentInvites -> {
            Map<String, InviteData> oldCache = cache.getOrDefault(guild.getIdLong(), new ConcurrentHashMap<>());

            InviteData usedInvite = null;
            int        newUses    = 0;
            for (Invite inv : currentInvites) {
                InviteData old = oldCache.get(inv.getCode());
                if (old != null && inv.getUses() > old.uses) {
                    usedInvite = old;
                    newUses    = inv.getUses();
                    break;
                }
            }

            // Cache aktualisieren
            Map<String, InviteData> newMap = new ConcurrentHashMap<>();
            for (Invite inv : currentInvites) {
                User inviter = inv.getInviter();
                newMap.put(inv.getCode(), new InviteData(
                    inv.getUses(),
                    inviter != null ? inviter.getIdLong()    : 0L,
                    inviter != null ? inviter.getName()      : "Unbekannt",
                    inviter != null ? inviter.getAsMention() : "Unbekannt"
                ));
            }
            cache.put(guild.getIdLong(), newMap);

            final String inviterName    = usedInvite != null ? usedInvite.inviterName    : "Unbekannt";
            final String inviterMention = usedInvite != null ? usedInvite.inviterMention : "Unbekannt";
            final long   inviterId      = usedInvite != null ? usedInvite.inviterId      : 0L;
            final int    finalUses      = newUses;

            // Mapping + Economy persistieren
            if (usedInvite != null && inviterId != 0L) {
                persistInvitedBy(guild.getIdLong(), user.getIdLong(), inviterId, inviterName, inviterMention, finalUses);
                EconomyStore.addCoins(guild.getIdLong(), inviterId, EconomyStore.INVITE_REWARD);
                log.info("[Economy] +{} für {} (Einladung von {}).",
                    EconomyStore.INVITE_REWARD, user.getName(), inviterName);
            }

            // ── Invite-Log: Beitritt (+ Ping des Einladers) ───────
            TextChannel inviteLog = guild.getTextChannelById(LoggingConfig.INVITE_LOG_CHANNEL_ID);
            if (inviteLog != null) {
                String content = inviterId != 0L ? inviterMention : ""; // Ping außerhalb des Embeds
                inviteLog.sendMessage(content)
                    .addEmbeds(
                        EmbedFactory.create()
                            .setTitle("📨 Neues Mitglied")
                            .setDescription(
                                "**" + user.getName() + "** hat den Server betreten.\n\n" +
                                "Er wurde von " + inviterMention + " eingeladen,\n" +
                                "der jetzt **" + finalUses + " Einladung" + (finalUses == 1 ? "" : "en") + "** hat.")
                            .setThumbnail(user.getEffectiveAvatarUrl())
                            .setTimestamp(Instant.now())
                            .build()
                    ).queue();
            }
        }, err -> log.warn("[Invite-Tracker] Einladungen nicht abrufbar beim Beitritt von '{}'.", user.getName(), err));
    }

    // ════════════════════════════════════════════════════════════
    //  VERLASSEN
    // ════════════════════════════════════════════════════════════

    @Override
    public void onGuildMemberRemove(GuildMemberRemoveEvent event) {
        Guild guild = event.getGuild();
        User  user  = event.getUser();
        if (user.isBot()) return;

        // Mitgliederanzahl ohne Bots (Mitglied ist bereits weg)
        long memberCount = guild.getMembers().stream().filter(m -> !m.getUser().isBot()).count();

        // ── Abschieds-Embed ───────────────────────────────────────
        TextChannel goodbyeChannel = guild.getTextChannelById(LoggingConfig.GOODBYE_CHANNEL_ID);
        if (goodbyeChannel != null) {
            goodbyeChannel.sendMessageEmbeds(
                EmbedFactory.create()
                    .setTitle("👋 Mitglied verlassen")
                    .setDescription(
                        "**" + user.getName() + "**\n" +
                        "hat **Paradise City Roleplay** verlassen.\n\n" +
                        "Es befinden sich noch **" + memberCount + " Mitglieder** auf dem Server.")
                    .setThumbnail(user.getEffectiveAvatarUrl())
                    .setTimestamp(Instant.now())
                    .build()
            ).queue();
        }

        // ── Invite-Log: Verlassen + Economy-Abzug ─────────────────
        InviterRecord record = loadInvitedBy(guild.getIdLong(), user.getIdLong());
        TextChannel inviteLog = guild.getTextChannelById(LoggingConfig.INVITE_LOG_CHANNEL_ID);
        if (inviteLog != null) {
            String inviterStr = record != null ? record.inviterMention : "Unbekannt";
            inviteLog.sendMessageEmbeds(
                EmbedFactory.create()
                    .setTitle("📤 Mitglied verlassen")
                    .setDescription(
                        "**" + user.getName() + "** hat den Server verlassen.\n\n" +
                        "Er wurde von " + inviterStr + " eingeladen.")
                    .setThumbnail(user.getEffectiveAvatarUrl())
                    .setTimestamp(Instant.now())
                    .build()
            ).queue();
        }

        // Economy: Einladungs-Bonus wieder abziehen
        if (record != null && record.inviterId != 0L) {
            EconomyStore.subtractCoins(guild.getIdLong(), record.inviterId, EconomyStore.INVITE_REWARD);
            log.info("[Economy] -{} für {} (verlassen: {}).",
                EconomyStore.INVITE_REWARD, record.inviterName, user.getName());
        }
    }

    // ════════════════════════════════════════════════════════════
    //  PERSISTENZ – wer hat wen eingeladen
    // ════════════════════════════════════════════════════════════

    private static String inviteFile(long guildId) { return "invite-by-" + guildId + ".json"; }

    private static void persistInvitedBy(long guildId, long memberId,
                                          long inviterId, String inviterName,
                                          String inviterMention, int uses) {
        String raw  = DataStore.readString(inviteFile(guildId));
        JsonObject root = raw != null ? JsonParser.parseString(raw).getAsJsonObject() : new JsonObject();
        JsonObject entry = new JsonObject();
        entry.addProperty("inviterId",      inviterId);
        entry.addProperty("inviterName",    inviterName);
        entry.addProperty("inviterMention", inviterMention);
        entry.addProperty("uses",           uses);
        root.add(String.valueOf(memberId), entry);
        DataStore.writeString(inviteFile(guildId), GSON.toJson(root));
    }

    private static InviterRecord loadInvitedBy(long guildId, long memberId) {
        String raw = DataStore.readString(inviteFile(guildId));
        if (raw == null) return null;
        try {
            JsonObject root = JsonParser.parseString(raw).getAsJsonObject();
            JsonElement el  = root.get(String.valueOf(memberId));
            if (el == null || !el.isJsonObject()) return null;
            JsonObject obj = el.getAsJsonObject();
            return new InviterRecord(
                obj.get("inviterId").getAsLong(),
                obj.get("inviterName").getAsString(),
                obj.get("inviterMention").getAsString()
            );
        } catch (Exception e) {
            log.warn("[Invite-Persistenz] Fehler beim Lesen für Mitglied {}.", memberId, e);
            return null;
        }
    }

    // ════════════════════════════════════════════════════════════
    //  DATENKLASSEN
    // ════════════════════════════════════════════════════════════

    private static class InviteData {
        final int    uses;
        final long   inviterId;
        final String inviterName;
        final String inviterMention;

        InviteData(int uses, long inviterId, String inviterName, String inviterMention) {
            this.uses           = uses;
            this.inviterId      = inviterId;
            this.inviterName    = inviterName;
            this.inviterMention = inviterMention;
        }
    }

    private static class InviterRecord {
        final long   inviterId;
        final String inviterName;
        final String inviterMention;

        InviterRecord(long inviterId, String inviterName, String inviterMention) {
            this.inviterId      = inviterId;
            this.inviterName    = inviterName;
            this.inviterMention = inviterMention;
        }
    }
}
