# -*- coding: utf-8 -*-
# ki.py — Groq KI-Assistent mit Konversationsmodus
# Paradise City Roleplay Discord Bot

import aiohttp
import os
from datetime import datetime, timezone

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
COOLDOWN_SECONDS = 5
MAX_ANTWORT_LEN  = 1800

# Aktive Konversationen: channel_id -> user_id
active_sessions: dict[int, int] = {}

# Cooldown-Speicher: user_id -> letzter Aufruf
cooldowns: dict[int, datetime] = {}

# Damit commands.py "if not _ki.model" pruefen kann
model = True if GROQ_API_KEY else None

_SYSTEM = (
    "Du bist ein hilfreicher KI-Assistent. "
    "Beantworte alle Fragen ehrlich, klar und praezise. "
    "Antworte immer in der Sprache des Nutzers. "
    "Halte deine Antworten unter 1800 Zeichen."
)

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


def setup(bot):
    """Registriert den on_message-Listener fuer den Konversationsmodus."""

    @bot.listen("on_message")
    async def ki_message_handler(message):
        # Bot-Nachrichten und Slash-Commands ignorieren
        if message.author.bot:
            return
        if message.content.startswith("/"):
            return

        channel_id = message.channel.id
        if channel_id not in active_sessions:
            return

        session_user_id = active_sessions[channel_id]

        # Jemand anderes schreibt rein -> einschreiten
        if message.author.id != session_user_id:
            await message.channel.send(
                f"{message.author.mention} NaNaNa Ich f\u00fchre gerade eine Konversation, "
                "es ist Unfreundlich uns ins Wort zu fallen du Pisser \U0001f6ab"
            )
            return

        # Nachricht des Session-Nutzers -> an KI weiterleiten
        if not GROQ_API_KEY:
            await message.channel.send("\u274c KI nicht verf\u00fcgbar (GROQ_API_KEY fehlt).")
            return

        now  = datetime.now(timezone.utc)
        last = cooldowns.get(message.author.id)
        if last and (now - last).total_seconds() < COOLDOWN_SECONDS:
            return  # Cooldown still running - silently ignore

        cooldowns[message.author.id] = now

        async with message.channel.typing():
            try:
                antwort = await ask(message.content)
                await message.channel.send(antwort)
            except Exception as exc:
                await message.channel.send(f"\u274c Fehler: `{exc}`")
