import pygame
import math
import random
from typing import List, Tuple
from utils.math_helpers import get_angle


class Bullet:
    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        is_enemy: bool = False,
        damage: int = 1,
        pierce_count: int = 0,
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.radius: int = 6
        self.speed: int = 500
        self.angle: float = angle
        self.is_enemy: bool = is_enemy
        self.damage: int = damage
        # Pierce charges remaining; bullet passes through an enemy instead of
        # being destroyed as long as pierce_count > 0 (decrements on each hit).
        self.pierce_count: int = pierce_count

    def update(self, dt: float, time_scale: float) -> None:
        # Multiply dt by the global time_scale
        effective_dt = dt * time_scale

        self.x += math.cos(self.angle) * self.speed * effective_dt
        self.y += math.sin(self.angle) * self.speed * effective_dt

    def draw(self, screen: pygame.Surface) -> None:
        color = (255, 50, 50) if self.is_enemy else (255, 255, 0)
        pygame.draw.circle(screen, color,
                           (int(self.x), int(self.y)), self.radius)


class BaseEnemy:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.size: float = 24.0
        self.speed: int = 120
        self.fire_timer: float = 2.5
        self.color: Tuple[int, int, int] = (150, 200, 255)
        self.inner_color: Tuple[int, int, int] = (200, 230, 255)
        self.hp: int = 1
        # Knockback velocity set by Supernova; decays exponentially each frame
        self.knockback_vel: List[float] = [0.0, 0.0]
        
        self.is_imploding: bool = False
        self.implosion_timer: float = 0.15
        self.is_dead: bool = False

    def update(self, dt: float, time_scale: float, target_x: float, target_y: float) -> List[Bullet]:
        """
        Base update method.
        Should be overridden by subclasses.
        Must return a list of Bullet objects (can be empty).
        """
        effective_dt = dt * time_scale
        if self.hp <= 0 and not self.is_imploding:
            self.is_imploding = True
            
        if self.is_imploding:
            self.implosion_timer -= effective_dt
            # Rapidly scale down size
            self.size = max(0.0, self.size - (24.0 / 0.15) * effective_dt)
            if self.implosion_timer <= 0:
                self.is_dead = True

        return []

    def _apply_knockback(self, effective_dt: float) -> None:
        """Apply knockback velocity then decay it so it reaches ~zero in 0.5 s."""
        self.x += self.knockback_vel[0] * effective_dt
        self.y += self.knockback_vel[1] * effective_dt
        # Slower decay keeps Supernova knockback visible over a longer distance.
        decay = max(0.0, 1.0 - 4.0 * effective_dt)
        self.knockback_vel[0] *= decay
        self.knockback_vel[1] *= decay

    def draw(self, screen: pygame.Surface) -> None:
        # Draw a simple square for the Enemy
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(screen, self.color, rect)

        # Draw an inner square for some detail
        inner_rect = pygame.Rect(0, 0, self.size - 8, self.size - 8)
        inner_rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(screen, self.inner_color, inner_rect)


class TrackerCube(BaseEnemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self.speed: int = 120
        self.fire_timer: float = 2.0
        self.color = (50, 100, 255)       # Blue
        self.inner_color = (100, 150, 255)

    def update(self, dt: float, time_scale: float, target_x: float, target_y: float) -> List[Bullet]:
        super().update(dt, time_scale, target_x, target_y)
        if self.is_imploding:
            return []

        angle = get_angle(self.x, self.y, target_x, target_y)
        effective_dt = dt * time_scale

        # Resolve knockback before normal movement
        self._apply_knockback(effective_dt)

        self.x += math.cos(angle) * self.speed * effective_dt
        self.y += math.sin(angle) * self.speed * effective_dt

        self.fire_timer -= effective_dt
        if self.fire_timer <= 0:
            self.fire_timer = 2.0 + random.uniform(-0.2, 0.2)
            return [Bullet(self.x, self.y, angle, is_enemy=True)]

        return []


class ShotgunCube(BaseEnemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self.speed: int = 70  # Slower movement
        self.fire_timer: float = 3.0
        self.color = (255, 140, 0)       # Orange
        self.inner_color = (255, 180, 50)

    def update(self, dt: float, time_scale: float, target_x: float, target_y: float) -> List[Bullet]:
        super().update(dt, time_scale, target_x, target_y)
        if self.is_imploding:
            return []

        angle = get_angle(self.x, self.y, target_x, target_y)
        effective_dt = dt * time_scale

        self._apply_knockback(effective_dt)

        self.x += math.cos(angle) * self.speed * effective_dt
        self.y += math.sin(angle) * self.speed * effective_dt

        self.fire_timer -= effective_dt
        if self.fire_timer <= 0:
            self.fire_timer = 3.0 + random.uniform(-0.5, 0.5)
            spread = math.radians(15)
            return [
                Bullet(self.x, self.y, angle - spread, is_enemy=True),
                Bullet(self.x, self.y, angle, is_enemy=True),
                Bullet(self.x, self.y, angle + spread, is_enemy=True)
            ]

        return []


class NovaCube(BaseEnemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self.speed: int = 100
        self.fire_timer: float = 3.5
        self.color = (150, 50, 255)       # Purple
        self.inner_color = (200, 100, 255)
        self.stopped: bool = False

    def update(self, dt: float, time_scale: float, target_x: float, target_y: float) -> List[Bullet]:
        super().update(dt, time_scale, target_x, target_y)
        if self.is_imploding:
            return []

        effective_dt = dt * time_scale

        self._apply_knockback(effective_dt)

        # Move until reaching the top-third of the screen
        if not self.stopped:
            angle = get_angle(self.x, self.y, target_x, target_y)
            self.x += math.cos(angle) * self.speed * effective_dt
            self.y += math.sin(angle) * self.speed * effective_dt

            # Assuming screen height is roughly 600, top third is y < 200
            # Since enemies spawn off-screen, check if they enter the top third and stop
            if 50 < self.y < 200:
                self.stopped = True

        self.fire_timer -= effective_dt
        if self.fire_timer <= 0:
            self.fire_timer = 3.5 + random.uniform(-0.5, 0.5)
            bullets: List[Bullet] = []
            num_bullets = 8
            angle_step = (2 * math.pi) / num_bullets
            for i in range(num_bullets):
                bullets.append(Bullet(self.x, self.y, i *
                               angle_step, is_enemy=True))
            return bullets

        return []
