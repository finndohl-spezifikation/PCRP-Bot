package de.pcrp.bot.listeners;

import club.minnced.discord.webhook.WebhookClient;
import club.minnced.discord.webhook.WebhookClientBuilder;
import club.minnced.discord.webhook.send.WebhookMessageBuilder;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.*;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.message.MessageReceivedEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Type;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Nachrichten-Moderation:
 *  1. Wortfilter       – vulgäre Kraftausdrücke → sofort löschen + Log
 *  2. Eigenwerbung     – fremde Discord-Links → löschen, 14d Timeout, DM, Alert + Log
 *  3. 67-Filter        – „67"/„sixseven" → korrigiert neu posten + Log
 *  4. Spamschutz       – zu viele Nachrichten → DM-Verwarnung, beim 2. Mal 10 Min. Timeout + Log
 * Der Inhaber (OwnerId) ist von allem ausgenommen.
 */
public class ModerationListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(ModerationListener.class);

    private static final Pattern INVITE_REGEX = Pattern.compile(
        "(?:discord(?:app)?\\.com/invite|discord\\.gg)/([A-Za-z0-9-]+)",
        Pattern.CASE_INSENSITIVE);

    private static final Pattern SIX_SEVEN_REGEX = Pattern.compile(
        "\\b67\\b|sixseven",
        Pattern.CASE_INSENSITIVE);

    // Spam-Tracking
    private final ConcurrentHashMap<Long, ArrayDeque<Long>> messageTimes = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<Long, Long>             lastSpamAction = new ConcurrentHashMap<>();
    private ConcurrentHashMap<Long, Integer>                spamOffenses   = new ConcurrentHashMap<>();
    private static final String OFFENSES_FILE = "spam_offenses.json";
    private static final Gson   GSON          = new Gson();

    public ModerationListener() {
        loadOffenses();
    }

    @Override
    public void onMessageReceived(MessageReceivedEvent event) {
        if (!event.isFromGuild()) return;
        if (!(event.getChannel() instanceof TextChannel)) return; // Threads / andere Kanaltypen überspringen

        Message  message = event.getMessage();
        User     author  = event.getAuthor();
        if (author.isBot() || author.isSystem()) return;

        Member member = event.getMember();
        if (member == null) return;

        // Nachricht in den Cache stellen (für MessageDeleteEvent im LoggingListener)
        cacheMessage(message);

        // Inhaber ist von allem ausgenommen
        if (author.getIdLong() == ModerationConfig.OWNER_ID) return;

        Guild       guild   = event.getGuild();
        TextChannel channel = event.getChannel().asTextChannel();

        try {
            // 1. Wortfilter
            String matched = WordFilter.getMatchedWord(message.getContentRaw());
            if (matched != null) {
                message.delete().queue();

                guild.timeoutFor(member, Duration.ofMinutes(ModerationConfig.SPAM_TIMEOUT_MINUTES)).queue();

                BotLogger.tryDm(author, EmbedFactory.build(
                    "⚠️ Verwarnung – Verbotenes Wort",
                    "Deine Nachricht auf **" + guild.getName() + "** wurde gelöscht, weil sie " +
                    "einen verbotenen Ausdruck enthielt.\n\n" +
                    "Du hast daher automatisch einen **10-minütigen Timeout** erhalten.\n\n" +
                    "Bitte halte dich an die Serverregeln."));

                BotLogger.logModeration(guild,
                    "🔤 Wortfilter ausgelöst",
                    "**Nutzer:** " + member.getAsMention() + " | " + author.getName() + " (`" + author.getId() + "`)\n" +
                    "**Kanal:** " + channel.getAsMention() + "\n" +
                    "**Erkanntes Wort:** `" + matched + "`\n" +
                    "**Aktion:** Nachricht gelöscht · 10 Min. Timeout · DM gesendet\n" +
                    "**Nachrichteninhalt:**\n```\n" + truncate(message.getContentRaw(), 900) + "\n```");
                return;
            }

            // 2. Fremde Discord-Server-Links
            if (handleForeignInvite(event, message, channel, member, guild)) return;

            // 3. 67 / sixseven → 69 / sixnine
            if (SIX_SEVEN_REGEX.matcher(message.getContentRaw()).find()) {
                handleSixSeven(event, message, channel, member, guild);
                return;
            }

            // 4. Spamschutz
            handleSpam(message, member, channel, guild);

        } catch (Exception ex) {
            log.error("Fehler in der Nachrichten-Moderation.", ex);
        }
    }

    // ── Fremde Server-Links ───────────────────────────────────────────────────

    private boolean handleForeignInvite(MessageReceivedEvent event,
                                        Message message, TextChannel channel,
                                        Member member, Guild guild) {
        Matcher m = INVITE_REGEX.matcher(message.getContentRaw());
        if (!m.find()) return false;
        String code = m.group(1);

        // Prüfen ob der Invite zum eigenen Server gehört
        guild.retrieveInvites().queue(invites -> {
            boolean ownServer = invites.stream().anyMatch(inv -> inv.getCode().equals(code));
            if (ownServer) return;

            message.delete().queue();
            guild.timeoutFor(member, Duration.ofDays(ModerationConfig.PROTECTION_TIMEOUT_DAYS)).queue();

            BotLogger.tryDm(member.getUser(), EmbedFactory.build(
                "Schutz für Eigenwerbung aktiv",
                "Auf **PCRP** sind fremde Discord-Server-Links nicht erlaubt.\n\n" +
                "Deine Nachricht wurde gelöscht und du hast einen **14-tägigen Timeout** erhalten. " +
                "Dieser Fall wird nun geprüft."));

            BotLogger.sendAlert(guild,
                "Aktivitätswarnung – Eigenwerbung",
                "**Nutzer:** " + member.getAsMention() + " (`" + member.getId() + "`)\n" +
                "**Kanal:** " + channel.getAsMention() + "\n" +
                "**Aktion:** Fremder Discord-Link gelöscht, 14 Tage Timeout vergeben.\n" +
                "**Link:** `" + m.group() + "`");

            BotLogger.logModeration(guild,
                "🔗 Eigenwerbung – Link entfernt",
                "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                "**Kanal:** " + channel.getAsMention() + "\n" +
                "**Erkannter Link:** `" + m.group() + "`\n" +
                "**Aktionen:** Nachricht gelöscht · 14 Tage Timeout · DM gesendet\n" +
                "**Nachrichteninhalt:**\n```\n" + truncate(message.getContentRaw(), 700) + "\n```");
        });

        return true; // als fremd behandeln bis der Callback das klärt
    }

    // ── 67 → 69 ──────────────────────────────────────────────────────────────

    private void handleSixSeven(MessageReceivedEvent event, Message message,
                                TextChannel channel, Member member, Guild guild) {
        String fixed = SIX_SEVEN_REGEX.matcher(message.getContentRaw()).replaceAll(found ->
            found.group().equalsIgnoreCase("sixseven") ? "sixnine" : "69");

        BotLogger.logModeration(guild,
            "🔢 67-Filter ausgelöst",
            "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
            "**Kanal:** " + channel.getAsMention() + "\n" +
            "**Aktion:** Nachricht gelöscht · korrigierte Version gepostet\n" +
            "**Original:**\n```\n" + truncate(message.getContentRaw(), 400) + "\n```\n" +
            "**Korrigiert:**\n```\n" + truncate(fixed, 400) + "\n```");

        message.delete().queue();

        // Über Webhook im Namen des Nutzers neu posten
        channel.retrieveWebhooks().queue(webhooks -> {
            Webhook webhook = webhooks.stream()
                .filter(w -> "PCRP Moderation".equals(w.getName()))
                .findFirst()
                .orElse(null);

            if (webhook == null) {
                channel.createWebhook("PCRP Moderation").queue(
                    created -> sendViaWebhook(created, fixed, member),
                    err -> log.warn("Webhook konnte nicht erstellt werden.", err));
            } else {
                sendViaWebhook(webhook, fixed, member);
            }
        });
    }

    private void sendViaWebhook(Webhook webhook, String content, Member member) {
        try (WebhookClient client = new WebhookClientBuilder(webhook.getUrl())
                .setWait(false).build()) {
            client.send(new WebhookMessageBuilder()
                .setContent(content)
                .setUsername(member.getEffectiveName())
                .setAvatarUrl(member.getEffectiveAvatarUrl())
                .build());
        } catch (Exception ex) {
            log.warn("Webhook-Nachricht konnte nicht gesendet werden.", ex);
        }
    }

    // ── Spamschutz ────────────────────────────────────────────────────────────

    private void handleSpam(Message message, Member member, TextChannel channel, Guild guild) {
        long now    = Instant.now().toEpochMilli();
        long userId = member.getIdLong();

        ArrayDeque<Long> times = messageTimes.computeIfAbsent(userId, k -> new ArrayDeque<>());
        int count;
        synchronized (times) {
            times.addLast(now);
            while (!times.isEmpty() && now - times.peekFirst() > ModerationConfig.SPAM_WINDOW_MS)
                times.pollFirst();
            count = times.size();
        }

        if (count <= ModerationConfig.SPAM_MESSAGE_LIMIT) return;

        // Nicht mehrfach innerhalb derselben Spamwelle bestrafen
        Long last = lastSpamAction.get(userId);
        if (last != null && now - last < 30_000L) return;
        lastSpamAction.put(userId, now);

        int offenses = spamOffenses.merge(userId, 1, Integer::sum);
        saveOffenses();

        if (offenses == 1) {
            BotLogger.tryDm(member.getUser(), EmbedFactory.build(
                "Verwarnung – Spamschutz",
                "Du hast in kürzester Zeit zu viele Nachrichten auf **PCRP** gesendet.\n\n" +
                "Dies ist deine **Verwarnung**. Beim nächsten Verstoß erhältst du automatisch einen **10-minütigen Timeout**."));

            BotLogger.logModeration(guild,
                "⚠️ Spam – Verwarnung ausgesprochen",
                "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                "**Kanal:** " + channel.getAsMention() + "\n" +
                "**Verstoß Nr.:** " + offenses + "\n" +
                "**Aktion:** DM-Verwarnung gesendet (nächster Verstoß = 10 Min. Timeout)");
        } else {
            guild.timeoutFor(member, Duration.ofMinutes(ModerationConfig.SPAM_TIMEOUT_MINUTES)).queue();

            BotLogger.tryDm(member.getUser(), EmbedFactory.build(
                "Timeout – Spamschutz",
                "Du wurdest trotz Verwarnung erneut wegen Spam auffällig.\n\n" +
                "Du hast automatisch einen **10-minütigen Timeout** erhalten."));

            BotLogger.logModeration(guild,
                "🔇 Spam – 10 Min. Timeout vergeben",
                "**Nutzer:** " + member.getAsMention() + " | " + member.getUser().getName() + " (`" + member.getId() + "`)\n" +
                "**Kanal:** " + channel.getAsMention() + "\n" +
                "**Verstoß Nr.:** " + offenses + "\n" +
                "**Aktion:** 10 Minuten Timeout · DM gesendet");
        }
    }

    // ── Hilfs-Methoden ────────────────────────────────────────────────────────

    private static void cacheMessage(Message message) {
        List<String> attachments = message.getAttachments().stream()
            .map(Message.Attachment::getFileName)
            .toList();
        MessageCache.put(message.getIdLong(), new MessageCache.CachedMessage(
            message.getAuthor().getId(),
            message.getAuthor().getName(),
            message.getAuthor().getEffectiveAvatarUrl(),
            message.getContentRaw(),
            message.getChannel().getAsMention(),
            attachments,
            message.getTimeCreated().toEpochSecond()
        ));
    }

    @SuppressWarnings("unchecked")
    private void loadOffenses() {
        String json = DataStore.readString(OFFENSES_FILE);
        if (json == null) return;
        try {
            Type type = new TypeToken<Map<String, Integer>>() {}.getType();
            Map<String, Integer> loaded = GSON.fromJson(json, type);
            if (loaded != null)
                loaded.forEach((k, v) -> spamOffenses.put(Long.parseLong(k), v));
        } catch (Exception ex) {
            log.warn("Spam-Verstöße konnten nicht geladen werden.", ex);
        }
    }

    private void saveOffenses() {
        try {
            Map<String, Integer> out = new LinkedHashMap<>();
            spamOffenses.forEach((k, v) -> out.put(k.toString(), v));
            DataStore.writeString(OFFENSES_FILE, GSON.toJson(out));
        } catch (Exception ex) {
            log.warn("Spam-Verstöße konnten nicht gespeichert werden.", ex);
        }
    }

    private static String truncate(String s, int max) {
        return s != null && s.length() > max ? s.substring(0, max - 1) + "…" : (s != null ? s : "");
    }
}
