# -*- coding: utf-8 -*-
# dashboard.py \u2014 Web-Dashboard f\u00FCr Paradise City Roleplay Bot
# 3-Stufen Rollen-System: Mod / Admin / Inhaber

import os
import json
import threading
from pathlib import Path
from datetime import datetime, timezone
from flask import Flask, render_template_string, request, session, redirect, url_for

DATA_DIR        = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
ECONOMY_FILE    = DATA_DIR / "economy_data.json"
SHOP_FILE       = DATA_DIR / "shop_data.json"
WARNS_FILE      = DATA_DIR / "warns_data.json"
TEAM_WARNS_FILE = DATA_DIR / "team_warns_data.json"

# Rollen-Passw\u00F6rter (in Railway als ENV-Variablen setzen)
_MOD_PW     = os.environ.get("DASHBOARD_MOD_PW", "")
_ADMIN_PW   = os.environ.get("DASHBOARD_ADMIN_PW", "")
_INHABER_PW = os.environ.get("DASHBOARD_INHABER_PW",
              os.environ.get("DASHBOARD_PASSWORD", ""))  # Backward-Compat

DASHBOARD_PORT = int(os.environ.get("PORT", os.environ.get("DASHBOARD_PORT", "8080")))

ROLE_LEVEL = {"mod": 1, "admin": 2, "inhaber": 3}

BOT_SYSTEMS = [
    ("Economy System",         "economy_data.json"),
    ("Shop System",            "shop_data.json"),
    ("Warn System",            "warns_data.json"),
    ("Team Warn System",       "team_warns_data.json"),
    ("Ticket System",          "ticket_msg.json"),
    ("Casino System",          "casino_cooldown.json"),
    ("Lotto System",           "lotto_msg.json"),
    ("Aktien System",          "aktien_data.json"),
    ("Handy System",           "handy_numbers.json"),
    ("Ausweis System",         "ausweis_data.json"),
    ("F\u00FChrerschein System",     "fuehrerschein_data.json"),
    ("Dienst System",          "duty_status.json"),
    ("Rechnungs System",       "rechnungen_data.json"),
    ("Lohnliste",              "lohnliste_msg.json"),
    ("Staatsbank Raub",        "sb_raid_data.json"),
    ("Humane Labs Raub",       "hl_raid_data.json"),
    ("Raub\u00FCberfall (Bar)",    "raubueberfall_msg.json"),
    ("Nebenserver Embed",      "nebenserver_msg.json"),
    ("Startinfo Embed",        "startinfo_msg.json"),
    ("Starterpaket Embed",     "starterpaket_msg.json"),
    ("Boost Embed",            "boost_msg.json"),
    ("Einreise Embed",         "einreise_msg.json"),
]

app = Flask(__name__)
app.secret_key = os.environ.get("DASHBOARD_SECRET", "pcrp-dashboard-2025")
_lock = threading.Lock()


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

def get_role():
    return session.get("role", "")

def logged_in():
    return get_role() in ROLE_LEVEL

def has_role(min_role):
    return ROLE_LEVEL.get(get_role(), 0) >= ROLE_LEVEL.get(min_role, 99)

def require_login():
    if not logged_in():
        return redirect(url_for("login"))
    return None

def require_role(min_role):
    if not logged_in():
        return redirect(url_for("login"))
    if not has_role(min_role):
        return _forbidden()
    return None

def _forbidden():
    return render_template_string("""<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><title>Kein Zugriff</title>
<style>body{background:#0b0b12;color:#ddd;font-family:'Segoe UI',sans-serif;
display:flex;align-items:center;justify-content:center;min-height:100vh}
.box{background:#13131e;border:1px solid #922b21;border-radius:11px;padding:38px;
text-align:center;max-width:360px}h1{color:#e74c3c;font-size:22px;margin-bottom:10px}
p{color:#555;font-size:13px;margin-bottom:20px}
a{background:#1c1c2e;color:#888;padding:9px 20px;border-radius:6px;text-decoration:none;
font-size:13px}a:hover{color:#fff}</style></head>
<body><div class="box">
<h1>\u274C Kein Zugriff</h1>
<p>Du hast keine Berechtigung f\u00FCr diesen Bereich.<br>
Deine Rolle: <b>{{ role }}</b></p>
<a href="/">\u2190 Zur\u00FCck</a>
</div></body></html>""", role=get_role() or "nicht angemeldet"), 403


# \u2500\u2500 CSS & Basis-Template \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
BASE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paradise City Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0b12;color:#ddd;font-family:'Segoe UI',sans-serif;min-height:100vh}
a{color:inherit;text-decoration:none}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-thumb{background:#e67e22;border-radius:3px}
.sidebar{position:fixed;left:0;top:0;width:230px;height:100vh;background:#0f0f1a;border-right:1px solid #1c1c2e;display:flex;flex-direction:column;z-index:100;overflow-y:auto}
.logo{padding:22px 20px 14px;border-bottom:1px solid #1c1c2e}
.logo-title{color:#e67e22;font-size:18px;font-weight:800;letter-spacing:.4px}
.logo-sub{color:#444;font-size:11px;margin-top:2px}
.role-badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;margin-top:5px}
.rb-mod{background:#12243a;color:#3498db}
.rb-admin{background:#2a1a3a;color:#9b59b6}
.rb-inhaber{background:#3a2710;color:#e67e22}
.nav-section{padding:10px 0 4px 20px;font-size:10px;color:#333;text-transform:uppercase;letter-spacing:1px;font-weight:700}
.nav a{display:flex;align-items:center;gap:10px;padding:10px 20px;color:#666;font-size:13px;transition:.12s;border-left:2px solid transparent}
.nav a:hover{color:#ccc;background:#141424}
.nav a.active{color:#e67e22;background:#171726;border-left-color:#e67e22}
.nav a .ic{font-size:15px;width:18px;text-align:center}
.sidebar-foot{padding:14px 20px;border-top:1px solid #1c1c2e;font-size:11px;color:#333;margin-top:auto}
.main{margin-left:230px;padding:26px 30px;min-height:100vh}
h1{font-size:21px;font-weight:700;margin-bottom:2px}
.sub{color:#444;font-size:12px;margin-bottom:22px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px;margin-bottom:24px}
.card{background:#13131e;border:1px solid #1c1c2e;border-radius:9px;padding:18px}
.card-lbl{font-size:10px;color:#444;text-transform:uppercase;letter-spacing:.8px;margin-bottom:5px}
.card-val{font-size:26px;font-weight:700;color:#e67e22}
.card-sub{font-size:11px;color:#333;margin-top:3px}
.tbl-wrap{background:#13131e;border:1px solid #1c1c2e;border-radius:9px;overflow:hidden;margin-bottom:20px}
.tbl-head{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid #1c1c2e;gap:10px;flex-wrap:wrap}
.tbl-head h2{font-size:13px;font-weight:600;color:#bbb}
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:9px 18px;font-size:10px;color:#444;text-transform:uppercase;letter-spacing:.6px;border-bottom:1px solid #181828}
td{padding:10px 18px;font-size:13px;border-bottom:1px solid #14142a;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#14142a}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700}
.g{background:#1a3a28;color:#2ecc71}
.r{background:#3a1212;color:#e74c3c}
.o{background:#3a2710;color:#e67e22}
.b{background:#12243a;color:#3498db}
.pu{background:#2a1a3a;color:#9b59b6}
.btn{display:inline-flex;align-items:center;gap:5px;padding:6px 14px;border-radius:6px;font-size:12px;font-weight:700;cursor:pointer;border:none;transition:.12s;text-decoration:none}
.btn-p{background:#e67e22;color:#fff}.btn-p:hover{background:#d35400}
.btn-d{background:#922b21;color:#fff}.btn-d:hover{background:#c0392b}
.btn-s{background:#1c1c2e;color:#888;border:1px solid #2a2a3a}.btn-s:hover{color:#fff}
.btn-sm{padding:3px 9px;font-size:11px}
.frm{background:#13131e;border:1px solid #1c1c2e;border-radius:9px;padding:18px;margin-bottom:18px}
.frm h2{font-size:13px;font-weight:600;color:#999;margin-bottom:13px}
.row{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:13px}
.fg{display:flex;flex-direction:column;gap:4px;flex:1;min-width:140px}
label{font-size:10px;color:#555;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
input,select{background:#0a0a15;border:1px solid #1c1c2e;color:#ddd;padding:8px 11px;border-radius:6px;font-size:13px;outline:none;width:100%;font-family:inherit}
input:focus,select:focus{border-color:#e67e22}
.alert{padding:10px 14px;border-radius:7px;font-size:12px;margin-bottom:14px}
.alert-ok{background:#152b1e;border:1px solid #27ae60;color:#2ecc71}
.alert-err{background:#2c1010;border:1px solid #922b21;color:#e74c3c}
.sb{background:#0a0a15;border:1px solid #1c1c2e;color:#ddd;padding:7px 12px;border-radius:6px;font-size:12px;outline:none;width:200px}
.sb:focus{border-color:#e67e22}
.inv-list{display:flex;flex-direction:column;gap:5px;max-height:200px;overflow-y:auto;margin:8px 0}
.inv-item{display:flex;align-items:center;justify-content:space-between;background:#0a0a15;border:1px solid #1c1c2e;border-radius:5px;padding:6px 10px;font-size:12px}
.rm{color:#922b21;cursor:pointer;font-weight:700;font-size:15px;line-height:1;padding:0 3px;background:none;border:none}.rm:hover{color:#e74c3c}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px;margin-bottom:20px}
.pc{background:#13131e;border:1px solid #1c1c2e;border-radius:9px;padding:14px;text-align:center;cursor:pointer;transition:.12s}
.pc:hover{border-color:#e67e22;transform:translateY(-1px)}
.pc .av{width:46px;height:46px;border-radius:50%;background:#1c1c2e;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;font-size:20px}
.pc .nm{font-size:12px;font-weight:700;margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pc .id{font-size:10px;color:#333;margin-bottom:7px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pc .mn{display:flex;justify-content:center;gap:10px;font-size:10px}
.pc .mn span{color:#444}.pc .mn b{color:#e67e22}
.sys-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:20px}
.sys-card{background:#13131e;border:1px solid #1c1c2e;border-radius:9px;padding:16px;display:flex;align-items:center;justify-content:space-between}
.sys-name{font-size:13px;font-weight:600}
.sys-sub{font-size:10px;color:#444;margin-top:2px}
.dot-on{width:10px;height:10px;border-radius:50%;background:#2ecc71;box-shadow:0 0 6px #2ecc71;flex-shrink:0}
.dot-off{width:10px;height:10px;border-radius:50%;background:#555;flex-shrink:0}
@media(max-width:700px){.sidebar{width:100%;height:auto;position:relative}.main{margin-left:0}}
</style>
</head>
<body>
<div class="sidebar">
  <div class="logo">
    <div class="logo-title">Paradise City</div>
    <div class="logo-sub">Bot Dashboard</div>
    {% if role == 'mod' %}<span class="role-badge rb-mod">\U0001F6E1\uFE0F Moderator</span>
    {% elif role == 'admin' %}<span class="role-badge rb-admin">\u2699\uFE0F Administrator</span>
    {% elif role == 'inhaber' %}<span class="role-badge rb-inhaber">\U0001F451 Inhaber</span>{% endif %}
  </div>
  <nav class="nav">
    <div class="nav-section">Hauptmen\u00FC</div>
    <a href="/" class="{{ 'active' if page=='home' }}"><span class="ic">\U0001F3E0</span> \u00DCbersicht</a>
    {% if role == 'inhaber' %}
    <a href="/systeme" class="{{ 'active' if page=='systeme' }}"><span class="ic">\U0001F7E2</span> Bot Systeme</a>
    {% endif %}
    <div class="nav-section">Spieler</div>
    <a href="/spieler" class="{{ 'active' if page=='spieler' }}"><span class="ic">\U0001F465</span> Spielerliste</a>
    {% if role in ('admin','inhaber') %}
    <a href="/konten" class="{{ 'active' if page=='konten' }}"><span class="ic">\U0001F4B0</span> Kontost\u00E4nde</a>
    <a href="/inventar" class="{{ 'active' if page=='inventar' }}"><span class="ic">\U0001F392</span> Inventare</a>
    <a href="/shop" class="{{ 'active' if page=='shop' }}"><span class="ic">\U0001F6D2</span> Shop</a>
    <a href="/cooldowns" class="{{ 'active' if page=='cooldowns' }}"><span class="ic">\u23F1\uFE0F</span> Cooldowns</a>
    {% endif %}
    <div class="nav-section">Moderation</div>
    <a href="/warns" class="{{ 'active' if page=='warns' }}"><span class="ic">\u26A0\uFE0F</span> Verwarnungen</a>
    {% if role in ('admin','inhaber') %}
    <a href="/teamwarns" class="{{ 'active' if page=='teamwarns' }}"><span class="ic">\U0001F6E1\uFE0F</span> Team Warns</a>
    {% endif %}
    <div class="nav-section">Account</div>
    <a href="/logout"><span class="ic">\U0001F6AA</span> Abmelden</a>
  </nav>
  <div class="sidebar-foot">Paradise City RP &copy; 2025</div>
</div>
<div class="main">
  {% if msg %}<div class="alert alert-{{ mtype }}">{{ msg }}</div>{% endif %}
  {{ content | safe }}
</div>
<script>
function ft(inp,tid){const q=inp.value.toLowerCase();document.querySelectorAll('#'+tid+' tbody tr').forEach(r=>{r.style.display=r.textContent.toLowerCase().includes(q)?'':'none'})}
function fc(inp){const q=inp.value.toLowerCase();document.querySelectorAll('.pc').forEach(c=>{c.style.display=c.textContent.toLowerCase().includes(q)?'':'none'})}
</script>
</body></html>"""


def render(page, content, msg=None, mtype="alert-ok"):
    return render_template_string(BASE, page=page, content=content,
                                  msg=msg, mtype=mtype, role=get_role())


# \u2500\u2500 Login \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
LOGIN = """<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login \u2014 Paradise City Dashboard</title>
<style>*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0b12;color:#ddd;font-family:'Segoe UI',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#13131e;border:1px solid #1c1c2e;border-radius:11px;padding:38px;width:360px}
h1{color:#e67e22;font-size:20px;font-weight:800;margin-bottom:3px}
p{color:#444;font-size:12px;margin-bottom:22px}
label{display:block;font-size:10px;color:#555;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;font-weight:700}
input{width:100%;background:#0a0a15;border:1px solid #1c1c2e;color:#ddd;padding:10px 13px;border-radius:6px;font-size:13px;outline:none;margin-bottom:14px}
input:focus{border-color:#e67e22}
button{width:100%;background:#e67e22;color:#fff;border:none;padding:11px;border-radius:6px;font-size:13px;font-weight:800;cursor:pointer}
button:hover{background:#d35400}
.err{background:#2c1010;border:1px solid #922b21;color:#e74c3c;padding:9px 13px;border-radius:6px;font-size:12px;margin-bottom:12px}
.roles{display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap}
.role-info{flex:1;min-width:90px;background:#0a0a15;border:1px solid #1c1c2e;border-radius:7px;padding:10px;text-align:center}
.role-info .ri{font-size:18px;margin-bottom:3px}
.role-info .rn{font-size:11px;font-weight:700}
.role-info .rd{font-size:10px;color:#444;margin-top:2px}
</style></head>
<body><div class="box">
  <h1>Paradise City</h1>
  <p>Bot Dashboard &mdash; Anmelden</p>
  <div class="roles">
    <div class="role-info"><div class="ri">\U0001F6E1\uFE0F</div><div class="rn" style="color:#3498db">Moderator</div><div class="rd">Warns &amp; Spieler</div></div>
    <div class="role-info"><div class="ri">\u2699\uFE0F</div><div class="rn" style="color:#9b59b6">Admin</div><div class="rd">Economy &amp; Shop</div></div>
    <div class="role-info"><div class="ri">\U0001F451</div><div class="rn" style="color:#e67e22">Inhaber</div><div class="rd">Vollzugriff</div></div>
  </div>
  {% if error %}<div class="err">\u274C {{ error }}</div>{% endif %}
  <form method="post">
    <label>Passwort</label>
    <input type="password" name="password" autofocus placeholder="Passwort eingeben...">
    <button type="submit">Anmelden</button>
  </form>
</div></body></html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if not (_MOD_PW or _ADMIN_PW or _INHABER_PW):
        session["role"] = "inhaber"
        return redirect("/")
    err = None
    if request.method == "POST":
        pw = request.form.get("password", "")
        if _INHABER_PW and pw == _INHABER_PW:
            session["role"] = "inhaber"
            return redirect("/")
        elif _ADMIN_PW and pw == _ADMIN_PW:
            session["role"] = "admin"
            return redirect("/")
        elif _MOD_PW and pw == _MOD_PW:
            session["role"] = "mod"
            return redirect("/")
        else:
            err = "Falsches Passwort"
    return render_template_string(LOGIN, error=err)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# \u2500\u2500 \u00DCbersicht \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/")
def home():
    r = require_login()
    if r: return r
    eco   = load_json(ECONOMY_FILE)
    shop  = load_json(SHOP_FILE, default=[])
    warns = load_json(WARNS_FILE)
    twarn = load_json(TEAM_WARNS_FILE)

    total_cash  = sum(int(v.get("cash", 0)) for v in eco.values())
    total_bank  = sum(int(v.get("bank", 0)) for v in eco.values())
    total_warns = sum(len(v) for v in warns.values() if isinstance(v, list))
    total_tw    = sum(len(v) for v in twarn.values() if isinstance(v, list))

    richest = sorted(eco.items(), key=lambda x: int(x[1].get("bank",0))+int(x[1].get("cash",0)), reverse=True)[:5]
    top_rows = ""
    for uid, d in richest:
        t = int(d.get("cash",0)) + int(d.get("bank",0))
        top_rows += f"<tr><td><code style='color:#555;font-size:11px'>{uid}</code></td><td style='color:#e67e22;font-weight:700'>${fmt(d.get('cash',0))}</td><td style='color:#3498db;font-weight:700'>${fmt(d.get('bank',0))}</td><td style='font-weight:700'>${fmt(t)}</td></tr>"

    role = get_role()
    role_name = {"mod": "\U0001F6E1\uFE0F Moderator", "admin": "\u2699\uFE0F Administrator", "inhaber": "\U0001F451 Inhaber"}.get(role, "")

    content = f"""
<h1>\U0001F3E0 \u00DCbersicht</h1>
<div class="sub">Paradise City Roleplay &mdash; Angemeldet als <b>{role_name}</b></div>
<div class="cards">
  <div class="card"><div class="card-lbl">Spieler gesamt</div><div class="card-val">{len(eco)}</div></div>
  <div class="card"><div class="card-lbl">Geld im Umlauf (Bar)</div><div class="card-val">${fmt(total_cash)}</div></div>
  <div class="card"><div class="card-lbl">Geld im Umlauf (Bank)</div><div class="card-val">${fmt(total_bank)}</div></div>
  <div class="card"><div class="card-lbl">Shop Items</div><div class="card-val">{len(shop) if isinstance(shop,list) else 0}</div></div>
  <div class="card"><div class="card-lbl">Spieler Warns</div><div class="card-val">{total_warns}</div></div>
  <div class="card"><div class="card-lbl">Team Warns</div><div class="card-val">{total_tw}</div></div>
</div>
<div class="tbl-wrap">
  <div class="tbl-head"><h2>\U0001F451 Top 5 Reichste Spieler</h2></div>
  <table><thead><tr><th>User ID</th><th>Bar</th><th>Bank</th><th>Gesamt</th></tr></thead>
  <tbody>{top_rows}</tbody></table>
</div>"""
    return render("home", content)


# \u2500\u2500 Bot Systeme (nur Inhaber) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/systeme")
def systeme():
    r = require_role("inhaber")
    if r: return r
    cards = ""
    online = 0
    for name, fname in BOT_SYSTEMS:
        exists = (DATA_DIR / fname).exists()
        if exists: online += 1
        dot   = '<div class="dot-on"></div>' if exists else '<div class="dot-off"></div>'
        badge = '<span class="badge g">Online</span>' if exists else '<span class="badge" style="background:#1a1a1a;color:#555">Keine Daten</span>'
        cards += f"""<div class="sys-card">
  <div><div class="sys-name">{name}</div><div class="sys-sub">{fname}</div></div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px">{badge}{dot}</div>
</div>"""
    content = f"""
<h1>\U0001F7E2 Bot Systeme</h1>
<div class="sub">{online} von {len(BOT_SYSTEMS)} Systemen aktiv (Datei vorhanden)</div>
<div class="sys-grid">{cards}</div>"""
    return render("systeme", content)


# \u2500\u2500 Spielerliste (alle Rollen) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/spieler")
def spieler():
    r = require_login()
    if r: return r
    eco = load_json(ECONOMY_FILE)
    cards = ""
    for uid, d in eco.items():
        cash = int(d.get("cash", 0))
        bank = int(d.get("bank", 0))
        inv  = len(d.get("inventory", []))
        cards += f"""<div class="pc" onclick="location='/spieler/{uid}'">
  <div class="av">\U0001F464</div>
  <div class="nm" title="{uid}">#{uid[-6:]}</div>
  <div class="id">{uid}</div>
  <div class="mn"><div><span>Bar</span><br><b>${fmt(cash)}</b></div><div><span>Bank</span><br><b>${fmt(bank)}</b></div></div>
  <div style="margin-top:7px"><span class="badge b">{inv} Items</span></div>
</div>"""
    content = f"""
<h1>\U0001F465 Spielerliste</h1>
<div class="sub">{len(eco)} registrierte Spieler</div>
<div style="margin-bottom:14px"><input class="sb" style="width:100%;max-width:300px" type="text" placeholder="\U0001F50D Spieler suchen..." oninput="fc(this)"></div>
<div class="pgrid">{cards if cards else '<p style="color:#444">Keine Spieler gefunden</p>'}</div>"""
    return render("spieler", content)


@app.route("/spieler/<uid>", methods=["GET", "POST"])
def spieler_detail(uid):
    r = require_login()
    if r: return r

    eco   = load_json(ECONOMY_FILE)
    msg   = request.args.get("_msg")
    mtype = "alert-ok"
    role         = get_role()
    can_edit_money = has_role("admin")
    can_edit_inv   = has_role("mod")

    if uid not in eco:
        eco[uid] = {"cash":0,"bank":0,"inventory":[],"last_wage":None,
                    "daily_deposit":0,"daily_withdraw":0,"daily_transfer":0,
                    "daily_reset":None,"custom_limit":None,"dispo":0}

    data = eco[uid]

    if request.method == "POST":
        action = request.form.get("action","")
        if action in ("money","reset") and can_edit_money:
            if action == "money":
                try:
                    data["cash"] = int(request.form.get("cash",0))
                    data["bank"] = int(request.form.get("bank",0))
                    eco[uid] = data
                    save_json(ECONOMY_FILE, eco)
                    msg = "\u2705 Guthaben gespeichert"
                except Exception as e:
                    msg = f"\u274C {e}"; mtype="alert-err"
            else:
                data["cash"] = 0; data["bank"] = 0
                eco[uid] = data; save_json(ECONOMY_FILE, eco)
                msg = "\u2705 Guthaben zur\u00FCckgesetzt"
        elif action == "add_item" and can_edit_inv:
            item = request.form.get("item","").strip()
            if item:
                data.setdefault("inventory",[]).append(item)
                eco[uid]=data; save_json(ECONOMY_FILE,eco)
                msg = "\u2705 Item hinzugef\u00FCgt"
            else:
                msg="\u274C Kein Item eingegeben"; mtype="alert-err"
        elif action == "rm_item" and can_edit_inv:
            item = request.form.get("item","")
            inv = data.get("inventory",[])
            if item in inv:
                inv.remove(item); data["inventory"]=inv
                eco[uid]=data; save_json(ECONOMY_FILE,eco)
                msg="\u2705 Item entfernt"
            else:
                msg="\u274C Item nicht gefunden"; mtype="alert-err"
        else:
            msg="\u274C Keine Berechtigung"; mtype="alert-err"
        return redirect(f"/spieler/{uid}?_msg={msg}")

    inv = data.get("inventory",[])
    # Inventar: Mod+ darf bearbeiten (x-Button + Add)
    if can_edit_inv:
        inv_html = "".join(f"""<div class="inv-item"><span>{i}</span>
          <form method="post" style="margin:0"><input type="hidden" name="action" value="rm_item">
          <input type="hidden" name="item" value="{i.replace('"','&quot;')}">
          <button class="rm" type="submit">&times;</button></form></div>""" for i in inv)
    else:
        inv_html = "".join(f'<div class="inv-item"><span>{i}</span></div>' for i in inv)

    warns = load_json(WARNS_FILE)
    uw = warns.get(uid,[])
    w_rows = "".join(f"""<tr><td>{i+1}</td><td>{w.get('reason','')}</td><td>{w.get('by_name','')}</td>
      <td>{w.get('timestamp','')[:10]}</td>
      <td><form method="post" action="/warns/remove"><input type="hidden" name="uid" value="{uid}">
      <input type="hidden" name="idx" value="{i}"><input type="hidden" name="back" value="/spieler/{uid}">
      <button class="btn btn-d btn-sm" type="submit">\u274C</button></form></td></tr>""" for i,w in enumerate(uw))

    # Guthaben: Admin+ darf bearbeiten, Mod nur lesen
    if can_edit_money:
        guthaben_html = f"""<div class="frm"><h2>\U0001F4B0 Guthaben bearbeiten</h2>
    <form method="post"><input type="hidden" name="action" value="money">
      <div class="row">
        <div class="fg"><label>Bar ($)</label><input type="number" name="cash" value="{int(data.get('cash',0))}"></div>
        <div class="fg"><label>Bank ($)</label><input type="number" name="bank" value="{int(data.get('bank',0))}"></div>
      </div>
      <div style="display:flex;gap:7px">
        <button class="btn btn-p" type="submit">\u2705 Speichern</button>
        <button class="btn btn-d" type="button" onclick="if(confirm('Wirklich auf $0 setzen?')){{document.querySelector('[name=action]').value='reset';this.closest('form').submit()}}">Zur\u00FCcksetzen</button>
      </div>
    </form></div>"""
    else:
        guthaben_html = f"""<div class="frm"><h2>\U0001F4B0 Guthaben (nur lesen)</h2>
    <div class="row">
      <div class="fg"><label>Bar ($)</label><div style="padding:9px;background:#0a0a15;border:1px solid #1c1c2e;border-radius:6px;color:#e67e22;font-weight:700">${fmt(data.get('cash',0))}</div></div>
      <div class="fg"><label>Bank ($)</label><div style="padding:9px;background:#0a0a15;border:1px solid #1c1c2e;border-radius:6px;color:#3498db;font-weight:700">${fmt(data.get('bank',0))}</div></div>
    </div></div>"""

    # Inventar: Mod+ darf bearbeiten
    if can_edit_inv:
        inventar_html = f"""<div class="frm"><h2>\U0001F392 Inventar ({len(inv)} Items)</h2>
    <div class="inv-list">{inv_html or '<span style="color:#333;font-size:12px">Leer</span>'}</div>
    <form method="post" style="display:flex;gap:7px;margin-top:9px">
      <input type="hidden" name="action" value="add_item">
      <input type="text" name="item" placeholder="Item hinzuf\u00FCgen...">
      <button class="btn btn-p" type="submit" style="white-space:nowrap">+ Add</button>
    </form></div>"""
    else:
        inventar_html = f"""<div class="frm"><h2>\U0001F392 Inventar ({len(inv)} Items)</h2>
    <div class="inv-list">{inv_html or '<span style="color:#333;font-size:12px">Leer</span>'}</div></div>"""

    content = f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:18px">
  <a href="/spieler" class="btn btn-s">\u2190 Zur\u00FCck</a>
  <div><h1>\U0001F464 Spieler #{uid[-6:]}</h1><div class="sub" style="margin:0">ID: {uid}</div></div>
</div>
{"<div class='alert "+mtype+"'>"+msg+"</div>" if msg else ""}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px">
{guthaben_html}
{inventar_html}
</div>
<div class="tbl-wrap"><div class="tbl-head"><h2>\u26A0\uFE0F Verwarnungen ({len(uw)})</h2></div>
  <table><thead><tr><th>#</th><th>Grund</th><th>Von</th><th>Datum</th><th>Aktion</th></tr></thead>
  <tbody>{w_rows or "<tr><td colspan='5' style='color:#333;text-align:center;padding:14px'>Keine Warns</td></tr>"}</tbody></table>
</div>"""
    return render("spieler", content)


# \u2500\u2500 Kontost\u00E4nde (Admin+) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/konten", methods=["GET","POST"])
def konten():
    r = require_role("admin")
    if r: return r
    eco = load_json(ECONOMY_FILE)
    msg = None; mtype = "alert-ok"

    if request.method == "POST":
        action = request.form.get("action","")
        uid = request.form.get("uid","").strip()
        if action == "save" and uid:
            try:
                if uid not in eco:
                    eco[uid]={"cash":0,"bank":0,"inventory":[],"last_wage":None,"daily_deposit":0,"daily_withdraw":0,"daily_transfer":0,"daily_reset":None,"custom_limit":None,"dispo":0}
                eco[uid]["cash"] = int(request.form.get("cash",0))
                eco[uid]["bank"] = int(request.form.get("bank",0))
                save_json(ECONOMY_FILE, eco)
                msg = f"\u2705 Konto {uid[-6:]} gespeichert"
            except Exception as e:
                msg=f"\u274C {e}"; mtype="alert-err"
        elif action == "add_all":
            try:
                betrag = int(request.form.get("betrag",0))
                ziel   = request.form.get("ziel","bank")
                for d in eco.values():
                    d[ziel] = int(d.get(ziel,0)) + betrag
                save_json(ECONOMY_FILE, eco)
                msg = f"\u2705 Allen Spielern ${fmt(betrag)} auf {ziel.capitalize()} hinzugef\u00FCgt"
            except Exception as e:
                msg=f"\u274C {e}"; mtype="alert-err"
        elif action == "reset_all":
            if has_role("inhaber"):
                for d in eco.values():
                    d["cash"]=0; d["bank"]=0
                save_json(ECONOMY_FILE, eco)
                msg = "\u2705 Alle Konten zur\u00FCckgesetzt"
            else:
                msg = "\u274C Nur Inhaber k\u00F6nnen alle Konten zur\u00FCcksetzen"; mtype="alert-err"

    rows = ""
    for uid, d in sorted(eco.items(), key=lambda x: int(x[1].get("bank",0))+int(x[1].get("cash",0)), reverse=True):
        rows += f"""<tr>
          <td><code style="font-size:11px;color:#555">{uid}</code></td>
          <td><b style="color:#e67e22">${fmt(d.get('cash',0))}</b></td>
          <td><b style="color:#3498db">${fmt(d.get('bank',0))}</b></td>
          <td><b>${fmt(int(d.get('cash',0))+int(d.get('bank',0)))}</b></td>
          <td><a href="/spieler/{uid}" class="btn btn-s btn-sm">Bearbeiten</a></td>
        </tr>"""

    reset_btn = ""
    if has_role("inhaber"):
        reset_btn = """<div class="frm"><h2>\u26A0\uFE0F Alle Konten zur\u00FCcksetzen</h2>
    <p style="color:#555;font-size:12px;margin-bottom:12px">Setzt Bar und Bank aller Spieler auf $0.</p>
    <form method="post"><input type="hidden" name="action" value="reset_all">
      <button class="btn btn-d" type="submit" onclick="return confirm('Wirklich ALLE Konten auf $0 setzen?')">\u274C Alle zur\u00FCcksetzen</button>
    </form></div>"""

    content = f"""
<h1>\U0001F4B0 Kontost\u00E4nde</h1>
<div class="sub">Alle Spielerkonten verwalten</div>
{"<div class='alert "+mtype+"'>"+msg+"</div>" if msg else ""}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px">
  <div class="frm"><h2>Allen Spielern Geld hinzuf\u00FCgen</h2>
    <form method="post"><input type="hidden" name="action" value="add_all">
      <div class="row">
        <div class="fg"><label>Betrag ($)</label><input type="number" name="betrag" placeholder="5000"></div>
        <div class="fg"><label>Konto</label><select name="ziel"><option value="cash">Bar</option><option value="bank">Bank</option></select></div>
      </div>
      <button class="btn btn-p" type="submit">\u2705 Allen hinzuf\u00FCgen</button>
    </form>
  </div>
  {reset_btn}
</div>
<div class="tbl-wrap">
  <div class="tbl-head"><h2>Alle Konten ({len(eco)})</h2>
    <input class="sb" type="text" placeholder="\U0001F50D Suchen..." oninput="ft(this,'kt')">
  </div>
  <table id="kt"><thead><tr><th>User ID</th><th>Bar</th><th>Bank</th><th>Gesamt</th><th>Aktion</th></tr></thead>
  <tbody>{rows}</tbody></table>
</div>"""
    return render("konten", content, msg=None)


# \u2500\u2500 Inventare (Admin+) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/inventar")
def inventar():
    r = require_role("admin")
    if r: return r
    eco = load_json(ECONOMY_FILE)
    rows = ""
    for uid, d in eco.items():
        inv = d.get("inventory",[])
        if not inv: continue
        from collections import Counter
        counts = Counter(inv)
        items_html = " ".join(f'<span class="badge b" style="margin:2px">{i}{"&times;"+str(c) if c>1 else ""}</span>' for i,c in counts.items())
        rows += f"""<tr>
          <td><code style="font-size:11px;color:#555">{uid}</code></td>
          <td>{len(inv)}</td>
          <td style="max-width:350px">{items_html}</td>
          <td><a href="/spieler/{uid}" class="btn btn-s btn-sm">Bearbeiten</a></td>
        </tr>"""
    content = f"""
<h1>\U0001F392 Inventare</h1>
<div class="sub">Alle Spieler mit Items im Inventar</div>
<div class="tbl-wrap">
  <div class="tbl-head"><h2>Inventar\u00FCbersicht</h2>
    <input class="sb" type="text" placeholder="\U0001F50D Suchen..." oninput="ft(this,'invt')">
  </div>
  <table id="invt"><thead><tr><th>User ID</th><th>Anzahl</th><th>Items</th><th>Aktion</th></tr></thead>
  <tbody>{rows or "<tr><td colspan='4' style='color:#333;text-align:center;padding:14px'>Keine Spieler mit Items</td></tr>"}</tbody></table>
</div>"""
    return render("inventar", content)


# \u2500\u2500 Shop (Admin+) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.route("/shop", methods=["GET","POST"])
def shop():
    r = require_role("admin")
    if r: return r
    items = load_json(SHOP_FILE, default=[])
    msg = None; mtype = "alert-ok"

    if request.method == "POST":
        action = request.form.get("action","")
        if action == "add":
            name = request.form.get("name","").strip()
            try:
                price = int(request.form.get("price",0))
                if not name: raise ValueError("Kein Name")
                items.append({"name":name,"price":price})
                save_json(SHOP_FILE, items)
                msg = f"\u2705 Item \"{name}\" hinzugef\u00FCgt"
            except Exception as e:
                msg=f"\u274C {e}"; mtype="alert-err"
        elif action == "del":
            name = request.form.get("name","")
            items = [i for i in items if i.get("name")!=name]
            save_json(SHOP_FILE, items)
            msg = "\u2705 Item gel\u00F6scht"
        elif action == "price":
            name = request.form.get("name","")
            try:
                price = int(request.form.get("price",0))
                for i in items:
                    if i.get("name")==name: i["price"]=price
                save_json(SHOP_FILE, items)
                msg = "\u2705 Preis gespeichert"
            except Exception as e:
                msg=f"\u274C {e}"; mtype="alert-err"

    rows = ""
    for item in (items if isinstance(items,list) else []):
        n = item.get("name",""); p = item.get("price",0)
        sn = n.replace('"','&quot;')
        rows += f"""<tr><td>{n}</td><td><b style="color:#e67e22">${fmt(p)}</b></td>
          <td><div style="display:flex;gap:6px;align-items:center">
            <form method="post" style="display:flex;gap:4px;align-items:center">
              <input type="hidden" name="action" value="price"><input type="hidden" name="name" value="{sn}">
              <input type="number" name="price" value="{p}" style="width:100px;padding:4px 7px;font-size:11px">
              <button class="btn btn-s btn-sm" type="submit">\u2713</button>
            </form>
            <form method="post"><input type="hidden" name="action" value="del"><input type="hidden" name="name" value="{sn}">
              <button class="btn btn-d btn-sm" onclick="return confirm('L\u00F6schen?')" type="submit">\u274C</button>
            </form>
          </div></td></tr>"""

    content = f"""
<h1>\U0001F6D2 Shop Verwaltung</h1>
<div class="sub">{len(items) if isinstance(items,list) else 0} Items im Shop</div>
{"<div class='alert "+mtype+"'>"+msg+"</div>" if msg else ""}
<div class="frm"><h2>+ Neues Item hinzuf\u00FCgen</h2>
  <form method="post"><input type="hidden" name="action" value="add">
    <div class="row">
      <div class="fg"><label>Name</label><input type="text" name="name" placeholder="z.B. \U0001F4F1| Handy"></div>
      <div class="fg" style="max-width:160px"><label>Preis ($)</label><input type="number" name="price" placeholder="5000" min="0"></div>
    </div>
    <button class="btn btn-p" type="submit">Item hinzuf\u00FCgen</button>
  </form>
</div>
<div class="tbl-wrap">
  <div class="tbl-head"><h2>Alle Shop Items</h2>
    <input class="sb" type="text" placeholder="\U0001F50D Suchen..." oninput="ft(this,'shopt')">
  </div>
  <table id="shopt"><thead><tr><th>Name</th><th>Preis</th><th>Aktionen</th></tr></thead>
  <tbody>{rows or "<tr><td colspan='3' style='color:#333;text-align:center;padding:14px'>Keine Items</td></tr>"}</tbody></table>
</div>"""
    return render("shop", content)


# \u2500\u2500 Cooldowns / Dispo / Tageslimit (Admin+) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
RAUB_KEYS = {
    "raub_last_raid":     "\U0001F37A Bar-Raub\u00FCberfall",
    "atm_last_raid":      "\U0001F3E7 ATM-Raub",
    "shop_raub_last_raid":"\U0001F6D2 Shop-Raub",
    "hl_last_raid":       "\U0001F9EA Humane Labs",
    "sb_last_raid":       "\U0001F3E6 Staatsbank",
}

LIMIT_OPTIONS = [0, 5000, 10000, 25000, 50000, 100000, 250000, 500000]

@app.route("/cooldowns", methods=["GET","POST"])
def cooldowns():
    r = require_role("admin")
    if r: return r

    eco = load_json(ECONOMY_FILE)
    msg = None; mtype = "alert-ok"

    if request.method == "POST":
        action = request.form.get("action","")
        uid    = request.form.get("uid","").strip()

        if not uid or uid not in eco:
            msg = "\u274C Spieler nicht gefunden"; mtype="alert-err"
        else:
            d = eco[uid]
            if action == "reset_cd":
                key = request.form.get("key","")
                if key in RAUB_KEYS:
                    d[key] = None
                    save_json(ECONOMY_FILE, eco)
                    msg = f"\u2705 {RAUB_KEYS[key]} Cooldown zur\u00FCckgesetzt"
                else:
                    msg = "\u274C Unbekannter Cooldown-Typ"; mtype="alert-err"
            elif action == "reset_all_cd":
                for k in RAUB_KEYS:
                    d[k] = None
                save_json(ECONOMY_FILE, eco)
                msg = "\u2705 Alle Cooldowns des Spielers zur\u00FCckgesetzt"
            elif action == "set_dispo":
                try:
                    betrag = int(request.form.get("betrag", 0))
                    if betrag < 0: raise ValueError("Muss 0 oder mehr sein")
                    d["dispo"] = betrag
                    save_json(ECONOMY_FILE, eco)
                    msg = f"\u2705 Dispo auf ${fmt(betrag)} gesetzt"
                except Exception as e:
                    msg = f"\u274C {e}"; mtype="alert-err"
            elif action == "set_limit":
                try:
                    limit = int(request.form.get("limit", 0))
                    d["custom_limit"] = limit if limit > 0 else None
                    save_json(ECONOMY_FILE, eco)
                    msg = f"\u2705 Tageslimit auf ${fmt(limit)} gesetzt" if limit > 0 else "\u2705 Tageslimit zur\u00FCckgesetzt (Standard)"
                except Exception as e:
                    msg = f"\u274C {e}"; mtype="alert-err"

    # Spieler mit aktiven Cooldowns sammeln
    cd_rows = ""
    for uid, d in eco.items():
        active = {k: v for k, v in d.items() if k in RAUB_KEYS and v}
        if not active: continue
        badges = " ".join(f'<span class="badge o">{RAUB_KEYS[k]}</span>' for k in active)
        cd_rows += f"""<tr>
          <td><code style="font-size:11px;color:#555">{uid}</code></td>
          <td style="max-width:280px">{badges}</td>
          <td>
            <form method="post" style="display:inline-flex;gap:5px;align-items:center">
              <input type="hidden" name="uid" value="{uid}">
              <input type="hidden" name="action" value="reset_all_cd">
              <button class="btn btn-d btn-sm" type="submit">\u23F1\uFE0F Alle zur\u00FCcksetzen</button>
            </form>
          </td>
        </tr>"""

    # Spieler mit Dispo oder custom Limit
    settings_rows = ""
    for uid, d in eco.items():
        dispo = int(d.get("dispo", 0))
        limit = d.get("custom_limit")
        if not dispo and limit is None: continue
        settings_rows += f"""<tr>
          <td><code style="font-size:11px;color:#555">{uid}</code></td>
          <td>{'<span class="badge r">-$'+fmt(dispo)+'</span>' if dispo else '<span style="color:#333">-</span>'}</td>
          <td>{'<span class="badge b">$'+fmt(limit)+'</span>' if limit else '<span style="color:#333">Standard</span>'}</td>
          <td><a href="/spieler/{uid}" class="btn btn-s btn-sm">Bearbeiten</a></td>
        </tr>"""

    uid_options = "".join(f'<option value="{uid}">#{uid[-6:]} ({uid})</option>' for uid in eco)
    key_options = "".join(f'<option value="{k}">{v}</option>' for k,v in RAUB_KEYS.items())
    limit_options = "".join(f'<option value="{l}">{"Standard (kein Limit)" if l==0 else "$"+fmt(l)}</option>' for l in LIMIT_OPTIONS)

    content = f"""
<h1>\u23F1\uFE0F Cooldowns & Einstellungen</h1>
<div class="sub">Raub-Cooldowns zur\u00FCcksetzen &mdash; Dispo & Tageslimit verwalten</div>
{"<div class='alert "+mtype+"'>"+msg+"</div>" if msg else ""}

<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-bottom:20px">
  <div class="frm"><h2>\u23F1\uFE0F Raub-Cooldown zur\u00FCcksetzen</h2>
    <form method="post">
      <input type="hidden" name="action" value="reset_cd">
      <div class="row">
        <div class="fg"><label>Spieler (User ID)</label><select name="uid"><option value="">-- Spieler w\u00E4hlen --</option>{uid_options}</select></div>
      </div>
      <div class="row">
        <div class="fg"><label>Raub</label><select name="key"><option value="">-- Raub w\u00E4hlen --</option>{key_options}</select></div>
      </div>
      <button class="btn btn-p" type="submit">\u23F1\uFE0F Cooldown zur\u00FCcksetzen</button>
    </form>
  </div>

  <div class="frm"><h2>\U0001F4CA Dispo-Limit setzen</h2>
    <form method="post">
      <input type="hidden" name="action" value="set_dispo">
      <div class="row">
        <div class="fg"><label>Spieler (User ID)</label><select name="uid"><option value="">-- Spieler w\u00E4hlen --</option>{uid_options}</select></div>
      </div>
      <div class="row">
        <div class="fg"><label>Dispo-Limit ($) &mdash; 0 = kein Dispo</label><input type="number" name="betrag" placeholder="0" min="0"></div>
      </div>
      <button class="btn btn-p" type="submit">\U0001F4CA Dispo setzen</button>
    </form>
  </div>

  <div class="frm"><h2>\u2699\uFE0F Tageslimit setzen</h2>
    <form method="post">
      <input type="hidden" name="action" value="set_limit">
      <div class="row">
        <div class="fg"><label>Spieler (User ID)</label><select name="uid"><option value="">-- Spieler w\u00E4hlen --</option>{uid_options}</select></div>
      </div>
      <div class="row">
        <div class="fg"><label>Tageslimit</label><select name="limit">{limit_options}</select></div>
      </div>
      <button class="btn btn-p" type="submit">\u2699\uFE0F Limit setzen</button>
    </form>
  </div>
</div>

<div class="tbl-wrap">
  <div class="tbl-head"><h2>\U0001F534 Aktive Raub-Cooldowns</h2></div>
  <table><thead><tr><th>User ID</th><th>Aktive Cooldowns</th><th>Aktion</th></tr></thead>
  <tbody>{cd_rows or "<tr><td colspan='3' style='color:#333;text-align:center;padding:14px'>Keine aktiven Cooldowns</td></tr>"}</tbody></table>
</div>

<div class="tbl-wrap">
  <div class="tbl-head"><h2>\U0001F4CA Dispo & Tageslimit-\u00DCbersicht</h2></div>
  <table><thead><tr><th>User ID</th><th>Dispo</th><th>Tageslimit</th><th>Aktion</th></tr></thead>
  <tbody>{settings_rows or "<tr><td colspan='4' style='color:#333;text-align:center;padding:14px'>Keine besonderen Einstellungen</td></tr>"}</tbody></table>
</div>"""
    return render("cooldowns", content)


# \u2500\u2500 Warns (alle Rollen) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def _warns_page(file, title, page_id, base_url):
    warns = load_json(file)
    rows = ""
    for uid, uw in warns.items():
        if not isinstance(uw, list) or not uw: continue
        c = len(uw)
        badge = f'<span class="badge {"r" if c>=3 else "o" if c>=2 else "g"}">{c}x</span>'
        last = uw[-1].get("reason","") if uw else ""
        by   = uw[-1].get("by_name","") if uw else ""
        rows += f"""<tr><td><code style="font-size:11px;color:#555">{uid}</code></td>
          <td>{badge}</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis">{last}</td><td>{by}</td>
          <td><div style="display:flex;gap:5px">
            <a href="{base_url}/{uid}" class="btn btn-s btn-sm">Details</a>
            <form method="post" action="{base_url}/clear"><input type="hidden" name="uid" value="{uid}">
              <button class="btn btn-d btn-sm" onclick="return confirm('Alle Warns l\u00F6schen?')" type="submit">Alle \u274C</button>
            </form>
          </div></td></tr>"""
    content = f"""
<h1>{title}</h1>
<div class="sub">{sum(len(v) for v in warns.values() if isinstance(v,list))} aktive Eintr\u00E4ge</div>
<div class="tbl-wrap">
  <div class="tbl-head"><h2>Liste</h2>
    <input class="sb" type="text" placeholder="\U0001F50D Suchen..." oninput="ft(this,'wt')">
  </div>
  <table id="wt"><thead><tr><th>User ID</th><th>Anzahl</th><th>Letzter Grund</th><th>Von</th><th>Aktionen</th></tr></thead>
  <tbody>{rows or "<tr><td colspan='5' style='color:#333;text-align:center;padding:14px'>Keine Eintr\u00E4ge</td></tr>"}</tbody></table>
</div>"""
    return render(page_id, content, msg=request.args.get("_msg"))


@app.route("/warns")
def warns_page():
    r = require_login()
    if r: return r
    return _warns_page(WARNS_FILE, "\u26A0\uFE0F Verwarnungen", "warns", "/warns")


@app.route("/teamwarns")
def teamwarns_page():
    r = require_role("admin")
    if r: return r
    return _warns_page(TEAM_WARNS_FILE, "\U0001F6E1\uFE0F Team Warns", "teamwarns", "/teamwarns")


def _warn_detail(file, uid, title, page_id, base_url):
    warns = load_json(file)
    uw    = warns.get(uid, [])
    msg   = request.args.get("_msg")

    rows = ""
    for i, w in enumerate(uw):
        reason = w.get("reason","").replace('"','&quot;')
        by     = w.get("by_name","").replace('"','&quot;')
        ts     = w.get("timestamp","")[:10]
        rows += f"""<tr>
          <td style="color:#555">{i+1}</td>
          <td>
            <form method="post" action="{base_url}/edit" style="display:flex;gap:5px;align-items:center">
              <input type="hidden" name="uid" value="{uid}">
              <input type="hidden" name="idx" value="{i}">
              <input type="hidden" name="back" value="{base_url}/{uid}">
              <input type="text" name="reason" value="{reason}" style="flex:1;padding:4px 8px;font-size:12px">
              <input type="text" name="by_name" value="{by}" style="width:110px;padding:4px 8px;font-size:12px" placeholder="Von">
              <button class="btn btn-s btn-sm" type="submit">\u2713</button>
            </form>
          </td>
          <td style="color:#555;font-size:11px">{ts}</td>
          <td>
            <form method="post" action="{base_url}/remove">
              <input type="hidden" name="uid" value="{uid}">
              <input type="hidden" name="idx" value="{i}">
              <input type="hidden" name="back" value="{base_url}/{uid}">
              <button class="btn btn-d btn-sm" type="submit">\u274C Entfernen</button>
            </form>
          </td>
        </tr>"""

    content = f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;flex-wrap:wrap;gap:10px">
  <div style="display:flex;align-items:center;gap:12px">
    <a href="{base_url}" class="btn btn-s">\u2190 Zur\u00FCck</a>
    <div><h1>{title} \u2014 #{uid[-6:]}</h1><div class="sub" style="margin:0">ID: {uid} &mdash; {len(uw)} Verwarnung(en)</div></div>
  </div>
  <form method="post" action="{base_url}/clear" style="margin:0">
    <input type="hidden" name="uid" value="{uid}">
    <button class="btn btn-d" onclick="return confirm('Alle Warns l\u00F6schen?')" type="submit">\u274C Alle l\u00F6schen</button>
  </form>
</div>

<div class="frm"><h2>+ Neue Verwarnung manuell hinzuf\u00FCgen</h2>
  <form method="post" action="{base_url}/add">
    <input type="hidden" name="uid" value="{uid}">
    <input type="hidden" name="back" value="{base_url}/{uid}">
    <div class="row">
      <div class="fg"><label>Grund</label><input type="text" name="reason" placeholder="z.B. Regelversto\u00DF" required></div>
      <div class="fg" style="max-width:180px"><label>Von (Name)</label><input type="text" name="by_name" placeholder="Mod-Name"></div>
    </div>
    <button class="btn btn-p" type="submit">\u26A0\uFE0F Warn hinzuf\u00FCgen</button>
  </form>
</div>

<div class="tbl-wrap">
  <div class="tbl-head"><h2>Alle Verwarnungen ({len(uw)})</h2></div>
  <table><thead><tr><th>#</th><th>Grund &amp; Von (bearbeitbar)</th><th>Datum</th><th>Aktion</th></tr></thead>
  <tbody>{rows or "<tr><td colspan='4' style='color:#333;text-align:center;padding:14px'>Keine Verwarnungen</td></tr>"}</tbody></table>
</div>"""
    return render(page_id, content, msg=msg)


@app.route("/warns/<uid>")
def warn_detail(uid):
    r = require_login()
    if r: return r
    return _warn_detail(WARNS_FILE, uid, "\u26A0\uFE0F Warns", "warns", "/warns")


@app.route("/teamwarns/<uid>")
def teamwarn_detail(uid):
    r = require_role("admin")
    if r: return r
    return _warn_detail(TEAM_WARNS_FILE, uid, "\U0001F6E1\uFE0F Team Warns", "teamwarns", "/teamwarns")


def _warns_remove(file, back_default):
    uid  = request.form.get("uid","")
    idx  = request.form.get("idx","")
    back = request.form.get("back", back_default)
    warns = load_json(file)
    try:
        warns.get(uid,[]).pop(int(idx))
        save_json(file, warns)
        msg = "\u2705 Eintrag entfernt"
    except Exception as e:
        msg = f"\u274C {e}"
    return redirect(f"{back}?_msg={msg}")


def _warns_clear(file, back):
    uid = request.form.get("uid","")
    warns = load_json(file)
    warns[uid] = []
    save_json(file, warns)
    return redirect(f"{back}?_msg=\u2705+Alle+Warns+gel\u00F6scht")


def _warns_add(file):
    uid    = request.form.get("uid","").strip()
    reason = request.form.get("reason","").strip()
    by     = request.form.get("by_name","Dashboard").strip()
    back   = request.form.get("back","/warns")
    warns  = load_json(file)
    if uid and reason:
        warns.setdefault(uid,[]).append({
            "reason":    reason,
            "by_name":   by or "Dashboard",
            "by_id":     0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        save_json(file, warns)
        msg = "\u2705 Verwarnung hinzugef\u00FCgt"
    else:
        msg = "\u274C Bitte UID und Grund angeben"
    return redirect(f"{back}?_msg={msg}")


def _warns_edit(file):
    uid    = request.form.get("uid","")
    idx    = request.form.get("idx","")
    reason = request.form.get("reason","").strip()
    by     = request.form.get("by_name","").strip()
    back   = request.form.get("back","/warns")
    warns  = load_json(file)
    try:
        w = warns.get(uid,[])[int(idx)]
        if reason: w["reason"] = reason
        if by:     w["by_name"] = by
        save_json(file, warns)
        msg = "\u2705 Verwarnung bearbeitet"
    except Exception as e:
        msg = f"\u274C {e}"
    return redirect(f"{back}?_msg={msg}")


@app.route("/warns/add",    methods=["POST"])
def warns_add():
    r = require_login()
    if r: return r
    return _warns_add(WARNS_FILE)

@app.route("/warns/edit",   methods=["POST"])
def warns_edit():
    r = require_login()
    if r: return r
    return _warns_edit(WARNS_FILE)

@app.route("/warns/remove", methods=["POST"])
def warns_remove():
    r = require_login()
    if r: return r
    return _warns_remove(WARNS_FILE, "/warns")

@app.route("/warns/clear",  methods=["POST"])
def warns_clear():
    r = require_login()
    if r: return r
    return _warns_clear(WARNS_FILE, "/warns")

@app.route("/teamwarns/add",    methods=["POST"])
def teamwarns_add():
    r = require_role("admin")
    if r: return r
    return _warns_add(TEAM_WARNS_FILE)

@app.route("/teamwarns/edit",   methods=["POST"])
def teamwarns_edit():
    r = require_role("admin")
    if r: return r
    return _warns_edit(TEAM_WARNS_FILE)

@app.route("/teamwarns/remove", methods=["POST"])
def teamwarns_remove():
    r = require_role("admin")
    if r: return r
    return _warns_remove(TEAM_WARNS_FILE, "/teamwarns")

@app.route("/teamwarns/clear",  methods=["POST"])
def teamwarns_clear():
    r = require_role("admin")
    if r: return r
    return _warns_clear(TEAM_WARNS_FILE, "/teamwarns")


# \u2500\u2500 Dashboard starten \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def start_dashboard():
    if not (_MOD_PW or _ADMIN_PW or _INHABER_PW) and not os.environ.get("DASHBOARD_OPEN"):
        print("[dashboard] \u26A0\uFE0F Kein Passwort gesetzt \u2014 Dashboard ohne Passwort ge\u00F6ffnet")
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    print(f"[dashboard] \U0001F30D Startet auf Port {DASHBOARD_PORT}")
    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=False, use_reloader=False)
