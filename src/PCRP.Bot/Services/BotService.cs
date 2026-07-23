using System.Reflection;
using Discord;
using Discord.Interactions;
using Discord.WebSocket;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace PCRP.Bot.Services;

/// <summary>
/// Startet den Discord-Client, registriert Slash Commands und leitet
/// Interactions an die Module weiter.
/// </summary>
public class BotService : BackgroundService
{
    private readonly DiscordSocketClient _client;
    private readonly InteractionService _interactions;
    private readonly IServiceProvider _services;
    private readonly ILogger<BotService> _logger;

    public BotService(
        DiscordSocketClient client,
        InteractionService interactions,
        IServiceProvider services,
        ILogger<BotService> logger)
    {
        _client = client;
        _interactions = interactions;
        _services = services;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var token = Environment.GetEnvironmentVariable("DISCORD_BOT_TOKEN");
        if (string.IsNullOrWhiteSpace(token))
        {
            _logger.LogCritical("DISCORD_BOT_TOKEN ist nicht gesetzt. Bot kann nicht starten.");
            return;
        }

        _client.Log += OnLogAsync;
        _interactions.Log += OnLogAsync;
        _client.Ready += OnReadyAsync;
        _client.InteractionCreated += OnInteractionAsync;

        await _interactions.AddModulesAsync(Assembly.GetExecutingAssembly(), _services);

        await _client.LoginAsync(TokenType.Bot, token);
        await _client.StartAsync();

        // Läuft, bis der Host gestoppt wird.
        await Task.Delay(Timeout.Infinite, stoppingToken).ContinueWith(_ => { });

        await _client.StopAsync();
    }

    private async Task OnReadyAsync()
    {
        // Global registrieren – auf allen Servern verfügbar.
        await _interactions.RegisterCommandsGloballyAsync();
        _logger.LogInformation("Bot ist bereit. Eingeloggt als {User}.", _client.CurrentUser);
    }

    private async Task OnInteractionAsync(SocketInteraction interaction)
    {
        try
        {
            var context = new SocketInteractionContext(_client, interaction);
            await _interactions.ExecuteCommandAsync(context, _services);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Fehler beim Verarbeiten einer Interaction.");
            if (interaction.Type == InteractionType.ApplicationCommand)
            {
                var response = await interaction.GetOriginalResponseAsync();
                if (response is not null)
                    await response.DeleteAsync();
            }
        }
    }

    private Task OnLogAsync(LogMessage message)
    {
        var level = message.Severity switch
        {
            LogSeverity.Critical => LogLevel.Critical,
            LogSeverity.Error => LogLevel.Error,
            LogSeverity.Warning => LogLevel.Warning,
            LogSeverity.Info => LogLevel.Information,
            LogSeverity.Verbose => LogLevel.Debug,
            _ => LogLevel.Trace,
        };
        _logger.Log(level, message.Exception, "[{Source}] {Message}", message.Source, message.Message);
        return Task.CompletedTask;
    }
}
