namespace PCRP.Bot.Common;

/// <summary>
/// Zentraler Speicherort für alle persistenten Daten des Bots.
/// Auf Railway ist ein Volume unter /app/data gemountet – alles,
/// was Neustarts überleben muss (z.B. "Panel wurde bereits gesendet"),
/// wird hier abgelegt.
/// </summary>
public static class DataStore
{
    /// <summary>Basisverzeichnis für persistente Daten.</summary>
    public static readonly string BasePath =
        Environment.GetEnvironmentVariable("DATA_DIR") ?? "/app/data";

    /// <summary>Liefert einen vollständigen Pfad unterhalb des Datenverzeichnisses und stellt sicher, dass das Verzeichnis existiert.</summary>
    public static string GetPath(string fileName)
    {
        Directory.CreateDirectory(BasePath);
        return Path.Combine(BasePath, fileName);
    }
}
