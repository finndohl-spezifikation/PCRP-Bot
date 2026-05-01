# -*- coding: utf-8 -*-
# ausweis_tokens.py — Token-Verwaltung für Ausweis-Webformular
import uuid, time

_tokens: dict = {}
TTL = 900  # 15 Minuten


def create(uid: int, einreise_typ: str) -> str:
    for t in list(_tokens.keys()):
        if _tokens[t].get("uid") == uid:
            del _tokens[t]
    token = uuid.uuid4().hex
    _tokens[token] = {
        "uid": uid,
        "einreise_typ": einreise_typ,
        "expires": time.time() + TTL,
    }
    return token


def get(token: str) -> dict | None:
    entry = _tokens.get(token)
    if not entry:
        return None
    if time.time() > entry["expires"]:
        del _tokens[token]
        return None
    return entry


def consume(token: str) -> dict | None:
    entry = get(token)
    if entry and token in _tokens:
        del _tokens[token]
    return entry
