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
                   | GatewayIntents.GuildBans,
    LogLevel = LogSeverity.Info,
});
builder.Services.AddSingleton<DiscordSocketClient>();
builder.Services.AddSingleton(sp =>
    new InteractionService(sp.GetRequiredService<DiscordSocketClient>()));

builder.Services.AddSingleton<ModerationService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<ModerationService>());
builder.Services.AddSingleton<GuildProtectionService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<GuildProtectionService>());
builder.Services.AddHostedService<BotService>();

await builder.Build().RunAsync();
