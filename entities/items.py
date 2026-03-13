import pygame
import math
import random
from typing import Tuple

# Probability that a destroyed enemy drops a powerup
SPAWN_CHANCE: float = 0.25

# All possible powerup types for random selection
POWERUP_TYPES = ["ThermalShield", "FlashStep", "Supernova", "ChronoSurge"]

# Distinct color per powerup type for visual differentiation
_TYPE_COLORS: dict = {
    "ThermalShield": (0, 200, 255),
    "FlashStep":     (255, 210, 50),
    "Supernova":     (255, 120, 30),
    "ChronoSurge":   (100, 255, 200),
}


class Powerup:
    """
    A Field Drop that spawns at an enemy's death position.
    Immediately applies its effect when the player overlaps it.
    FlashStep is the exception — it stores a charge for manual use (SHIFT).
    """

    def __init__(self, x: float, y: float, powerup_type: str) -> None:
        self.x = x
        self.y = y
        self.type = powerup_type
        self.pickup_radius: int = 25
        self.color: Tuple[int, int, int] = _TYPE_COLORS.get(
            powerup_type, (255, 255, 255)
        )
        # Bob animation — randomise starting phase so clustered drops don't sync
        self.bob_timer: float = random.uniform(0.0, math.tau)
        self._bob_offset: float = 0.0

    def update(self, dt: float) -> None:
        self.bob_timer += dt * 3.0
        self._bob_offset = math.sin(self.bob_timer) * 5.0

    def draw(self, screen: pygame.Surface) -> None:
        draw_y = int(self.y + self._bob_offset)
        cx, cy = int(self.x), draw_y

        # Soft glow ring drawn on a temporary SRCALPHA surface
        glow_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 55), (32, 32), 22)
        screen.blit(glow_surf, (cx - 32, cy - 32))

        # Outer coloured circle
        pygame.draw.circle(screen, self.color, (cx, cy), 14)

        # Dark inner disc so the icon has breathing room
        pygame.draw.circle(screen, (20, 20, 30), (cx, cy), 10)

        # Per-type icon
        self._draw_icon(screen, cx, cy)

    def _draw_icon(self, screen: pygame.Surface, cx: int, cy: int) -> None:
        c = self.color
        if self.type == "ThermalShield":
            # Shield-ring arc with centre dot
            pygame.draw.circle(screen, c, (cx, cy), 7, 2)
            pygame.draw.circle(screen, c, (cx, cy), 2)

        elif self.type == "FlashStep":
            # Right-pointing chevron / arrow
            pts = [(cx - 4, cy - 5), (cx + 5, cy), (cx - 4, cy + 5)]
            pygame.draw.polygon(screen, c, pts)

        elif self.type == "Supernova":
            # 4-pointed radial burst lines
            for angle in [0.0, math.pi / 2, math.pi, 3 * math.pi / 2]:
                ex = cx + math.cos(angle) * 7
                ey = cy + math.sin(angle) * 7
                pygame.draw.line(screen, c, (cx, cy), (int(ex), int(ey)), 2)
            pygame.draw.circle(screen, c, (cx, cy), 3)

        elif self.type == "ChronoSurge":
            # Concentric rings (freeze symbol)
            pygame.draw.circle(screen, c, (cx, cy), 5)
            pygame.draw.circle(screen, c, (cx, cy), 8, 1)


class Ember:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.radius = 4
        self.pickup_radius = 15
        self.color = (255, 150, 50)
        self.velocity = [random.uniform(-50, 50), random.uniform(-50, 50)]
        self.lifetime = 10.0

    def update(self, dt: float) -> None:
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        # Friction
        self.velocity[0] *= (1.0 - 2.0 * dt)
        self.velocity[1] *= (1.0 - 2.0 * dt)
        self.lifetime -= dt

    def draw(self, screen: pygame.Surface) -> None:
        alpha = int(255 * min(1.0, self.lifetime))
        if alpha <= 0:
            return

        cx, cy = int(self.x), int(self.y)
        pygame.draw.circle(screen, self.color, (cx, cy), self.radius)
