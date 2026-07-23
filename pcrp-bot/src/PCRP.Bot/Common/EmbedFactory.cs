using Discord;

namespace PCRP.Bot.Common;

/// <summary>
/// Zentrale Stelle für alle Embeds des Bots.
/// Regeln:
///  - Jedes Embed ist IMMER dunkelorange.
///  - Niemals Footer-Texte. Embeds bleiben clean.
/// Alle Embeds müssen über diese Factory erstellt werden.
/// </summary>
public static class EmbedFactory
{
    /// <summary>Dunkelorange – die einzige erlaubte Embed-Farbe.</summary>
    public static readonly Color DarkOrange = new(0xCC, 0x55, 0x00);

    public static EmbedBuilder Create()
        => new EmbedBuilder().WithColor(DarkOrange);

    public static Embed Build(string title, string description)
        => Create()
            .WithTitle(title)
            .WithDescription(description)
            .Build();
}
