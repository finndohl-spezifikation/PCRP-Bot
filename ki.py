# -*- coding: utf-8 -*-
# ki.py — Google Gemini KI-Assistent
# Paradise City Roleplay Discord Bot

import aiohttp
import os
from datetime import datetime, timezone

GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
COOLDOWN_SECONDS = 15
MAX_ANTWORT_LEN  = 1800

# Cooldown-Speicher: user_id -> letzter Aufruf
cooldowns: dict[int, datetime] = {}

# Damit commands.py "if not _ki.model" pruefen kann
model = True if GEMINI_API_KEY else None

_KONTEXT = (
    "Du bist der KI-Assistent von Paradise City Roleplay (PCRP), "
    "einem deutschen GTA V Roleplay-Server. "
    "Antworte immer auf Deutsch, freundlich und kurz (max. 1800 Zeichen). "
    "Wenn du etwas nicht weisst, sage es ehrlich."
)

if not GEMINI_API_KEY:
    print("[ki] GEMINI_API_KEY nicht gesetzt.")
else:
    print("[ki] Bereit.")


async def ask(frage: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY fehlt.")

    # Einfachstes gueltiges Payload-Format fuer alle Gemini-Modelle
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{_KONTEXT}\n\nFrage: {frage}"}
                ]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    modelle = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-2.0-flash-lite",
    ]

    letzter_fehler = None
    async with aiohttp.ClientSession(headers=headers) as session:
        for modell in modelle:
            url = (
                "https://generativelanguage.googleapis.com"
                f"/v1beta/models/{modell}:generateContent"
                f"?key={GEMINI_API_KEY}"
            )
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                    data = await resp.json(content_type=None)
                    if resp.status == 200:
                        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
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
