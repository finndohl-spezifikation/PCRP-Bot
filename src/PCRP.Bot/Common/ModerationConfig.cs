namespace PCRP.Bot.Common;

/// <summary>
/// Zentrale Konfiguration für das Moderationssystem.
/// </summary>
public static class ModerationConfig
{
    /// <summary>Inhaber – hat keinerlei Einschränkungen und wird bei Aktivitätswarnungen gepingt.</summary>
    public const ulong OwnerId = 1259265007791636540;

    /// <summary>Kanal für Aktivitätswarnungen (Anti-Nuke, Eigenwerbung usw.).</summary>
    public const ulong AlertChannelId = 1529636455079608431;

    // Spamschutz
    public const int SpamMessageLimit = 7;                                        // mehr als 7 Nachrichten ...
    public static readonly TimeSpan SpamWindow = TimeSpan.FromSeconds(10);        // ... in kürzester Zeit
    public static readonly TimeSpan SpamTimeout = TimeSpan.FromMinutes(10);       // Timeout beim 2. Verstoß

    // Nuke-Schutz (Kanäle/Rollen löschen)
    public const int MassDeleteLimit = 3;                                         // ab so vielen Löschungen ...
    public static readonly TimeSpan MassDeleteWindow = TimeSpan.FromSeconds(60);  // ... innerhalb dieser Zeit

    /// <summary>14 Tage Timeout bei Nuke-Verdacht und Eigenwerbung.</summary>
    public static readonly TimeSpan ProtectionTimeout = TimeSpan.FromDays(14);

    /// <summary>Ping des Inhabers für Aktivitätswarnungen.</summary>
    public static string OwnerMention => $"<@{OwnerId}>";
}
