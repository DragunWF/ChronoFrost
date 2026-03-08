import pygame
import math
import random
from utils.math_helpers import get_angle

class BaseEnemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 24
        self.speed = 120
        self.fire_timer = 2.5
        self.color = (150, 200, 255)
        self.inner_color = (200, 230, 255)

    def update(self, dt, time_scale, target_x, target_y):
        """
        Base update method.
        Should be overridden by subclasses.
        Must return a list of Bullet objects (can be empty).
        """
        return []

    def draw(self, screen):
        # Draw a simple square for the Enemy
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(screen, self.color, rect)
        
        # Draw an inner square for some detail
        inner_rect = pygame.Rect(0, 0, self.size - 8, self.size - 8)
        inner_rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(screen, self.inner_color, inner_rect)


class TrackerCube(BaseEnemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 120
        self.fire_timer = 2.0
        self.color = (50, 100, 255)       # Blue
        self.inner_color = (100, 150, 255)

    def update(self, dt, time_scale, target_x, target_y):
        angle = get_angle(self.x, self.y, target_x, target_y)
        effective_dt = dt * time_scale

        self.x += math.cos(angle) * self.speed * effective_dt
        self.y += math.sin(angle) * self.speed * effective_dt

        self.fire_timer -= effective_dt
        if self.fire_timer <= 0:
            self.fire_timer = 2.0 + random.uniform(-0.2, 0.2)
            return [Bullet(self.x, self.y, angle, is_enemy=True)]
        
        return []


class ShotgunCube(BaseEnemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 70  # Slower movement
        self.fire_timer = 3.0
        self.color = (255, 140, 0)       # Orange
        self.inner_color = (255, 180, 50)

    def update(self, dt, time_scale, target_x, target_y):
        angle = get_angle(self.x, self.y, target_x, target_y)
        effective_dt = dt * time_scale

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
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 100
        self.fire_timer = 3.5
        self.color = (150, 50, 255)       # Purple
        self.inner_color = (200, 100, 255)
        self.stopped = False

    def update(self, dt, time_scale, target_x, target_y):
        effective_dt = dt * time_scale

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
            bullets = []
            num_bullets = 8
            angle_step = (2 * math.pi) / num_bullets
            for i in range(num_bullets):
                bullets.append(Bullet(self.x, self.y, i * angle_step, is_enemy=True))
            return bullets
            
        return []


class Bullet:
    def __init__(self, x, y, angle, is_enemy=False):
        self.x = x
        self.y = y
        self.radius = 6
        self.speed = 500
        self.angle = angle
        self.is_enemy = is_enemy

    def update(self, dt, time_scale):
        # Multiply dt by the global time_scale
        effective_dt = dt * time_scale

        self.x += math.cos(self.angle) * self.speed * effective_dt
        self.y += math.sin(self.angle) * self.speed * effective_dt

    def draw(self, screen):
        color = (255, 50, 50) if self.is_enemy else (255, 255, 0)
        pygame.draw.circle(screen, color,
                           (int(self.x), int(self.y)), self.radius)
