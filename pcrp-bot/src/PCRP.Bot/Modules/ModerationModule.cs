using Discord;
using Discord.Interactions;
using Discord.WebSocket;
using Microsoft.Extensions.Logging;
using PCRP.Bot.Common;
using PCRP.Bot.Services;

namespace PCRP.Bot.Modules;

/// <summary>
/// Moderations-Befehle: /löschen, /bannen, /entbannen, /timeout
/// Alle Aktionen werden automatisch in den Moderations-Log-Kanal geschrieben.
/// Der Inhaber (OwnerId) ist von keiner Einschränkung betroffen.
/// </summary>
public class ModerationModule : InteractionModuleBase<SocketInteractionContext>
{
    private readonly LoggingService _logging;
    private readonly ILogger<ModerationModule> _logger;

    public ModerationModule(LoggingService logging, ILogger<ModerationModule> logger)
    {
        _logging = logging;
        _logger = logger;
    }

    // ════════════════════════════════════════════════════════════
    //  /löschen
    // ════════════════════════════════════════════════════════════

    [SlashCommand("löschen", "Löscht 1–200 Nachrichten im aktuellen Kanal")]
    [RequireUserPermission(GuildPermission.ManageMessages)]
    [RequireBotPermission(GuildPermission.ManageMessages)]
    public async Task DeleteMessagesAsync(
        [Summary("anzahl", "Anzahl der zu löschenden Nachrichten (1–200)")]
        [MinValue(1), MaxValue(200)] int anzahl)
    {
        await DeferAsync(ephemeral: true);

        if (Context.Channel is not SocketTextChannel channel)
        {
            await FollowupAsync(embed: EmbedFactory.Build("Fehler", "Dieser Befehl kann nur in Text-Kanälen verwendet werden."), ephemeral: true);
            return;
        }

        try
        {
            // Nachrichten abrufen (Discord gibt max. 100 auf einmal zurück, daher ggf. mehrere Batches)
            var allMessages = new List<IMessage>();
            IMessage? lastMessage = null;
            var cutoff = DateTimeOffset.UtcNow.AddDays(-14); // Discord: Bulk-Delete nur für Nachrichten < 14 Tage

            while (allMessages.Count < anzahl)
            {
                var batch = lastMessage is null
                    ? await channel.GetMessagesAsync(Math.Min(100, anzahl - allMessages.Count)).FlattenAsync()
                    : await channel.GetMessagesAsync(lastMessage, Direction.Before, Math.Min(100, anzahl - allMessages.Count)).FlattenAsync();

                var batchList = batch.ToList();
                if (batchList.Count == 0) break;

                allMessages.AddRange(batchList);
                lastMessage = batchList.Last();
            }

            var toDelete = allMessages.Where(m => m.Timestamp >= cutoff).ToList();
            var tooOld   = allMessages.Count - toDelete.Count;

            if (toDelete.Count == 0)
            {
                await FollowupAsync(embed: EmbedFactory.Build("Keine Nachrichten gefunden",
                    "Es wurden keine Nachrichten gefunden, die gelöscht werden können.\n" +
                    "_(Nachrichten älter als 14 Tage können nicht per Bulk-Delete gelöscht werden.)_"),
                    ephemeral: true);
                return;
            }

            await channel.DeleteMessagesAsync(toDelete);

            var desc = $"✅ **{toDelete.Count} Nachricht{(toDelete.Count == 1 ? "" : "en")} gelöscht**\n" +
                       $"**Kanal:** {channel.Mention}\n" +
                       $"**Ausgeführt von:** {Context.User.Mention}";
            if (tooOld > 0)
                desc += $"\n⚠️ {tooOld} Nachricht{(tooOld == 1 ? "" : "en")} übersprungen (älter als 14 Tage)";

            await FollowupAsync(embed: EmbedFactory.Build("Nachrichten gelöscht", desc), ephemeral: true);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Fehler beim Löschen von Nachrichten.");
            await FollowupAsync(embed: EmbedFactory.Build("Fehler",
                "Die Nachrichten konnten nicht gelöscht werden. Prüfe die Bot-Berechtigungen."), ephemeral: true);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  /bannen
    // ════════════════════════════════════════════════════════════

    [SlashCommand("bannen", "Bannt ein Mitglied permanent vom Server")]
    [RequireUserPermission(GuildPermission.BanMembers)]
    [RequireBotPermission(GuildPermission.BanMembers)]
    public async Task BanAsync(
        [Summary("mitglied", "Das Mitglied, das gebannt werden soll")] SocketGuildUser mitglied,
        [Summary("grund", "Grund für den Bann (erscheint im Audit-Log und in der DM)")] string grund = "Kein Grund angegeben")
    {
        await DeferAsync(ephemeral: true);

        // Sicherheitsprüfungen
        if (mitglied.Id == Context.User.Id)
        {
            await FollowupAsync(embed: EmbedFactory.Build("Fehler", "Du kannst dich nicht selbst bannen."), ephemeral: true);
            return;
        }
        if (mitglied.Id == Context.Client.CurrentUser.Id)
        {
            await FollowupAsync(embed: EmbedFactory.Build("Fehler", "Den Bot selbst zu bannen ist nicht möglich."), ephemeral: true);
            return;
        }
        // Rollen-Hierarchie prüfen (außer wenn Ausführender der Inhaber ist)
        if (Context.User.Id != ModerationConfig.OwnerId)
        {
            var executor = Context.Guild.GetUser(Context.User.Id);
            if (executor is not null && mitglied.Hierarchy >= executor.Hierarchy)
            {
                await FollowupAsync(embed: EmbedFactory.Build("Fehler",
                    "Du kannst kein Mitglied bannen, das die gleiche oder eine höhere Rolle als du hat."), ephemeral: true);
                return;
            }
        }

        try
        {
            // Zuerst DM senden (vor dem Bann, solange Nutzer noch auf dem Server ist)
            await ModerationService.TrySendDmAsync(mitglied, EmbedFactory.Build(
                "Du wurdest gebannt",
                $"Du wurdest von **{Context.Guild.Name}** permanent gebannt.\n\n" +
                $"**Grund:** {grund}\n" +
                $"**Gebannt von:** {Context.User.Username}"));

            // Bann ausführen
            await Context.Guild.AddBanAsync(mitglied, 0, grund);

            await _logging.LogModerationAsync(Context.Guild,
                "🔨 Mitglied gebannt (Befehl)",
                $"**Gebanntes Mitglied:** {mitglied.Mention} | {mitglied.Username} (`{mitglied.Id}`)\n" +
                $"**Gebannt von:** {Context.User.Mention} | {Context.User.Username} (`{Context.User.Id}`)\n" +
                $"**Grund:** {grund}\n" +
                $"**Art:** Permanenter Bann · DM gesendet");

            await FollowupAsync(embed: EmbedFactory.Build("Mitglied gebannt",
                $"✅ **{mitglied.Username}** wurde permanent gebannt.\n" +
                $"**Grund:** {grund}\n" +
                $"**DM:** gesendet"), ephemeral: true);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Fehler beim Bannen von {User}.", mitglied.Username);
            await FollowupAsync(embed: EmbedFactory.Build("Fehler",
                "Der Bann konnte nicht ausgeführt werden. Prüfe die Rollen-Hierarchie und Bot-Berechtigungen."), ephemeral: true);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  /entbannen
    // ════════════════════════════════════════════════════════════

    [SlashCommand("entbannen", "Hebt den Bann eines Mitglieds auf")]
    [RequireUserPermission(GuildPermission.BanMembers)]
    [RequireBotPermission(GuildPermission.BanMembers)]
    public async Task UnbanAsync(
        [Summary("nutzer", "Name oder ID des gebannten Nutzers (Vorschläge erscheinen beim Tippen)")]
        [Autocomplete(typeof(BanListAutocompleteHandler))] string nutzerId)
    {
        await DeferAsync(ephemeral: true);

        if (!ulong.TryParse(nutzerId, out var userId))
        {
            await FollowupAsync(embed: EmbedFactory.Build("Ungültige Eingabe",
                "Bitte wähle einen Nutzer aus der Vorschlagsliste oder gib eine gültige Nutzer-ID ein."), ephemeral: true);
            return;
        }

        try
        {
            var ban = await Context.Guild.GetBanAsync(userId);
            if (ban is null)
            {
                await FollowupAsync(embed: EmbedFactory.Build("Nicht gefunden",
                    $"Kein Bann für Nutzer-ID `{userId}` gefunden."), ephemeral: true);
                return;
            }

            await Context.Guild.RemoveBanAsync(userId);

            await _logging.LogModerationAsync(Context.Guild,
                "✅ Bann aufgehoben (Befehl)",
                $"**Entbannter Nutzer:** {ban.User.Username} (`{ban.User.Id}`)\n" +
                $"**Entbannt von:** {Context.User.Mention} | {Context.User.Username} (`{Context.User.Id}`)\n" +
                $"**Ursprünglicher Bann-Grund:** {ban.Reason ?? "Nicht angegeben"}");

            await FollowupAsync(embed: EmbedFactory.Build("Bann aufgehoben",
                $"✅ Der Bann von **{ban.User.Username}** (`{ban.User.Id}`) wurde aufgehoben."), ephemeral: true);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Fehler beim Entbannen von ID {Id}.", userId);
            await FollowupAsync(embed: EmbedFactory.Build("Fehler",
                "Der Bann konnte nicht aufgehoben werden. Prüfe die Bot-Berechtigungen."), ephemeral: true);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  /timeout
    // ════════════════════════════════════════════════════════════

    [SlashCommand("timeout", "Gibt einem Mitglied einen Timeout")]
    [RequireUserPermission(GuildPermission.ModerateMembers)]
    [RequireBotPermission(GuildPermission.ModerateMembers)]
    public async Task TimeoutAsync(
        [Summary("mitglied", "Das Mitglied, das einen Timeout erhalten soll")] SocketGuildUser mitglied,
        [Summary("dauer", "Wie lange soll der Timeout dauern?")]
        [Choice("5 Minuten",  "5m"),  Choice("10 Minuten", "10m"), Choice("30 Minuten", "30m"),
         Choice("1 Stunde",   "1h"),  Choice("6 Stunden",  "6h"),  Choice("12 Stunden", "12h"),
         Choice("1 Tag",      "1d"),  Choice("3 Tage",     "3d"),  Choice("7 Tage",     "7d"),
         Choice("14 Tage",    "14d")] string dauer,
        [Summary("grund", "Grund für den Timeout")] string grund = "Kein Grund angegeben")
    {
        await DeferAsync(ephemeral: true);

        // Sicherheitsprüfungen
        if (mitglied.Id == Context.User.Id)
        {
            await FollowupAsync(embed: EmbedFactory.Build("Fehler", "Du kannst dich nicht selbst mit einem Timeout belegen."), ephemeral: true);
            return;
        }
        if (mitglied.Id == ModerationConfig.OwnerId)
        {
            await FollowupAsync(embed: EmbedFactory.Build("Fehler", "Der Inhaber kann nicht mit einem Timeout belegt werden."), ephemeral: true);
            return;
        }
        if (Context.User.Id != ModerationConfig.OwnerId)
        {
            var executor = Context.Guild.GetUser(Context.User.Id);
            if (executor is not null && mitglied.Hierarchy >= executor.Hierarchy)
            {
                await FollowupAsync(embed: EmbedFactory.Build("Fehler",
                    "Du kannst kein Mitglied mit einem Timeout belegen, das die gleiche oder eine höhere Rolle als du hat."), ephemeral: true);
                return;
            }
        }

        try
        {
            var duration = ParseDuration(dauer);
            var until = DateTimeOffset.UtcNow + duration;

            // DM senden bevor Timeout
            await ModerationService.TrySendDmAsync(mitglied, EmbedFactory.Build(
                "Du hast einen Timeout erhalten",
                $"Du hast auf **{Context.Guild.Name}** einen Timeout erhalten.\n\n" +
                $"**Dauer:** {FormatDuration(duration)}\n" +
                $"**Grund:** {grund}\n" +
                $"**Gegeben von:** {Context.User.Username}\n" +
                $"**Timeout endet:** <t:{until.ToUnixTimeSeconds()}:F>"));

            await mitglied.SetTimeOutAsync(duration);

            await _logging.LogModerationAsync(Context.Guild,
                "⏱️ Timeout vergeben (Befehl)",
                $"**Mitglied:** {mitglied.Mention} | {mitglied.Username} (`{mitglied.Id}`)\n" +
                $"**Gegeben von:** {Context.User.Mention} | {Context.User.Username} (`{Context.User.Id}`)\n" +
                $"**Dauer:** {FormatDuration(duration)}\n" +
                $"**Endet:** <t:{until.ToUnixTimeSeconds()}:F>\n" +
                $"**Grund:** {grund}\n" +
                $"**DM:** gesendet");

            await FollowupAsync(embed: EmbedFactory.Build("Timeout vergeben",
                $"✅ **{mitglied.Username}** hat einen Timeout für **{FormatDuration(duration)}** erhalten.\n" +
                $"**Grund:** {grund}\n" +
                $"**Endet:** <t:{until.ToUnixTimeSeconds()}:F>"), ephemeral: true);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Fehler beim Timeout für {User}.", mitglied.Username);
            await FollowupAsync(embed: EmbedFactory.Build("Fehler",
                "Der Timeout konnte nicht vergeben werden. Prüfe die Rollen-Hierarchie und Bot-Berechtigungen."), ephemeral: true);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  HILFS-METHODEN
    // ════════════════════════════════════════════════════════════

    private static TimeSpan ParseDuration(string dauer) => dauer switch
    {
        "5m"  => TimeSpan.FromMinutes(5),
        "10m" => TimeSpan.FromMinutes(10),
        "30m" => TimeSpan.FromMinutes(30),
        "1h"  => TimeSpan.FromHours(1),
        "6h"  => TimeSpan.FromHours(6),
        "12h" => TimeSpan.FromHours(12),
        "1d"  => TimeSpan.FromDays(1),
        "3d"  => TimeSpan.FromDays(3),
        "7d"  => TimeSpan.FromDays(7),
        "14d" => TimeSpan.FromDays(14),
        _     => TimeSpan.FromMinutes(10),
    };

    private static string FormatDuration(TimeSpan d)
    {
        if (d.TotalDays >= 1)   return $"{(int)d.TotalDays} Tag{((int)d.TotalDays == 1 ? "" : "e")}";
        if (d.TotalHours >= 1)  return $"{(int)d.TotalHours} Stunde{((int)d.TotalHours == 1 ? "" : "n")}";
        return $"{(int)d.TotalMinutes} Minute{((int)d.TotalMinutes == 1 ? "" : "n")}";
    }
}

/// <summary>
/// Autocomplete-Handler für /entbannen: zeigt die Bannliste des Servers als Vorschläge an.
/// </summary>
public class BanListAutocompleteHandler : AutocompleteHandler
{
    public override async Task<AutocompletionResult> GenerateSuggestionsAsync(
        IInteractionContext context,
        IAutocompleteInteraction autocompleteInteraction,
        IParameterInfo parameter,
        IServiceProvider services)
    {
        try
        {
            var query = autocompleteInteraction.Data.Current.Value?.ToString() ?? "";
            var bans = await context.Guild.GetBansAsync().FlattenAsync();

            var results = bans
                .Where(b => string.IsNullOrWhiteSpace(query)
                    || b.User.Username.Contains(query, StringComparison.OrdinalIgnoreCase)
                    || b.User.Id.ToString().Contains(query))
                .Take(25)
                .Select(b => new AutocompleteResult(
                    $"{b.User.Username} ({b.User.Id})" +
                    (string.IsNullOrWhiteSpace(b.Reason) ? "" : $" – {b.Reason[..Math.Min(b.Reason.Length, 40)]}"),
                    b.User.Id.ToString()));

            return AutocompletionResult.FromSuccess(results);
        }
        catch
        {
            return AutocompletionResult.FromSuccess(Enumerable.Empty<AutocompleteResult>());
        }
    }
}
