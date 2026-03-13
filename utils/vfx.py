import pygame
import random
import math
from typing import Tuple, List, Optional
from dataclasses import dataclass

from utils.font_manager import font_manager


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
    p_type: str = 'solid'
    angle: float = 0.0
    angular_velocity: float = 0.0

@dataclass
class FloatingText:
    """A simple floating text dataclass for object pooling."""
    x: float = 0.0
    y: float = 0.0
    text: str = ""
    lifetime: float = 0.0
    max_lifetime: float = 1.0
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
        self.floating_texts: List[FloatingText] = [FloatingText() for _ in range(20)]
        
        self.score_font = font_manager.get_font(24)

    def _get_free_particle(self) -> Optional[Particle]:
        """Returns the first inactive particle in the pool."""
        for p in self.particles:
            if not p.active:
                return p
        return None

    def _get_free_floating_text(self) -> Optional[FloatingText]:
        """Returns the first inactive floating text in the pool."""
        for ft in self.floating_texts:
            if not ft.active:
                return ft
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
                p.p_type = 'solid'
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
                p.p_type = 'solid'
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

    def spawn_pickup_ring(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        """Spawns a particle that renders as a rapidly expanding hollow circle."""
        p = self._get_free_particle()
        if p:
            p.active = True
            p.p_type = 'ring'
            p.x = x
            p.y = y
            p.vx = 0.0
            p.vy = 0.0
            p.max_lifetime = 0.4
            p.lifetime = p.max_lifetime
            p.color = color
            p.size = 50.0  # Max radius

    def spawn_player_leak(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        """Spawns 3-5 slow-moving, spinning hollow squares that drift away from the player."""
        num_particles = random.randint(3, 5)
        for _ in range(num_particles):
            p = self._get_free_particle()
            if p:
                p.active = True
                p.p_type = 'hollow_square'
                p.x = x
                p.y = y
                
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(20.0, 60.0)
                
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed
                p.angle = random.uniform(0, 2 * math.pi)
                p.angular_velocity = random.uniform(-5.0, 5.0)
                
                p.max_lifetime = random.uniform(0.5, 1.0)
                p.lifetime = p.max_lifetime
                p.color = color
                p.size = random.uniform(6.0, 10.0)

    def spawn_score_popup(self, x: float, y: float, score_amount: int) -> None:
        """Activates a FloatingText object that slowly drifts upward."""
        ft = self._get_free_floating_text()
        if ft:
            ft.active = True
            ft.x = x
            ft.y = y
            ft.text = f"+{score_amount}"
            ft.max_lifetime = 1.0
            ft.lifetime = ft.max_lifetime

    def update(self, dt: float, time_scale: float = 1.0) -> None:
        """Updates the state of screen-level effects, particles, and floating text."""
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
                    if p.p_type == 'hollow_square':
                        p.angle += p.angular_velocity * dt * time_scale
                    else:
                        # High friction for sparks and shatter
                        p.vx *= max(0.0, 1.0 - (dt * time_scale * 5.0))
                        p.vy *= max(0.0, 1.0 - (dt * time_scale * 5.0))

        # Update floating texts
        for ft in self.floating_texts:
            if ft.active:
                ft.lifetime -= dt * time_scale
                if ft.lifetime <= 0:
                    ft.active = False
                else:
                    ft.y -= 30.0 * dt * time_scale  # Drift upward

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
        """Renders active particles and floating texts."""
        for p in self.particles:
            if p.active:
                ratio = max(0.0, p.lifetime / p.max_lifetime)
                alpha = int(255 * ratio)
                
                if alpha > 0:
                    if p.p_type == 'ring':
                        # Ring expands over time
                        radius = max(1.0, p.size * (1.0 - ratio))
                        thickness = max(1, int(3 * ratio))
                        temp_surf = pygame.Surface((int(radius) * 2 + 2, int(radius) * 2 + 2), pygame.SRCALPHA)
                        pygame.draw.circle(temp_surf, (*p.color, alpha), (int(radius) + 1, int(radius) + 1), int(radius), thickness)
                        surface.blit(temp_surf, (int(p.x - radius - 1), int(p.y - radius - 1)), special_flags=pygame.BLEND_RGBA_ADD)
                    elif p.p_type == 'hollow_square':
                        current_size = max(1.0, p.size)
                        temp_surf = pygame.Surface((int(current_size) * 2, int(current_size) * 2), pygame.SRCALPHA)
                        
                        # Calculate rotated square corners
                        half_size = current_size / 2.0
                        corners = [
                            (-half_size, -half_size),
                            (half_size, -half_size),
                            (half_size, half_size),
                            (-half_size, half_size)
                        ]
                        
                        rotated_corners = []
                        cos_a = math.cos(p.angle)
                        sin_a = math.sin(p.angle)
                        for cx, cy in corners:
                            rx = cx * cos_a - cy * sin_a + current_size
                            ry = cx * sin_a + cy * cos_a + current_size
                            rotated_corners.append((rx, ry))
                            
                        pygame.draw.polygon(temp_surf, (*p.color, alpha), rotated_corners, 2)
                        surface.blit(temp_surf, (int(p.x - current_size), int(p.y - current_size)), special_flags=pygame.BLEND_RGBA_ADD)
                    else: # solid
                        current_size = max(1.0, p.size * ratio)
                        r = int(current_size)
                        temp_surf = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
                        pygame.draw.circle(temp_surf, (*p.color, alpha), (r, r), r)
                        surface.blit(temp_surf, (int(p.x - r), int(p.y - r)), special_flags=pygame.BLEND_RGBA_ADD)

        # Draw floating texts
        for ft in self.floating_texts:
            if ft.active:
                ratio = max(0.0, ft.lifetime / ft.max_lifetime)
                alpha = int(255 * ratio)
                if alpha > 0:
                    text_surf = self.score_font.render(ft.text, True, (255, 255, 255))
                    text_surf.set_alpha(alpha)
                    surface.blit(text_surf, (int(ft.x - text_surf.get_width() / 2), int(ft.y - text_surf.get_height() / 2)))