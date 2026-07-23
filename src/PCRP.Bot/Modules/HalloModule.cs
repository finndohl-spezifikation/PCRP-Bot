using Discord.Interactions;
using PCRP.Bot.Common;

namespace PCRP.Bot.Modules;

public class HalloModule : InteractionModuleBase<SocketInteractionContext>
{
    [SlashCommand("hallo", "Der Bot begrüßt dich.")]
    public async Task HalloAsync()
    {
        var embed = EmbedFactory.Build(
            "Hallo!",
            $"Hallo {Context.User.Mention}, willkommen auf **PCRP**!");

        await RespondAsync(embed: embed);
    }
}
