package de.pcrp.bot.listeners;

import com.google.gson.JsonObject;
import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.Permission;
import net.dv8tion.jda.api.entities.*;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.entities.emoji.Emoji;
import net.dv8tion.jda.api.events.interaction.command.*;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.commands.Command;
import net.dv8tion.jda.api.interactions.commands.OptionMapping;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.awt.Color;
import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/**
 * Slash-Command-Handler: /löschen, /bannen, /entbannen, /timeout
 * Autocomplete für /entbannen (Bannliste des Servers).
 */
public class CommandListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(CommandListener.class);

    // ════════════════════════════════════════════════════════════
    //  COMMAND-DISPATCH
    // ════════════════════════════════════════════════════════════

    @Override
    public void onSlashCommandInteraction(SlashCommandInteractionEvent event) {
        switch (event.getName()) {
            case "löschen"          -> handleLoeschen(event);
            case "bannen"           -> handleBannen(event);
            case "entbannen"        -> handleEntbannen(event);
            case "timeout"          -> handleTimeout(event);
            case "ausweis"          -> handleAusweis(event);
            case "abstimmung"       -> handleAbstimmung(event);
            case "aktivitätscheck"  -> handleAktivitaetscheck(event);
            case "event"               -> handleEvent(event);
            case "gewinnspiel"         -> handleGewinnspiel(event);
            case "verwarnung"          -> handleVerwarnung(event);
            case "verwarn-liste"       -> handleVerwarnListe(event);
            case "verwarnung-löschen"  -> handleVerwarnungLoeschen(event);
            case "einreise-sperre"     -> handleEinreiseSperre(event);
            case "einreise-entsperren" -> handleEinreiseEntsperre(event);
        }
    }

    // ════════════════════════════════════════════════════════════
    //  BUTTON
    // ════════════════════════════════════════════════════════════

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if ("status-aktive-systeme".equals(event.getComponentId()))
            event.replyEmbeds(buildActiveSystemsEmbed()).setEphemeral(true).queue();
    }

    private static net.dv8tion.jda.api.entities.MessageEmbed buildActiveSystemsEmbed() {
        String owner = "<@" + ModerationConfig.OWNER_ID + "> · <@" + ModerationConfig.CO_OWNER_ID + ">";
        String bot   = "Bot selbst";

        return EmbedFactory.create()
            .setTitle("🛡️ Aktive Moderationssysteme — Paradise City Roleplay")
            .setDescription(
                "**🔤 Wortfilter**\n" +
                "Verbotener Ausdruck → Nachricht löschen · 10 Min. Timeout · DM\n" +
                "✅ Ausgenommen: " + owner + "\n\n" +

                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +

                "**🔗 Eigenwerbungs-Filter**\n" +
                "Fremder Discord-Link → Nachricht löschen · 14 Tage Timeout · DM · Alert\n" +
                "✅ Ausgenommen: " + owner + "\n\n" +

                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +

                "**🔢 67-Filter**\n" +
                "\"67\" / \"sixseven\" → Nachricht löschen · korrigiert als \"69\" via Webhook neu gepostet\n" +
                "✅ Ausgenommen: " + owner + "\n\n" +

                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +

                "**📨 Spamschutz** (>" + ModerationConfig.SPAM_MESSAGE_LIMIT +
                    " Nachrichten / " + (ModerationConfig.SPAM_WINDOW_MS / 1000) + "s)\n" +
                "1. Verstoß → Nachrichten löschen · DM-Verwarnung\n" +
                "2. Verstoß → Nachrichten löschen · " + ModerationConfig.SPAM_TIMEOUT_MINUTES + " Min. Timeout · DM\n" +
                "✅ Ausgenommen: " + owner + "\n\n" +

                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +

                "**💣 Anti-Nuke — Kanalschutz**\n" +
                "Jede Kanallöschung → Sofortiger Restore · " + ModerationConfig.PROTECTION_TIMEOUT_DAYS + " Tage Timeout · DM · Alert\n" +
                "✅ Ausgenommen: " + owner + " · " + bot + "\n\n" +

                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +

                "**💣 Anti-Nuke — Rollenschutz**\n" +
                "≥" + ModerationConfig.MASS_DELETE_LIMIT + " Rollenlöschungen / " +
                    (ModerationConfig.MASS_DELETE_WINDOW_MS / 1000) + "s → Rolle restore · " +
                    ModerationConfig.PROTECTION_TIMEOUT_DAYS + " Tage Timeout · DM · Alert\n" +
                "✅ Ausgenommen: " + owner + " · " + bot + "\n\n" +

                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +

                "**🤖 Anti-Nuke — Fremde Bots**\n" +
                "Fremder Bot betritt den Server → Permanenter Bann · DM an Einladenden · Alert\n" +
                "✅ Ausgenommen: " + bot + "\n\n" +

                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n" +

                "**⚠️ Verwarnungssystem** (`/verwarnung`)\n" +
                "1.–2. Verwarnung → Warn-Rolle · Log\n" +
                "3. Verwarnung → Warn-Rolle · Log · 3 Tage Auto-Timeout · DM\n" +
                "✅ Ausgenommen: " + owner
            )
            .build();
    }

    // ════════════════════════════════════════════════════════════
    //  AUTOCOMPLETE – /entbannen (Bannliste)
    // ════════════════════════════════════════════════════════════

    @Override
    public void onCommandAutoCompleteInteraction(CommandAutoCompleteInteractionEvent event) {
        if (event.getGuild() == null) return;
        if ("verwarnung-löschen".equals(event.getName())) {
            handleVerwarnungLoeschenAutocomplete(event);
            return;
        }
        if (!"entbannen".equals(event.getName())) return;

        String query = event.getFocusedOption().getValue().toLowerCase();

        event.getGuild().retrieveBanList().queue(bans -> {
            List<Command.Choice> choices = bans.stream()
                .filter(b -> query.isBlank()
                    || b.getUser().getName().toLowerCase().contains(query)
                    || b.getUser().getId().contains(query))
                .limit(25)
                .map(b -> {
                    String label = b.getUser().getName() + " (" + b.getUser().getId() + ")" +
                        (b.getReason() != null ? " – " + truncate(b.getReason(), 40) : "");
                    return new Command.Choice(truncate(label, 100), b.getUser().getId());
                })
                .toList();

            event.replyChoices(choices).queue(null, err -> {});
        }, err -> event.replyChoices().queue(null, e -> {}));
    }

    // ════════════════════════════════════════════════════════════
    //  /löschen
    // ════════════════════════════════════════════════════════════

    private void handleLoeschen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (!(event.getChannel() instanceof TextChannel channel)) {
            event.replyEmbeds(embed("Fehler", "Nur in Text-Kanälen verwendbar.")).setEphemeral(true).queue();
            return;
        }

        int anzahl = Math.min(200, Math.max(1, event.getOption("anzahl", 1, OptionMapping::getAsInt)));
        event.deferReply(true).queue();

        // Nachrichten abrufen – max. 100 pro API-Aufruf
        fetchAndDelete(channel, anzahl, event);
    }

    private void fetchAndDelete(TextChannel channel, int anzahl, SlashCommandInteractionEvent event) {
        int firstBatch = Math.min(anzahl, 100);
        channel.getHistory().retrievePast(firstBatch).queue(batch1 -> {
            if (anzahl > 100 && batch1.size() == 100) {
                // Zweiten Batch holen
                Message last = batch1.get(batch1.size() - 1);
                int secondBatch = Math.min(anzahl - 100, 100);
                channel.getHistoryBefore(last, secondBatch).queue(hist -> {
                    batch1.addAll(hist.getRetrievedHistory());
                    doDelete(channel, batch1, anzahl, event);
                }, err -> doDelete(channel, batch1, anzahl, event));
            } else {
                doDelete(channel, batch1, anzahl, event);
            }
        }, err -> {
            log.error("Nachrichten konnten nicht abgerufen werden.", err);
            event.getHook().sendMessageEmbeds(embed("Fehler",
                "Nachrichten konnten nicht abgerufen werden.")).setEphemeral(true).queue();
        });
    }

    private void doDelete(TextChannel channel, List<Message> all, int requested, SlashCommandInteractionEvent event) {
        OffsetDateTime cutoff = OffsetDateTime.now().minusDays(14);
        List<Message> toDelete = all.stream()
            .filter(m -> m.getEmbeds().isEmpty())              // Embeds werden nie gelöscht
            .filter(m -> m.getTimeCreated().isAfter(cutoff))
            .limit(requested)
            .toList();
        final int skipped = all.size() - toDelete.size();

        if (toDelete.isEmpty()) {
            event.getHook().sendMessageEmbeds(embed("Keine Nachrichten",
                "Keine löschbaren Nachrichten gefunden.\n" +
                "_(Nachrichten älter als 14 Tage können nicht gelöscht werden.)_"))
                .setEphemeral(true).queue();
            return;
        }

        // Nachrichteninhalt vor dem Löschen sichern
        StringBuilder contentLog = new StringBuilder();
        for (Message m : toDelete) {
            String text = m.getContentDisplay().trim();
            if (text.isEmpty() && !m.getAttachments().isEmpty())
                text = "[" + m.getAttachments().size() + " Anhang/Anhänge]";
            else if (text.isEmpty())
                text = "[kein Text]";
            else if (text.length() > 120)
                text = text.substring(0, 120) + "…";
            contentLog.append("`").append(m.getAuthor().getName()).append("`: ")
                      .append(text).append("\n");
        }
        final String logText    = contentLog.toString();
        final int    deleteCount = toDelete.size();

        @SuppressWarnings("unchecked")
        List<CompletableFuture<Void>> futures = (List<CompletableFuture<Void>>) (List<?>) channel.purgeMessages(toDelete);
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).thenRun(() -> {

            // Rückmeldung an den Ausführenden (ephemeral)
            String desc = "✅ **" + deleteCount + " Nachricht(en) gelöscht**\n" +
                "**Kanal:** " + channel.getAsMention() + "\n" +
                "**Ausgeführt von:** " + event.getUser().getAsMention();
            if (skipped > 0) desc += "\n⚠️ " + skipped + " Nachricht(en) übersprungen (älter als 14 Tage)";
            event.getHook().sendMessageEmbeds(embed("Nachrichten gelöscht", desc)).setEphemeral(true).queue();

            // Log mit Nachrichteninhalten in den Nachrichten-Log-Kanal
            if (event.getGuild() == null) return;
            TextChannel logChannel = event.getGuild().getTextChannelById(LoggingConfig.MESSAGE_LOG_CHANNEL_ID);
            if (logChannel == null) return;

            String truncated = logText.length() > 1000
                ? logText.substring(0, 1000) + "\n_… weitere Nachrichten gekürzt_"
                : logText;

            net.dv8tion.jda.api.EmbedBuilder logEmbed = EmbedFactory.create()
                .setTitle("🗑️ " + deleteCount + " Nachrichten per Command gelöscht")
                .addField("📍 Kanal",          channel.getAsMention(),                                     true)
                .addField("👮 Ausgeführt von", event.getUser().getAsMention() + " | " + event.getUser().getName(), true)
                .addField("🔢 Anzahl",          String.valueOf(deleteCount),                                true)
                .addField("📝 Nachrichteninhalt", truncated.isBlank() ? "*(kein Inhalt)*" : truncated,    false)
;

            logChannel.sendMessageEmbeds(logEmbed.build()).queue();
        });
    }

    // ════════════════════════════════════════════════════════════
    //  /bannen
    // ════════════════════════════════════════════════════════════

    private void handleBannen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden.")).setEphemeral(true).queue();
            return;
        }
        String grund = event.getOption("grund", "Kein Grund angegeben", OptionMapping::getAsString);

        // Sicherheitsprüfungen
        if (target.getIdLong() == event.getUser().getIdLong()) {
            event.replyEmbeds(embed("Fehler", "Du kannst dich nicht selbst bannen.")).setEphemeral(true).queue();
            return;
        }
        if (target.getIdLong() == event.getJDA().getSelfUser().getIdLong()) {
            event.replyEmbeds(embed("Fehler", "Den Bot selbst zu bannen ist nicht möglich.")).setEphemeral(true).queue();
            return;
        }
        Member executor = event.getMember();
        if (executor != null && !ModerationConfig.isExempt(event.getUser().getIdLong())) {
            if (target.canInteract(executor)) {
                event.replyEmbeds(embed("Fehler",
                    "Du kannst kein Mitglied bannen, das die gleiche oder eine höhere Rolle hat."))
                    .setEphemeral(true).queue();
                return;
            }
        }

        event.deferReply(true).queue();

        // DM zuerst senden (Nutzer ist noch auf dem Server)
        BotLogger.tryDm(target.getUser(), EmbedFactory.build(
            "Du wurdest gebannt",
            "Du wurdest von **" + event.getGuild().getName() + "** permanent gebannt.\n\n" +
            "**Grund:** " + grund + "\n" +
            "**Gebannt von:** " + event.getUser().getName()));

        event.getGuild().ban(target.getUser(), 0, TimeUnit.SECONDS).reason(grund).queue(
            ok -> {
                BotLogger.logModeration(event.getGuild(),
                    "🔨 Mitglied gebannt (Befehl)",
                    "**Gebanntes Mitglied:** " + target.getAsMention() + " | " + target.getUser().getName() + " (`" + target.getId() + "`)\n" +
                    "**Gebannt von:** " + event.getUser().getAsMention() + " | " + event.getUser().getName() + " (`" + event.getUser().getId() + "`)\n" +
                    "**Grund:** " + grund + "\n" +
                    "**Art:** Permanenter Bann · DM gesendet");

                event.getHook().sendMessageEmbeds(embed("Mitglied gebannt",
                    "✅ **" + target.getUser().getName() + "** wurde permanent gebannt.\n" +
                    "**Grund:** " + grund + "\n**DM:** gesendet"))
                    .setEphemeral(true).queue();
            },
            err -> {
                log.error("Bann fehlgeschlagen.", err);
                event.getHook().sendMessageEmbeds(embed("Fehler",
                    "Bann fehlgeschlagen. Prüfe Rollen-Hierarchie und Bot-Berechtigungen."))
                    .setEphemeral(true).queue();
            }
        );
    }

    // ════════════════════════════════════════════════════════════
    //  /entbannen
    // ════════════════════════════════════════════════════════════

    private void handleEntbannen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String nutzerId = event.getOption("nutzer", "", OptionMapping::getAsString);

        long userId;
        try {
            userId = Long.parseLong(nutzerId);
        } catch (NumberFormatException ex) {
            event.replyEmbeds(embed("Ungültige Eingabe",
                "Bitte wähle einen Nutzer aus der Vorschlagsliste oder gib eine gültige Nutzer-ID ein."))
                .setEphemeral(true).queue();
            return;
        }

        event.deferReply(true).queue();
        long finalUserId = userId;

        event.getGuild().retrieveBan(UserSnowflake.fromId(userId)).queue(
            ban -> {
                event.getGuild().unban(UserSnowflake.fromId(finalUserId)).queue(
                    ok -> {
                        BotLogger.logModeration(event.getGuild(),
                            "✅ Bann aufgehoben (Befehl)",
                            "**Entbannter Nutzer:** " + ban.getUser().getName() + " (`" + ban.getUser().getId() + "`)\n" +
                            "**Entbannt von:** " + event.getUser().getAsMention() + " | " + event.getUser().getName() + " (`" + event.getUser().getId() + "`)\n" +
                            "**Ursprünglicher Grund:** " + (ban.getReason() != null ? ban.getReason() : "Nicht angegeben"));

                        event.getHook().sendMessageEmbeds(embed("Bann aufgehoben",
                            "✅ Der Bann von **" + ban.getUser().getName() + "** (`" + ban.getUser().getId() + "`) wurde aufgehoben."))
                            .setEphemeral(true).queue();
                    },
                    err -> event.getHook().sendMessageEmbeds(embed("Fehler", "Entbannen fehlgeschlagen.")).setEphemeral(true).queue());
            },
            err -> event.getHook().sendMessageEmbeds(embed("Nicht gefunden",
                "Kein Bann für ID `" + nutzerId + "` gefunden.")).setEphemeral(true).queue());
    }

    // ════════════════════════════════════════════════════════════
    //  /timeout
    // ════════════════════════════════════════════════════════════

    private void handleTimeout(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden.")).setEphemeral(true).queue();
            return;
        }
        String dauerKey = event.getOption("dauer", "10m", OptionMapping::getAsString);
        String grund    = event.getOption("grund", "Kein Grund angegeben", OptionMapping::getAsString);

        // Sicherheitsprüfungen
        if (target.getIdLong() == event.getUser().getIdLong()) {
            event.replyEmbeds(embed("Fehler", "Du kannst dich nicht selbst mit einem Timeout belegen.")).setEphemeral(true).queue();
            return;
        }
        if (ModerationConfig.isExempt(target.getIdLong())) {
            event.replyEmbeds(embed("Fehler", "Dieser Nutzer ist vom Timeout-System ausgenommen.")).setEphemeral(true).queue();
            return;
        }
        Member executor = event.getMember();
        if (executor != null && !ModerationConfig.isExempt(event.getUser().getIdLong())) {
            if (target.canInteract(executor)) {
                event.replyEmbeds(embed("Fehler",
                    "Du kannst kein Mitglied mit einem Timeout belegen, das die gleiche oder eine höhere Rolle hat."))
                    .setEphemeral(true).queue();
                return;
            }
        }

        Duration duration = parseDuration(dauerKey);
        OffsetDateTime until = OffsetDateTime.now().plus(duration);

        event.deferReply(true).queue();

        BotLogger.tryDm(target.getUser(), EmbedFactory.build(
            "Du hast einen Timeout erhalten",
            "Du hast auf **" + event.getGuild().getName() + "** einen Timeout erhalten.\n\n" +
            "**Dauer:** " + formatDuration(duration) + "\n" +
            "**Grund:** " + grund + "\n" +
            "**Gegeben von:** " + event.getUser().getName() + "\n" +
            "**Timeout endet:** <t:" + until.toEpochSecond() + ":F>"));

        event.getGuild().timeoutFor(target, duration).queue(
            ok -> {
                BotLogger.logModeration(event.getGuild(),
                    "⏱️ Timeout vergeben (Befehl)",
                    "**Mitglied:** " + target.getAsMention() + " | " + target.getUser().getName() + " (`" + target.getId() + "`)\n" +
                    "**Gegeben von:** " + event.getUser().getAsMention() + " | " + event.getUser().getName() + " (`" + event.getUser().getId() + "`)\n" +
                    "**Dauer:** " + formatDuration(duration) + "\n" +
                    "**Endet:** <t:" + until.toEpochSecond() + ":F>\n" +
                    "**Grund:** " + grund + "\n**DM:** gesendet");

                event.getHook().sendMessageEmbeds(embed("Timeout vergeben",
                    "✅ **" + target.getUser().getName() + "** hat einen Timeout für **" + formatDuration(duration) + "** erhalten.\n" +
                    "**Grund:** " + grund + "\n**Endet:** <t:" + until.toEpochSecond() + ":F>"))
                    .setEphemeral(true).queue();
            },
            err -> {
                log.error("Timeout fehlgeschlagen.", err);
                event.getHook().sendMessageEmbeds(embed("Fehler",
                    "Timeout fehlgeschlagen. Prüfe Rollen-Hierarchie und Bot-Berechtigungen."))
                    .setEphemeral(true).queue();
            });
    }

    // ════════════════════════════════════════════════════════════
    //  /ausweis
    // ════════════════════════════════════════════════════════════

    private void handleAusweis(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        // Nur im Ausweis-Kanal erlaubt
        if (event.getChannelIdLong() != RoleConfig.AUSWEIS_CHANNEL_ID) {
            event.replyEmbeds(embed("Falscher Kanal",
                "Dieser Command kann nur im <#" + RoleConfig.AUSWEIS_CHANNEL_ID + "> verwendet werden."))
                .setEphemeral(true).queue();
            return;
        }

        Member executor = event.getMember();
        if (executor == null) return;

        // Optionaler Fremd-Ausweis
        String targetUsername = event.getOption("nutzer", OptionMapping::getAsString);
        Member target;

        if (targetUsername != null && !targetUsername.isBlank()) {
            target = BotContext.findMemberByUsername(targetUsername);
            if (target == null) {
                event.replyEmbeds(embed("Nicht gefunden",
                    "Kein Mitglied mit dem Nutzernamen **" + targetUsername + "** gefunden."))
                    .setEphemeral(true).queue();
                return;
            }
        } else {
            target = executor;
        }

        // Einreiseart aus Rollen ableiten
        boolean isLegal   = target.getRoles().stream().anyMatch(r -> r.getIdLong() == RoleConfig.LEGAL_RESIDENT_ROLE_ID);
        boolean isIllegal = !isLegal && target.getRoles().stream()
            .anyMatch(r -> {
                for (long id : RoleConfig.ILLEGAL_ROLES) if (r.getIdLong() == id) return true;
                return false;
            });

        String einreise = isLegal ? "✅ Legal" : isIllegal ? "🚫 Illegal" : "❓ Unbekannt";

        // Konto-Erstellungsdatum (Epoch-Sekunden)
        long createdEpoch = target.getUser().getTimeCreated().toEpochSecond();
        // Beitrittsdatum
        long joinedEpoch  = target.getTimeJoined().toEpochSecond();

        net.dv8tion.jda.api.entities.MessageEmbed ausweisEmbed = EmbedFactory.create()
            .setTitle("🪪 Personalausweis — " + target.getUser().getName())
            .setThumbnail(target.getUser().getEffectiveAvatarUrl())
            .setDescription(
                "**Mitglied:** " + target.getAsMention() + "\n" +
                "**Einreiseart:** " + einreise + "\n\n" +
                "━━━━━━━━━━━━━━━━━━━━━━\n\n" +
                "📅 **Discord-Konto erstellt:** <t:" + createdEpoch + ":D>\n" +
                "📥 **Server beigetreten:** <t:" + joinedEpoch + ":D>")
            .build();

        event.replyEmbeds(ausweisEmbed).setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /verwarnung
    // ════════════════════════════════════════════════════════════

    private void handleVerwarnung(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        String grund       = event.getOption("grund",      OptionMapping::getAsString);
        String konsequenz  = event.getOption("konsequenz", OptionMapping::getAsString);

        if (target == null || grund == null || konsequenz == null) {
            event.replyEmbeds(embed("Fehler", "Alle Felder sind erforderlich.")).setEphemeral(true).queue();
            return;
        }
        if (target.getUser().isBot()) {
            event.replyEmbeds(embed("Fehler", "Bots können nicht verwarnt werden.")).setEphemeral(true).queue();
            return;
        }

        long guildId = event.getGuild().getIdLong();
        long userId  = target.getIdLong();
        List<WarnStore.WarnEntry> existing = WarnStore.getWarns(guildId, userId);

        if (existing.size() >= 3) {
            event.replyEmbeds(embed("Maximum erreicht",
                target.getAsMention() + " hat bereits **3 Verwarnungen** und kann keine weiteren erhalten."))
                .setEphemeral(true).queue();
            return;
        }

        event.deferReply(true).queue();

        WarnStore.WarnEntry warn = new WarnStore.WarnEntry(
            grund, konsequenz,
            event.getUser().getId(), event.getUser().getName());
        int total = WarnStore.addWarn(guildId, userId, warn);

        // Rollen-Handling
        applyWarnRole(event.getGuild(), target, total);

        // Log-Embed (rot)
        TextChannel logCh = event.getGuild().getTextChannelById(LoggingConfig.WARN_LOG_CHANNEL_ID);
        if (logCh != null) {
            logCh.sendMessageEmbeds(buildWarnEmbed(total, event.getUser(), target.getUser(), grund, konsequenz))
                 .queue();
        }

        // Auto-Timeout bei 3 Warns
        if (total == 3) {
            Duration dur = Duration.ofDays(3);
            BotLogger.tryDm(target.getUser(), EmbedFactory.build(
                "⚠️ Du hast 3 Verwarnungen erhalten",
                "Du hast auf **" + event.getGuild().getName() + "** die dritte Verwarnung erhalten " +
                "und wurdest automatisch für **3 Tage** mit einem Timeout belegt.\n\n" +
                "**Letzte Verwarnung**\n" +
                "**Grund:** " + grund + "\n" +
                "**Konsequenz:** " + konsequenz));
            event.getGuild().timeoutFor(target, dur).queue(
                v -> log.info("[Warn] Auto-Timeout für {} (3 Warns).", target.getUser().getName()),
                e -> log.warn("[Warn] Auto-Timeout fehlgeschlagen.", e));
        }

        event.getHook().sendMessageEmbeds(embed("✅ Verwarnung erteilt",
            target.getAsMention() + " hat jetzt **" + total + "/3** Verwarnungen." +
            (total == 3 ? "\n⏱️ Automatischer **3-Tage-Timeout** wurde verhängt." : "")))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /verwarn-liste
    // ════════════════════════════════════════════════════════════

    private void handleVerwarnListe(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        List<WarnStore.WarnEntry> warns = WarnStore.getWarns(
            event.getGuild().getIdLong(), target.getIdLong());

        if (warns.isEmpty()) {
            event.replyEmbeds(embed("Keine Verwarnungen",
                target.getAsMention() + " hat keine Verwarnungen."))
                .setEphemeral(true).queue();
            return;
        }

        StringBuilder sb = new StringBuilder();
        sb.append("**").append(target.getUser().getName())
          .append("** — ").append(warns.size()).append("/3 Verwarnungen\n\n");
        sb.append("━━━━━━━━━━━━━━━━━━━━━━\n\n");

        for (int i = 0; i < warns.size(); i++) {
            WarnStore.WarnEntry w = warns.get(i);
            sb.append("**").append(i + 1).append(". Verwarnung** (").append(w.dateString()).append(")\n");
            sb.append("📝 **Grund:** ").append(w.reason).append("\n");
            sb.append("⚖️ **Konsequenz:** ").append(w.consequence).append("\n");
            sb.append("👮 **Von:** <@").append(w.byId).append(">\n");
            sb.append("`ID: ").append(w.id, 0, 8).append("…`\n");
            if (i < warns.size() - 1) sb.append("\n");
        }

        event.replyEmbeds(buildWarnListEmbed(sb.toString()))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /verwarnung-löschen  +  Autocomplete
    // ════════════════════════════════════════════════════════════

    private void handleVerwarnungLoeschenAutocomplete(CommandAutoCompleteInteractionEvent event) {
        OptionMapping memberOpt = event.getOption("mitglied");
        if (memberOpt == null) { event.replyChoices().queue(null, e -> {}); return; }

        long userId;
        try { userId = Long.parseLong(memberOpt.getAsString()); }
        catch (NumberFormatException e) { event.replyChoices().queue(null, ex -> {}); return; }

        List<WarnStore.WarnEntry> warns = WarnStore.getWarns(event.getGuild().getIdLong(), userId);
        String query = event.getFocusedOption().getValue().toLowerCase();

        List<Command.Choice> choices = new ArrayList<>();
        for (int i = 0; i < warns.size(); i++) {
            WarnStore.WarnEntry w = warns.get(i);
            String label = (i + 1) + ". " + truncate(w.reason, 40) + " — " + w.dateString();
            if (query.isBlank() || label.toLowerCase().contains(query) || w.id.startsWith(query)) {
                choices.add(new Command.Choice(truncate(label, 100), w.id));
            }
        }
        event.replyChoices(choices).queue(null, e -> {});
    }

    private void handleVerwarnungLoeschen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        String warnId  = event.getOption("warn-id",  OptionMapping::getAsString);

        if (target == null || warnId == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied oder Verwarnung nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        long guildId = event.getGuild().getIdLong();
        long userId  = target.getIdLong();

        boolean removed = WarnStore.removeWarn(guildId, userId, warnId);
        if (!removed) {
            event.replyEmbeds(embed("Nicht gefunden",
                "Verwarnung mit dieser ID wurde nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        // Rolle nach neuer Anzahl anpassen
        List<WarnStore.WarnEntry> remaining = WarnStore.getWarns(guildId, userId);
        applyWarnRole(event.getGuild(), target, remaining.size());

        event.replyEmbeds(embed("✅ Verwarnung entfernt",
            "Eine Verwarnung von " + target.getAsMention() + " wurde gelöscht.\n" +
            "Aktuelle Verwarnungen: **" + remaining.size() + "/3**"))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  Warn-Hilfsmethoden
    // ════════════════════════════════════════════════════════════

    private static void applyWarnRole(net.dv8tion.jda.api.entities.Guild guild, Member member, int warnCount) {
        long[] warnRoleIds = RoleConfig.WARN_ROLES;

        // Alle alten Warn-Rollen entfernen
        for (long rid : warnRoleIds) {
            Role r = guild.getRoleById(rid);
            if (r != null && member.getRoles().stream().anyMatch(mr -> mr.getIdLong() == rid)) {
                guild.removeRoleFromMember(member, r).queue(null, e -> {});
            }
        }
        // Neue Warn-Rolle vergeben (falls noch Warns vorhanden)
        if (warnCount >= 1 && warnCount <= 3) {
            Role r = guild.getRoleById(warnRoleIds[warnCount - 1]);
            if (r != null) guild.addRoleToMember(member, r).queue(null, e -> {});
        }
    }

    private static net.dv8tion.jda.api.entities.MessageEmbed buildWarnEmbed(
            int total, User by, User target, String grund, String konsequenz) {
        return new EmbedBuilder()
            .setColor(Color.RED)
            .setTitle("⚠️ Verwarnung " + total + "/3")
            .addField("👮 Von",         by.getAsMention(),     true)
            .addField("🎯 An",          target.getAsMention(), true)
            .addField("📝 Grund",       grund,      false)
            .addField("⚖️ Konsequenz", konsequenz, false)
            .build();
    }

    private static net.dv8tion.jda.api.entities.MessageEmbed buildWarnListEmbed(String description) {
        return new EmbedBuilder()
            .setColor(Color.RED)
            .setTitle("📋 Verwarnungsliste")
            .setDescription(description)
            .build();
    }

    // ════════════════════════════════════════════════════════════
    //  /event
    // ════════════════════════════════════════════════════════════

    private void handleEvent(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        String was          = event.getOption("was",          OptionMapping::getAsString);
        String beschreibung = event.getOption("beschreibung", OptionMapping::getAsString);
        String wo           = event.getOption("wo",           OptionMapping::getAsString);
        String wann         = event.getOption("wann",         OptionMapping::getAsString);

        if (was == null || beschreibung == null || wo == null || wann == null) {
            event.replyEmbeds(embed("Fehler", "Alle Felder sind erforderlich.")).setEphemeral(true).queue();
            return;
        }

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.EVENT_CHANNEL_ID);
        if (ch == null) {
            event.replyEmbeds(embed("Fehler", "Event-Kanal nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        event.deferReply(true).queue();

        net.dv8tion.jda.api.entities.MessageEmbed eventEmbed = EmbedFactory.create()
            .setTitle("📅 " + was)
            .setDescription(
                beschreibung + "\n\n" +
                "━━━━━━━━━━━━━━━━━━━━━━\n\n" +
                "📍 **Wo:** " + wo + "\n" +
                "🕐 **Wann:** " + wann)
            .build();

        final String finalWas = was;
        ch.sendMessage("<@&" + LoggingConfig.EVENT_ROLE_ID + ">")
          .setEmbeds(eventEmbed)
          .queue(
            msg -> event.getHook().sendMessageEmbeds(embed("✅ Event gepostet",
                "Das Event **" + finalWas + "** wurde in <#" + LoggingConfig.EVENT_CHANNEL_ID + "> veröffentlicht."))
                .setEphemeral(true).queue(),
            err -> {
                log.error("[Event] Konnte nicht gesendet werden.", err);
                event.getHook().sendMessageEmbeds(embed("Fehler", "Event konnte nicht gepostet werden."))
                    .setEphemeral(true).queue();
            });
    }

    // ════════════════════════════════════════════════════════════
    //  /gewinnspiel
    // ════════════════════════════════════════════════════════════

    private void handleGewinnspiel(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        String titel = event.getOption("titel", OptionMapping::getAsString);
        String was   = event.getOption("was",   OptionMapping::getAsString);
        String dauer = event.getOption("dauer", "1h", OptionMapping::getAsString);

        if (titel == null || was == null) {
            event.replyEmbeds(embed("Fehler", "Titel und Preis sind erforderlich.")).setEphemeral(true).queue();
            return;
        }

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.GEWINNSPIEL_CHANNEL_ID);
        if (ch == null) {
            event.replyEmbeds(embed("Fehler", "Gewinnspiel-Kanal nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        long delaySec = parseDauerSeconds(dauer);
        long endEpoch = System.currentTimeMillis() / 1000 + delaySec;

        event.deferReply(true).queue();

        net.dv8tion.jda.api.entities.MessageEmbed gEmbed =
            GiveawayListener.buildEmbed(titel, was, endEpoch, 0);

        final String finalTitel = titel;
        final String finalWas   = was;
        final long   fDelay     = delaySec;
        final long   fEnd       = endEpoch;
        final long   guildId    = event.getGuild().getIdLong();

        ch.sendMessage("@everyone")
          .setEmbeds(gEmbed)
          .queue(msg -> {
              // Persistieren
              String stored = "GIVEAWAY\n"
                  + GiveawayListener.encode(finalTitel) + "\n"
                  + GiveawayListener.encode(finalWas)   + "\n"
                  + fEnd                                + "\n"
                  + ch.getIdLong()                      + "\n"
                  + guildId;
              DataStore.writeString("giveaway-" + msg.getId(), stored);
              GiveawayListener.addToList(msg.getId());

              // 🎉 hinzufügen
              msg.addReaction(net.dv8tion.jda.api.entities.emoji.Emoji.fromUnicode(GiveawayListener.PARTY)).queue();

              // Ablauf planen
              GiveawayListener.schedule(event.getJDA(), msg.getId(), ch.getIdLong(), guildId, fDelay);

              event.getHook().sendMessageEmbeds(embed("✅ Gewinnspiel gestartet",
                  "Das Gewinnspiel **" + finalTitel + "** wurde in <#"
                  + LoggingConfig.GEWINNSPIEL_CHANNEL_ID + "> gepostet.\n"
                  + "⏰ Endet <t:" + fEnd + ":R>"))
                  .setEphemeral(true).queue();
          }, err -> {
              log.error("[Gewinnspiel] Konnte nicht gesendet werden.", err);
              event.getHook().sendMessageEmbeds(embed("Fehler", "Gewinnspiel konnte nicht erstellt werden."))
                  .setEphemeral(true).queue();
          });
    }

    private static long parseDauerSeconds(String key) {
        return switch (key) {
            case "10m" -> 600L;
            case "30m" -> 1_800L;
            case "1h"  -> 3_600L;
            case "6h"  -> 21_600L;
            case "12h" -> 43_200L;
            case "1d"  -> 86_400L;
            case "3d"  -> 259_200L;
            case "7d"  -> 604_800L;
            default    -> 3_600L;
        };
    }

    // ════════════════════════════════════════════════════════════
    //  /abstimmung
    // ════════════════════════════════════════════════════════════

    private void handleAbstimmung(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        String titel = event.getOption("titel", OptionMapping::getAsString);
        String text  = event.getOption("text",  OptionMapping::getAsString);

        if (titel == null || text == null) {
            event.replyEmbeds(embed("Fehler", "Titel und Text sind erforderlich.")).setEphemeral(true).queue();
            return;
        }

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.ABSTIMMUNG_CHANNEL_ID);
        if (ch == null) {
            event.replyEmbeds(embed("Fehler", "Abstimmungs-Kanal nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        event.deferReply(true).queue();

        net.dv8tion.jda.api.entities.MessageEmbed pollEmbed =
            PollListener.buildPollEmbed(titel, text, "", 0, 0);

        final String finalTitel = titel;
        final String finalText  = text;

        ch.sendMessage("<@&" + LoggingConfig.ABSTIMMUNG_ROLE_ID + ">")
          .setEmbeds(pollEmbed)
          .queue(msg -> {
              // Abstimmungsdaten speichern
              String stored = "POLL\n"
                  + PollListener.encode(finalTitel) + "\n"
                  + PollListener.encode(finalText)  + "\n"
                  + PollListener.encode("");
              DataStore.writeString("poll-" + msg.getId(), stored);

              // Reaktionen hinzufügen (sequenziell, um Reihenfolge zu garantieren)
              msg.addReaction(Emoji.fromUnicode(PollListener.THUMB_UP)).queue(
                  v -> msg.addReaction(Emoji.fromUnicode(PollListener.THUMB_DOWN)).queue()
              );

              event.getHook().sendMessageEmbeds(embed("✅ Abstimmung erstellt",
                  "Die Abstimmung **" + finalTitel + "** wurde in <#"
                  + LoggingConfig.ABSTIMMUNG_CHANNEL_ID + "> gepostet."))
                  .setEphemeral(true).queue();
          }, err -> {
              log.error("[Abstimmung] Konnte nicht gesendet werden.", err);
              event.getHook().sendMessageEmbeds(embed("Fehler",
                  "Die Abstimmung konnte nicht erstellt werden."))
                  .setEphemeral(true).queue();
          });
    }

    // ════════════════════════════════════════════════════════════
    //  /aktivitätscheck
    // ════════════════════════════════════════════════════════════

    private void handleAktivitaetscheck(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.AKTIVITAETSCHECK_CHANNEL_ID);
        if (ch == null) {
            event.replyEmbeds(embed("Fehler", "Aktivitätscheck-Kanal nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        event.deferReply(true).queue();

        final String title = "Aktivitätscheck";
        net.dv8tion.jda.api.entities.MessageEmbed actEmbed = PollListener.buildActivityEmbed(title, 0);

        ch.sendMessage("@everyone")
          .setEmbeds(actEmbed)
          .queue(msg -> {
              DataStore.writeString("poll-" + msg.getId(),
                  "ACTIVITY\n" + PollListener.encode(title));

              msg.addReaction(Emoji.fromUnicode(PollListener.CHECK)).queue();

              event.getHook().sendMessageEmbeds(embed("✅ Aktivitätscheck gesendet",
                  "Der Aktivitätscheck wurde in <#"
                  + LoggingConfig.AKTIVITAETSCHECK_CHANNEL_ID + "> gepostet."))
                  .setEphemeral(true).queue();
          }, err -> {
              log.error("[Aktivitätscheck] Konnte nicht gesendet werden.", err);
              event.getHook().sendMessageEmbeds(embed("Fehler",
                  "Der Aktivitätscheck konnte nicht erstellt werden."))
                  .setEphemeral(true).queue();
          });
    }

    // ════════════════════════════════════════════════════════════
    //  /einreise-sperre
    // ════════════════════════════════════════════════════════════

    private void handleEinreiseSperre(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String key = "einreise-sperre-" + event.getGuild().getId();

        String existing = DataStore.readString(key);
        if (existing != null && !existing.isBlank()) {
            event.replyEmbeds(embed("Bereits aktiv",
                "⛔ Der Einreise-Stopp ist **bereits aktiv**. Nutze `/einreise-entsperren` um ihn aufzuheben."))
                .setEphemeral(true).queue();
            return;
        }

        DataStore.writeString(key, "active");
        event.replyEmbeds(embed("✅ Einreise-Stopp aktiviert",
            "Der Einreise-Stopp ist jetzt **aktiv**. Die Website zeigt den Sperr-Bildschirm."))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /einreise-entsperren
    // ════════════════════════════════════════════════════════════

    private void handleEinreiseEntsperre(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String key = "einreise-sperre-" + event.getGuild().getId();

        String stored = DataStore.readString(key);
        if (stored == null || stored.isBlank()) {
            event.replyEmbeds(embed("Nicht aktiv",
                "Es ist derzeit **kein Einreise-Stopp** aktiv."))
                .setEphemeral(true).queue();
            return;
        }

        event.deferReply(true).queue();
        finishEinreiseEntsperre(event, key);
    }

    private void finishEinreiseEntsperre(SlashCommandInteractionEvent event, String sperreKey) {
        Guild guild = event.getGuild();
        DataStore.deleteKey(sperreKey);

        // Notify-Liste abarbeiten
        String notifyKey = "einreise-notify-" + guild.getId();
        String raw = DataStore.readString(notifyKey);
        int notified = 0;
        if (raw != null && !raw.isBlank()) {
            try {
                com.google.gson.JsonArray arr = new com.google.gson.Gson().fromJson(raw, com.google.gson.JsonArray.class);
                net.dv8tion.jda.api.entities.MessageEmbed dmEmbed = new EmbedBuilder()
                    .setColor(new java.awt.Color(0x22CC55))
                    .setTitle("✅ Die Einreise ist wieder offen!")
                    .setDescription("Der Einreise-Stopp auf **Paradise City Roleplay** wurde aufgehoben.\n" +
                                    "Du kannst dich jetzt im Einwohner Meldeamt registrieren.")
                    .build();
                for (com.google.gson.JsonElement el : arr) {
                    try {
                        Member m = guild.getMemberById(el.getAsString());
                        if (m != null) { BotLogger.tryDm(m.getUser(), dmEmbed); notified++; }
                    } catch (Exception ignored) {}
                }
                DataStore.deleteKey(notifyKey);
            } catch (Exception e) {
                log.warn("Fehler beim Versenden der Einreise-Benachrichtigungen: {}", e.getMessage());
            }
        }

        String extra = notified > 0 ? "\n**" + notified + " Mitglieder** wurden per DM benachrichtigt." : "";
        event.getHook().sendMessageEmbeds(embed("✅ Einreise-Stopp aufgehoben",
            "Der Einreise-Stopp wurde entfernt. Die Einreise ist wieder möglich." + extra))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  HILFS-METHODEN
    // ════════════════════════════════════════════════════════════

    private static net.dv8tion.jda.api.entities.MessageEmbed embed(String title, String description) {
        return EmbedFactory.build(title, description);
    }

    private static Duration parseDuration(String key) {
        return switch (key) {
            case "5m"  -> Duration.ofMinutes(5);
            case "10m" -> Duration.ofMinutes(10);
            case "30m" -> Duration.ofMinutes(30);
            case "1h"  -> Duration.ofHours(1);
            case "6h"  -> Duration.ofHours(6);
            case "12h" -> Duration.ofHours(12);
            case "1d"  -> Duration.ofDays(1);
            case "3d"  -> Duration.ofDays(3);
            case "7d"  -> Duration.ofDays(7);
            case "14d" -> Duration.ofDays(14);
            default    -> Duration.ofMinutes(10);
        };
    }

    private static String formatDuration(Duration d) {
        long days  = d.toDays();
        long hours = d.toHoursPart();
        long mins  = d.toMinutesPart();
        if (days  > 0) return days  + " Tag"    + (days  == 1 ? "" : "e");
        if (hours > 0) return hours + " Stunde"  + (hours == 1 ? "" : "n");
        return mins + " Minute" + (mins == 1 ? "" : "n");
    }

    private static String truncate(String s, int max) {
        return s != null && s.length() > max ? s.substring(0, max - 1) + "…" : (s != null ? s : "");
    }
}
