package de.pcrp.bot.common;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.file.*;

/**
 * Zugriff auf das persistente Datenverzeichnis.
 * Railway mountet ein Volume unter /app/data – alle dauerhaften Daten kommen hierhin.
 * Der Pfad kann über die Umgebungsvariable DATA_DIR überschrieben werden.
 */
public final class DataStore {

    private static final Logger log = LoggerFactory.getLogger(DataStore.class);
    private static final Path DATA_DIR;

    static {
        String env = System.getenv("DATA_DIR");
        DATA_DIR = Paths.get(env != null && !env.isBlank() ? env : "/app/data");
        try {
            Files.createDirectories(DATA_DIR);
        } catch (IOException e) {
            log.warn("Datenverzeichnis konnte nicht angelegt werden: {}", DATA_DIR, e);
        }
    }

    private DataStore() {}

    /** Gibt den vollständigen Pfad zu einer Datei im Datenverzeichnis zurück. */
    public static Path getPath(String filename) {
        return DATA_DIR.resolve(filename);
    }

    /** Liest den Inhalt einer Datei als String, oder null wenn die Datei nicht existiert. */
    public static String readString(String filename) {
        Path path = getPath(filename);
        if (!Files.exists(path)) return null;
        try {
            return Files.readString(path);
        } catch (IOException e) {
            log.warn("Datei konnte nicht gelesen werden: {}", filename, e);
            return null;
        }
    }

    /** Schreibt einen String in eine Datei im Datenverzeichnis. */
    public static void writeString(String filename, String content) {
        try {
            Files.writeString(getPath(filename), content,
                StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
        } catch (IOException e) {
            log.warn("Datei konnte nicht geschrieben werden: {}", filename, e);
        }
    }

    /** Löscht eine Datei aus dem Datenverzeichnis (ignoriert falls nicht vorhanden). */
    public static void deleteKey(String filename) {
        try {
            Files.deleteIfExists(getPath(filename));
        } catch (IOException e) {
            log.warn("Datei konnte nicht gelöscht werden: {}", filename, e);
        }
    }
}
