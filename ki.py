# -*- coding: utf-8 -*-
# ki.py — Groq KI-Assistent (direkte HTTP-Anfragen via aiohttp)
# Paradise City Roleplay Discord Bot

import aiohttp
import os
from datetime import datetime, timezone

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
COOLDOWN_SECONDS = 15
MAX_ANTWORT_LEN  = 1800

# Cooldown-Speicher: user_id -> letzter Aufruf
cooldowns: dict[int, datetime] = {}

# Damit commands.py "if not _ki.model" pruefen kann
model = True if GROQ_API_KEY else None

_SYSTEM = (
    "Du bist der KI-Assistent von Paradise City Roleplay (PCRP), "
    "einem deutschen GTA V Roleplay-Server. "
    "Antworte immer auf Deutsch, freundlich und praezise (max. 1800 Zeichen). "
    "Wenn du etwas nicht weisst, sage es ehrlich."
)

# Modelle der Reihe nach versuchen
_MODELLE = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]

if not GROQ_API_KEY:
    print("[ki] GROQ_API_KEY nicht gesetzt — KI-Modul deaktiviert.")
else:
    print("[ki] Bereit (Groq API).")


async def ask(frage: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY fehlt.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }

    payload = {
        "model": _MODELLE[0],
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": frage},
        ],
        "max_tokens": 800,
        "temperature": 0.7,
    }

    letzter_fehler = None
    async with aiohttp.ClientSession(headers=headers) as session:
        for modell in _MODELLE:
            payload["model"] = modell
            url = "https://api.groq.com/openai/v1/chat/completions"
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                    data = await resp.json(content_type=None)
                    if resp.status == 200:
                        text = data["choices"][0]["message"]["content"].strip()
                        if len(text) > MAX_ANTWORT_LEN:
                            text = text[:MAX_ANTWORT_LEN] + "\n*\u2026(gek\u00fcrzt)*"
                        print(f"[ki] OK via {modell}")
                        return text
                    fehler = data.get("error", {}).get("message", f"HTTP {resp.status}")
                    print(f"[ki] {modell} -> {fehler}")
                    letzter_fehler = fehler
            except Exception as exc:
                print(f"[ki] {modell} -> Ausnahme: {exc}")
                letzter_fehler = exc

    raise RuntimeError(f"Kein Modell verfuegbar. Letzter Fehler: {letzter_fehler}")
