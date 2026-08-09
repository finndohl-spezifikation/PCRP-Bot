package de.pcrp.bot.common;

import net.dv8tion.jda.api.audio.AudioSendHandler;
import net.dv8tion.jda.api.audio.hooks.ConnectionStatus;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.channel.middleman.AudioChannel;
import net.dv8tion.jda.api.managers.AudioManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Sprach-Unterstützung für den Support-Warteraum.
 *
 *  - Der Bot verbindet sich in den Sprachkanal und spielt eine sanfte, synthetisierte
 *    Wartemusik (Endlos-Loop, wird direkt in Java erzeugt — keine externen Dateien).
 *  - Zusätzlich werden in einer deutschen Stimme (espeak-ng) im Wechsel zwei Ansagen
 *    gesprochen: Willkommenstext → 10 s Pause (nur Musik) → Team-Hinweis → 10 s Pause →
 *    wieder von vorn. Die Musik läuft dabei ununterbrochen weiter.
 */
public final class SupportAudio {

    private static final Logger log = LoggerFactory.getLogger(SupportAudio.class);

    private static final int SAMPLE_RATE = 48_000;

    /** Ansagen (deutsche Stimme). */
    private static final String PHRASE_WELCOME =
        "Willkommen im Sprachsupport von Paradise City Roleplay. Bitte habe noch einen Moment Geduld, " +
        "während ich ein Teammitglied benachrichtige, das deinen Fall übernimmt.";
    private static final String PHRASE_TEAM =
        "Du hast Interesse, ein Teil des Teams zu werden? Dann öffne gerne ein Bewerbungsticket " +
        "und bewirb dich für unser Team.";

    /** Pause zwischen den Ansagen (nur Musik). */
    private static final long SPEECH_GAP_MS = 10_000;

    private static final ScheduledExecutorService EXECUTOR = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "support-audio");
        t.setDaemon(true);
        return t;
    });

    private static volatile SupportAudioHandler handler;
    private static volatile byte[] musicLoop;
    private static volatile boolean active = false;
    private static volatile Guild activeGuild;

    /** Wird aufgerufen, wenn eine Verbindung gescheitert ist (z. B. für einen späteren Retry). */
    private static volatile Runnable failureHandler;

    private SupportAudio() {}

    /** Setzt den Callback, der bei einem Verbindungsfehler aufgerufen wird. */
    public static void setFailureHandler(Runnable handler) {
        failureHandler = handler;
    }

    /** Startet Musik + Ansagen im Warteraum (falls nicht bereits aktiv). */
    public static synchronized void start(Guild guild, AudioChannel channel) {
        if (active && activeGuild != null && activeGuild.getIdLong() == guild.getIdLong()) return;
        stop();
        try {
            if (musicLoop == null) musicLoop = synthesizeMusic();
            handler = new SupportAudioHandler(musicLoop);
            AudioManager am = guild.getAudioManager();
            // KEIN Auto-Reconnect: Wenn die Verbindung scheitert (z. B. UDP zu Discords
            // Voice-Servern von der Hosting-Umgebung aus blockiert), würde JDA sonst endlos
            // beitreten/verlassen wiederholen. Stattdessen einmal versuchen und sauber aufhören.
            am.setAutoReconnect(false);
            am.setConnectionListener(new net.dv8tion.jda.api.audio.hooks.ConnectionListener() {
                @Override
                public void onStatusChange(ConnectionStatus status) {
                    onConnectionStatus(status);
                }
            });
            am.setSendingHandler(handler);
            am.openAudioConnection(channel);
            active = true;
            activeGuild = guild;
            startSpeechLoop();
            log.info("[SupportAudio] Wartemusik + Ansagen in '{}' gestartet.", channel.getName());
        } catch (Exception e) {
            log.error("[SupportAudio] Start fehlgeschlagen.", e);
        }
    }

    /** Stoppt Musik + Ansagen und trennt die Verbindung. */
    public static synchronized void stop() {
        active = false;
        if (activeGuild != null) {
            try {
                AudioManager am = activeGuild.getAudioManager();
                am.setSendingHandler(null);
                am.closeAudioConnection();
            } catch (Exception ignored) {
                // Verbindung war evtl. schon zu — ignorieren
            }
            activeGuild = null;
        }
        handler = null;
    }

    /**
     * Verbindungs-Status-Callback von JDA. Loggt den Status und setzt bei einem
     * Verbindungsende/-fehler den Zustand zurück, damit kein Reconnect-Loop entsteht
     * und der nächste Beitritt einen frischen Versuch starten kann.
     */
    private static void onConnectionStatus(ConnectionStatus status) {
        log.info("[SupportAudio] Verbindungsstatus: {}", status);
        if (status == ConnectionStatus.CONNECTED
            || status.name().startsWith("CONNECTING_")
            || status == ConnectionStatus.SHUTTING_DOWN
            || status == ConnectionStatus.AUDIO_REGION_CHANGE) {
            return; // transient oder ok
        }
        // Verbindung beendet oder gescheitert → Zustand zurücksetzen
        active = false;
        activeGuild = null;
        handler = null;
        Runnable onFail = failureHandler;
        if (onFail != null) {
            try {
                onFail.run();
            } catch (Exception e) {
                log.warn("[SupportAudio] Fehler im Failure-Handler: {}", e.getMessage());
            }
        }
    }

    // ── Ansage-Loop ───────────────────────────────────────────────────────────

    private static void startSpeechLoop() {
        EXECUTOR.execute(() -> speechCycle(true));
    }

    private static void speechCycle(boolean welcome) {
        if (!active) return;
        speak(welcome ? PHRASE_WELCOME : PHRASE_TEAM);
        if (!active) return;
        try {
            Thread.sleep(SPEECH_GAP_MS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return;
        }
        if (!active) return;
        speechCycle(!welcome);
    }

    /** Erzeugt die Ansage per espeak-ng und spielt sie über der Musik ab. */
    private static void speak(String text) {
        if (handler == null || !active) return;
        File wav = null;
        try {
            wav = File.createTempFile("pcrp_tts_", ".wav");
            Process p = new ProcessBuilder("espeak-ng", "-v", "de", "-s", "150", "-w", wav.getAbsolutePath(), text)
                .redirectErrorStream(true)
                .start();
            if (!p.waitFor(10, TimeUnit.SECONDS)) p.destroyForcibly();
            byte[] mono = parseWavData(Files.readAllBytes(wav.toPath()));
            byte[] pcm = toPcmStereo48k(mono);
            if (!active) return;
            handler.queueSpeech(pcm);
            // Warten bis die Ansage fertig abgespielt ist, damit die 10s-Pause danach startet
            long durationMs = pcm.length / (SAMPLE_RATE * 4L) * 1000L;
            Thread.sleep(durationMs + 200);
        } catch (Exception e) {
            log.warn("[SupportAudio] TTS fehlgeschlagen: {}", e.getMessage());
            try {
                Thread.sleep(500);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
            }
        } finally {
            if (wav != null && wav.exists()) {
                //noinspection ResultOfMethodCallIgnored
                wav.delete();
            }
        }
    }

    // ── WAV/PCM-Verarbeitung ──────────────────────────────────────────────────

    /** Liest die reinen PCM-Daten (16-bit, mono) aus einer WAV-Datei. */
    private static byte[] parseWavData(byte[] wav) throws IOException {
        if (wav.length < 12 || wav[0] != 'R' || wav[1] != 'I' || wav[2] != 'F' || wav[3] != 'F') {
            throw new IOException("Keine gültige WAV-Datei");
        }
        int pos = 12;
        while (pos + 8 <= wav.length) {
            int len = ByteBuffer.wrap(wav, pos + 4, 4).order(ByteOrder.LITTLE_ENDIAN).getInt();
            if (wav[pos] == 'd' && wav[pos + 1] == 'a' && wav[pos + 2] == 't' && wav[pos + 3] == 'a') {
                int start = pos + 8;
                int end   = Math.min(start + len, wav.length);
                byte[] data = new byte[end - start];
                System.arraycopy(wav, start, data, 0, data.length);
                return data;
            }
            pos += 8 + len + (len % 2);
        }
        throw new IOException("Kein data-Chunk in WAV gefunden");
    }

    /** Wandelt 16-bit-mono-PCM (22.05 kHz, espeak-ng) in 16-bit-stereo-PCM (48 kHz) um. */
    private static byte[] toPcmStereo48k(byte[] mono) {
        int inSamples = mono.length / 2;
        double ratio  = (double) SAMPLE_RATE / 22_050.0;
        int outSamples = (int) Math.ceil(inSamples * ratio);
        byte[] out = new byte[outSamples * 4];
        for (int i = 0; i < outSamples; i++) {
            int srcIdx = (int) (i / ratio);
            if (srcIdx >= inSamples - 1) srcIdx = inSamples - 1;
            int v = read16(mono, srcIdx * 2);
            write16(out, i * 4, v);
            write16(out, i * 4 + 2, v);
        }
        return out;
    }

    /**
     * Synthetisiert eine sanfte Wartemusik (Akkord-Fläche Am–F–C–G, ~24 s Loop)
     * direkt als 16-bit-stereo-PCM (48 kHz) — komplett ohne externe Dateien.
     */
    private static byte[] synthesizeMusic() {
        double[][] chords = {
            {110.00, 164.81, 220.00, 261.63},   // Am
            { 87.31, 130.81, 174.61, 220.00},   // F
            {130.81, 196.00, 261.63, 329.63},   // C
            { 98.00, 146.83, 196.00, 246.94}    // G
        };
        int chordSamples = SAMPLE_RATE * 6;
        int total = chords.length * chordSamples;
        byte[] out = new byte[total * 4];

        for (int c = 0; c < chords.length; c++) {
            int base = c * chordSamples;
            for (int i = 0; i < chordSamples; i++) {
                double t   = (double) i / SAMPLE_RATE;
                double env = Math.min(1.0, i / (SAMPLE_RATE * 0.9));
                env = Math.min(env, (double) (chordSamples - i) / (SAMPLE_RATE * 1.2));
                double sum = 0;
                for (double f : chords[c]) {
                    sum += Math.sin(2 * Math.PI * f * t)
                         + 0.35 * Math.sin(2 * Math.PI * f * 1.004 * t + 0.5);
                }
                double trem = 1.0 + 0.06 * Math.sin(2 * Math.PI * 0.4 * t);
                int v = (int) Math.round(sum * 0.10 * env * trem * 32767);
                if (v > 32767) v = 32767;
                else if (v < -32768) v = -32768;
                int idx = (base + i) * 4;
                out[idx]     = (byte) (v & 0xFF);
                out[idx + 1] = (byte) ((v >> 8) & 0xFF);
                out[idx + 2] = out[idx];
                out[idx + 3] = out[idx + 1];
            }
        }
        return out;
    }

    // ── Little-Endian-Helfer ──────────────────────────────────────────────────

    private static int read16(byte[] b, int off) {
        return (short) ((b[off] & 0xFF) | ((b[off + 1] & 0xFF) << 8));
    }

    private static void write16(byte[] b, int off, int v) {
        b[off]     = (byte) (v & 0xFF);
        b[off + 1] = (byte) ((v >> 8) & 0xFF);
    }

    // ── Audio-Send-Handler (mischt Musik + Ansage) ────────────────────────────

    private static final class SupportAudioHandler implements AudioSendHandler {

        private final byte[] music;
        private int musicPos = 0;

        private volatile byte[] speech;
        private int speechPos = 0;

        private SupportAudioHandler(byte[] music) { this.music = music; }

        synchronized void queueSpeech(byte[] pcm) {
            this.speech = pcm;
            this.speechPos = 0;
        }

        @Override
        public boolean canProvide() {
            return true; // Musik läuft als Endlos-Loop
        }

        @Override
        public java.nio.ByteBuffer provide20MsAudio() {
            byte[] frame = new byte[3840]; // 20 ms @ 48 kHz, Stereo, 16-bit
            byte[] sp = speech;
            for (int i = 0; i < 3840; i += 2) {
                int m = read16(music, musicPos + i);
                int s = (sp != null && speechPos + i + 1 < sp.length) ? read16(sp, speechPos + i) : 0;
                int v = (int) (m * 0.32) + (int) (s * 0.9);
                if (v > 32767) v = 32767;
                else if (v < -32768) v = -32768;
                write16(frame, i, v);
            }
            musicPos += 3840;
            if (musicPos >= music.length) musicPos = 0;
            if (sp != null) {
                speechPos += 3840;
                if (speechPos >= sp.length) {
                    speech = null;
                    speechPos = 0;
                }
            }
            return java.nio.ByteBuffer.wrap(frame);
        }
    }
}
