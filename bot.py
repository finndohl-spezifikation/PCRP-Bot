# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# main.py \u2014 Bot-Einstiegspunkt
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#
# Importiert alle Module, startet den Bot mit dem TOKEN.
# Alle DISCORD_TOKEN m\xfcssen als Umgebungsvariable gesetzt sein.
#
# Startreihenfolge:
#   python main.py
#
# Deployment: Railway (RAILWAY_ENVIRONMENT muss gesetzt sein)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

import os
import sys

# UTF-8 Encoding erzwingen (wichtig f\xfcr Railway/Linux-Deployments)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')
os.environ.setdefault("PYTHONUTF8", "1")

# Bot-Instanz laden
from config import bot

# Doppelte Command-Registrierung erlauben (Railway hat alte Ordnerstruktur)
# Falls ein Command bereits registriert ist, wird er einfach \xfcberschrieben statt zu crashen.
_orig_add_command = bot.tree.add_command
def _safe_add_command(command, /, **kwargs):
    kwargs["override"] = True
    return _orig_add_command(command, **kwargs)
bot.tree.add_command = _safe_add_command

# Alle Module importieren \u2014 Reihenfolge ist wichtig!
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
import fuehrerschein            # F\xfchrerschein-System
import support_voice          # Automatischer Voice-Support mit TTS  \u2190 muss vor lobby stehen
import casino                   # Casino Gl\xfccksrad
import lobby                    # /lobby-abstimmung, /lobby-open, /lobby-close
import giveaway                 # /create-giveaway
import event_system             # /create-event
import abstimmung               # /abstimmung, reaction polls
import misc_commands            # /kartenkontrolle, /delete, /commands, /kategorien-setup
import rechnungen               # /rechnung-schreiben, /rechnungen, /mahnung
import beschlagnahmung          # /beschlagnahmen, /remove-beschlagnahmung, /konfiszieren
import dienst                   # Dienst-System (Anmelden/Abmelden, Embed-Boards)
import help_embed               # Automatisches Command-\xdcbersicht Embed
import ic_actions               # /erste-hilfe, /ortung, /fesseln
import ping_roles               # Ping-Rollen Auswahl-Embed
import team_overview           # Team \xdcbersicht mit On/Off Duty
import boost                   # Boost Belohnungen Embed
import lotto                   # Lotto-System
import bingo                   # W\xf6chentliches Bingo-System
import startinfo               # "Wo starte ich?" Embed
import starterpaket            # Starter Paket Embed
import vorschlag               # Vorschlag-System
import auto_geben              # Fahrzeug-Vergabe-System
import atm_raub               # ATM-Raub System
import shop_raub              # Shop-Raub System
import raubueberfall          # Raub\xfcberfall System
import human_labs_raub        # Humane Labs Raub\xfcberfall System
import staatsbank_raub        # Staatsbank Raub\xfcberfall System
import aktien                 # Aktienmarkt-System
import kanal_sperre           # /kanal-sperre, /kanal-entsperren

try:
    import server_schutz      # Schutz vor unbefugten Kanal/Rollen-\xc4nderungen
except Exception as _import_err:
    print(f"[WARNING] server_schutz konnte nicht geladen werden: {_import_err}")

try:
    import logs                 # Erweiterte Server-Logs (Voice, Name, Timeout, Rollen)
    import bot_status           # Auto-aktualisierendes Status-Dashboard
except Exception as _import_err:
    print(f"[WARNING] logs/bot_status konnten nicht geladen werden: {_import_err}")

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    print("\u274c DISCORD_TOKEN ist nicht gesetzt!")
    exit(1)

bot.run(TOKEN)
