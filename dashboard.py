# -*- coding: utf-8 -*-
import json, os, sys, time, threading, asyncio, psutil
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
from flask import (Flask, render_template_string, redirect, url_for, request,
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

app = Flask(__name__)
app.secret_key = os.environ.get("DASHBOARD_SECRET", "pcrp-dash-secret-2026")
app.config["SESSION_PERMANENT"]        = False
app.config["SESSION_COOKIE_SAMESITE"]  = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"]  = True

_LOGIN_HTML = '<!DOCTYPE html>\n<html lang="de">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Paradise City \u2014 Login</title>\n<style>\n  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }\n\n  body {\n    min-height: 100vh;\n    display: flex;\n    align-items: center;\n    justify-content: center;\n    background: #0d0f14;\n    font-family: \'Segoe UI\', system-ui, sans-serif;\n    overflow: hidden;\n  }\n\n  body::before {\n    content: \'\';\n    position: fixed;\n    inset: 0;\n    background:\n      radial-gradient(ellipse 80% 60% at 20% 80%, rgba(99,102,241,0.18) 0%, transparent 60%),\n      radial-gradient(ellipse 60% 50% at 80% 20%, rgba(139,92,246,0.15) 0%, transparent 60%);\n    pointer-events: none;\n  }\n\n  .card {\n    background: rgba(255,255,255,0.04);\n    border: 1px solid rgba(255,255,255,0.08);\n    border-radius: 20px;\n    padding: 48px 44px;\n    width: 100%;\n    max-width: 420px;\n    backdrop-filter: blur(20px);\n    box-shadow: 0 24px 60px rgba(0,0,0,0.5);\n    position: relative;\n    z-index: 1;\n    animation: fadeUp .4s ease;\n  }\n\n  @keyframes fadeUp {\n    from { opacity:0; transform:translateY(20px); }\n    to   { opacity:1; transform:translateY(0); }\n  }\n\n  .logo {\n    text-align: center;\n    margin-bottom: 28px;\n  }\n\n  .logo-icon {\n    display: inline-flex;\n    width: 72px; height: 72px;\n    border-radius: 20px;\n    background: linear-gradient(135deg, #6366f1, #8b5cf6);\n    align-items: center;\n    justify-content: center;\n    font-size: 34px;\n    box-shadow: 0 8px 24px rgba(99,102,241,0.4);\n    margin-bottom: 18px;\n  }\n\n  h1 {\n    color: #fff;\n    font-size: 22px;\n    font-weight: 700;\n    text-align: center;\n    letter-spacing: .3px;\n  }\n\n  .sub {\n    color: rgba(255,255,255,0.45);\n    font-size: 13px;\n    text-align: center;\n    margin-top: 5px;\n    margin-bottom: 36px;\n    letter-spacing: .5px;\n    text-transform: uppercase;\n  }\n\n  .error {\n    background: rgba(239,68,68,0.12);\n    border: 1px solid rgba(239,68,68,0.3);\n    color: #f87171;\n    border-radius: 10px;\n    padding: 10px 14px;\n    font-size: 13px;\n    margin-bottom: 20px;\n    text-align: center;\n  }\n\n  .field-label {\n    color: rgba(255,255,255,0.5);\n    font-size: 11px;\n    letter-spacing: .6px;\n    text-transform: uppercase;\n    margin-bottom: 6px;\n    margin-top: 14px;\n  }\n\n  .input-wrap {\n    position: relative;\n    margin-bottom: 4px;\n  }\n\n  .input-wrap input {\n    width: 100%;\n    background: rgba(255,255,255,0.06);\n    border: 1px solid rgba(255,255,255,0.1);\n    border-radius: 12px;\n    color: #fff;\n    font-size: 15px;\n    padding: 13px 16px 13px 46px;\n    outline: none;\n    transition: border-color .2s, background .2s;\n  }\n\n  .input-wrap input::placeholder { color: rgba(255,255,255,0.25); }\n\n  .input-wrap input:focus {\n    border-color: rgba(99,102,241,0.6);\n    background: rgba(255,255,255,0.08);\n  }\n\n  .input-icon {\n    position: absolute;\n    left: 14px;\n    top: 50%;\n    transform: translateY(-50%);\n    font-size: 17px;\n    pointer-events: none;\n  }\n\n  .hint {\n    color: rgba(255,255,255,0.25);\n    font-size: 11px;\n    margin-top: 5px;\n    margin-bottom: 0;\n  }\n\n  .btn {\n    width: 100%;\n    padding: 14px;\n    border: none;\n    border-radius: 12px;\n    background: linear-gradient(135deg, #6366f1, #8b5cf6);\n    color: #fff;\n    font-size: 15px;\n    font-weight: 700;\n    cursor: pointer;\n    letter-spacing: .3px;\n    transition: opacity .2s, transform .1s;\n    box-shadow: 0 6px 20px rgba(99,102,241,0.35);\n    margin-top: 24px;\n  }\n\n  .btn:hover  { opacity: .9; }\n  .btn:active { transform: scale(.98); }\n\n  .footer-note {\n    text-align: center;\n    color: rgba(255,255,255,0.2);\n    font-size: 11px;\n    margin-top: 28px;\n    letter-spacing: .3px;\n  }\n</style>\n</head>\n<body>\n<div class="card">\n  <div class="logo">\n    <div class="logo-icon">&#x1F3D9;</div>\n    <h1>Paradise City</h1>\n    <p class="sub">Admin Dashboard</p>\n  </div>\n\n  {% if error %}\n  <div class="error">&#x274C; {{ error }}</div>\n  {% endif %}\n\n  <form method="POST" action="/login">\n    <div class="field-label">Discord User ID</div>\n    <div class="input-wrap">\n      <span class="input-icon">&#x1F194;</span>\n      <input type="text" name="discord_id" placeholder="z.B. 123456789012345678" autofocus required inputmode="numeric" pattern="[0-9]+">\n    </div>\n    <p class="hint">Rechtsklick auf deinen Namen in Discord &rarr; &bdquo;ID kopieren&ldquo;</p>\n\n    <div class="field-label">Passwort</div>\n    <div class="input-wrap">\n      <span class="input-icon">&#x1F512;</span>\n      <input type="password" name="password" placeholder="Passwort eingeben&#x2026;" required>\n    </div>\n\n    <button type="submit" class="btn">Einloggen</button>\n  </form>\n\n  <p class="footer-note">Nur f&uuml;r berechtigte Team-Mitglieder &mdash; Paradise City Roleplay</p>\n</div>\n</body>\n</html>\n'

_DASH_HTML = '<!DOCTYPE html>\n<html lang="de">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Paradise City Admin Dashboard</title>\n<style>\n*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }\n\n:root {\n  --orange-1: #FF6B00;\n  --orange-2: #FF8C00;\n  --orange-3: #FFA500;\n  --orange-4: #FFB347;\n  --dark-bg:  #0f0f13;\n  --card-bg:  #1a1a24;\n  --card-border: rgba(255,107,0,0.25);\n  --text:     #f0f0f0;\n  --text-dim: #9090a0;\n  --danger:   #e74c3c;\n  --success:  #2ecc71;\n  --sidebar-w: 240px;\n}\n\nbody {\n  font-family: \'Segoe UI\', system-ui, sans-serif;\n  background: var(--dark-bg);\n  color: var(--text);\n  display: flex;\n  min-height: 100vh;\n}\n\n/* \u2500\u2500 Sidebar \u2500\u2500 */\n.sidebar {\n  width: var(--sidebar-w);\n  flex-shrink: 0;\n  display: flex;\n  flex-direction: column;\n  background: linear-gradient(180deg, #18080a 0%, #0f0f13 100%);\n  border-right: 1px solid var(--card-border);\n  position: sticky;\n  top: 0;\n  height: 100vh;\n  overflow-y: auto;\n}\n.sidebar-header {\n  display: flex;\n  align-items: center;\n  gap: 10px;\n  padding: 20px 16px 16px;\n  border-bottom: 1px solid var(--card-border);\n}\n.sidebar-icon { font-size: 28px; }\n.sidebar-title {\n  font-weight: 700;\n  font-size: 14px;\n  background: linear-gradient(90deg, var(--orange-1), var(--orange-4));\n  -webkit-background-clip: text;\n  -webkit-text-fill-color: transparent;\n}\n.sidebar-sub { font-size: 11px; color: var(--text-dim); }\n.nav-list { list-style: none; padding: 10px 0; flex: 1; }\n.nav-item {\n  padding: 11px 18px;\n  font-size: 13.5px;\n  cursor: pointer;\n  border-left: 3px solid transparent;\n  transition: all .15s;\n  color: var(--text-dim);\n}\n.nav-item:hover { background: rgba(255,107,0,0.08); color: var(--text); }\n.nav-item.active {\n  border-left-color: var(--orange-1);\n  background: rgba(255,107,0,0.12);\n  color: var(--orange-3);\n  font-weight: 600;\n}\n.sidebar-footer { padding: 16px; border-top: 1px solid var(--card-border); }\n.btn-logout {\n  display: block;\n  text-align: center;\n  padding: 10px;\n  background: rgba(231,76,60,0.15);\n  border: 1px solid rgba(231,76,60,0.4);\n  border-radius: 8px;\n  color: #e74c3c;\n  text-decoration: none;\n  font-size: 13px;\n  transition: all .15s;\n}\n.btn-logout:hover { background: rgba(231,76,60,0.25); }\n\n/* \u2500\u2500 Main \u2500\u2500 */\n.main-content { flex: 1; padding: 28px 32px; overflow-x: hidden; }\n.section { display: none; }\n.section.active { display: block; }\n.section-title {\n  font-size: 22px;\n  font-weight: 700;\n  margin-bottom: 20px;\n  background: linear-gradient(90deg, var(--orange-1), var(--orange-4));\n  -webkit-background-clip: text;\n  -webkit-text-fill-color: transparent;\n}\n\n/* \u2500\u2500 Cards \u2500\u2500 */\n.card {\n  background: var(--card-bg);\n  border: 1px solid var(--card-border);\n  border-radius: 12px;\n  padding: 20px;\n}\n.card-title { font-size: 14px; font-weight: 600; color: var(--orange-3); margin-bottom: 14px; }\n.mt-20 { margin-top: 20px; }\n.mt-10 { margin-top: 10px; }\n\n/* \u2500\u2500 Stats \u2500\u2500 */\n.stats-grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));\n  gap: 14px;\n}\n.stat-card {\n  background: linear-gradient(135deg, #1a1a24, #1d0f00);\n  border: 1px solid var(--card-border);\n  border-radius: 12px;\n  padding: 18px 14px;\n  text-align: center;\n}\n.stat-val { font-size: 26px; font-weight: 700; color: var(--orange-3); }\n.stat-label { font-size: 12px; color: var(--text-dim); margin-top: 4px; }\n\n/* \u2500\u2500 Tables \u2500\u2500 */\n.toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }\n.search-input {\n  flex: 1;\n  min-width: 180px;\n  padding: 9px 14px;\n  background: var(--card-bg);\n  border: 1px solid var(--card-border);\n  border-radius: 8px;\n  color: var(--text);\n  font-size: 13px;\n  outline: none;\n}\n.search-input:focus { border-color: var(--orange-2); }\n.table-wrap { overflow-x: auto; }\n.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }\n.data-table th {\n  background: linear-gradient(90deg, rgba(255,107,0,0.2), rgba(255,140,0,0.1));\n  padding: 10px 12px;\n  text-align: left;\n  font-size: 12px;\n  color: var(--orange-4);\n  text-transform: uppercase;\n  letter-spacing: .5px;\n}\n.data-table td {\n  padding: 9px 12px;\n  border-bottom: 1px solid rgba(255,255,255,0.04);\n  vertical-align: top;\n}\n.data-table tr:hover td { background: rgba(255,107,0,0.05); }\n.loading { color: var(--text-dim); font-style: italic; }\n.uid-small { font-size: 11px; color: var(--text-dim); }\n\n/* \u2500\u2500 Tabs \u2500\u2500 */\n.tabs { display: flex; gap: 8px; margin-bottom: 16px; }\n.tab-btn {\n  padding: 8px 18px;\n  border: 1px solid var(--card-border);\n  border-radius: 8px;\n  background: var(--card-bg);\n  color: var(--text-dim);\n  cursor: pointer;\n  font-size: 13px;\n}\n.tab-btn.active {\n  background: linear-gradient(135deg, var(--orange-1), var(--orange-2));\n  color: #fff;\n  border-color: transparent;\n  font-weight: 600;\n}\n\n/* \u2500\u2500 Forms \u2500\u2500 */\n.form-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-start; }\n.form-input {\n  padding: 9px 12px;\n  background: #11111a;\n  border: 1px solid var(--card-border);\n  border-radius: 8px;\n  color: var(--text);\n  font-size: 13px;\n  outline: none;\n  flex: 1;\n  min-width: 100px;\n}\n.form-input:focus { border-color: var(--orange-2); }\n.form-select {\n  padding: 9px 12px;\n  background: #11111a;\n  border: 1px solid var(--card-border);\n  border-radius: 8px;\n  color: var(--text);\n  font-size: 13px;\n  outline: none;\n  min-width: 140px;\n}\n.form-msg { margin-top: 8px; font-size: 13px; }\n.form-msg.ok { color: var(--success); }\n.form-msg.err { color: var(--danger); }\n\n/* \u2500\u2500 Buttons \u2500\u2500 */\n.btn-primary {\n  padding: 9px 18px;\n  border: none;\n  border-radius: 8px;\n  cursor: pointer;\n  font-size: 13px;\n  font-weight: 600;\n  background: linear-gradient(135deg, var(--orange-1), var(--orange-2));\n  color: #fff;\n}\n.btn-primary:hover { opacity: .85; }\n.btn-secondary {\n  padding: 9px 14px;\n  border: 1px solid var(--card-border);\n  border-radius: 8px;\n  cursor: pointer;\n  font-size: 13px;\n  background: var(--card-bg);\n  color: var(--text);\n}\n.btn-secondary:hover { border-color: var(--orange-2); }\n.btn-danger {\n  padding: 5px 12px;\n  border: 1px solid rgba(231,76,60,0.4);\n  border-radius: 6px;\n  cursor: pointer;\n  font-size: 12px;\n  background: rgba(231,76,60,0.1);\n  color: var(--danger);\n}\n.btn-danger:hover { background: rgba(231,76,60,0.2); }\n.btn-success {\n  padding: 5px 12px;\n  border: 1px solid rgba(46,204,113,0.4);\n  border-radius: 6px;\n  cursor: pointer;\n  font-size: 12px;\n  background: rgba(46,204,113,0.1);\n  color: var(--success);\n}\n.btn-success:hover { background: rgba(46,204,113,0.2); }\n\n/* \u2500\u2500 Log list \u2500\u2500 */\n.log-list { display: flex; flex-direction: column; gap: 6px; }\n.log-entry {\n  background: var(--card-bg);\n  border: 1px solid var(--card-border);\n  border-radius: 8px;\n  padding: 10px 14px;\n  font-size: 13px;\n  border-left: 3px solid var(--orange-1);\n}\n.log-entry.type-GELD   { border-left-color: #2ecc71; }\n.log-entry.type-ITEM   { border-left-color: #3498db; }\n.log-entry.type-ROLLE  { border-left-color: #9b59b6; }\n.log-entry.type-BAN    { border-left-color: #e74c3c; }\n.log-entry.type-WARN   { border-left-color: #f39c12; }\n.log-entry.type-SERVER { border-left-color: #1abc9c; }\n.log-time { font-size: 11px; color: var(--text-dim); margin-top: 3px; }\n.warn-entry {\n  background: var(--card-bg);\n  border: 1px solid rgba(231,76,60,0.3);\n  border-radius: 8px;\n  padding: 12px 16px;\n  border-left: 3px solid var(--danger);\n}\n.warn-entry-title { font-weight: 600; font-size: 13px; color: #ff6b6b; }\n\n/* \u2500\u2500 Shop panels \u2500\u2500 */\n.shop-section {\n  margin-top: 20px;\n  background: var(--card-bg);\n  border: 1px solid var(--card-border);\n  border-radius: 12px;\n  overflow: hidden;\n}\n.shop-header {\n  padding: 12px 18px;\n  background: linear-gradient(90deg, rgba(255,107,0,0.2), transparent);\n  font-weight: 600;\n  font-size: 14px;\n  color: var(--orange-3);\n}\n.shop-item-row {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  padding: 9px 18px;\n  border-bottom: 1px solid rgba(255,255,255,0.04);\n  font-size: 13px;\n}\n.shop-item-row:last-child { border-bottom: none; }\n.item-price { color: var(--orange-3); font-weight: 600; }\n\n/* \u2500\u2500 Notes grid \u2500\u2500 */\n.notes-grid { display: flex; flex-direction: column; gap: 12px; }\n.note-card {\n  background: var(--card-bg);\n  border: 1px solid var(--card-border);\n  border-radius: 10px;\n  padding: 14px 18px;\n}\n.note-user { font-weight: 600; color: var(--orange-3); margin-bottom: 8px; font-size: 14px; }\n.note-entry {\n  display: flex;\n  justify-content: space-between;\n  align-items: flex-start;\n  padding: 6px 0;\n  border-bottom: 1px solid rgba(255,255,255,0.04);\n  font-size: 13px;\n}\n.note-entry:last-child { border-bottom: none; }\n.note-time { font-size: 11px; color: var(--text-dim); }\n\n/* \u2500\u2500 Features grid \u2500\u2500 */\n.features-grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));\n  gap: 10px;\n}\n.feature-item {\n  padding: 10px 14px;\n  border-radius: 8px;\n  font-size: 13px;\n  display: flex;\n  align-items: center;\n  gap: 8px;\n  background: rgba(255,255,255,0.04);\n  border: 1px solid var(--card-border);\n}\n.feature-ok  { border-color: rgba(46,204,113,0.3); }\n.feature-err { border-color: rgba(231,76,60,0.3); }\n\n/* \u2500\u2500 Live badge \u2500\u2500 */\n.live-badge {\n  background: rgba(46,204,113,0.15);\n  border: 1px solid rgba(46,204,113,0.4);\n  color: var(--success);\n  padding: 5px 12px;\n  border-radius: 20px;\n  font-size: 12px;\n}\n\n/* \u2500\u2500 Badges \u2500\u2500 */\n.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }\n.badge-red    { background: rgba(231,76,60,0.2); color: #e74c3c; }\n.badge-orange { background: rgba(255,107,0,0.2); color: var(--orange-3); }\n\n/* \u2500\u2500 Money \u2500\u2500 */\n.money     { color: var(--orange-3); font-weight: 600; }\n.money-neg { color: var(--danger); }\n\n/* \u2500\u2500 Scrollbar \u2500\u2500 */\n::-webkit-scrollbar { width: 6px; height: 6px; }\n::-webkit-scrollbar-track { background: transparent; }\n::-webkit-scrollbar-thumb { background: rgba(255,107,0,0.3); border-radius: 3px; }\n::-webkit-scrollbar-thumb:hover { background: rgba(255,107,0,0.5); }\n</style>\n</head>\n<body>\n\n<!-- SIDEBAR -->\n<nav class="sidebar">\n  <div class="sidebar-header">\n    <span class="sidebar-icon">&#x1F3D9;&#xFE0F;</span>\n    <div>\n      <div class="sidebar-title">Paradise City</div>\n      <div class="sidebar-sub">Admin Dashboard</div>\n    </div>\n  </div>\n  <ul class="nav-list">\n    <li class="nav-item active" onclick="goto(\'overview\')">&#x1F4CA; &Uuml;bersicht</li>\n    <li class="nav-item" onclick="goto(\'economy\')">&#x1F4B0; Kontost&auml;nde</li>\n    <li class="nav-item" onclick="goto(\'warns\')">&#x26A0;&#xFE0F; Verwarnungen</li>\n    <li class="nav-item" onclick="goto(\'inventories\')">&#x1F392; Inventare</li>\n    <li class="nav-item" onclick="goto(\'shops\')">&#x1F3EA; Shop-Verwaltung</li>\n    <li class="nav-item" onclick="goto(\'bans\')">&#x1F528; Gebannte Spieler</li>\n    <li class="nav-item" onclick="goto(\'blacklist\')">&#x1F6AB; Blacklist</li>\n    <li class="nav-item" onclick="goto(\'logs\')">&#x1F4CB; Echtzeit-Logs</li>\n    <li class="nav-item" onclick="goto(\'warnings\')">&#x1F6A8; Aktivit&auml;tswarnungen</li>\n    <li class="nav-item" onclick="goto(\'invites\')">&#x1F4E8; Einladungen</li>\n    <li class="nav-item" onclick="goto(\'players\')">&#x1F465; Spielerliste</li>\n    <li class="nav-item" onclick="goto(\'notes\')">&#x1F4DD; Notizen</li>\n    <li class="nav-item" onclick="goto(\'status\')">&#x2699;&#xFE0F; Bot-Status</li>\n  </ul>\n  <div class="sidebar-footer">\n    <a href="/logout" class="btn-logout">&#x1F6AA; Ausloggen</a>\n  </div>\n</nav>\n\n<!-- MAIN CONTENT -->\n<main class="main-content">\n\n  <!-- UEBERSICHT -->\n  <section id="sec-overview" class="section active">\n    <h2 class="section-title">&#x1F4CA; &Uuml;bersicht</h2>\n    <div class="stats-grid">\n      <div class="stat-card"><div class="stat-val" id="stat-members">&ndash;</div><div class="stat-label">Mitglieder</div></div>\n      <div class="stat-card"><div class="stat-val" id="stat-players">&ndash;</div><div class="stat-label">Spieler (B&uuml;rger)</div></div>\n      <div class="stat-card"><div class="stat-val" id="stat-bans">&ndash;</div><div class="stat-label">Gebannte</div></div>\n      <div class="stat-card"><div class="stat-val" id="stat-warns">&ndash;</div><div class="stat-label">Offene Warns</div></div>\n      <div class="stat-card"><div class="stat-val" id="stat-latency">&ndash;</div><div class="stat-label">Latenz</div></div>\n      <div class="stat-card"><div class="stat-val" id="stat-ram">&ndash;</div><div class="stat-label">RAM (MB)</div></div>\n    </div>\n    <div class="card mt-20">\n      <div class="card-title">&#x1F6A8; Letzte Aktivit&auml;tswarnungen</div>\n      <div id="overview-warnings" class="log-list">Lade&hellip;</div>\n    </div>\n    <div class="card mt-20">\n      <div class="card-title">&#x1F4CB; Letzte Logs</div>\n      <div id="overview-logs" class="log-list">Lade&hellip;</div>\n    </div>\n  </section>\n\n  <!-- KONTOSTAENDE -->\n  <section id="sec-economy" class="section">\n    <h2 class="section-title">&#x1F4B0; Kontost&auml;nde</h2>\n    <div class="toolbar">\n      <input class="search-input" id="eco-search" placeholder="Suche nach Name / ID&hellip;" oninput="filterTable(\'eco-tbody\',\'eco-search\')">\n    </div>\n    <div class="table-wrap">\n      <table class="data-table">\n        <thead><tr><th>Name</th><th>ID</th><th>Kasse</th><th>Bank</th><th>Gesamt</th><th>Dispo</th><th>Schulden</th></tr></thead>\n        <tbody id="eco-tbody"><tr><td colspan="7" class="loading">Lade&hellip;</td></tr></tbody>\n      </table>\n    </div>\n  </section>\n\n  <!-- VERWARNUNGEN -->\n  <section id="sec-warns" class="section">\n    <h2 class="section-title">&#x26A0;&#xFE0F; Verwarnungen</h2>\n    <div class="tabs">\n      <button class="tab-btn active" onclick="switchTab(this,\'warn-panel\',\'team-panel\')">Spieler-Warns</button>\n      <button class="tab-btn" onclick="switchTab(this,\'team-panel\',\'warn-panel\')">Team-Warns</button>\n    </div>\n    <div id="warn-panel">\n      <div class="toolbar"><input class="search-input" id="warn-search" placeholder="Suche&hellip;" oninput="filterTable(\'warn-tbody\',\'warn-search\')"></div>\n      <div class="table-wrap">\n        <table class="data-table">\n          <thead><tr><th>Name</th><th>ID</th><th>Anzahl</th><th>Verwarnungen</th></tr></thead>\n          <tbody id="warn-tbody"><tr><td colspan="4" class="loading">Lade&hellip;</td></tr></tbody>\n        </table>\n      </div>\n    </div>\n    <div id="team-panel" style="display:none">\n      <div class="toolbar"><input class="search-input" id="teamwarn-search" placeholder="Suche&hellip;" oninput="filterTable(\'teamwarn-tbody\',\'teamwarn-search\')"></div>\n      <div class="table-wrap">\n        <table class="data-table">\n          <thead><tr><th>Name</th><th>ID</th><th>Anzahl</th><th>Verwarnungen</th></tr></thead>\n          <tbody id="teamwarn-tbody"><tr><td colspan="4" class="loading">Lade&hellip;</td></tr></tbody>\n        </table>\n      </div>\n    </div>\n  </section>\n\n  <!-- INVENTARE -->\n  <section id="sec-inventories" class="section">\n    <h2 class="section-title">&#x1F392; Inventare</h2>\n    <div class="toolbar"><input class="search-input" id="inv-search" placeholder="Suche nach Name&hellip;" oninput="filterTable(\'inv-tbody\',\'inv-search\')"></div>\n    <div class="table-wrap">\n      <table class="data-table">\n        <thead><tr><th>Name</th><th>ID</th><th>Inventar</th><th>Lager</th></tr></thead>\n        <tbody id="inv-tbody"><tr><td colspan="4" class="loading">Lade&hellip;</td></tr></tbody>\n      </table>\n    </div>\n  </section>\n\n  <!-- SHOP -->\n  <section id="sec-shops" class="section">\n    <h2 class="section-title">&#x1F3EA; Shop-Verwaltung</h2>\n    <div class="card">\n      <div class="card-title">&#x2795; Item hinzuf&uuml;gen</div>\n      <div class="form-row">\n        <select id="shop-sel" class="form-select"><option value="">Shop w&auml;hlen&hellip;</option></select>\n        <input id="shop-emoji" class="form-input" placeholder="Emoji (z.B. &#x1F52B;)">\n        <input id="shop-name" class="form-input" placeholder="Itemname">\n        <input id="shop-preis" class="form-input" type="number" placeholder="Preis ($)">\n        <button class="btn-primary" onclick="addShopItem()">Hinzuf&uuml;gen</button>\n      </div>\n      <div id="shop-msg" class="form-msg"></div>\n    </div>\n    <div id="shop-panels"></div>\n  </section>\n\n  <!-- BANS -->\n  <section id="sec-bans" class="section">\n    <h2 class="section-title">&#x1F528; Gebannte Spieler</h2>\n    <div class="toolbar">\n      <input class="search-input" id="ban-search" placeholder="Suche nach Name / ID&hellip;" oninput="filterTable(\'ban-tbody\',\'ban-search\')">\n      <button class="btn-secondary" onclick="refreshBans()">&#x1F504; Aktualisieren</button>\n    </div>\n    <div class="table-wrap">\n      <table class="data-table">\n        <thead><tr><th>Name</th><th>ID</th><th>Grund</th><th>Aktion</th></tr></thead>\n        <tbody id="ban-tbody"><tr><td colspan="4" class="loading">Lade&hellip;</td></tr></tbody>\n      </table>\n    </div>\n  </section>\n\n  <!-- BLACKLIST -->\n  <section id="sec-blacklist" class="section">\n    <h2 class="section-title">&#x1F6AB; Blacklist</h2>\n    <div class="card">\n      <div class="card-title">&#x2795; Eintrag hinzuf&uuml;gen</div>\n      <div class="form-row">\n        <input id="bl-name" class="form-input" placeholder="Name">\n        <input id="bl-id" class="form-input" placeholder="Discord ID">\n        <input id="bl-reason" class="form-input" placeholder="Grund">\n        <button class="btn-primary" onclick="addBlacklist()">Hinzuf&uuml;gen</button>\n      </div>\n    </div>\n    <div class="toolbar mt-10"><input class="search-input" id="bl-search" placeholder="Suche&hellip;" oninput="filterTable(\'bl-tbody\',\'bl-search\')"></div>\n    <div class="table-wrap">\n      <table class="data-table">\n        <thead><tr><th>Name</th><th>Discord ID</th><th>Grund</th><th>Hinzugef&uuml;gt</th><th>Aktion</th></tr></thead>\n        <tbody id="bl-tbody"><tr><td colspan="5" class="loading">Lade&hellip;</td></tr></tbody>\n      </table>\n    </div>\n  </section>\n\n  <!-- LOGS -->\n  <section id="sec-logs" class="section">\n    <h2 class="section-title">&#x1F4CB; Echtzeit-Logs</h2>\n    <div class="toolbar">\n      <input class="search-input" id="log-search" placeholder="Filtern&hellip;" oninput="filterLogs()">\n      <select class="form-select" id="log-type-filter" onchange="filterLogs()" style="width:160px">\n        <option value="">Alle Typen</option>\n        <option>GELD</option><option>ITEM</option><option>ROLLE</option>\n        <option>BAN</option><option>SHOP</option><option>BLACKLIST</option>\n        <option>MITGLIED</option><option>AUSWEIS</option><option>WARN</option>\n        <option>SERVER</option>\n      </select>\n      <span class="live-badge">&#x1F7E2; Live</span>\n    </div>\n    <div id="log-list" class="log-list" style="max-height:600px;overflow-y:auto">Lade&hellip;</div>\n  </section>\n\n  <!-- WARNUNGEN -->\n  <section id="sec-warnings" class="section">\n    <h2 class="section-title">&#x1F6A8; Aktivit&auml;tswarnungen</h2>\n    <div class="toolbar">\n      <input class="search-input" id="aw-search" placeholder="Suche&hellip;" oninput="filterWarnings()">\n      <span class="live-badge">&#x1F7E2; Live</span>\n    </div>\n    <div id="aw-list" class="log-list" style="max-height:600px;overflow-y:auto">Lade&hellip;</div>\n  </section>\n\n  <!-- EINLADUNGEN -->\n  <section id="sec-invites" class="section">\n    <h2 class="section-title">&#x1F4E8; Einladungen</h2>\n    <div class="toolbar"><input class="search-input" id="inv2-search" placeholder="Suche&hellip;" oninput="filterTable(\'inv2-tbody\',\'inv2-search\')"></div>\n    <div class="table-wrap">\n      <table class="data-table">\n        <thead><tr><th>Einladender</th><th>ID</th><th>Code</th><th>Nutzungen</th></tr></thead>\n        <tbody id="inv2-tbody"><tr><td colspan="4" class="loading">Lade&hellip;</td></tr></tbody>\n      </table>\n    </div>\n  </section>\n\n  <!-- SPIELERLISTE -->\n  <section id="sec-players" class="section">\n    <h2 class="section-title">&#x1F465; Spielerliste &mdash; B&uuml;rger</h2>\n    <div class="stat-card" style="margin-bottom:16px;display:inline-block;min-width:160px">\n      <div class="stat-val" id="player-count">&ndash;</div>\n      <div class="stat-label">Spieler gesamt</div>\n    </div>\n    <div class="toolbar"><input class="search-input" id="pl-search" placeholder="Suche&hellip;" oninput="filterTable(\'pl-tbody\',\'pl-search\')"></div>\n    <div class="table-wrap">\n      <table class="data-table">\n        <thead><tr><th>Name</th><th>Discord ID</th></tr></thead>\n        <tbody id="pl-tbody"><tr><td colspan="2" class="loading">Lade&hellip;</td></tr></tbody>\n      </table>\n    </div>\n  </section>\n\n  <!-- NOTIZEN -->\n  <section id="sec-notes" class="section">\n    <h2 class="section-title">&#x1F4DD; Notizen &uuml;ber Spieler</h2>\n    <div class="card">\n      <div class="card-title">&#x2795; Notiz hinzuf&uuml;gen</div>\n      <div class="form-row">\n        <input id="note-uid" class="form-input" placeholder="Discord ID">\n        <input id="note-text" class="form-input" placeholder="Notiz / Verhaltensauff&auml;lligkeit">\n        <button class="btn-primary" onclick="addNote()">Hinzuf&uuml;gen</button>\n      </div>\n    </div>\n    <div class="toolbar mt-10"><input class="search-input" id="note-search" placeholder="Suche&hellip;" oninput="filterNotes()"></div>\n    <div id="notes-list" class="notes-grid">Lade&hellip;</div>\n  </section>\n\n  <!-- STATUS -->\n  <section id="sec-status" class="section">\n    <h2 class="section-title">&#x2699;&#xFE0F; Bot-Status &amp; Services</h2>\n    <div class="stats-grid">\n      <div class="stat-card"><div class="stat-val" id="ss-ram">&ndash;</div><div class="stat-label">RAM (MB)</div></div>\n      <div class="stat-card"><div class="stat-val" id="ss-cpu">&ndash;</div><div class="stat-label">CPU %</div></div>\n      <div class="stat-card"><div class="stat-val" id="ss-disk">&ndash;</div><div class="stat-label">Disk %</div></div>\n      <div class="stat-card"><div class="stat-val" id="ss-lat">&ndash;</div><div class="stat-label">Latenz (ms)</div></div>\n      <div class="stat-card"><div class="stat-val" id="ss-uptime">&ndash;</div><div class="stat-label">Uptime</div></div>\n      <div class="stat-card"><div class="stat-val" id="ss-members">&ndash;</div><div class="stat-label">Mitglieder</div></div>\n    </div>\n    <div class="card mt-20">\n      <div class="card-title">&#x1F50C; Aktive Features</div>\n      <div id="features-list" class="features-grid">Lade&hellip;</div>\n    </div>\n  </section>\n\n</main>\n\n<script>\n/* Paradise City Admin Dashboard - Frontend JS */\n\nconst $ = id => document.getElementById(id);\nconst fmt = n => typeof n === \'number\' ? n.toLocaleString(\'de-DE\') : (n ?? \'\\u2013\');\nconst fmtMoney = n => (typeof n === \'number\'\n  ? (n < 0\n    ? `<span class="money-neg">-$${Math.abs(n).toLocaleString(\'de-DE\')}</span>`\n    : `<span class="money">$${n.toLocaleString(\'de-DE\')}</span>`)\n  : \'\\u2013\');\n\nfunction goto(id) {\n  document.querySelectorAll(\'.section\').forEach(s => s.classList.remove(\'active\'));\n  document.querySelectorAll(\'.nav-item\').forEach(n => n.classList.remove(\'active\'));\n  const sec = document.getElementById(\'sec-\' + id);\n  if (sec) sec.classList.add(\'active\');\n  const nav = [...document.querySelectorAll(\'.nav-item\')].find(n => n.getAttribute(\'onclick\')?.includes("\'" + id + "\'"));\n  if (nav) nav.classList.add(\'active\');\n  loadSection(id);\n}\n\nfunction switchTab(btn, show, hide) {\n  document.querySelectorAll(\'.tab-btn\').forEach(b => b.classList.remove(\'active\'));\n  btn.classList.add(\'active\');\n  $(show).style.display = \'\';\n  $(hide).style.display = \'none\';\n}\n\nasync function api(path, opts = {}) {\n  try {\n    const r = await fetch(path, { headers: {\'Content-Type\':\'application/json\'}, ...opts });\n    if (!r.ok) return null;\n    return await r.json();\n  } catch { return null; }\n}\n\nfunction loadSection(id) {\n  ({\n    overview:    loadOverview,\n    economy:     loadEconomy,\n    warns:       loadWarns,\n    inventories: loadInventories,\n    shops:       loadShops,\n    bans:        loadBans,\n    blacklist:   loadBlacklist,\n    logs:        loadLogs,\n    warnings:    loadWarnings,\n    invites:     loadInvites,\n    players:     loadPlayers,\n    notes:       loadNotes,\n    status:      loadStatus,\n  }[id] || (() => {}))();\n}\n\nasync function loadOverview() {\n  const [status, players, bans, warns, warnlog, logs] = await Promise.all([\n    api(\'/api/status\'), api(\'/api/players\'), api(\'/api/bans\'),\n    api(\'/api/warns\'), api(\'/api/warnings-log?limit=5\'), api(\'/api/activity-log?limit=10\'),\n  ]);\n  if (status) {\n    $(\'stat-members\').textContent = fmt(status.members);\n    $(\'stat-latency\').textContent = status.latency_ms ? status.latency_ms + \' ms\' : \'\\u2013\';\n    $(\'stat-ram\').textContent = status.ram_mb ? status.ram_mb + \' MB\' : \'\\u2013\';\n  }\n  if (players) $(\'stat-players\').textContent = fmt(players.count);\n  if (bans)    $(\'stat-bans\').textContent    = fmt(bans.length);\n  if (warns)   $(\'stat-warns\').textContent   = fmt(warns.reduce((s,w) => s + w.count, 0));\n  if (warnlog) renderWarningEntries(warnlog, \'overview-warnings\');\n  if (logs)    renderLogEntries(logs, \'overview-logs\');\n}\n\nasync function loadEconomy() {\n  const rows = await api(\'/api/economy\');\n  if (!rows) return;\n  $(\'eco-tbody\').innerHTML = rows.length ? rows.map(r => `\n    <tr data-search="${(r.name+\' \'+r.id).toLowerCase()}">\n      <td><b>${esc(r.name)}</b></td>\n      <td><span class="uid-small">${r.id}</span></td>\n      <td>${fmtMoney(r.kasse)}</td>\n      <td>${fmtMoney(r.bank)}</td>\n      <td>${fmtMoney(r.gesamt)}</td>\n      <td>${fmtMoney(r.dispo)}</td>\n      <td>${r.schulden ? fmtMoney(-r.schulden) : \'\\u2013\'}</td>\n    </tr>`).join(\'\') : \'<tr><td colspan="7" class="loading">Keine Daten</td></tr>\';\n}\n\nasync function loadWarns() {\n  const [w, tw] = await Promise.all([api(\'/api/warns\'), api(\'/api/team-warns\')]);\n  renderWarnTable(w, \'warn-tbody\', 4);\n  renderWarnTable(tw, \'teamwarn-tbody\', 4);\n}\n\nfunction renderWarnTable(rows, tbodyId, cols) {\n  if (!rows) return;\n  $(tbodyId).innerHTML = rows.length ? rows.map(r => `\n    <tr data-search="${(r.name+\' \'+r.id).toLowerCase()}">\n      <td><b>${esc(r.name)}</b></td>\n      <td><span class="uid-small">${r.id}</span></td>\n      <td><span class="badge badge-red">${r.count}</span></td>\n      <td style="font-size:12px;color:var(--text-dim)">${r.warns.map(w=>esc(w.grund||w.reason||JSON.stringify(w))).join(\' | \')}</td>\n    </tr>`).join(\'\') : `<tr><td colspan="${cols}" class="loading">Keine Verwarnungen</td></tr>`;\n}\n\nasync function loadInventories() {\n  const rows = await api(\'/api/inventories\');\n  if (!rows) return;\n  $(\'inv-tbody\').innerHTML = rows.length ? rows.map(r => `\n    <tr data-search="${(r.name+\' \'+r.id).toLowerCase()}">\n      <td><b>${esc(r.name)}</b></td>\n      <td><span class="uid-small">${r.id}</span></td>\n      <td style="font-size:12px">${(r.inv||[]).join(\', \') || \'\\u2013\'}</td>\n      <td style="font-size:12px">${(r.lager||[]).join(\', \') || \'\\u2013\'}</td>\n    </tr>`).join(\'\') : \'<tr><td colspan="4" class="loading">Keine Inventare</td></tr>\';\n}\n\nlet _shopData = {};\n\nasync function loadShops() {\n  const data = await api(\'/api/shops\');\n  if (!data) return;\n  _shopData = data;\n  const sel = $(\'shop-sel\');\n  sel.innerHTML = \'<option value="">Shop w\\u00E4hlen\\u2026</option>\' +\n    Object.keys(data).map(k => `<option value="${esc(k)}">${esc(k)}</option>`).join(\'\');\n  $(\'shop-panels\').innerHTML = Object.entries(data).map(([shop, info]) => `\n    <div class="shop-section">\n      <div class="shop-header">\\u{1F3EA} ${esc(shop)}</div>\n      <div class="shop-items">\n        ${(info.items||[]).length ? (info.items||[]).map((item,i) => `\n          <div class="shop-item-row">\n            <span>${esc(item.name || (item.emoji||\'\') + \' \' + (item.itemname||\'\') || JSON.stringify(item))}</span>\n            <div style="display:flex;gap:12px;align-items:center">\n              <span class="item-price">$${fmt(item.preis||item.price||0)}</span>\n              <button class="btn-danger" onclick="deleteShopItem(\'${esc(shop)}\',${i})">\\u{1F5D1}\\uFE0F</button>\n            </div>\n          </div>`).join(\'\') : \'<div style="padding:12px 18px;color:var(--text-dim);font-size:13px">Keine Items</div>\'}\n      </div>\n    </div>`).join(\'\');\n}\n\nasync function addShopItem() {\n  const shop  = $(\'shop-sel\').value;\n  const emoji = $(\'shop-emoji\').value.trim();\n  const name  = $(\'shop-name\').value.trim();\n  const preis = $(\'shop-preis\').value;\n  const msg   = $(\'shop-msg\');\n  if (!shop || !name || !preis) { msg.className=\'form-msg err\'; msg.textContent=\'\\u274C Bitte alle Felder ausf\\u00FCllen.\'; return; }\n  const r = await api(\'/api/shop-item\', { method:\'POST\', body: JSON.stringify({shop,emoji,name,preis:parseInt(preis)}) });\n  if (r?.ok) {\n    msg.className=\'form-msg ok\'; msg.textContent=\'\\u2705 Item hinzugef\\u00FCgt!\';\n    $(\'shop-emoji\').value=\'\'; $(\'shop-name\').value=\'\'; $(\'shop-preis\').value=\'\';\n    loadShops();\n  } else { msg.className=\'form-msg err\'; msg.textContent=\'\\u274C \' + (r?.error || \'Fehler\'); }\n}\n\nasync function deleteShopItem(shop, idx) {\n  if (!confirm(\'Item wirklich l\\u00F6schen?\')) return;\n  const r = await api(\'/api/shop-item\', { method:\'DELETE\', body: JSON.stringify({shop, index:idx}) });\n  if (r?.ok) loadShops();\n  else alert(\'Fehler beim L\\u00F6schen\');\n}\n\nasync function loadBans() {\n  const bans = await api(\'/api/bans\');\n  renderBans(bans || []);\n}\n\nfunction renderBans(bans) {\n  $(\'ban-tbody\').innerHTML = bans.length ? bans.map(b => `\n    <tr data-search="${(b.name+\' \'+b.id).toLowerCase()}">\n      <td><b>${esc(b.name)}</b></td>\n      <td><span class="uid-small">${b.id}</span></td>\n      <td style="font-size:12px">${esc(b.reason||\'\\u2013\')}</td>\n      <td><button class="btn-success" onclick="unbanUser(\'${b.id}\',\'${esc(b.name)}\')">\\u2705 Entbannen</button></td>\n    </tr>`).join(\'\') : \'<tr><td colspan="4" class="loading">Keine gebannten Spieler</td></tr>\';\n}\n\nasync function refreshBans() {\n  $(\'ban-tbody\').innerHTML = \'<tr><td colspan="4" class="loading">Aktualisiere\\u2026</td></tr>\';\n  const bans = await api(\'/api/bans/refresh\', { method:\'POST\' });\n  renderBans(bans || []);\n}\n\nasync function unbanUser(id, name) {\n  if (!confirm(`${name} (${id}) wirklich entbannen?`)) return;\n  const r = await api(\'/api/unban\', { method:\'POST\', body: JSON.stringify({user_id:id}) });\n  if (r?.ok) { alert(\'\\u2705 Entbannt!\'); loadBans(); }\n  else alert(\'\\u274C Fehler beim Entbannen\');\n}\n\nasync function loadBlacklist() {\n  const bl = await api(\'/api/blacklist\');\n  if (!bl) return;\n  $(\'bl-tbody\').innerHTML = bl.length ? bl.map((e,i) => `\n    <tr data-search="${(e.name+\' \'+(e.id||\'\')).toLowerCase()}">\n      <td><b>${esc(e.name)}</b></td>\n      <td><span class="uid-small">${e.id||\'\\u2013\'}</span></td>\n      <td style="font-size:12px">${esc(e.reason||\'\\u2013\')}</td>\n      <td style="font-size:11px;color:var(--text-dim)">${esc(e.added_at||\'\\u2013\')}</td>\n      <td><button class="btn-danger" onclick="deleteBlacklist(${i})">\\u{1F5D1}\\uFE0F Entfernen</button></td>\n    </tr>`).join(\'\') : \'<tr><td colspan="5" class="loading">Keine Eintr\\u00E4ge</td></tr>\';\n}\n\nasync function addBlacklist() {\n  const name   = $(\'bl-name\').value.trim();\n  const discId = $(\'bl-id\').value.trim();\n  const reason = $(\'bl-reason\').value.trim();\n  if (!name && !discId) { alert(\'Name oder Discord-ID erforderlich\'); return; }\n  const r = await api(\'/api/blacklist\', { method:\'POST\', body: JSON.stringify({name, discord_id:discId, reason}) });\n  if (r?.ok) { $(\'bl-name\').value=\'\'; $(\'bl-id\').value=\'\'; $(\'bl-reason\').value=\'\'; loadBlacklist(); }\n  else alert(\'\\u274C Fehler\');\n}\n\nasync function deleteBlacklist(idx) {\n  if (!confirm(\'Eintrag wirklich entfernen?\')) return;\n  const r = await api(`/api/blacklist/${idx}`, { method:\'DELETE\' });\n  if (r?.ok) loadBlacklist();\n}\n\nlet _allLogs = [];\n\nasync function loadLogs() {\n  const logs = await api(\'/api/activity-log?limit=200\');\n  if (!logs) return;\n  _allLogs = logs;\n  filterLogs();\n}\n\nfunction filterLogs() {\n  const q    = ($(\'log-search\')?.value || \'\').toLowerCase();\n  const type = $(\'log-type-filter\')?.value || \'\';\n  const filtered = _allLogs.filter(e =>\n    (!type || e.type === type) &&\n    (!q || (e.desc||\'\').toLowerCase().includes(q) || (e.user||\'\').includes(q))\n  );\n  renderLogEntries(filtered, \'log-list\');\n}\n\nfunction renderLogEntries(entries, containerId) {\n  const el = $(containerId);\n  if (!el) return;\n  if (!entries || !entries.length) { el.innerHTML = \'<div style="color:var(--text-dim);font-size:13px">Keine Logs</div>\'; return; }\n  el.innerHTML = entries.map(e => `\n    <div class="log-entry type-${e.type||\'\'}">\n      <div><span class="badge badge-orange" style="margin-right:8px">${e.type||\'LOG\'}</span>${esc(e.desc||\'\')}</div>\n      ${e.user ? `<div class="uid-small">Nutzer: ${e.user}</div>` : \'\'}\n      <div class="log-time">\\u{1F550} ${e.time}</div>\n    </div>`).join(\'\');\n}\n\nlet _allWarnings = [];\n\nasync function loadWarnings() {\n  const w = await api(\'/api/warnings-log?limit=200\');\n  if (!w) return;\n  _allWarnings = w;\n  filterWarnings();\n}\n\nfunction filterWarnings() {\n  const q = ($(\'aw-search\')?.value || \'\').toLowerCase();\n  const filtered = _allWarnings.filter(e => !q || (e.title+e.desc).toLowerCase().includes(q));\n  renderWarningEntries(filtered, \'aw-list\');\n}\n\nfunction renderWarningEntries(entries, containerId) {\n  const el = $(containerId);\n  if (!el) return;\n  if (!entries || !entries.length) { el.innerHTML = \'<div style="color:var(--text-dim);font-size:13px">Keine Warnungen</div>\'; return; }\n  el.innerHTML = entries.map(e => `\n    <div class="warn-entry">\n      <div class="warn-entry-title">\\u{1F6A8} ${esc(e.title||\'Warnung\')}</div>\n      <div style="font-size:13px;margin-top:4px;white-space:pre-line">${esc(e.desc||\'\')}</div>\n      <div class="log-time">\\u{1F550} ${e.time}</div>\n    </div>`).join(\'\');\n}\n\nasync function loadInvites() {\n  const data = await api(\'/api/invites\');\n  if (!data) return;\n  const entries = Object.entries(data);\n  $(\'inv2-tbody\').innerHTML = entries.length ? entries.map(([code, inv]) => `\n    <tr data-search="${(inv.inviter_name||inv.inviter||code).toLowerCase()}">\n      <td><b>${esc(inv.inviter_name || inv.inviter || \'\\u2013\')}</b></td>\n      <td><span class="uid-small">${inv.inviter_id||\'\\u2013\'}</span></td>\n      <td><code style="font-size:12px">${esc(code)}</code></td>\n      <td><span class="badge badge-orange">${inv.uses||0}</span></td>\n    </tr>`).join(\'\') : \'<tr><td colspan="4" class="loading">Keine Einladungsdaten</td></tr>\';\n}\n\nasync function loadPlayers() {\n  const data = await api(\'/api/players\');\n  if (!data) return;\n  $(\'player-count\').textContent = fmt(data.count);\n  const players = Object.entries(data.players || {});\n  $(\'pl-tbody\').innerHTML = players.length ? players.map(([uid, m]) => `\n    <tr data-search="${(m.name||uid).toLowerCase()}">\n      <td><b>${esc(m.name||m.tag||uid)}</b></td>\n      <td><span class="uid-small">${uid}</span></td>\n    </tr>`).join(\'\') : \'<tr><td colspan="2" class="loading">Keine Spieler</td></tr>\';\n}\n\nlet _allNotes = {};\n\nasync function loadNotes() {\n  const data = await api(\'/api/notes\');\n  if (!data) return;\n  _allNotes = data;\n  filterNotes();\n}\n\nfunction filterNotes() {\n  const q = ($(\'note-search\')?.value || \'\').toLowerCase();\n  const $el = $(\'notes-list\');\n  const entries = Object.entries(_allNotes).filter(([uid, d]) =>\n    !q || (d.name||uid).toLowerCase().includes(q) ||\n    (d.notes||[]).some(n => (n.note||\'\').toLowerCase().includes(q))\n  );\n  if (!entries.length) { $el.innerHTML = \'<div style="color:var(--text-dim)">Keine Notizen</div>\'; return; }\n  $el.innerHTML = entries.map(([uid, d]) => `\n    <div class="note-card">\n      <div class="note-user">\\u{1F464} ${esc(d.name||uid)} <span class="uid-small">${uid}</span></div>\n      ${(d.notes||[]).map((n,i) => `\n        <div class="note-entry">\n          <div>\n            <div>${esc(n.note)}</div>\n            <div class="note-time">\\u{1F550} ${n.time||\'\\u2013\'}</div>\n          </div>\n          <button class="btn-danger" onclick="deleteNote(\'${uid}\',${i})">\\u{1F5D1}\\uFE0F</button>\n        </div>`).join(\'\')}\n    </div>`).join(\'\');\n}\n\nasync function addNote() {\n  const uid  = $(\'note-uid\').value.trim();\n  const note = $(\'note-text\').value.trim();\n  if (!uid || !note) { alert(\'ID und Notiz erforderlich\'); return; }\n  const r = await api(\'/api/notes\', { method:\'POST\', body: JSON.stringify({user_id:uid, note}) });\n  if (r?.ok) { $(\'note-uid\').value=\'\'; $(\'note-text\').value=\'\'; loadNotes(); }\n  else alert(\'\\u274C Fehler\');\n}\n\nasync function deleteNote(uid, idx) {\n  if (!confirm(\'Notiz l\\u00F6schen?\')) return;\n  const r = await api(`/api/notes/${uid}/${idx}`, { method:\'DELETE\' });\n  if (r?.ok) loadNotes();\n}\n\nasync function loadStatus() {\n  const s = await api(\'/api/status\');\n  if (!s) return;\n  $(\'ss-ram\').textContent     = s.ram_mb + \' MB\';\n  $(\'ss-cpu\').textContent     = s.cpu_pct + \'%\';\n  $(\'ss-disk\').textContent    = s.disk_pct + \'%\';\n  $(\'ss-lat\').textContent     = s.latency_ms ? s.latency_ms + \' ms\' : \'\\u2013\';\n  $(\'ss-uptime\').textContent  = s.uptime || \'\\u2013\';\n  $(\'ss-members\').textContent = fmt(s.members);\n  const fl = $(\'features-list\');\n  if (s.features && Object.keys(s.features).length) {\n    fl.innerHTML = Object.entries(s.features).map(([name, f]) =>\n      `<div class="feature-item ${f.ok?\'feature-ok\':\'feature-err\'}">\n        ${f.ok ? \'\\u{1F7E2}\' : \'\\u{1F534}\'} ${esc(name)}\n        ${!f.ok && f.err ? `<span style="font-size:11px;color:var(--text-dim)"> \\u2014 ${esc(f.err)}</span>` : \'\'}\n      </div>`).join(\'\');\n  } else {\n    fl.innerHTML = \'<div style="color:var(--text-dim)">Keine Feature-Daten</div>\';\n  }\n}\n\nfunction filterTable(tbodyId, searchId) {\n  const q = ($(searchId)?.value || \'\').toLowerCase();\n  document.querySelectorAll(`#${tbodyId} tr[data-search]`).forEach(row => {\n    row.style.display = row.getAttribute(\'data-search\').includes(q) ? \'\' : \'none\';\n  });\n}\n\nfunction esc(str) {\n  if (str === null || str === undefined) return \'\';\n  return String(str).replace(/&/g,\'&amp;\').replace(/</g,\'&lt;\').replace(/>/g,\'&gt;\').replace(/"/g,\'&quot;\');\n}\n\nfunction autoRefresh() {\n  const active = document.querySelector(\'.section.active\')?.id?.replace(\'sec-\',\'\');\n  if (active === \'logs\')     loadLogs();\n  if (active === \'warnings\') loadWarnings();\n  if (active === \'overview\') loadOverview();\n  if (active === \'status\')   loadStatus();\n  if (active === \'players\')  loadPlayers();\n}\n\nsetInterval(autoRefresh, 8000);\nloadSection(\'overview\');\n</script>\n</body>\n</html>\n'

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

    return render_template_string(_LOGIN_HTML, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# \u2500\u2500 Main UI \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template_string(_DASH_HTML)


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
