"""Incremental cache for JSONL parsing with file-offset tracking."""
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Tuple

CACHE_VERSION = 1


def load_cache(cache_path: str) -> dict:
    """Load cache from disk. Returns empty structure if absent or invalid."""
    try:
        with open(cache_path) as f:
            cache = json.load(f)
        if cache.get("version") != CACHE_VERSION:
            return _empty_cache()
        return cache
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return _empty_cache()


def save_cache(cache: dict, cache_path: str) -> None:
    """Atomically save cache to disk."""
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    tmp_path = cache_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(cache, f)
    os.replace(tmp_path, cache_path)


def is_window_expired(cache: dict) -> bool:
    """Check if the current 5-hour window has expired."""
    window_end = cache.get("window_end")
    if not window_end:
        return True
    return datetime.now(timezone.utc) >= datetime.fromisoformat(window_end)


def compute_window_boundaries(
    now: datetime, window_hours: int = 5
) -> Tuple[str, str]:
    """Compute 5-hour window boundaries. Floor to UTC hour boundary."""
    window_start = now.replace(minute=0, second=0, microsecond=0)
    window_end = window_start + timedelta(hours=window_hours)
    return window_start.isoformat(), window_end.isoformat()


def _empty_cache() -> dict:
    return {
        "version": CACHE_VERSION,
        "window_start": None,
        "window_end": None,
        "accumulated_cost": 0.0,
        "total_requests": 0,
        "last_activity": None,
        "file_offsets": {},
        "file_mtimes": {},
        "seen_request_ids": [],
        "last_updated": None,
    }
