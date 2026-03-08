import pygame
import math
import random
from utils.math_helpers import get_angle


class IceCube:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 24
        self.speed = 120
        self.fire_timer = 2.5  # Shoots every 2.5 seconds

    def update(self, dt, time_scale, target_x, target_y):
        # 1. Calculate angle to player
        angle = get_angle(self.x, self.y, target_x, target_y)

        # 2. CRITICAL: Multiply dt by time_scale
        effective_dt = dt * time_scale

        # 3. Move towards player
        self.x += math.cos(angle) * self.speed * effective_dt
        self.y += math.sin(angle) * self.speed * effective_dt

        # 4. Handle Firing
        self.fire_timer -= effective_dt
        if self.fire_timer <= 0:
            self.fire_timer = 2.5 + random.uniform(-0.5, 0.5)  # Add slight variance
            # Return a new enemy bullet aimed at the player
            return Bullet(self.x, self.y, angle, is_enemy=True)

        return None

    def draw(self, screen):
        # Draw a simple square for the Ice Cube
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(screen, (150, 200, 255), rect)
        # Draw an inner square for some detail
        inner_rect = pygame.Rect(0, 0, self.size - 8, self.size - 8)
        inner_rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(screen, (200, 230, 255), inner_rect)


class Bullet:
    def __init__(self, x, y, angle, is_enemy=False):
        self.x = x
        self.y = y
        self.radius = 6
        self.speed = 500
        self.angle = angle
        self.is_enemy = is_enemy

    def update(self, dt, time_scale):
        # Note: Depending on design, player bullets might ignore time_scale.
        # However, for consistency with the prompt's instruction:
        # "Both the IceCube's movement and the Bullet's movement MUST multiply their dt by the global time_scale"
        effective_dt = dt * time_scale

        self.x += math.cos(self.angle) * self.speed * effective_dt
        self.y += math.sin(self.angle) * self.speed * effective_dt

    def draw(self, screen):
        color = (255, 50, 50) if self.is_enemy else (255, 255, 0)
        pygame.draw.circle(screen, color,
                           (int(self.x), int(self.y)), self.radius)