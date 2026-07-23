using Discord;
using Discord.Rest;
using Discord.WebSocket;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using PCRP.Bot.Common;

namespace PCRP.Bot.Services;

/// <summary>
/// Umfassendes Log-System – protokolliert jeden relevanten Vorgang im Server
/// bis ins kleinste Detail in die jeweiligen Log-Kanäle.
///
/// Kanal-Zuordnung:
///   Server-Logs      → Guild, Kanäle, Einladungen, Voice
///   Moderations-Logs → Bans, Timeouts, Wortfilter, Spam, Eigenwerbung, Anti-Nuke
///   Spieler-Logs     → Bot-Neustart, Beitritt, Verlassen, Nickname
///   Nachrichten-Logs → Gelöscht, Bearbeitet, Massenlöschung
///   Rollen-Logs      → Erstellt, Gelöscht, Geändert, Vergeben/Entzogen
///   Geld-Logs        → Wirtschaftsvorgänge (für spätere Implementierung vorbereitet)
///   Ticket-Logs      → Tickets & Transkripte (für spätere Implementierung vorbereitet)
/// </summary>
public class LoggingService : BackgroundService
{
    private readonly DiscordSocketClient _client;
    private readonly ILogger<LoggingService> _logger;

    public LoggingService(DiscordSocketClient client, ILogger<LoggingService> logger)
    {
        _client = client;
        _logger = logger;
    }

    protected override Task ExecuteAsync(CancellationToken stoppingToken)
    {
        // Server-Logs
        _client.GuildUpdated        += OnGuildUpdatedAsync;
        _client.ChannelCreated      += OnChannelCreatedAsync;
        _client.ChannelDestroyed    += OnChannelDestroyedAsync;
        _client.ChannelUpdated      += OnChannelUpdatedAsync;
        _client.InviteCreated       += OnInviteCreatedAsync;
        _client.InviteDeleted       += OnInviteDeletedAsync;
        _client.UserVoiceStateUpdated += OnVoiceStateUpdatedAsync;

        // Moderations-Logs
        _client.UserBanned          += OnUserBannedAsync;
        _client.UserUnbanned        += OnUserUnbannedAsync;

        // Spieler-Logs + Rollen-Logs (GuildMemberUpdated deckt beides)
        _client.Ready               += OnReadyAsync;
        _client.UserJoined          += OnUserJoinedAsync;
        _client.UserLeft            += OnUserLeftAsync;
        _client.GuildMemberUpdated  += OnGuildMemberUpdatedAsync;

        // Nachrichten-Logs
        _client.MessageDeleted      += OnMessageDeletedAsync;
        _client.MessageUpdated      += OnMessageUpdatedAsync;
        _client.MessagesBulkDeleted += OnMessagesBulkDeletedAsync;

        // Rollen-Logs
        _client.RoleCreated         += OnRoleCreatedAsync;
        _client.RoleDeleted         += OnRoleDeletedAsync;
        _client.RoleUpdated         += OnRoleUpdatedAsync;

        return Task.CompletedTask;
    }

    // ════════════════════════════════════════════════════════════
    //  ÖFFENTLICHE METHODE – für ModerationService & GuildProtectionService
    // ════════════════════════════════════════════════════════════

    /// <summary>
    /// Schreibt einen Eintrag in den Moderations-Log-Kanal.
    /// Wird von ModerationService und GuildProtectionService aufgerufen.
    /// </summary>
    public Task LogModerationAsync(SocketGuild guild, string title, string description,
        IEnumerable<EmbedFieldBuilder>? fields = null)
    {
        var embed = EmbedFactory.Create()
            .WithTitle(title)
            .WithDescription(description)
            .WithCurrentTimestamp();
        if (fields is not null)
            foreach (var f in fields)
                embed.AddField(f);
        return LogAsync(guild, LoggingConfig.ModerationLogChannelId, embed);
    }

    // ════════════════════════════════════════════════════════════
    //  SERVER-LOGS
    // ════════════════════════════════════════════════════════════

    private async Task OnGuildUpdatedAsync(SocketGuild before, SocketGuild after)
    {
        var changes = new List<EmbedFieldBuilder>();

        void Add(string name, object? b, object? a)
        {
            if (!Equals(b, a))
                changes.Add(Field(name, $"**Vorher:** {b ?? "—"}\n**Nachher:** {a ?? "—"}"));
        }

        Add("Name",                    before.Name,                       after.Name);
        Add("Beschreibung",            before.Description,                after.Description);
        Add("Icon-URL",                before.IconUrl,                    after.IconUrl);
        Add("Banner-URL",              before.BannerUrl,                  after.BannerUrl);
        Add("Vanity-URL",              before.VanityURLCode,              after.VanityURLCode);
        Add("Verifizierungsstufe",     before.VerificationLevel,          after.VerificationLevel);
        Add("Expliziter Inhaltsfilter",before.ExplicitContentFilter,      after.ExplicitContentFilter);
        Add("Standardbenachrichtigung",before.DefaultMessageNotifications,after.DefaultMessageNotifications);
        Add("2FA-Stufe",               before.MfaLevel,                   after.MfaLevel);
        Add("AFK-Timeout (Sek.)",      before.AFKTimeout,                 after.AFKTimeout);
        Add("AFK-Kanal",               before.AFKChannel?.Mention,        after.AFKChannel?.Mention);
        Add("System-Kanal",            before.SystemChannel?.Mention,     after.SystemChannel?.Mention);
        Add("Inhaber",                 $"<@{before.OwnerId}>",            $"<@{after.OwnerId}>");
        Add("NSFW-Stufe",              before.NsfwLevel,                  after.NsfwLevel);
        Add("Boost-Stufe",             before.PremiumTier,                after.PremiumTier);
        Add("Bevorzugte Sprache",      before.PreferredLocale,            after.PreferredLocale);

        if (changes.Count == 0) return;

        var embed = EmbedFactory.Create()
            .WithTitle("⚙️ Server bearbeitet")
            .WithDescription($"**Server:** {after.Name} (`{after.Id}`)\n**{changes.Count} Änderung(en)**")
            .WithCurrentTimestamp();
        foreach (var f in changes.Take(25)) embed.AddField(f);

        await LogAsync(after, LoggingConfig.ServerLogChannelId, embed);
    }

    private async Task OnChannelCreatedAsync(SocketChannel socketChannel)
    {
        if (socketChannel is not SocketGuildChannel ch) return;
        var executor = await TryGetAuditEntryAsync(ch.Guild, ActionType.ChannelCreated);

        var embed = EmbedFactory.Create()
            .WithTitle("📁 Kanal erstellt")
            .WithDescription($"**Name:** {ch.Name}\n**Typ:** {FormatChannelType(ch)}\n" +
                             $"**Position:** {ch.Position}" +
                             (ch is SocketTextChannel tc && tc.CategoryId.HasValue ? $"\n**Kategorie:** <#{tc.CategoryId}>" :
                              ch is SocketVoiceChannel vc && vc.CategoryId.HasValue ? $"\n**Kategorie:** <#{vc.CategoryId}>" : "") +
                             $"\n**Kanal-ID:** `{ch.Id}`")
            .WithCurrentTimestamp();
        if (executor is not null)
            embed.AddField(Field("Erstellt von", $"{executor.User?.Mention} (`{executor.User?.Id}`)"));
        if (ch.PermissionOverwrites.Count > 0)
            embed.AddField(Field("Berechtigungs-Overwrites", $"{ch.PermissionOverwrites.Count} Einträge gesetzt"));

        await LogAsync(ch.Guild, LoggingConfig.ServerLogChannelId, embed);
    }

    private async Task OnChannelDestroyedAsync(SocketChannel socketChannel)
    {
        if (socketChannel is not SocketGuildChannel ch) return;
        var executor = await TryGetAuditEntryAsync(ch.Guild, ActionType.ChannelDeleted);

        var embed = EmbedFactory.Create()
            .WithTitle("🗑️ Kanal gelöscht")
            .WithDescription($"**Name:** {ch.Name}\n**Typ:** {FormatChannelType(ch)}" +
                             (ch is SocketTextChannel tc && tc.CategoryId.HasValue ? $"\n**Kategorie:** <#{tc.CategoryId}>" :
                              ch is SocketVoiceChannel vc && vc.CategoryId.HasValue ? $"\n**Kategorie:** <#{vc.CategoryId}>" : "") +
                             $"\n**Kanal-ID:** `{ch.Id}`")
            .WithCurrentTimestamp();
        if (executor is not null)
            embed.AddField(Field("Gelöscht von", $"{executor.User?.Mention} (`{executor.User?.Id}`)"));

        await LogAsync(ch.Guild, LoggingConfig.ServerLogChannelId, embed);
    }

    private async Task OnChannelUpdatedAsync(SocketChannel before, SocketChannel after)
    {
        if (before is not SocketGuildChannel chBefore || after is not SocketGuildChannel chAfter) return;

        var changes = new List<EmbedFieldBuilder>();

        void Add(string name, object? b, object? a)
        {
            if (!Equals(b, a))
                changes.Add(Field(name, $"**Vorher:** {b ?? "—"}\n**Nachher:** {a ?? "—"}"));
        }

        Add("Name", chBefore.Name, chAfter.Name);
        Add("Position", chBefore.Position, chAfter.Position);

        if (chBefore is SocketTextChannel tBefore && chAfter is SocketTextChannel tAfter)
        {
            Add("Thema", tBefore.Topic, tAfter.Topic);
            Add("NSFW", tBefore.IsNsfw, tAfter.IsNsfw);
            Add("Slowmode (Sek.)", tBefore.SlowModeInterval, tAfter.SlowModeInterval);
            Add("Kategorie", tBefore.CategoryId, tAfter.CategoryId);
        }
        else if (chBefore is SocketVoiceChannel vBefore && chAfter is SocketVoiceChannel vAfter)
        {
            Add("Bitrate", vBefore.Bitrate, vAfter.Bitrate);
            Add("Nutzerlimit", vBefore.UserLimit, vAfter.UserLimit);
            Add("Kategorie", vBefore.CategoryId, vAfter.CategoryId);
        }

        if (changes.Count == 0) return;

        var executor = await TryGetAuditEntryAsync(chAfter.Guild, ActionType.ChannelUpdated);
        var embed = EmbedFactory.Create()
            .WithTitle("✏️ Kanal bearbeitet")
            .WithDescription($"**Kanal:** {chAfter.Name} (`{chAfter.Id}`)")
            .WithCurrentTimestamp();
        if (executor is not null)
            embed.AddField(Field("Bearbeitet von", $"{executor.User?.Mention} (`{executor.User?.Id}`)"));
        foreach (var f in changes.Take(24)) embed.AddField(f);

        await LogAsync(chAfter.Guild, LoggingConfig.ServerLogChannelId, embed);
    }

    private async Task OnInviteCreatedAsync(SocketInvite invite)
    {
        var expiry = invite.MaxAge == 0
            ? "Niemals"
            : $"in {TimeSpan.FromSeconds(invite.MaxAge):d\\d\\ h\\h\\ m\\m}";

        var embed = EmbedFactory.Create()
            .WithTitle("🔗 Einladung erstellt")
            .WithDescription($"**Code:** `{invite.Code}`\n**Kanal:** {invite.Channel?.Name}\n" +
                             $"**Erstellt von:** {invite.Inviter?.Mention} (`{invite.Inviter?.Id}`)\n" +
                             $"**Max. Nutzungen:** {(invite.MaxUses == 0 ? "Unbegrenzt" : invite.MaxUses)}\n" +
                             $"**Läuft ab:** {expiry}\n" +
                             $"**Temporäre Mitgliedschaft:** {(invite.IsTemporary ? "Ja" : "Nein")}\n" +
                             $"**URL:** discord.gg/{invite.Code}")
            .WithCurrentTimestamp();

        await LogAsync(invite.Guild, LoggingConfig.ServerLogChannelId, embed);
    }

    private async Task OnInviteDeletedAsync(SocketGuildChannel channel, string code)
    {
        var executor = await TryGetAuditEntryAsync(channel.Guild, ActionType.InviteDeleted);

        var embed = EmbedFactory.Create()
            .WithTitle("❌ Einladung gelöscht")
            .WithDescription($"**Code:** `{code}`\n**Kanal:** {channel.Name} (`{channel.Id}`)")
            .WithCurrentTimestamp();
        if (executor is not null)
            embed.AddField(Field("Gelöscht von", $"{executor.User?.Mention} (`{executor.User?.Id}`)"));

        await LogAsync(channel.Guild, LoggingConfig.ServerLogChannelId, embed);
    }

    private async Task OnVoiceStateUpdatedAsync(SocketUser user, SocketVoiceState before, SocketVoiceState after)
    {
        if (user is not SocketGuildUser guildUser) return;

        string title;
        var details = new List<string>();

        // Kanal-Bewegung ermitteln
        if (before.VoiceChannel is null && after.VoiceChannel is not null)
        {
            title = "🎤 Voice: Beigetreten";
            details.Add($"**Kanal:** {after.VoiceChannel.Name} (`{after.VoiceChannel.Id}`)");
        }
        else if (before.VoiceChannel is not null && after.VoiceChannel is null)
        {
            title = "🚪 Voice: Verlassen";
            details.Add($"**Kanal:** {before.VoiceChannel.Name} (`{before.VoiceChannel.Id}`)");
        }
        else if (before.VoiceChannel is not null && after.VoiceChannel is not null
                 && before.VoiceChannel.Id != after.VoiceChannel.Id)
        {
            title = "🔀 Voice: Gewechselt";
            details.Add($"**Von:** {before.VoiceChannel.Name}\n**Nach:** {after.VoiceChannel.Name}");
        }
        else
        {
            title = "🎙️ Voice: Status geändert";
        }

        // Statusänderungen
        if (before.IsMuted != after.IsMuted)
            details.Add(after.IsMuted ? "🔇 Server-Stummschaltung **aktiviert**" : "🔊 Server-Stummschaltung **aufgehoben**");
        if (before.IsDeafened != after.IsDeafened)
            details.Add(after.IsDeafened ? "🔕 Server-Taubschaltung **aktiviert**" : "🔔 Server-Taubschaltung **aufgehoben**");
        if (before.IsSelfMuted != after.IsSelfMuted)
            details.Add(after.IsSelfMuted ? "🎤 Selbst **stummgeschaltet**" : "🎤 Selbst-Stummschaltung **aufgehoben**");
        if (before.IsSelfDeafened != after.IsSelfDeafened)
            details.Add(after.IsSelfDeafened ? "🎧 Selbst **taubgeschaltet**" : "🎧 Selbst-Taubschaltung **aufgehoben**");
        if (before.IsStreaming != after.IsStreaming)
            details.Add(after.IsStreaming ? "📡 **Streaming** gestartet" : "📡 Streaming **beendet**");
        if (before.IsVideoing != after.IsVideoing)
            details.Add(after.IsVideoing ? "📷 Kamera **eingeschaltet**" : "📷 Kamera **ausgeschaltet**");

        if (details.Count == 0) return;

        var embed = EmbedFactory.Create()
            .WithTitle(title)
            .WithDescription($"**Nutzer:** {guildUser.Mention} | {guildUser.Username} (`{guildUser.Id}`)\n" +
                             string.Join("\n", details))
            .WithThumbnailUrl(guildUser.GetDisplayAvatarUrl() ?? guildUser.GetDefaultAvatarUrl())
            .WithCurrentTimestamp();

        await LogAsync(guildUser.Guild, LoggingConfig.ServerLogChannelId, embed);
    }

    // ════════════════════════════════════════════════════════════
    //  MODERATIONS-LOGS
    // ════════════════════════════════════════════════════════════

    private async Task OnUserBannedAsync(SocketUser user, SocketGuild guild)
    {
        var executor = await TryGetAuditEntryAsync(guild, ActionType.Ban);
        var reason = executor?.Reason ?? "Kein Grund angegeben";

        var embed = EmbedFactory.Create()
            .WithTitle("🔨 Nutzer gebannt")
            .WithDescription($"**Nutzer:** {user.Mention} | {user.Username} (`{user.Id}`)\n" +
                             $"**Grund:** {reason}\n" +
                             $"**Ausgeführt von:** {(executor?.User is not null ? $"{executor.User.Mention} (`{executor.User.Id}`)" : "Unbekannt")}")
            .WithThumbnailUrl(user.GetAvatarUrl() ?? user.GetDefaultAvatarUrl())
            .WithCurrentTimestamp();

        await LogAsync(guild, LoggingConfig.ModerationLogChannelId, embed);
    }

    private async Task OnUserUnbannedAsync(SocketUser user, SocketGuild guild)
    {
        var executor = await TryGetAuditEntryAsync(guild, ActionType.Unban);

        var embed = EmbedFactory.Create()
            .WithTitle("✅ Bann aufgehoben")
            .WithDescription($"**Nutzer:** {user.Mention} | {user.Username} (`{user.Id}`)\n" +
                             $"**Aufgehoben von:** {(executor?.User is not null ? $"{executor.User.Mention} (`{executor.User.Id}`)" : "Unbekannt")}")
            .WithThumbnailUrl(user.GetAvatarUrl() ?? user.GetDefaultAvatarUrl())
            .WithCurrentTimestamp();

        await LogAsync(guild, LoggingConfig.ModerationLogChannelId, embed);
    }

    // ════════════════════════════════════════════════════════════
    //  SPIELER-LOGS
    // ════════════════════════════════════════════════════════════

    private async Task OnReadyAsync()
    {
        var embed = EmbedFactory.CreateWithFooterIcon(LoggingConfig.CSharpLogoUrl)
            .WithTitle("🟢 Bot gestartet / neugestartet")
            .WithDescription($"**Bot:** {_client.CurrentUser?.Username} (`{_client.CurrentUser?.Id}`)\n" +
                             $"**Version:** .NET 8 · Discord.Net 3.20\n" +
                             $"**Verbundene Server:** {_client.Guilds.Count}\n" +
                             $"**Neustart-Zeit:** <t:{DateTimeOffset.UtcNow.ToUnixTimeSeconds()}:F>")
            .WithCurrentTimestamp();

        foreach (var guild in _client.Guilds)
            await LogAsync(guild, LoggingConfig.PlayerLogChannelId, embed);
    }

    private async Task OnUserJoinedAsync(SocketGuildUser user)
    {
        var accountAge = DateTimeOffset.UtcNow - user.CreatedAt;
        var ageStr = accountAge.TotalDays >= 1
            ? $"{(int)accountAge.TotalDays} Tage"
            : $"{(int)accountAge.TotalHours} Stunden";

        var suspiciousFlag = accountAge.TotalDays < 7 ? "\n⚠️ **Neues Konto! Weniger als 7 Tage alt.**" : "";

        var embed = EmbedFactory.Create()
            .WithTitle("📥 Mitglied beigetreten")
            .WithDescription($"**Nutzer:** {user.Mention} | {user.Username} (`{user.Id}`)\n" +
                             $"**Konto erstellt:** <t:{user.CreatedAt.ToUnixTimeSeconds()}:F>\n" +
                             $"**Kontoalter:** {ageStr}" +
                             suspiciousFlag)
            .WithThumbnailUrl(user.GetDisplayAvatarUrl() ?? user.GetDefaultAvatarUrl())
            .WithCurrentTimestamp();

        await LogAsync(user.Guild, LoggingConfig.PlayerLogChannelId, embed);
    }

    private async Task OnUserLeftAsync(SocketGuild guild, SocketUser user)
    {
        var guildUser = user as SocketGuildUser;
        var joinedAt = guildUser?.JoinedAt;
        string timeOnServer = "Unbekannt";
        if (joinedAt.HasValue)
        {
            var duration = DateTimeOffset.UtcNow - joinedAt.Value;
            timeOnServer = duration.TotalDays >= 1
                ? $"{(int)duration.TotalDays} Tage"
                : $"{(int)duration.TotalHours} Stunden";
        }

        var roles = guildUser?.Roles
            .Where(r => !r.IsEveryone)
            .Select(r => r.Mention)
            .ToList() ?? [];

        var embed = EmbedFactory.Create()
            .WithTitle("📤 Mitglied verlassen")
            .WithDescription($"**Nutzer:** {user.Mention} | {user.Username} (`{user.Id}`)\n" +
                             $"**Beigetreten:** {(joinedAt.HasValue ? $"<t:{joinedAt.Value.ToUnixTimeSeconds()}:F>" : "Unbekannt")}\n" +
                             $"**Zeit auf dem Server:** {timeOnServer}")
            .WithThumbnailUrl(user.GetAvatarUrl() ?? user.GetDefaultAvatarUrl())
            .WithCurrentTimestamp();

        if (roles.Count > 0)
            embed.AddField(Field("Hatte diese Rollen", string.Join(" ", roles.Take(20))));

        await LogAsync(guild, LoggingConfig.PlayerLogChannelId, embed);
    }

    private async Task OnGuildMemberUpdatedAsync(Cacheable<SocketGuildUser, ulong> beforeCacheable, SocketGuildUser after)
    {
        if (after.IsBot) return;
        var before = beforeCacheable.Value; // null wenn nicht gecacht

        // ── Timeout (Moderations-Log) ──
        var beforeTimeout = before?.TimedOutUntil;
        var afterTimeout = after.TimedOutUntil;
        if (!Equals(beforeTimeout, afterTimeout))
        {
            var executor = await TryGetAuditEntryAsync(after.Guild, ActionType.MemberUpdated);
            if (afterTimeout.HasValue && afterTimeout > DateTimeOffset.UtcNow)
            {
                // Timeout vergeben
                await LogAsync(after.Guild, LoggingConfig.ModerationLogChannelId,
                    EmbedFactory.Create()
                        .WithTitle("⏱️ Timeout vergeben")
                        .WithDescription($"**Nutzer:** {after.Mention} | {after.Username} (`{after.Id}`)\n" +
                                         $"**Timeout bis:** <t:{afterTimeout.Value.ToUnixTimeSeconds()}:F>\n" +
                                         $"**Ausgeführt von:** {(executor?.User is not null ? $"{executor.User.Mention} (`{executor.User.Id}`)" : "Unbekannt")}")
                        .WithThumbnailUrl(after.GetDisplayAvatarUrl() ?? after.GetDefaultAvatarUrl())
                        .WithCurrentTimestamp());
            }
            else if (beforeTimeout.HasValue)
            {
                // Timeout aufgehoben
                await LogAsync(after.Guild, LoggingConfig.ModerationLogChannelId,
                    EmbedFactory.Create()
                        .WithTitle("✅ Timeout aufgehoben")
                        .WithDescription($"**Nutzer:** {after.Mention} | {after.Username} (`{after.Id}`)\n" +
                                         $"**Aufgehoben von:** {(executor?.User is not null ? $"{executor.User.Mention} (`{executor.User.Id}`)" : "Unbekannt")}")
                        .WithThumbnailUrl(after.GetDisplayAvatarUrl() ?? after.GetDefaultAvatarUrl())
                        .WithCurrentTimestamp());
            }
        }

        // ── Nickname (Spieler-Log) ──
        if (before is not null && before.Nickname != after.Nickname)
        {
            var executor = await TryGetAuditEntryAsync(after.Guild, ActionType.MemberUpdated);
            await LogAsync(after.Guild, LoggingConfig.PlayerLogChannelId,
                EmbedFactory.Create()
                    .WithTitle("✏️ Nickname geändert")
                    .WithDescription($"**Nutzer:** {after.Mention} | {after.Username} (`{after.Id}`)\n" +
                                     $"**Vorher:** {before.Nickname ?? "_(kein Nickname)_"}\n" +
                                     $"**Nachher:** {after.Nickname ?? "_(kein Nickname)_"}\n" +
                                     $"**Geändert von:** {(executor?.User is not null ? $"{executor.User.Mention} (`{executor.User.Id}`)" : "Unbekannt")}")
                    .WithThumbnailUrl(after.GetDisplayAvatarUrl() ?? after.GetDefaultAvatarUrl())
                    .WithCurrentTimestamp());
        }

        // ── Rollen (Rollen-Log) ──
        if (before is not null)
        {
            var addedRoles   = after.Roles.Where(r => !r.IsEveryone && before.Roles.All(br => br.Id != r.Id)).ToList();
            var removedRoles = before.Roles.Where(r => !r.IsEveryone && after.Roles.All(ar => ar.Id != r.Id)).ToList();

            if (addedRoles.Count > 0 || removedRoles.Count > 0)
            {
                var executor = await TryGetAuditEntryAsync(after.Guild, ActionType.MemberRoleUpdated);
                var embed = EmbedFactory.Create()
                    .WithTitle("🏷️ Rollen eines Mitglieds geändert")
                    .WithDescription($"**Nutzer:** {after.Mention} | {after.Username} (`{after.Id}`)\n" +
                                     $"**Geändert von:** {(executor?.User is not null ? $"{executor.User.Mention} (`{executor.User.Id}`)" : "Unbekannt")}")
                    .WithThumbnailUrl(after.GetDisplayAvatarUrl() ?? after.GetDefaultAvatarUrl())
                    .WithCurrentTimestamp();

                if (addedRoles.Count > 0)
                    embed.AddField(Field("➕ Hinzugefügte Rollen",
                        string.Join("\n", addedRoles.Select(r => $"{r.Mention} (`{r.Id}`)"))));
                if (removedRoles.Count > 0)
                    embed.AddField(Field("➖ Entfernte Rollen",
                        string.Join("\n", removedRoles.Select(r => $"{r.Mention} (`{r.Id}`)"))));

                await LogAsync(after.Guild, LoggingConfig.RoleLogChannelId, embed);
            }
        }
    }

    // ════════════════════════════════════════════════════════════
    //  NACHRICHTEN-LOGS
    // ════════════════════════════════════════════════════════════

    private async Task OnMessageDeletedAsync(
        Cacheable<IMessage, ulong> cachedMsg,
        Cacheable<IMessageChannel, ulong> cachedChannel)
    {
        if (await cachedChannel.GetOrDownloadAsync() is not SocketTextChannel channel) return;

        var message = cachedMsg.Value;
        var executor = await TryGetAuditEntryAsync(channel.Guild, ActionType.MessageDeleted);

        var desc = new System.Text.StringBuilder();
        desc.AppendLine($"**Kanal:** {channel.Mention} (`{channel.Id}`)");
        desc.AppendLine($"**Nachrichten-ID:** `{cachedMsg.Id}`");

        if (message is not null)
        {
            desc.AppendLine($"**Autor:** {message.Author.Mention} | {message.Author.Username} (`{message.Author.Id}`)");
            desc.AppendLine($"**Gesendet:** <t:{message.Timestamp.ToUnixTimeSeconds()}:F>");
            if (!string.IsNullOrWhiteSpace(message.Content))
                desc.AppendLine($"**Inhalt:**\n```\n{Truncate(message.Content, 900)}\n```");
            else
                desc.AppendLine("**Inhalt:** _(leer oder nur Anhänge)_");

            if (message.Attachments.Count > 0)
                desc.AppendLine($"**Anhänge ({message.Attachments.Count}):** " +
                                string.Join(", ", message.Attachments.Select(a => a.Filename)));
            if (message.Embeds.Count > 0)
                desc.AppendLine($"**Embeds:** {message.Embeds.Count} Embed(s) enthalten");
        }
        else
        {
            desc.AppendLine("**Inhalt:** _(nicht im Cache – Nachricht zu alt)_");
        }

        if (executor is not null)
            desc.AppendLine($"**Gelöscht von:** {executor.User?.Mention} (`{executor.User?.Id}`)");

        var embed = EmbedFactory.Create()
            .WithTitle("🗑️ Nachricht gelöscht")
            .WithDescription(desc.ToString())
            .WithCurrentTimestamp();

        await LogAsync(channel.Guild, LoggingConfig.MessageLogChannelId, embed);
    }

    private async Task OnMessageUpdatedAsync(
        Cacheable<IMessage, ulong> before,
        SocketMessage after,
        ISocketMessageChannel channel)
    {
        if (after.Author.IsBot || after.Author.IsWebhook) return;
        if (channel is not SocketTextChannel textChannel) return;

        var beforeMsg = before.Value;
        var beforeContent = beforeMsg?.Content ?? "_(nicht im Cache)_";
        var afterContent = after.Content ?? "_(leer)_";

        if (beforeContent == afterContent) return; // nur Embed-Aktualisierung

        var embed = EmbedFactory.Create()
            .WithTitle("✏️ Nachricht bearbeitet")
            .WithDescription($"**Autor:** {after.Author.Mention} | {after.Author.Username} (`{after.Author.Id}`)\n" +
                             $"**Kanal:** {textChannel.Mention} (`{textChannel.Id}`)\n" +
                             $"**Nachrichten-ID:** `{after.Id}`\n" +
                             $"**[Zur Nachricht springen](https://discord.com/channels/{textChannel.Guild.Id}/{textChannel.Id}/{after.Id})**")
            .AddField(Field("📝 Vorher", $"```\n{Truncate(beforeContent, 450)}\n```"))
            .AddField(Field("📝 Nachher", $"```\n{Truncate(afterContent, 450)}\n```"))
            .WithCurrentTimestamp();

        await LogAsync(textChannel.Guild, LoggingConfig.MessageLogChannelId, embed);
    }

    private async Task OnMessagesBulkDeletedAsync(
        IReadOnlyCollection<Cacheable<IMessage, ulong>> messages,
        Cacheable<IMessageChannel, ulong> cachedChannel)
    {
        if (await cachedChannel.GetOrDownloadAsync() is not SocketTextChannel channel) return;

        var executor = await TryGetAuditEntryAsync(channel.Guild, ActionType.MessageBulkDeleted);
        var cached = messages.Select(m => m.Value).Where(m => m is not null).ToList();

        var desc = new System.Text.StringBuilder();
        desc.AppendLine($"**Kanal:** {channel.Mention} (`{channel.Id}`)");
        desc.AppendLine($"**Gelöschte Nachrichten:** {messages.Count}");
        desc.AppendLine($"**Im Cache gefunden:** {cached.Count}");
        if (executor is not null)
            desc.AppendLine($"**Ausgeführt von:** {executor.User?.Mention} (`{executor.User?.Id}`)");

        var embed = EmbedFactory.Create()
            .WithTitle($"💥 Massenlöschung – {messages.Count} Nachrichten")
            .WithDescription(desc.ToString())
            .WithCurrentTimestamp();

        // Bis zu 15 gecachte Nachrichten einzeln auflisten
        if (cached.Count > 0)
        {
            var list = new System.Text.StringBuilder();
            foreach (var msg in cached.Take(15))
            {
                var line = $"• **{msg!.Author.Username}** <t:{msg.Timestamp.ToUnixTimeSeconds()}:R>: " +
                           $"{Truncate(msg.Content ?? "_(leer)_", 80)}";
                list.AppendLine(line);
            }
            if (cached.Count > 15)
                list.AppendLine($"… und {cached.Count - 15} weitere (im Cache)");
            embed.AddField(Field("Nachrichtenliste (aus Cache)", list.ToString()));
        }

        await LogAsync(channel.Guild, LoggingConfig.MessageLogChannelId, embed);
    }

    // ════════════════════════════════════════════════════════════
    //  ROLLEN-LOGS
    // ════════════════════════════════════════════════════════════

    private async Task OnRoleCreatedAsync(SocketRole role)
    {
        var executor = await TryGetAuditEntryAsync(role.Guild, ActionType.RoleCreated);

        var embed = EmbedFactory.Create()
            .WithTitle("➕ Rolle erstellt")
            .WithDescription($"**Name:** {role.Mention} (`{role.Id}`)\n" +
                             $"**Farbe:** #{role.Colors.PrimaryColor.RawValue:X6}\n" +
                             $"**Angezeigt (hoist):** {(role.IsHoisted ? "Ja" : "Nein")}\n" +
                             $"**Erwähnbar:** {(role.IsMentionable ? "Ja" : "Nein")}\n" +
                             $"**Position:** {role.Position}\n" +
                             $"**Erstellt von:** {(executor?.User is not null ? $"{executor.User.Mention} (`{executor.User.Id}`)" : "Unbekannt")}")
            .AddField(Field("Berechtigungen", FormatPermissions(role.Permissions)))
            .WithCurrentTimestamp();

        await LogAsync(role.Guild, LoggingConfig.RoleLogChannelId, embed);
    }

    private async Task OnRoleDeletedAsync(SocketRole role)
    {
        var executor = await TryGetAuditEntryAsync(role.Guild, ActionType.RoleDeleted);

        var embed = EmbedFactory.Create()
            .WithTitle("➖ Rolle gelöscht")
            .WithDescription($"**Name:** {role.Name} (`{role.Id}`)\n" +
                             $"**Farbe:** #{role.Colors.PrimaryColor.RawValue:X6}\n" +
                             $"**Gelöscht von:** {(executor?.User is not null ? $"{executor.User.Mention} (`{executor.User.Id}`)" : "Unbekannt")}")
            .AddField(Field("Hatte diese Berechtigungen", FormatPermissions(role.Permissions)))
            .WithCurrentTimestamp();

        await LogAsync(role.Guild, LoggingConfig.RoleLogChannelId, embed);
    }

    private async Task OnRoleUpdatedAsync(SocketRole before, SocketRole after)
    {
        var changes = new List<EmbedFieldBuilder>();

        void Add(string name, object? b, object? a)
        {
            if (!Equals(b, a))
                changes.Add(Field(name, $"**Vorher:** {b ?? "—"}\n**Nachher:** {a ?? "—"}"));
        }

        Add("Name", before.Name, after.Name);
        Add("Farbe", $"#{before.Colors.PrimaryColor.RawValue:X6}", $"#{after.Colors.PrimaryColor.RawValue:X6}");
        Add("Angezeigt (hoist)", before.IsHoisted, after.IsHoisted);
        Add("Erwähnbar", before.IsMentionable, after.IsMentionable);
        Add("Position", before.Position, after.Position);

        // Berechtigungen diff
        var permAdded = after.Permissions.RawValue & ~before.Permissions.RawValue;
        var permRemoved = before.Permissions.RawValue & ~after.Permissions.RawValue;
        if (permAdded != 0)
            changes.Add(Field("➕ Berechtigungen hinzugefügt",
                FormatPermissionBits(permAdded)));
        if (permRemoved != 0)
            changes.Add(Field("➖ Berechtigungen entfernt",
                FormatPermissionBits(permRemoved)));

        if (changes.Count == 0) return;

        var executor = await TryGetAuditEntryAsync(after.Guild, ActionType.RoleUpdated);
        var embed = EmbedFactory.Create()
            .WithTitle("✏️ Rolle bearbeitet")
            .WithDescription($"**Rolle:** {after.Mention} (`{after.Id}`)\n" +
                             $"**Bearbeitet von:** {(executor?.User is not null ? $"{executor.User.Mention} (`{executor.User.Id}`)" : "Unbekannt")}")
            .WithCurrentTimestamp();
        foreach (var f in changes.Take(25)) embed.AddField(f);

        await LogAsync(after.Guild, LoggingConfig.RoleLogChannelId, embed);
    }

    // ════════════════════════════════════════════════════════════
    //  HILFS-METHODEN
    // ════════════════════════════════════════════════════════════

    private async Task LogAsync(SocketGuild guild, ulong channelId, EmbedBuilder embed)
    {
        try
        {
            if (guild.GetTextChannel(channelId) is not { } ch) return;
            await ch.SendMessageAsync(embed: embed.Build());
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Logging fehlgeschlagen (Kanal {Id}).", channelId);
        }
    }

    private async Task<RestAuditLogEntry?> TryGetAuditEntryAsync(SocketGuild guild, ActionType action, int maxAgeSeconds = 5)
    {
        try
        {
            var logs = await guild.GetAuditLogsAsync(5, actionType: action).FlattenAsync();
            var cutoff = DateTimeOffset.UtcNow.AddSeconds(-maxAgeSeconds);
            return logs.FirstOrDefault(l => l.CreatedAt >= cutoff);
        }
        catch { return null; }
    }

    private static EmbedFieldBuilder Field(string name, string value)
        => new EmbedFieldBuilder().WithName(name).WithValue(Truncate(value, 1024)).WithIsInline(false);

    private static string Truncate(string s, int max)
        => s.Length <= max ? s : s[..(max - 3)] + "…";

    private static string FormatChannelType(SocketGuildChannel ch) => ch switch
    {
        SocketCategoryChannel => "Kategorie",
        SocketVoiceChannel    => "Sprachkanal",
        SocketTextChannel     => "Textkanal",
        _                     => ch.GetType().Name,
    };

    private static string FormatPermissions(ChannelPermissions p) =>
        FormatPermissionBits((ulong)p.RawValue);

    private static string FormatPermissions(GuildPermissions p) =>
        FormatPermissionBits(p.RawValue);

    private static string FormatPermissionBits(ulong raw)
    {
        if (raw == 0) return "Keine";
        var perms = (GuildPermission)raw;
        var names = Enum.GetValues<GuildPermission>()
            .Where(f => perms.HasFlag(f))
            .Select(f => f switch
            {
                GuildPermission.Administrator        => "Administrator",
                GuildPermission.ManageGuild          => "Server verwalten",
                GuildPermission.ManageChannels       => "Kanäle verwalten",
                GuildPermission.ManageRoles          => "Rollen verwalten",
                GuildPermission.ManageMessages       => "Nachrichten verwalten",
                GuildPermission.BanMembers           => "Mitglieder bannen",
                GuildPermission.KickMembers          => "Mitglieder kicken",
                GuildPermission.ModerateMembers      => "Mitglieder moderieren",
                GuildPermission.MentionEveryone      => "@everyone erwähnen",
                GuildPermission.ManageWebhooks       => "Webhooks verwalten",
                GuildPermission.ManageNicknames      => "Spitznamen verwalten",
                GuildPermission.ViewAuditLog         => "Audit-Log einsehen",
                GuildPermission.SendMessages         => "Nachrichten senden",
                GuildPermission.ReadMessageHistory   => "Nachrichtenverlauf lesen",
                GuildPermission.ViewChannel          => "Kanal ansehen",
                GuildPermission.Connect              => "Verbinden (Voice)",
                GuildPermission.Speak                => "Sprechen",
                GuildPermission.MuteMembers          => "Mitglieder stummschalten",
                GuildPermission.DeafenMembers        => "Mitglieder taubschalten",
                GuildPermission.MoveMembers          => "Mitglieder verschieben",
                GuildPermission.AttachFiles          => "Dateien anhängen",
                GuildPermission.EmbedLinks           => "Links einbetten",
                GuildPermission.AddReactions         => "Reaktionen hinzufügen",
                GuildPermission.UseApplicationCommands => "App-Befehle nutzen",
                _                                    => f.ToString(),
            });
        return string.Join(", ", names);
    }
}
