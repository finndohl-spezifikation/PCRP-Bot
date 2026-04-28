# -*- coding: utf-8 -*-
# ═════════════════════════════════════════════════════════════════
# info_embeds.py — Statische Info-Embeds (Save Zones, Fraktionsregelwerk)
# Paradise City Roleplay Discord Bot
# ═════════════════════════════════════════════════════════════════
#
# Postet beim Bot-Start zwei orangene Info-Embeds in feste Kanäle.
# Die Message-IDs werden lokal gespeichert, damit der Bot beim
# nächsten Start die bestehende Nachricht editiert statt eine
# neue zu posten (kein Spam, keine Doppelposts).
#
# Aufgerufen über embed_manager.setup_all_embeds().
# ═════════════════════════════════════════════════════════════════

from config import *

# ── Channel-IDs ──────────────────────────────────────────────────
SAVE_ZONES_CHANNEL_ID         = 1490882549499564184
FRAKTIONS_REGEL_CHANNEL_ID    = 1490882548266696849
FRAKTIONS_REGEL_AENDERUNG_CH  = 1490882547310399508  # für §11 Mention

# ── Persistente Message-IDs ──────────────────────────────────────
SAVE_ZONES_MSG_FILE       = DATA_DIR / "info_embed_savezones.json"
FRAKTIONS_REGEL_MSG_FILE  = DATA_DIR / "info_embed_fraktionsregel.json"

# ── Farbe (Discord-Orange) ───────────────────────────────────────
ORANGE = 0xE67E22


# ─────────────────────────────────────────────────────────────────
# Embed-Builder
# ─────────────────────────────────────────────────────────────────
def _build_save_zones_embed() -> discord.Embed:
    desc = (
        "> Regierungsgebäude, alle Flächen und Objekte staatlicher "
        "Unternehmen und die Spieler, die sich dort befinden, dürfen "
        "weder angegriffen noch entführt werden. Beim PD-Gebäude "
        "besteht die Ausnahme: Wenn ein Überfall geplant ist oder "
        "sich ein Fraktionsmitglied in Gewahrsam befindet, darf das "
        "betroffene Mitglied befreit werden.\n\n"
        "> Verstöße jeglicher Art werden sanktioniert."
    )
    emb = discord.Embed(
        title="__**Save Zones**__",
        description=desc,
        color=ORANGE,
    )
    emb.set_footer(text="Paradise City Roleplay")
    return emb


def _build_fraktions_regel_embed() -> discord.Embed:
    desc = (
        "**§1** **Geltungsbereich**\n"
        "> Dieses Regelwerk gilt für alle Fraktionen auf dem Server. "
        "Jedes Fraktionsmitglied ist verpflichtet, sich an die folgenden "
        "Bestimmungen zu halten.\n\n"

        "**§2** **Allgemeines Verhalten**\n"
        "> (1) Grundloses Angreifen von Spielern, Beamten oder anderen "
        "Fraktionen ohne entsprechenden RP-Hintergrund ist untersagt.\n"
        "> (2) Jegliche Form von unrealistischem oder regelwidrigem "
        "Verhalten ist zu unterlassen.\n\n"

        "**§3** **Illegale Routen**\n"
        "> (1) Fraktionen sind berechtigt, illegale Routen für sich zu "
        "beanspruchen.\n"
        "> (2) Die Klärung und Durchsetzung solcher Ansprüche muss "
        "ausschließlich IC (In Character) erfolgen.\n\n"

        "**§4** **Gambo-Verhalten**\n"
        "> (1) Auffälliges, nicht RP-basiertes Kampfverhalten („Gambo“) "
        "ist untersagt.\n"
        "> (2) Verstöße führen zu Fraktionsverwarnungen.\n"
        "> (3) Im Wiederholungsfall kann die Fraktion aufgelöst werden.\n\n"

        "**§5** **Fraktionsgründung**\n"
        "> (1) Jede Fraktion muss vor der Gründung eine Bewerbung bzw. "
        "Anmeldung einreichen.\n"
        "> (2) Über die Annahme entscheidet die Projektleitung.\n"
        "> (3) Es besteht kein Anspruch auf Genehmigung.\n\n"

        "**§6** **Namensgebung**\n"
        "> Echtnamen sowie Fraktionsnamen von anderen Servern sind "
        "erlaubt.\n\n"

        "**§7** **Ausstattung**\n"
        "> (1) Es bestehen keine Einschränkungen hinsichtlich "
        "Fraktionskleidung, Fahrzeugen oder Immobilien.\n"
        "> (2) Die Nutzung hat dennoch im Rahmen des Roleplays zu "
        "erfolgen.\n\n"

        "**§8** **Mitgliederanzahl**\n"
        "> (1) Ein festes Limit für Fraktionsmitglieder besteht "
        "grundsätzlich nicht.\n"
        "> (2) Überschreitet eine Fraktion die Anzahl von 15 "
        "Mitgliedern, kann eine Aufteilung in mehrere Fraktionen "
        "durch die Projektleitung angeordnet oder empfohlen werden.\n\n"

        "**§9** **Fraktionsgüter**\n"
        "> (1) Der Server stellt keine Fraktionsgüter zur Verfügung.\n"
        "> (2) Fahrzeuge, Immobilien, Waffen und sonstige Gegenstände "
        "müssen IC erworben werden.\n"
        "> (3) Ausgenommen hiervon sind Kleidungsgegenstände.\n\n"

        "**§10** **Sanktionen**\n"
        "> (1) Wiederholtes negatives Auffallen einer Fraktion kann zu "
        "Fraktionsverwarnungen führen.\n"
        "> (2) Im Extremfall kann eine Fraktionssperre oder Auflösung "
        "erfolgen.\n"
        "> (3) Vergehen einzelner Mitglieder werden grundsätzlich "
        "individuell bestraft.\n"
        "> (4) Erfolgt das Fehlverhalten im Namen der Fraktion, kann "
        "die gesamte Fraktion sanktioniert werden.\n\n"

        "**§11** **Änderungen**\n"
        f"> Die Projektleitung behält sich das Recht vor, das "
        f"Fraktionsregelwerk jederzeit in Absprache mit dem Serverteam "
        f"zu verändern. Änderungen treten sofort in Kraft und werden "
        f"in <#{FRAKTIONS_REGEL_AENDERUNG_CH}> angekündigt."
    )
    emb = discord.Embed(
        title="📜 Fraktionsregelwerk",
        description=desc,
        color=ORANGE,
    )
    emb.set_footer(text="Paradise City Roleplay • Fraktionen")
    return emb


# ─────────────────────────────────────────────────────────────────
# Send / Edit Helper
# ─────────────────────────────────────────────────────────────────
async def _send_or_edit(channel, msg_file, embed) -> str:
    """Editiert die bestehende Nachricht falls vorhanden, sonst neu posten.
    Speichert die Message-ID lokal, damit Reposts vermieden werden."""
    msg_id = None
    try:
        if msg_file.exists():
            msg_id = json.load(open(msg_file, encoding="utf-8")).get("message_id")
    except Exception:
        pass

    if msg_id:
        try:
            existing = await channel.fetch_message(msg_id)
            await existing.edit(embed=embed)
            return "✅ aktualisiert"
        except Exception:
            pass  # Nachricht gelöscht oder unauffindbar → neu senden

    try:
        sent = await channel.send(embed=embed)
        json.dump(
            {"message_id": sent.id},
            open(msg_file, "w", encoding="utf-8"),
            indent=2,
        )
        return "✅ neu gesendet"
    except Exception as e:
        return f"❌ Fehler beim Senden: {e}"


# ─────────────────────────────────────────────────────────────────
# Auto-Setup (wird von embed_manager.setup_all_embeds aufgerufen)
# ─────────────────────────────────────────────────────────────────
async def auto_info_embeds_setup():
    await bot.wait_until_ready()
    await asyncio.sleep(3)

    # ── Save Zones ──────────────────────────────────────────────
    try:
        ch = await bot.fetch_channel(SAVE_ZONES_CHANNEL_ID)
        result = await _send_or_edit(ch, SAVE_ZONES_MSG_FILE, _build_save_zones_embed())
        print(f"[info_embeds] Save Zones: {result}")
    except Exception as e:
        print(f"[info_embeds] ❌ Save Zones Kanal nicht erreichbar ({SAVE_ZONES_CHANNEL_ID}): {e}")

    # ── Fraktionsregelwerk ──────────────────────────────────────
    try:
        ch = await bot.fetch_channel(FRAKTIONS_REGEL_CHANNEL_ID)
        result = await _send_or_edit(ch, FRAKTIONS_REGEL_MSG_FILE, _build_fraktions_regel_embed())
        print(f"[info_embeds] Fraktionsregelwerk: {result}")
    except Exception as e:
        print(f"[info_embeds] ❌ Fraktionsregelwerk Kanal nicht erreichbar ({FRAKTIONS_REGEL_CHANNEL_ID}): {e}")
