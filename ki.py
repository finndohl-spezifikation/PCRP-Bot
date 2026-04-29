# -*- coding: utf-8 -*-
# ki.py — Google Gemini Hilfsfunktionen (direkte HTTP-Anfragen via aiohttp)
# Paradise City Roleplay Discord Bot

import aiohttp
import os
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

# Modelle der Reihe nach versuchen
_MODELLE = [
    ("v1beta", "gemini-2.0-flash"),
    ("v1beta", "gemini-2.0-flash-lite"),
    ("v1beta", "gemini-1.5-flash-latest"),
    ("v1beta", "gemini-1.5-flash-8b"),
    ("v1",     "gemini-2.0-flash"),
    ("v1",     "gemini-1.5-flash"),
]

# Cooldown-Speicher: user_id -> letzter Aufruf
cooldowns: dict[int, datetime] = {}

# Damit commands.py model != None pruefen kann
model = True if GEMINI_API_KEY else None

if not GEMINI_API_KEY:
    print("[ki] \u26a0\ufe0f  GEMINI_API_KEY nicht gesetzt \u2014 KI-Modul deaktiviert.")
else:
    print("[ki] \u2705 KI-Modul bereit (direkte HTTP-Anfragen an Gemini API).")


async def ask(frage: str) -> str:
    """Stellt eine Frage an Gemini API und gibt die Antwort als String zur\u00fcck."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY fehlt.")

    # Systemkontext direkt in die Nutzernachricht einbetten —
    # das ist das kompatibelste Format f\u00fcr alle Gemini-Modelle
    nachricht = f"{_SYSTEM_PROMPT}\n\nFrage des Nutzers: {frage}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": nachricht}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 800,
            "temperature": 0.7,
        }
    }

    letzter_fehler = None
    async with aiohttp.ClientSession() as session:
        for api_version, model_name in _MODELLE:
            url = (
                f"https://generativelanguage.googleapis.com"
                f"/{api_version}/models/{model_name}:generateContent"
                f"?key={GEMINI_API_KEY}"
            )
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        antwort = (
                            data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        )
                        if len(antwort) > MAX_ANTWORT_LEN:
                            antwort = antwort[:MAX_ANTWORT_LEN] + "\n*\u2026(Antwort gek\u00fcrzt)*"
                        print(f"[ki] \u2705 Antwort erhalten via {api_version}/{model_name}")
                        return antwort
                    else:
                        err = data.get("error", {}).get("message", str(data))
                        print(f"[ki] {api_version}/{model_name} -> HTTP {resp.status}: {err}")
                        letzter_fehler = err
            except Exception as e:
                print(f"[ki] {api_version}/{model_name} -> Fehler: {e}")
                letzter_fehler = e

    raise RuntimeError(f"Kein Gemini-Modell verf\u00fcgbar. Letzter Fehler: {letzter_fehler}")
