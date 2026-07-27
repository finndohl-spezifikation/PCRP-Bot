package de.pcrp.bot.web;

import com.google.gson.*;
import de.pcrp.bot.common.*;
import io.javalin.http.Context;

import java.time.Instant;
import java.util.*;

/**
 * Citygram API – Instagram-ähnliches Foto-/Story-Netzwerk.
 *
 * Routen (in WebServer registriert):
 *   POST   /api/citygram/auth
 *   GET    /api/citygram/me
 *   PUT    /api/citygram/profile
 *   GET    /api/citygram/avatar/{phone}
 *   GET    /api/citygram/profile/{phone}
 *   GET    /api/citygram/feed
 *   GET    /api/citygram/posts/{phone}
 *   POST   /api/citygram/post
 *   DELETE /api/citygram/post/{postId}
 *   GET    /api/citygram/img/{postId}
 *   POST   /api/citygram/like/{postId}
 *   GET    /api/citygram/comments/{postId}
 *   POST   /api/citygram/comment/{postId}
 *   DELETE /api/citygram/comment/{postId}/{commentId}
 *   POST   /api/citygram/follow/{phone}
 *   GET    /api/citygram/search
 *   GET    /api/citygram/stories
 *   POST   /api/citygram/story
 *   GET    /api/citygram/story-img/{storyId}
 */
public final class CityCitygramHandler {

    private static final Gson GSON       = new GsonBuilder().create();
    private static final long STORY_TTL  = 24 * 3600_000L;

    private CityCitygramHandler() {}

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static String guildId() {
        net.dv8tion.jda.api.entities.Guild g = BotContext.getGuild();
        return g != null ? g.getId() : "unknown";
    }

    private static JsonObject parseBody(Context ctx) {
        try { return GSON.fromJson(ctx.body(), JsonObject.class); }
        catch (Exception e) { return null; }
    }

    private static String str(JsonObject o, String k) {
        return o != null && o.has(k) && !o.get(k).isJsonNull() ? o.get(k).getAsString() : null;
    }

    private static String err(String msg) {
        return "{\"error\":\"" + msg.replace("\"","\\\"") + "\"}";
    }

    private static String norm(String phone) {
        return phone == null ? "" : phone.replaceAll("[^0-9]", "");
    }

    private static PhoneManager.Contract auth(Context ctx) {
        String token = ctx.header("Authorization");
        if (token != null && token.startsWith("Bearer ")) token = token.substring(7).trim();
        if (token == null || token.isBlank()) token = ctx.queryParam("token");
        if (token == null || token.isBlank()) { ctx.status(401).result(err("Nicht authentifiziert")); return null; }
        PhoneManager.Contract c = PhoneManager.validateSession(token);
        if (c == null) { ctx.status(401).result(err("Session ungültig")); return null; }
        return c;
    }

    // ── Profile helpers ───────────────────────────────────────────────────────

    private static JsonObject loadProfile(String guildId, String phone) {
        String s = DataStore.readString("cg-profile-" + guildId + "-" + norm(phone));
        if (s == null || s.isBlank()) return new JsonObject();
        try { return GSON.fromJson(s, JsonObject.class); } catch (Exception e) { return new JsonObject(); }
    }

    private static void saveProfile(String guildId, String phone, JsonObject p) {
        DataStore.writeString("cg-profile-" + guildId + "-" + norm(phone), GSON.toJson(p));
    }

    private static String pStr(JsonObject p, String k, String def) {
        return p != null && p.has(k) && !p.get(k).isJsonNull() ? p.get(k).getAsString() : def;
    }

    // ── Post helpers ──────────────────────────────────────────────────────────

    private static JsonArray loadPosts(String guildId) {
        String s = DataStore.readString("cg-posts-" + guildId);
        if (s == null || s.isBlank()) return new JsonArray();
        try { return GSON.fromJson(s, JsonArray.class); } catch (Exception e) { return new JsonArray(); }
    }

    private static void savePosts(String guildId, JsonArray a) {
        DataStore.writeString("cg-posts-" + guildId, GSON.toJson(a));
    }

    private static JsonArray loadLikes(String guildId, String postId) {
        String s = DataStore.readString("cg-likes-" + guildId + "-" + postId);
        if (s == null) return new JsonArray();
        try { return GSON.fromJson(s, JsonArray.class); } catch (Exception e) { return new JsonArray(); }
    }

    private static void saveLikes(String guildId, String postId, JsonArray a) {
        DataStore.writeString("cg-likes-" + guildId + "-" + postId, GSON.toJson(a));
    }

    private static JsonArray loadComments(String guildId, String postId) {
        String s = DataStore.readString("cg-comments-" + guildId + "-" + postId);
        if (s == null) return new JsonArray();
        try { return GSON.fromJson(s, JsonArray.class); } catch (Exception e) { return new JsonArray(); }
    }

    private static JsonArray loadFollowing(String guildId, String phone) {
        String s = DataStore.readString("cg-following-" + guildId + "-" + norm(phone));
        if (s == null) return new JsonArray();
        try { return GSON.fromJson(s, JsonArray.class); } catch (Exception e) { return new JsonArray(); }
    }

    private static void saveFollowing(String guildId, String phone, JsonArray a) {
        DataStore.writeString("cg-following-" + guildId + "-" + norm(phone), GSON.toJson(a));
    }

    private static JsonObject enrich(JsonObject post, String guildId, String myPhone) {
        String pid = str(post, "id");
        JsonArray likes = loadLikes(guildId, pid);
        JsonArray comments = loadComments(guildId, pid);
        boolean liked = false;
        String me = norm(myPhone);
        for (JsonElement e : likes) if (me.equals(norm(e.getAsString()))) { liked = true; break; }
        JsonObject out = post.deepCopy();
        out.addProperty("likeCount", likes.size());
        out.addProperty("liked", liked);
        out.addProperty("commentCount", comments.size());
        return out;
    }

    private static int followerCount(String guildId, String phone) {
        String normT = norm(phone);
        int count = 0;
        for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId)) {
            for (JsonElement f : loadFollowing(guildId, ct.phoneNumber))
                if (normT.equals(norm(f.getAsString()))) { count++; break; }
        }
        return count;
    }

    private static int postCount(String guildId, String phone) {
        String normT = norm(phone);
        int c = 0;
        for (JsonElement e : loadPosts(guildId))
            if (normT.equals(norm(str(e.getAsJsonObject(), "phone")))) c++;
        return c;
    }

    private static void serveImage(Context ctx, String b64) {
        if (b64 == null || b64.isBlank()) { ctx.status(404).result("Not found"); return; }
        if (b64.startsWith("data:")) {
            int c = b64.indexOf(',');
            if (c >= 0) {
                String mime = b64.substring(5, b64.indexOf(';'));
                ctx.contentType(mime).result(Base64.getDecoder().decode(b64.substring(c + 1)));
                return;
            }
        }
        ctx.status(400).result("Bad image");
    }

    // ── Auth ──────────────────────────────────────────────────────────────────

    public static void handleAuth(Context ctx) {
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).result(err("Ungültiger Body")); return; }
        String phone = str(body, "phoneNumber");
        String pin   = str(body, "safePin");
        if (phone == null || pin == null) { ctx.status(400).result(err("Zugangsdaten fehlen")); return; }
        String guildId = guildId();
        PhoneManager.Contract c = PhoneManager.getContractByNumber(guildId, phone);
        if (c == null) {
            // try by normalized number
            String normP = norm(phone);
            for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId))
                if (normP.equals(norm(ct.phoneNumber))) { c = ct; break; }
        }
        if (c == null || !c.safePin.equals(pin)) { ctx.status(401).result(err("Ungültige Zugangsdaten")); return; }
        String token = PhoneManager.createSession(guildId, c.phoneNumber);
        JsonObject profile = loadProfile(guildId, c.phoneNumber);
        JsonObject res = new JsonObject();
        res.addProperty("token",    token);
        res.addProperty("phone",    norm(c.phoneNumber));
        res.addProperty("username", pStr(profile, "username", c.displayName()));
        ctx.json(GSON.toJson(res));
    }

    // ── Profile ───────────────────────────────────────────────────────────────

    public static void handleGetMe(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String guildId = guildId();
        JsonObject profile = loadProfile(guildId, c.phoneNumber);
        JsonObject res = new JsonObject();
        res.addProperty("phone",          norm(c.phoneNumber));
        res.addProperty("username",       pStr(profile, "username", c.displayName()));
        res.addProperty("bio",            pStr(profile, "bio", ""));
        res.addProperty("website",        pStr(profile, "website", ""));
        res.addProperty("hasAvatar",           !pStr(profile, "avatar", "").isEmpty());
        res.addProperty("postCount",           postCount(guildId, c.phoneNumber));
        res.addProperty("followerCount",       followerCount(guildId, c.phoneNumber));
        res.addProperty("followingCount",      loadFollowing(guildId, c.phoneNumber).size());
        res.addProperty("isPrivate",           profile.has("isPrivate") && profile.get("isPrivate").getAsBoolean());
        res.addProperty("pendingRequestCount", loadFollowRequests(guildId, c.phoneNumber).size());
        ctx.json(GSON.toJson(res));
    }

    public static void handleGetProfile(Context ctx) {
        PhoneManager.Contract me = auth(ctx); if (me == null) return;
        String phone = ctx.pathParam("phone");
        String guildId = guildId();
        String normT = norm(phone);
        PhoneManager.Contract c = null;
        for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId))
            if (normT.equals(norm(ct.phoneNumber))) { c = ct; break; }
        if (c == null) { ctx.status(404).result(err("Nutzer nicht gefunden")); return; }
        JsonObject profile = loadProfile(guildId, c.phoneNumber);
        // am I following?
        boolean isFollowing = false;
        for (JsonElement f : loadFollowing(guildId, me.phoneNumber))
            if (normT.equals(norm(f.getAsString()))) { isFollowing = true; break; }
        JsonObject res = new JsonObject();
        res.addProperty("phone",          normT);
        res.addProperty("username",       pStr(profile, "username", c.displayName()));
        res.addProperty("bio",            pStr(profile, "bio", ""));
        res.addProperty("website",        pStr(profile, "website", ""));
        res.addProperty("hasAvatar",      !pStr(profile, "avatar", "").isEmpty());
        res.addProperty("postCount",      postCount(guildId, c.phoneNumber));
        res.addProperty("followerCount",  followerCount(guildId, c.phoneNumber));
        res.addProperty("followingCount", loadFollowing(guildId, c.phoneNumber).size());
        boolean isPrivate = profile.has("isPrivate") && profile.get("isPrivate").getAsBoolean();
        boolean isPending = false;
        for (JsonElement e : loadFollowRequests(guildId, normT))
            if (norm(me.phoneNumber).equals(norm(e.getAsString()))) { isPending = true; break; }
        res.addProperty("isFollowing",    isFollowing);
        res.addProperty("isMe",           norm(me.phoneNumber).equals(normT));
        res.addProperty("isPrivate",      isPrivate);
        res.addProperty("isPending",      isPending);
        ctx.json(GSON.toJson(res));
    }

    public static void handleUpdateProfile(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).result(err("Ungültiger Body")); return; }
        String guildId = guildId();
        JsonObject p = loadProfile(guildId, c.phoneNumber);
        if (body.has("username"))  p.addProperty("username",  str(body, "username"));
        if (body.has("bio"))       p.addProperty("bio",       str(body, "bio"));
        if (body.has("website"))   p.addProperty("website",   str(body, "website"));
        if (body.has("avatar"))    p.addProperty("avatar",    str(body, "avatar"));
        if (body.has("isPrivate")) p.addProperty("isPrivate", body.get("isPrivate").getAsBoolean());
        saveProfile(guildId, c.phoneNumber, p);
        ctx.json("{\"ok\":true}");
    }

    public static void handleGetAvatar(Context ctx) {
        String phone = ctx.pathParam("phone");
        // auth check
        String token = ctx.queryParam("token");
        if (token == null) { String h = ctx.header("Authorization"); if (h != null && h.startsWith("Bearer ")) token = h.substring(7).trim(); }
        if (PhoneManager.validateSession(token) == null) { ctx.status(401).result("Unauthorized"); return; }
        String normP = norm(phone);
        for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId())) {
            if (normP.equals(norm(ct.phoneNumber))) {
                serveImage(ctx, pStr(loadProfile(guildId(), ct.phoneNumber), "avatar", ""));
                return;
            }
        }
        ctx.status(404).result("Not found");
    }

    // ── Feed ──────────────────────────────────────────────────────────────────

    public static void handleFeed(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String guildId = guildId();
        JsonArray all = loadPosts(guildId);
        List<JsonObject> list = new ArrayList<>();
        for (int i = all.size() - 1; i >= 0; i--)
            list.add(enrich(all.get(i).getAsJsonObject(), guildId, c.phoneNumber));
        if (list.size() > 60) list = list.subList(0, 60);
        ctx.json(GSON.toJson(list));
    }

    // ── User posts ────────────────────────────────────────────────────────────

    public static void handleGetUserPosts(Context ctx) {
        PhoneManager.Contract me = auth(ctx); if (me == null) return;
        String normT = norm(ctx.pathParam("phone"));
        String guildId = guildId();
        JsonArray all = loadPosts(guildId);
        List<JsonObject> list = new ArrayList<>();
        for (int i = all.size() - 1; i >= 0; i--) {
            JsonObject p = all.get(i).getAsJsonObject();
            if (normT.equals(norm(str(p, "phone")))) list.add(enrich(p, guildId, me.phoneNumber));
        }
        ctx.json(GSON.toJson(list));
    }

    // ── Create / Delete post ──────────────────────────────────────────────────

    public static void handleCreatePost(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).result(err("Ungültiger Body")); return; }
        String image   = str(body, "image");
        String caption = str(body, "caption");
        if (image == null || image.isEmpty()) { ctx.status(400).result(err("Kein Bild")); return; }
        String guildId = guildId();
        String postId  = UUID.randomUUID().toString().replace("-","").substring(0,16);
        DataStore.writeString("cg-img-" + guildId + "-" + postId, image);
        JsonObject profile = loadProfile(guildId, c.phoneNumber);
        JsonObject post = new JsonObject();
        post.addProperty("id",        postId);
        post.addProperty("phone",     norm(c.phoneNumber));
        post.addProperty("username",  pStr(profile, "username", c.displayName()));
        post.addProperty("hasAvatar", !pStr(profile, "avatar", "").isEmpty());
        post.addProperty("caption",   caption != null ? caption : "");
        post.addProperty("ts",        Instant.now().toEpochMilli());
        JsonArray all = loadPosts(guildId);
        all.add(post);
        savePosts(guildId, all);
        ctx.json(GSON.toJson(enrich(post, guildId, c.phoneNumber)));
    }

    public static void handleDeletePost(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String postId = ctx.pathParam("postId");
        String guildId = guildId();
        String normMe = norm(c.phoneNumber);
        JsonArray all = loadPosts(guildId);
        for (int i = 0; i < all.size(); i++) {
            JsonObject p = all.get(i).getAsJsonObject();
            if (postId.equals(str(p, "id")) && normMe.equals(str(p, "phone"))) {
                all.remove(i);
                savePosts(guildId, all);
                DataStore.deleteKey("cg-img-" + guildId + "-" + postId);
                DataStore.deleteKey("cg-likes-" + guildId + "-" + postId);
                DataStore.deleteKey("cg-comments-" + guildId + "-" + postId);
                ctx.json("{\"ok\":true}"); return;
            }
        }
        ctx.status(404).result(err("Nicht gefunden"));
    }

    public static void handleGetPostImage(Context ctx) {
        String postId = ctx.pathParam("postId");
        String token = ctx.queryParam("token");
        if (token == null) { String h = ctx.header("Authorization"); if (h != null && h.startsWith("Bearer ")) token = h.substring(7).trim(); }
        if (PhoneManager.validateSession(token) == null) { ctx.status(401).result("Unauthorized"); return; }
        serveImage(ctx, DataStore.readString("cg-img-" + guildId() + "-" + postId));
    }

    // ── Likes ─────────────────────────────────────────────────────────────────

    public static void handleToggleLike(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String postId = ctx.pathParam("postId");
        String guildId = guildId();
        String normMe = norm(c.phoneNumber);
        JsonArray likes = loadLikes(guildId, postId);
        boolean wasLiked = false;
        for (int i = 0; i < likes.size(); i++) {
            if (normMe.equals(norm(likes.get(i).getAsString()))) { likes.remove(i); wasLiked = true; break; }
        }
        if (!wasLiked) likes.add(normMe);
        saveLikes(guildId, postId, likes);
        JsonObject res = new JsonObject();
        res.addProperty("liked",     !wasLiked);
        res.addProperty("likeCount", likes.size());
        ctx.json(GSON.toJson(res));
    }

    // ── Comments ──────────────────────────────────────────────────────────────

    public static void handleGetComments(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String raw = DataStore.readString("cg-comments-" + guildId() + "-" + ctx.pathParam("postId"));
        ctx.json(raw != null ? raw : "[]");
    }

    public static void handleAddComment(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String postId = ctx.pathParam("postId");
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).result(err("Ungültiger Body")); return; }
        String text = str(body, "text");
        if (text == null || text.isBlank()) { ctx.status(400).result(err("Text fehlt")); return; }
        String guildId = guildId();
        JsonObject profile = loadProfile(guildId, c.phoneNumber);
        JsonObject comment = new JsonObject();
        comment.addProperty("id",       UUID.randomUUID().toString().replace("-","").substring(0,12));
        comment.addProperty("phone",    norm(c.phoneNumber));
        comment.addProperty("username", pStr(profile, "username", c.displayName()));
        comment.addProperty("text",     text);
        comment.addProperty("ts",       Instant.now().toEpochMilli());
        String key = "cg-comments-" + guildId + "-" + postId;
        JsonArray comments = loadComments(guildId, postId);
        comments.add(comment);
        DataStore.writeString(key, GSON.toJson(comments));
        ctx.json(GSON.toJson(comment));
    }

    public static void handleDeleteComment(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String postId    = ctx.pathParam("postId");
        String commentId = ctx.pathParam("commentId");
        String guildId   = guildId();
        String normMe    = norm(c.phoneNumber);
        // check if post author (can delete any comment)
        boolean isAuthor = false;
        for (JsonElement e : loadPosts(guildId)) {
            JsonObject p = e.getAsJsonObject();
            if (postId.equals(str(p, "id")) && normMe.equals(str(p, "phone"))) { isAuthor = true; break; }
        }
        JsonArray comments = loadComments(guildId, postId);
        for (int i = 0; i < comments.size(); i++) {
            JsonObject cm = comments.get(i).getAsJsonObject();
            if (commentId.equals(str(cm, "id")) && (normMe.equals(str(cm, "phone")) || isAuthor)) {
                comments.remove(i);
                DataStore.writeString("cg-comments-" + guildId + "-" + postId, GSON.toJson(comments));
                ctx.json("{\"ok\":true}"); return;
            }
        }
        ctx.status(404).result(err("Nicht gefunden"));
    }

    // ── Block helpers ─────────────────────────────────────────────────────────

    private static JsonArray loadBlocked(String guildId, String phone) {
        String s = DataStore.readString("cg-blocked-" + guildId + "-" + norm(phone));
        if (s == null) return new JsonArray();
        try { return GSON.fromJson(s, JsonArray.class); } catch (Exception e) { return new JsonArray(); }
    }

    private static void saveBlocked(String guildId, String phone, JsonArray a) {
        DataStore.writeString("cg-blocked-" + guildId + "-" + norm(phone), GSON.toJson(a));
    }

    private static boolean isBlocked(String guildId, String byPhone, String ofPhone) {
        for (JsonElement e : loadBlocked(guildId, byPhone))
            if (norm(ofPhone).equals(norm(e.getAsString()))) return true;
        return false;
    }

    // ── Follow-request helpers ────────────────────────────────────────────────

    private static JsonArray loadFollowRequests(String guildId, String phone) {
        String s = DataStore.readString("cg-follow-req-" + guildId + "-" + norm(phone));
        if (s == null) return new JsonArray();
        try { return GSON.fromJson(s, JsonArray.class); } catch (Exception e) { return new JsonArray(); }
    }

    private static void saveFollowRequests(String guildId, String phone, JsonArray a) {
        DataStore.writeString("cg-follow-req-" + guildId + "-" + norm(phone), GSON.toJson(a));
    }

    // ── Follow ────────────────────────────────────────────────────────────────

    public static void handleToggleFollow(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String normT  = norm(ctx.pathParam("phone"));
        String normMe = norm(c.phoneNumber);
        if (normMe.equals(normT)) { ctx.status(400).result(err("Nicht möglich")); return; }
        String guildId = guildId();

        // Blocked?
        if (isBlocked(guildId, normT, normMe)) { ctx.status(403).result(err("Nicht möglich")); return; }

        JsonArray following = loadFollowing(guildId, c.phoneNumber);
        boolean was = false;
        for (int i = 0; i < following.size(); i++)
            if (normT.equals(norm(following.get(i).getAsString()))) { following.remove(i); was = true; break; }

        JsonObject res = new JsonObject();

        if (!was) {
            // Check if target account is private
            JsonObject targetProfile = loadProfile(guildId, normT);
            boolean isPrivate = targetProfile.has("isPrivate") && targetProfile.get("isPrivate").getAsBoolean();
            if (isPrivate) {
                // Check if already requested
                JsonArray reqs = loadFollowRequests(guildId, normT);
                boolean alreadyPending = false;
                for (JsonElement e : reqs)
                    if (normMe.equals(norm(e.getAsString()))) { alreadyPending = true; break; }
                if (!alreadyPending) { reqs.add(normMe); saveFollowRequests(guildId, normT, reqs); }
                res.addProperty("following", false);
                res.addProperty("pending", true);
                ctx.json(GSON.toJson(res)); return;
            }
            following.add(normT);
        } else {
            // Cancel pending request if exists
            JsonArray reqs = loadFollowRequests(guildId, normT);
            for (int i = 0; i < reqs.size(); i++)
                if (normMe.equals(norm(reqs.get(i).getAsString()))) { reqs.remove(i); break; }
            saveFollowRequests(guildId, normT, reqs);
        }

        saveFollowing(guildId, c.phoneNumber, following);
        res.addProperty("following", !was);
        res.addProperty("pending", false);
        ctx.json(GSON.toJson(res));
    }

    public static void handleGetFollowers(Context ctx) {
        PhoneManager.Contract me = auth(ctx); if (me == null) return;
        String normT  = norm(ctx.pathParam("phone"));
        String guildId = guildId();
        List<JsonObject> list = new ArrayList<>();
        for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId)) {
            for (JsonElement f : loadFollowing(guildId, ct.phoneNumber)) {
                if (normT.equals(norm(f.getAsString()))) {
                    JsonObject profile = loadProfile(guildId, ct.phoneNumber);
                    JsonObject u = new JsonObject();
                    u.addProperty("phone",     norm(ct.phoneNumber));
                    u.addProperty("username",  pStr(profile, "username", ct.displayName()));
                    u.addProperty("hasAvatar", !pStr(profile, "avatar", "").isEmpty());
                    list.add(u); break;
                }
            }
        }
        ctx.json(GSON.toJson(list));
    }

    public static void handleGetFollowing(Context ctx) {
        PhoneManager.Contract me = auth(ctx); if (me == null) return;
        String normT   = norm(ctx.pathParam("phone"));
        String guildId = guildId();
        PhoneManager.Contract target = null;
        for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId))
            if (normT.equals(norm(ct.phoneNumber))) { target = ct; break; }
        if (target == null) { ctx.status(404).result(err("Nicht gefunden")); return; }
        List<JsonObject> list = new ArrayList<>();
        for (JsonElement f : loadFollowing(guildId, target.phoneNumber)) {
            String fp = norm(f.getAsString());
            for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId)) {
                if (fp.equals(norm(ct.phoneNumber))) {
                    JsonObject profile = loadProfile(guildId, ct.phoneNumber);
                    JsonObject u = new JsonObject();
                    u.addProperty("phone",     fp);
                    u.addProperty("username",  pStr(profile, "username", ct.displayName()));
                    u.addProperty("hasAvatar", !pStr(profile, "avatar", "").isEmpty());
                    list.add(u); break;
                }
            }
        }
        ctx.json(GSON.toJson(list));
    }

    // ── Block ─────────────────────────────────────────────────────────────────

    public static void handleToggleBlock(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String normT  = norm(ctx.pathParam("phone"));
        String normMe = norm(c.phoneNumber);
        if (normMe.equals(normT)) { ctx.status(400).result(err("Nicht möglich")); return; }
        String guildId = guildId();
        JsonArray blocked = loadBlocked(guildId, normMe);
        boolean was = false;
        for (int i = 0; i < blocked.size(); i++)
            if (normT.equals(norm(blocked.get(i).getAsString()))) { blocked.remove(i); was = true; break; }
        if (!was) {
            blocked.add(normT);
            // Remove follows both ways
            JsonArray myF = loadFollowing(guildId, normMe);
            for (int i = 0; i < myF.size(); i++)
                if (normT.equals(norm(myF.get(i).getAsString()))) { myF.remove(i); break; }
            saveFollowing(guildId, normMe, myF);
            JsonArray theirF = loadFollowing(guildId, normT);
            for (int i = 0; i < theirF.size(); i++)
                if (normMe.equals(norm(theirF.get(i).getAsString()))) { theirF.remove(i); break; }
            saveFollowing(guildId, normT, theirF);
        }
        saveBlocked(guildId, normMe, blocked);
        JsonObject res = new JsonObject();
        res.addProperty("blocked", !was);
        ctx.json(GSON.toJson(res));
    }

    public static void handleGetBlocked(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String guildId = guildId();
        List<JsonObject> list = new ArrayList<>();
        for (JsonElement e : loadBlocked(guildId, norm(c.phoneNumber))) {
            String fp = norm(e.getAsString());
            for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId)) {
                if (fp.equals(norm(ct.phoneNumber))) {
                    JsonObject profile = loadProfile(guildId, ct.phoneNumber);
                    JsonObject u = new JsonObject();
                    u.addProperty("phone",     fp);
                    u.addProperty("username",  pStr(profile, "username", ct.displayName()));
                    u.addProperty("hasAvatar", !pStr(profile, "avatar", "").isEmpty());
                    list.add(u); break;
                }
            }
        }
        ctx.json(GSON.toJson(list));
    }

    // ── Follow requests ───────────────────────────────────────────────────────

    public static void handleGetFollowRequests(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String guildId = guildId();
        String normMe  = norm(c.phoneNumber);
        List<JsonObject> list = new ArrayList<>();
        for (JsonElement e : loadFollowRequests(guildId, normMe)) {
            String fp = norm(e.getAsString());
            for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId)) {
                if (fp.equals(norm(ct.phoneNumber))) {
                    JsonObject profile = loadProfile(guildId, ct.phoneNumber);
                    JsonObject u = new JsonObject();
                    u.addProperty("phone",     fp);
                    u.addProperty("username",  pStr(profile, "username", ct.displayName()));
                    u.addProperty("hasAvatar", !pStr(profile, "avatar", "").isEmpty());
                    list.add(u); break;
                }
            }
        }
        ctx.json(GSON.toJson(list));
    }

    public static void handleApproveFollowRequest(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String normReq = norm(ctx.pathParam("phone"));
        String normMe  = norm(c.phoneNumber);
        String guildId = guildId();
        JsonArray reqs = loadFollowRequests(guildId, normMe);
        boolean found = false;
        for (int i = 0; i < reqs.size(); i++)
            if (normReq.equals(norm(reqs.get(i).getAsString()))) { reqs.remove(i); found = true; break; }
        if (!found) { ctx.status(404).result(err("Anfrage nicht gefunden")); return; }
        saveFollowRequests(guildId, normMe, reqs);
        JsonArray following = loadFollowing(guildId, normReq);
        following.add(normMe);
        saveFollowing(guildId, normReq, following);
        ctx.json("{\"ok\":true}");
    }

    public static void handleRejectFollowRequest(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String normReq = norm(ctx.pathParam("phone"));
        String normMe  = norm(c.phoneNumber);
        String guildId = guildId();
        JsonArray reqs = loadFollowRequests(guildId, normMe);
        for (int i = 0; i < reqs.size(); i++)
            if (normReq.equals(norm(reqs.get(i).getAsString()))) { reqs.remove(i); break; }
        saveFollowRequests(guildId, normMe, reqs);
        ctx.json("{\"ok\":true}");
    }

    // ── Delete all data for a phone (on number change) ────────────────────────

    public static void deleteCitygramData(String guildId, String phone) {
        String normP = norm(phone);
        // Profile
        DataStore.deleteKey("cg-profile-" + guildId + "-" + normP);
        // Following / blocked / follow-requests
        DataStore.deleteKey("cg-following-"  + guildId + "-" + normP);
        DataStore.deleteKey("cg-blocked-"    + guildId + "-" + normP);
        DataStore.deleteKey("cg-follow-req-" + guildId + "-" + normP);
        // Posts (remove from global list, delete images/likes/comments)
        JsonArray posts = loadPosts(guildId);
        JsonArray remaining = new JsonArray();
        for (JsonElement e : posts) {
            JsonObject p = e.getAsJsonObject();
            if (normP.equals(norm(str(p, "phone")))) {
                String pid = str(p, "id");
                DataStore.deleteKey("cg-img-"      + guildId + "-" + pid);
                DataStore.deleteKey("cg-likes-"    + guildId + "-" + pid);
                DataStore.deleteKey("cg-comments-" + guildId + "-" + pid);
            } else {
                remaining.add(p);
            }
        }
        savePosts(guildId, remaining);
        // Stories
        JsonArray stories = loadStories(guildId);
        JsonArray remainStories = new JsonArray();
        for (JsonElement e : stories) {
            JsonObject s = e.getAsJsonObject();
            if (normP.equals(norm(str(s, "phone")))) {
                DataStore.deleteKey("cg-story-img-" + guildId + "-" + str(s, "id"));
            } else {
                remainStories.add(s);
            }
        }
        DataStore.writeString("cg-stories-" + guildId, GSON.toJson(remainStories));
        // Remove from other users' following lists
        for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId)) {
            JsonArray f = loadFollowing(guildId, ct.phoneNumber);
            boolean changed = false;
            for (int i = 0; i < f.size(); i++)
                if (normP.equals(norm(f.get(i).getAsString()))) { f.remove(i); changed = true; break; }
            if (changed) saveFollowing(guildId, ct.phoneNumber, f);
        }
    }

    // ── Search ────────────────────────────────────────────────────────────────

    public static void handleSearch(Context ctx) {
        PhoneManager.Contract me = auth(ctx); if (me == null) return;
        String q = ctx.queryParam("q");
        if (q == null || q.isBlank()) { ctx.json("[]"); return; }
        String guildId = guildId();
        String qLo = q.toLowerCase();
        List<JsonObject> res = new ArrayList<>();
        for (PhoneManager.Contract ct : PhoneManager.getAllContracts(guildId)) {
            JsonObject profile = loadProfile(guildId, ct.phoneNumber);
            String username = pStr(profile, "username", ct.displayName());
            if (username.toLowerCase().contains(qLo) || norm(ct.phoneNumber).contains(qLo)) {
                JsonObject u = new JsonObject();
                u.addProperty("phone",     norm(ct.phoneNumber));
                u.addProperty("username",  username);
                u.addProperty("hasAvatar", !pStr(profile, "avatar", "").isEmpty());
                res.add(u);
                if (res.size() >= 20) break;
            }
        }
        ctx.json(GSON.toJson(res));
    }

    // ── Stories ───────────────────────────────────────────────────────────────

    private static JsonArray loadStories(String guildId) {
        String s = DataStore.readString("cg-stories-" + guildId);
        if (s == null) return new JsonArray();
        try { return GSON.fromJson(s, JsonArray.class); } catch (Exception e) { return new JsonArray(); }
    }

    public static void handleGetStories(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        String guildId = guildId();
        JsonArray stories = loadStories(guildId);
        long now = Instant.now().toEpochMilli();
        JsonArray valid = new JsonArray();
        Map<String, JsonObject> byPhone = new LinkedHashMap<>();
        for (JsonElement e : stories) {
            JsonObject s = e.getAsJsonObject();
            if (now - s.get("ts").getAsLong() < STORY_TTL) {
                valid.add(s);
                byPhone.put(str(s, "phone"), s);
            }
        }
        if (valid.size() < stories.size()) DataStore.writeString("cg-stories-" + guildId, GSON.toJson(valid));
        ctx.json(GSON.toJson(new ArrayList<>(byPhone.values())));
    }

    public static void handleCreateStory(Context ctx) {
        PhoneManager.Contract c = auth(ctx); if (c == null) return;
        JsonObject body = parseBody(ctx);
        if (body == null) { ctx.status(400).result(err("Ungültiger Body")); return; }
        String image = str(body, "image");
        String text  = str(body, "text");
        if (image == null && (text == null || text.isBlank())) { ctx.status(400).result(err("Bild oder Text erforderlich")); return; }
        String guildId = guildId();
        String storyId = UUID.randomUUID().toString().replace("-","").substring(0,12);
        if (image != null) DataStore.writeString("cg-story-img-" + guildId + "-" + storyId, image);
        JsonObject profile = loadProfile(guildId, c.phoneNumber);
        JsonObject story = new JsonObject();
        story.addProperty("id",        storyId);
        story.addProperty("phone",     norm(c.phoneNumber));
        story.addProperty("username",  pStr(profile, "username", c.displayName()));
        story.addProperty("hasAvatar", !pStr(profile, "avatar", "").isEmpty());
        story.addProperty("text",      text != null ? text : "");
        story.addProperty("hasImage",  image != null);
        story.addProperty("ts",        Instant.now().toEpochMilli());
        JsonArray stories = loadStories(guildId);
        stories.add(story);
        DataStore.writeString("cg-stories-" + guildId, GSON.toJson(stories));
        ctx.json(GSON.toJson(story));
    }

    public static void handleGetStoryImage(Context ctx) {
        String storyId = ctx.pathParam("storyId");
        String token = ctx.queryParam("token");
        if (token == null) { String h = ctx.header("Authorization"); if (h != null && h.startsWith("Bearer ")) token = h.substring(7).trim(); }
        if (PhoneManager.validateSession(token) == null) { ctx.status(401).result("Unauthorized"); return; }
        serveImage(ctx, DataStore.readString("cg-story-img-" + guildId() + "-" + storyId));
    }
}
