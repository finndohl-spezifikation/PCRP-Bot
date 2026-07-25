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

/**
 * Kwik-E-Markt Shop.
 * Flow: Shop Öffnen → Suchleiste (StringSelectMenu) → Menge wählen → Warenkorb → Kaufen
 */
public class ShopListener extends ListenerAdapter {

    private static final Logger log = LoggerFactory.getLogger(ShopListener.class);

    public static final String SHOP_KWIKE = "kwik-e-markt";

    /** Warenkörbe (userId → CartEntry-Liste), flüchtig. */
    private static final Map<String, List<CartEntry>> CARTS = new ConcurrentHashMap<>();

    /** Hooks für laufende Mengen-Modals (userId → ShopMessage-Hook). */
    private static final Map<String, InteractionHook> QTY_HOOKS = new ConcurrentHashMap<>();

    public static class CartEntry {
        public final String itemId;
        public final String name;
        public final int    price;
        public       int    qty;

        CartEntry(String itemId, String name, int price, int qty) {
            this.itemId = itemId; this.name = name; this.price = price; this.qty = qty;
        }
    }

    // ── Button-Handler ────────────────────────────────────────────────────────

    @Override
    public void onButtonInteraction(ButtonInteractionEvent event) {
        if (event.getGuild() == null) return;
        String cid     = event.getComponentId();
        String userId  = event.getUser().getId();
        String guildId = event.getGuild().getId();

        // ── Shop öffnen ──
        if ("shop-open-kwike".equals(cid)) {
            CARTS.remove(userId);
            List<ShopManager.ShopItem> items = ShopManager.getItemsForShop(guildId, SHOP_KWIKE);
            if (items.isEmpty()) {
                event.replyEmbeds(EmbedFactory.build("🏪 Kwik-E-Markt",
                    "Es sind aktuell keine Artikel verfügbar."))
                    .setEphemeral(true).queue();
                return;
            }
            event.replyEmbeds(buildShopEmbed(guildId, userId))
                .addComponents(buildShopRows(guildId, userId))
                .setEphemeral(true).queue();
            return;
        }

        // ── Zurück zur Shop-Übersicht (von Mengen-Auswahl) ──
        if ("shop-back".equals(cid)) {
            event.editMessageEmbeds(buildShopEmbed(guildId, userId))
                .setComponents(buildShopRows(guildId, userId)).queue();
            return;
        }

        // ── Menge eingeben: Modal öffnen ──
        if (cid.startsWith("shop-qty-enter-")) {
            String itemId = cid.substring("shop-qty-enter-".length());
            ShopManager.ShopItem item = ShopManager.getItemById(guildId, itemId);
            if (item == null) { event.deferEdit().queue(); return; }
            QTY_HOOKS.put(userId, event.getHook());
            Modal modal = Modal.create("shop-qty-modal-" + itemId,
                    "Menge — " + item.name)
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
            CARTS.remove(userId);
            event.editMessageEmbeds(buildShopEmbed(guildId, userId))
                .setComponents(buildShopRows(guildId, userId)).queue();
            return;
        }

        // ── Kaufen ──
        if ("shop-buy".equals(cid)) {
            handleBuy(event, guildId, userId);
        }
    }

    // ── Modal-Handler (Mengen-Eingabe) ───────────────────────────────────────

    @Override
    public void onModalInteraction(ModalInteractionEvent event) {
        if (event.getGuild() == null) return;
        String mid = event.getModalId();
        if (!mid.startsWith("shop-qty-modal-")) return;

        String guildId = event.getGuild().getId();
        String userId  = event.getUser().getId();
        String itemId  = mid.substring("shop-qty-modal-".length());

        InteractionHook shopHook = QTY_HOOKS.remove(userId);

        // Anzahl parsen
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

        // Warenkorb aktualisieren
        List<CartEntry> cart = CARTS.computeIfAbsent(userId, k -> new ArrayList<>());
        CartEntry existing = cart.stream().filter(e -> e.itemId.equals(itemId)).findFirst().orElse(null);
        if (existing != null) existing.qty += qty;
        else cart.add(new CartEntry(item.id, item.name, item.price, qty));

        // Modal bestätigen + Shop-Nachricht zurück editieren
        event.deferReply(true).queue(hook -> {
            if (shopHook != null) {
                shopHook.editOriginalEmbeds(buildShopEmbed(guildId, userId))
                    .setComponents(buildShopRows(guildId, userId)).queue();
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

        event.editMessageEmbeds(buildQtyEmbed(item))
            .setComponents(buildQtyRows(item)).queue();
    }

    // ── Kauf verarbeiten ─────────────────────────────────────────────────────

    private void handleBuy(ButtonInteractionEvent event, String guildId, String userId) {
        List<CartEntry> cart = CARTS.getOrDefault(userId, Collections.emptyList());
        if (cart.isEmpty()) {
            event.editMessageEmbeds(buildShopEmbed(guildId, userId))
                .setComponents(buildShopRows(guildId, userId)).queue();
            return;
        }
        long total = cartTotal(cart);
        long cash  = getCash(guildId, userId);
        if (cash < total) {
            // Sollte durch deaktivierten Button nicht erreichbar sein, zur Sicherheit:
            event.editMessageEmbeds(buildShopEmbed(guildId, userId))
                .setComponents(buildShopRows(guildId, userId)).queue();
            return;
        }

        // Zahlung abbuchen + Artikel gutschreiben
        BargeldManager.remove(guildId, userId, total);
        for (CartEntry e : cart)
            InventoryManager.addItem(guildId, userId, e.name, e.qty);

        // Quittung
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

        // Logs
        BotLogger.logMoney(event.getGuild(), "🛒 Shop-Kauf",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Gesamt:** -" + ShopManager.formatPrice(total) + " (Bargeld)\n" +
            "**Shop:** " + ShopManager.shopDisplayName(SHOP_KWIKE));
        StringBuilder itemLog = new StringBuilder();
        for (CartEntry e : cart)
            itemLog.append("• ").append(e.name).append(" × ").append(e.qty).append("\n");
        BotLogger.logItem(event.getGuild(), "🛒 Shop-Kauf — Artikel",
            "**Spieler:** " + event.getUser().getAsMention() + "\n" +
            "**Artikel:**\n" + itemLog);

        log.info("[Shop] {} kaufte Artikel für {}$.", event.getUser().getAsTag(), total);
    }

    // ── Embeds ────────────────────────────────────────────────────────────────

    /** Haupt-Shop-Embed: Artikelliste + Warenkorb + Bargeld (rot wenn zu wenig). */
    public static MessageEmbed buildShopEmbed(String guildId, String userId) {
        List<ShopManager.ShopItem> items = ShopManager.getItemsForShop(guildId, SHOP_KWIKE);
        List<CartEntry>            cart  = CARTS.getOrDefault(userId, Collections.emptyList());
        long cash        = getCash(guildId, userId);
        long total       = cartTotal(cart);
        boolean tooLow   = !cart.isEmpty() && cash < total;

        EmbedBuilder eb = EmbedFactory.create().setTitle("🏪 Kwik-E-Markt");

        // Artikelliste
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

        // Warenkorb
        if (cart.isEmpty()) {
            eb.addField("🛒 Warenkorb", "*Leer — füge Artikel über die Suchleiste hinzu.*", false);
        } else {
            StringBuilder cartStr = new StringBuilder();
            for (CartEntry e : cart)
                cartStr.append("• **").append(e.name).append("** × ").append(e.qty)
                    .append(" — ").append(ShopManager.formatPrice((long) e.price * e.qty)).append("\n");
            cartStr.append("\n**Gesamt: ").append(ShopManager.formatPrice(total)).append("**");
            eb.addField("🛒 Warenkorb", cartStr.toString(), false);
        }

        // Bargeld — rot hervorheben wenn nicht genug
        if (tooLow) {
            long missing = total - cash;
            eb.addField(
                "❌ Dein Bargeld",
                "~~" + ShopManager.formatPrice(cash) + "~~  *(fehlen: **" + ShopManager.formatPrice(missing) + "**)*",
                true);
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
    public static List<ActionRow> buildShopRows(String guildId, String userId) {
        List<ShopManager.ShopItem> items = ShopManager.getItemsForShop(guildId, SHOP_KWIKE);
        List<CartEntry>            cart  = CARTS.getOrDefault(userId, Collections.emptyList());
        long cash      = getCash(guildId, userId);
        long total     = cartTotal(cart);
        boolean tooLow = !cart.isEmpty() && cash < total;
        boolean hasCart = !cart.isEmpty();

        List<ActionRow> rows = new ArrayList<>();

        // StringSelectMenu als Suchleiste
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

        // Steuerbuttons
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

    // ── Hilfsmethoden ─────────────────────────────────────────────────────────

    static long getCash(String guildId, String userId) {
        return BargeldManager.get(guildId, userId);
    }

    private static long cartTotal(List<CartEntry> cart) {
        return cart.stream().mapToLong(e -> (long) e.price * e.qty).sum();
    }

    private static int safeInt(long v) { return (int) Math.min(v, Integer.MAX_VALUE); }
}
