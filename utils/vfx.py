import pygame
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
