package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Aktien-Panel-Posting: Jede Aktie hat ihren eigenen Kanal mit einem Embed
 * und einem Link-Button zur externen Aktien-Webseite (/aktien).
 */
public class AktienListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(AktienListener.class);

    /** Postet die Panels für alle Aktien (einmalig nach Bot-Start). */
    public static void postAllPanels(Guild guild) {
        for (AktienManager.Aktie a : AktienManager.STOCKS) {
            postPanel(guild, a);
        }
    }

    private static void postPanel(Guild guild, AktienManager.Aktie stock) {
        long channelId = channelFor(stock.id());
        String key = "panel-aktie-" + stock.id() + "-v1-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(channelId);
        if (ch == null) { log.warn("[Aktien] Kanal für '{}' nicht gefunden.", stock.name()); return; }
        PanelHelper.post(ch, key, stock.emoji() + " " + stock.name() + " — Aktie",
            () -> sendPanel(ch, key, stock));
    }

    private static void sendPanel(TextChannel ch, String key, AktienManager.Aktie stock) {
        String guildId = ch.getGuild().getId();
        ch.sendMessageEmbeds(EmbedFactory.build(
            stock.emoji() + " " + stock.name() + " — Aktie",
            "Kaufe die **" + stock.name() + "-Aktie** mit deinen PC Coins und verfolge den Kurs in Echtzeit.\n\n" +
            "Aktueller Kurs: **" + AktienManager.formatRate(AktienManager.getRate(stock, guildId)) + " PC**\n" +
            "Im Umlauf: **" + AktienManager.formatShares(AktienManager.getSupply(stock.id(), guildId)) + "**"))
            .addActionRow(
                Button.link(aktienUrl(stock.id()), "📈 Aktie ansehen"))
            .queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Aktien] Panel für '{}' konnte nicht gesendet werden.", stock.name(), err); PanelHelper.onFailed(key); });
    }

    private static long channelFor(String stockId) {
        return switch (stockId) {
            case "maze"       -> LoggingConfig.AKTIE_MAZE_CHANNEL_ID;
            case "benefactor" -> LoggingConfig.AKTIE_BENEFACTOR_CHANNEL_ID;
            case "goldwand"   -> LoggingConfig.AKTIE_GOLDWAND_CHANNEL_ID;
            default           -> LoggingConfig.AKTIE_DIAMOND_CHANNEL_ID;
        };
    }

    private static String aktienUrl(String stockId) {
        String webUrl = System.getenv("WEB_URL");
        if (webUrl == null || webUrl.isBlank()) {
            String domain = System.getenv("RAILWAY_PUBLIC_DOMAIN");
            webUrl = (domain != null && !domain.isBlank())
                ? (domain.startsWith("http") ? domain : "https://" + domain)
                : "https://dashboards.paradisecity-roleplay-85a.workers.dev";
        }
        return webUrl.replaceAll("/$", "") + "/aktien?stock=" + stockId;
    }
}
