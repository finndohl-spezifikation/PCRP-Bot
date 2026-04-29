# -*- coding: utf-8 -*-
# ki.py — KI-Assistent powered by Google Gemini
# Paradise City Roleplay Discord Bot

from config import *
import google.generativeai as genai
import os
import asyncio
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Konfiguration
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
COOLDOWN_SECONDS = 15          # Sekunden zwischen zwei Anfragen pro User
MAX_FRAGE_LEN    = 500         # Maximale Länge der Frage
MAX_ANTWORT_LEN  = 1800        # Maximale Länge der Antwort im Embed

# System-Prompt: Gibt der KI den PCRP-Kontext vor
_SYSTEM_PROMPT = (
    "Du bist der freundliche KI-Assistent des Discord-Bots von "
    "Paradise City Roleplay (PCRP) — einem deutschen GTA V Roleplay-Server.\n"
    "Du hilfst Spielern bei Fragen rund um den Server, GTA Roleplay-Mechaniken, "
    "Regeln und allgemeinen Themen.\n"
    "Halte deine Antworten immer auf Deutsch, klar und präzise. "
    "Nutze maximal 1800 Zeichen. Wenn du etwas nicht weißt, sage es ehrlich.\n"
    "Du produzierst keine beleidigenden, diskriminierenden oder unangemessenen Inhalte."
)

# ──────────────────────────────────────────────
# Modell initialisieren
# ──────────────────────────────────────────────
def _init_model():
    if not GEMINI_API_KEY:
        print("[ki] ⚠️  GEMINI_API_KEY nicht gesetzt — KI-Modul deaktiviert.")
        return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=_SYSTEM_PROMPT,
        )
        print("[ki] ✅ Google Gemini Modell geladen (gemini-1.5-flash).")
        return model
    except Exception as e:
        print(f"[ki] ❌ Fehler beim Laden des Modells: {e}")
        return None

_model = _init_model()

# Cooldown-Speicher: user_id → letzter Aufruf
_cooldowns: dict[int, datetime] = {}

# ──────────────────────────────────────────────
# /ki Slash-Command
# ──────────────────────────────────────────────
@bot.tree.command(
    name="ki",
    description="🤖 Stelle dem KI-Assistenten eine Frage",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(frage="Deine Frage an den KI-Assistenten")
async def ki_command(interaction: discord.Interaction, frage: str):

    # ── Modul verfügbar? ──
    if not _model:
        await interaction.response.send_message(
            "❌ Der KI-Assistent ist aktuell nicht verfügbar.\n"
            "*(GEMINI_API_KEY fehlt — bitte einen Admin kontaktieren)*",
            ephemeral=True,
        )
        return

    # ── Frage zu lang? ──
    if len(frage) > MAX_FRAGE_LEN:
        await interaction.response.send_message(
            f"❌ Deine Frage ist zu lang. Maximal **{MAX_FRAGE_LEN} Zeichen** erlaubt.",
            ephemeral=True,
        )
        return

    # ── Cooldown prüfen ──
    now  = datetime.now(timezone.utc)
    last = _cooldowns.get(interaction.user.id)
    if last:
        vergangen = (now - last).total_seconds()
        if vergangen < COOLDOWN_SECONDS:
            warte = int(COOLDOWN_SECONDS - vergangen) + 1
            await interaction.response.send_message(
                f"⏳ Bitte warte noch **{warte} Sekunden** bevor du erneut fragst.",
                ephemeral=True,
            )
            return

    await interaction.response.defer(ephemeral=True)
    _cooldowns[interaction.user.id] = now

    # ── Gemini API aufrufen ──
    try:
        response = await asyncio.to_thread(_model.generate_content, frage)
        antwort  = response.text.strip()
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler beim Abrufen der KI-Antwort:\n`{e}`",
            ephemeral=True,
        )
        return

    # ── Antwort kürzen falls nötig ──
    if len(antwort) > MAX_ANTWORT_LEN:
        antwort = antwort[:MAX_ANTWORT_LEN] + "\n*…(Antwort gekürzt)*"

    # ── Embed bauen ──
    sep = "\u2501" * 26
    embed = discord.Embed(
        title="🤖  KI-Assistent",
        description=sep,
        color=0x4285F4,
    )
    embed.add_field(
        name="❓  Deine Frage",
        value=f"> {frage}",
        inline=False,
    )
    embed.add_field(
        name="\u200b",
        value=sep,
        inline=False,
    )
    embed.add_field(
        name="💬  Antwort",
        value=antwort,
        inline=False,
    )
    embed.set_footer(
        text=f"Powered by Google Gemini  •  {interaction.user.display_name}"
    )

    await interaction.followup.send(embed=embed, ephemeral=True)
