package de.pcrp.bot.listeners;

import de.pcrp.bot.common.*;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.MessageEmbed;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import net.dv8tion.jda.api.events.interaction.ModalInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.ButtonInteractionEvent;
import net.dv8tion.jda.api.events.interaction.component.StringSelectInteractionEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import net.dv8tion.jda.api.interactions.InteractionHook;
import net.dv8tion.jda.api.interactions.components.ActionRow;
import net.dv8tion.jda.api.interactions.components.buttons.Button;
import net.dv8tion.jda.api.interactions.components.selections.StringSelectMenu;
import net.dv8tion.jda.api.interactions.components.text.TextInput;
import net.dv8tion.jda.api.interactions.components.text.TextInputStyle;
import net.dv8tion.jda.api.interactions.modals.Modal;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * Shop-System — unterstützt mehrere Shops (Kwik-E-Markt, Baumarkt, Angler-Shop, Schwarzmarkt).
 * Flow pro Shop: Shop Öffnen → Suchleiste (StringSelectMenu) → Menge wählen → Warenkorb → Kaufen.
 *
 * Backward-Kompat:
 *  - Button-ID "shop-open-kwike" wird intern als "shop-open-kwik-e-markt" behandelt.
 *  - ShopItem.shopId entscheidet, welcher Shop-Cart betroffen ist (Warenkorb ist ein Misch-Cart
 *    pro User, wird aber bei jedem "shop-open" zurückgesetzt — faktisch Ein-Shop-pro-Cart).
 */
public class ShopListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(ShopListener.class);

    // ─── Shop-Konfiguration (Enum zentralisiert alle Shop-Metadaten) ─────────

    public enum ShopType {
        KWIKE("kwik-e-markt", "Kwik-E-Markt", "🏪",
              LoggingConfig.SHOP_KWIKE_CHANNEL_ID,
              "Willkommen im **Kwik-E-Markt**!\n\n" +
              "Hier findest du alles für den täglichen Bedarf.\n" +
              "Zahlung erfolgt ausschließlich mit **Bargeld** aus deinem Rucksack.\n\n" +
              "Klicke auf **Shop Öffnen**, um den Shop zu betreten."),
        BAUMARKT("baumarkt", "Baumarkt", "🛠️",
                 LoggingConfig.SHOP_BAUMARKT_CHANNEL_ID,
                 "Willkommen im **Baumarkt**!\n\n" +
                 "Werkzeuge, Baumaterial und alles für den Heimwerker.\n" +
                 "Zahlung erfolgt ausschließlich mit **Bargeld**.\n\n" +
                 "Klicke auf **Shop Öffnen**, um den Shop zu betreten."),
        ANGLER("angler-shop", "Angler-Shop", "🎣",
               LoggingConfig.SHOP_ANGLER_CHANNEL_ID,
               "Willkommen im **Angler-Shop**!\n\n" +
               "Ruten, Köder und mehr für Angler.\n" +
               "Zahlung erfolgt ausschließlich mit **Bargeld**.\n\n" +
               "Klicke auf **Shop Öffnen**, um den Shop zu betreten."),
        SCHWARZMARKT("schwarzmarkt", "Schwarzmarkt", "🥷",
                     LoggingConfig.SHOP_SCHWARZMARKT_CHANNEL_ID,
                     "Willkommen im **Schwarzmarkt**!\n\n" +
                     "Du weißt nicht was du hier tust. Bargeld only.\n\n" +
                     "Klicke auf **Shop Öffnen**, um den Shop zu betreten.");

        public final String id;
        public final String name;
        public final String emoji;
        public final long   channelId;
        public final String description;

        ShopType(String id, String name, String emoji, long channelId, String description) {
            this.id = id; this.name = name; this.emoji = emoji; this.channelId = channelId; this.description = description;
        }

        public static ShopType byId(String shopId) {
            if (shopId == null) return null;
            for (ShopType s : values()) if (s.id.equalsIgnoreCase(shopId)) return s;
            return null;
        }
    }

    /** Backward-Compat-Konstante — zeigt weiterhin auf Kwik-E-Markt. */
    public static final String SHOP_KWIKE = ShopType.KWIKE.id;

    /** Warenkörbe (userId → CartEntry-Liste), flüchtig. Wird bei Shop-Open geleert. */
    private static final Map<String, List<CartEntry>> CARTS = new ConcurrentHashMap<>();

    /** Aktuell offener Shop pro User — Kontext für Buttons ohne Shop-ID. */
    private static final Map<String, String> CURRENT_SHOP = new ConcurrentHashMap<>();

    /** Hooks für laufende Mengen-Modals (userId → ShopMessage-Hook). */
    private static final Map<String, InteractionHook> QTY_HOOKS = new ConcurrentHashMap<>();

    public static class CartEntry {
        public final String itemId;
        public final String name;
        public final String shopId;   // NEU: jeder CartEntry kennt seinen Shop
        public final int    price;
        public       int    qty;

        CartEntry(String itemId, String name, String shopId, int price, int qty) {
            this.itemId = itemId; this.name = name; this.shopId = shopId; this.price = price; this.qty = qty;
        }
    }

    private static ShopType shopForUser(String userId) {
        String sid = CURRENT_SHOP.get(userId);
        return sid != null ? ShopType.byId(sid) : null;
    }

    // ── Button-Handler ────────────────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String cid     = event.getComponentId();
        String userId  = event.getUser().getId();
        String guildId = event.getGuild().getId();

        // ── Shop öffnen: "shop-open-{shopId}" (Legacy "shop-open-kwike" gemappt) ──
        if (cid.startsWith("shop-open-")) {
            String shopId = cid.substring("shop-open-".length());
            if ("kwike".equals(shopId)) shopId = "kwik-e-markt";   // Legacy-Alias
            ShopType shop = ShopType.byId(shopId);
            if (shop == null) {
                event.reply("❌ Unbekannter Shop.").setEphemeral(true).queue();
                return;
            }
            if (shop.channelId == 0L) {
                event.reply("❌ Dieser Shop ist noch nicht konfiguriert (TODO: Kanal-ID fehlt).")
                     .setEphemeral(true).queue();
                return;
            }
            CARTS.remove(userId);
            CURRENT_SHOP.put(userId, shop.id);
            List<ShopManager.ShopItem> items = ShopManager.getItemsForShop(guildId, shop.id);
            if (items.isEmpty()) {
                event.replyEmbeds(EmbedFactory.build(shop.emoji + " " + shop.name,
                    "Es sind aktuell keine Artikel verfügbar."))
                    .setEphemeral(true).queue();
                return;
            }
            event.replyEmbeds(buildShopEmbed(shop, guildId, userId))
                .addComponents(buildShopRows(shop, guildId, userId))
                .setEphemeral(true).queue();
            return;
        }

        // ── Zurück zur Shop-Übersicht (von Mengen-Auswahl) ──
        if ("shop-back".equals(cid)) {
            ShopType shop = shopForUser(userId);
            if (shop == null) { event.deferEdit().queue(); return; }
            event.editMessageEmbeds(buildShopEmbed(shop, guildId, userId))
                .setComponents(buildShopRows(shop, guildId, userId)).queue();
            return;
        }

        // ── Menge eingeben: Modal öffnen ──
        if (cid.startsWith("shop-qty-enter-")) {
            String itemId = cid.substring("shop-qty-enter-".length());
            ShopManager.ShopItem item = ShopManager.getItemById(guildId, itemId);
            if (item == null) { event.deferEdit().queue(); return; }
            ShopType shop = ShopType.byId(item.shopId);
            if (shop == null) { event.deferEdit().queue(); return; }
            CURRENT_SHOP.put(userId, shop.id);
            QTY_HOOKS.put(userId, event.getHook());
            Modal modal = Modal.create("shop-qty-modal-" + itemId, "Menge — " + item.name)
                .addComponents(ActionRow.of(
                    TextInput.create("qty", "Anzahl", TextInputStyle.SHORT)
                        .setPlaceholder("z. B. 3")
                        .setMinLength(1).setMaxLength(5)
                        .setRequired(true).build()))
                .build();
            event.replyModal(modal).queue();
            return;
        }

        // ── Warenkorb leeren ──
        if ("shop-clear".equals(cid)) {
            ShopType shop = shopForUser(userId);
            if (shop == null) { event.deferEdit().queue(); return; }
            CARTS.remove(userId);
            event.editMessageEmbeds(buildShopEmbed(shop, guildId, userId))
                .setComponents(buildShopRows(shop, guildId, userId)).queue();
            return;
        }

        // ── Kaufen ──
        if ("shop-buy".equals(cid)) {
            handleBuy(event, guildId, userId);
        }
    }

    // ── Modal-Handler (Mengen-Eingabe) ────────────────────────────────────────

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        if (event.getGuild() == null) return;
        String mid = event.getModalId();
        if (!mid.startsWith("shop-qty-modal-")) return;

        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();
        String itemId  = mid.substring("shop-qty-modal-".length());

        InteractionHook shopHook = QTY_HOOKS.remove(userId);

        int qty;
        try { qty = Integer.parseInt(event.getValue("qty").getAsString().trim()); }
        catch (NumberFormatException e) {
            event.reply("❌ Ungültige Anzahl — bitte eine ganze Zahl eingeben.")
                .setEphemeral(true).queue();
            return;
        }
        if (qty < 1) {
            event.reply("❌ Anzahl muss mindestens 1 sein.").setEphemeral(true).queue();
            return;
        }

        ShopManager.ShopItem item = ShopManager.getItemById(guildId, itemId);
        if (item == null) {
            event.deferReply(true).queue(h -> h.deleteOriginal().queue());
            return;
        }

        ShopType shop = ShopType.byId(item.shopId);
        if (shop != null) CURRENT_SHOP.put(userId, shop.id);

        List<CartEntry> cart = CARTS.computeIfAbsent(userId, k -> new ArrayList<>());
        CartEntry existing = cart.stream().filter(e -> e.itemId.equals(itemId)).findFirst().orElse(null);
        if (existing != null) existing.qty += qty;
        else cart.add(new CartEntry(item.id, item.name, item.shopId, item.price, qty));

        event.deferReply(true).queue(hook -> {
            if (shopHook != null && shop != null) {
                shopHook.editOriginalEmbeds(buildShopEmbed(shop, guildId, userId))
                    .setComponents(buildShopRows(shop, guildId, userId)).queue();
            }
            hook.deleteOriginal().queue();
        });
    }

    // ── StringSelectMenu-Handler (Suchleiste) ────────────────────────────────

    @Override
    public void onStringSelectInteraction(StringSelectInteractionEvent event) {
        if (event.getGuild() == null) return;
        if (!"shop-item-select".equals(event.getComponentId())) return;

        String userId  = event.getUser().getId();
        String guildId = event.getGuild().getId();
        String itemId  = event.getValues().get(0);

        ShopManager.ShopItem item = ShopManager.getItemById(guildId, itemId);
        if (item == null) { event.deferEdit().queue(); return; }

        ShopType shop = ShopType.byId(item.shopId);
        if (shop != null) CURRENT_SHOP.put(userId, shop.id);

        event.editMessageEmbeds(buildQtyEmbed(item))
            .setComponents(buildQtyRows(item)).queue();
    }

    // ── Kauf verarbeiten ─────────────────────────────────────────────────────

    private void handleBuy(ButtonInteractionEvent event, String guildId, String userId) {
        List<CartEntry> cart = CARTS.getOrDefault(userId, Collections.emptyList());
        if (cart.isEmpty()) {
            ShopType shop = shopForUser(userId);
            if (shop != null) {
                event.editMessageEmbeds(buildShopEmbed(shop, guildId, userId))
                    .setComponents(buildShopRows(shop, guildId, userId)).queue();
            }
            return;
        }

        // Shop aus erstem Cart-Item ableiten (oder CURRENT_SHOP als Fallback)
        ShopType shop = ShopType.byId(cart.get(0).shopId);
        if (shop == null) shop = shopForUser(userId);
        if (shop == null) return;

        long total = cartTotal(cart);
        long cash  = getCash(guildId, userId);
        if (cash < total) {
            event.editMessageEmbeds(buildShopEmbed(shop, guildId, userId))
                .setComponents(buildShopRows(shop, guildId, userId)).queue();
            return;
        }

        BargeldManager.remove(guildId, userId, total);
        for (CartEntry e : cart)
            InventoryManager.addItem(guildId, userId, e.name, e.qty);

        StringBuilder receipt = new StringBuilder();
        for (CartEntry e : cart)
            receipt.append("• **").append(e.name).append("** × ").append(e.qty)
                .append(" — ").append(ShopManager.formatPrice((long) e.price * e.qty)).append("\n");
        receipt.append("\n💰 Restliches Bargeld: **").append(ShopManager.formatPrice(cash - total)).append("**");

        CARTS.remove(userId);
        event.editMessageEmbeds(EmbedFactory.create()
            .setTitle("✅ Kauf erfolgreich!")
            .setDescription(receipt.toString())
            .build())
            .setComponents(Collections.emptyList()).queue();

        BotLogger.logMoney(event.getGuild(), "🛒 Shop-Kauf",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Gesamt:** -" + ShopManager.formatPrice(total) + " (Bargeld)\n" +
            "**Shop:** " + ShopManager.shopDisplayName(shop.id));
        StringBuilder itemLog = new StringBuilder();
        for (CartEntry e : cart)
            itemLog.append("• ").append(e.name).append(" × ").append(e.qty).append("\n");
        BotLogger.logItem(event.getGuild(), "🛒 Shop-Kauf — Artikel",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Artikel:**\n" + itemLog);

        log.info("[Shop] {} kaufte {} Artikel im {} für {}$.",
            event.getUser().getAsTag(), cart.size(), shop.name, total);
    }

    // ── Embeds ────────────────────────────────────────────────────────────────

    /** Haupt-Shop-Embed: Artikelliste + Warenkorb + Bargeld (rot wenn zu wenig). */
    public static MessageEmbed buildShopEmbed(ShopType shop, String guildId, String userId) {
        List<ShopManager.ShopItem> items = ShopManager.getItemsForShop(guildId, shop.id);
        List<CartEntry> cart       = CARTS.getOrDefault(userId, Collections.emptyList());
        List<CartEntry> cartForShop = cart.stream()
            .filter(e -> shop.id.equalsIgnoreCase(e.shopId))
            .collect(Collectors.toList());
        long cash         = getCash(guildId, userId);
        long totalForShop = cartForShop.stream().mapToLong(e -> (long) e.price * e.qty).sum();
        boolean tooLow    = !cartForShop.isEmpty() && cash < totalForShop;

        EmbedBuilder eb = EmbedFactory.create().setTitle(shop.emoji + " " + shop.name);

        if (items.isEmpty()) {
            eb.setDescription("*Keine Artikel verfügbar.*");
        } else {
            StringBuilder desc = new StringBuilder("Wähle Artikel über die **Suchleiste** unten aus:\n\n");
            for (ShopManager.ShopItem it : items) {
                long inCart = cart.stream().filter(e -> e.itemId.equals(it.id)).mapToLong(e -> e.qty).sum();
                desc.append("🏷️ **").append(it.name).append("** — ")
                    .append(ShopManager.formatPrice(it.price));
                if (inCart > 0) desc.append("  *(×").append(inCart).append(" im Warenkorb)*");
                desc.append("\n");
            }
            eb.setDescription(desc.toString());
        }

        if (cartForShop.isEmpty()) {
            String note = cart.isEmpty()
                ? "*Leer — füge Artikel über die Suchleiste hinzu.*"
                : "*Warenkorb enthält nur Items aus anderen Shops.*";
            eb.addField("🛒 Warenkorb", note, false);
        } else {
            StringBuilder cartStr = new StringBuilder();
            for (CartEntry e : cartForShop)
                cartStr.append("• **").append(e.name).append("** × ").append(e.qty)
                    .append(" — ").append(ShopManager.formatPrice((long) e.price * e.qty)).append("\n");
            cartStr.append("\n**Gesamt: ").append(ShopManager.formatPrice(totalForShop)).append("**");
            eb.addField("🛒 Warenkorb", cartStr.toString(), false);
        }

        if (tooLow) {
            long missing = totalForShop - cash;
            eb.addField("❌ Dein Bargeld",
                "~~" + ShopManager.formatPrice(cash) + "~~  *(fehlen: **" + ShopManager.formatPrice(missing) + "**)*", true);
        } else {
            eb.addField("💵 Dein Bargeld", ShopManager.formatPrice(cash), true);
        }

        return eb.build();
    }

    /** Embed für die Mengenauswahl eines einzelnen Artikels. */
    private static MessageEmbed buildQtyEmbed(ShopManager.ShopItem item) {
        return EmbedFactory.create()
            .setTitle("🏷️ " + item.name + " — Menge wählen")
            .setDescription(
                "**Preis:** " + ShopManager.formatPrice(item.price) + " pro Stück\n\n" +
                "Wie viele Stück möchtest du in den **Warenkorb** legen?")
            .build();
    }

    // ── ActionRows ────────────────────────────────────────────────────────────

    /** Haupt-Shop-Rows: StringSelectMenu (Suchleiste) + Steuerbuttons. */
    public static List<ActionRow> buildShopRows(ShopType shop, String guildId, String userId) {
        List<ShopManager.ShopItem> items     = ShopManager.getItemsForShop(guildId, shop.id);
        List<CartEntry>            cartForShop = CARTS.getOrDefault(userId, Collections.emptyList()).stream()
            .filter(e -> shop.id.equalsIgnoreCase(e.shopId))
            .collect(Collectors.toList());
        long cash      = getCash(guildId, userId);
        long total     = cartForShop.stream().mapToLong(e -> (long) e.price * e.qty).sum();
        boolean tooLow = !cartForShop.isEmpty() && cash < total;
        boolean hasCart = !cartForShop.isEmpty();

        List<ActionRow> rows = new ArrayList<>();

        if (!items.isEmpty()) {
            StringSelectMenu.Builder menu = StringSelectMenu
                .create("shop-item-select")
                .setPlaceholder("🔍 Artikel suchen und hinzufügen…")
                .setMinValues(1).setMaxValues(1);
            int limit = Math.min(items.size(), 25);
            for (int i = 0; i < limit; i++) {
                ShopManager.ShopItem it = items.get(i);
                menu.addOption(it.name, it.id, ShopManager.formatPrice(it.price) + " pro Stück");
            }
            rows.add(ActionRow.of(menu.build()));
        }

        rows.add(ActionRow.of(
            Button.danger( "shop-clear", "🗑️ Warenkorb leeren").withDisabled(!hasCart),
            Button.success("shop-buy",   "💳 Kaufen"          ).withDisabled(!hasCart || tooLow)
        ));

        return rows;
    }

    /** Rows für die Mengenauswahl (Menge eingeben + ← Zurück). */
    private static List<ActionRow> buildQtyRows(ShopManager.ShopItem item) {
        return List.of(
            ActionRow.of(
                Button.primary( "shop-qty-enter-" + item.id, "🔢 Menge eingeben"),
                Button.secondary("shop-back",                 "← Zurück zum Shop")
            )
        );
    }

    // ── Panel-Posting ─────────────────────────────────────────────────────────

    /** Postet alle konfigurierten Shop-Panels (Überspringt channelId=0 = TODO). */
    public static void postAllPanels(Guild guild) {
        for (ShopType s : ShopType.values()) {
            if (s.channelId == 0L) continue;   // TODO: Schwarzmarkt-Kanal-ID fehlt
            String key = "panel-" + s.id + "-v1-" + guild.getId();
            TextChannel ch = guild.getTextChannelById(s.channelId);
            if (ch == null) { log.warn("[Shop] Kanal für '{}' nicht gefunden.", s.name); continue; }
            PanelHelper.post(ch, key, s.emoji + " " + s.name, () -> sendPanel(ch, key, s));
        }
    }

    /** Backward-Compat-Methode: Alle Panels posten (altes Verhalten: nur Kwik-E). */
    public static void postPanelIfNeeded(Guild guild) {
        postAllPanels(guild);
    }

    private static void sendPanel(TextChannel ch, String key, ShopType shop) {
        ch.sendMessageEmbeds(EmbedFactory.build(
            shop.emoji + " " + shop.name,
            shop.description))
            .addActionRow(Button.primary("shop-open-" + shop.id, "🛒 Shop Öffnen"))
            .queue(
                msg -> PanelHelper.onSent(key, msg.getId()),
                err -> { log.error("[Shop] Panel '{}' konnte nicht gesendet werden.", key, err); PanelHelper.onFailed(key); });
    }

    // ── Hilfsmethoden ─────────────────────────────────────────────────────────

    static long getCash(String guildId, String userId) {
        return BargeldManager.get(guildId, userId);
    }

    private static long cartTotal(List<CartEntry> cart) {
        return cart.stream().mapToLong(e -> (long) e.price * e.qty).sum();
    }

    private static int safeInt(long v) { return (int) Math.min(v, Integer.MAX_VALUE); }
}
