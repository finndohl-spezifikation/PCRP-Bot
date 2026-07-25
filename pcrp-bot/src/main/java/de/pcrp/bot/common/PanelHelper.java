package de.pcrp.bot.common;

import net.dv8tion.jda.api.entities.Message;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Zentrales Panel-Posting-Utility.
 *
 * Verhindert Doppel-Sends durch drei Schutzebenen:
 * 1. In-Memory-Guard — verhindert parallele Sends innerhalb desselben Prozesses
 * 2. DataStore-Check — gespeicherte Nachrichten-ID wird per Discord-API geprüft
 * 3. Kanal-History-Fallback — sucht die letzten 30 Nachrichten nach Embed-Titel,
 *    falls DataStore leer ist (z. B. nach Railway-Reset)
 */
public final class PanelHelper {

    private static final Logger log = LoggerFactory.getLogger(PanelHelper.class);

    /** In-Memory-Guard: verhindert gleichzeitige Posts desselben Panels. */
    private static final Set<String> GUARDS = ConcurrentHashMap.newKeySet();

    private PanelHelper() {}

    /**
     * Prüft ob das Panel bereits existiert. Sendet nur wenn nicht.
     *
     * @param ch         Ziel-Kanal
     * @param key        DataStore-Schlüssel (eindeutig pro Panel + Guild)
     * @param embedTitle Embed-Titel zur Erkennung im Kanal
     * @param sender     Runnable der die eigentliche Nachricht sendet;
     *                   MUSS am Ende {@link #onSent} oder {@link #onFailed} aufrufen
     */
    public static void post(TextChannel ch, String key, String embedTitle, Runnable sender) {
        if (!GUARDS.add(key)) {
            log.debug("[Panel] Guard aktiv für '{}', überspringe Doppel-Send.", key);
            return;
        }

        String stored = DataStore.readString(key);
        if (stored != null && !stored.isBlank()) {
            // Altes Format "msgId|extra" bereinigen (z. B. Meldeamt speicherte "id|url")
            String storedId = stored.trim();
            if (storedId.contains("|")) storedId = storedId.split("\\|", 2)[0].trim();
            final String resolvedId = storedId;
            // Gespeicherte ID per Discord-API prüfen
            ch.retrieveMessageById(resolvedId).queue(
                msg -> {
                    log.debug("[Panel] '{}' aktiv (ID {}), kein Neuversand.", key, stored.trim());
                    GUARDS.remove(key);
                },
                err -> {
                    // Nachricht gelöscht → DataStore bereinigen und Kanal-Suche
                    DataStore.deleteKey(key);
                    findAndSend(ch, key, embedTitle, sender);
                }
            );
        } else {
            // DataStore leer → Kanal nach vorhandenem Panel durchsuchen
            findAndSend(ch, key, embedTitle, sender);
        }
    }

    /**
     * Sucht in den letzten 30 Nachrichten des Kanals nach einem Bot-Embed mit
     * passendem Titel. Sendet nur wenn nicht gefunden.
     */
    private static void findAndSend(TextChannel ch, String key, String embedTitle, Runnable sender) {
        ch.getHistory().retrievePast(30).queue(
            messages -> {
                for (Message msg : messages) {
                    if (!msg.getAuthor().isBot() || msg.getEmbeds().isEmpty()) continue;
                    String title = msg.getEmbeds().get(0).getTitle();
                    if (embedTitle != null && embedTitle.equals(title)) {
                        log.info("[Panel] '{}' bereits im Kanal (ID {}), speichere ID und überspringe.", key, msg.getId());
                        DataStore.writeString(key, msg.getId());
                        GUARDS.remove(key);
                        return;
                    }
                }
                // Nicht im Kanal → jetzt wirklich senden
                sender.run();
            },
            err -> {
                log.warn("[Panel] Kanal-History für '{}' nicht abrufbar, sende trotzdem.", key);
                sender.run();
            }
        );
    }

    /**
     * Nach erfolgreichem Senden aufrufen — speichert Nachrichten-ID, gibt Guard frei.
     */
    public static void onSent(String key, String messageId) {
        DataStore.writeString(key, messageId);
        GUARDS.remove(key);
    }

    /**
     * Bei Sende-Fehler aufrufen — gibt Guard frei.
     */
    public static void onFailed(String key) {
        GUARDS.remove(key);
    }
}
