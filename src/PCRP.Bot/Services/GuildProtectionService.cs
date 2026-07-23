using System.Collections.Concurrent;
using Discord;
using Discord.Rest;
using Discord.WebSocket;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using PCRP.Bot.Common;

namespace PCRP.Bot.Services;

/// <summary>
/// Anti-Nuke-Schutz:
///  - Fremde Bots werden beim Beitritt sofort permanent gebannt (DM an den Einladenden + Aktivitätswarnung)
///  - Massenhaftes Löschen von Kanälen/Kategorien/Rollen -> 14 Tage Timeout, DM, Aktivitätswarnung
///    und automatische Wiederherstellung (gleicher Name, gleiche Berechtigungen, bei Rollen gleiche Farbe)
/// Der Inhaber ist von allen Einschränkungen ausgenommen.
/// </summary>
public class GuildProtectionService : BackgroundService
{
    private readonly DiscordSocketClient _client;
    private readonly ModerationService _moderation;
    private readonly ILogger<GuildProtectionService> _logger;

    // Lösch-Tracking pro Nutzer
    private readonly ConcurrentDictionary<ulong, List<DateTimeOffset>> _deletions = new();
    private readonly ConcurrentDictionary<ulong, DateTimeOffset> _flagged = new();

    public GuildProtectionService(DiscordSocketClient client, ModerationService moderation, ILogger<GuildProtectionService> logger)
    {
        _client = client;
        _moderation = moderation;
        _logger = logger;
    }

    protected override Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _client.UserJoined += OnUserJoinedAsync;
        _client.ChannelDestroyed += OnChannelDestroyedAsync;
        _client.RoleDeleted += OnRoleDeletedAsync;
        return Task.CompletedTask;
    }

    // ---------- Fremde Bots ----------

    private async Task OnUserJoinedAsync(SocketGuildUser user)
    {
        if (!user.IsBot || user.Id == _client.CurrentUser.Id) return;

        try
        {
            // Einladenden über das Audit-Log ermitteln.
            IUser? inviter = null;
            var logs = await user.Guild.GetAuditLogsAsync(5, actionType: ActionType.BotAdded).FlattenAsync();
            var entry = logs.FirstOrDefault(l => l.Data is BotAddAuditLogData data && data.Target.Id == user.Id);
            inviter = entry?.User;

            // Bot permanent bannen.
            await user.Guild.AddBanAsync(user, reason: "Anti-Nuke-Schutz: Fremde Bots sind nicht erlaubt.");

            if (inviter is not null && inviter.Id != ModerationConfig.OwnerId)
            {
                await ModerationService.TrySendDmAsync(inviter, EmbedFactory.Build(
                    "Anti-Nuke-Schutz aktiv",
                    "Auf **PCRP** ist der Anti-Nuke-Schutz aktiv, daher können **keine fremden Discord-Bots eingeladen werden**.\n\n" +
                    $"Der Bot **{user.Username}** wurde **permanent gebannt**."));
            }

            await _moderation.SendAlertAsync(user.Guild,
                "Aktivitätswarnung – Anti-Nuke (Fremder Bot)",
                $"**Versuch:** Ein fremder Bot wurde auf den Server eingeladen.\n" +
                $"**Bot:** {user.Username} (`{user.Id}`) – wurde **permanent gebannt**.\n" +
                $"**Eingeladen von:** {(inviter is not null ? $"{inviter.Mention} (`{inviter.Id}`)" : "Unbekannt")}");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Fehler beim Bannen eines fremden Bots.");
        }
    }

    // ---------- Kanäle / Rollen löschen ----------

    private async Task OnChannelDestroyedAsync(SocketChannel channel)
    {
        if (channel is not SocketGuildChannel guildChannel) return;

        try
        {
            var executor = await FindExecutorAsync(guildChannel.Guild, ActionType.ChannelDeleted);
            if (executor is null || executor.Id == ModerationConfig.OwnerId || executor.Id == _client.CurrentUser.Id)
                return;

            var triggered = RegisterDeletion(executor.Id);
            if (triggered || IsFlagged(executor.Id))
            {
                if (triggered)
                    await PunishAsync(guildChannel.Guild, executor, "Kanäle/Kategorien");

                await RestoreChannelAsync(guildChannel);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Fehler beim Verarbeiten einer Kanal-Löschung.");
        }
    }

    private async Task OnRoleDeletedAsync(SocketRole role)
    {
        try
        {
            var executor = await FindExecutorAsync(role.Guild, ActionType.RoleDeleted);
            if (executor is null || executor.Id == ModerationConfig.OwnerId || executor.Id == _client.CurrentUser.Id)
                return;

            var triggered = RegisterDeletion(executor.Id);
            if (triggered || IsFlagged(executor.Id))
            {
                if (triggered)
                    await PunishAsync(role.Guild, executor, "Rollen");

                await role.Guild.CreateRoleAsync(
                    role.Name,
                    role.Permissions,
                    role.Colors.PrimaryColor,
                    role.IsHoisted,
                    role.IsMentionable);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Fehler beim Verarbeiten einer Rollen-Löschung.");
        }
    }

    private static async Task RestoreChannelAsync(SocketGuildChannel channel)
    {
        var guild = channel.Guild;
        var overwrites = channel.PermissionOverwrites;

        switch (channel)
        {
            case SocketCategoryChannel category:
                await guild.CreateCategoryChannelAsync(category.Name, p =>
                {
                    p.Position = category.Position;
                    p.PermissionOverwrites = new Optional<IEnumerable<Overwrite>>(overwrites);
                });
                break;

            case SocketVoiceChannel voice:
                await guild.CreateVoiceChannelAsync(voice.Name, p =>
                {
                    p.Position = voice.Position;
                    p.CategoryId = voice.CategoryId ?? Optional<ulong?>.Unspecified;
                    p.PermissionOverwrites = new Optional<IEnumerable<Overwrite>>(overwrites);
                });
                break;

            case SocketTextChannel text:
                await guild.CreateTextChannelAsync(text.Name, p =>
                {
                    p.Position = text.Position;
                    p.CategoryId = text.CategoryId ?? Optional<ulong?>.Unspecified;
                    p.Topic = text.Topic ?? Optional<string>.Unspecified;
                    p.IsNsfw = text.IsNsfw;
                    p.SlowModeInterval = text.SlowModeInterval;
                    p.PermissionOverwrites = new Optional<IEnumerable<Overwrite>>(overwrites);
                });
                break;
        }
    }

    private async Task PunishAsync(SocketGuild guild, IUser executor, string whatWasDeleted)
    {
        if (guild.GetUser(executor.Id) is { } member)
        {
            await member.SetTimeOutAsync(ModerationConfig.ProtectionTimeout);
        }

        await ModerationService.TrySendDmAsync(executor, EmbedFactory.Build(
            "Serverschutz aktiv",
            "Auf **PCRP** ist der Serverschutz aktiv.\n\n" +
            $"Du hast in kürzester Zeit mehrere **{whatWasDeleted}** gelöscht und daher zur Sicherheit einen " +
            "**14-tägigen Timeout** erhalten, bis entschieden wurde, ob dieses Handeln legitim war.\n\n" +
            "Wenn alles passt, wird der Timeout **sofort aufgehoben**."));

        await _moderation.SendAlertAsync(guild,
            "Aktivitätswarnung – Anti-Nuke (Massenlöschung)",
            $"**Nutzer:** {executor.Mention} (`{executor.Id}`)\n" +
            $"**Versuch:** Es wurden in kürzester Zeit mehrere **{whatWasDeleted}** gelöscht.\n" +
            $"**Maßnahmen:** 14 Tage Timeout vergeben, gelöschte Inhalte werden automatisch wiederhergestellt.");
    }

    private bool RegisterDeletion(ulong userId)
    {
        var now = DateTimeOffset.UtcNow;
        var list = _deletions.GetOrAdd(userId, _ => new List<DateTimeOffset>());

        lock (list)
        {
            list.Add(now);
            list.RemoveAll(t => now - t > ModerationConfig.MassDeleteWindow);

            if (list.Count >= ModerationConfig.MassDeleteLimit && !IsFlagged(userId))
            {
                _flagged[userId] = now;
                return true;
            }
        }
        return false;
    }

    private bool IsFlagged(ulong userId)
        => _flagged.TryGetValue(userId, out var since) && DateTimeOffset.UtcNow - since < TimeSpan.FromMinutes(10);

    private async Task<IUser?> FindExecutorAsync(SocketGuild guild, ActionType actionType)
    {
        try
        {
            var logs = await guild.GetAuditLogsAsync(1, actionType: actionType).FlattenAsync();
            var entry = logs.FirstOrDefault();
            // Nur frische Einträge akzeptieren (max. 30 Sekunden alt).
            if (entry is null || DateTimeOffset.UtcNow - entry.CreatedAt > TimeSpan.FromSeconds(30))
                return null;
            return entry.User;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Audit-Log konnte nicht gelesen werden.");
            return null;
        }
    }
}
