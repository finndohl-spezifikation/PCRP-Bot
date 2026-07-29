package de.pcrp.bot.common;

import com.google.gson.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/** Verwaltet Shop-Artikel für alle Shops. Gespeichert in DataStore. */
public final class ShopManager {

    private static final Logger log  = LoggerFactory.getLogger(ShopManager.class);
    private static final Gson   GSON = new GsonBuilder().create();
    private static final String KEY  = "shop-items-";

    private ShopManager() {}

    // ── Datenklasse ───────────────────────────────────────────────────────────

    public static class ShopItem {
        public final String id;
        public final String name;
        public final int    price;
        public final String shopId;

        public ShopItem(String id, String name, int price, String shopId) {
            this.id = id; this.name = name; this.price = price; this.shopId = shopId;
        }
    }

    // ── Lesen ──────────────────────────────────────────────────────────────────

    public static List<ShopItem> getAllItems(String guildId) {
        String raw = DataStore.readString(KEY + guildId);
        if (raw == null || raw.isBlank()) return new ArrayList<>();
        try {
            JsonArray arr = JsonParser.parseString(raw).getAsJsonArray();
            List<ShopItem> list = new ArrayList<>();
            for (JsonElement el : arr) {
                JsonObject o = el.getAsJsonObject();
                list.add(new ShopItem(
                    o.get("id").getAsString(),
                    o.get("name").getAsString(),
                    o.get("price").getAsInt(),
                    o.get("shopId").getAsString()
                ));
            }
            return list;
        } catch (Exception e) {
            log.warn("[Shop] Fehler beim Lesen der Items (Guild {}).", guildId, e);
            return new ArrayList<>();
        }
    }

    public static List<ShopItem> getItemsForShop(String guildId, String shopId) {
        List<ShopItem> result = new ArrayList<>();
        for (ShopItem it : getAllItems(guildId))
            if (shopId.equalsIgnoreCase(it.shopId)) result.add(it);
        return result;
    }

    public static ShopItem getItemById(String guildId, String itemId) {
        return getAllItems(guildId).stream()
            .filter(it -> it.id.equals(itemId)).findFirst().orElse(null);
    }

    // ── Schreiben ─────────────────────────────────────────────────────────────

    public static String addItem(String guildId, String name, int price, String shopId) {
        String id = UUID.randomUUID().toString().replace("-", "").substring(0, 8);
        List<ShopItem> items = getAllItems(guildId);
        items.add(new ShopItem(id, name, price, shopId));
        save(guildId, items);
        log.info("[Shop] Artikel '{}' ({}) in '{}' erstellt.", name, price, shopId);
        return id;
    }

    public static boolean editItem(String guildId, String itemId,
                                   String newName, Integer newPrice, String newShopId) {
        List<ShopItem> items = getAllItems(guildId);
        for (int i = 0; i < items.size(); i++) {
            if (items.get(i).id.equals(itemId)) {
                ShopItem old = items.get(i);
                items.set(i, new ShopItem(
                    old.id,
                    newName    != null ? newName    : old.name,
                    newPrice   != null ? newPrice   : old.price,
                    newShopId  != null ? newShopId  : old.shopId
                ));
                save(guildId, items);
                return true;
            }
        }
        return false;
    }

    public static boolean removeItem(String guildId, String itemId) {
        List<ShopItem> items = getAllItems(guildId);
        boolean removed = items.removeIf(it -> it.id.equals(itemId));
        if (removed) save(guildId, items);
        return removed;
    }

    // ── Intern ────────────────────────────────────────────────────────────────

    private static void save(String guildId, List<ShopItem> items) {
        JsonArray arr = new JsonArray();
        for (ShopItem it : items) {
            JsonObject o = new JsonObject();
            o.addProperty("id",     it.id);
            o.addProperty("name",   it.name);
            o.addProperty("price",  it.price);
            o.addProperty("shopId", it.shopId);
            arr.add(o);
        }
        DataStore.writeString(KEY + guildId, GSON.toJson(arr));
    }

    // ── Hilfsfunktionen ───────────────────────────────────────────────────────

    public static String formatPrice(long v) {
        return String.format("%,d", v).replace(',', '.') + "$";
    }

    /** Gibt den lesbaren Shop-Namen zurück. */
    public static String shopDisplayName(String shopId) {
        return switch (shopId.toLowerCase()) {
            case "kwik-e-markt" -> "Kwik-E-Markt";
            case "baumarkt"     -> "Baumarkt";
            case "angler-shop"  -> "Angler-Shop";
            case "schwarzmarkt" -> "Schwarzmarkt";
            default             -> shopId;
        };
    }
}
