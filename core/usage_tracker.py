"""Scan JSONL session files and calculate usage for the current 5-hour window."""
import json
import os
from datetime import datetime, timezone
from typing import List

from core.cache_manager import (
    _empty_cache,
    compute_window_boundaries,
    is_window_expired,
    load_cache,
    save_cache,
)
from core.config import load_config
from core.pricing import calculate_cost

PROJECTS_DIR = os.path.expanduser("~/.claude/projects")


def get_all_jsonl_files() -> List[str]:
    """Find all JSONL session files in ~/.claude/projects/."""
    files = []
    if not os.path.isdir(PROJECTS_DIR):
        return files
    for dirpath, _, filenames in os.walk(PROJECTS_DIR):
        for fname in filenames:
            if fname.endswith(".jsonl"):
                files.append(os.path.join(dirpath, fname))
    return files


def get_recently_modified_jsonl(since_mtime: float) -> List[str]:
    """Find JSONL files modified after a given mtime."""
    return [
        f
        for f in get_all_jsonl_files()
        if os.path.getmtime(f) > since_mtime
    ]


def parse_new_entries(
    file_path: str,
    start_offset: int,
    window_start_iso: str,
    window_end_iso: str,
    seen_ids: set,
    pricing_table: dict,
) -> dict:
    """Parse a JSONL file from byte offset, extract usage in the window."""
    result = {
        "new_cost": 0.0,
        "new_request_ids": [],
        "new_offset": start_offset,
        "latest_timestamp": None,
    }

    try:
        file_size = os.path.getsize(file_path)
        # If file was truncated/rotated, reset offset
        if file_size < start_offset:
            start_offset = 0

        if file_size <= start_offset:
            result["new_offset"] = file_size
            return result

        with open(file_path, "r") as f:
            f.seek(start_offset)
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Only process assistant messages with usage data
                if entry.get("type") != "assistant":
                    continue

                message = entry.get("message", {})
                usage = message.get("usage")
                if not usage:
                    continue

                timestamp = entry.get("timestamp")
                if not timestamp:
                    continue

                # Skip entries outside our window
                if timestamp < window_start_iso or timestamp >= window_end_iso:
                    continue

                # Deduplicate by requestId
                request_id = entry.get("requestId", "")
                if request_id and request_id in seen_ids:
                    continue

                model = message.get("model", "default")
                cost = calculate_cost(usage, model, pricing_table)

                result["new_cost"] += cost
                if request_id:
                    result["new_request_ids"].append(request_id)
                result["latest_timestamp"] = timestamp

            result["new_offset"] = f.tell()

    except (IOError, OSError):
        pass

    return result


def get_current_usage() -> dict:
    """Get current window usage stats.

    Returns dict with: cost, window_start, window_end,
    window_remaining_seconds, total_requests, status,
    threshold_pct, max_cost, message.
    """
    config = load_config()
    cache_path = os.path.expanduser(config["cache_file"])
    cache = load_cache(cache_path)

    now = datetime.now(timezone.utc)
    window_hours = config.get("window_hours", 5)
    max_cost = config["max_cost_per_window_usd"]
    warn_pct = config["warning_threshold_pct"]
    block_pct = config["block_threshold_pct"]
    pricing = config["pricing"]

    # Reset cache if window expired
    if is_window_expired(cache):
        cache = _empty_cache()

    seen_ids = set(cache.get("seen_request_ids", []))

    # Determine which files to scan
    if cache.get("last_updated"):
        last_ts = datetime.fromisoformat(cache["last_updated"]).timestamp() - 1
        files_to_scan = get_recently_modified_jsonl(last_ts)
    else:
        files_to_scan = get_all_jsonl_files()

    # Establish window if not set
    window_start_iso = cache.get("window_start")
    window_end_iso = cache.get("window_end")

    if not window_start_iso:
        window_start_iso, window_end_iso = compute_window_boundaries(
            now, window_hours
        )
        cache["window_start"] = window_start_iso
        cache["window_end"] = window_end_iso

    # Parse each file incrementally
    total_new_cost = 0.0
    all_new_ids = []

    for file_path in files_to_scan:
        offset = cache["file_offsets"].get(file_path, 0)

        current_mtime = os.path.getmtime(file_path)
        stored_mtime = cache["file_mtimes"].get(file_path, 0)

        if current_mtime <= stored_mtime and offset > 0:
            continue

        result = parse_new_entries(
            file_path, offset, window_start_iso, window_end_iso,
            seen_ids, pricing,
        )

        cache["file_offsets"][file_path] = result["new_offset"]
        cache["file_mtimes"][file_path] = current_mtime

        total_new_cost += result["new_cost"]
        all_new_ids.extend(result["new_request_ids"])
        seen_ids.update(result["new_request_ids"])

    # Update totals
    cache["accumulated_cost"] = cache.get("accumulated_cost", 0) + total_new_cost
    cache["total_requests"] = cache.get("total_requests", 0) + len(all_new_ids)
    cache["seen_request_ids"] = list(seen_ids)
    cache["last_updated"] = now.isoformat()

    # Determine status
    total_cost = cache["accumulated_cost"]
    pct = (total_cost / max_cost * 100) if max_cost > 0 else 0

    window_end_dt = datetime.fromisoformat(window_end_iso)
    remaining_seconds = max(0, int((window_end_dt - now).total_seconds()))

    if pct >= block_pct:
        status = "blocked"
    elif pct >= warn_pct:
        status = "warning"
    else:
        status = "ok"

    save_cache(cache, cache_path)

    # Human-readable message
    remaining_h = remaining_seconds // 3600
    remaining_m = (remaining_seconds % 3600) // 60

    if status == "blocked":
        message = (
            f"USAGE GUARD: Budget exhausted ({pct:.0f}% of ${max_cost:.2f}). "
            f"Window resets in {remaining_h}h{remaining_m:02d}m "
            f"(at {window_end_iso[:16]}Z). "
            f"All tool calls are blocked until then."
        )
    elif status == "warning":
        message = (
            f"USAGE GUARD WARNING: {pct:.0f}% of budget used "
            f"(${total_cost:.2f} / ${max_cost:.2f}). "
            f"Window resets in {remaining_h}h{remaining_m:02d}m."
        )
    else:
        message = (
            f"Usage: ${total_cost:.2f} / ${max_cost:.2f} "
            f"({pct:.0f}%) | Window resets in {remaining_h}h{remaining_m:02d}m"
        )

    return {
        "cost": total_cost,
        "window_start": window_start_iso,
        "window_end": window_end_iso,
        "window_remaining_seconds": remaining_seconds,
        "total_requests": cache["total_requests"],
        "status": status,
        "threshold_pct": pct,
        "max_cost": max_cost,
        "message": message,
    }
