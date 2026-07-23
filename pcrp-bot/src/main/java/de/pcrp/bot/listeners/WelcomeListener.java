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
 *  - Einlader → neues Mitglied-Mapping persistent in DataStore speichern.
 *  - Beim Verlassen: gespeichertes Mapping lesen, Einlader im Log nennen.
 */
public class WelcomeListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(WelcomeListener.class);
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
                    inviter != null ? inviter.getIdLong() : 0L,
                    inviter != null ? inviter.getName()   : "Unbekannt",
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
        Invite inv  = event.getInvite();
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

        // Mitgliederanzahl ohne Bots (inkl. gerade beigetretener Nutzer)
        long memberCount = guild.getMembers().stream().filter(m -> !m.getUser().isBot()).count();

        // ── Willkommens-Embed ─────────────────────────────────────
        TextChannel welcomeChannel = guild.getTextChannelById(LoggingConfig.WELCOME_CHANNEL_ID);
        if (welcomeChannel != null) {
            welcomeChannel.sendMessageEmbeds(
                EmbedFactory.create()
                    .setTitle("👋 Willkommen auf Paradise City Roleplay!")
                    .setDescription(
                        user.getAsMention() + "\n\n" +
                        "Willkommen auf **Paradise City Roleplay**,\n" +
                        "du bist unser **" + memberCount + ".** Mitglied! 🎉")
                    .setThumbnail(user.getEffectiveAvatarUrl())
                    .setTimestamp(Instant.now())
                    .build()
            ).queue();
        }

        // ── Invite-Tracker ────────────────────────────────────────
        guild.retrieveInvites().queue(currentInvites -> {
            Map<String, InviteData> oldCache = cache.getOrDefault(guild.getIdLong(), new ConcurrentHashMap<>());

            // Benutzte Einladung finden: Uses-Zahl hat sich erhöht
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

            // Mapping persistieren
            final String inviterName    = usedInvite != null ? usedInvite.inviterName    : "Unbekannt";
            final String inviterMention = usedInvite != null ? usedInvite.inviterMention : "Unbekannt";
            final long   inviterId      = usedInvite != null ? usedInvite.inviterId      : 0L;
            final int    finalUses      = newUses;

            if (usedInvite != null)
                persistInvitedBy(guild.getIdLong(), user.getIdLong(), inviterId, inviterName, inviterMention, finalUses);

            // ── Invite-Log: Beitritt ──────────────────────────────
            TextChannel inviteLog = guild.getTextChannelById(LoggingConfig.INVITE_LOG_CHANNEL_ID);
            if (inviteLog != null) {
                inviteLog.sendMessageEmbeds(
                    EmbedFactory.create()
                        .setTitle("📨 Neues Mitglied")
                        .setDescription(
                            "**" + user.getName() + "** hat den Server betreten\n\n" +
                            "Er wurde von **" + inviterName + "** eingeladen,\n" +
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

        // ── Invite-Log: Verlassen ─────────────────────────────────
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
        JsonObject root = JsonParser.parseString(raw).getAsJsonObject();
        JsonElement el  = root.get(String.valueOf(memberId));
        if (el == null || !el.isJsonObject()) return null;
        JsonObject obj = el.getAsJsonObject();
        return new InviterRecord(
            obj.get("inviterId").getAsLong(),
            obj.get("inviterName").getAsString(),
            obj.get("inviterMention").getAsString()
        );
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
