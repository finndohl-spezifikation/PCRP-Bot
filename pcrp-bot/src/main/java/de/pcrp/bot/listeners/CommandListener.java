package de.pcrp.bot.listeners;

import com.google.gson.JsonObject;
import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.Permission;
import net.dv8tion.jda.api.entities.*;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.entities.emoji.Emoji;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.command.*;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.StringSelectInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.commands.Command;
import net.dv8tion.jda.api.interactions.commands.OptionMapping;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.dv8tion.jda.api.utils.FileUpload;

import java.awt.Color;
import java.io.InputStream;
import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

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
            case "embed-schreiben"  -> handleEmbedSchreiben(event);
            case "bannen"           -> handleBannen(event);
            case "entbannen"        -> handleEntbannen(event);
            case "timeout"          -> handleTimeout(event);
            case "ausweis-erstellen"      -> handleAusweisErstellen(event);
            case "ausweis-löschen"        -> handleAusweisLoeschen(event);
            case "führerschein-erstellen" -> handleFuehrerscheinErstellen(event);
            case "führerschein-löschen"   -> handleFuehrerscheinLoeschen(event);
            case "verbrauchen"            -> handleVerbrauchen(event);
            case "verstecken"             -> handleVerstecken(event);
            case "abstimmung"       -> handleAbstimmung(event);
            case "aktivitätscheck"  -> handleAktivitaetscheck(event);
            case "event"               -> handleEvent(event);
            case "gewinnspiel"         -> handleGewinnspiel(event);
            case "verwarnung"          -> handleVerwarnung(event);
            case "verwarn-liste"       -> handleVerwarnListe(event);
            case "verwarnung-löschen"  -> handleVerwarnungLoeschen(event);
            case "einreise-sperre"     -> handleEinreiseSperre(event);
            case "einreise-entsperren" -> handleEinreiseEntsperre(event);
            case "frak-erstellen"      -> handleFrakErstellen(event);
            case "frak-löschen"        -> handleFrakLoeschen(event);
            case "frakwarn"            -> handleFrakWarn(event);
            case "frakwarn-entfernen"  -> handleFrakWarnEntfernen(event);
            case "frak-sperren"        -> handleFrakSperren(event);
            case "frak-entsperren"     -> handleFrakEntsprerren(event);
            case "teamverwarnung"        -> handleTeamverwarnung(event);
            case "teamverwarnung-entfernen" -> handleTeamverwarnungEntfernen(event);
            case "teamverwarnung-liste"  -> handleTeamverwarnungListe(event);
            case "spieler-info"          -> handleSpielerInfo(event);
            case "item-geben"          -> handleItemGeben(event);
            case "item-erstellen"      -> handleItemErstellen(event);
            case "item-bearbeiten"     -> handleItemBearbeiten(event);
            case "item-löschen"        -> handleItemLoeschen(event);
            case "item-entnehmen"      -> handleItemEntnehmen(event);
            case "geld-geben"          -> handleGeldGeben(event);
            case "geld-entfernen"      -> handleGeldEntfernen(event);
            case "lobby-abstimmung"    -> handleLobbyAbstimmung(event);
            case "lobby-öffnen"        -> handleLobbyOeffnen(event);
            case "lobby-schließen"     -> handleLobbySchliessen(event);
            case "vorschlag"           -> handleVorschlag(event);
            case "vorschlag-annehmen"    -> handleVorschlagAnnehmen(event);
            case "vorschlag-ablehnen"    -> handleVorschlagAblehnen(event);
            case "bannen-dashboard"      -> handleBannenDashboard(event);
            case "entbannen-dashboard"   -> handleEntbannenDashboard(event);
            // (handy-reset + bewohner-information entfernt — siehe Commit-History)
            case "charakter-zurücksetzen" -> handleCharakterZuruecksetzen(event);
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
        String guildId = event.getGuild().getId();

        switch (event.getName()) {
            case "verwarnung-löschen"      -> handleVerwarnungLoeschenAutocomplete(event);
            case "teamverwarnung-entfernen" -> handleTeamverwarnungEntfernenAutocomplete(event);
            // Item-Management: Wert = itemId
            case "item-bearbeiten", "item-löschen" -> {
                if (!"item".equals(event.getFocusedOption().getName())) return;
                String typed = event.getFocusedOption().getValue().toLowerCase();
                List<Command.Choice> choices = ShopManager.getAllItems(guildId).stream()
                    .filter(it -> it.name.toLowerCase().contains(typed))
                    .limit(25)
                    .map(it -> new Command.Choice(
                        it.name + " (" + ShopManager.formatPrice(it.price) + " — " + ShopManager.shopDisplayName(it.shopId) + ")",
                        it.id))
                    .collect(Collectors.toList());
                event.replyChoices(choices).queue(null, e -> {});
            }
            // Inventar geben/entnehmen: Wert = Artikelname
            case "item-geben", "item-entnehmen" -> {
                if (!"item".equals(event.getFocusedOption().getName())) return;
                String typed2 = event.getFocusedOption().getValue().toLowerCase();
                List<Command.Choice> choices2 = ShopManager.getAllItems(guildId).stream()
                    .filter(it -> it.name.toLowerCase().contains(typed2))
                    .limit(25)
                    .map(it -> new Command.Choice(it.name, it.name))
                    .collect(Collectors.toList());
                event.replyChoices(choices2).queue(null, e -> {});
            }
            // /verbrauchen item: autocomplete (eigene sichtbare Items als Vorschläge)
            case "verbrauchen" -> handleVerbrauchenAutocomplete(event);
            case "vorschlag-annehmen", "vorschlag-ablehnen" -> {
                if (!"vorschlag".equals(event.getFocusedOption().getName())) return;
                String typed = event.getFocusedOption().getValue().toLowerCase();
                List<Command.Choice> choices = VorschlagManager.getActive(guildId).stream()
                    .filter(v -> v.title.toLowerCase().contains(typed))
                    .limit(25)
                    .map(v -> new Command.Choice(v.title, v.messageId))
                    .collect(Collectors.toList());
                event.replyChoices(choices).queue(null, e -> {});
            }
            case "frakwarn", "frakwarn-entfernen", "frak-sperren", "frak-entsperren" -> {
                if (!"fraktion".equals(event.getFocusedOption().getName())) return;
                String typed = event.getFocusedOption().getValue().toLowerCase();
                List<Command.Choice> choices = FraktionManager.getFrakList(guildId).stream()
                    .filter(f -> f.toLowerCase().contains(typed))
                    .limit(25)
                    .map(f -> new Command.Choice(f, f))
                    .collect(Collectors.toList());
                event.replyChoices(choices).queue(null, e -> {});
            }
            case "entbannen" -> {
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
            case "ausweis-löschen", "führerschein-löschen" -> {
                if (!"wer".equals(event.getFocusedOption().getName())) return;
                String typed = event.getFocusedOption().getValue().toLowerCase();
                if (BotContext.getGuild() == null) { event.replyChoices().queue(null, e -> {}); return; }
                List<Command.Choice> choices = BotContext.getGuild().getMembers().stream()
                    .filter(m -> !m.getUser().isBot())
                    .filter(m -> m.getUser().getName().toLowerCase().contains(typed)
                              || m.getEffectiveName().toLowerCase().contains(typed)
                              || m.getUser().getId().contains(typed))
                    .limit(25)
                    .map(m -> new Command.Choice(
                        m.getEffectiveName() + " (" + m.getUser().getId() + ")",
                        m.getUser().getId()))
                    .collect(Collectors.toList());
                event.replyChoices(choices).queue(null, e -> {});
            }
        }
    }

    // ════════════════════════════════════════════════════════════
    //  /embed-schreiben
    // ════════════════════════════════════════════════════════════

    private void handleEmbedSchreiben(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        String colorName = event.getOption("farbe", "blau", OptionMapping::getAsString);
        var channelOpt = event.getOption("kanal");
        String title = event.getOption("titel", "", OptionMapping::getAsString);
        String text  = event.getOption("text",  "", OptionMapping::getAsString);

        if (channelOpt == null || !(channelOpt.getAsChannel() instanceof TextChannel channel)) {
            event.replyEmbeds(embed("Fehler", "Bitte einen gültigen Text-Kanal wählen.")).setEphemeral(true).queue();
            return;
        }
        if (title.isBlank() && text.isBlank()) {
            event.replyEmbeds(embed("Fehler", "Titel oder Text darf nicht leer sein.")).setEphemeral(true).queue();
            return;
        }

        event.deferReply(true).queue();
        channel.sendMessageEmbeds(
            EmbedFactory.create()
                .setTitle(title.isBlank() ? " " : title)
                .setDescription(text)
                .setColor(parseEmbedColor(colorName))
                .build()
        ).queue(
            msg -> {
                CustomEmbedManager.mark(event.getGuild().getIdLong(), msg.getId());
                event.getHook().sendMessageEmbeds(embed("✅ Embed gesendet",
                    "Das Embed wurde in " + channel.getAsMention() + " gesendet.\n" +
                    "Es ist frei löschbar – manuell oder mit /löschen."))
                    .setEphemeral(true).queue(null, e -> {});
            },
            err -> event.getHook().sendMessageEmbeds(embed("Fehler",
                "Das Embed konnte nicht gesendet werden.")).setEphemeral(true).queue(null, e -> {})
        );
    }

    private static Color parseEmbedColor(String name) {
        return switch (name == null ? "" : name.toLowerCase()) {
            case "rot"     -> new Color(0xE74C3C);
            case "orange"  -> new Color(0xE67E22);
            case "gelb"    -> new Color(0xF1C40F);
            case "grün"    -> new Color(0x2ECC71);
            case "blau"    -> new Color(0x3498DB);
            case "lila"    -> new Color(0x9B59B6);
            case "pink"    -> new Color(0xE91E63);
            case "schwarz" -> new Color(0x000000);
            case "weiß"    -> new Color(0xFFFFFF);
            case "grau"    -> new Color(0x95A5A6);
            default        -> new Color(0x3498DB);
        };
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
        boolean allowEmbeds = LoggingListener.ALLOWED_EMBED_DELETION_CHANNELS.contains(channel.getIdLong());
        long guildId = channel.getGuild().getIdLong();
        List<Message> toDelete = all.stream()
            .filter(m -> allowEmbeds || m.getEmbeds().isEmpty()
                    || CustomEmbedManager.isCustom(guildId, m.getId()))  // Custom-Embeds immer löschbar
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
    //  /ausweis-erstellen — DM an Executor mit Web-Form-Link
    // ════════════════════════════════════════════════════════════

    private void handleAusweisErstellen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target = event.getOption("wer", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden."))
                .setEphemeral(true).queue();
            return;
        }
        // Rolle prüfen: nur Legaler Bewohner
        boolean isLegalResident = target.getRoles().stream()
            .anyMatch(r -> r.getIdLong() == RoleConfig.LEGAL_RESIDENT_ROLE_ID);
        if (!isLegalResident) {
            event.replyEmbeds(embed("Fehler",
                target.getAsMention() + " hat **nicht** die Rolle **Legaler Bewohner** " +
                "(<@&" + RoleConfig.LEGAL_RESIDENT_ROLE_ID + ">). Ausweis-Erstellung nur " +
                "nach legaler Einreise möglich."))
                .setEphemeral(true).queue();
            return;
        }

        String guildId   = event.getGuild().getId();
        String createUrl = DocumentsManager.ausweisCreateUrl(guildId, target.getId());

        // DM-Öffnung ist async — daher deferReply VOR .queue(...)
        event.deferReply(true).queue();

        final Member finTarget = target;
        final String finUrl    = createUrl;

        event.getUser().openPrivateChannel().queue(pc -> {
            pc.sendMessageEmbeds(EmbedFactory.build(
                "🪪 Personalausweis erstellen — " + finTarget.getEffectiveName(),
                "Klicke unten auf den Link und fülle das Formular aus.\n\n" +
                "**Zielperson:** " + finTarget.getAsMention() + "\n" +
                "**Server:** " + event.getGuild().getName() + "\n\n" +
                "Der ausgefüllte Ausweis wird automatisch im Bot gespeichert."))
                .setActionRow(Button.link(finUrl, "🪪 Ausweis-Formular öffnen"))
                .queue(ok -> event.getHook().sendMessageEmbeds(embed("✅ DM gesendet",
                    "Kontrolliere deine DMs — das Ausweis-Formular wartet auf dich."))
                    .setEphemeral(true).queue(),
                    err -> event.getHook().sendMessageEmbeds(embed("❌ DM geschlossen",
                        "Deine DMs sind geschlossen. Öffne sie und versuche es erneut."))
                        .setEphemeral(true).queue());
        }, err -> event.getHook().sendMessageEmbeds(embed("❌ Fehler",
            "DM-Kanal konnte nicht geöffnet werden."))
            .setEphemeral(true).queue());
    }

    // ════════════════════════════════════════════════════════════
    //  /ausweis-löschen — löscht nur den Ausweis-Datensatz
    // ════════════════════════════════════════════════════════════

    private void handleAusweisLoeschen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        String targetId;
        String targetName;

        String werOpt = event.getOption("wer", OptionMapping::getAsString);
        if (werOpt != null && !werOpt.isBlank()) {
            try {
                Member m = event.getGuild().retrieveMemberById(werOpt).complete();
                if (m == null) throw new IllegalArgumentException("not in guild");
                targetId   = m.getId();
                targetName = m.getEffectiveName();
            } catch (Exception e) {
                event.replyEmbeds(embed("Nicht gefunden",
                    "Kein Mitglied mit dieser ID gefunden."))
                    .setEphemeral(true).queue();
                return;
            }
        } else {
            targetId   = event.getUser().getId();
            Member execA = event.getMember();
            targetName = (execA != null ? execA.getEffectiveName() : event.getUser().getName());
        }

        String guildId = event.getGuild().getId();
        if (!DocumentsManager.hasAusweis(guildId, targetId)) {
            event.replyEmbeds(embed("Kein Ausweis",
                "**" + targetName + "** hat aktuell keinen Ausweis."))
                .setEphemeral(true).queue();
            return;
        }

        DocumentsManager.deleteAusweis(guildId, targetId);
        String finalTargetName = targetName;
        event.replyEmbeds(embed("🗑️ Ausweis gelöscht",
            "Der Ausweis von **" + finalTargetName + "** wurde entfernt.\n\n" +
            "ℹ️ Inventar, Geld und Rollen sind **unverändert** geblieben."))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /führerschein-erstellen — DM an Executor mit Web-Form-Link
    // ════════════════════════════════════════════════════════════

    private void handleFuehrerscheinErstellen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target = event.getOption("wer", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden."))
                .setEphemeral(true).queue();
            return;
        }

        String guildId   = event.getGuild().getId();
        String createUrl = DocumentsManager.fuehrerscheinCreateUrl(guildId, target.getId());

        // DM-Öffnung ist async — daher deferReply VOR .queue(...)
        event.deferReply(true).queue();

        final Member finTarget = target;
        final String finUrl    = createUrl;

        event.getUser().openPrivateChannel().queue(pc -> {
            pc.sendMessageEmbeds(EmbedFactory.build(
                "🚗 Führerschein erstellen — " + finTarget.getEffectiveName(),
                "Klicke unten auf den Link und fülle das Formular aus.\n\n" +
                "**Zielperson:** " + finTarget.getAsMention() + "\n" +
                "**Server:** " + event.getGuild().getName() + "\n\n" +
                "Trage alle Daten ein, die für einen Führerschein nötig sind.\n" +
                "Der ausgefüllte Führerschein wird automatisch im Bot gespeichert."))
                .setActionRow(Button.link(finUrl, "🚗 Führerschein-Formular öffnen"))
                .queue(ok -> event.getHook().sendMessageEmbeds(embed("✅ DM gesendet",
                    "Kontrolliere deine DMs — das Führerschein-Formular wartet auf dich."))
                    .setEphemeral(true).queue(),
                    err -> event.getHook().sendMessageEmbeds(embed("❌ DM geschlossen",
                        "Deine DMs sind geschlossen. Öffne sie und versuche es erneut."))
                        .setEphemeral(true).queue());
        }, err -> event.getHook().sendMessageEmbeds(embed("❌ Fehler",
            "DM-Kanal konnte nicht geöffnet werden."))
            .setEphemeral(true).queue());
    }

    // ════════════════════════════════════════════════════════════
    //  /führerschein-löschen
    // ════════════════════════════════════════════════════════════

    private void handleFuehrerscheinLoeschen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        String targetId;
        String targetName;

        String werOpt = event.getOption("wer", OptionMapping::getAsString);
        if (werOpt != null && !werOpt.isBlank()) {
            try {
                Member m = event.getGuild().retrieveMemberById(werOpt).complete();
                if (m == null) throw new IllegalArgumentException("not in guild");
                targetId   = m.getId();
                targetName = m.getEffectiveName();
            } catch (Exception e) {
                event.replyEmbeds(embed("Nicht gefunden",
                    "Kein Mitglied mit dieser ID gefunden."))
                    .setEphemeral(true).queue();
                return;
            }
        } else {
            targetId   = event.getUser().getId();
            Member execB = event.getMember();
            targetName = (execB != null ? execB.getEffectiveName() : event.getUser().getName());
        }

        String guildId = event.getGuild().getId();
        if (!DocumentsManager.hasFuehrerschein(guildId, targetId)) {
            event.replyEmbeds(embed("Kein Führerschein",
                "**" + targetName + "** hat aktuell keinen Führerschein."))
                .setEphemeral(true).queue();
            return;
        }

        DocumentsManager.deleteFuehrerschein(guildId, targetId);
        String finalTargetName = targetName;
        event.replyEmbeds(embed("🗑️ Führerschein gelöscht",
            "Der Führerschein von **" + finalTargetName + "** wurde entfernt."))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /verbrauchen  —  item + menge direkt im Command (wie /lizenzen) → Info-Embed
    // ════════════════════════════════════════════════════════════

    private void handleVerbrauchen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        // PLAIN-Nachricht (kein Embed) bei falschem Kanal
        if (event.getChannel().getIdLong() != LoggingConfig.INVENTORY_ACTIONS_CHANNEL_ID) {
            event.reply("Dieser command funktioniert nur in <#" + LoggingConfig.INVENTORY_ACTIONS_CHANNEL_ID + ">")
                .setEphemeral(true).queue();
            return;
        }
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();

        String itemName = event.getOption("item", "", OptionMapping::getAsString).trim();
        long   qtyLong  = event.getOption("menge", 1L, OptionMapping::getAsLong);

        if (itemName.isEmpty()) {
            event.reply("❌ Du musst ein Item angeben (Tipp `item:` und such dir eines aus).")
                .setEphemeral(true).queue();
            return;
        }
        if (qtyLong <= 0) {
            event.reply("❌ Die Menge muss größer als 0 sein.")
                .setEphemeral(true).queue();
            return;
        }
        if (qtyLong > Integer.MAX_VALUE) {
            event.reply("❌ Die Menge ist zu groß.")
                .setEphemeral(true).queue();
            return;
        }
        int qty = (int) qtyLong;

        int maxQty = InventoryManager.getVisibleItems(guildId, userId).stream()
            .filter(it -> InventoryManager.nameMatches(it.name, itemName))
            .mapToInt(it -> it.quantity).sum();
        if (maxQty <= 0) {
            event.reply("ℹ️ **" + itemName + "** ist nicht in deinem Inventar.")
                .setEphemeral(true).queue();
            return;
        }
        if (qty > maxQty) {
            event.reply("❌ Du hast nur **" + maxQty + "× ** **" + itemName + "** — mehr geht nicht.")
                .setEphemeral(true).queue();
            return;
        }

        boolean removed = InventoryManager.removeItem(guildId, userId, itemName, qty);
        if (!removed) {
            event.reply("❌ Konnte **" + itemName + "** nicht abbuchen.")
                .setEphemeral(true).queue();
            return;
        }

        // Ephemeral-Bestätigung an dich
        event.reply("✅ Du hast **" + itemName + "** × " + qty + " verbraucht.")
            .setEphemeral(true).queue();

        // Öffentliches Info-Embed im Inventar-Aktionen-Kanal
        Member member = event.getMember();
        String actor  = member != null ? member.getEffectiveName() : event.getUser().getName();
        TextChannel ch = event.getGuild().getTextChannelById(
            LoggingConfig.INVENTORY_ACTIONS_CHANNEL_ID);
        if (ch != null) {
            ch.sendMessageEmbeds(EmbedFactory.build("🍽️ Item verbraucht",
                "**" + actor + "** hat **" + itemName + "** × " + qty + " verbraucht."))
                .queue();
        }
    }

    /** Autocomplete für `/verbrauchen item:` — filtert die sichtbaren Items des Nutzers. */
    private void handleVerbrauchenAutocomplete(CommandAutoCompleteInteractionEvent event) {
        if (!"item".equals(event.getFocusedOption().getName())) { event.replyChoices().queue(); return; }
        if (event.getGuild() == null) { event.replyChoices().queue(); return; }
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();
        String typed   = event.getFocusedOption().getValue().toLowerCase();

        List<Command.Choice> choices = InventoryManager.getVisibleItems(guildId, userId).stream()
            .filter(it -> typed.isBlank() || it.name.toLowerCase().contains(typed))
            .limit(25)
            .map(it -> new Command.Choice(it.name + " × " + it.quantity, it.name))
            .collect(Collectors.toList());
        event.replyChoices(choices).queue(null, e -> {});
    }
    //  /verstecken — Item auswählen → setHidden(true) + Info-Embed

    private void handleVerstecken(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (event.getChannel().getIdLong() != LoggingConfig.INVENTORY_ACTIONS_CHANNEL_ID) {
            event.replyEmbeds(embed("Falscher Kanal",
                "`/verstecken` ist nur im Inventar-Aktionen-Kanal erlaubt."))
                .setEphemeral(true).queue();
            return;
        }
        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();

        List<InventoryManager.Item> items = InventoryManager.getVisibleItems(guildId, userId);
        if (items.isEmpty()) {
            event.replyEmbeds(embed("Leeres Inventar",
                "Du hast aktuell keine sichtbaren Items zum Verstecken."))
                .setEphemeral(true).queue();
            return;
        }

        StringSelectMenu.Builder menu = StringSelectMenu.create("verstecken-item:" + userId)
            .setPlaceholder("Welches Item möchtest du verstecken?")
            .setMinValues(1).setMaxValues(1);
        int n = 0;
        for (InventoryManager.Item it : items) {
            if (++n > 25) break;
            menu.addOption(it.name + " × " + it.quantity, it.name);
        }

        event.replyEmbeds(EmbedFactory.build("🫣 Item verstecken",
            "Wähle unten das Item aus, das im Inventar versteckt werden soll."))
            .addActionRow(menu.build())
            .setEphemeral(true).queue();
    }

    /** StringSelect: führt das Verstecken aus + postet Info-Embed im Kanal. */
    private void handleVersteckenSelect(StringSelectInteractionEvent event) {
        String[] parts = event.getComponentId().split(":", 2);
        if (parts.length < 2) return;
        String userId = parts[1];
        if (!userId.equals(event.getUser().getId())) {
            event.replyEmbeds(embed("❌ Fehler",
                "Nur deine eigenen Items können versteckt werden."))
                .setEphemeral(true).queue();
            return;
        }

        String itemName = event.getValues().get(0);
        String guildId  = event.getGuild().getId();

        InventoryManager.setHidden(guildId, userId, itemName, true);

        event.replyEmbeds(embed("✅ Versteckt",
            "**" + itemName + "** ist jetzt im Inventar versteckt."))
            .setEphemeral(true).queue();

        Member member = event.getMember();
        String actor  = member != null ? member.getEffectiveName() : event.getUser().getName();
        TextChannel ch = event.getGuild().getTextChannelById(
            LoggingConfig.INVENTORY_ACTIONS_CHANNEL_ID);
        if (ch != null) {
            // Minimal-Info in der IC Konsole: "Beispiel hat folgendes Item versteckt: <Item>"
            ch.sendMessageEmbeds(EmbedFactory.build(
                "🫣 Item versteckt",
                actor + " hat folgendes Item versteckt: **" + itemName + "**"))
                .queue();
        }
    }

    // ════════════════════════════════════════════════════════════
    //  StringSelect & Modal Event-Handler
    // ════════════════════════════════════════════════════════════

    @Override
    public void onStringSelectInteraction(StringSelectInteractionEvent event) {
        String id = event.getComponentId();
        if (id.startsWith("verstecken-item:"))  handleVersteckenSelect(event);
        // Weitere IDs (rucksack-unhide-…) werden vom RucksackListener behandelt
    }

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        // Modal-IDs für /verbrauchen gibt es nicht mehr (Args direkt im Command).
        // Andere Modal-IDs (rucksack-transfer-items) werden vom RucksackListener behandelt
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

    // ════════════════════════════════════════════════════════════
    //  /frak-erstellen  /frak-löschen
    // ════════════════════════════════════════════════════════════

    private void handleFrakErstellen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String name = event.getOption("fraktion", OptionMapping::getAsString);
        if (name == null) return;
        String guildId = event.getGuild().getId();

        if (!FraktionManager.addFrak(guildId, name)) {
            event.replyEmbeds(embed("Bereits vorhanden",
                "Die Fraktion **" + name + "** existiert bereits in der Liste."))
                .setEphemeral(true).queue();
            return;
        }
        FraktionManager.updatePanelEmbed(event.getGuild());
        event.replyEmbeds(embed("✅ Fraktion erstellt",
            "**" + name + "** wurde zur Fraktions-Liste hinzugefügt."))
            .setEphemeral(true).queue();
    }

    private void handleFrakLoeschen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String name = event.getOption("fraktion", OptionMapping::getAsString);
        if (name == null) return;
        String guildId = event.getGuild().getId();

        if (!FraktionManager.removeFrak(guildId, name)) {
            event.replyEmbeds(embed("Nicht gefunden",
                "Die Fraktion **" + name + "** existiert nicht in der Liste."))
                .setEphemeral(true).queue();
            return;
        }
        // Warns + Sperre mitlöschen
        FraktionManager.clearWarns(guildId, name);
        FraktionManager.unlock(guildId, name);
        FraktionManager.updatePanelEmbed(event.getGuild());
        event.replyEmbeds(embed("✅ Fraktion gelöscht",
            "**" + name + "** wurde entfernt. Alle Verwarnungen und Sperren wurden ebenfalls gelöscht."))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /frakwarn  /frakwarn-entfernen  /frak-sperren  /frak-entsperren
    // ════════════════════════════════════════════════════════════

    private void handleFrakWarn(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String frak       = event.getOption("fraktion",   OptionMapping::getAsString);
        String grund      = event.getOption("grund",      OptionMapping::getAsString);
        String konsequenz = event.getOption("konsequenz", OptionMapping::getAsString);
        if (frak == null || grund == null || konsequenz == null) return;

        String guildId = event.getGuild().getId();
        if (!FraktionManager.frakExists(guildId, frak)) {
            event.replyEmbeds(embed("Fraktion nicht gefunden",
                "**" + frak + "** existiert nicht. Erstelle sie zuerst mit `/frak-erstellen`."))
                .setEphemeral(true).queue();
            return;
        }
        int count = FraktionManager.addWarn(guildId, frak, grund, konsequenz, event.getUser().getName());

        // Warn-Embed in Frak-Warn-Kanal
        TextChannel warnCh = event.getGuild().getTextChannelById(LoggingConfig.FRAK_WARN_CHANNEL_ID);
        if (warnCh != null) {
            warnCh.sendMessageEmbeds(new EmbedBuilder()
                .setColor(new Color(0xE07B00))
                .setTitle("⚠️ Fraktionsverwarnung — " + frak)
                .setDescription(
                    "**Verwarnung " + count + "/3**\n\n" +
                    "**Fraktion:** " + frak + "\n" +
                    "**Grund:** " + grund + "\n" +
                    "**Konsequenz:** " + konsequenz + "\n" +
                    "**Ausgesprochen von:** " + event.getUser().getAsMention())
                .build()).queue();
        }

        // Bei 3. Verwarnung → sperren
        if (count >= 3) {
            FraktionManager.lock(guildId, frak);
            FraktionManager.updatePanelEmbed(event.getGuild());
            TextChannel sperreCh = event.getGuild().getTextChannelById(LoggingConfig.FRAK_SPERRE_CHANNEL_ID);
            if (sperreCh != null) {
                sperreCh.sendMessageEmbeds(new EmbedBuilder()
                    .setColor(Color.RED)
                    .setTitle("🔴 Fraktionssperre — " + frak)
                    .setDescription(
                        "Die Fraktion **" + frak + "** hat **3 Verwarnungen** erhalten und wurde gesperrt.\n\n" +
                        "**Letzte Verwarnung von:** " + event.getUser().getAsMention() + "\n" +
                        "**Grund:** " + grund)
                    .build()).queue();
            }
        } else {
            FraktionManager.updatePanelEmbed(event.getGuild());
        }

        event.replyEmbeds(embed("✅ Verwarnung ausgesprochen",
            "**" + frak + "** hat jetzt **" + count + "/3** Verwarnungen." +
            (count >= 3 ? "\n🔴 Die Fraktion wurde automatisch **gesperrt**." : "")))
            .setEphemeral(true).queue();
    }

    private void handleFrakWarnEntfernen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String frak = event.getOption("fraktion", OptionMapping::getAsString);
        if (frak == null) return;
        String guildId = event.getGuild().getId();
        if (!FraktionManager.frakExists(guildId, frak)) {
            event.replyEmbeds(embed("Fraktion nicht gefunden",
                "**" + frak + "** existiert nicht in der Liste."))
                .setEphemeral(true).queue();
            return;
        }

        FraktionManager.clearWarns(guildId, frak);
        FraktionManager.unlock(guildId, frak);
        FraktionManager.updatePanelEmbed(event.getGuild());

        event.replyEmbeds(embed("✅ Verwarnungen entfernt",
            "Alle Verwarnungen und eine eventuelle Sperre von **" + frak + "** wurden aufgehoben."))
            .setEphemeral(true).queue();
    }

    private void handleFrakSperren(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String frak  = event.getOption("fraktion", OptionMapping::getAsString);
        String grund = event.getOption("grund",    OptionMapping::getAsString);
        if (frak == null || grund == null) return;
        String guildId = event.getGuild().getId();
        if (!FraktionManager.frakExists(guildId, frak)) {
            event.replyEmbeds(embed("Fraktion nicht gefunden",
                "**" + frak + "** existiert nicht in der Liste."))
                .setEphemeral(true).queue();
            return;
        }

        FraktionManager.lock(guildId, frak);
        FraktionManager.updatePanelEmbed(event.getGuild());

        TextChannel sperreCh = event.getGuild().getTextChannelById(LoggingConfig.FRAK_SPERRE_CHANNEL_ID);
        if (sperreCh != null) {
            sperreCh.sendMessageEmbeds(new EmbedBuilder()
                .setColor(Color.RED)
                .setTitle("🔴 Fraktionssperre — " + frak)
                .setDescription(
                    "**Fraktion:** " + frak + "\n" +
                    "**Grund:** " + grund + "\n" +
                    "**Gesperrt von:** " + event.getUser().getAsMention())
                .build()).queue();
        }

        event.replyEmbeds(embed("🔴 Fraktion gesperrt",
            "**" + frak + "** wurde gesperrt und im Fraktions-Embed durchgestrichen."))
            .setEphemeral(true).queue();
    }

    private void handleFrakEntsprerren(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String frak = event.getOption("fraktion", OptionMapping::getAsString);
        if (frak == null) return;
        String guildId = event.getGuild().getId();
        if (!FraktionManager.frakExists(guildId, frak)) {
            event.replyEmbeds(embed("Fraktion nicht gefunden",
                "**" + frak + "** existiert nicht in der Liste."))
                .setEphemeral(true).queue();
            return;
        }

        FraktionManager.unlock(guildId, frak);
        FraktionManager.updatePanelEmbed(event.getGuild());

        event.replyEmbeds(embed("✅ Fraktion entsperrt",
            "**" + frak + "** wurde entsperrt und erscheint wieder normal in der Liste."))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /vorschlag  /vorschlag-annehmen  /vorschlag-ablehnen
    // ════════════════════════════════════════════════════════════

    // ════════════════════════════════════════════════════════════
    //  /lobby-abstimmung
    // ════════════════════════════════════════════════════════════

    private void handleItemGeben(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target   = event.getOption("mitglied", OptionMapping::getAsMember);
        String itemName = event.getOption("item",     OptionMapping::getAsString);
        long   qty      = event.getOption("menge",    OptionMapping::getAsLong);
        if (target == null || itemName == null || itemName.isBlank()) return;
        if (qty <= 0) {
            event.replyEmbeds(embed("Fehler", "Die Menge muss größer als 0 sein."))
                .setEphemeral(true).queue();
            return;
        }
        InventoryManager.addItem(event.getGuild().getId(), target.getId(), itemName.trim(), (int) qty);
        event.replyEmbeds(embed("✅ Item vergeben",
            "**" + itemName.trim() + "** × " + qty + " wurde dem Inventar von **" +
            target.getEffectiveName() + "** hinzugefügt."))
            .setEphemeral(true).queue();
        BotLogger.tryDm(target.getUser(), EmbedFactory.build(
            "📦 Item erhalten",
            "Du hast **" + itemName.trim() + "** × " + qty + " von einem Admin erhalten."));
        BotLogger.logItem(event.getGuild(), "📦 Item gegeben",
            "**Admin:** " + event.getUser().getAsMention() + "\n" +
            "**Spieler:** " + target.getAsMention() + " (" + target.getEffectiveName() + ")\n" +
            "**Item:** " + itemName.trim() + " × " + qty);
    }

    // ── Item-Erstellen ────────────────────────────────────────────────────────

    private void handleItemErstellen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String  name   = event.getOption("name",  OptionMapping::getAsString);
        Long    preis  = event.getOption("preis", OptionMapping::getAsLong);
        String  shopId = event.getOption("shop",  OptionMapping::getAsString);
        if (name == null || name.isBlank() || preis == null || shopId == null) return;
        if (preis <= 0) {
            event.replyEmbeds(embed("Fehler", "Der Preis muss größer als 0 sein."))
                .setEphemeral(true).queue(); return;
        }
        String id = ShopManager.addItem(event.getGuild().getId(), name.trim(), (int) Math.min(preis, Integer.MAX_VALUE), shopId);
        event.replyEmbeds(embed("✅ Artikel erstellt",
            "**" + name.trim() + "** wurde für **" + ShopManager.formatPrice(preis)
            + "** im Shop **" + ShopManager.shopDisplayName(shopId) + "** hinzugefügt.\n`ID: " + id + "`"))
            .setEphemeral(true).queue();
        BotLogger.logItem(event.getGuild(), "📦 Item erstellt",
            "**Admin:** " + event.getUser().getAsMention() + "\n" +
            "**Item:** " + name.trim() + "\n" +
            "**Preis:** " + ShopManager.formatPrice(preis) + "\n" +
            "**Shop:** " + ShopManager.shopDisplayName(shopId));
    }

    // ── Item-Bearbeiten ───────────────────────────────────────────────────────

    private void handleItemBearbeiten(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String  itemId    = event.getOption("item",       OptionMapping::getAsString);
        String  neuerName = event.getOption("neuer-name", OptionMapping::getAsString);
        Long    neuerPreis= event.getOption("neuer-preis",OptionMapping::getAsLong);
        String  neuerShop = event.getOption("neuer-shop", OptionMapping::getAsString);
        if (itemId == null || itemId.isBlank()) return;
        String guildId = event.getGuild().getId();
        ShopManager.ShopItem item = ShopManager.getItemById(guildId, itemId);
        if (item == null) {
            event.replyEmbeds(embed("Nicht gefunden", "Kein Artikel mit dieser ID gefunden."))
                .setEphemeral(true).queue(); return;
        }
        boolean changed = ShopManager.editItem(guildId, itemId,
            neuerName, neuerPreis != null ? (int) Math.min(neuerPreis, Integer.MAX_VALUE) : null, neuerShop);
        if (!changed) {
            event.replyEmbeds(embed("Fehler", "Artikel konnte nicht bearbeitet werden."))
                .setEphemeral(true).queue(); return;
        }
        ShopManager.ShopItem updated = ShopManager.getItemById(guildId, itemId);
        event.replyEmbeds(embed("✅ Artikel bearbeitet",
            "**" + updated.name + "** — **" + ShopManager.formatPrice(updated.price)
            + "** im Shop **" + ShopManager.shopDisplayName(updated.shopId) + "**"))
            .setEphemeral(true).queue();
        BotLogger.logItem(event.getGuild(), "✏️ Item bearbeitet",
            "**Admin:** " + event.getUser().getAsMention() + "\n" +
            "**Item:** " + item.name + " → " + updated.name + "\n" +
            "**Preis:** " + ShopManager.formatPrice(item.price) + " → " + ShopManager.formatPrice(updated.price) + "\n" +
            "**Shop:** " + ShopManager.shopDisplayName(updated.shopId));
    }

    // ── Item-Löschen ──────────────────────────────────────────────────────────

    private void handleItemLoeschen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String itemId = event.getOption("item", OptionMapping::getAsString);
        if (itemId == null || itemId.isBlank()) return;
        String guildId = event.getGuild().getId();
        ShopManager.ShopItem item = ShopManager.getItemById(guildId, itemId);
        if (item == null) {
            event.replyEmbeds(embed("Nicht gefunden", "Kein Artikel mit dieser ID gefunden."))
                .setEphemeral(true).queue(); return;
        }
        ShopManager.removeItem(guildId, itemId);
        event.replyEmbeds(embed("🗑️ Artikel gelöscht",
            "**" + item.name + "** wurde aus dem Shop **"
            + ShopManager.shopDisplayName(item.shopId) + "** entfernt."))
            .setEphemeral(true).queue();
        BotLogger.logItem(event.getGuild(), "🗑️ Item gelöscht",
            "**Admin:** " + event.getUser().getAsMention() + "\n" +
            "**Item:** " + item.name + "\n" +
            "**Shop:** " + ShopManager.shopDisplayName(item.shopId));
    }

    // ── Item-Entnehmen ────────────────────────────────────────────────────────

    private void handleItemEntnehmen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target   = event.getOption("mitglied", OptionMapping::getAsMember);
        String itemName = event.getOption("item",     OptionMapping::getAsString);
        long   qty      = event.getOption("menge",    OptionMapping::getAsLong);
        if (target == null || itemName == null || itemName.isBlank()) return;
        if (qty <= 0) {
            event.replyEmbeds(embed("Fehler", "Die Menge muss größer als 0 sein."))
                .setEphemeral(true).queue(); return;
        }
        boolean removed = InventoryManager.removeItem(
            event.getGuild().getId(), target.getId(), itemName.trim(), (int) qty);
        if (!removed) {
            event.replyEmbeds(embed("Fehler",
                "**" + target.getEffectiveName() + "** besitzt kein **" + itemName.trim() + "** (oder nicht genug)."))
                .setEphemeral(true).queue(); return;
        }
        event.replyEmbeds(embed("✅ Item entnommen",
            "**" + itemName.trim() + "** × " + qty + " wurde aus dem Inventar von **"
            + target.getEffectiveName() + "** entfernt."))
            .setEphemeral(true).queue();
        BotLogger.tryDm(target.getUser(), EmbedFactory.build(
            "📦 Item entnommen",
            "**" + itemName.trim() + "** × " + qty + " wurde von einem Admin aus deinem Inventar entfernt."));
        BotLogger.logItem(event.getGuild(), "📦 Item entnommen",
            "**Admin:** " + event.getUser().getAsMention() + "\n" +
            "**Spieler:** " + target.getAsMention() + " (" + target.getEffectiveName() + ")\n" +
            "**Item:** " + itemName.trim() + " × " + qty);
    }

    // ── Geld-Geben ────────────────────────────────────────────────────────────

    private void handleGeldGeben(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        String typ    = event.getOption("typ",      OptionMapping::getAsString);
        Long   betrag = event.getOption("betrag",   OptionMapping::getAsLong);
        if (target == null || typ == null || betrag == null) return;
        if (betrag <= 0) {
            event.replyEmbeds(embed("Fehler", "Der Betrag muss größer als 0 sein."))
                .setEphemeral(true).queue(); return;
        }
        String guildId = event.getGuild().getId();
        boolean isBank   = "kontogeld".equalsIgnoreCase(typ);
        boolean isCrypto = "pc-coins".equalsIgnoreCase(typ);

        if (isCrypto) {
            KryptoManager.adminGive(guildId, target.getId(), betrag);
            event.replyEmbeds(embed("✅ PC Coins gegeben",
                "**+" + KryptoManager.formatCoins(betrag) + "** wurden **" + target.getEffectiveName()
                + "** gutgeschrieben."))
                .setEphemeral(true).queue();
            BotLogger.tryDm(target.getUser(), EmbedFactory.build(
                "🪙 PC Coins erhalten",
                "Du hast **+" + KryptoManager.formatCoins(betrag) + "** von einem Admin erhalten."));
            BotLogger.logMoney(event.getGuild(), "🪙 PC Coins gegeben",
                "**Admin:** " + event.getUser().getAsMention() + "\n" +
                "**Spieler:** " + target.getAsMention() + " (" + target.getEffectiveName() + ")\n" +
                "**Menge:** +" + KryptoManager.formatCoins(betrag));
            return;
        }

        BankManager.adminAdd(guildId, target.getId(), betrag, isBank);
        String typLabel = isBank ? "Kontogeld" : "Bargeld";
        event.replyEmbeds(embed("✅ Geld gegeben",
            "**+" + BankManager.formatAmount(betrag) + "** " + typLabel
            + " wurden **" + target.getEffectiveName() + "** gutgeschrieben."))
            .setEphemeral(true).queue();
        BotLogger.tryDm(target.getUser(), EmbedFactory.build(
            "💰 Geld erhalten",
            "Du hast **+" + BankManager.formatAmount(betrag) + "** " + typLabel
            + " von einem Admin erhalten."));
        BotLogger.logMoney(event.getGuild(), "💰 Geld gegeben",
            "**Admin:** " + event.getUser().getAsMention() + "\n" +
            "**Spieler:** " + target.getAsMention() + " (" + target.getEffectiveName() + ")\n" +
            "**Betrag:** +" + BankManager.formatAmount(betrag) + " (" + typLabel + ")");
    }

    // ── Geld-Entfernen ────────────────────────────────────────────────────────

    private void handleGeldEntfernen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        String typ    = event.getOption("typ",      OptionMapping::getAsString);
        Long   betrag = event.getOption("betrag",   OptionMapping::getAsLong);
        if (target == null || typ == null || betrag == null) return;
        if (betrag <= 0) {
            event.replyEmbeds(embed("Fehler", "Der Betrag muss größer als 0 sein."))
                .setEphemeral(true).queue(); return;
        }
        String guildId = event.getGuild().getId();
        boolean isBank   = "kontogeld".equalsIgnoreCase(typ);
        boolean isCrypto = "pc-coins".equalsIgnoreCase(typ);

        if (isCrypto) {
            String errCrypto = KryptoManager.adminRemove(guildId, target.getId(), betrag);
            if (errCrypto != null) {
                event.replyEmbeds(embed("❌ Fehler", errCrypto)).setEphemeral(true).queue(); return;
            }
            event.replyEmbeds(embed("✅ PC Coins entfernt",
                "**-" + KryptoManager.formatCoins(betrag) + "** wurden von **" + target.getEffectiveName() + "** abgezogen."))
                .setEphemeral(true).queue();
            BotLogger.tryDm(target.getUser(), EmbedFactory.build(
                "🪙 PC Coins abgezogen",
                "**-" + KryptoManager.formatCoins(betrag) + "** wurden von einem Admin abgezogen."));
            BotLogger.logMoney(event.getGuild(), "🪙 PC Coins entfernt",
                "**Admin:** " + event.getUser().getAsMention() + "\n" +
                "**Spieler:** " + target.getAsMention() + " (" + target.getEffectiveName() + ")\n" +
                "**Menge:** -" + KryptoManager.formatCoins(betrag));
            return;
        }

        String err = BankManager.adminRemove(guildId, target.getId(), betrag, isBank);
        if (err != null) {
            event.replyEmbeds(embed("❌ Fehler", err)).setEphemeral(true).queue(); return;
        }
        String typLabel = isBank ? "Kontogeld" : "Bargeld";
        event.replyEmbeds(embed("✅ Geld entfernt",
            "**-" + BankManager.formatAmount(betrag) + "** " + typLabel
            + " wurden von **" + target.getEffectiveName() + "** abgezogen."))
            .setEphemeral(true).queue();
        BotLogger.tryDm(target.getUser(), EmbedFactory.build(
            "💸 Geld abgezogen",
            "**-" + BankManager.formatAmount(betrag) + "** " + typLabel
            + " wurden von einem Admin abgezogen."));
        BotLogger.logMoney(event.getGuild(), "💸 Geld entfernt",
            "**Admin:** " + event.getUser().getAsMention() + "\n" +
            "**Spieler:** " + target.getAsMention() + " (" + target.getEffectiveName() + ")\n" +
            "**Betrag:** -" + BankManager.formatAmount(betrag) + " (" + typLabel + ")");
    }

    private void handleLobbyAbstimmung(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String uhrzeit = event.getOption("uhrzeit", OptionMapping::getAsString);
        if (uhrzeit == null) return;

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.LOBBY_ABSTIMMUNG_CHANNEL_ID);
        if (ch == null) {
            event.replyEmbeds(embed("Fehler", "Lobby-Abstimmungs-Kanal nicht gefunden."))
                .setEphemeral(true).queue();
            return;
        }

        event.deferReply(true).queue();

        final String finalUhrzeit = uhrzeit;
        ch.sendMessage("<@&" + LoggingConfig.LOBBY_ABSTIMMUNG_ROLE_ID + ">")
            .setEmbeds(LobbyManager.buildInitialEmbed(finalUhrzeit))
            .queue(msg -> {
                LobbyManager.storeUhrzeit(msg.getId(), finalUhrzeit);

                msg.addReaction(Emoji.fromUnicode(LobbyManager.E_JA)).queue();
                msg.addReaction(Emoji.fromUnicode(LobbyManager.E_SPAETER)).queue();
                msg.addReaction(Emoji.fromUnicode(LobbyManager.E_MAYBE)).queue();
                msg.addReaction(Emoji.fromUnicode(LobbyManager.E_NEIN)).queue();

                event.getHook().sendMessageEmbeds(embed("✅ Lobby-Abstimmung gesendet",
                    "Die Abstimmung für **" + finalUhrzeit + "** wurde gepostet."))
                    .setEphemeral(true).queue();
            }, err -> {
                log.error("[LobbyAbstimmung] Fehler beim Senden.", err);
                event.getHook().sendMessageEmbeds(embed("Fehler",
                    "Die Abstimmung konnte nicht erstellt werden."))
                    .setEphemeral(true).queue();
            });
    }

    private void handleLobbyOeffnen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String host = event.getOption("lobbyhost", OptionMapping::getAsString);
        if (host == null) return;

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.LOBBY_OEFFNEN_CHANNEL_ID);
        if (ch == null) {
            event.replyEmbeds(embed("Fehler", "Lobby-Öffnen-Kanal nicht gefunden."))
                .setEphemeral(true).queue();
            return;
        }

        net.dv8tion.jda.api.entities.MessageEmbed lobbyEmbed = EmbedFactory.create()
            .setDescription(
                "────── ⋆⋅☆⋅⋆ ──────\n\n" +
                "🎉 **LOBBY GEÖFFNET** 🎉\n\n" +
                "👤 **LOBBY HOST** 👤\n" +
                host + "\n\n" +
                "Wir wünschen euch viel Spaß im RP\n\n" +
                "Solltest du noch nicht in der Crew sein öffne hier ein Support Ticket " +
                "<#1529636489732952264> und stelle eine Crew Anfrage")
            .build();

        event.deferReply(true).queue();
        LohnManager.onLobbyOpen(event.getGuild());
        ch.sendMessage("<@&" + LoggingConfig.LOBBY_ABSTIMMUNG_ROLE_ID + ">")
            .setEmbeds(lobbyEmbed)
            .queue(msg -> event.getHook().sendMessageEmbeds(
                embed("✅ Lobby geöffnet", "Die Nachricht wurde in <#" + LoggingConfig.LOBBY_OEFFNEN_CHANNEL_ID + "> gepostet."))
                .setEphemeral(true).queue(),
                err -> {
                    log.error("[LobbyOeffnen] Fehler beim Senden.", err);
                    event.getHook().sendMessageEmbeds(embed("Fehler", "Die Nachricht konnte nicht gesendet werden."))
                        .setEphemeral(true).queue();
                });
    }

    private void handleLobbySchliessen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.LOBBY_OEFFNEN_CHANNEL_ID);
        if (ch == null) {
            event.replyEmbeds(embed("Fehler", "Lobby-Kanal nicht gefunden."))
                .setEphemeral(true).queue();
            return;
        }

        net.dv8tion.jda.api.entities.MessageEmbed lobbyEmbed = EmbedFactory.create()
            .setDescription(
                "────── ⋆⋅☆⋅⋆ ──────\n\n" +
                "❌ **LOBBY GESCHLOSSEN** ❌\n\n" +
                "Die RP Lobby hat jetzt geschlossen, wir bedanken uns bei euch fürs Mitspielen.\n\n" +
                "Wenn ihr Vorschläge habt schickt diese gerne in den Kanal <#1529636537292161185>\n\n" +
                "Solltet ihr heute Probleme haben oder möchtet eine Beschwerde abgeben, " +
                "öffnet gerne jederzeit hier ein Ticket <#1529636489732952264>")
            .build();

        event.deferReply(true).queue();
        LohnManager.onLobbyClose(event.getGuild());
        ch.sendMessage("<@&" + LoggingConfig.LOBBY_ABSTIMMUNG_ROLE_ID + ">")
            .setEmbeds(lobbyEmbed)
            .queue(msg -> event.getHook().sendMessageEmbeds(
                embed("✅ Lobby geschlossen", "Die Nachricht wurde in <#" + LoggingConfig.LOBBY_OEFFNEN_CHANNEL_ID + "> gepostet."))
                .setEphemeral(true).queue(),
                err -> {
                    log.error("[LobbySchliessen] Fehler beim Senden.", err);
                    event.getHook().sendMessageEmbeds(embed("Fehler", "Die Nachricht konnte nicht gesendet werden."))
                        .setEphemeral(true).queue();
                });
    }

    private void handleVorschlag(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        // Nur im Vorschlag-Kanal erlaubt
        if (event.getChannel().getIdLong() != LoggingConfig.VORSCHLAG_CHANNEL_ID) {
            event.replyEmbeds(embed("Falscher Kanal",
                "Dieser Befehl kann nur in <#" + LoggingConfig.VORSCHLAG_CHANNEL_ID + "> verwendet werden."))
                .setEphemeral(true).queue();
            return;
        }

        String titel       = event.getOption("titel",        OptionMapping::getAsString);
        String beschreibung = event.getOption("beschreibung", OptionMapping::getAsString);
        if (titel == null || beschreibung == null) return;

        String guildId = event.getGuild().getId();
        VorschlagManager.Vorschlag v = new VorschlagManager.Vorschlag(
            UUID.randomUUID().toString(), titel, beschreibung);

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.VORSCHLAG_CHANNEL_ID);
        if (ch == null) return;

        event.deferReply(true).queue();

        ch.sendMessage("<@&" + LoggingConfig.ABSTIMMUNG_ROLE_ID + ">")
            .setEmbeds(VorschlagManager.buildVorschlagEmbed(v))
            .queue(msg -> {
                v.messageId = msg.getId();
                VorschlagManager.add(guildId, v);

                msg.addReaction(Emoji.fromUnicode(VorschlagManager.EMOJI_UP)).queue();
                msg.addReaction(Emoji.fromUnicode(VorschlagManager.EMOJI_DOWN)).queue();

                event.getHook().sendMessageEmbeds(embed("✅ Vorschlag gesendet",
                    "Dein Vorschlag **" + titel + "** wurde in <#" +
                    LoggingConfig.VORSCHLAG_CHANNEL_ID + "> gepostet."))
                    .setEphemeral(true).queue();
            }, err -> {
                log.error("[Vorschlag] Konnte nicht gesendet werden.", err);
                event.getHook().sendMessageEmbeds(embed("Fehler",
                    "Der Vorschlag konnte nicht erstellt werden."))
                    .setEphemeral(true).queue();
            });
    }

    private void handleVorschlagAnnehmen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String messageId = event.getOption("vorschlag", OptionMapping::getAsString);
        if (messageId == null) return;
        String guildId = event.getGuild().getId();

        VorschlagManager.Vorschlag v = VorschlagManager.getByMessageId(guildId, messageId);
        if (v == null || !"active".equals(v.status)) {
            event.replyEmbeds(embed("Nicht gefunden",
                "Kein aktiver Vorschlag mit dieser ID gefunden."))
                .setEphemeral(true).queue();
            return;
        }

        v.status = "angenommen";
        VorschlagManager.update(guildId, v);

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.VORSCHLAG_CHANNEL_ID);
        if (ch != null) {
            ch.editMessageEmbedsById(messageId, VorschlagManager.buildVorschlagEmbed(v))
                .queue(null, e -> {});
        }

        event.replyEmbeds(embed("✅ Vorschlag angenommen",
            "**" + v.title + "** wurde als angenommen markiert."))
            .setEphemeral(true).queue();
    }

    private void handleVorschlagAblehnen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        String messageId = event.getOption("vorschlag", OptionMapping::getAsString);
        if (messageId == null) return;
        String guildId = event.getGuild().getId();

        VorschlagManager.Vorschlag v = VorschlagManager.getByMessageId(guildId, messageId);
        if (v == null || !"active".equals(v.status)) {
            event.replyEmbeds(embed("Nicht gefunden",
                "Kein aktiver Vorschlag mit dieser ID gefunden."))
                .setEphemeral(true).queue();
            return;
        }

        v.status = "abgelehnt";
        VorschlagManager.update(guildId, v);

        TextChannel ch = event.getGuild().getTextChannelById(LoggingConfig.VORSCHLAG_CHANNEL_ID);
        if (ch != null) {
            ch.editMessageEmbedsById(messageId, VorschlagManager.buildVorschlagEmbed(v))
                .queue(null, e -> {});
        }

        event.replyEmbeds(embed("❌ Vorschlag abgelehnt",
            "**" + v.title + "** wurde als abgelehnt markiert."))
            .setEphemeral(true).queue();
    }

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
    //  /bannen-dashboard
    // ════════════════════════════════════════════════════════════

    private void handleBannenDashboard(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden.")).setEphemeral(true).queue(); return;
        }
        String guildId = event.getGuild().getId();
        String userId  = target.getId();
        de.pcrp.bot.common.DataStore.writeString("web-ban-" + guildId + "-" + userId, "1");
        BotLogger.logModeration(event.getGuild(),
            "🌐 Web-Bann",
            "**Mitglied:** " + target.getAsMention() + " (`" + userId + "`)\n" +
            "**Gebannt von:** " + event.getUser().getAsMention() + "\n" +
            "**Effekt:** Alle PCRP-Webseiten gesperrt");
        event.replyEmbeds(embed("✅ Web-Bann gesetzt",
            "**" + target.getEffectiveName() + "** hat keinen Zugriff mehr auf PCRP-Webseiten."))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  /entbannen-dashboard
    // ════════════════════════════════════════════════════════════

    private void handleEntbannenDashboard(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden.")).setEphemeral(true).queue(); return;
        }
        String guildId = event.getGuild().getId();
        de.pcrp.bot.common.DataStore.deleteKey("web-ban-" + guildId + "-" + target.getId());
        event.replyEmbeds(embed("✅ Web-Bann aufgehoben",
            "**" + target.getEffectiveName() + "** hat wieder Zugriff auf PCRP-Webseiten."))
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

    // ── /handy-reset entfernt (war destruktiver Admin-Command) ──────────────

    // ════════════════════════════════════════════════════════════
    //  /charakter-zurücksetzen — Inventory + Bargeld + Kontostand auf 0
    // ════════════════════════════════════════════════════════════

    private void handleCharakterZuruecksetzen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden."))
                .setEphemeral(true).queue();
            return;
        }
        if (target.getUser().isBot()) {
            event.replyEmbeds(embed("Fehler", "Bots können nicht zurückgesetzt werden."))
                .setEphemeral(true).queue();
            return;
        }

        String guildId = event.getGuild().getId();
        String userId  = target.getId();

        // 1) Vorzustand für Audit-Log einfangen
        long preBank  = BankManager.getBalance(guildId, userId);
        long preCash  = BargeldManager.get(guildId, userId);
        int preItemsCount = InventoryManager.getInventory(guildId, userId).stream()
            .mapToInt(i -> i.quantity).sum();

        // 2) Zurücksetzen: Inventar leeren, Bargeld + Kontostand auf 0
        InventoryManager.clearInventory(guildId, userId);
        BargeldManager.set(guildId, userId, 0L);
        BankManager.setBalance(guildId, userId, 0L);

        // 3) Bestätigung an den Admin (ephemeral)
        StringBuilder sb = new StringBuilder();
        sb.append("**").append(target.getUser().getName()).append("** wurde zurückgesetzt:\n\n");
        sb.append("💳 **Kontostand:** ").append(BankManager.formatAmount(preBank)).append(" → **0$**\n");
        sb.append("💵 **Bargeld:** ").append(BargeldManager.format(preCash)).append(" → **0$**\n");
        sb.append("📦 **Inventar:** ").append(preItemsCount).append(" Items entfernt\n\n");
        sb.append("_Ausweis + Führerschein + Rollen + Handy-Vertrag bleiben erhalten._");
        event.replyEmbeds(embed("🔄 Charakter zurückgesetzt", sb.toString()))
            .setEphemeral(true).queue();

        // 4) DM an betroffenen Spieler
        BotLogger.tryDm(target.getUser(), EmbedFactory.build("🔄 Charakter zurückgesetzt",
            "Dein Charakter wurde von einem Teammitglied zurückgesetzt:\n\n" +
            "💳 **Kontostand:** " + BankManager.formatAmount(preBank) + " → 0$\n" +
            "💵 **Bargeld:** " + BargeldManager.format(preCash) + " → 0$\n" +
            "📦 **Inventar:** " + preItemsCount + " Items entfernt\n\n" +
            "_Ausweis + Führerschein + Rollen + Handy-Vertrag bleiben erhalten._"));

        // 5) Audit-Log in den Item-Log-Channel
        BotLogger.logItem(event.getGuild(), "🔄 Charakter-Reset",
            "**Mitglied:** " + target.getAsMention() + "\n" +
            "**Bank:** " + BankManager.formatAmount(preBank) + " → 0$\n" +
            "**Bargeld:** " + BargeldManager.format(preCash) + " → 0$\n" +
            "**Items entfernt:** " + preItemsCount + "\n" +
            "**Von:** " + event.getUser().getAsMention());

        log.info("[Charakter-Reset] {} reset {} (Bank {}→0, Bargeld {}→0, {} Items entfernt)",
            event.getUser().getAsTag(), target.getUser().getAsTag(), preBank, preCash, preItemsCount);
    }

    // ════════════════════════════════════════════════════════════
    //  /teamverwarnung  +  /teamverwarnung-entfernen  +  /teamverwarnung-liste
    // ════════════════════════════════════════════════════════════

    private void handleTeamverwarnung(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (event.getChannel().getIdLong() != LoggingConfig.TEAM_WARN_CHANNEL_ID) {
            event.reply("Dieser command funktioniert nur in <#" + LoggingConfig.TEAM_WARN_CHANNEL_ID + ">")
                .setEphemeral(true).queue();
            return;
        }

        Member target     = event.getOption("mitglied", OptionMapping::getAsMember);
        String grund      = event.getOption("grund",      OptionMapping::getAsString);
        String konsequenz = event.getOption("konsequenz", OptionMapping::getAsString);

        if (target == null || grund == null || konsequenz == null) {
            event.replyEmbeds(embed("Fehler", "Alle Felder sind erforderlich.")).setEphemeral(true).queue();
            return;
        }
        if (target.getUser().isBot()) {
            event.replyEmbeds(embed("Fehler", "Bots können keine Team-Verwarnung erhalten.")).setEphemeral(true).queue();
            return;
        }

        long guildId = event.getGuild().getIdLong();
        long userId  = target.getIdLong();

        // Ziel muss Teammitglied-Rolle besitzen.
        boolean targetIsMitglied = target.getRoles().stream()
            .anyMatch(r -> r.getIdLong() == RoleConfig.TEAMMITGLIED_ROLE_ID);
        if (!targetIsMitglied) {
            event.replyEmbeds(embed("Fehler",
                target.getAsMention() + " ist **kein Teammitglied** und kann keine Team-Verwarnung erhalten."))
                .setEphemeral(true).queue();
            return;
        }

        List<WarnStore.WarnEntry> existing = TeamWarnStore.getWarns(guildId, userId);
        if (existing.size() >= 3) {
            event.replyEmbeds(embed("Maximum erreicht",
                target.getAsMention() + " hat bereits **3 Team-Verwarnungen** und kann keine weiteren erhalten."))
                .setEphemeral(true).queue();
            return;
        }

        event.deferReply(true).queue();

        WarnStore.WarnEntry warn = new WarnStore.WarnEntry(
            grund, konsequenz,
            event.getUser().getId(), event.getUser().getName());
        int total = TeamWarnStore.addWarn(guildId, userId, warn);

        // Log-Embed in den Team-Warn-Kanal (Rot — ausnahmsweise, da Team-Warns
        // keine Auto-Timeouts auslösen, aber visuell als schwerwiegend markiert sind).
        TextChannel warnCh = event.getGuild().getTextChannelById(LoggingConfig.TEAM_WARN_CHANNEL_ID);
        if (warnCh != null) {
            warnCh.sendMessageEmbeds(new EmbedBuilder()
                .setColor(Color.RED)
                .setTitle("🛡️ Team-Verwarnung — " + target.getUser().getName())
                .setDescription(
                    "**Verwarnung " + total + "/3**\n\n" +
                    "**Mitglied:** " + target.getAsMention() + "\n" +
                    "**Grund:** " + grund + "\n" +
                    "**Konsequenz:** " + konsequenz + "\n" +
                    "**Ausgesprochen von:** " + event.getUser().getAsMention())
                .build()).queue();
        }

        event.getHook().sendMessageEmbeds(embed("✅ Team-Verwarnung erteilt",
            target.getAsMention() + " hat jetzt **" + total + "/3** Team-Verwarnungen."))
            .setEphemeral(true).queue();
    }

    private void handleTeamverwarnungEntfernen(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (event.getChannel().getIdLong() != LoggingConfig.TEAM_WARN_CHANNEL_ID) {
            event.reply("Dieser command funktioniert nur in <#" + LoggingConfig.TEAM_WARN_CHANNEL_ID + ">")
                .setEphemeral(true).queue();
            return;
        }

        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        String warnId = event.getOption("warn-id",   OptionMapping::getAsString);

        if (target == null || warnId == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied oder Team-Verwarnungs-ID nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        long guildId = event.getGuild().getIdLong();
        long userId  = target.getIdLong();

        boolean removed = TeamWarnStore.removeWarn(guildId, userId, warnId);
        if (!removed) {
            event.replyEmbeds(embed("Nicht gefunden",
                "Team-Verwarnung mit dieser ID wurde nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        List<WarnStore.WarnEntry> remaining = TeamWarnStore.getWarns(guildId, userId);

        event.replyEmbeds(embed("✅ Team-Verwarnung entfernt",
            "Eine Team-Verwarnung von " + target.getAsMention() + " wurde gelöscht.\n" +
            "Aktuelle Team-Verwarnungen: **" + remaining.size() + "/3**"))
            .setEphemeral(true).queue();
    }

    private void handleTeamverwarnungListe(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (event.getChannel().getIdLong() != LoggingConfig.TEAM_WARN_CHANNEL_ID) {
            event.reply("Dieser command funktioniert nur in <#" + LoggingConfig.TEAM_WARN_CHANNEL_ID + ">")
                .setEphemeral(true).queue();
            return;
        }

        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        List<WarnStore.WarnEntry> warns = TeamWarnStore.getWarns(
            event.getGuild().getIdLong(), target.getIdLong());

        if (warns.isEmpty()) {
            event.replyEmbeds(embed("Keine Team-Verwarnungen",
                target.getAsMention() + " hat keine Team-Verwarnungen."))
                .setEphemeral(true).queue();
            return;
        }

        StringBuilder sb = new StringBuilder();
        sb.append("**").append(target.getUser().getName())
          .append("** — ").append(warns.size()).append("/3 Team-Verwarnungen\n\n");
        sb.append("━━━━━━━━━━━━━━━━━━━━━━\n\n");

        for (int i = 0; i < warns.size(); i++) {
            WarnStore.WarnEntry w = warns.get(i);
            sb.append("**").append(i + 1).append(". Team-Verwarnung** (").append(w.dateString()).append(")\n");
            sb.append("📝 **Grund:** ").append(w.reason).append("\n");
            sb.append("⚖️ **Konsequenz:** ").append(w.consequence).append("\n");
            sb.append("👮 **Von:** <@").append(w.byId).append(">\n");
            sb.append("`ID: ").append(w.id, 0, 8).append("…`\n");
            if (i < warns.size() - 1) sb.append("\n");
        }

        event.replyEmbeds(buildWarnListEmbed("🛡️ **Team-Verwarnungen — " + target.getUser().getName() + "**\n\n" + sb.toString()))
            .setEphemeral(true).queue();
    }

    // ════════════════════════════════════════════════════════════
    //  Autocomplete für /teamverwarnung-entfernen  (Warn-ID-Picker)
    // ════════════════════════════════════════════════════════════

    private void handleTeamverwarnungEntfernenAutocomplete(CommandAutoCompleteInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (event.getChannel().getIdLong() != LoggingConfig.TEAM_WARN_CHANNEL_ID) {
            event.replyChoices(List.of()).queue();   // Falscher Kanal → keine Vorschläge leaken
            return;
        }
        OptionMapping memberOpt = event.getOption("mitglied");
        if (memberOpt == null) { event.replyChoices().queue(null, e -> {}); return; }

        long userId;
        try { userId = Long.parseLong(memberOpt.getAsString()); }
        catch (NumberFormatException e) { event.replyChoices().queue(null, ex -> {}); return; }

        List<WarnStore.WarnEntry> warns = TeamWarnStore.getWarns(event.getGuild().getIdLong(), userId);
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

    // ════════════════════════════════════════════════════════════
    //  /spieler-info  – IC-Daten + Kontostand + Bargeld + Inventar
    // ════════════════════════════════════════════════════════════

    private void handleSpielerInfo(SlashCommandInteractionEvent event) {
        if (event.getGuild() == null) return;

        Member target = event.getOption("mitglied", OptionMapping::getAsMember);
        if (target == null) {
            event.replyEmbeds(embed("Fehler", "Mitglied nicht gefunden.")).setEphemeral(true).queue();
            return;
        }

        long guildId     = event.getGuild().getIdLong();
        String gIdStr    = event.getGuild().getId();
        long userId      = target.getIdLong();
        String userIdStr = target.getId();

        event.deferReply(true).queue();

        // 1) IC-Charakter-Daten
        StringBuilder charLines = new StringBuilder();
        JsonObject charData = CharacterStore.get(guildId, userId);
        if (charData == null) {
            charLines.append("**⚠️ Illegal Eingereist** — Kein gültiger Ausweis vorhanden");
        } else {
            String typeRaw = CharacterStore.str(charData, "type");
            String typePretty = "legal".equalsIgnoreCase(typeRaw)   ? "📗 Legal"
                              : "illegal".equalsIgnoreCase(typeRaw) ? "📕 Illegal"
                              : typeRaw;
            charLines.append("**Charakter-Typ:** ").append(typePretty).append("\n");
            charLines.append("**Vorname:** ").append(CharacterStore.str(charData, "firstName")).append("\n");
            charLines.append("**Nachname:** ").append(CharacterStore.str(charData, "lastName")).append("\n");
            String birth = CharacterStore.str(charData, "birthDate");
            if (!"-".equals(birth)) charLines.append("**Geburtsdatum:** ").append(birth).append("\n");
            String birthPlace = CharacterStore.str(charData, "birthPlace");
            if (!"-".equals(birthPlace)) charLines.append("**Geburtsort:** ").append(birthPlace).append("\n");
            String nat = CharacterStore.str(charData, "nationality");
            if (!"-".equals(nat)) charLines.append("**Nationalität:** ").append(nat).append("\n");
            String residence = CharacterStore.str(charData, "residence");
            if (!"-".equals(residence)) charLines.append("**Wohnsitz:** ").append(residence).append("\n");
            String regAt = CharacterStore.str(charData, "registeredAt");
            if (!"-".equals(regAt)) charLines.append("**Registriert seit:** ").append(regAt);
        }

        // 2) Geld: Kontostand + Bargeld
        long bank = BankManager.getBalance(gIdStr, userIdStr);
        long cash = BargeldManager.get(gIdStr, userIdStr);
        String moneyBlock = "💳 **Kontostand:** " + BankManager.formatAmount(bank)
                          + "\n💵 **Bargeld:** "   + BankManager.formatAmount(cash);

        // 3) Sichtbare Inventar-Items (Top 25, +Zähler)
        List<InventoryManager.Item> items = InventoryManager.getVisibleItems(gIdStr, userIdStr);
        StringBuilder invBlock = new StringBuilder();
        if (items == null || items.isEmpty()) {
            invBlock.append("— Inventar ist leer —");
        } else {
            int shown = 0;
            for (InventoryManager.Item it : items) {
                if (shown >= 25) {
                    invBlock.append("_… +").append(items.size() - shown).append(" weitere_");
                    break;
                }
                invBlock.append("• ").append(it.name).append(" ×").append(it.quantity).append("\n");
                shown++;
            }
        }

        event.getHook().sendMessageEmbeds(new EmbedBuilder()
                .setColor(new Color(0xCC5500))
                .setTitle("📋 Spieler-Info — " + target.getUser().getName())
                .setDescription(
                    "**__🧑 IC-Charakter__**\n" + charLines + "\n\n" +
                    "**__💰 Geld__**\n" + moneyBlock + "\n\n" +
                    "**__📦 Inventar (sichtbar)__**\n" + invBlock)
                .build())
            .queue();
    }
}
