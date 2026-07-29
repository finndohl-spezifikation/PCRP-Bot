package de.pcrp.bot.common;

import com.google.gson.*;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.entities.MessageEmbed;

import java.util.*;

/**
 * Verwaltet Spieler-Inventare.
 * DataStore-Key: {@code inventory-{guildId}-{userId}} → JSON-Array [{name, quantity}]
 */
public final class InventoryManager {

    private static final Gson GSON = new Gson();

    // ── Datenklasse ───────────────────────────────────────────────────────────

    public static class Item {
        public String  name;
        public int     quantity;
        public boolean hidden;   // Optional — Legacy-Daten ohne Feld werden als sichtbar behandelt
        public Item(String name, int quantity) { this.name = name; this.quantity = quantity; }
    }

    public static class TransferError extends RuntimeException {
        public TransferError(String msg) { super(msg); }
    }

    // ── Schlüssel ─────────────────────────────────────────────────────────────

    private static String key(String guildId, String userId) {
        return "inventory-" + guildId + "-" + userId;
    }

    // ── Lesen / Schreiben ─────────────────────────────────────────────────────

    public static List<Item> getInventory(String guildId, String userId) {
        String raw = DataStore.readString(key(guildId, userId));
        List<Item> list = new ArrayList<>();
        if (raw == null || raw.isBlank()) return list;
        try {
            JsonArray arr = GSON.fromJson(raw, JsonArray.class);
            for (JsonElement el : arr) {
                JsonObject o = el.getAsJsonObject();
                list.add(new Item(o.get("name").getAsString(), o.get("quantity").getAsInt()));
            }
        } catch (Exception ignored) {}
        return list;
    }

    private static void saveInventory(String guildId, String userId, List<Item> items) {
        JsonArray arr = new JsonArray();
        for (Item it : items) {
            JsonObject o = new JsonObject();
            o.addProperty("name",     it.name);
            o.addProperty("quantity", it.quantity);
            o.addProperty("hidden",   it.hidden);
            arr.add(o);
        }
        DataStore.writeString(key(guildId, userId), GSON.toJson(arr));
    }

    private static final java.util.stream.Collector<Item, ?, List<Item>> TO_LIST =
        java.util.stream.Collectors.toList();

    // ── Operationen ───────────────────────────────────────────────────────────

    /**
     * Prüft ob ein gespeicherter Item-Name einem Suchbegriff entspricht.
     * Unterstützt exakten Vergleich und das "🎫 | ItemName"-Präfix-Format.
     */
    public static boolean nameMatches(String stored, String search) {
        String s = search.trim();
        if (stored.equalsIgnoreCase(s)) return true;
        int pipe = stored.lastIndexOf('|');
        return pipe >= 0 && stored.substring(pipe + 1).trim().equalsIgnoreCase(s);
    }

    public static synchronized void addItem(String guildId, String userId, String itemName, int qty) {
        String name = itemName.trim();
        List<Item> inv = getInventory(guildId, userId);
        Optional<Item> existing = inv.stream().filter(i -> i.name.equalsIgnoreCase(name)).findFirst();
        if (existing.isPresent()) {
            existing.get().quantity += qty;
        } else {
            inv.add(new Item(name, qty));
        }
        saveInventory(guildId, userId, inv);
    }

    /**
     * Zieht qty ab. Gibt false zurück wenn nicht genug vorhanden.
     * Unterstützt Emoji-Präfix: Suche nach "Rubbellos" trifft auch "🎫 | Rubbellos".
     */
    public static synchronized boolean removeItem(String guildId, String userId, String itemName, int qty) {
        List<Item> inv = getInventory(guildId, userId);
        Optional<Item> existing = inv.stream().filter(i -> nameMatches(i.name, itemName)).findFirst();
        if (existing.isEmpty() || existing.get().quantity < qty) return false;
        existing.get().quantity -= qty;
        if (existing.get().quantity == 0) inv.removeIf(i -> nameMatches(i.name, itemName));
        saveInventory(guildId, userId, inv);
        return true;
    }

    /**
     * Übergibt mehrere Items von einem Spieler an einen anderen.
     * @param transfers Liste von {name, qty}
     * @throws TransferError wenn ein Item nicht vorhanden / nicht genug
     */
    public static synchronized void transfer(
            String guildId, String fromId, String toId, List<Item> transfers) {
        List<Item> fromInv = getInventory(guildId, fromId);
        // Alle Mengen vorab prüfen
        for (Item t : transfers) {
            int have = fromInv.stream()
                .filter(i -> i.name.equalsIgnoreCase(t.name))
                .mapToInt(i -> i.quantity).sum();
            if (have < t.quantity) {
                throw new TransferError("Nicht genug **" + t.name + "** im Inventar (vorhanden: " + have + ").");
            }
        }
        // Abziehen
        for (Item t : transfers) removeItem(guildId, fromId, t.name, t.quantity);
        // Hinzufügen
        for (Item t : transfers) addItem(guildId, toId, t.name, t.quantity);
    }

    /**
     * Parst "Bargeld: 500, Waffe: 1" → Liste von Items.
     * @throws TransferError bei ungültigem Format
     */
    public static List<Item> parseTransferInput(String input) {
        List<Item> result = new ArrayList<>();
        String[] parts = input.split(",");
        for (String part : parts) {
            String[] kv = part.trim().split(":", 2);
            if (kv.length != 2) throw new TransferError(
                "Ungültiges Format bei `" + part.trim() + "`. Bitte verwende: **ItemName: Menge**");
            String name = kv[0].trim();
            int qty;
            try { qty = Integer.parseInt(kv[1].trim()); }
            catch (NumberFormatException e) {
                throw new TransferError("Ungültige Menge bei `" + part.trim() + "`.");
            }
            if (qty <= 0) throw new TransferError("Menge muss größer als 0 sein (`" + name + "`).");
            result.add(new Item(name, qty));
        }
        if (result.isEmpty()) throw new TransferError("Keine Items angegeben.");
        return result;
    }

    // ── Embed ─────────────────────────────────────────────────────────────────

    public static MessageEmbed buildEmbed(String guildId, String userId, String displayName) {
        List<Item> inv = getInventory(guildId, userId);
        // Bargeld ist kein Inventar-Item mehr — Altdaten ausfiltern
        inv.removeIf(it -> nameMatches(it.name, "Bargeld"));
        EmbedBuilder eb = EmbedFactory.create()
            .setTitle("🎒 Rucksack — " + displayName);

        if (inv.isEmpty()) {
            eb.setDescription("Dein Rucksack ist leer.");
        } else {
            StringBuilder sb = new StringBuilder();
            for (Item it : inv) {
                sb.append("• **").append(it.name).append("** × ").append(it.quantity).append("\n");
            }
            eb.setDescription(sb.toString());
        }
        return eb.build();
    }

    /**
     * Erweiterte Embed-Variante: versteckte Items werden durchgestrichen dargestellt
     * mit Hinweis „⬇ Item Versteckt". Der bestehende {@link #buildEmbed} bleibt unverändert.
     */
    public static MessageEmbed buildEmbedWithHidden(String guildId, String userId, String displayName) {
        List<Item> inv = getInventory(guildId, userId);
        inv.removeIf(it -> nameMatches(it.name, "Bargeld"));

        EmbedBuilder eb = EmbedFactory.create()
            .setTitle("🎒 Rucksack — " + displayName);

        List<Item> visible = new ArrayList<>();
        List<Item> hidden  = new ArrayList<>();
        for (Item it : inv) {
            (it.hidden ? hidden : visible).add(it);
        }

        if (visible.isEmpty() && hidden.isEmpty()) {
            eb.setDescription("Dein Rucksack ist leer.");
            return eb.build();
        }

        StringBuilder sb = new StringBuilder();
        if (visible.isEmpty()) {
            sb.append("_Keine sichtbaren Items._\n");
        } else {
            sb.append("**Sichtbar:**\n");
            for (Item it : visible) {
                sb.append("• **").append(it.name).append("** × ").append(it.quantity).append("\n");
            }
        }

        if (!hidden.isEmpty()) {
            sb.append("\n**Versteckt:**\n");
            for (Item it : hidden) {
                sb.append("• ~~").append(it.name).append("~~ × ").append(it.quantity).append("\n");
                sb.append("  ⬇ Item Versteckt\n");
            }
        }

        eb.setDescription(sb.toString());
        return eb.build();
    }

    /**
     * Liefert nur die aktuell versteckten Items eines Spielers (mit quantity > 0).
     * Bargeld wird wie in {@link #buildEmbed} herausgefiltert.
     */
    public static List<Item> getHiddenItems(String guildId, String userId) {
        return getInventory(guildId, userId).stream()
            .filter(i -> i.hidden && i.quantity > 0 && !nameMatches(i.name, "Bargeld"))
            .collect(java.util.stream.Collectors.toList());
    }

    /**
     * Liefert nur die aktuell sichtbaren Items (Kandidaten für /verstecken).
     */
    public static List<Item> getVisibleItems(String guildId, String userId) {
        return getInventory(guildId, userId).stream()
            .filter(i -> !i.hidden && i.quantity > 0 && !nameMatches(i.name, "Bargeld"))
            .collect(java.util.stream.Collectors.toList());
    }

    /**
     * Setzt das hidden-Flag für alle Items mit passendem Namen auf den gewünschten Wert.
     * Mehrere Items mit gleichem Namen werden alle gleichzeitig behandelt (idempotent).
     */
    public static synchronized void setHidden(String guildId, String userId, String itemName, boolean hidden) {
        List<Item> inv = getInventory(guildId, userId);
        boolean changed = false;
        for (Item it : inv) {
            if (nameMatches(it.name, itemName)) {
                it.hidden = hidden;
                changed = true;
            }
        }
        if (changed) saveInventory(guildId, userId, inv);
    }

    private InventoryManager() {}
}
