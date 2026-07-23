using System.Collections.Concurrent;
using System.Text.Json;
using System.Text.RegularExpressions;
using Discord;
using Discord.Webhook;
using Discord.WebSocket;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using PCRP.Bot.Common;

namespace PCRP.Bot.Services;

/// <summary>
/// Nachrichten-Moderation:
///  - Wortfilter (vulgäre Kraftausdrücke -> sofort löschen)
///  - Spamschutz (mehr als 7 Nachrichten in kürzester Zeit -> DM-Verwarnung, beim 2. Mal 10 Minuten Timeout)
///  - 67/sixseven -> wird automatisch zu 69/sixnine geändert
///  - Fremde Discord-Server-Links -> löschen, 14 Tage Timeout, DM + Aktivitätswarnung
/// Der Inhaber ist von allen Einschränkungen ausgenommen.
/// </summary>
public partial class ModerationService : BackgroundService
{
    private static readonly Regex InviteRegex = InvitePattern();
    private static readonly Regex SixSevenRegex = SixSevenPattern();

    [GeneratedRegex(@"(?:discord(?:app)?\.com/invite|discord\.gg)/([A-Za-z0-9-]+)", RegexOptions.IgnoreCase)]
    private static partial Regex InvitePattern();

    [GeneratedRegex(@"\b67\b|sixseven", RegexOptions.IgnoreCase)]
    private static partial Regex SixSevenPattern();

    private readonly DiscordSocketClient _client;
    private readonly LoggingService _logging;
    private readonly ILogger<ModerationService> _logger;

    // Spam-Tracking
    private readonly ConcurrentDictionary<ulong, Queue<DateTimeOffset>> _messageTimes = new();
    private readonly ConcurrentDictionary<ulong, DateTimeOffset> _lastSpamAction = new();
    private ConcurrentDictionary<ulong, int> _spamOffenses = new();
    private readonly string _offensesFile = DataStore.GetPath("spam_offenses.json");

    public ModerationService(DiscordSocketClient client, LoggingService logging, ILogger<ModerationService> logger)
    {
        _client = client;
        _logging = logging;
        _logger = logger;
    }

    protected override Task ExecuteAsync(CancellationToken stoppingToken)
    {
        LoadOffenses();
        _client.MessageReceived += OnMessageAsync;
        return Task.CompletedTask;
    }

    private async Task OnMessageAsync(SocketMessage rawMessage)
    {
        if (rawMessage is not SocketUserMessage message) return;
        if (message.Author.IsBot || message.Author.IsWebhook) return;
        if (message.Channel is not SocketTextChannel channel) return;
        if (message.Author is not SocketGuildUser user) return;

        // Der Inhaber hat keinerlei Einschränkungen.
        if (user.Id == ModerationConfig.OwnerId) return;

        try
        {
            // 1. Wortfilter – sofort löschen.
            if (WordFilter.TryGetBannedWord(message.Content, out var matchedWord))
            {
                await message.DeleteAsync();
                await _logging.LogModerationAsync(channel.Guild,
                    "🔤 Wortfilter ausgelöst",
                    $"**Nutzer:** {user.Mention} | {user.Username} (`{user.Id}`)\n" +
                    $"**Kanal:** {channel.Mention}\n" +
                    $"**Erkanntes Wort:** `{matchedWord}`\n" +
                    $"**Aktion:** Nachricht sofort gelöscht\n" +
                    $"**Nachrichteninhalt:**\n```\n{(message.Content.Length > 800 ? message.Content[..800] + "…" : message.Content)}\n```");
                return;
            }

            // 2. Fremde Discord-Server-Links – absolutes Tabu.
            if (await HandleForeignInviteAsync(message, channel, user))
                return;

            // 3. 67 / sixseven -> 69 / sixnine.
            if (SixSevenRegex.IsMatch(message.Content))
            {
                await ReplaceSixSevenAsync(message, channel, user);
                return;
            }

            // 4. Spamschutz.
            await HandleSpamAsync(message, user);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Fehler in der Nachrichten-Moderation.");
        }
    }

    // ---------- Fremde Server-Links ----------

    private async Task<bool> HandleForeignInviteAsync(SocketUserMessage message, SocketTextChannel channel, SocketGuildUser user)
    {
        var match = InviteRegex.Match(message.Content);
        if (!match.Success) return false;

        // Eigene Server-Invites sind erlaubt.
        var code = match.Groups[1].Value;
        try
        {
            var invite = await _client.GetInviteAsync(code);
            if (invite?.GuildId == channel.Guild.Id) return false;
        }
        catch
        {
            // Invite nicht auflösbar -> als fremd behandeln.
        }

        await message.DeleteAsync();
        await user.SetTimeOutAsync(ModerationConfig.ProtectionTimeout);

        await TrySendDmAsync(user, EmbedFactory.Build(
            "Schutz für Eigenwerbung aktiv",
            "Auf **PCRP** sind fremde Discord-Server-Links nicht erlaubt.\n\n" +
            "Deine Nachricht wurde gelöscht und du hast einen **14-tägigen Timeout** erhalten. " +
            "Dieses Handeln wurde an das Serverteam weitergeleitet und der Fall wird nun geprüft."));

        await SendAlertAsync(channel.Guild,
            "Aktivitätswarnung – Eigenwerbung",
            $"**Nutzer:** {user.Mention} (`{user.Id}`)\n" +
            $"**Kanal:** {channel.Mention}\n" +
            $"**Aktion:** Fremder Discord-Server-Link wurde gepostet und gelöscht, 14 Tage Timeout vergeben.\n" +
            $"**Link:** `{match.Value}`");

        await _logging.LogModerationAsync(channel.Guild,
            "🔗 Eigenwerbung – Link entfernt",
            $"**Nutzer:** {user.Mention} | {user.Username} (`{user.Id}`)\n" +
            $"**Kanal:** {channel.Mention}\n" +
            $"**Erkannter Link:** `{match.Value}`\n" +
            $"**Aktionen:** Nachricht gelöscht · 14 Tage Timeout vergeben · DM gesendet\n" +
            $"**Vollständiger Nachrichteninhalt:**\n```\n{(message.Content.Length > 700 ? message.Content[..700] + "…" : message.Content)}\n```");

        return true;
    }

    // ---------- 67 -> 69 ----------

    private async Task ReplaceSixSevenAsync(SocketUserMessage message, SocketTextChannel channel, SocketGuildUser user)
    {
        var fixedContent = SixSevenRegex.Replace(message.Content, m =>
            m.Value.Equals("67", StringComparison.Ordinal) ? "69" :
            m.Value.All(char.IsDigit) ? "69" : "sixnine");

        await _logging.LogModerationAsync(channel.Guild,
            "🔢 67-Filter ausgelöst",
            $"**Nutzer:** {user.Mention} | {user.Username} (`{user.Id}`)\n" +
            $"**Kanal:** {channel.Mention}\n" +
            $"**Aktion:** Nachricht gelöscht · erneut als korrigierte Version gepostet\n" +
            $"**Original:**\n```\n{(message.Content.Length > 450 ? message.Content[..450] + "…" : message.Content)}\n```\n" +
            $"**Korrigiert:**\n```\n{(fixedContent.Length > 450 ? fixedContent[..450] + "…" : fixedContent)}\n```");

        await message.DeleteAsync();

        // Über einen Webhook im Namen des Nutzers erneut senden.
        var webhooks = await channel.GetWebhooksAsync();
        var webhook = webhooks.FirstOrDefault(w => w.Name == "PCRP Moderation")
                      ?? await channel.CreateWebhookAsync("PCRP Moderation");

        using var webhookClient = new DiscordWebhookClient(webhook);
        await webhookClient.SendMessageAsync(
            fixedContent,
            username: user.DisplayName,
            avatarUrl: user.GetDisplayAvatarUrl() ?? user.GetDefaultAvatarUrl(),
            allowedMentions: AllowedMentions.None);
    }

    // ---------- Spamschutz ----------

    private async Task HandleSpamAsync(SocketUserMessage message, SocketGuildUser user)
    {
        var now = DateTimeOffset.UtcNow;
        var queue = _messageTimes.GetOrAdd(user.Id, _ => new Queue<DateTimeOffset>());

        int count;
        lock (queue)
        {
            queue.Enqueue(now);
            while (queue.Count > 0 && now - queue.Peek() > ModerationConfig.SpamWindow)
                queue.Dequeue();
            count = queue.Count;
        }

        if (count <= ModerationConfig.SpamMessageLimit) return;

        // Nicht mehrfach pro Spamwelle bestrafen.
        if (_lastSpamAction.TryGetValue(user.Id, out var last) && now - last < TimeSpan.FromSeconds(30))
            return;
        _lastSpamAction[user.Id] = now;

        var offenses = _spamOffenses.AddOrUpdate(user.Id, 1, (_, v) => v + 1);
        SaveOffenses();

        if (offenses == 1)
        {
            await TrySendDmAsync(user, EmbedFactory.Build(
                "Verwarnung – Spamschutz",
                "Du hast in kürzester Zeit zu viele Nachrichten auf **PCRP** gesendet.\n\n" +
                "Dies ist deine **Verwarnung**. Beim nächsten Verstoß erhältst du automatisch einen **10-minütigen Timeout**."));

            await _logging.LogModerationAsync(message.Channel is SocketTextChannel stc ? stc.Guild : user.Guild,
                "⚠️ Spam – Verwarnung ausgesprochen",
                $"**Nutzer:** {user.Mention} | {user.Username} (`{user.Id}`)\n" +
                $"**Kanal:** {(message.Channel is SocketTextChannel ch ? ch.Mention : "Unbekannt")}\n" +
                $"**Verstoß Nr.:** {offenses}\n" +
                $"**Aktion:** DM-Verwarnung gesendet (nächster Verstoß = 10 Min. Timeout)");
        }
        else
        {
            await user.SetTimeOutAsync(ModerationConfig.SpamTimeout);
            await TrySendDmAsync(user, EmbedFactory.Build(
                "Timeout – Spamschutz",
                "Du wurdest trotz Verwarnung erneut wegen Spam auffällig.\n\n" +
                "Du hast automatisch einen **10-minütigen Timeout** erhalten."));

            await _logging.LogModerationAsync(message.Channel is SocketTextChannel stc2 ? stc2.Guild : user.Guild,
                "🔇 Spam – 10 Min. Timeout vergeben",
                $"**Nutzer:** {user.Mention} | {user.Username} (`{user.Id}`)\n" +
                $"**Kanal:** {(message.Channel is SocketTextChannel ch2 ? ch2.Mention : "Unbekannt")}\n" +
                $"**Verstoß Nr.:** {offenses}\n" +
                $"**Aktion:** 10 Minuten Timeout · DM gesendet");
        }
    }

    // ---------- Helfer ----------

    private void LoadOffenses()
    {
        try
        {
            if (File.Exists(_offensesFile))
            {
                var data = JsonSerializer.Deserialize<Dictionary<ulong, int>>(File.ReadAllText(_offensesFile));
                if (data is not null)
                    _spamOffenses = new ConcurrentDictionary<ulong, int>(data);
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Spam-Verstöße konnten nicht geladen werden.");
        }
    }

    private void SaveOffenses()
    {
        try
        {
            File.WriteAllText(_offensesFile, JsonSerializer.Serialize(_spamOffenses.ToDictionary(k => k.Key, v => v.Value)));
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Spam-Verstöße konnten nicht gespeichert werden.");
        }
    }

    internal async Task SendAlertAsync(SocketGuild guild, string title, string description)
    {
        if (guild.GetTextChannel(ModerationConfig.AlertChannelId) is not { } alertChannel)
        {
            _logger.LogWarning("Aktivitätswarnungs-Kanal {Id} nicht gefunden.", ModerationConfig.AlertChannelId);
            return;
        }

        await alertChannel.SendMessageAsync(
            text: ModerationConfig.OwnerMention,
            embed: EmbedFactory.Build(title, description),
            allowedMentions: new AllowedMentions { UserIds = new List<ulong> { ModerationConfig.OwnerId } });
    }

    internal static async Task TrySendDmAsync(IUser user, Embed embed)
    {
        try
        {
            await user.SendMessageAsync(embed: embed);
        }
        catch
        {
            // DMs deaktiviert – ignorieren.
        }
    }
}
