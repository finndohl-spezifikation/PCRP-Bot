package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import net.dv8tion.jda.api.entities.Role;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.interaction.component.StringSelectInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * Verwaltet das Ping-Roles-Panel und dessen Select-Menu-Interaktionen.
 *
 * Jede Auswahl im Menü toggled die entsprechende Rolle:
 *   – Nutzer hat die Rolle → Rolle wird entfernt
 *   – Nutzer hat die Rolle nicht → Rolle wird vergeben
 */
public class RoleMenuListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(RoleMenuListener.class);

    public static final String SELECT_ID = "pingroles-sel";

    // Ping-Rollen (Name → ID)
    public record PingRole(String label, String value, long roleId) {}

    public static final List<PingRole> PING_ROLES = List.of(
        new PingRole("🔔 Lobby Ping",      "lobby-ping",    1529636309633863752L),
        new PingRole("📅 Event Ping",       "event-ping",    1529636310422130728L),
        new PingRole("⚔️ Fraktions Ping",   "fraktions-ping",1529636312339189792L),
        new PingRole("🎭 IC Ping",          "ic-ping",       1529636311403724971L),
        new PingRole("ℹ️ Info Ping",        "info-ping",     1529636308559855810L),
        new PingRole("🔄 Update Ping",      "update-ping",   1529636313819512832L)
    );

    // ════════════════════════════════════════════════════════════
    //  Select-Menu-Interaktion
    // ════════════════════════════════════════════════════════════

    @Override
    public void onStringSelectInteraction(StringSelectInteractionEvent event) {
        if (!SELECT_ID.equals(event.getComponentId())) return;
        if (event.getGuild() == null) return;

        Member member = event.getMember();
        if (member == null) return;

        Guild guild = event.getGuild();
        List<String> selected = event.getValues();

        List<String> added   = new ArrayList<>();
        List<String> removed = new ArrayList<>();

        for (PingRole pr : PING_ROLES) {
            if (!selected.contains(pr.value())) continue;

            Role role = guild.getRoleById(pr.roleId());
            if (role == null) continue;

            boolean hasRole = member.getRoles().stream()
                .anyMatch(r -> r.getIdLong() == pr.roleId());

            if (hasRole) {
                guild.removeRoleFromMember(member, role).queue(
                    v -> {},
                    e -> log.warn("[PingRoles] Rolle '{}' konnte nicht entfernt werden: {}", pr.label(), e.getMessage())
                );
                removed.add(pr.label());
            } else {
                guild.addRoleToMember(member, role).queue(
                    v -> {},
                    e -> log.warn("[PingRoles] Rolle '{}' konnte nicht vergeben werden: {}", pr.label(), e.getMessage())
                );
                added.add(pr.label());
            }
        }

        // Rückmeldung zusammenbauen
        StringBuilder sb = new StringBuilder();
        if (!added.isEmpty())   sb.append("✅ **Hinzugefügt:** ").append(String.join(", ", added)).append("\n");
        if (!removed.isEmpty()) sb.append("🗑️ **Entfernt:** ").append(String.join(", ", removed)).append("\n");
        if (sb.isEmpty())       sb.append("Keine Änderungen vorgenommen.");

        event.replyEmbeds(EmbedFactory.build("🔔 Ping-Rollen aktualisiert", sb.toString().trim()))
            .setEphemeral(true)
            .queue();
    }

    // ════════════════════════════════════════════════════════════
    //  Panel-Embed bauen
    // ════════════════════════════════════════════════════════════

    public static net.dv8tion.jda.api.entities.MessageEmbed buildPanelEmbed() {
        return EmbedFactory.create()
            .setTitle("🔔 Ping-Rollen")
            .setDescription(
                "Wähle deine Ping-Rollen aus dem Menü unten aus.\n" +
                "Wählst du eine Rolle erneut, wird sie wieder entfernt.\n\n" +
                "━━━━━━━━━━━━━━━━━━━━━━\n\n" +
                "🔔 **Lobby Ping**\n" +
                "📅 **Event Ping**\n" +
                "⚔️ **Fraktions Ping**\n" +
                "🎭 **IC Ping**\n" +
                "ℹ️ **Info Ping**\n" +
                "🔄 **Update Ping**")
            .build();
    }

    public static StringSelectMenu buildSelectMenu() {
        StringSelectMenu.Builder builder = StringSelectMenu.create(SELECT_ID)
            .setPlaceholder("Ping-Rolle auswählen / entfernen …")
            .setMinValues(1)
            .setMaxValues(PING_ROLES.size());

        for (PingRole pr : PING_ROLES) {
            builder.addOption(pr.label(), pr.value());
        }
        return builder.build();
    }

    // ════════════════════════════════════════════════════════════
    //  Panel posten (einmalig auf Startup)
    // ════════════════════════════════════════════════════════════

    public static void postPanel(Guild guild) {
        String key = "panel-pingroles-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(LoggingConfig.PING_ROLES_CHANNEL_ID);
        if (ch == null) { log.warn("[PingRoles] Kanal nicht gefunden."); return; }

        String stored = DataStore.readString(key);
        if (stored != null && !stored.isBlank()) {
            ch.retrieveMessageById(stored.trim()).queue(
                msg -> log.info("[PingRoles] Panel aktiv (ID: {}), kein Neuversand.", stored.trim()),
                err -> { DataStore.deleteKey(key); sendPanel(ch, key); }
            );
        } else {
            sendPanel(ch, key);
        }
    }

    private static void sendPanel(TextChannel ch, String key) {
        ch.sendMessageEmbeds(buildPanelEmbed())
          .addActionRow(buildSelectMenu())
          .queue(
            msg -> DataStore.writeString(key, msg.getId()),
            err -> log.error("[PingRoles] Panel konnte nicht gesendet werden.", err)
          );
    }
}
