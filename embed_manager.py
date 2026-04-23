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

    from ticket        import auto_ticket_setup, auto_lohnliste_setup
    from handy         import auto_handy_setup
    from einreise      import auto_einreise_setup
    from casino        import auto_casino_setup
    from dienst        import auto_dienst_setup
    from team_overview import auto_team_setup
    from boost         import auto_boost_setup
    from lotto         import auto_lotto_setup
    from startinfo     import auto_startinfo_setup
    from starterpaket  import auto_starterpaket_setup
    from nebenserver   import auto_nebenserver_setup
    from human_labs_raub  import _hl_info_auto_setup
    from staatsbank_raub  import _sb_info_auto_setup
    from aktien        import aktien_setup
    from shop          import auto_shop_setup

    _setups = [
        ("ticket",        auto_ticket_setup),
        ("lohnliste",     auto_lohnliste_setup),
        ("einreise",      auto_einreise_setup),
        ("handy",         auto_handy_setup),
        ("casino",        auto_casino_setup),
        ("dienst",        auto_dienst_setup),
        ("team_overview", auto_team_setup),
        ("boost",         auto_boost_setup),
        ("lotto",         auto_lotto_setup),
        ("startinfo",     auto_startinfo_setup),
        ("starterpaket",  auto_starterpaket_setup),
        ("nebenserver",   auto_nebenserver_setup),
        ("human_labs",    _hl_info_auto_setup),
        ("staatsbank",    _sb_info_auto_setup),
        ("aktien",        aktien_setup),
        ("shop",          auto_shop_setup),
    ]

    for name, fn in _setups:
        try:
            await fn()
        except Exception as e:
            print(f"[embed_manager] \u274C Fehler in {name}: {e}")

    try:
        from help_embed import update_help_embed
        await update_help_embed()
    except Exception as e:
        print(f"[embed_manager] \u274C Fehler in help_embed: {e}")

    print("[embed_manager] \u2705 Alle Embeds eingerichtet")
