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

    /// <summary>
    /// Erstellt einen EmbedBuilder mit einem winzig-kleinen Icon unten links (Footer-Icon).
    /// Wird ausschließlich für das Bot-Neustart-Embed verwendet – die einzige Ausnahme von
    /// der „kein Footer"-Regel, da der Nutzer dies explizit für Bot-Neustarts gewünscht hat.
    /// Als Footer-Text wird ein unsichtbares Zeichen genutzt, damit das Icon angezeigt wird.
    /// </summary>
    public static EmbedBuilder CreateWithFooterIcon(string iconUrl)
        => Create().WithFooter(new EmbedFooterBuilder()
            .WithIconUrl(iconUrl)
            .WithText("\u200b")); // unsichtbares Zeichen – kein sichtbarer Footer-Text
}
