# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# main.py — Bot-Einstiegspunkt
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════
#
# Importiert alle Module, startet den Bot mit dem TOKEN.
# Alle DISCORD_TOKEN müssen als Umgebungsvariable gesetzt sein.
#
# Startreihenfolge:
#   python main.py
#
# Deployment: Railway (RAILWAY_ENVIRONMENT muss gesetzt sein)
# ══════════════════════════════════════════════════════════════

import os
import sys

# Unterordner zum Python-Pfad hinzufügen — sucht in allen möglichen Positionen
_BASE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_BASE)
for _candidate in [
    os.path.join(_BASE, "beschlagnahmung"),        # bot_split/beschlagnahmung/
    os.path.join(_REPO_ROOT, "beschlagnahmung"),   # repo_root/beschlagnahmung/
    _BASE,                                          # bot_split/ direkt
]:
    if os.path.isdir(_candidate) and _candidate not in sys.path:
        sys.path.insert(0, _candidate)

# Alle Module importieren — Reihenfolge ist wichtig!
from config import bot          # bot-Instanz, alle IDs
import helpers                  # Hilfsfunktionen
import economy_helpers          # Economy-Datenschicht
import handy                    # Handy-System
import ticket                   # Ticket-System
import moderation               # Auto-Mod
import events                   # on_ready, on_message, Logs
import commands                 # Prefix Commands (!hallo etc.)
import economy_commands         # /lohn-abholen, /kontostand, etc.
import shop                     # /shop, /buy, /shop-add, /delete-item
import inventory                # /rucksack, /uebergeben, /verstecken, /use-item
import warns                    # /warn, /warn-list, /remove-warn, etc.
import einreise                 # Einreise-System, /ausweisen, /ausweis-*
import fuehrerschein            # Führerschein-System
import casino                   # Casino Glücksrad
import lobby                    # /lobby-abstimmung, /lobby-open, /lobby-close
import giveaway                 # /create-giveaway
import event_system             # /create-event
import abstimmung               # /abstimmung, reaction polls
import misc_commands            # /kartenkontrolle, /delete, /commands, /kategorien-setup
import rechnungen               # /rechnung-schreiben, /rechnungen, /mahnung
import beschlagnahmung          # /beschlagnahmen, /remove-beschlagnahmung, /konfiszieren
import dienst                   # Dienst-System (Anmelden/Abmelden, Embed-Boards)
import help_embed               # Automatisches Command-Übersicht Embed
import ic_actions               # /erste-hilfe, /ortung, /fesseln
import ping_roles               # Ping-Rollen Auswahl-Embed

try:
    import logs                 # Erweiterte Server-Logs (Voice, Name, Timeout, Rollen)
    import bot_status           # Auto-aktualisierendes Status-Dashboard
except Exception as _import_err:
    print(f"[WARNING] logs/bot_status konnten nicht geladen werden: {_import_err}")

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    print("❌ DISCORD_TOKEN ist nicht gesetzt!")
    exit(1)

bot.run(TOKEN)
