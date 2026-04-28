# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# embed_manager.py \u2014 Zentraler Embed-Manager
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#
# Ruft beim Start alle Auto-Setup-Funktionen auf.
# Neue Embeds hier eintragen \u2014 events.py bleibt sauber.
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550


async def setup_all_embeds():
    """Richtet alle persistenten Channel-Embeds ein."""

    _setups = []

    def _try_import(name, module, func):
        try:
            mod = __import__(module)
            fn  = getattr(mod, func)
            _setups.append((name, fn))
        except Exception as e:
            print(f"[embed_manager] âš ï¸ Import Ã¼bersprungen [{name}]: {e}")

    _try_import("ticket",        "ticket",           "auto_ticket_setup")
    _try_import("lohnliste",     "ticket",           "auto_lohnliste_setup")
    _try_import("einreise",      "einreise",         "auto_einreise_setup")
    _try_import("handy",         "handy",            "auto_handy_setup")
    _try_import("casino",        "casino",           "auto_casino_setup")
    _try_import("dienst",        "dienst",           "auto_dienst_setup")
    _try_import("team_overview", "team_overview",    "auto_team_setup")
    _try_import("boost",         "boost",            "auto_boost_setup")
    _try_import("lotto",         "lotto",            "auto_lotto_setup")
    _try_import("startinfo",     "startinfo",        "auto_startinfo_setup")
    _try_import("starterpaket",  "starterpaket",     "auto_starterpaket_setup")
    _try_import("nebenserver",   "nebenserver",      "auto_nebenserver_setup")
    _try_import("human_labs",    "human_labs_raub",  "_hl_info_auto_setup")
    _try_import("staatsbank",    "staatsbank_raub",  "_sb_info_auto_setup")
    _try_import("aktien",        "aktien",           "aktien_setup")
    _try_import("shop",          "shop",             "auto_shop_setup")
    _try_import("kokain",        "kokain",           "auto_kokain_setup")
    _try_import("weed",          "weed",             "auto_weed_setup")
    _try_import("angeln",        "angeln",           "auto_angeln_setup")
    _try_import("angler_shop",   "angeln",           "auto_angler_shop_setup")
    _try_import("info_embeds",   "info_embeds",      "auto_info_embeds_setup")

    for name, fn in _setups:
        try:
            await fn()
        except Exception as e:
            print(f"[embed_manager] âŒ Fehler in {name}: {e}")

    try:
        from help_embed import update_help_embed
        await update_help_embed()
    except Exception as e:
        print(f"[embed_manager] \u274C Fehler in help_embed: {e}")

    print("[embed_manager] \u2705 Alle Embeds eingerichtet")
