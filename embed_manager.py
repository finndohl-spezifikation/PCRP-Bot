# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# embed_manager.py — Zentraler Embed-Manager
# Paradise City Roleplay Discord Bot
# ══════════════════════════════════════════════════════════════
#
# Ruft beim Start alle Auto-Setup-Funktionen auf.
# Neue Embeds hier eintragen — events.py bleibt sauber.
# ══════════════════════════════════════════════════════════════


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
    ]

    for name, fn in _setups:
        try:
            await fn()
        except Exception as e:
            print(f"[embed_manager] ❌ Fehler in {name}: {e}")

    try:
        from help_embed import update_help_embed
        await update_help_embed()
    except Exception as e:
        print(f"[embed_manager] ❌ Fehler in help_embed: {e}")

    print("[embed_manager] ✅ Alle Embeds eingerichtet")
