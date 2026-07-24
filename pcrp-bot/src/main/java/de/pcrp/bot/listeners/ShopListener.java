package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.MessageEmbed;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Verwaltet den Discord-Shop.
 * Unterstützte Shops: kwik-e-markt (Kanal 1529636612932374631)
 */
public class ShopListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(ShopListener.class);

    /** Shop-ID-Konstante für den Kwik-E-Markt. */
    public static final String SHOP_KWIKE = "kwik-e-markt";

    /**
     * In-Memory Warenkörbe: userId → CartEntry-Liste.
     * Flüchtig – wird bei Bot-Neustart zurückgesetzt.
     */
    private static final Map<String, List<CartEntry>> CARTS = new ConcurrentHashMap<>();

    public static class CartEntry {
        public final String itemId;
        public final String name;
        public final int    price;
        public       int    qty;

        CartEntry(String itemId, String name, int price) {
            this.itemId = itemId; this.name = name; this.price = price; this.qty = 1;
        }
    }

    // ── Button-Handler ────────────────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String cid     = event.getComponentId();
        String userId  = event.getUser().getId();
        String guildId = event.getGuild().getId();

        // Shop öffnen
        if ("shop-open-kwike".equals(cid)) {
            CARTS.remove(userId); // frischen Warenkorb starten
            List<ShopManager.ShopItem> items = ShopManager.getItemsForShop(guildId, SHOP_KWIKE);
            if (items.isEmpty()) {
                event.replyEmbeds(EmbedFactory.build(
                    "🏪 Kwik-E-Markt",
                    "Es sind aktuell keine Artikel verfügbar."))
                    .setEphemeral(true).queue();
                return;
            }
            event.replyEmbeds(buildShopEmbed(guildId, userId))
                .addComponents(buildRows(guildId, userId))
                .setEphemeral(true).queue();
            return;
        }

        // Artikel in den Warenkorb
        if (cid.startsWith("shop-add-")) {
            String itemId = cid.substring("shop-add-".length());
            ShopManager.ShopItem item = ShopManager.getItemById(guildId, itemId);
            if (item == null) { event.deferEdit().queue(); return; }
            List<CartEntry> cart = CARTS.computeIfAbsent(userId, k -> new ArrayList<>());
            CartEntry existing = cart.stream().filter(e -> e.itemId.equals(itemId)).findFirst().orElse(null);
            if (existing != null) existing.qty++;
            else cart.add(new CartEntry(item.id, item.name, item.price));
            event.editMessageEmbeds(buildShopEmbed(guildId, userId))
                .setComponents(buildRows(guildId, userId)).queue();
            return;
        }

        // Warenkorb leeren
        if ("shop-clear".equals(cid)) {
            CARTS.remove(userId);
            event.editMessageEmbeds(buildShopEmbed(guildId, userId))
                .setComponents(buildRows(guildId, userId)).queue();
            return;
        }

        // Kaufen
        if ("shop-buy".equals(cid)) {
            handleBuy(event, guildId, userId);
        }
    }

    // ── Kauf verarbeiten ─────────────────────────────────────────────────────

    private void handleBuy(ButtonInteractionEvent event, String guildId, String userId) {
        List<CartEntry> cart = CARTS.getOrDefault(userId, Collections.emptyList());
        if (cart.isEmpty()) {
            event.editMessageEmbeds(EmbedFactory.build("🛒 Warenkorb leer",
                "Wähle zuerst Artikel aus."))
                .setComponents(buildRows(guildId, userId)).queue();
            return;
        }
        long total = cartTotal(cart);

        // Bargeld prüfen
        long cash = InventoryManager.getInventory(guildId, userId).stream()
            .filter(it -> "Bargeld".equalsIgnoreCase(it.name))
            .mapToLong(it -> (long) it.quantity).sum();

        if (cash < total) {
            event.editMessageEmbeds(EmbedFactory.create()
                .setTitle("❌ Nicht genug Bargeld")
                .setDescription(
                    "💵 Dein Bargeld: **" + ShopManager.formatPrice(cash) + "**\n" +
                    "🛒 Gesamtbetrag: **" + ShopManager.formatPrice(total) + "**\n\n" +
                    "Bitte entnehme Bargeld aus der Bank oder reduziere deinen Warenkorb.")
                .build())
                .setComponents(buildRows(guildId, userId)).queue();
            return;
        }

        // Zahlung abbuchen
        InventoryManager.removeItem(guildId, userId, "Bargeld", safeInt(total));

        // Artikel gutschreiben
        for (CartEntry e : cart)
            InventoryManager.addItem(guildId, userId, e.name, e.qty);

        // Quittung
        StringBuilder receipt = new StringBuilder();
        for (CartEntry e : cart)
            receipt.append("• **").append(e.name).append("** × ").append(e.qty)
                .append(" — ").append(ShopManager.formatPrice((long) e.price * e.qty)).append("\n");
        long remaining = cash - total;
        receipt.append("\n💰 Restliches Bargeld: **").append(ShopManager.formatPrice(remaining)).append("**");

        CARTS.remove(userId);
        event.editMessageEmbeds(EmbedFactory.create()
            .setTitle("✅ Kauf erfolgreich!")
            .setDescription(receipt.toString())
            .build())
            .setComponents(Collections.emptyList()).queue();

        // Geld-Log: Einkauf
        BotLogger.logMoney(event.getGuild(), "🛒 Shop-Kauf",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Gesamt:** -" + ShopManager.formatPrice(total) + " (Bargeld)\n" +
            "**Shop:** " + ShopManager.shopDisplayName(SHOP_KWIKE));
        // Item-Log: Artikel erhalten
        StringBuilder itemLog = new StringBuilder();
        for (CartEntry e : cart)
            itemLog.append("• ").append(e.name).append(" × ").append(e.qty).append("\n");
        BotLogger.logItem(event.getGuild(), "🛒 Shop-Kauf — Artikel",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Artikel:**\n" + itemLog);

        log.info("[Shop] {} kaufte Artikel für {}$.", event.getUser().getAsTag(), total);
    }

    // ── Embed & Komponenten bauen ──────────────────────────────────────────────

    public static MessageEmbed buildShopEmbed(String guildId, String userId) {
        List<ShopManager.ShopItem> items = ShopManager.getItemsForShop(guildId, SHOP_KWIKE);
        List<CartEntry>            cart  = CARTS.getOrDefault(userId, Collections.emptyList());
        long cash = InventoryManager.getInventory(guildId, userId).stream()
            .filter(it -> "Bargeld".equalsIgnoreCase(it.name))
            .mapToLong(it -> (long) it.quantity).sum();
        long total = cartTotal(cart);

        EmbedBuilder eb = EmbedFactory.create().setTitle("🏪 Kwik-E-Markt");

        // Artikelliste
        StringBuilder desc = new StringBuilder("**Verfügbare Artikel** — Klicke auf einen Artikel, um ihn hinzuzufügen:\n\n");
        for (ShopManager.ShopItem it : items) {
            long inCart = cart.stream().filter(e -> e.itemId.equals(it.id)).mapToLong(e -> e.qty).sum();
            desc.append("🏷️ **").append(it.name).append("** — ")
                .append(ShopManager.formatPrice(it.price));
            if (inCart > 0) desc.append("  *(im Warenkorb: ").append(inCart).append("×)*");
            desc.append("\n");
        }
        eb.setDescription(desc.toString());

        // Warenkorb-Feld
        if (cart.isEmpty()) {
            eb.addField("🛒 Warenkorb", "*Leer*", false);
        } else {
            StringBuilder cartStr = new StringBuilder();
            for (CartEntry e : cart)
                cartStr.append("• ").append(e.name).append(" × ").append(e.qty)
                    .append(" — **").append(ShopManager.formatPrice((long) e.price * e.qty)).append("**\n");
            cartStr.append("\n**Gesamt: ").append(ShopManager.formatPrice(total)).append("**");
            eb.addField("🛒 Warenkorb", cartStr.toString(), false);
        }

        eb.addField("💵 Dein Bargeld", ShopManager.formatPrice(cash), true);

        return eb.build();
    }

    /**
     * Baut die ActionRows für die Shop-Nachricht.
     * Bis zu 4 Reihen mit Artikel-Buttons + 1 Reihe mit Steuerbuttons (max 25 Artikel).
     */
    public static List<ActionRow> buildRows(String guildId, String userId) {
        List<ShopManager.ShopItem> items = ShopManager.getItemsForShop(guildId, SHOP_KWIKE);
        List<CartEntry>            cart  = CARTS.getOrDefault(userId, Collections.emptyList());
        List<ActionRow>            rows  = new ArrayList<>();

        // Artikel-Buttons (max 20 Artikel à 5 pro Reihe = 4 Reihen)
        List<Button> btns = new ArrayList<>();
        int limit = Math.min(items.size(), 20);
        for (int i = 0; i < limit; i++) {
            ShopManager.ShopItem it = items.get(i);
            long qty = cart.stream().filter(e -> e.itemId.equals(it.id)).mapToLong(e -> e.qty).sum();
            String label = trunc(it.name, 14) + " (" + ShopManager.formatPrice(it.price) + ")"
                + (qty > 0 ? " ×" + qty : "");
            btns.add(Button.secondary("shop-add-" + it.id, label));
        }
        for (int i = 0; i < btns.size(); i += 5)
            rows.add(ActionRow.of(btns.subList(i, Math.min(i + 5, btns.size()))));

        // Steuer-Reihe
        boolean hasCart = !cart.isEmpty();
        rows.add(ActionRow.of(
            Button.danger( "shop-clear", "🗑️ Warenkorb leeren").withDisabled(!hasCart),
            Button.success("shop-buy",   "💳 Kaufen"          ).withDisabled(!hasCart)
        ));
        return rows;
    }

    // ── Panel Posting ──────────────────────────────────────────────────────────

    public static void postPanelIfNeeded(Guild guild) {
        String key = "panel-kwike-v1-" + guild.getId();
        TextChannel ch = guild.getTextChannelById(LoggingConfig.SHOP_KWIKE_CHANNEL_ID);
        if (ch == null) { log.warn("[Shop] Kwik-E-Markt Kanal nicht gefunden."); return; }
        String stored = DataStore.readString(key);
        if (stored != null && !stored.isBlank()) {
            ch.retrieveMessageById(stored).queue(
                msg -> { /* bereits vorhanden */ },
                err -> { DataStore.deleteKey(key); sendPanel(ch, key); });
        } else {
            sendPanel(ch, key);
        }
    }

    private static void sendPanel(TextChannel ch, String key) {
        ch.sendMessageEmbeds(EmbedFactory.build(
            "🏪 Kwik-E-Markt",
            "Willkommen im **Kwik-E-Markt**!\n\n" +
            "Hier findest du alles für den täglichen Bedarf.\n" +
            "Zahlung erfolgt ausschließlich mit **Bargeld** aus deinem Rucksack.\n\n" +
            "Klicke auf **Shop Öffnen**, um den Shop zu betreten."))
            .addActionRow(Button.primary("shop-open-kwike", "🛒 Shop Öffnen"))
            .queue(
                msg -> DataStore.writeString(key, msg.getId()),
                err -> log.error("[Shop] Panel konnte nicht gesendet werden.", err));
    }

    // ── Utils ──────────────────────────────────────────────────────────────────

    private static long cartTotal(List<CartEntry> cart) {
        return cart.stream().mapToLong(e -> (long) e.price * e.qty).sum();
    }

    private static int safeInt(long v) { return (int) Math.min(v, Integer.MAX_VALUE); }

    private static String trunc(String s, int max) {
        return s.length() <= max ? s : s.substring(0, max - 1) + "…";
    }
}
