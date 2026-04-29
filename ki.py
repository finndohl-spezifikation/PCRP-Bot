# -*- coding: utf-8 -*-
# ki.py — Google Gemini Hilfsfunktionen
# Paradise City Roleplay Discord Bot

import google.generativeai as genai
import os
import asyncio
from datetime import datetime, timezone

GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
COOLDOWN_SECONDS = 15
MAX_ANTWORT_LEN  = 1800

_SYSTEM_PROMPT = (
    "Du bist der freundliche KI-Assistent des Discord-Bots von "
    "Paradise City Roleplay (PCRP) \u2014 einem deutschen GTA V Roleplay-Server.\n"
    "Du hilfst Spielern bei Fragen rund um den Server, GTA Roleplay-Mechaniken, "
    "Regeln und allgemeinen Themen.\n"
    "Halte deine Antworten immer auf Deutsch, klar und pr\u00e4zise. "
    "Nutze maximal 1800 Zeichen. Wenn du etwas nicht wei\u00dft, sage es ehrlich.\n"
    "Du produzierst keine beleidigenden, diskriminierenden oder unangemessenen Inhalte."
)

# Cooldown-Speicher: user_id \u2192 letzter Aufruf
cooldowns: dict[int, datetime] = {}


def _init_model():
    if not GEMINI_API_KEY:
        print("[ki] \u26a0\ufe0f  GEMINI_API_KEY nicht gesetzt \u2014 KI-Modul deaktiviert.")
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    # Modelle der Reihe nach versuchen (neueste zuerst)
    for model_name in ("gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"):
        try:
            m = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=_SYSTEM_PROMPT,
            )
            print(f"[ki] \u2705 Google Gemini Modell geladen ({model_name}).")
            return m
        except Exception as e:
            print(f"[ki] \u26a0\ufe0f  {model_name} nicht verf\u00fcgbar: {e}")
    print("[ki] \u274c Kein Gemini-Modell verf\u00fcgbar.")
    return None


model = _init_model()

_MODELLE = (
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest",
    "gemini-pro",
)


def _get_model(name: str):
    return genai.GenerativeModel(
        model_name=name,
        system_instruction=_SYSTEM_PROMPT,
    )


async def ask(frage: str) -> str:
    """Stellt eine Frage an Gemini — probiert automatisch alle verf\u00fcgbaren Modelle."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY fehlt.")

    letzter_fehler = None
    for model_name in _MODELLE:
        try:
            m = _get_model(model_name)
            response = await asyncio.to_thread(m.generate_content, frage)
            antwort  = response.text.strip()
            if len(antwort) > MAX_ANTWORT_LEN:
                antwort = antwort[:MAX_ANTWORT_LEN] + "\n*\u2026(Antwort gek\u00fcrzt)*"
            return antwort
        except Exception as e:
            print(f"[ki] {model_name} fehlgeschlagen: {e}")
            letzter_fehler = e

    raise RuntimeError(f"Kein Gemini-Modell verf\u00fcgbar. Letzter Fehler: {letzter_fehler}")
