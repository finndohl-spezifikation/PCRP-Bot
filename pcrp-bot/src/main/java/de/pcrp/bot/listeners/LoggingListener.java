package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.JDA;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.audit.ActionType;
import net.dv8tion.jda.api.audit.AuditLogEntry;
import net.dv8tion.jda.api.entities.*;
import net.dv8tion.jda.api.entities.channel.*;
import net.dv8tion.jda.api.entities.channel.concrete.*;
import net.dv8tion.jda.api.entities.channel.middleman.AudioChannel;
import net.dv8tion.jda.api.entities.channel.middleman.GuildChannel;
import net.dv8tion.jda.api.events.channel.*;
import net.dv8tion.jda.api.events.channel.update.*;
import net.dv8tion.jda.api.events.guild.*;
import net.dv8tion.jda.api.events.guild.invite.*;
import net.dv8tion.jda.api.events.guild.member.*;
import net.dv8tion.jda.api.events.guild.member.update.*;
import net.dv8tion.jda.api.events.guild.update.*;
import net.dv8tion.jda.api.events.guild.voice.*;
import net.dv8tion.jda.api.events.message.*;
import net.dv8tion.jda.api.events.role.*;
import net.dv8tion.jda.api.events.role.update.*;
import net.dv8tion.jda.api.events.session.ReadyEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;

import java.awt.Color;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.function.Consumer;

/**
 * Umfassendes Log-System – protokolliert jeden relevanten Vorgang bis ins Detail.
 *
 * Kanal-Zuordnung:
 *   Server-Logs       → Guild, Kanäle, Einladungen, Voice
 *   Moderations-Logs  → Bans, Timeouts (+ aus ModerationListener/GuildProtectionListener)
 *   Spieler-Logs      → Bot-Neustart, Beitritt, Verlassen, Nickname
 *   Nachrichten-Logs  → Gelöscht, Bearbeitet, Massenlöschung
 *   Rollen-Logs       → Erstellt, Gelöscht, Geändert, Vergaben
 */
public class LoggingListener extends ListenerAdapter {

    // ════════════════════════════════════════════════════════════
    //  SPIELER-LOGS – Bot-Neustart
    // ════════════════════════════════════════════════════════════

    @Override
    public void onReady(ReadyEvent event) {
        JDA  jda = event.getJDA();
        long now = Instant.now().getEpochSecond();

        // Neustart-Embed: Java-Logo klein unten links, keine Discord-Bilder, übersichtliche Felder
        EmbedBuilder embed = EmbedFactory.createWithFooterIcon(LoggingConfig.JAVA_LOGO_URL)
            .setTitle("🟢 PCRP-Bot wurde neugestartet")
            .addField("🤖 Bot",        jda.getSelfUser().getName() + "  (`" + jda.getSelfUser().getId() + "`)", false)
            .addField("📦 Version",    "Java 19  ·  JDA 5.2.2", true)
            .addField("🌐 Server",     String.valueOf(jda.getGuilds().size()), true)
            .addField("🕐 Zeitpunkt",  "<t:" + now + ":F>", false)
;

        for (Guild guild : jda.getGuilds()) {
            TextChannel ch = guild.getTextChannelById(LoggingConfig.PLAYER_LOG_CHANNEL_ID);
            if (ch != null)
                ch.sendMessageEmbeds(embed.build())
                    .addActionRow(
                        Button.primary("status-aktive-systeme", "🛡️ Aktive Systeme"))
                    .queue();
        }
    }

    // ════════════════════════════════════════════════════════════
    //  SERVER-LOGS – Guild-Einstellungen
    // ════════════════════════════════════════════════════════════

    @Override public void onGuildUpdateName(GuildUpdateNameEvent e) {
        serverLog(e.getGuild(), "⚙️ Servername geändert",
            diff("Name", e.getOldName(), e.getNewName())); }

    @Override public void onGuildUpdateIcon(GuildUpdateIconEvent e) {
        serverLog(e.getGuild(), "⚙️ Server-Icon geändert",
            "**Vorher:** " + strOrNone(e.getOldIconUrl()) + "\n**Nachher:** " + strOrNone(e.getNewIconUrl())); }

    @Override public void onGuildUpdateDescription(GuildUpdateDescriptionEvent e) {
        serverLog(e.getGuild(), "⚙️ Server-Beschreibung geändert",
            diff("Beschreibung", e.getOldDescription(), e.getNewDescription())); }

    @Override public void onGuildUpdateVerificationLevel(GuildUpdateVerificationLevelEvent e) {
        serverLog(e.getGuild(), "⚙️ Verifizierungsstufe geändert",
            diff("Stufe", e.getOldVerificationLevel(), e.getNewVerificationLevel())); }

    @Override public void onGuildUpdateExplicitContentLevel(GuildUpdateExplicitContentLevelEvent e) {
        serverLog(e.getGuild(), "⚙️ Explizit-Inhaltsfilter geändert",
            diff("Filter", e.getOldLevel(), e.getNewLevel())); }

    // GuildUpdateDefaultNotificationsEvent existiert in JDA 5.2.x nicht mehr.

    @Override public void onGuildUpdateMFALevel(GuildUpdateMFALevelEvent e) {
        serverLog(e.getGuild(), "⚙️ 2FA-Stufe geändert",
            diff("Stufe", e.getOldMFALevel(), e.getNewMFALevel())); }

    @Override public void onGuildUpdateAfkTimeout(GuildUpdateAfkTimeoutEvent e) {
        serverLog(e.getGuild(), "⚙️ AFK-Timeout geändert",
            diff("Timeout (Sek.)", e.getOldAfkTimeout(), e.getNewAfkTimeout())); }

    @Override public void onGuildUpdateAfkChannel(GuildUpdateAfkChannelEvent e) {
        serverLog(e.getGuild(), "⚙️ AFK-Kanal geändert",
            diff("Kanal",
                e.getOldAfkChannel() != null ? e.getOldAfkChannel().getName() : "—",
                e.getNewAfkChannel() != null ? e.getNewAfkChannel().getName() : "—")); }

    @Override public void onGuildUpdateSystemChannel(GuildUpdateSystemChannelEvent e) {
        serverLog(e.getGuild(), "⚙️ System-Kanal geändert",
            diff("Kanal",
                e.getOldSystemChannel() != null ? e.getOldSystemChannel().getAsMention() : "—",
                e.getNewSystemChannel() != null ? e.getNewSystemChannel().getAsMention() : "—")); }

    @Override public void onGuildUpdateOwner(GuildUpdateOwnerEvent e) {
        serverLog(e.getGuild(), "⚙️ Server-Inhaber geändert",
            diff("Inhaber",
                e.getOldOwner() != null ? e.getOldOwner().getAsMention() : "—",
                e.getNewOwner() != null ? e.getNewOwner().getAsMention() : "—")); }

    @Override public void onGuildUpdateBoostTier(GuildUpdateBoostTierEvent e) {
        serverLog(e.getGuild(), "⚙️ Boost-Stufe geändert",
            diff("Stufe", e.getOldBoostTier(), e.getNewBoostTier())); }

    @Override public void onGuildUpdateLocale(GuildUpdateLocaleEvent e) {
        serverLog(e.getGuild(), "⚙️ Serversprache geändert",
            diff("Sprache", e.getOldValue(), e.getNewValue())); }

    // ── Kanäle ───────────────────────────────────────────────────────────────

    @Override
    public void onChannelCreate(ChannelCreateEvent e) {
        if (!(e.getChannel() instanceof GuildChannel ch)) return;
        withAudit(ch.getGuild(), ActionType.CHANNEL_CREATE, entry ->
            log(ch.getGuild(), LoggingConfig.SERVER_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("📁 Kanal erstellt")
                .setDescription(
                    "**Name:** " + ch.getName() + "\n" +
                    "**Typ:** " + formatChannelType(ch) + "\n" +
                    "**ID:** `" + ch.getId() + "`\n" +
                    auditUser("Erstellt von", entry))

                .build()));
    }

    @Override
    public void onChannelDelete(ChannelDeleteEvent e) {
        if (!(e.getChannel() instanceof GuildChannel ch)) return;
        withAudit(ch.getGuild(), ActionType.CHANNEL_DELETE, entry ->
            log(ch.getGuild(), LoggingConfig.SERVER_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("🗑️ Kanal gelöscht")
                .setDescription(
                    "**Name:** " + ch.getName() + "\n" +
                    "**Typ:** " + formatChannelType(ch) + "\n" +
                    "**ID:** `" + ch.getId() + "`\n" +
                    auditUser("Gelöscht von", entry))

                .build()));
    }

    @Override public void onChannelUpdateName(ChannelUpdateNameEvent e) {
        if (!(e.getChannel() instanceof GuildChannel ch)) return;
        serverLogWithAudit(ch.getGuild(), ActionType.CHANNEL_UPDATE,
            "✏️ Kanal umbenannt – " + e.getNewValue(),
            "**Kanal:** " + ch.getName() + " (`" + ch.getId() + "`)\n" +
            diff("Name", e.getOldValue(), e.getNewValue())); }

    @Override public void onChannelUpdateTopic(ChannelUpdateTopicEvent e) {
        if (!(e.getChannel() instanceof GuildChannel ch)) return;
        serverLog(ch.getGuild(), "✏️ Kanal-Thema geändert",
            "**Kanal:** " + ch.getAsMention() + "\n" +
            diff("Thema", e.getOldValue(), e.getNewValue())); }

    @Override public void onChannelUpdateSlowmode(ChannelUpdateSlowmodeEvent e) {
        if (!(e.getChannel() instanceof GuildChannel ch)) return;
        serverLog(ch.getGuild(), "✏️ Slowmode geändert",
            "**Kanal:** " + ch.getAsMention() + "\n" +
            diff("Slowmode (Sek.)", e.getOldValue(), e.getNewValue())); }

    @Override public void onChannelUpdatePosition(ChannelUpdatePositionEvent e) {
        if (!(e.getChannel() instanceof GuildChannel ch)) return;
        serverLog(ch.getGuild(), "✏️ Kanal-Position geändert",
            "**Kanal:** " + ch.getName() + "\n" +
            diff("Position", e.getOldValue(), e.getNewValue())); }

    // ── Einladungen ───────────────────────────────────────────────────────────

    @Override
    public void onGuildInviteCreate(GuildInviteCreateEvent e) {
        Invite inv = e.getInvite();
        String expiry = inv.getMaxAge() == 0 ? "Niemals" :
            "in " + inv.getMaxAge() + " Sekunden";
        serverLog(e.getGuild(), "🔗 Einladung erstellt",
            "**Code:** `" + inv.getCode() + "`\n" +
            "**Kanal:** " + e.getChannel().getAsMention() + "\n" +
            "**Erstellt von:** " + (inv.getInviter() != null ? inv.getInviter().getAsMention() + " (`" + inv.getInviter().getId() + "`)" : "Unbekannt") + "\n" +
            "**Max. Nutzungen:** " + (inv.getMaxUses() == 0 ? "Unbegrenzt" : inv.getMaxUses()) + "\n" +
            "**Läuft ab:** " + expiry + "\n" +
            "**Temporär:** " + (inv.isTemporary() ? "Ja" : "Nein") + "\n" +
            "**URL:** discord.gg/" + inv.getCode());
    }

    @Override
    public void onGuildInviteDelete(GuildInviteDeleteEvent e) {
        serverLog(e.getGuild(), "❌ Einladung gelöscht",
            "**Code:** `" + e.getCode() + "`\n" +
            "**Kanal:** " + e.getChannel().getAsMention());
    }

    // ── Voice-Status ──────────────────────────────────────────────────────────

    @Override
    public void onGuildVoiceUpdate(GuildVoiceUpdateEvent e) {
        Member member = e.getMember();
        AudioChannel left   = e.getChannelLeft();
        AudioChannel joined = e.getChannelJoined();

        String title, detail;
        if (left == null) {
            title  = "🎤 Voice: Beigetreten";
            detail = "**Kanal:** " + joined.getName();
        } else if (joined == null) {
            title  = "🚪 Voice: Verlassen";
            detail = "**Kanal:** " + left.getName();
        } else {
            title  = "🔀 Voice: Gewechselt";
            detail = "**Von:** " + left.getName() + " → **" + joined.getName() + "**";
        }

        serverLog(member.getGuild(), title,
            "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" + detail);
    }

    @Override public void onGuildVoiceMute(GuildVoiceMuteEvent e) {
        serverLog(e.getGuild(), e.isMuted() ? "🔇 Server-Stummschaltung aktiviert" : "🔊 Server-Stummschaltung aufgehoben",
            "**Nutzer:** " + e.getMember().getAsMention() + " (`" + e.getMember().getId() + "`)"); }

    @Override public void onGuildVoiceDeafen(GuildVoiceDeafenEvent e) {
        serverLog(e.getGuild(), e.isDeafened() ? "🔕 Server-Taubschaltung aktiviert" : "🔔 Server-Taubschaltung aufgehoben",
            "**Nutzer:** " + e.getMember().getAsMention() + " (`" + e.getMember().getId() + "`)"); }

    @Override public void onGuildVoiceSelfMute(GuildVoiceSelfMuteEvent e) {
        serverLog(e.getGuild(), e.isSelfMuted() ? "🎤 Selbst stummgeschaltet" : "🎤 Selbst-Stummschaltung aufgehoben",
            "**Nutzer:** " + e.getMember().getAsMention() + " (`" + e.getMember().getId() + "`)"); }

    @Override public void onGuildVoiceSelfDeafen(GuildVoiceSelfDeafenEvent e) {
        serverLog(e.getGuild(), e.isSelfDeafened() ? "🎧 Selbst taubgeschaltet" : "🎧 Selbst-Taubschaltung aufgehoben",
            "**Nutzer:** " + e.getMember().getAsMention() + " (`" + e.getMember().getId() + "`)"); }

    // GuildVoiceStreamEvent / GuildVoiceVideoEvent sind in JDA 5.2.x nicht verfügbar.

    // ════════════════════════════════════════════════════════════
    //  MODERATIONS-LOGS
    // ════════════════════════════════════════════════════════════

    @Override
    public void onGuildBan(GuildBanEvent e) {
        User user = e.getUser();
        withAudit(e.getGuild(), ActionType.BAN, entry ->
            log(e.getGuild(), LoggingConfig.MODERATION_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("🔨 Nutzer gebannt")
                .setDescription(
                    "**Nutzer:** " + user.getAsMention() + " | " + user.getName() + " (`" + user.getId() + "`)\n" +
                    "**Grund:** " + (entry != null && entry.getReason() != null ? entry.getReason() : "Kein Grund angegeben") + "\n" +
                    auditUser("Ausgeführt von", entry))
                .setThumbnail(user.getEffectiveAvatarUrl())

                .build()));
    }

    @Override
    public void onGuildUnban(GuildUnbanEvent e) {
        User user = e.getUser();
        withAudit(e.getGuild(), ActionType.UNBAN, entry ->
            log(e.getGuild(), LoggingConfig.MODERATION_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("✅ Bann aufgehoben")
                .setDescription(
                    "**Nutzer:** " + user.getAsMention() + " | " + user.getName() + " (`" + user.getId() + "`)\n" +
                    auditUser("Aufgehoben von", entry))
                .setThumbnail(user.getEffectiveAvatarUrl())

                .build()));
    }

    @Override
    public void onGuildMemberUpdateTimeOut(GuildMemberUpdateTimeOutEvent e) {
        OffsetDateTime newEnd = e.getNewTimeOutEnd();
        OffsetDateTime oldEnd = e.getOldTimeOutEnd();
        Member member = e.getMember();

        withAudit(e.getGuild(), ActionType.MEMBER_UPDATE, entry -> {
            if (newEnd != null && newEnd.isAfter(OffsetDateTime.now())) {
                log(e.getGuild(), LoggingConfig.MODERATION_LOG_CHANNEL_ID, EmbedFactory.create()
                    .setTitle("⏱️ Timeout vergeben")
                    .setDescription(
                        "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                        "**Timeout bis:** <t:" + newEnd.toEpochSecond() + ":F>\n" +
                        auditUser("Ausgeführt von", entry))
                    .setThumbnail(member.getEffectiveAvatarUrl())

                    .build());
            } else if (oldEnd != null) {
                log(e.getGuild(), LoggingConfig.MODERATION_LOG_CHANNEL_ID, EmbedFactory.create()
                    .setTitle("✅ Timeout aufgehoben")
                    .setDescription(
                        "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                        auditUser("Aufgehoben von", entry))
                    .setThumbnail(member.getEffectiveAvatarUrl())

                    .build());
            }
        });
    }

    // ════════════════════════════════════════════════════════════
    //  SPIELER-LOGS
    // ════════════════════════════════════════════════════════════

    @Override
    public void onGuildMemberJoin(GuildMemberJoinEvent e) {
        Member member = e.getMember();
        if (member.getUser().isBot()) return;

        long accountAgeDays = java.time.Duration.between(
            member.getUser().getTimeCreated().toInstant(), Instant.now()).toDays();
        String warning = accountAgeDays < 7
            ? "\n⚠️ **Neues Konto! Weniger als 7 Tage alt.**" : "";

        log(e.getGuild(), LoggingConfig.MEMBER_LOG_CHANNEL_ID, EmbedFactory.create()
            .setTitle("📥 Mitglied beigetreten")
            .setDescription(
                "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                "**Konto erstellt:** <t:" + member.getUser().getTimeCreated().toEpochSecond() + ":F>\n" +
                "**Kontoalter:** " + accountAgeDays + " Tage" + warning)
            .setThumbnail(member.getEffectiveAvatarUrl())

            .build());
    }

    @Override
    public void onGuildMemberRemove(GuildMemberRemoveEvent e) {
        User user = e.getUser();
        if (user.isBot()) return;
        Member member = e.getMember();

        String timeOnServer = "Unbekannt";
        String roles        = "";
        if (member != null) {
            long days = java.time.Duration.between(
                member.getTimeJoined().toInstant(), Instant.now()).toDays();
            timeOnServer = days + " Tage";
            List<String> roleList = member.getRoles().stream()
                .map(Role::getAsMention).toList();
            if (!roleList.isEmpty())
                roles = "\n**Hatte diese Rollen:** " + String.join(" ", roleList.subList(0, Math.min(roleList.size(), 20)));
        }

        log(e.getGuild(), LoggingConfig.MEMBER_LOG_CHANNEL_ID, EmbedFactory.create()
            .setTitle("📤 Mitglied verlassen")
            .setDescription(
                "**Nutzer:** " + user.getAsMention() + " | " + user.getName() + " (`" + user.getId() + "`)\n" +
                "**Zeit auf dem Server:** " + timeOnServer + roles)
            .setThumbnail(user.getEffectiveAvatarUrl())

            .build());
    }

    @Override
    public void onGuildMemberUpdateNickname(GuildMemberUpdateNicknameEvent e) {
        Member member = e.getMember();
        withAudit(e.getGuild(), ActionType.MEMBER_UPDATE, entry ->
            log(e.getGuild(), LoggingConfig.MEMBER_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("✏️ Nickname geändert")
                .setDescription(
                    "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                    diff("Nickname",
                        e.getOldNickname() != null ? e.getOldNickname() : "_(kein Nickname)_",
                        e.getNewNickname() != null ? e.getNewNickname() : "_(kein Nickname)_") + "\n" +
                    auditUser("Geändert von", entry))
                .setThumbnail(member.getEffectiveAvatarUrl())

                .build()));
    }

    // ════════════════════════════════════════════════════════════
    //  NACHRICHTEN-LOGS
    // ════════════════════════════════════════════════════════════

    @Override
    public void onMessageDelete(MessageDeleteEvent e) {
        if (!e.isFromGuild()) return;
        Guild guild = e.getGuild();
        MessageCache.CachedMessage cached = MessageCache.get(e.getMessageIdLong());

        StringBuilder desc = new StringBuilder();
        desc.append("**Kanal:** ").append(e.getChannel().getAsMention())
            .append(" (`").append(e.getChannel().getId()).append("`)\n")
            .append("**Nachrichten-ID:** `").append(e.getMessageId()).append("`\n");

        if (cached != null) {
            desc.append("**Autor:** <@").append(cached.authorId()).append("> | ")
                .append(cached.authorName()).append(" (`").append(cached.authorId()).append("`)\n")
                .append("**Gesendet:** <t:").append(cached.timestampEpoch()).append(":F>\n");
            if (!cached.content().isBlank())
                desc.append("**Inhalt:**\n```\n").append(truncate(cached.content(), 900)).append("\n```");
            if (!cached.attachments().isEmpty())
                desc.append("\n**Anhänge:** ").append(String.join(", ", cached.attachments()));
        } else {
            desc.append("**Inhalt:** _(nicht im Cache – Nachricht zu alt oder nicht erfasst)_");
        }

        withAudit(guild, ActionType.MESSAGE_DELETE, entry -> {
            if (entry != null)
                desc.append("\n").append(auditUser("Gelöscht von", entry));

            log(guild, LoggingConfig.MESSAGE_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("🗑️ Nachricht gelöscht")
                .setDescription(desc.toString())

                .build());
        });

        MessageCache.remove(e.getMessageIdLong());
    }

    @Override
    public void onMessageUpdate(MessageUpdateEvent e) {
        if (!e.isFromGuild()) return;
        if (e.getAuthor().isBot()) return;

        Message newMsg = e.getMessage();
        String newContent = newMsg.getContentRaw();

        // Nur tatsächliche Inhaltsänderungen loggen (keine reinen Embed-Updates)
        MessageCache.CachedMessage cached = MessageCache.get(e.getMessageIdLong());
        String oldContent = cached != null ? cached.content() : "_(nicht im Cache)_";
        if (oldContent.equals(newContent)) return;

        log(e.getGuild(), LoggingConfig.MESSAGE_LOG_CHANNEL_ID, EmbedFactory.create()
            .setTitle("✏️ Nachricht bearbeitet")
            .setDescription(
                "**Autor:** " + e.getAuthor().getAsMention() + " | " + e.getAuthor().getName() + " (`" + e.getAuthor().getId() + "`)\n" +
                "**Kanal:** " + e.getChannel().getAsMention() + "\n" +
                "**[Zur Nachricht](https://discord.com/channels/" + e.getGuild().getId() + "/" + e.getChannel().getId() + "/" + e.getMessageId() + ")**\n\n" +
                "**📝 Vorher:**\n```\n" + truncate(oldContent, 450) + "\n```\n" +
                "**📝 Nachher:**\n```\n" + truncate(newContent, 450) + "\n```")

            .build());

        // Cache aktualisieren
        if (cached != null)
            MessageCache.put(e.getMessageIdLong(), new MessageCache.CachedMessage(
                cached.authorId(), cached.authorName(), cached.authorAvatar(),
                newContent, cached.channelMention(), cached.attachments(), cached.timestampEpoch()));
    }

    @Override
    public void onMessageBulkDelete(MessageBulkDeleteEvent e) {
        // MessageBulkDeleteEvent ist in JDA immer von einem Guild-Kanal
        Guild guild = e.getGuild();
        List<String> ids = e.getMessageIds();

        StringBuilder list = new StringBuilder();
        int shown = 0;
        for (String id : ids) {
            MessageCache.CachedMessage c = MessageCache.get(Long.parseLong(id));
            if (c != null && shown < 15) {
                list.append("• **").append(c.authorName()).append("** <t:").append(c.timestampEpoch()).append(":R>: ")
                    .append(truncate(c.content(), 80)).append("\n");
                shown++;
                MessageCache.remove(Long.parseLong(id));
            }
        }

        final int shownFinal = shown;
        withAudit(guild, ActionType.MESSAGE_BULK_DELETE, entry -> {
            StringBuilder desc = new StringBuilder()
                .append("**Kanal:** ").append(e.getChannel().getAsMention()).append("\n")
                .append("**Gelöschte Nachrichten:** ").append(ids.size()).append("\n")
                .append("**Im Cache gefunden:** ").append(shownFinal).append("\n")
                .append(auditUser("Ausgeführt von", entry));

            EmbedBuilder embed = EmbedFactory.create()
                .setTitle("💥 Massenlöschung – " + ids.size() + " Nachrichten")
                .setDescription(desc.toString())
;

            if (list.length() > 0)
                embed.addField("Nachrichtenliste (aus Cache)", list.toString(), false);

            log(guild, LoggingConfig.MESSAGE_LOG_CHANNEL_ID, embed.build());
        });
    }

    // ════════════════════════════════════════════════════════════
    //  ROLLEN-LOGS
    // ════════════════════════════════════════════════════════════

    @Override
    public void onRoleCreate(RoleCreateEvent e) {
        Role role = e.getRole();
        withAudit(e.getGuild(), ActionType.ROLE_CREATE, entry ->
            log(e.getGuild(), LoggingConfig.ROLE_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("➕ Rolle erstellt")
                .setDescription(
                    "**Name:** " + role.getAsMention() + " (`" + role.getId() + "`)\n" +
                    "**Farbe:** " + formatColor(role.getColor()) + "\n" +
                    "**Angezeigt (hoist):** " + (role.isHoisted() ? "Ja" : "Nein") + "\n" +
                    "**Erwähnbar:** " + (role.isMentionable() ? "Ja" : "Nein") + "\n" +
                    "**Position:** " + role.getPosition() + "\n" +
                    auditUser("Erstellt von", entry) + "\n" +
                    "**Berechtigungen:** " + formatPermissions(role.getPermissionsRaw()))

                .build()));
    }

    @Override
    public void onRoleDelete(RoleDeleteEvent e) {
        Role role = e.getRole();
        withAudit(e.getGuild(), ActionType.ROLE_DELETE, entry ->
            log(e.getGuild(), LoggingConfig.ROLE_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("➖ Rolle gelöscht")
                .setDescription(
                    "**Name:** " + role.getName() + " (`" + role.getId() + "`)\n" +
                    "**Farbe:** " + formatColor(role.getColor()) + "\n" +
                    auditUser("Gelöscht von", entry) + "\n" +
                    "**Hatte diese Berechtigungen:** " + formatPermissions(role.getPermissionsRaw()))

                .build()));
    }

    @Override public void onRoleUpdateName(RoleUpdateNameEvent e) {
        roleLog(e.getGuild(), e.getRole(), "✏️ Rollenname geändert",
            diff("Name", e.getOldName(), e.getNewName())); }

    @Override public void onRoleUpdateColor(RoleUpdateColorEvent e) {
        roleLog(e.getGuild(), e.getRole(), "✏️ Rollenfarbe geändert",
            diff("Farbe", formatColor(e.getOldColor()), formatColor(e.getNewColor()))); }

    @Override public void onRoleUpdateHoisted(RoleUpdateHoistedEvent e) {
        roleLog(e.getGuild(), e.getRole(), "✏️ Rollen-Hoist geändert",
            diff("Angezeigt", e.getOldValue(), e.getNewValue())); }

    @Override public void onRoleUpdateMentionable(RoleUpdateMentionableEvent e) {
        roleLog(e.getGuild(), e.getRole(), "✏️ Rollen-Erwähnbarkeit geändert",
            diff("Erwähnbar", e.getOldValue(), e.getNewValue())); }

    @Override
    public void onRoleUpdatePermissions(RoleUpdatePermissionsEvent e) {
        long added   = e.getNewPermissionsRaw() & ~e.getOldPermissionsRaw();
        long removed = e.getOldPermissionsRaw() & ~e.getNewPermissionsRaw();
        String desc = "**Rolle:** " + e.getRole().getAsMention() + " (`" + e.getRole().getId() + "`)\n";
        if (added   != 0) desc += "**➕ Hinzugefügt:** " + formatPermissions(added) + "\n";
        if (removed != 0) desc += "**➖ Entfernt:** "    + formatPermissions(removed);
        roleLog(e.getGuild(), e.getRole(), "✏️ Rollen-Berechtigungen geändert", desc);
    }

    // GuildMemberUpdateRolesEvent existiert in JDA 5.2.x nicht.
    // Stattdessen: onGuildMemberRoleAdd + onGuildMemberRoleRemove

    @Override
    public void onGuildMemberRoleAdd(net.dv8tion.jda.api.events.guild.member.GuildMemberRoleAddEvent e) {
        Member member = e.getMember();
        List<Role> added = e.getRoles();
        withAudit(e.getGuild(), ActionType.MEMBER_ROLE_UPDATE, entry ->
            log(e.getGuild(), LoggingConfig.ROLE_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("🏷️ Rollen vergeben")
                .setDescription(
                    "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                    "**➕ Hinzugefügte Rollen:** " + added.stream().map(Role::getAsMention).reduce("", (a, b) -> a + " " + b) + "\n" +
                    auditUser("Ausgeführt von", entry))
                .setThumbnail(member.getEffectiveAvatarUrl())

                .build()));
    }

    @Override
    public void onGuildMemberRoleRemove(net.dv8tion.jda.api.events.guild.member.GuildMemberRoleRemoveEvent e) {
        Member member = e.getMember();
        List<Role> removed = e.getRoles();
        withAudit(e.getGuild(), ActionType.MEMBER_ROLE_UPDATE, entry ->
            log(e.getGuild(), LoggingConfig.ROLE_LOG_CHANNEL_ID, EmbedFactory.create()
                .setTitle("🏷️ Rollen entzogen")
                .setDescription(
                    "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                    "**➖ Entfernte Rollen:** " + removed.stream().map(Role::getAsMention).reduce("", (a, b) -> a + " " + b) + "\n" +
                    auditUser("Ausgeführt von", entry))
                .setThumbnail(member.getEffectiveAvatarUrl())

                .build()));
    }

    // ════════════════════════════════════════════════════════════
    //  HILFS-METHODEN
    // ════════════════════════════════════════════════════════════

    private static void log(Guild guild, long channelId, net.dv8tion.jda.api.entities.MessageEmbed embed) {
        BotLogger.log(guild, channelId, embed);
    }

    private void serverLog(Guild guild, String title, String description) {
        log(guild, LoggingConfig.SERVER_LOG_CHANNEL_ID, EmbedFactory.build(title, description));
    }

    private void serverLogWithAudit(Guild guild, ActionType action, String title, String description) {
        withAudit(guild, action, entry ->
            log(guild, LoggingConfig.SERVER_LOG_CHANNEL_ID,
                EmbedFactory.create().setTitle(title)
                    .setDescription(description + "\n" + auditUser("Ausgeführt von", entry))
.build()));
    }

    private void roleLog(Guild guild, Role role, String title, String description) {
        log(guild, LoggingConfig.ROLE_LOG_CHANNEL_ID, EmbedFactory.create()
            .setTitle(title)
            .setDescription("**Rolle:** " + role.getName() + " (`" + role.getId() + "`)\n" + description)

            .build());
    }

    private static void withAudit(Guild guild, ActionType actionType, Consumer<AuditLogEntry> callback) {
        guild.retrieveAuditLogs().type(actionType).limit(5).queue(entries -> {
            Instant cutoff = Instant.now().minusSeconds(5);
            AuditLogEntry entry = entries.stream()
                .filter(e -> e.getTimeCreated().toInstant().isAfter(cutoff))
                .findFirst().orElse(null);
            callback.accept(entry);
        }, err -> callback.accept(null));
    }

    private static String auditUser(String label, AuditLogEntry entry) {
        if (entry == null || entry.getUser() == null) return "**" + label + ":** Unbekannt";
        return "**" + label + ":** " + entry.getUser().getAsMention() + " (`" + entry.getUser().getId() + "`)";
    }

    private static String diff(String label, Object oldVal, Object newVal) {
        return "**" + label + " vorher:** " + strOrNone(oldVal) + "\n**" + label + " nachher:** " + strOrNone(newVal);
    }

    private static String strOrNone(Object o) {
        return (o == null || o.toString().isBlank()) ? "—" : o.toString();
    }

    private static String formatChannelType(Channel ch) {
        if (ch instanceof Category)    return "Kategorie";
        if (ch instanceof VoiceChannel) return "Sprachkanal";
        if (ch instanceof TextChannel)  return "Textkanal";
        return ch.getType().name();
    }

    private static String formatColor(Color c) {
        return c != null ? "#" + String.format("%06X", c.getRGB() & 0xFFFFFF) : "#000000";
    }

    private static String formatPermissions(long raw) {
        if (raw == 0) return "Keine";
        StringBuilder sb = new StringBuilder();
        for (net.dv8tion.jda.api.Permission p : net.dv8tion.jda.api.Permission.getPermissions(raw))
            sb.append(p.getName()).append(", ");
        return sb.length() > 2 ? sb.substring(0, sb.length() - 2) : "Keine";
    }

    private static String truncate(String s, int max) {
        return s != null && s.length() > max ? s.substring(0, max - 1) + "…" : (s != null ? s : "");
    }
}
