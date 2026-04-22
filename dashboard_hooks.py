# -*- coding: utf-8 -*-
import json
import threading
from pathlib import Path
from datetime import datetime, timezone

from config import DATA_DIR

ACTIVITY_LOG_FILE  = DATA_DIR / "dashboard_activity_log.json"
WARNINGS_LOG_FILE  = DATA_DIR / "dashboard_warnings_log.json"
MEMBERS_CACHE_FILE = DATA_DIR / "dashboard_members.json"
INVITES_CACHE_FILE = DATA_DIR / "dashboard_invites.json"
NOTES_FILE         = DATA_DIR / "dashboard_notes.json"
BLACKLIST_FILE     = DATA_DIR / "dashboard_blacklist.json"

MAX_LOG_ENTRIES = 1000
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _read_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text("utf-8"))
    except Exception:
        pass
    return default


def _write_json(path: Path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _append_log(file: Path, entry: dict, max_entries: int = MAX_LOG_ENTRIES):
    with _lock:
        entries = _read_json(file, [])
        entries.insert(0, entry)
        if len(entries) > max_entries:
            entries = entries[:max_entries]
        _write_json(file, entries)


def log_activity(typ: str, beschreibung: str, user_id: int = None, extra: str = None):
    entry = {
        "time":  _now(),
        "type":  typ,
        "desc":  beschreibung,
        "user":  str(user_id) if user_id else None,
        "extra": extra,
    }
    _append_log(ACTIVITY_LOG_FILE, entry)


def log_warning(title: str, beschreibung: str):
    entry = {
        "time":  _now(),
        "title": title,
        "desc":  beschreibung,
    }
    _append_log(WARNINGS_LOG_FILE, entry)


def update_member(member):
    with _lock:
        cache = _read_json(MEMBERS_CACHE_FILE, {})
        cache[str(member.id)] = {
            "name":   member.display_name,
            "tag":    str(member),
            "avatar": str(member.display_avatar.url) if member.display_avatar else "",
            "roles":  [r.id for r in getattr(member, "roles", [])],
        }
        _write_json(MEMBERS_CACHE_FILE, cache)


def remove_member(member_id: int):
    with _lock:
        cache = _read_json(MEMBERS_CACHE_FILE, {})
        cache.pop(str(member_id), None)
        _write_json(MEMBERS_CACHE_FILE, cache)


def update_invites(invite_map: dict):
    with _lock:
        _write_json(INVITES_CACHE_FILE, invite_map)


def get_member_name(user_id) -> str:
    cache = _read_json(MEMBERS_CACHE_FILE, {})
    entry = cache.get(str(user_id))
    if entry:
        return entry.get("name") or entry.get("tag") or str(user_id)
    return str(user_id)
