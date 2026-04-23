# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# main.py \u2014 Bot-Einstiegspunkt
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#
# Importiert alle Module, startet den Bot mit dem TOKEN.
# Alle DISCORD_TOKEN m\u00FCssen als Umgebungsvariable gesetzt sein.
#
# Startreihenfolge:
#   python main.py
#
# Deployment: Railway (RAILWAY_ENVIRONMENT muss gesetzt sein)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

import os
import sys

# UTF-8 Encoding erzwingen (wichtig f\u00FCr Railway/Linux-Deployments)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')
os.environ.setdefault("PYTHONUTF8", "1")

# Bot-Instanz laden
from config import bot

# Dashboard sofort starten (vor allen anderen Imports) damit Railway-Healthcheck antwortet
try:
    from dashboard import start_dashboard
    _dash_port = int(os.environ.get("PORT") or os.environ.get("DASHBOARD_PORT") or "8080")
    print(f"[Dashboard] Starte auf Port {_dash_port} (PORT={os.environ.get('PORT')})")
    start_dashboard(None, port=_dash_port)
except Exception as _de:
    import traceback; traceback.print_exc()
    print(f"[Dashboard] Konnte nicht gestartet werden: {_de}")


# Doppelte Command-Registrierung erlauben (Railway hat alte Ordnerstruktur)
# Falls ein Command bereits registriert ist, wird er einfach \u00FCberschrieben statt zu crashen.
_orig_add_command = bot.tree.add_command
def _safe_add_command(command, /, **kwargs):
    kwargs["override"] = True
    return _orig_add_command(command, **kwargs)
bot.tree.add_command = _safe_add_command

# Alle Module importieren \u2014 Reihenfolge ist wichtig!
import helpers                  # Hilfsfunktionen

try:
    import economy_helpers      # Economy-Datenschicht
except Exception as _e:
    import traceback; traceback.print_exc()
    print(f"[FEHLER] economy_helpers konnte nicht geladen werden: {_e}")
    raise

import handy                    # Handy-System
import ticket                   # Ticket-System
import moderation               # Auto-Mod
import events                   # on_ready, on_message, Logs
import commands                 # Prefix Commands (!hallo etc.)

try:
    import economy_commands     # /lohn-abholen, /kontostand, etc.
except Exception as _e:
    import traceback; traceback.print_exc()
    print(f"[FEHLER] economy_commands konnte nicht geladen werden: {_e}")
    raise

try:
    import shop                 # /shop, /buy, /shop-add, /delete-item
except Exception as _e:
    import traceback; traceback.print_exc()
    print(f"[FEHLER] shop konnte nicht geladen werden: {_e}")
    raise

try:
    import team_shop            # /items, /items-add, /items-delete (Team-Shop)
except Exception as _e:
    import traceback; traceback.print_exc()
    print(f"[FEHLER] team_shop konnte nicht geladen werden: {_e}")
    raise

try:
    import inventory            # /rucksack, /uebergeben, /verstecken, /use-item
except Exception as _e:
    import traceback; traceback.print_exc()
    print(f"[FEHLER] inventory konnte nicht geladen werden: {_e}")
    raise
import warns                    # /warn, /warn-list, /remove-warn, etc.
import einreise                 # Einreise-System, /ausweisen, /ausweis-*
import fuehrerschein            # F\u00FChrerschein-System
import support_voice          # Automatischer Voice-Support mit TTS  \u2190 muss vor lobby stehen
import casino                   # Casino Gl\u00FCcksrad
import lobby                    # /lobby-abstimmung, /lobby-open, /lobby-close
import giveaway                 # /create-giveaway
import event_system             # /create-event
import abstimmung               # /abstimmung, reaction polls
import misc_commands            # /kartenkontrolle, /delete, /commands, /kategorien-setup
import rechnungen               # /rechnung-schreiben, /rechnungen, /mahnung
import beschlagnahmung          # /beschlagnahmen, /remove-beschlagnahmung, /konfiszieren
import dienst                   # Dienst-System (Anmelden/Abmelden, Embed-Boards)
import help_embed               # Automatisches Command-\u00DCbersicht Embed
import ic_actions               # /erste-hilfe, /ortung, /fesseln
import ping_roles               # Ping-Rollen Auswahl-Embed
import team_overview           # Team \u00DCbersicht mit On/Off Duty
import boost                   # Boost Belohnungen Embed
import lotto                   # Lotto-System
import bingo                   # W\u00F6chentliches Bingo-System
import startinfo               # "Wo starte ich?" Embed
import starterpaket            # Starter Paket Embed
import vorschlag               # Vorschlag-System
import auto_geben              # Fahrzeug-Vergabe-System
import atm_raub               # ATM-Raub System
import shop_raub              # Shop-Raub System
import raubueberfall          # Raub\u00FCberfall System
import human_labs_raub        # Humane Labs Raub\u00FCberfall System
import staatsbank_raub        # Staatsbank Raub\u00FCberfall System
import kokain                # Kokain-Herstellungs-System
import aktien                 # Aktienmarkt-System
import kanal_sperre           # /kanal-sperre, /kanal-entsperren
import nebenserver            # Nebenserver Import/Export Embed

try:
    import server_schutz      # Schutz vor unbefugten Kanal/Rollen-\u00C4nderungen
except Exception as _import_err:
    print(f"[WARNING] server_schutz konnte nicht geladen werden: {_import_err}")

try:
    import logs                 # Erweiterte Server-Logs (Voice, Name, Timeout, Rollen)
    import bot_status           # Auto-aktualisierendes Status-Dashboard
except Exception as _import_err:
    print(f"[WARNING] logs/bot_status konnten nicht geladen werden: {_import_err}")

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    print("\u274C DISCORD_TOKEN ist nicht gesetzt!")
    exit(1)


# Bot-Referenz im Dashboard aktualisieren
try:
    from dashboard import set_bot
    set_bot(bot)
except Exception:
    pass

bot.run(TOKEN)
