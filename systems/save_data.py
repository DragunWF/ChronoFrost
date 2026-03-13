"""
Manages save_data.json for persistent leaderboard and lifetime statistics.
All I/O is wrapped in try/except to handle corrupt or missing files safely.
"""
from __future__ import annotations

import copy
import datetime
import json
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Path & schema
# ---------------------------------------------------------------------------

_SAVE_PATH = "data/save_data.json"

_MAX_LEADERBOARD = 10

_TEMPLATE: Dict[str, Any] = {
    "leaderboard": [],
    "lifetime_stats": {
        "total_shattered": 0,
        "total_time_played": 0,
        "runs_completed": 0,
    },
}


def _blank() -> Dict[str, Any]:
    return copy.deepcopy(_TEMPLATE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load() -> Dict[str, Any]:
    """Load save data from disk; returns a fresh template on any read error."""
    try:
        with open(_SAVE_PATH, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if not isinstance(raw.get("leaderboard"), list):
            raise ValueError("bad leaderboard")
        if not isinstance(raw.get("lifetime_stats"), dict):
            raise ValueError("bad lifetime_stats")
        return raw
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError, OSError, IOError):
        # Return blank template on any I/O error (common in browser environments)
        return _blank()


def _write(data: Dict[str, Any]) -> None:
    try:
        with open(_SAVE_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except (OSError, IOError):
        # Non-critical; saves are best-effort (esp. in browser environments)
        pass


def record_run(
    score: int,
    time_survived: float,
    enemies_shattered: int,
    boons_acquired: int,
) -> Tuple[bool, int]:
    """
    Persist end-of-run stats. Called exactly once per run at game-over.

    Returns
    -------
    (is_new_top5, rank)  where rank is 1-indexed (1 = best) and 0 means the
    score did not make the leaderboard at all.
    """
    data = load()

    mins = int(time_survived // 60)
    secs = int(time_survived % 60)
    entry: Dict[str, Any] = {
        "score": score,
        "date":  datetime.date.today().isoformat(),
        "time":  f"{mins:02d}:{secs:02d}",
    }

    board: List[Dict[str, Any]] = data["leaderboard"]
    board.append(entry)
    board.sort(key=lambda e: e["score"], reverse=True)
    board = board[:_MAX_LEADERBOARD]
    data["leaderboard"] = board

    ls = data["lifetime_stats"]
    ls["total_shattered"] = ls.get("total_shattered",   0) + enemies_shattered
    ls["total_time_played"] = ls.get(
        "total_time_played", 0) + int(time_survived)
    ls["runs_completed"] = ls.get("runs_completed",    0) + 1

    _write(data)

    # Locate the just-inserted entry by object identity (pre-GC, same in-process list)
    rank = next((i + 1 for i, e in enumerate(board) if e is entry), 0)
    return 0 < rank <= 5, rank


def get_leaderboard() -> List[Dict[str, Any]]:
    """Return the leaderboard list (sorted best-first)."""
    return load()["leaderboard"]


def get_lifetime_stats() -> Dict[str, Any]:
    """Return the lifetime stats dict."""
    return load()["lifetime_stats"]
