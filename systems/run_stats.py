from dataclasses import dataclass, field
from typing import List


@dataclass
class RunStats:
    """
    Persistent run state shared by Player and bullet creation.
    Boon apply-functions mutate this in-place; it lives for the whole run.
    """

    # PierceShot: each stack lets bullets pass through one extra enemy
    pierce_count: int = 0

    # RapidFire: multiplied onto the base 200ms fire cooldown (0.8 per stack, floor 0.4)
    fire_cooldown_mult: float = 1.0

    # SpreadShot: fire 3 bullets in a ±15° cone instead of 1
    spread_shot: bool = False

    # HeavyCaliber: bullet damage ×2, fire rate ×0.7 (slower)
    heavy_caliber: bool = False

    # DeepFreeze: each stack adds 25 to the Chrono-Freeze max capacity
    deep_freeze_stacks: int = 0

    # EmberMagnet: bonus pixels added to ember pickup radius
    ember_magnet_bonus: float = 0.0

    # KineticPlating: number of active stacks; 5 hits triggers a cooldown cut
    kinetic_plating_stacks: int = 0
    kinetic_hits_since_proc: int = 0  # resets to 0 after every 5th hit

    # Overclock: each stack shaves 15% off the Chrono-Freeze drain rate
    overclock_stacks: int = 0

    # Boon names already picked this run — prevents duplicates
    selected_boons: List[str] = field(default_factory=list)
