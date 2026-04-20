# -*- coding: utf-8 -*-
# dashboard.py \u2014 Web-Dashboard f\u00FCr Paradise City Roleplay Bot
# Wird als Hintergrund-Thread in bot.py gestartet

import os
import json
import threading
from pathlib import Path
from datetime import datetime, timezone
from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify

# \u2500\u2500 Konfiguration \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
DATA_DIR           = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
ECONOMY_FILE       = DATA_DIR / "economy_data.json"
SHOP_FILE          = DATA_DIR / "shop_data.json"
WARNS_FILE         = DATA_DIR / "warns_data.json"
TEAM_WARNS_FILE    = DATA_DIR / "team_warns_data.json"

DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "")
DASHBOARD_PORT     = int(os.environ.get("DASHBOARD_PORT", "8080"))

app = Flask(__name__)
app.secret_key = os.environ.get("DASHBOARD_SECRET", "pcrp-dashboard-secret-key-2025")

_lock = threading.Lock()


# \u2500\u2500 JSON Helfer \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def load_json(path, default=None):
    with _lock:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default if default is not None else {}


def save_json(path, data):
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def fmt(n):
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return str(n)


# \u2500\u2500 Auth Helfer \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def logged_in():
    return session.get("auth") == "ok"


def require_login():
    if not logged_in():
        return redirect(url_for("login"))
    return None


# \u2500\u2500 HTML Basis-Template \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
BASE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paradise City \u2014 Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0b12;color:#ddd;font-family:'Segoe UI',sans-serif;min-height:100vh}
a{color:inherit;text-decoration:none}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:#0b0b12}::-webkit-scrollbar-thumb{background:#e67e22;border-radius:3px}

/* Sidebar */
.sidebar{position:fixed;left:0;top:0;width:220px;height:100vh;background:#10101a;border-right:1px solid #1e1e2e;display:flex;flex-direction:column;z-index:100}
.sidebar-logo{padding:24px 20px 16px;border-bottom:1px solid #1e1e2e}
.sidebar-logo span{color:#e67e22;font-size:20px;font-weight:700;letter-spacing:.5px}
.sidebar-logo small{display:block;color:#555;font-size:11px;margin-top:2px}
.nav{flex:1;padding:12px 0}
.nav a{display:flex;align-items:center;gap:10px;padding:11px 20px;color:#888;font-size:14px;transition:.15s}
.nav a:hover,.nav a.active{color:#e67e22;background:#1a1a28}
.nav a .icon{font-size:16px;width:20px;text-align:center}
.sidebar-footer{padding:16px 20px;border-top:1px solid #1e1e2e;font-size:12px;color:#444}

/* Main */
.main{margin-left:220px;padding:28px 32px;min-height:100vh}
h1{font-size:22px;font-weight:700;margin-bottom:4px}
.subtitle{color:#555;font-size:13px;margin-bottom:24px}

/* Cards */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-bottom:28px}
.card{background:#13131e;border:1px solid #1e1e2e;border-radius:10px;padding:20px}
.card-label{font-size:11px;color:#555;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px}
.card-value{font-size:28px;font-weight:700;color:#e67e22}
.card-sub{font-size:12px;color:#444;margin-top:4px}

/* Table */
.table-wrap{background:#13131e;border:1px solid #1e1e2e;border-radius:10px;overflow:hidden;margin-bottom:24px}
.table-header{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid #1e1e2e}
.table-header h2{font-size:14px;font-weight:600;color:#ccc}
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:10px 20px;font-size:11px;color:#555;text-transform:uppercase;letter-spacing:.6px;border-bottom:1px solid #1a1a28}
td{padding:11px 20px;font-size:13px;border-bottom:1px solid #161622;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#16162a}

/* Badges */
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600}
.badge-green{background:#1a3a28;color:#2ecc71}
.badge-red{background:#3a1a1a;color:#e74c3c}
.badge-orange{background:#3a2a1a;color:#e67e22}
.badge-blue{background:#1a2a3a;color:#3498db}

/* Buttons */
.btn{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;border-radius:7px;font-size:13px;font-weight:600;cursor:pointer;border:none;transition:.15s}
.btn-primary{background:#e67e22;color:#fff}.btn-primary:hover{background:#d35400}
.btn-danger{background:#c0392b;color:#fff}.btn-danger:hover{background:#a93226}
.btn-secondary{background:#1e1e2e;color:#aaa;border:1px solid #2a2a3a}.btn-secondary:hover{color:#fff}
.btn-sm{padding:4px 10px;font-size:12px}

/* Form */
.form-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.form-group{display:flex;flex-direction:column;gap:5px;flex:1;min-width:160px}
label{font-size:12px;color:#666;font-weight:600;text-transform:uppercase;letter-spacing:.5px}
input,select,textarea{background:#0d0d18;border:1px solid #1e1e2e;color:#ddd;padding:9px 13px;border-radius:7px;font-size:13px;outline:none;width:100%;font-family:inherit}
input:focus,select:focus{border-color:#e67e22}
.form-wrap{background:#13131e;border:1px solid #1e1e2e;border-radius:10px;padding:20px;margin-bottom:20px}

/* Alert */
.alert{padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px}
.alert-success{background:#1a3a28;border:1px solid #2ecc71;color:#2ecc71}
.alert-error{background:#3a1a1a;border:1px solid #e74c3c;color:#e74c3c}

/* Search */
.search-bar{background:#0d0d18;border:1px solid #1e1e2e;color:#ddd;padding:8px 14px;border-radius:7px;font-size:13px;outline:none;width:240px}
.search-bar:focus{border-color:#e67e22}

/* Player grid */
.player-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px;margin-bottom:24px}
.player-card{background:#13131e;border:1px solid #1e1e2e;border-radius:10px;padding:16px;text-align:center;cursor:pointer;transition:.15s}
.player-card:hover{border-color:#e67e22;transform:translateY(-2px)}
.player-card .avatar{width:52px;height:52px;border-radius:50%;background:#1e1e2e;display:flex;align-items:center;justify-content:center;margin:0 auto 10px;font-size:22px}
.player-card .name{font-size:13px;font-weight:600;margin-bottom:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.player-card .uid{font-size:10px;color:#444;margin-bottom:8px}
.player-card .money{display:flex;justify-content:center;gap:12px;font-size:11px}
.player-card .money span{color:#555}
.player-card .money b{color:#e67e22}

/* Modal */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:200;align-items:center;justify-content:center}
.modal-overlay.show{display:flex}
.modal{background:#13131e;border:1px solid #1e1e2e;border-radius:12px;padding:28px;width:520px;max-width:95vw;max-height:90vh;overflow-y:auto}
.modal h2{font-size:17px;margin-bottom:18px;color:#e67e22}
.modal-close{float:right;cursor:pointer;color:#555;font-size:20px;line-height:1}.modal-close:hover{color:#e67e22}

/* Inventory list */
.inv-list{display:flex;flex-direction:column;gap:6px;max-height:220px;overflow-y:auto;margin:10px 0}
.inv-item{display:flex;align-items:center;justify-content:space-between;background:#0d0d18;border:1px solid #1e1e2e;border-radius:6px;padding:7px 12px;font-size:13px}
.inv-item .rm{color:#c0392b;cursor:pointer;font-weight:700;font-size:16px;line-height:1;padding:0 4px}.inv-item .rm:hover{color:#e74c3c}

/* Tag */
.tag{display:inline-block;background:#1a1a28;border:1px solid #2a2a3a;border-radius:5px;padding:2px 8px;font-size:11px;color:#aaa;margin:2px}

/* Divider */
.divider{border:none;border-top:1px solid #1a1a28;margin:18px 0}

/* Responsive */
@media(max-width:768px){.sidebar{display:none}.main{margin-left:0}}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sidebar-logo">
    <span>Paradise City</span>
    <small>Bot Dashboard</small>
  </div>
  <nav class="nav">
    <a href="{{ url_for('home') }}" class="{{ 'active' if page=='home' else '' }}"><span class="icon">\U0001F3E0</span> \u00DCbersicht</a>
    <a href="{{ url_for('spieler') }}" class="{{ 'active' if page=='spieler' else '' }}"><span class="icon">\U0001F465</span> Spieler</a>
    <a href="{{ url_for('shop') }}" class="{{ 'active' if page=='shop' else '' }}"><span class="icon">\U0001F6D2</span> Shop</a>
    <a href="{{ url_for('warns_page') }}" class="{{ 'active' if page=='warns' else '' }}"><span class="icon">\u26A0\uFE0F</span> Verwarnungen</a>
  </nav>
  <div class="sidebar-footer">Paradise City RP &copy; 2025</div>
</div>
<div class="main">
  {% if msg %}<div class="alert alert-{{ msg_type }}">{{ msg }}</div>{% endif %}
  {{ content | safe }}
</div>
<script>
function filterTable(input, tableId) {
  const q = input.value.toLowerCase();
  document.querySelectorAll('#' + tableId + ' tbody tr').forEach(tr => {
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}
function openModal(id) {
  document.getElementById(id).classList.add('show');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('show');
}
function filterCards(input) {
  const q = input.value.toLowerCase();
  document.querySelectorAll('.player-card').forEach(c => {
    c.style.display = c.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}
</script>
</body></html>"""


def render(page, content, msg=None, msg_type="success"):
    return render_template_string(
        BASE, page=page, content=content, msg=msg, msg_type=msg_type
    )


# \u2500\u2500 Login \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
LOGIN_TMPL = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login \u2014 Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0b12;color:#ddd;font-family:'Segoe UI',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#13131e;border:1px solid #1e1e2e;border-radius:12px;padding:40px;width:360px}
h1{color:#e67e22;font-size:22px;margin-bottom:4px}
p{color:#555;font-size:13px;margin-bottom:24px}
label{display:block;font-size:12px;color:#666;text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px}
input{width:100%;background:#0d0d18;border:1px solid #1e1e2e;color:#ddd;padding:10px 14px;border-radius:7px;font-size:14px;outline:none;margin-bottom:16px}
input:focus{border-color:#e67e22}
button{width:100%;background:#e67e22;color:#fff;border:none;padding:11px;border-radius:7px;font-size:14px;font-weight:700;cursor:pointer}
button:hover{background:#d35400}
.err{background:#3a1a1a;border:1px solid #e74c3c;color:#e74c3c;padding:10px 14px;border-radius:7px;font-size:13px;margin-bottom:14px}
</style></head>
<body>
<div class="box">
  <h1>Paradise City</h1>
  <p>Bot Dashboard &mdash; Bitte anmelden</p>
  {% if error %}<div class="err">\u274C {{ error }}</div>{% endif %}
  <form method="post">
    <label>Passwort</label>
    <input type="password" name="password" autofocus placeholder="Dashboard-Passwort">
    <button type="submit">Anmelden</button>
  </form>
</div>
</body></html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if not DASHBOARD_PASSWORD:
        session["auth"] = "ok"
        return redirect(url_for("home"))
    error = None
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASSWORD:
            session["auth"] = "ok"
            return redirect(url_for("home"))
        error = "Falsches Passwort"
    return render_template_string(LOGIN_TMPL, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# \u2500\u2500 Home / \u00DCbersicht \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/")
def home():
    r = require_login()
    if r:
        return r

    eco   = load_json(ECONOMY_FILE)
    shop  = load_json(SHOP_FILE, default=[])
    warns = load_json(WARNS_FILE)

    total_players   = len(eco)
    total_cash      = sum(int(v.get("cash", 0)) for v in eco.values())
    total_bank      = sum(int(v.get("bank", 0)) for v in eco.values())
    total_warns     = sum(len(v) for v in warns.values())
    shop_items      = len(shop) if isinstance(shop, list) else 0

    richest = sorted(eco.items(), key=lambda x: int(x[1].get("bank", 0)) + int(x[1].get("cash", 0)), reverse=True)[:5]

    rows = ""
    for uid, data in richest:
        total = int(data.get("cash", 0)) + int(data.get("bank", 0))
        rows += f"""<tr>
          <td><code style="color:#888;font-size:11px">{uid}</code></td>
          <td><b style="color:#e67e22">${fmt(data.get('cash',0))}</b></td>
          <td><b style="color:#3498db">${fmt(data.get('bank',0))}</b></td>
          <td><b>${fmt(total)}</b></td>
          <td><span class="badge badge-blue">{len(data.get('inventory',[]))} Items</span></td>
        </tr>"""

    content = f"""
<h1>\U0001F3E0 \u00DCbersicht</h1>
<div class="subtitle">Paradise City Roleplay \u2014 Bot Dashboard</div>

<div class="cards">
  <div class="card">
    <div class="card-label">Registrierte Spieler</div>
    <div class="card-value">{total_players}</div>
  </div>
  <div class="card">
    <div class="card-label">Gesamt Bar-Geld</div>
    <div class="card-value">${fmt(total_cash)}</div>
  </div>
  <div class="card">
    <div class="card-label">Gesamt Bank-Geld</div>
    <div class="card-value">${fmt(total_bank)}</div>
  </div>
  <div class="card">
    <div class="card-label">Shop Items</div>
    <div class="card-value">{shop_items}</div>
  </div>
  <div class="card">
    <div class="card-label">Aktive Verwarnungen</div>
    <div class="card-value">{total_warns}</div>
  </div>
</div>

<div class="table-wrap">
  <div class="table-header"><h2>\U0001F451 Top 5 Reichste Spieler</h2></div>
  <table id="top-table">
    <thead><tr><th>User ID</th><th>Bar</th><th>Bank</th><th>Gesamt</th><th>Inventar</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
"""
    return render("home", content)


# \u2500\u2500 Spieler \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/spieler")
def spieler():
    r = require_login()
    if r:
        return r

    eco = load_json(ECONOMY_FILE)

    cards = ""
    for uid, data in eco.items():
        cash = int(data.get("cash", 0))
        bank = int(data.get("bank", 0))
        inv_count = len(data.get("inventory", []))
        short_id = uid[-6:]
        cards += f"""
<div class="player-card" onclick="window.location='/spieler/{uid}'">
  <div class="avatar">\U0001F464</div>
  <div class="name" title="{uid}">#{short_id}</div>
  <div class="uid">{uid}</div>
  <div class="money">
    <div><span>Bar</span><br><b>${fmt(cash)}</b></div>
    <div><span>Bank</span><br><b>${fmt(bank)}</b></div>
  </div>
  <div style="margin-top:8px"><span class="badge badge-blue">{inv_count} Items</span></div>
</div>"""

    content = f"""
<h1>\U0001F465 Spieler</h1>
<div class="subtitle">Alle registrierten Spieler ({len(eco)})</div>
<div style="margin-bottom:16px">
  <input class="search-bar" type="text" placeholder="\U0001F50D Spieler suchen (ID)..." oninput="filterCards(this)">
</div>
<div class="player-grid">{cards}</div>
"""
    return render("spieler", content)


@app.route("/spieler/<uid>", methods=["GET", "POST"])
def spieler_detail(uid):
    r = require_login()
    if r:
        return r

    eco = load_json(ECONOMY_FILE)
    msg = None
    msg_type = "success"

    if uid not in eco:
        eco[uid] = {"cash": 0, "bank": 0, "inventory": [], "last_wage": None,
                    "daily_deposit": 0, "daily_withdraw": 0, "daily_transfer": 0,
                    "daily_reset": None, "custom_limit": None, "dispo": 0}

    data = eco[uid]

    if request.method == "POST":
        action = request.form.get("action")

        if action == "edit_money":
            try:
                data["cash"] = int(request.form.get("cash", data.get("cash", 0)))
                data["bank"] = int(request.form.get("bank", data.get("bank", 0)))
                eco[uid] = data
                save_json(ECONOMY_FILE, eco)
                msg = "\u2705 Guthaben gespeichert"
            except Exception as e:
                msg = f"\u274C Fehler: {e}"
                msg_type = "error"

        elif action == "add_item":
            item = request.form.get("item", "").strip()
            if item:
                data.setdefault("inventory", []).append(item)
                eco[uid] = data
                save_json(ECONOMY_FILE, eco)
                msg = f"\u2705 Item \"{item}\" hinzugef\u00FCgt"
            else:
                msg = "\u274C Kein Item angegeben"
                msg_type = "error"

        elif action == "remove_item":
            item = request.form.get("item", "").strip()
            inv = data.get("inventory", [])
            if item in inv:
                inv.remove(item)
                data["inventory"] = inv
                eco[uid] = data
                save_json(ECONOMY_FILE, eco)
                msg = f"\u2705 Item \"{item}\" entfernt"
            else:
                msg = "\u274C Item nicht gefunden"
                msg_type = "error"

        elif action == "reset_money":
            data["cash"] = 0
            data["bank"] = 0
            eco[uid] = data
            save_json(ECONOMY_FILE, eco)
            msg = "\u2705 Guthaben zur\u00FCckgesetzt"

        return redirect(url_for("spieler_detail", uid=uid, _msg=msg))

    if request.args.get("_msg"):
        msg = request.args.get("_msg")

    inventory = data.get("inventory", [])
    inv_html = ""
    for item in inventory:
        safe_item = item.replace('"', '&quot;')
        inv_html += f"""<div class="inv-item">
          <span>{item}</span>
          <form method="post" style="margin:0">
            <input type="hidden" name="action" value="remove_item">
            <input type="hidden" name="item" value="{safe_item}">
            <button class="rm" type="submit" title="Entfernen">&times;</button>
          </form>
        </div>"""

    warns = load_json(WARNS_FILE)
    user_warns = warns.get(uid, [])
    warns_html = ""
    for i, w in enumerate(user_warns):
        reason   = w.get("reason", "Kein Grund")
        by       = w.get("by_name", "Unbekannt")
        at       = w.get("timestamp", "")[:10] if w.get("timestamp") else ""
        warns_html += f"""<tr>
          <td>{i+1}</td>
          <td>{reason}</td>
          <td>{by}</td>
          <td>{at}</td>
          <td>
            <form method="post" action="/warns/remove" style="margin:0">
              <input type="hidden" name="uid" value="{uid}">
              <input type="hidden" name="index" value="{i}">
              <button class="btn btn-danger btn-sm" type="submit">\u274C</button>
            </form>
          </td>
        </tr>"""

    content = f"""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
  <a href="/spieler" class="btn btn-secondary">\u2190 Zur\u00FCck</a>
  <div>
    <h1>\U0001F464 Spieler #{uid[-6:]}</h1>
    <div class="subtitle" style="margin-bottom:0">ID: {uid}</div>
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
  <!-- Geld bearbeiten -->
  <div class="form-wrap">
    <h2 style="font-size:14px;margin-bottom:14px;color:#aaa">\U0001F4B0 Guthaben bearbeiten</h2>
    <form method="post">
      <input type="hidden" name="action" value="edit_money">
      <div class="form-row">
        <div class="form-group">
          <label>Bar ($)</label>
          <input type="number" name="cash" value="{int(data.get('cash',0))}">
        </div>
        <div class="form-group">
          <label>Bank ($)</label>
          <input type="number" name="bank" value="{int(data.get('bank',0))}">
        </div>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-primary" type="submit">\u2705 Speichern</button>
        <button class="btn btn-danger" type="button" onclick="if(confirm('Guthaben wirklich auf $0 setzen?')){{this.form.action.value='reset_money';this.form.submit()}}">Zur\u00FCcksetzen</button>
      </div>
    </form>
  </div>

  <!-- Inventar -->
  <div class="form-wrap">
    <h2 style="font-size:14px;margin-bottom:10px;color:#aaa">\U0001F392 Inventar ({len(inventory)} Items)</h2>
    <div class="inv-list">{inv_html if inv_html else '<span style="color:#444;font-size:13px">Kein Items</span>'}</div>
    <form method="post" style="display:flex;gap:8px;margin-top:10px">
      <input type="hidden" name="action" value="add_item">
      <input type="text" name="item" placeholder="Item hinzuf\u00FCgen..." style="flex:1">
      <button class="btn btn-primary" type="submit">+</button>
    </form>
  </div>
</div>

<!-- Verwarnungen -->
<div class="table-wrap">
  <div class="table-header"><h2>\u26A0\uFE0F Verwarnungen ({len(user_warns)})</h2></div>
  <table>
    <thead><tr><th>#</th><th>Grund</th><th>Von</th><th>Datum</th><th>Aktion</th></tr></thead>
    <tbody>{warns_html if warns_html else '<tr><td colspan="5" style="color:#444;text-align:center;padding:16px">Keine Verwarnungen</td></tr>'}</tbody>
  </table>
</div>
"""
    return render("spieler", content, msg=msg, msg_type=msg_type)


# \u2500\u2500 Shop \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/shop", methods=["GET", "POST"])
def shop():
    r = require_login()
    if r:
        return r

    items = load_json(SHOP_FILE, default=[])
    msg = None
    msg_type = "success"

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            name  = request.form.get("name", "").strip()
            price = request.form.get("price", "0").strip()
            try:
                price = int(price)
                if not name:
                    raise ValueError("Kein Name")
                items.append({"name": name, "price": price})
                save_json(SHOP_FILE, items)
                msg = f"\u2705 Item \"{name}\" hinzugef\u00FCgt"
            except Exception as e:
                msg = f"\u274C Fehler: {e}"
                msg_type = "error"

        elif action == "delete":
            name = request.form.get("name", "")
            items = [i for i in items if i.get("name") != name]
            save_json(SHOP_FILE, items)
            msg = f"\u2705 Item gel\u00F6scht"

        elif action == "edit_price":
            name  = request.form.get("name", "")
            price = request.form.get("price", "0")
            try:
                price = int(price)
                for item in items:
                    if item.get("name") == name:
                        item["price"] = price
                save_json(SHOP_FILE, items)
                msg = "\u2705 Preis gespeichert"
            except Exception as e:
                msg = f"\u274C Fehler: {e}"
                msg_type = "error"

    rows = ""
    for item in (items if isinstance(items, list) else []):
        name  = item.get("name", "")
        price = item.get("price", 0)
        safe_name = name.replace('"', '&quot;')
        rows += f"""<tr>
          <td>{name}</td>
          <td><b style="color:#e67e22">${fmt(price)}</b></td>
          <td>
            <div style="display:flex;gap:6px;align-items:center">
              <form method="post" style="display:flex;gap:4px;align-items:center">
                <input type="hidden" name="action" value="edit_price">
                <input type="hidden" name="name" value="{safe_name}">
                <input type="number" name="price" value="{price}" style="width:110px;padding:5px 8px;font-size:12px">
                <button class="btn btn-secondary btn-sm" type="submit">\u2713</button>
              </form>
              <form method="post" style="margin:0">
                <input type="hidden" name="action" value="delete">
                <input type="hidden" name="name" value="{safe_name}">
                <button class="btn btn-danger btn-sm" type="submit" onclick="return confirm('Wirklich l\u00F6schen?')">\u274C</button>
              </form>
            </div>
          </td>
        </tr>"""

    content = f"""
<h1>\U0001F6D2 Shop-Verwaltung</h1>
<div class="subtitle">{len(items) if isinstance(items, list) else 0} Items im Shop</div>

<div class="form-wrap">
  <h2 style="font-size:14px;margin-bottom:14px;color:#aaa">+ Neues Item</h2>
  <form method="post">
    <input type="hidden" name="action" value="add">
    <div class="form-row">
      <div class="form-group">
        <label>Name</label>
        <input type="text" name="name" placeholder="z.B. \U0001F4F1| Handy">
      </div>
      <div class="form-group" style="max-width:180px">
        <label>Preis ($)</label>
        <input type="number" name="price" placeholder="5000" min="0">
      </div>
    </div>
    <button class="btn btn-primary" type="submit">Item hinzuf\u00FCgen</button>
  </form>
</div>

<div class="table-wrap">
  <div class="table-header">
    <h2>Alle Shop-Items</h2>
    <input class="search-bar" type="text" placeholder="\U0001F50D Suchen..." oninput="filterTable(this,'shop-table')" style="width:180px">
  </div>
  <table id="shop-table">
    <thead><tr><th>Name</th><th>Preis</th><th>Aktionen</th></tr></thead>
    <tbody>{rows if rows else '<tr><td colspan="3" style="color:#444;text-align:center;padding:16px">Keine Items</td></tr>'}</tbody>
  </table>
</div>
"""
    return render("shop", content, msg=msg, msg_type=msg_type)


# \u2500\u2500 Warns \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/warns")
def warns_page():
    r = require_login()
    if r:
        return r

    warns = load_json(WARNS_FILE)
    msg = request.args.get("_msg")

    rows = ""
    for uid, user_warns in warns.items():
        if not user_warns:
            continue
        count = len(user_warns)
        badge = "badge-red" if count >= 3 else "badge-orange" if count >= 2 else "badge-green"
        latest = user_warns[-1].get("reason", "Kein Grund") if user_warns else "-"
        latest_by = user_warns[-1].get("by_name", "Unbekannt") if user_warns else "-"
        rows += f"""<tr>
          <td><code style="color:#888;font-size:11px">{uid}</code></td>
          <td><span class="badge {badge}">{count} Warn(s)</span></td>
          <td style="max-width:240px;overflow:hidden;text-overflow:ellipsis">{latest}</td>
          <td>{latest_by}</td>
          <td>
            <a href="/warns/{uid}" class="btn btn-secondary btn-sm">Details</a>
            <form method="post" action="/warns/clear" style="display:inline;margin-left:4px">
              <input type="hidden" name="uid" value="{uid}">
              <button class="btn btn-danger btn-sm" onclick="return confirm('Alle Warns l\u00F6schen?')" type="submit">Alle \u274C</button>
            </form>
          </td>
        </tr>"""

    content = f"""
<h1>\u26A0\uFE0F Verwarnungen</h1>
<div class="subtitle">Alle Spieler mit aktiven Verwarnungen</div>

<div class="table-wrap">
  <div class="table-header">
    <h2>Warn-Liste</h2>
    <input class="search-bar" type="text" placeholder="\U0001F50D Suchen..." oninput="filterTable(this,'warn-table')" style="width:180px">
  </div>
  <table id="warn-table">
    <thead><tr><th>User ID</th><th>Anzahl</th><th>Letzter Grund</th><th>Von</th><th>Aktionen</th></tr></thead>
    <tbody>{rows if rows else '<tr><td colspan="5" style="color:#444;text-align:center;padding:16px">Keine Verwarnungen vorhanden</td></tr>'}</tbody>
  </table>
</div>
"""
    return render("warns", content, msg=msg)


@app.route("/warns/<uid>")
def warn_detail(uid):
    r = require_login()
    if r:
        return r

    warns = load_json(WARNS_FILE)
    user_warns = warns.get(uid, [])
    msg = request.args.get("_msg")

    rows = ""
    for i, w in enumerate(user_warns):
        reason = w.get("reason", "Kein Grund")
        by     = w.get("by_name", "Unbekannt")
        at     = w.get("timestamp", "")[:16].replace("T", " ") if w.get("timestamp") else ""
        rows += f"""<tr>
          <td>{i+1}</td>
          <td>{reason}</td>
          <td>{by}</td>
          <td>{at}</td>
          <td>
            <form method="post" action="/warns/remove">
              <input type="hidden" name="uid" value="{uid}">
              <input type="hidden" name="index" value="{i}">
              <input type="hidden" name="redirect" value="/warns/{uid}">
              <button class="btn btn-danger btn-sm" type="submit">\u274C Entfernen</button>
            </form>
          </td>
        </tr>"""

    content = f"""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
  <a href="/warns" class="btn btn-secondary">\u2190 Zur\u00FCck</a>
  <div>
    <h1>\u26A0\uFE0F Warns f\u00FCr #{uid[-6:]}</h1>
    <div class="subtitle" style="margin-bottom:0">ID: {uid} &mdash; {len(user_warns)} Verwarnung(en)</div>
  </div>
</div>
<div class="table-wrap">
  <table>
    <thead><tr><th>#</th><th>Grund</th><th>Von</th><th>Zeitpunkt</th><th>Aktion</th></tr></thead>
    <tbody>{rows if rows else '<tr><td colspan="5" style="color:#444;text-align:center;padding:16px">Keine Warns</td></tr>'}</tbody>
  </table>
</div>
"""
    return render("warns", content, msg=msg)


@app.route("/warns/remove", methods=["POST"])
def warns_remove():
    r = require_login()
    if r:
        return r
    uid      = request.form.get("uid", "")
    index    = request.form.get("index", "")
    redir    = request.form.get("redirect", "/warns")
    warns = load_json(WARNS_FILE)
    user_warns = warns.get(uid, [])
    try:
        idx = int(index)
        user_warns.pop(idx)
        warns[uid] = user_warns
        save_json(WARNS_FILE, warns)
        msg = "\u2705 Verwarnung entfernt"
    except Exception as e:
        msg = f"\u274C Fehler: {e}"
    return redirect(redir + f"?_msg={msg}")


@app.route("/warns/clear", methods=["POST"])
def warns_clear():
    r = require_login()
    if r:
        return r
    uid = request.form.get("uid", "")
    warns = load_json(WARNS_FILE)
    warns[uid] = []
    save_json(WARNS_FILE, warns)
    return redirect(f"/warns?_msg=\u2705+Alle+Warns+gel\u00F6scht")


# \u2500\u2500 Dashboard starten (Thread) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def start_dashboard():
    if not DASHBOARD_PASSWORD and not os.environ.get("DASHBOARD_OPEN"):
        print("[dashboard] \u26A0\uFE0F DASHBOARD_PASSWORD nicht gesetzt \u2014 Dashboard deaktiviert")
        return
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    print(f"[dashboard] \U0001F30D Dashboard startet auf Port {DASHBOARD_PORT}")
    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=False, use_reloader=False)
