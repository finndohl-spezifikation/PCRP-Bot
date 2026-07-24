package de.pcrp.bot.listeners;

import com.google.gson.JsonObject;
import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.Permission;
import net.dv8tion.jda.api.entities.*;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.entities.emoji.Emoji;
import net.dv8tion.jda.api.events.interaction.command.*;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.commands.Command;
import net.dv8tion.jda.api.interactions.commands.OptionMapping;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
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
        }
    }

    // ════════════════════════════════════════════════════════════
    //  AUTOCOMPLETE – /entbannen (Bannliste)
    // ════════════════════════════════════════════════════════════

    @Override
    public void onCommandAutoCompleteInteraction(CommandAutoCompleteInteractionEvent event) {
        if (!"entbannen".equals(event.getName())) return;
        if (event.getGuild() == null) return;

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
        if (executor != null && event.getUser().getIdLong() != ModerationConfig.OWNER_ID) {
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
        if (target.getIdLong() == ModerationConfig.OWNER_ID) {
            event.replyEmbeds(embed("Fehler", "Der Inhaber kann keinen Timeout erhalten.")).setEphemeral(true).queue();
            return;
        }
        Member executor = event.getMember();
        if (executor != null && event.getUser().getIdLong() != ModerationConfig.OWNER_ID) {
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

        // Nur legale Bewohner
        boolean hasRole = executor.getRoles().stream()
            .anyMatch(r -> r.getIdLong() == RoleConfig.LEGAL_RESIDENT_ROLE_ID);
        if (!hasRole) {
            event.replyEmbeds(embed("Kein Zugriff",
                "Nur legale Bewohner <@&" + RoleConfig.LEGAL_RESIDENT_ROLE_ID + "> können einen Ausweis einsehen."))
                .setEphemeral(true).queue();
            return;
        }

        // Optionaler Fremd-Ausweis
        String targetUsername = event.getOption("nutzer", OptionMapping::getAsString);
        long   targetId;
        String targetName;

        if (targetUsername != null && !targetUsername.isBlank()) {
            Member target = BotContext.findMemberByUsername(targetUsername);
            if (target == null) {
                event.replyEmbeds(embed("Nicht gefunden",
                    "Kein Mitglied mit dem Nutzernamen **" + targetUsername + "** gefunden."))
                    .setEphemeral(true).queue();
                return;
            }
            targetId   = target.getIdLong();
            targetName = target.getUser().getName();
        } else {
            targetId   = executor.getIdLong();
            targetName = executor.getUser().getName();
        }

        // Charakter prüfen
        JsonObject character = CharacterStore.get(event.getGuild().getIdLong(), targetId);
        if (character == null) {
            event.replyEmbeds(embed("Kein Ausweis",
                "Für **" + targetName + "** wurde kein registrierter Charakter gefunden."))
                .setEphemeral(true).queue();
            return;
        }
        if (!"legal".equals(CharacterStore.str(character, "type"))) {
            event.replyEmbeds(embed("Kein Ausweis",
                "**" + targetName + "** ist illegal eingereist und besitzt keinen Ausweis."))
                .setEphemeral(true).queue();
            return;
        }

        String webUrl     = System.getenv().getOrDefault("WEB_URL", "https://example.com");
        String ausweisUrl = webUrl + "/ausweis/" + targetId;

        event.replyEmbeds(embed("🪪 Personalausweis",
                "Ausweis von **" + CharacterStore.str(character, "firstName") + " "
                + CharacterStore.str(character, "lastName") + "**"))
            .addActionRow(Button.link(ausweisUrl, "🪪 Ausweis einsehen"))
            .setEphemeral(true)
            .queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /abstimmung
    // ════════════════════════════════════════════════════════════

    private void handleAbstimmung(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        String titel    = event.getOption("titel",    OptionMapping::getAsString);
        String text     = event.getOption("text",     OptionMapping::getAsString);
        String optionen = event.getOption("optionen", "", OptionMapping::getAsString);

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
            PollListener.buildPollEmbed(titel, text, optionen, 0, 0);

        final String finalTitel    = titel;
        final String finalText     = text;
        final String finalOptionen = optionen;

        ch.sendMessage("<@&" + LoggingConfig.ABSTIMMUNG_ROLE_ID + ">")
          .setEmbeds(pollEmbed)
          .queue(msg -> {
              // Abstimmungsdaten speichern
              String stored = "POLL\n"
                  + PollListener.encode(finalTitel) + "\n"
                  + PollListener.encode(finalText)  + "\n"
                  + PollListener.encode(finalOptionen);
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
