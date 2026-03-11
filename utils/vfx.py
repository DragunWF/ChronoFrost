import pygame
import random
from typing import Tuple


class TextPop:
    """
    A floating text label that rises upward and alpha-fades.
    Create at pickup/event position; call update(dt) each frame and check the
    return value — it returns True while alive and False when expired.
    """

    def __init__(
        self,
        text: str,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (255, 255, 255),
        duration: float = 1.5,
    ) -> None:
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.elapsed: float = 0.0
        self.rise_speed: float = 40.0  # pixels per second upward

    def update(self, dt: float) -> bool:
        """Advance animation. Returns True while alive, False when expired."""
        self.elapsed += dt
        self.y -= self.rise_speed * dt
        return self.elapsed < self.duration

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        alpha = max(0, int(255 * (1.0 - self.elapsed / self.duration)))
        surf = font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        screen.blit(surf, (int(self.x - surf.get_width() / 2), int(self.y)))


class Particle:
    """A single velocity-driven dot that fades out. Used for burst effects."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: Tuple[int, int, int],
        radius: int = 3,
        duration: float = 0.6,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.duration = duration
        self.elapsed: float = 0.0

    def update(self, dt: float) -> bool:
        """Returns True while alive."""
        self.elapsed += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Exponential drag
        self.vx *= max(0.0, 1.0 - dt * 3.0)
        self.vy *= max(0.0, 1.0 - dt * 3.0)
        return self.elapsed < self.duration

    def draw(self, screen: pygame.Surface) -> None:
        alpha = max(0, int(255 * (1.0 - self.elapsed / self.duration)))
        r = max(1, int(self.radius * (1.0 - self.elapsed / self.duration * 0.5)))
        surf = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (r, r), r)
        screen.blit(surf, (int(self.x) - r, int(self.y) - r))


class ScreenFlash:
    """
    Full-screen colored overlay that fades to transparent.
    Good for Supernova bursts and other dramatic pickup effects.
    """

    def __init__(self, color: Tuple[int, int, int], duration: float = 0.3) -> None:
        self.color = color
        self.duration = duration
        self.elapsed: float = 0.0

    def update(self, dt: float) -> bool:
        """Returns True while the flash is still visible."""
        self.elapsed += dt
        return self.elapsed < self.duration

    def draw(self, screen: pygame.Surface) -> None:
        progress = min(1.0, self.elapsed / self.duration)
        alpha = max(0, int(180 * (1.0 - progress)))
        surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        surf.fill((*self.color, alpha))
        screen.blit(surf, (0, 0))


def draw_text_pop(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: float,
    y: float,
    color: Tuple[int, int, int] = (255, 255, 255),
) -> None:
    """One-shot helper: renders text centered at (x, y) with no animation."""
    surf = font.render(text, True, color)
    screen.blit(surf, (int(x - surf.get_width() / 2), int(y)))


class VFXManager:
    """Manages global screen-level visual effects like screen shake and overlays."""

    def __init__(self) -> None:
        self.shake_intensity: float = 0.0
        self.shake_decay: float = 45.0  # Pixels per second decay

        # Chrono-Shockwave variables
        self.shockwave_active: bool = False
        self.shockwave_radius: float = 0.0
        self.shockwave_thickness: int = 10
        self.shockwave_speed: float = 1200.0
        self.shockwave_max_radius: float = 800.0
        self.shockwave_center: Tuple[float, float] = (0.0, 0.0)

    def add_shake(self, intensity: float) -> None:
        """Adds to the current screen shake intensity."""
        self.shake_intensity += intensity

    def trigger_shockwave(self, center: Tuple[float, float]) -> None:
        """Triggers a rapidly expanding hollow circle from the given center."""
        self.shockwave_active = True
        self.shockwave_radius = 0.0
        self.shockwave_center = center
        self.shockwave_thickness = 10

    def update(self, dt: float) -> None:
        """Updates the state of screen-level effects."""
        # Update shake decay (damped spring/friction)
        if self.shake_intensity > 0:
            self.shake_intensity -= self.shake_decay * dt
            if self.shake_intensity < 0:
                self.shake_intensity = 0.0

        # Update shockwave
        if self.shockwave_active:
            self.shockwave_radius += self.shockwave_speed * dt
            self.shockwave_thickness = max(1, int(10 * (1.0 - self.shockwave_radius / self.shockwave_max_radius)))
            if self.shockwave_radius >= self.shockwave_max_radius:
                self.shockwave_active = False

    def get_shake_offset(self) -> Tuple[int, int]:
        """Returns a random (x, y) offset based on the current shake intensity."""
        if self.shake_intensity <= 0:
            return (0, 0)
        
        # Random offset within [-intensity, intensity]
        dx = int(random.uniform(-self.shake_intensity, self.shake_intensity))
        dy = int(random.uniform(-self.shake_intensity, self.shake_intensity))
        return (dx, dy)

    def draw_freeze_overlay(self, surface: pygame.Surface, is_frozen: bool, player_center: Tuple[float, float]) -> None:
        """Draws the atmospheric tint and the expanding shockwave."""
        if is_frozen:
            # Semi-transparent dark blue/purple tint
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((20, 10, 50, 100))  # R, G, B, A
            surface.blit(overlay, (0, 0))

        if self.shockwave_active:
            # Draw expanding hollow circle
            pygame.draw.circle(
                surface,
                (0, 255, 255),
                (int(self.shockwave_center[0]), int(self.shockwave_center[1])),
                int(self.shockwave_radius),
                self.shockwave_thickness
            )