# -*- coding: utf-8 -*-
import json, os, sys, time, threading, asyncio, psutil
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
from flask import (Flask, render_template, redirect, url_for, request,
                   session, jsonify, abort)

from config import (DATA_DIR, ECONOMY_FILE, SHOP_FILE, WARNS_FILE,
                    TEAM_WARNS_FILE, GUILD_ID, CITIZEN_ROLE_ID)
from dashboard_hooks import (ACTIVITY_LOG_FILE, WARNINGS_LOG_FILE,
                              MEMBERS_CACHE_FILE, INVITES_CACHE_FILE,
                              NOTES_FILE, BLACKLIST_FILE,
                              _read_json, _write_json, _lock, _now)

DASH_PASSWORD       = "PCRP2026+"
DASH_ROLE_ID        = 1490855702225485936
BANS_CACHE_FILE     = DATA_DIR / "dashboard_bans.json"

# Verzeichnis sicherstellen
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("DASHBOARD_SECRET", "pcrp-dash-secret-2026")
app.config["SESSION_PERMANENT"]        = False
app.config["SESSION_COOKIE_SAMESITE"]  = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"]  = True

_bot_ref = None
_bot_loop = None


def set_bot(b):
    global _bot_ref, _bot_loop
    _bot_ref  = b
    _bot_loop = b.loop


def _call_async(coro):
    if _bot_loop is None:
        return None
    fut = asyncio.run_coroutine_threadsafe(coro, _bot_loop)
    try:
        return fut.result(timeout=10)
    except Exception:
        return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Nicht eingeloggt"}), 401
        return f(*args, **kwargs)
    return decorated


# \u2500\u2500 Auth \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/", methods=["GET"])
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        pw       = request.form.get("password", "")
        disc_id  = request.form.get("discord_id", "").strip()

        if pw != DASH_PASSWORD:
            error = "Falsches Passwort"
        elif not disc_id.isdigit():
            error = "Bitte eine g\u00fcltige Discord-ID eingeben"
        else:
            members = _read_json(MEMBERS_CACHE_FILE, {})
            member  = members.get(disc_id)
            if not member:
                error = "Discord-ID nicht auf dem Server gefunden"
            elif DASH_ROLE_ID not in (member.get("roles") or []):
                error = "Du hast keine Berechtigung (fehlende Rolle)"
            else:
                session.permanent = False
                session["logged_in"]    = True
                session["discord_id"]   = disc_id
                session["discord_name"] = member.get("name", disc_id)
                return redirect(url_for("dashboard"))

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# \u2500\u2500 Main UI \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dash.html")


@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


# \u2500\u2500 Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _eco():
    return _read_json(ECONOMY_FILE, {})

def _members():
    return _read_json(MEMBERS_CACHE_FILE, {})

def _name(uid):
    m = _members().get(str(uid))
    return m["name"] if m else str(uid)


# \u2500\u2500 API: Economy \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/economy")
@api_login_required
def api_economy():
    eco  = _eco()
    mems = _members()
    rows = []
    for uid, d in eco.items():
        m = mems.get(uid, {})
        rows.append({
            "id":        uid,
            "name":      m.get("name") or m.get("tag") or uid,
            "kasse":     d.get("kasse", 0),
            "bank":      d.get("bank", 0),
            "gesamt":    d.get("kasse", 0) + d.get("bank", 0),
            "dispo":     d.get("dispo_limit", 0),
            "schulden":  d.get("schulden", 0),
        })
    rows.sort(key=lambda x: x["gesamt"], reverse=True)
    return jsonify(rows)


# \u2500\u2500 API: Warns \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/warns")
@api_login_required
def api_warns():
    data = _read_json(WARNS_FILE, {})
    mems = _members()
    rows = []
    for uid, warns in data.items():
        if not warns:
            continue
        m = mems.get(uid, {})
        rows.append({
            "id":    uid,
            "name":  m.get("name") or m.get("tag") or uid,
            "warns": warns,
            "count": len(warns),
        })
    rows.sort(key=lambda x: x["count"], reverse=True)
    return jsonify(rows)


@app.route("/api/team-warns")
@api_login_required
def api_team_warns():
    data = _read_json(TEAM_WARNS_FILE, {})
    mems = _members()
    rows = []
    for uid, warns in data.items():
        if not warns:
            continue
        m = mems.get(uid, {})
        rows.append({
            "id":    uid,
            "name":  m.get("name") or m.get("tag") or uid,
            "warns": warns,
            "count": len(warns),
        })
    rows.sort(key=lambda x: x["count"], reverse=True)
    return jsonify(rows)


# \u2500\u2500 API: Inventories \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/inventories")
@api_login_required
def api_inventories():
    eco  = _eco()
    mems = _members()
    rows = []
    for uid, d in eco.items():
        inv   = d.get("inventory", [])
        lager = d.get("lager", [])
        if not inv and not lager:
            continue
        m = mems.get(uid, {})
        rows.append({
            "id":    uid,
            "name":  m.get("name") or m.get("tag") or uid,
            "inv":   inv,
            "lager": lager,
        })
    return jsonify(rows)


# \u2500\u2500 API: Shops \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/shops")
@api_login_required
def api_shops():
    return jsonify(_read_json(SHOP_FILE, {}))


@app.route("/api/shop-item", methods=["POST"])
@api_login_required
def api_add_shop_item():
    body  = request.get_json(force=True) or {}
    shop  = body.get("shop", "").strip()
    name  = body.get("name", "").strip()
    emoji = body.get("emoji", "").strip()
    preis = body.get("preis")
    if not shop or not name or preis is None:
        return jsonify({"error": "shop, name, preis erforderlich"}), 400
    try:
        preis = int(preis)
    except ValueError:
        return jsonify({"error": "preis muss eine Zahl sein"}), 400

    with _lock:
        data = _read_json(SHOP_FILE, {})
        if shop not in data:
            return jsonify({"error": f"Shop '{shop}' nicht gefunden"}), 404
        item_entry = {"name": f"{emoji} {name}".strip(), "preis": preis, "emoji": emoji}
        items = data[shop].get("items", [])
        items.append(item_entry)
        data[shop]["items"] = items
        _write_json(SHOP_FILE, data)

    from dashboard_hooks import log_activity
    log_activity("SHOP", f"Item '{emoji} {name}' ({preis}$) zu Shop '{shop}' hinzugef\xfcgt")
    return jsonify({"ok": True})


@app.route("/api/shop-item", methods=["DELETE"])
@api_login_required
def api_delete_shop_item():
    body  = request.get_json(force=True) or {}
    shop  = body.get("shop", "").strip()
    idx   = body.get("index")
    if shop is None or idx is None:
        return jsonify({"error": "shop und index erforderlich"}), 400
    with _lock:
        data = _read_json(SHOP_FILE, {})
        if shop not in data:
            return jsonify({"error": "Shop nicht gefunden"}), 404
        items = data[shop].get("items", [])
        if idx < 0 or idx >= len(items):
            return jsonify({"error": "Index au\xdferhalb"}), 400
        removed = items.pop(idx)
        data[shop]["items"] = items
        _write_json(SHOP_FILE, data)
    from dashboard_hooks import log_activity
    log_activity("SHOP", f"Item '{removed.get('name')}' aus Shop '{shop}' entfernt")
    return jsonify({"ok": True})


# \u2500\u2500 API: Bans \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/bans")
@api_login_required
def api_bans():
    return jsonify(_read_json(BANS_CACHE_FILE, []))


@app.route("/api/bans/refresh", methods=["POST"])
@api_login_required
def api_bans_refresh():
    async def _fetch():
        guild = _bot_ref.get_guild(GUILD_ID)
        if not guild:
            return []
        bans = []
        async for be in guild.bans():
            bans.append({
                "id":     str(be.user.id),
                "name":   str(be.user),
                "reason": be.reason or "Kein Grund",
                "avatar": str(be.user.display_avatar.url) if be.user.display_avatar else "",
            })
        return bans
    bans = _call_async(_fetch())
    if bans is None:
        bans = _read_json(BANS_CACHE_FILE, [])
    else:
        _write_json(BANS_CACHE_FILE, bans)
    return jsonify(bans)


@app.route("/api/unban", methods=["POST"])
@api_login_required
def api_unban():
    body    = request.get_json(force=True) or {}
    user_id = int(body.get("user_id", 0))
    if not user_id:
        return jsonify({"error": "user_id fehlt"}), 400

    async def _do_unban():
        guild = _bot_ref.get_guild(GUILD_ID)
        if not guild:
            return False
        import discord
        try:
            obj = discord.Object(id=user_id)
            await guild.unban(obj, reason="Dashboard-Entbannung")
            return True
        except Exception:
            return False

    ok = _call_async(_do_unban())
    if ok:
        with _lock:
            bans = _read_json(BANS_CACHE_FILE, [])
            bans = [b for b in bans if b.get("id") != str(user_id)]
            _write_json(BANS_CACHE_FILE, bans)
        from dashboard_hooks import log_activity
        log_activity("BAN", f"Spieler {user_id} entbannt (Dashboard)")
        return jsonify({"ok": True})
    return jsonify({"error": "Entbannung fehlgeschlagen"}), 500


# \u2500\u2500 API: Blacklist \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/blacklist")
@api_login_required
def api_blacklist():
    return jsonify(_read_json(BLACKLIST_FILE, []))


@app.route("/api/blacklist", methods=["POST"])
@api_login_required
def api_blacklist_add():
    body   = request.get_json(force=True) or {}
    name   = body.get("name", "").strip()
    uid    = body.get("discord_id", "").strip()
    reason = body.get("reason", "").strip()
    if not name and not uid:
        return jsonify({"error": "Name oder Discord-ID erforderlich"}), 400
    entry = {
        "id":         uid or None,
        "name":       name or "Unbekannt",
        "reason":     reason or "Kein Grund",
        "added_at":   _now(),
    }
    with _lock:
        bl = _read_json(BLACKLIST_FILE, [])
        bl.append(entry)
        _write_json(BLACKLIST_FILE, bl)
    from dashboard_hooks import log_activity
    log_activity("BLACKLIST", f"'{name}' ({uid}) zur Blacklist hinzugef\xfcgt")
    return jsonify({"ok": True})


@app.route("/api/blacklist/<int:idx>", methods=["DELETE"])
@api_login_required
def api_blacklist_delete(idx):
    with _lock:
        bl = _read_json(BLACKLIST_FILE, [])
        if idx < 0 or idx >= len(bl):
            return jsonify({"error": "Index au\xdferhalb"}), 400
        removed = bl.pop(idx)
        _write_json(BLACKLIST_FILE, bl)
    from dashboard_hooks import log_activity
    log_activity("BLACKLIST", f"'{removed.get('name')}' von Blacklist entfernt")
    return jsonify({"ok": True})


# \u2500\u2500 API: Logs / Warnings \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/activity-log")
@api_login_required
def api_activity_log():
    limit = min(int(request.args.get("limit", 200)), 1000)
    data  = _read_json(ACTIVITY_LOG_FILE, [])
    return jsonify(data[:limit])


@app.route("/api/warnings-log")
@api_login_required
def api_warnings_log():
    limit = min(int(request.args.get("limit", 100)), 500)
    data  = _read_json(WARNINGS_LOG_FILE, [])
    return jsonify(data[:limit])


# \u2500\u2500 API: Members & Players \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/members")
@api_login_required
def api_members():
    return jsonify(_members())


@app.route("/api/players")
@api_login_required
def api_players():
    mems = _members()
    players = {
        uid: m for uid, m in mems.items()
        if CITIZEN_ROLE_ID in m.get("roles", [])
    }
    return jsonify({"count": len(players), "players": players})


# \u2500\u2500 API: Invites \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/invites")
@api_login_required
def api_invites():
    return jsonify(_read_json(INVITES_CACHE_FILE, {}))


# \u2500\u2500 API: Notes \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/notes")
@api_login_required
def api_notes():
    data = _read_json(NOTES_FILE, {})
    mems = _members()
    result = {}
    for uid, notes in data.items():
        m = mems.get(uid, {})
        result[uid] = {
            "name":  m.get("name") or m.get("tag") or uid,
            "notes": notes,
        }
    return jsonify(result)


@app.route("/api/notes", methods=["POST"])
@api_login_required
def api_notes_add():
    body    = request.get_json(force=True) or {}
    user_id = str(body.get("user_id", "")).strip()
    note    = body.get("note", "").strip()
    if not user_id or not note:
        return jsonify({"error": "user_id und note erforderlich"}), 400
    entry = {"note": note, "time": _now()}
    with _lock:
        data = _read_json(NOTES_FILE, {})
        data.setdefault(user_id, []).append(entry)
        _write_json(NOTES_FILE, data)
    return jsonify({"ok": True})


@app.route("/api/notes/<user_id>/<int:idx>", methods=["DELETE"])
@api_login_required
def api_notes_delete(user_id, idx):
    with _lock:
        data = _read_json(NOTES_FILE, {})
        notes = data.get(user_id, [])
        if idx < 0 or idx >= len(notes):
            return jsonify({"error": "Index au\xdferhalb"}), 400
        notes.pop(idx)
        data[user_id] = notes
        _write_json(NOTES_FILE, data)
    return jsonify({"ok": True})


# \u2500\u2500 API: Status \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/api/status")
@api_login_required
def api_status():
    proc    = psutil.Process(os.getpid())
    ram_mb  = proc.memory_info().rss / 1024 / 1024
    cpu_pct = psutil.cpu_percent(interval=0.2)
    disk    = psutil.disk_usage("/")

    guild   = _bot_ref.get_guild(GUILD_ID) if _bot_ref else None
    latency = round(_bot_ref.latency * 1000, 1) if _bot_ref else None

    features = {}
    try:
        from bot_status import _status
        features = {k: {"ok": v[0], "err": v[1]} for k, v in _status.items()}
    except Exception:
        pass

    return jsonify({
        "ram_mb":    round(ram_mb, 1),
        "cpu_pct":   cpu_pct,
        "disk_pct":  round(disk.percent, 1),
        "latency_ms": latency,
        "guilds":    len(_bot_ref.guilds) if _bot_ref else 0,
        "members":   guild.member_count if guild else 0,
        "uptime":    _uptime(),
        "features":  features,
    })


_start_time = time.time()


def _uptime() -> str:
    secs = int(time.time() - _start_time)
    h, r = divmod(secs, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"


# \u2500\u2500 Starter \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def start_dashboard(bot_instance, host="0.0.0.0", port=8080):
    set_bot(bot_instance)
    t = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False),
        daemon=True,
        name="dashboard-flask",
    )
    t.start()
    print(f"[Dashboard] \u2705 Gestartet auf http://{host}:{port}")
