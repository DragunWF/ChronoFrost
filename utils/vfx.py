import pygame
import random
import math
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class Particle:
    """A simple particle dataclass for object pooling."""
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    lifetime: float = 0.0
    max_lifetime: float = 1.0
    color: Tuple[int, int, int] = (255, 255, 255)
    size: float = 3.0
    active: bool = False


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

        # Object Pool for particles
        self.particles: List[Particle] = [Particle() for _ in range(200)]

    def _get_free_particle(self) -> Optional[Particle]:
        """Returns the first inactive particle in the pool."""
        for p in self.particles:
            if not p.active:
                return p
        return None

    def add_shake(self, intensity: float) -> None:
        """Adds to the current screen shake intensity."""
        self.shake_intensity += intensity

    def trigger_shockwave(self, center: Tuple[float, float]) -> None:
        """Triggers a rapidly expanding hollow circle from the given center."""
        self.shockwave_active = True
        self.shockwave_radius = 0.0
        self.shockwave_center = center
        self.shockwave_thickness = 10

    def spawn_bullet_sparks(self, x: float, y: float, impact_dir_x: float, impact_dir_y: float) -> None:
        """Activates 3-5 tiny line/circle particles flying opposite to impact direction."""
        num_sparks = random.randint(3, 5)
        for _ in range(num_sparks):
            p = self._get_free_particle()
            if p:
                p.active = True
                p.x = x
                p.y = y
                
                # Sparks fly opposite to impact direction, plus some spread
                base_angle = math.atan2(-impact_dir_y, -impact_dir_x)
                spread = math.radians(45)
                angle = base_angle + random.uniform(-spread, spread)
                
                speed = random.uniform(150.0, 400.0)
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed
                
                p.max_lifetime = random.uniform(0.15, 0.3)
                p.lifetime = p.max_lifetime
                p.color = (255, 200, 50)  # Orange/yellow spark
                p.size = random.uniform(1.0, 2.5)

    def spawn_enemy_shatter(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        """Activates 10-15 square/polygon particles bursting outward in 360 degrees."""
        num_particles = random.randint(10, 15)
        for _ in range(num_particles):
            p = self._get_free_particle()
            if p:
                p.active = True
                p.x = x
                p.y = y
                
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(50.0, 250.0)
                
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed
                
                p.max_lifetime = random.uniform(0.3, 0.6)
                p.lifetime = p.max_lifetime
                p.color = color
                p.size = random.uniform(3.0, 6.0)

    def update(self, dt: float, time_scale: float = 1.0) -> None:
        """Updates the state of screen-level effects and particles."""
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

        # Update particles
        for p in self.particles:
            if p.active:
                p.lifetime -= dt * time_scale
                if p.lifetime <= 0:
                    p.active = False
                else:
                    p.x += p.vx * dt * time_scale
                    p.y += p.vy * dt * time_scale
                    # High friction
                    p.vx *= max(0.0, 1.0 - (dt * time_scale * 5.0))
                    p.vy *= max(0.0, 1.0 - (dt * time_scale * 5.0))

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

    def draw_particles(self, surface: pygame.Surface) -> None:
        """Renders active particles."""
        for p in self.particles:
            if p.active:
                ratio = max(0.0, p.lifetime / p.max_lifetime)
                current_size = max(1.0, p.size * ratio)
                alpha = int(255 * ratio)
                
                if alpha > 0:
                    r = int(current_size)
                    temp_surf = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
                    pygame.draw.circle(temp_surf, (*p.color, alpha), (r, r), r)
                    surface.blit(temp_surf, (int(p.x - r), int(p.y - r)), special_flags=pygame.BLEND_RGBA_ADD)
