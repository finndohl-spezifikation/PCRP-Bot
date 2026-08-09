package de.pcrp.bot.listeners;

import de.pcrp.bot.common.DataStore;
import de.pcrp.bot.common.EmbedFactory;
import de.pcrp.bot.common.SupportAudio;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.entities.Role;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.entities.channel.middleman.AudioChannel;
import net.dv8tion.jda.api.events.guild.voice.GuildVoiceUpdateEvent;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.awt.Color;
import java.util.Collections;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Support-Warteraum:
 *
 *  - Betritt jemand den Warteraum-Sprachkanal, wird automatisch ein Embed mit Ping
 *    an Support- und Highteam-Rolle in den Support-Alert-Kanal gesendet.
 *  - Der Bot verbindet sich selbst in den Warteraum, spielt Wartemusik und sagt
 *    in deutscher Sprache die Ansagen (siehe {@link SupportAudio}).
 *  - Mit dem Button „Fall Übernehmen" (nur aus einem Sprachkanal klickbar) wird der
 *    wartende Spieler in den Sprachkanal des Teamlers bewegt. Der Button kann nur
 *    einmal geklickt werden — danach wird das Embed grün, der Button verschwindet
 *    und unten steht „Fall bereits Übernommen".
 */
public class SupportListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(SupportListener.class);

    /** Warteraum-Sprachkanal. */
    private static final long WAITROOM_VOICE_ID = 1529636427384623354L;

    /** Kanal in dem das Support-Alert-Embed gepostet wird. */
    private static final long ALERT_CHANNEL_ID = 1536000268120883302L;

    /** Rollen die beim Warteraum-Beitritt gepingt werden. */
    private static final long SUPPORT_ROLE_ID  = 1529636282148458538L;
    private static final long HIGHTEAM_ROLE_ID = 1529636280365748345L;

    private static final String CLAIM_PREFIX = "support-claim:";

    private static String alertKey(long guildId, long userId) {
        return "support-alert-" + guildId + "-" + userId;
    }

    private static String claimedKey(long guildId, long userId) {
        return "support-claimed-" + guildId + "-" + userId;
    }

    /** Guild-ID → aktuell wartende User-IDs. */
    private static final Map<Long, Set<Long>> WAITING = new ConcurrentHashMap<>();

    // ── Voice-Events ──────────────────────────────────────────────────────────

    @Override
    public void onGuildVoiceUpdate(GuildVoiceUpdateEvent e) {
        Member member = e.getMember();
        if (member == null || member.getUser().isBot()) return;

        long guildId = e.getGuild().getIdLong();
        AudioChannel joined = e.getChannelJoined();
        AudioChannel left   = e.getChannelLeft();

        // Beitritt in den Warteraum → Embed + Ping + Musik/Ansagen
        if (joined != null && joined.getIdLong() == WAITROOM_VOICE_ID) {
            WAITING.computeIfAbsent(guildId, k -> ConcurrentHashMap.newKeySet()).add(member.getIdLong());
            postAlert(e.getGuild(), member);
            SupportAudio.start(e.getGuild(), joined);
        }

        // Verlassen des Warteraums (auch durch den Move beim Übernehmen) → wenn niemand
        // mehr wartet, Musik + Ansagen stoppen.
        if (left != null && left.getIdLong() == WAITROOM_VOICE_ID) {
            Set<Long> waiting = WAITING.get(guildId);
            if (waiting != null) {
                waiting.remove(member.getIdLong());
                if (waiting.isEmpty()) {
                    WAITING.remove(guildId);
                    SupportAudio.stop();
                }
            }
        }
    }

    // ── Button „Fall Übernehmen" ──────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        String id = event.getComponentId();
        if (!id.startsWith(CLAIM_PREFIX)) return;
        if (event.getGuild() == null || event.getMember() == null) return;

        String[] parts = id.split(":");
        if (parts.length < 3) return;
        long waitingUserId;
        long guildId;
        try {
            waitingUserId = Long.parseLong(parts[1]);
            guildId       = Long.parseLong(parts[2]);
        } catch (NumberFormatException ex) {
            return;
        }
        Guild  guild       = event.getGuild();
        Member clicker     = event.getMember();

        // Bereits übernommen (Doppel-Klick-Schutz)
        if (DataStore.readString(claimedKey(guildId, waitingUserId)) != null) {
            event.reply("❌ Dieser Fall wurde bereits übernommen.").setEphemeral(true).queue();
            return;
        }

        // Man kann nicht seinen eigenen Fall übernehmen
        if (clicker.getIdLong() == waitingUserId) {
            event.reply("❌ Du kannst nicht deinen eigenen Fall übernehmen.").setEphemeral(true).queue();
            return;
        }

        // Klicker muss selbst in einem Sprachkanal sein
        AudioChannel teamChannel = clicker.getVoiceState() != null ? clicker.getVoiceState().getChannel() : null;
        if (teamChannel == null) {
            event.reply("❌ Du musst selbst in einem Sprachkanal sein, um einen Fall zu übernehmen.")
                .setEphemeral(true).queue();
            return;
        }

        // Wartender muss noch im Warteraum sein
        Member waiting = guild.getMemberById(waitingUserId);
        boolean stillWaiting = waiting != null
            && waiting.getVoiceState() != null
            && waiting.getVoiceState().getChannel() != null
            && waiting.getVoiceState().getChannel().getIdLong() == WAITROOM_VOICE_ID;
        if (!stillWaiting) {
            event.reply("❌ Der Spieler ist nicht mehr im Warteraum.").setEphemeral(true).queue();
            return;
        }

        // Fall als übernommen markieren (einmalig)
        DataStore.writeString(claimedKey(guildId, waitingUserId), clicker.getId());

        // Wartenden Spieler in den Sprachkanal des Teamlers bewegen
        guild.moveVoiceMember(waiting, teamChannel).queue(
            ok -> log.info("[Support] {} übernimmt Fall von {} → Kanal '{}'.",
                clicker.getEffectiveName(), waiting.getEffectiveName(), teamChannel.getName()),
            err -> log.warn("[Support] Move fehlgeschlagen: {}", err.getMessage())
        );

        // Button-Ack + Embed grün machen, Button entfernen, „Fall bereits Übernommen"
        event.deferEdit().queue(hook ->
            hook.sendMessage("✅ Du hast den Fall übernommen. " + waiting.getAsMention()
                    + " wird in deinen Kanal bewegt.")
                .setEphemeral(true).queue(null, e -> {})
        );
        String alertMsgId = DataStore.readString(alertKey(guildId, waitingUserId));
        if (alertMsgId != null && !alertMsgId.isBlank()) {
            TextChannel ch = guild.getTextChannelById(ALERT_CHANNEL_ID);
            if (ch != null) {
                ch.editMessageEmbedsById(alertMsgId.trim(),
                    EmbedFactory.create()
                        .setColor(Color.GREEN)
                        .setTitle("✅ Support-Fall übernommen")
                        .setDescription(
                            "**" + waiting.getEffectiveName() + "** wurde in den Sprachkanal von **"
                                + clicker.getEffectiveName() + "** bewegt.")
                        .setFooter("Fall bereits Übernommen")
                        .build()
                ).setComponents(Collections.emptyList()).queue(null, err ->
                    log.warn("[Support] Embed-Update fehlgeschlagen: {}", err.getMessage()));
            }
        }
    }

    // ── Alert-Embed ───────────────────────────────────────────────────────────

    private void postAlert(Guild guild, Member member) {
        TextChannel ch = guild.getTextChannelById(ALERT_CHANNEL_ID);
        if (ch == null) {
            log.warn("[Support] Alert-Kanal {} nicht gefunden.", ALERT_CHANNEL_ID);
            return;
        }
        Role support  = guild.getRoleById(SUPPORT_ROLE_ID);
        Role highteam = guild.getRoleById(HIGHTEAM_ROLE_ID);
        String ping = (support != null ? support.getAsMention() + " " : "")
                    + (highteam != null ? highteam.getAsMention() : "");

        String desc = "**" + member.getAsMention() + "** wartet im Support-Warteraum und benötigt Hilfe.\n\n"
                    + "Ein Teammitglied kann den Fall mit dem Button unten übernehmen.";

        String buttonId = CLAIM_PREFIX + member.getId() + ":" + guild.getId();
        var embed = EmbedFactory.create()
            .setTitle("🎧 Support-Warteraum")
            .setDescription(desc)
            .build();
        var action = ping.isBlank()
            ? ch.sendMessageEmbeds(embed)
            : ch.sendMessage(ping).addEmbeds(embed);
        action.addActionRow(
            Button.success(buttonId, "✅ Fall Übernehmen")
        ).queue(
            msg -> {
                DataStore.writeString(alertKey(guild.getIdLong(), member.getIdLong()), msg.getId());
                log.info("[Support] Alert für {} gepostet (msg={}).", member.getEffectiveName(), msg.getId());
            },
            err -> log.error("[Support] Alert konnte nicht gepostet werden.", err)
        );
    }
}
