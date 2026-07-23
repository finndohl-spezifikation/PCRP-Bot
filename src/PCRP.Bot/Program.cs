using Discord;
using Discord.Interactions;
using Discord.WebSocket;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using PCRP.Bot.Services;

var builder = Host.CreateApplicationBuilder(args);

builder.Services.AddSingleton(new DiscordSocketConfig
{
    GatewayIntents = GatewayIntents.Guilds
                   | GatewayIntents.GuildMessages
                   | GatewayIntents.MessageContent
                   | GatewayIntents.GuildMembers
                   | GatewayIntents.GuildBans
                   | GatewayIntents.GuildInvites       // Einladungen erstellt/gelöscht
                   | GatewayIntents.GuildVoiceStates,  // Voice-Beitritte/-Verlassen
    LogLevel = LogSeverity.Info,
    AlwaysDownloadUsers = true, // Mitglieder immer vorabraden (nötig für GuildMemberUpdated-Cache)
    MessageCacheSize = 1000,    // Nachrichten im Cache halten (nötig für Message-Logs)
});
builder.Services.AddSingleton<DiscordSocketClient>();
builder.Services.AddSingleton(sp =>
    new InteractionService(sp.GetRequiredService<DiscordSocketClient>()));

// LoggingService zuerst registrieren – ModerationService und GuildProtectionService nutzen es.
builder.Services.AddSingleton<LoggingService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<LoggingService>());

builder.Services.AddSingleton<ModerationService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<ModerationService>());
builder.Services.AddSingleton<GuildProtectionService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<GuildProtectionService>());
builder.Services.AddHostedService<BotService>();

await builder.Build().RunAsync();
