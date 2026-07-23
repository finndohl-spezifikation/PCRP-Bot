using System.Text;

namespace PCRP.Bot.Common;

/// <summary>
/// Wortfilter für vulgäre Kraftausdrücke (Deutsch + Englisch).
/// Nachrichten mit Treffern werden sofort gelöscht.
/// </summary>
public static class WordFilter
{
    private static readonly string[] BannedWords =
    {
        // Deutsch
        "hurensohn", "hurentochter", "hure", "nutte", "fotze", "wichser",
        "wixer", "wixxer", "schlampe", "missgeburt", "bastard", "arschloch",
        "drecksau", "dreckskerl", "spast", "spasti", "mongo", "behindert",
        "fick dich", "fickt euch", "verfickt", "ficker", "kanake", "untermensch",
        // Englisch
        "fuck", "fucking", "fucker", "motherfucker", "bitch", "asshole",
        "cunt", "slut", "whore", "dickhead", "retard", "faggot", "nigger",
        "nigga", "cocksucker", "son of a bitch",
    };

    /// <summary>Prüft, ob der Text einen vulgären Kraftausdruck enthält.</summary>
    public static bool ContainsBannedWord(string content)
        => TryGetBannedWord(content, out _);

    /// <summary>
    /// Prüft, ob der Text einen vulgären Kraftausdruck enthält und gibt ihn zurück.
    /// Wird vom Log-System genutzt, um den gefundenen Begriff zu protokollieren.
    /// </summary>
    public static bool TryGetBannedWord(string content, out string? matchedWord)
    {
        matchedWord = null;
        if (string.IsNullOrWhiteSpace(content))
            return false;

        var normalized = Normalize(content);
        matchedWord = BannedWords.FirstOrDefault(word =>
            normalized.Contains(word, StringComparison.Ordinal));
        return matchedWord is not null;
    }

    /// <summary>Kleinbuchstaben + einfache Leetspeak-Umschreibungen auflösen.</summary>
    private static string Normalize(string input)
    {
        var sb = new StringBuilder(input.Length);
        foreach (var c in input.ToLowerInvariant())
        {
            sb.Append(c switch
            {
                '0' => 'o',
                '1' => 'i',
                '3' => 'e',
                '4' => 'a',
                '5' => 's',
                '7' => 't',
                '@' => 'a',
                '$' => 's',
                _ => c,
            });
        }
        return sb.ToString();
    }
}
