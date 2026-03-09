"""
Boon pool and apply-functions.
Each boon is a plain dict so BoonsMenu can iterate the list without importing
every individual class.  apply_fn(run_stats) mutates RunStats in-place.
"""

from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from systems.run_stats import RunStats


# ---------------------------------------------------------------------------
# Apply functions — one per boon
# ---------------------------------------------------------------------------

def _apply_pierce_shot(run_stats: "RunStats") -> None:
    run_stats.pierce_count += 1


def _apply_rapid_fire(run_stats: "RunStats") -> None:
    # Each stack multiplies cooldown by 0.8; minimum mult 0.4 → 80ms at 200ms base
    run_stats.fire_cooldown_mult = max(0.4, run_stats.fire_cooldown_mult * 0.8)


def _apply_spread_shot(run_stats: "RunStats") -> None:
    run_stats.spread_shot = True


def _apply_heavy_caliber(run_stats: "RunStats") -> None:
    run_stats.heavy_caliber = True


def _apply_deep_freeze(run_stats: "RunStats") -> None:
    run_stats.deep_freeze_stacks += 1


def _apply_ember_magnet(run_stats: "RunStats") -> None:
    run_stats.ember_magnet_bonus += 40.0


def _apply_kinetic_plating(run_stats: "RunStats") -> None:
    run_stats.kinetic_plating_stacks += 1


def _apply_overclock(run_stats: "RunStats") -> None:
    run_stats.overclock_stacks += 1


# ---------------------------------------------------------------------------
# Boon pool — authoritative list consumed by BoonsMenu
# ---------------------------------------------------------------------------

BOON_POOL: List[Dict[str, Any]] = [
    {
        "name": "PierceShot",
        "category": "COMBAT",
        "description": "Bullets pass through\nan extra enemy.",
        "apply_fn": _apply_pierce_shot,
    },
    {
        "name": "RapidFire",
        "category": "COMBAT",
        "description": "-20% fire cooldown.\nStackable (min 80ms).",
        "apply_fn": _apply_rapid_fire,
    },
    {
        "name": "SpreadShot",
        "category": "COMBAT",
        "description": "Fire 3 bullets in\na spread cone.",
        "apply_fn": _apply_spread_shot,
    },
    {
        "name": "HeavyCaliber",
        "category": "COMBAT",
        "description": "+50% bullet damage.\n-30% fire rate.",
        "apply_fn": _apply_heavy_caliber,
    },
    {
        "name": "DeepFreeze",
        "category": "UTILITY",
        "description": "+25 max Chrono-\nFreeze capacity.",
        "apply_fn": _apply_deep_freeze,
    },
    {
        "name": "EmberMagnet",
        "category": "UTILITY",
        "description": "Ember pickup radius\n+40px.",
        "apply_fn": _apply_ember_magnet,
    },
    {
        "name": "KineticPlating",
        "category": "UTILITY",
        "description": "Every 5th hit taken\ncuts cooldowns by 1s.",
        "apply_fn": _apply_kinetic_plating,
    },
    {
        "name": "Overclock",
        "category": "UTILITY",
        "description": "Chrono-Freeze costs\n15% less per second.",
        "apply_fn": _apply_overclock,
    },
]
