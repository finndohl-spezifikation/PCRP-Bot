package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.Permission;
import net.dv8tion.jda.api.entities.*;
import net.dv8tion.jda.api.entities.channel.concrete.Category;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.*;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.EntitySelectMenu;
import net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu;
import net.dv8tion.jda.api.interactions.components.text.TextInput;
import net.dv8tion.jda.api.interactions.components.text.TextInputStyle;
import net.dv8tion.jda.api.interactions.modals.Modal;
import net.dv8tion.jda.api.requests.restaction.ChannelAction;
import net.dv8tion.jda.api.utils.FileUpload;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class TicketListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(TicketListener.class);

    // ── Kategorie-IDs ──────────────────────────────────────────────────────────
    private static final long SUPPORT_CATEGORY_ID  = 1529636378059472948L;
    private static final long HIGHTEAM_CATEGORY_ID = 1529636379062046740L;
    private static final long FRAKTION_CATEGORY_ID = 1529636379451986053L;

    // ── Kanal-IDs ──────────────────────────────────────────────────────────────
    private static final long TRANSCRIPT_CHANNEL_ID = 1529636431784317019L;
    private static final long RATING_CHANNEL_ID     = 1529636514294923284L;

    // ── Rollen-IDs ─────────────────────────────────────────────────────────────
    private static final long SUPPORT_ROLE_ID  = 1529636282148458538L;
    private static final long HIGHTEAM_ROLE_ID = 1529636280365748345L;
    private static final long FRAKTION_ROLE_ID = 1529636285159837807L;

    // ── Komponenten-IDs ────────────────────────────────────────────────────────
    public  static final String SELECT_ID  = "ticket-select";   // Panel-Auswahlmenü
    public  static final String ACTION_SEL = "ticket-action";   // Aktionsmenü im Ticket
    private static final String ASSIGN_SEL = "ticket-assign-sel";

    // ──────────────────────────────────────────────────────────────────────────
    // Panel-Auswahlmenü: Ticket-Typ wählen
    // ──────────────────────────────────────────────────────────────────────────

    @Override
    public void onStringSelectInteraction(StringSelectInteractionEvent event) {
        String cid = event.getComponentId();

        if (cid.equals(ACTION_SEL)) { handleTicketAction(event); return; }
        if (cid.startsWith("rate-sel-")) { handleRatingSelect(event); return; }
        if (!cid.equals(SELECT_ID)) return;

        String value  = event.getValues().get(0);
        Guild  guild  = event.getGuild();
        Member member = event.getMember();
        if (guild == null || member == null) return;

        if ("team-bewerbung".equals(value)) {
            event.reply("🔜 **Team Bewerbungen** sind demnächst verfügbar.").setEphemeral(true).queue();
            return;
        }

        // Max 1 offenes Ticket
        String openKey    = "ticket-open-" + guild.getId() + "-" + member.getId();
        String existingId = DataStore.readString(openKey);
        if (existingId != null && !existingId.isBlank()) {
            TextChannel existing = guild.getTextChannelById(existingId.trim());
            if (existing != null) {
                event.reply("❌ Du hast bereits ein offenes Ticket: " + existing.getAsMention()).setEphemeral(true).queue();
                return;
            }
            DataStore.deleteKey(openKey);
        }

        long   categoryId;
        long   roleId;
        String typeLabel;
        switch (value) {
            case "support":
                categoryId = SUPPORT_CATEGORY_ID;  roleId = SUPPORT_ROLE_ID;  typeLabel = "Support";             break;
            case "beschwerde":
                categoryId = SUPPORT_CATEGORY_ID;  roleId = SUPPORT_ROLE_ID;  typeLabel = "Beschwerde";          break;
            case "highteam":
                categoryId = HIGHTEAM_CATEGORY_ID; roleId = HIGHTEAM_ROLE_ID; typeLabel = "Highteam";            break;
            case "fraktion":
                categoryId = FRAKTION_CATEGORY_ID; roleId = FRAKTION_ROLE_ID; typeLabel = "Fraktions Bewerbung"; break;
            default:
                event.reply("❌ Unbekannte Kategorie.").setEphemeral(true).queue();
                return;
        }

        event.deferReply(true).queue();

        String counterKey = "ticket-counter-" + guild.getId();
        String cs         = DataStore.readString(counterKey);
        int    num        = (cs != null && !cs.isBlank()) ? Integer.parseInt(cs.trim()) + 1 : 1;
        DataStore.writeString(counterKey, String.valueOf(num));

        String   ticketName = "ticket-" + String.format("%04d", num);
        Category cat        = guild.getCategoryById(categoryId);
        Role     teamRole   = guild.getRoleById(roleId);

        ChannelAction<TextChannel> action = guild.createTextChannel(ticketName);
        if (cat != null) action = action.setParent(cat);

        action = action
            .addPermissionOverride(guild.getPublicRole(), null, EnumSet.of(Permission.VIEW_CHANNEL))
            .addPermissionOverride(member,
                EnumSet.of(Permission.VIEW_CHANNEL, Permission.MESSAGE_SEND,
                           Permission.MESSAGE_HISTORY, Permission.MESSAGE_ATTACH_FILES), null);

        if (teamRole != null)
            action = action.addPermissionOverride(teamRole,
                EnumSet.of(Permission.VIEW_CHANNEL, Permission.MESSAGE_SEND,
                           Permission.MESSAGE_HISTORY, Permission.MANAGE_CHANNEL), null);

        if (roleId != HIGHTEAM_ROLE_ID) {
            Role htRole = guild.getRoleById(HIGHTEAM_ROLE_ID);
            if (htRole != null)
                action = action.addPermissionOverride(htRole,
                    EnumSet.of(Permission.VIEW_CHANNEL, Permission.MESSAGE_SEND,
                               Permission.MESSAGE_HISTORY, Permission.MANAGE_CHANNEL), null);
        }

        final long   fRoleId    = roleId;
        final String fTypeLabel = typeLabel;
        final String fOpenKey   = openKey;
        final int    fNum       = num;

        action.queue(ch -> {
            DataStore.writeString(fOpenKey, ch.getId());
            // Format: creatorId|roleId|typeLabel|claimedBy|assignedUsers
            DataStore.writeString("ticket-data-" + guild.getId() + "-" + ch.getId(),
                member.getId() + "|" + fRoleId + "|" + fTypeLabel + "||");

            // Rolle dauerhaft pingen (kein Auto-Delete)
            if (teamRole != null) ch.sendMessage(teamRole.getAsMention()).queue();

            // Embed + Aktionsmenü
            ch.sendMessageEmbeds(buildTicketEmbed(fNum, fTypeLabel, member.getId(), ""))
                .addActionRow(buildActionMenu())
                .queue();

            event.getHook().sendMessage("✅ Dein Ticket wurde erstellt: " + ch.getAsMention()).queue();
            log.info("[Ticket] #{} ({}) erstellt von {}.", fNum, fTypeLabel, member.getUser().getName());

        }, err -> {
            log.error("[Ticket] Kanal konnte nicht erstellt werden.", err);
            event.getHook().sendMessage("❌ Fehler beim Erstellen des Tickets.").queue();
        });
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Aktionsmenü im Ticket (Claimen / Zuweisen / Schließen)
    // ──────────────────────────────────────────────────────────────────────────

    private void handleTicketAction(StringSelectInteractionEvent event) {
        Guild  guild  = event.getGuild();
        Member member = event.getMember();
        if (guild == null || member == null) return;

        switch (event.getValues().get(0)) {
            case "claim":  handleClaim(event, guild, member);  break;
            case "assign": handleAssign(event, guild, member); break;
            case "close":  handleClose(event, guild, member);  break;
        }
    }

    // ─── Claim ───────────────────────────────────────────────────────────────

    private void handleClaim(StringSelectInteractionEvent event, Guild guild, Member member) {
        TextChannel ch    = (TextChannel) event.getChannel();
        String      dKey  = "ticket-data-" + guild.getId() + "-" + ch.getId();
        String[]    parts = loadData(dKey);
        if (parts == null) { event.reply("❌ Ticket-Daten nicht gefunden.").setEphemeral(true).queue(); return; }

        if (!hasTeamPerm(member, Long.parseLong(parts[1]))) {
            event.reply("❌ Nur Teammitglieder können das Ticket claimen.").setEphemeral(true).queue();
            return;
        }
        if (!parts[3].isBlank()) {
            event.reply("ℹ️ Das Ticket wurde bereits von <@" + parts[3] + "> geclaimit.").setEphemeral(true).queue();
            return;
        }

        parts[3] = member.getId();
        DataStore.writeString(dKey, String.join("|", parts));

        int ticketNum = parseTicketNum(event.getMessage().getEmbeds().isEmpty()
            ? "" : event.getMessage().getEmbeds().get(0).getTitle());

        event.getMessage().editMessageEmbeds(
            buildTicketEmbed(ticketNum, parts[2], parts[0], member.getId())
        ).queue();

        event.reply("✅ " + member.getAsMention() + " hat das Ticket übernommen.").queue();
    }

    // ─── Assign ──────────────────────────────────────────────────────────────

    private void handleAssign(StringSelectInteractionEvent event, Guild guild, Member member) {
        TextChannel ch    = (TextChannel) event.getChannel();
        String[]    parts = loadData("ticket-data-" + guild.getId() + "-" + ch.getId());
        if (parts == null) { event.reply("❌ Ticket-Daten nicht gefunden.").setEphemeral(true).queue(); return; }

        if (!hasTeamPerm(member, Long.parseLong(parts[1]))) {
            event.reply("❌ Nur Teammitglieder können Personen zuweisen.").setEphemeral(true).queue();
            return;
        }

        EntitySelectMenu menu = EntitySelectMenu
            .create(ASSIGN_SEL, EntitySelectMenu.SelectTarget.USER)
            .setPlaceholder("Mitglied auswählen…")
            .setRequiredRange(1, 1)
            .build();

        event.reply("👤 Wähle ein Mitglied aus, das dem Ticket zugewiesen werden soll:")
            .addActionRow(menu)
            .setEphemeral(true)
            .queue();
    }

    // ─── Assign-Select (Entity-Picker) ───────────────────────────────────────

    @Override
    public void onEntitySelectInteraction(EntitySelectInteractionEvent event) {
        if (!event.getComponentId().equals(ASSIGN_SEL)) return;

        Guild  guild  = event.getGuild();
        Member member = event.getMember();
        if (guild == null || member == null) return;

        TextChannel ch    = (TextChannel) event.getChannel();
        String      dKey  = "ticket-data-" + guild.getId() + "-" + ch.getId();
        String[]    parts = loadData(dKey);
        if (parts == null) { event.reply("❌ Ticket-Daten nicht gefunden.").setEphemeral(true).queue(); return; }

        List<Member> selected = event.getMentions().getMembers();
        if (selected.isEmpty()) { event.reply("❌ Kein gültiges Mitglied ausgewählt.").setEphemeral(true).queue(); return; }

        Member target = selected.get(0);

        ch.getPermissionContainer().upsertPermissionOverride(target)
            .grant(Permission.VIEW_CHANNEL, Permission.MESSAGE_SEND, Permission.MESSAGE_HISTORY)
            .queue();

        parts[4] = parts[4].isBlank() ? target.getId() : parts[4] + "," + target.getId();
        DataStore.writeString(dKey, String.join("|", parts));

        event.reply("✅ " + target.getAsMention() + " wurde dem Ticket zugewiesen.").queue();
        ch.sendMessage("👤 **" + target.getEffectiveName() + "** wurde von "
            + member.getAsMention() + " diesem Ticket zugewiesen.").queue();
    }

    // ─── Close ───────────────────────────────────────────────────────────────

    private void handleClose(StringSelectInteractionEvent event, Guild guild, Member member) {
        TextChannel ch    = (TextChannel) event.getChannel();
        String      dKey  = "ticket-data-" + guild.getId() + "-" + ch.getId();
        String[]    parts = loadData(dKey);
        if (parts == null) { event.reply("❌ Ticket-Daten nicht gefunden.").setEphemeral(true).queue(); return; }

        String creatorId  = parts[0];
        long   roleId     = Long.parseLong(parts[1]);
        String typeLabel  = parts[2];
        String claimedBy  = parts[3];
        String ticketId   = ch.getId();
        String ticketName = ch.getName();

        if (!hasTeamPerm(member, roleId)) {
            event.reply("❌ Nur Teammitglieder können das Ticket schließen.").setEphemeral(true).queue();
            return;
        }

        event.deferReply().queue();

        ch.getIterableHistory().takeAsync(200).thenAccept(msgs -> {

            StringBuilder sb = new StringBuilder();
            sb.append("=== ").append(ticketName).append(" | ").append(typeLabel).append(" ===\n");
            sb.append("Erstellt von:    ").append(creatorId).append("\n");
            sb.append("Bearbeiter:      ").append(claimedBy.isBlank() ? "—" : claimedBy).append("\n");
            sb.append("Geschlossen von: ").append(member.getUser().getAsTag()).append("\n\n");

            DateTimeFormatter fmt = DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm");
            List<Message> ordered = new ArrayList<>(msgs);
            Collections.reverse(ordered);
            for (Message m : ordered) {
                sb.append("[").append(m.getTimeCreated().format(fmt)).append("] ")
                  .append(m.getAuthor().getName()).append(": ")
                  .append(m.getContentDisplay());
                if (!m.getAttachments().isEmpty())
                    sb.append(" [").append(m.getAttachments().size()).append(" Anhang/Anhänge]");
                sb.append("\n");
            }

            DataStore.deleteKey("ticket-open-" + guild.getId() + "-" + creatorId);
            DataStore.deleteKey(dKey);
            DataStore.writeString("ticket-rating-data-" + ticketId,
                creatorId + "|" + claimedBy + "|" + typeLabel + "|" + ticketName);

            TextChannel transcriptCh = guild.getTextChannelById(TRANSCRIPT_CHANNEL_ID);
            if (transcriptCh != null) {
                byte[]     bytes  = sb.toString().getBytes(StandardCharsets.UTF_8);
                FileUpload upload = FileUpload.fromData(new ByteArrayInputStream(bytes), ticketName + ".txt");
                transcriptCh.sendMessageEmbeds(EmbedFactory.create()
                    .setTitle("📋 Transkript — " + ticketName)
                    .setDescription(
                        "**Kategorie:** " + typeLabel + "\n" +
                        "**Erstellt von:** <@" + creatorId + ">\n" +
                        "**Bearbeiter:** " + (claimedBy.isBlank() ? "—" : "<@" + claimedBy + ">") + "\n" +
                        "**Geschlossen von:** " + member.getAsMention())
                    .build()
                ).addFiles(upload).queue();
            }

            ch.delete().reason("Ticket geschlossen von " + member.getUser().getName()).queue();

            guild.retrieveMemberById(creatorId).queue(creator -> {
                if (creator == null) return;
                creator.getUser().openPrivateChannel().queue(pm ->
                    pm.sendMessageEmbeds(EmbedFactory.create()
                        .setTitle("🎫 Dein Ticket wurde geschlossen")
                        .setDescription(
                            "Dein Ticket **" + ticketName + "** (" + typeLabel + ") wurde geschlossen.\n\n" +
                            "Wie war deine Erfahrung? Wähle eine Bewertung aus.\n" +
                            "Du kannst jedes Ticket nur **einmal** bewerten.")
                        .build())
                        .addActionRow(buildRatingMenu(ticketId, false))
                        .queue(null, e -> log.warn("[Ticket] DM an {} fehlgeschlagen.", creatorId))
                );
            }, e -> log.warn("[Ticket] Creator {} nicht abrufbar.", creatorId));

        }).exceptionally(e -> { log.error("[Ticket] Fehler beim Schließen.", e); return null; });
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Bewertungs-Auswahlmenü (DM) — rate-sel-{ticketId}
    // ──────────────────────────────────────────────────────────────────────────

    private void handleRatingSelect(StringSelectInteractionEvent event) {
        // ID-Format: rate-sel-{ticketId}
        String ticketId = event.getComponentId().substring("rate-sel-".length());
        String stars    = event.getValues().get(0);

        if (DataStore.readString("ticket-rated-" + ticketId) != null) {
            event.reply("❌ Du hast dieses Ticket bereits bewertet.").setEphemeral(true).queue();
            return;
        }

        Modal modal = Modal.create("ticket-rate-modal:" + ticketId + ":" + stars, "Ticket bewerten")
            .addComponents(ActionRow.of(
                TextInput.create("comment", "Optionaler Kommentar (kann leer bleiben)", TextInputStyle.PARAGRAPH)
                    .setPlaceholder("Dein Feedback…")
                    .setRequired(false)
                    .setMaxLength(500)
                    .build()))
            .build();

        event.replyModal(modal).queue();
    }

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        // kein Button mehr für Bewertungen
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Modal — Bewertung absenden
    // ──────────────────────────────────────────────────────────────────────────

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        String modalId = event.getModalId();
        if (!modalId.startsWith("ticket-rate-modal:")) return;

        String[] p      = modalId.split(":");
        if (p.length < 3) return;
        String ticketId = p[1];
        String stars    = p[2];

        String ratedKey = "ticket-rated-" + ticketId;
        if (DataStore.readString(ratedKey) != null) {
            event.reply("❌ Du hast dieses Ticket bereits bewertet.").setEphemeral(true).queue();
            return;
        }
        DataStore.writeString(ratedKey, "true");

        String comment = event.getValue("comment") != null
            ? event.getValue("comment").getAsString().trim() : "";

        String rdData    = DataStore.readString("ticket-rating-data-" + ticketId);
        String creatorId = "?", claimedBy = "", typeLabel = "?", channelName = "?";
        if (rdData != null) {
            String[] rd = rdData.split("\\|", -1);
            if (rd.length >= 4) { creatorId = rd[0]; claimedBy = rd[1]; typeLabel = rd[2]; channelName = rd[3]; }
        }

        int    starCount = Integer.parseInt(stars);
        String starStr   = "⭐".repeat(starCount) + "☆".repeat(5 - starCount);

        final String fCreator = creatorId, fClaimed = claimedBy,
                     fType = typeLabel, fChannel = channelName, fComment = comment;

        if (BotContext.getJda() != null) {
            for (Guild g : BotContext.getJda().getGuilds()) {
                TextChannel rCh = g.getTextChannelById(RATING_CHANNEL_ID);
                if (rCh == null) continue;
                StringBuilder desc = new StringBuilder()
                    .append("**Ticket:** ").append(fChannel).append("\n")
                    .append("**Kategorie:** ").append(fType).append("\n")
                    .append("**Erstellt von:** <@").append(fCreator).append(">\n")
                    .append("**Bearbeiter:** ").append(fClaimed.isBlank() ? "—" : "<@" + fClaimed + ">").append("\n")
                    .append("**Bewertung:** ").append(starStr);
                if (!fComment.isBlank()) desc.append("\n**Kommentar:** ").append(fComment);
                rCh.sendMessageEmbeds(EmbedFactory.create()
                    .setTitle("⭐ Ticket-Bewertung")
                    .setDescription(desc.toString())
                    .build()
                ).queue();
            }
        }

        event.reply("✅ Danke für deine Bewertung! (" + starStr + ")").setEphemeral(true).queue();

        if (event.getMessage() != null) {
            event.getMessage().editMessageComponents(
                ActionRow.of(buildRatingMenu(ticketId, true))
            ).queue(null, e -> {});
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Hilfsmethoden
    // ──────────────────────────────────────────────────────────────────────────

    /** Bewertungs-Auswahlmenü für die DM. disabled=true → nach Abgabe deaktiviert. */
    private static StringSelectMenu buildRatingMenu(String ticketId, boolean disabled) {
        StringSelectMenu.Builder b = StringSelectMenu.create("rate-sel-" + ticketId)
            .setPlaceholder("Bewertung auswählen…")
            .addOption("⭐ — Sehr schlecht",   "1", "1 von 5 Sternen")
            .addOption("⭐⭐ — Schlecht",       "2", "2 von 5 Sternen")
            .addOption("⭐⭐⭐ — Ok",           "3", "3 von 5 Sternen")
            .addOption("⭐⭐⭐⭐ — Gut",        "4", "4 von 5 Sternen")
            .addOption("⭐⭐⭐⭐⭐ — Sehr gut", "5", "5 von 5 Sternen");
        if (disabled) b.setDisabled(true);
        return b.build();
    }

    /** Aktionsmenü das im Ticket erscheint. */
    public static StringSelectMenu buildActionMenu() {
        return StringSelectMenu.create(ACTION_SEL)
            .setPlaceholder("Aktion auswählen…")
            .addOption("Ticket claimen",    "claim",  "Ticket zur Bearbeitung übernehmen",  net.dv8tion.jda.api.entities.emoji.Emoji.fromUnicode("🙋"))
            .addOption("Person zuweisen",   "assign", "Eine Person dem Ticket hinzufügen",  net.dv8tion.jda.api.entities.emoji.Emoji.fromUnicode("👤"))
            .addOption("Ticket schließen",  "close",  "Ticket schließen und Transkript senden", net.dv8tion.jda.api.entities.emoji.Emoji.fromUnicode("🔒"))
            .build();
    }

    private static String[] loadData(String key) {
        String raw = DataStore.readString(key);
        if (raw == null || raw.isBlank()) return null;
        String[] parts = raw.split("\\|", -1);
        if (parts.length < 5) {
            String[] padded = new String[]{"", "", "", "", ""};
            System.arraycopy(parts, 0, padded, 0, parts.length);
            return padded;
        }
        return parts;
    }

    private boolean hasTeamPerm(Member member, long roleId) {
        if (member.hasPermission(Permission.ADMINISTRATOR)) return true;
        for (Role r : member.getRoles()) {
            long rid = r.getIdLong();
            if (rid == roleId || rid == HIGHTEAM_ROLE_ID) return true;
        }
        return false;
    }

    private static MessageEmbed buildTicketEmbed(int num, String typeLabel, String creatorId, String claimedById) {
        String handler = claimedById.isBlank() ? "—" : "<@" + claimedById + ">";
        return EmbedFactory.create()
            .setTitle("🎫 Ticket #" + String.format("%04d", num) + " — " + typeLabel)
            .setDescription(
                "**Erstellt von:** <@" + creatorId + ">\n" +
                "**Kategorie:** " + typeLabel + "\n" +
                "**Bearbeiter:** " + handler + "\n\n" +
                "Beschreibe dein Anliegen. Ein Teammitglied wird sich so bald wie möglich um dich kümmern.")
            .build();
    }

    private static int parseTicketNum(String title) {
        if (title == null) return 0;
        try {
            int hash = title.indexOf('#');
            int sp   = title.indexOf(' ', hash + 1);
            if (hash >= 0 && sp > hash)
                return Integer.parseInt(title.substring(hash + 1, sp));
        } catch (NumberFormatException ignored) {}
        return 0;
    }
}
