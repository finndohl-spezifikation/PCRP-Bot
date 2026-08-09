package de.pcrp.bot.common;

import net.dv8tion.jda.api.entities.Message;
import net.dv8tion.jda.api.entities.MessageEmbed;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
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

    /**
     * Einmaliger Zwangs-Neuversand aller Panels (z. B. nach Wechsel auf einen neuen
     * Bot-Account). Pro Panel wird genau EINMAL ein frisches Embed gesendet
     * (unabhängig davon, ob bereits eines im Kanal liegt) — markiert über den
     * DataStore-Key {@code panel-force-<key>}. Danach greift wieder der normale
     * Duplikat-Schutz, damit bei späteren Neustarts nichts doppelt gesendet wird.
     */
    public static volatile boolean FORCE_RESEND = true;

    /** Panel-Referenz für den Embed-Lösch-Schutz (Kanal + Titel + Beschreibung + Sender). */
    private record PanelRef(long channelId, String title, String description, Runnable sender) {}

    /** Registrierte Panels: panelKey → Referenz (wird bei jedem post() aktualisiert). */
    private static final Map<String, PanelRef> PANELS = new ConcurrentHashMap<>();

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
        post(ch, key, embedTitle, null, sender);
    }

    /**
     * Prüft ob das Panel bereits existiert. Sendet nur wenn nicht.
     * Wird {@code embedDescription} angegeben, muss im Kanal ein Embed mit
     * gleichem Titel UND gleicher Beschreibung existieren, damit als
     * "bereits vorhanden" erkannt wird (verhindert, dass ein altes Embed
     * mit gleichem Titel einen inhaltlich neuen Panel blockiert).
     *
     * @param ch                Ziel-Kanal
     * @param key               DataStore-Schlüssel (eindeutig pro Panel + Guild)
     * @param embedTitle        Embed-Titel zur Erkennung im Kanal
     * @param embedDescription  Erwartete Embed-Beschreibung (optional, null = nur Titel vergleichen)
     * @param sender            Runnable der die eigentliche Nachricht sendet;
     *                          MUSS am Ende {@link #onSent} oder {@link #onFailed} aufrufen
     */
    public static void post(TextChannel ch, String key, String embedTitle, String embedDescription, Runnable sender) {
        if (!GUARDS.add(key)) {
            log.debug("[Panel] Guard aktiv für '{}', überspringe Doppel-Send.", key);
            return;
        }

        // Registry immer aktualisieren – der Embed-Lösch-Schutz braucht sie,
        // um gelöschte Panels nach einem Bot-Neustart wiederherzustellen.
        PANELS.put(key, new PanelRef(ch.getIdLong(), embedTitle, embedDescription, sender));

        // Zwangs-Neuversand (einmalig pro Panel): nach einem Bot-Wechsel werden alle
        // Panels frisch gesendet, auch wenn im Kanal bereits eines liegt.
        if (FORCE_RESEND && DataStore.readString("panel-force-" + key) == null) {
            DataStore.writeString("panel-force-" + key, "1");
            log.info("[Panel] Zwangs-Neuversand '{}' (Bot-Wechsel).", key);
            sender.run();
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
                    findAndSend(ch, key, embedTitle, embedDescription, sender);
                }
            );
        } else {
            // DataStore leer → Kanal nach vorhandenem Panel durchsuchen
            findAndSend(ch, key, embedTitle, embedDescription, sender);
        }
    }

    /**
     * Stellt ein Panel wieder her, wenn die zu diesem Panel gespeicherte
     * Nachricht gelöscht wurde (Embed-Schutz). Überlebt Bot-Neustarts, weil
     * die Panel-Registry bei jedem {@link #post} aktualisiert wird und die
     * gespeicherte Nachrichten-ID im DataStore liegt.
     *
     * @return true, wenn die gelöschte Nachricht einem registrierten Panel zugeordnet war
     */
    public static boolean restoreDeleted(TextChannel ch, long deletedMessageId) {
        String deletedId = String.valueOf(deletedMessageId);
        for (Map.Entry<String, PanelRef> e : PANELS.entrySet()) {
            PanelRef ref = e.getValue();
            if (ref.channelId() != ch.getIdLong()) continue;

            String stored = DataStore.readString(e.getKey());
            if (stored == null || stored.isBlank()) continue;
            String storedId = stored.trim();
            if (storedId.contains("|")) storedId = storedId.split("\\|", 2)[0].trim();

            if (storedId.equals(deletedId)) {
                log.info("[Panel] '{}' wurde gelöscht → sende Panel neu.", e.getKey());
                post(ch, e.getKey(), ref.title(), ref.description(), ref.sender());
                return true;
            }
        }
        return false;
    }

    /**
     * Sucht in den letzten 30 Nachrichten des Kanals nach einem Bot-Embed mit
     * passendem Titel (und optional passender Beschreibung). Sendet nur wenn nicht gefunden.
     */
    private static void findAndSend(TextChannel ch, String key, String embedTitle,
                                    String embedDescription, Runnable sender) {
        ch.getHistory().retrievePast(30).queue(
            messages -> {
                for (Message msg : messages) {
                    if (!msg.getAuthor().isBot() || msg.getEmbeds().isEmpty()) continue;
                    MessageEmbed em = msg.getEmbeds().get(0);
                    if (embedTitle != null && !embedTitle.equals(em.getTitle())) continue;
                    if (embedDescription != null && !embedDescription.equals(em.getDescription())) continue;
                    log.info("[Panel] '{}' bereits im Kanal (ID {}), speichere ID und überspringe.", key, msg.getId());
                    DataStore.writeString(key, msg.getId());
                    GUARDS.remove(key);
                    return;
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
