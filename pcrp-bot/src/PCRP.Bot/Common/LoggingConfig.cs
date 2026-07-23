namespace PCRP.Bot.Common;

/// <summary>
/// Kanal-IDs für das Log-System.
/// </summary>
public static class LoggingConfig
{
    /// <summary>Alles rund um den Server (Guild, Kanäle, Einladungen, Voice).</summary>
    public const ulong ServerLogChannelId = 1529636412628930723;

    /// <summary>Alles rund um Moderation (Bans, Timeouts, Wortfilter, Spam, Eigenwerbung…).</summary>
    public const ulong ModerationLogChannelId = 1529636417636929707;

    /// <summary>Bot-Neustarts und alles rund um Spieler (Beitritt, Verlassen, Nickname).</summary>
    public const ulong PlayerLogChannelId = 1529636419071639735;

    /// <summary>Alles rund um Nachrichten (gelöscht, bearbeitet, Massenlöschung).</summary>
    public const ulong MessageLogChannelId = 1529636425337667714;

    /// <summary>Alles rund um Rollen (erstellt, gelöscht, geändert, vergeben/entzogen).</summary>
    public const ulong RoleLogChannelId = 1529636428370280509;

    /// <summary>Alles rund um Gelder/Wirtschaft (für spätere Implementierung).</summary>
    public const ulong MoneyLogChannelId = 1529636430362574968;

    /// <summary>Alles rund um Tickets und Transkripte (für spätere Implementierung).</summary>
    public const ulong TicketLogChannelId = 1529636431784317019;

    /// <summary>
    /// C#-Logo URL – wird als winzig-kleines Icon unten links im Bot-Neustart-Embed eingebettet.
    /// (Technisch: Footer-Icon mit unsichtbarem Leerzeichen als Text – die einzige Ausnahme
    /// von der „kein Footer"-Regel, explizit für Bot-Neustart-Embeds.)
    /// </summary>
    public const string CSharpLogoUrl =
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Logo_C_sharp.svg/120px-Logo_C_sharp.svg.png";
}
