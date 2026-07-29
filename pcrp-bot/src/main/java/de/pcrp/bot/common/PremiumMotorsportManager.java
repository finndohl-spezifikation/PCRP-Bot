package de.pcrp.bot.common;

import com.google.gson.*;
import net.dv8tion.jda.api.JDA;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Member;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Premium Deluxe Motorsport — Fahrzeug-Verwaltung.
 *
 * DataStore-Keys (pro Guild):
 *   pd-vehicles-{guildId}     JSON-Array: Vehicle[]
 *   pd-info-{guildId}         JSON-Array: InfoMessage[]
 *   pd-offers-{guildId}       JSON-Array: Offer[]
 *   pd-garage-{guildId}-{userId}  JSON-Array: GarageEntry[]
 */
public final class PremiumMotorsportManager {

    private static final Logger log  = LoggerFactory.getLogger(PremiumMotorsportManager.class);
    private static final Gson   GSON = new GsonBuilder().create();

    /** Alle GTA-Online Fahrzeugklassen. */
    public static final String[] CATEGORIES = {
        "Super", "Sport", "Muscle", "Coupe", "Sedan", "SUV",
        "Compact", "Motorcycle", "Off-Road", "Industrial",
        "Utility", "Van", "Bicycle", "Helicopter", "Plane", "Boat"
    };

    /** Display-Reihenfolge in der Sidebar. */
    private static final Map<String, String> CAT_EMOJI = new LinkedHashMap<>();
    static {
        CAT_EMOJI.put("Super",       "🏎️");
        CAT_EMOJI.put("Sport",       "🚗");
        CAT_EMOJI.put("Muscle",      "💪");
        CAT_EMOJI.put("Coupe",       "🚙");
        CAT_EMOJI.put("Sedan",       "🚘");
        CAT_EMOJI.put("SUV",         "🚙");
        CAT_EMOJI.put("Compact",     "🚐");
        CAT_EMOJI.put("Motorcycle",  "🏍️");
        CAT_EMOJI.put("Off-Road",    "🛻");
        CAT_EMOJI.put("Industrial",  "🚛");
        CAT_EMOJI.put("Utility",     "🚚");
        CAT_EMOJI.put("Van",         "🚐");
        CAT_EMOJI.put("Bicycle",     "🚲");
        CAT_EMOJI.put("Helicopter",  "🚁");
        CAT_EMOJI.put("Plane",       "✈️");
        CAT_EMOJI.put("Boat",        "🛥️");
    }

    /** Cache der Auth-Resolves (Token → Guild/User Info), kurzlebig (5 min). */
    private static final Map<String, AuthInfo> AUTH_CACHE = new ConcurrentHashMap<>();
    private static final long AUTH_CACHE_TTL_MS = 5 * 60 * 1000L;

    private PremiumMotorsportManager() {}

    // ── Datenklassen ──────────────────────────────────────────────────────────

    public static class Vehicle {
        public final String id;
        public final String name;
        public final String category;
        public final String description;
        public final long   price;
        public final String imageUrl;
        public final int    stock;
        public final long   createdAt;

        public Vehicle(String id, String name, String category, String description,
                       long price, String imageUrl, int stock, long createdAt) {
            this.id = id; this.name = name; this.category = category;
            this.description = description; this.price = price;
            this.imageUrl = imageUrl == null ? "" : imageUrl;
            this.stock = stock; this.createdAt = createdAt;
        }
    }

    public static class InfoMessage {
        public final String id;
        public final String title;
        public final String text;
        public final String author;
        public final long   createdAt;

        public InfoMessage(String id, String title, String text, String author, long createdAt) {
            this.id = id; this.title = title; this.text = text;
            this.author = author; this.createdAt = createdAt;
        }
    }

    public static class Offer {
        public final String id;
        public final String title;
        public final String description;
        public final long   discountPercent;
        public final String vehicleId;
        public final long   validUntil;

        public Offer(String id, String title, String description, long discountPercent,
                     String vehicleId, long validUntil) {
            this.id = id; this.title = title; this.description = description;
            this.discountPercent = discountPercent; this.vehicleId = vehicleId;
            this.validUntil = validUntil;
        }
    }

    public static class GarageEntry {
        public final String  vin;          // Vehicle-ID (Referenz auf Katalog)
        public final String  name;         // Snapshot des Namens (falls Katalog-Eintrag mal gelöscht)
        public final String  category;
        public final long    pricePaid;
        public final long    purchasedAt;

        public GarageEntry(String vin, String name, String category, long pricePaid, long purchasedAt) {
            this.vin = vin; this.name = name; this.category = category;
            this.pricePaid = pricePaid; this.purchasedAt = purchasedAt;
        }

        /** Item-Name mit 🚘 | Prefix (Diskord-Item-Konvention für Garage). */
        public String displayName() { return "🚘 | " + name; }
    }

    public static class AuthInfo {
        public final String guildId;
        public final String userId;
        public final String displayName;
        public final boolean employee;
        public final long expiresAt;

        public AuthInfo(String guildId, String userId, String displayName, boolean employee, long expiresAt) {
            this.guildId = guildId; this.userId = userId; this.displayName = displayName;
            this.employee = employee; this.expiresAt = expiresAt;
        }

        public boolean expired() { return System.currentTimeMillis() > expiresAt; }
    }

    // ── Vehicles ──────────────────────────────────────────────────────────────

    public static List<Vehicle> getAllVehicles(String guildId) {
        return readArray(keyVehicles(guildId), Vehicle.class);
    }

    public static List<Vehicle> getVehiclesByCategory(String guildId, String category) {
        List<Vehicle> all = getAllVehicles(guildId);
        List<Vehicle> result = new ArrayList<>();
        for (Vehicle v : all) if (v.category.equalsIgnoreCase(category)) result.add(v);
        return result;
    }

    public static Vehicle getVehicleById(String guildId, String id) {
        for (Vehicle v : getAllVehicles(guildId)) if (v.id.equals(id)) return v;
        return null;
    }

    public static Vehicle createVehicle(String guildId, String name, String category, String description,
                                        long price, String imageUrl, int stock) {
        String id = UUID.randomUUID().toString().substring(0, 8);
        List<Vehicle> list = getAllVehicles(guildId);
        list.add(new Vehicle(id, name, category, description, price, imageUrl, stock, System.currentTimeMillis()));
        writeArray(keyVehicles(guildId), list);
        log.info("[PD] Vehicle created: '{}' ({}, {} $, stock {}) in guild {}", name, category, price, stock, guildId);
        return list.get(list.size() - 1);
    }

    public static boolean deleteVehicle(String guildId, String id) {
        List<Vehicle> list = getAllVehicles(guildId);
        boolean removed = list.removeIf(v -> v.id.equals(id));
        if (removed) writeArray(keyVehicles(guildId), list);
        return removed;
    }

    public static boolean adjustStock(String guildId, String id, int delta) {
        List<Vehicle> list = getAllVehicles(guildId);
        for (int i = 0; i < list.size(); i++) {
            if (list.get(i).id.equals(id)) {
                Vehicle old = list.get(i);
                int newStock = Math.max(0, old.stock + delta);
                list.set(i, new Vehicle(old.id, old.name, old.category, old.description,
                                        old.price, old.imageUrl, newStock, old.createdAt));
                writeArray(keyVehicles(guildId), list);
                return true;
            }
        }
        return false;
    }

    // ── Info Messages ─────────────────────────────────────────────────────────

    public static List<InfoMessage> getInfo(String guildId) {
        return readArray(keyInfo(guildId), InfoMessage.class);
    }

    public static InfoMessage addInfo(String guildId, String title, String text, String author) {
        String id = UUID.randomUUID().toString().substring(0, 8);
        List<InfoMessage> list = getInfo(guildId);
        list.add(0, new InfoMessage(id, title, text, author, System.currentTimeMillis())); // neuest oben
        writeArray(keyInfo(guildId), list);
        return list.get(0);
    }

    public static boolean deleteInfo(String guildId, String id) {
        List<InfoMessage> list = getInfo(guildId);
        boolean removed = list.removeIf(m -> m.id.equals(id));
        if (removed) writeArray(keyInfo(guildId), list);
        return removed;
    }

    // ── Offers ────────────────────────────────────────────────────────────────

    public static List<Offer> getOffers(String guildId) {
        return readArray(keyOffers(guildId), Offer.class);
    }

    public static Offer addOffer(String guildId, String title, String description,
                                 long discountPercent, String vehicleId, long validUntil) {
        String id = UUID.randomUUID().toString().substring(0, 8);
        List<Offer> list = getOffers(guildId);
        list.add(0, new Offer(id, title, description, discountPercent, vehicleId, validUntil));
        writeArray(keyOffers(guildId), list);
        return list.get(0);
    }

    public static boolean deleteOffer(String guildId, String id) {
        List<Offer> list = getOffers(guildId);
        boolean removed = list.removeIf(o -> o.id.equals(id));
        if (removed) writeArray(keyOffers(guildId), list);
        return removed;
    }

    // ── Garage (pro User) ──────────────────────────────────────────────────────

    public static List<GarageEntry> getGarage(String guildId, String userId) {
        return readArray(keyGarage(guildId, userId), GarageEntry.class);
    }

    /** Kauft ein Fahrzeug: Bargeld abbuchen, Stock reduzieren, Eintrag in Garage. */
    public synchronized static String purchaseVehicle(String guildId, String userId, String vehicleId) {
        Vehicle v = getVehicleById(guildId, vehicleId);
        if (v == null) return "Fahrzeug nicht gefunden.";
        if (v.stock <= 0) return "Fahrzeug ist ausverkauft.";

        long cash = BargeldManager.get(guildId, userId);
        if (cash < v.price) return "Nicht genug Bargeld. Preis: " + ShopManager.formatPrice(v.price)
                                  + ", du hast: " + BargeldManager.format(cash);

        BargeldManager.remove(guildId, userId, v.price);
        adjustStock(guildId, vehicleId, -1);

        List<GarageEntry> garage = getGarage(guildId, userId);
        garage.add(new GarageEntry(v.id, v.name, v.category, v.price, System.currentTimeMillis()));
        writeArray(keyGarage(guildId, userId), garage);
        return null; // null = OK
    }

    /** Überträgt ein Garagen-Fahrzeug an einen anderen User → dessen Garage. */
    public synchronized static String transferGarageVehicle(String guildId, String fromId, String toId,
                                                           String vin) {
        List<GarageEntry> fromGarage = getGarage(guildId, fromId);
        GarageEntry entry = null;
        for (GarageEntry e : fromGarage) {
            if (e.vin.equals(vin)) { entry = e; break; }
        }
        if (entry == null) return "Fahrzeug nicht in deiner Garage.";

        fromGarage.removeIf(e -> e.vin.equals(vin));
        writeArray(keyGarage(guildId, fromId), fromGarage);

        List<GarageEntry> toGarage = getGarage(guildId, toId);
        toGarage.add(new GarageEntry(entry.vin, entry.name, entry.category, entry.pricePaid,
                                     System.currentTimeMillis()));
        writeArray(keyGarage(guildId, toId), toGarage);
        return null;
    }

    // ── Auth (Token → AuthInfo) ──────────────────────────────────────────────

    /**
     * Validiert einen Token und liefert AuthInfo (guild, user, employee).
     * Wir nutzen den gleichen HMAC-Token-Mechanismus wie City Chat: PhoneManager.
     */
    public static AuthInfo validateToken(String token) {
        if (token == null || token.isBlank()) return null;
        AuthInfo cached = AUTH_CACHE.get(token);
        if (cached != null && !cached.expired()) return cached;

        JDA jda = BotContext.getJda();
        if (jda == null) return null;

        PhoneManager.Contract contract = PhoneManager.validateSession(token);
        if (contract == null || contract.userId == null) return null;

        Guild guild = BotContext.getGuild();
        if (guild == null) return null;

        Member member = guild.getMemberById(contract.userId);
        if (member == null) return null;

        boolean employee = hasEmployeeRole(member);
        AuthInfo info = new AuthInfo(guild.getId(), member.getId(), member.getEffectiveName(),
                                     employee, System.currentTimeMillis() + AUTH_CACHE_TTL_MS);
        AUTH_CACHE.put(token, info);
        return info;
    }

    private static boolean hasEmployeeRole(Member member) {
        long empRoleId = LoggingConfig.PD_EMPLOYEE_ROLE_ID;
        if (empRoleId == 0L) {
            // Fallback: ADMIN-permission
            return member.hasPermission(net.dv8tion.jda.api.Permission.ADMINISTRATOR);
        }
        return member.getRoles().stream().anyMatch(r -> r.getIdLong() == empRoleId);
    }

    // ── Util ─────────────────────────────────────────────────────────────────

    public static String displayCategory(String cat) {
        String emoji = CAT_EMOJI.get(cat);
        return (emoji != null ? emoji + " " : "") + cat;
    }

    public static Map<String, String> categoryEmojis() { return CAT_EMOJI; }

    private static String keyVehicles(String guildId) { return "pd-vehicles-" + guildId; }
    private static String keyInfo(String guildId)     { return "pd-info-" + guildId; }
    private static String keyOffers(String guildId)   { return "pd-offers-" + guildId; }
    private static String keyGarage(String guildId, String userId) {
        return "pd-garage-" + guildId + "-" + userId;
    }

    private static <T> List<T> readArray(String key, Class<T> type) {
        String raw = DataStore.readString(key);
        if (raw == null || raw.isBlank()) return new ArrayList<>();
        try {
            JsonArray arr = JsonParser.parseString(raw).getAsJsonArray();
            List<T> list = new ArrayList<>();
            for (JsonElement el : arr) {
                JsonObject o = el.getAsJsonObject();
                @SuppressWarnings("unchecked")
                T item = (T) deserialize(o, type);
                if (item != null) list.add(item);
            }
            return list;
        } catch (Exception e) {
            log.warn("[PD] Fehler beim Lesen von {}: {}", key, e.getMessage());
            return new ArrayList<>();
        }
    }

    private static Object deserialize(JsonObject o, Class<?> type) {
        if (type == Vehicle.class) {
            return new Vehicle(
                o.get("id").getAsString(),
                o.get("name").getAsString(),
                o.get("category").getAsString(),
                o.has("description") ? o.get("description").getAsString() : "",
                o.get("price").getAsLong(),
                o.has("imageUrl") ? o.get("imageUrl").getAsString() : "",
                o.has("stock") ? o.get("stock").getAsInt() : 0,
                o.has("createdAt") ? o.get("createdAt").getAsLong() : System.currentTimeMillis()
            );
        }
        if (type == InfoMessage.class) {
            return new InfoMessage(
                o.get("id").getAsString(),
                o.has("title") ? o.get("title").getAsString() : "Info",
                o.get("text").getAsString(),
                o.has("author") ? o.get("author").getAsString() : "",
                o.has("createdAt") ? o.get("createdAt").getAsLong() : System.currentTimeMillis()
            );
        }
        if (type == Offer.class) {
            return new Offer(
                o.get("id").getAsString(),
                o.get("title").getAsString(),
                o.has("description") ? o.get("description").getAsString() : "",
                o.has("discountPercent") ? o.get("discountPercent").getAsLong() : 0,
                o.has("vehicleId") && !o.get("vehicleId").isJsonNull() ? o.get("vehicleId").getAsString() : null,
                o.has("validUntil") ? o.get("validUntil").getAsLong() : 0
            );
        }
        if (type == GarageEntry.class) {
            return new GarageEntry(
                o.get("vin").getAsString(),
                o.has("name") ? o.get("name").getAsString() : "Unbekannt",
                o.has("category") ? o.get("category").getAsString() : "",
                o.has("pricePaid") ? o.get("pricePaid").getAsLong() : 0,
                o.has("purchasedAt") ? o.get("purchasedAt").getAsLong() : System.currentTimeMillis()
            );
        }
        return null;
    }

    private static void writeArray(String key, List<?> list) {
        JsonArray arr = new JsonArray();
        for (Object item : list) {
            JsonObject o = new JsonObject();
            if (item instanceof Vehicle v) {
                o.addProperty("id", v.id);
                o.addProperty("name", v.name);
                o.addProperty("category", v.category);
                o.addProperty("description", v.description);
                o.addProperty("price", v.price);
                o.addProperty("imageUrl", v.imageUrl);
                o.addProperty("stock", v.stock);
                o.addProperty("createdAt", v.createdAt);
            } else if (item instanceof InfoMessage m) {
                o.addProperty("id", m.id);
                o.addProperty("title", m.title);
                o.addProperty("text", m.text);
                o.addProperty("author", m.author);
                o.addProperty("createdAt", m.createdAt);
            } else if (item instanceof Offer of) {
                o.addProperty("id", of.id);
                o.addProperty("title", of.title);
                o.addProperty("description", of.description);
                o.addProperty("discountPercent", of.discountPercent);
                if (of.vehicleId != null) o.addProperty("vehicleId", of.vehicleId);
                o.addProperty("validUntil", of.validUntil);
            } else if (item instanceof GarageEntry g) {
                o.addProperty("vin", g.vin);
                o.addProperty("name", g.name);
                o.addProperty("category", g.category);
                o.addProperty("pricePaid", g.pricePaid);
                o.addProperty("purchasedAt", g.purchasedAt);
            }
            arr.add(o);
        }
        DataStore.writeString(key, GSON.toJson(arr));
    }
}
