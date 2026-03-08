import pygame
import math
from utils.math_helpers import get_angle

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.speed = 300
        self.freeze_meter = 100.0
        self.max_freeze_meter = 100.0
        self.freeze_drain_rate = 25.0  # Drains full meter in 4 seconds
        self.freeze_recovery_rate = 10.0  # Recovers full meter in 10 seconds
        self.is_freezing = False
        self.aim_angle = 0.0

    def update(self, dt, keys, mouse_pos):
        # 1. WASD Movement (unaffected by time_scale)
        dx = 0
        dy = 0
        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1

        if dx != 0 or dy != 0:
            # Normalize vector to prevent faster diagonal movement
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length

        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt

        # 2. Update Chrono-Freeze meter
        if self.is_freezing:
            self.freeze_meter -= self.freeze_drain_rate * dt
            if self.freeze_meter <= 0:
                self.freeze_meter = 0
                self.is_freezing = False
        else:
            self.freeze_meter += self.freeze_recovery_rate * dt
            if self.freeze_meter > self.max_freeze_meter:
                self.freeze_meter = self.max_freeze_meter

        # 3. Update Aiming Angle
        self.aim_angle = get_angle(self.x, self.y, mouse_pos[0], mouse_pos[1])

    def draw(self, screen):
        # Draw Player body (Circle)
        pygame.draw.circle(screen, (0, 255, 100), (int(self.x), int(self.y)), self.radius)
        
        # Draw Aiming Line
        end_x = self.x + math.cos(self.aim_angle) * (self.radius + 15)
        end_y = self.y + math.sin(self.aim_angle) * (self.radius + 15)
        pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y)), (int(end_x), int(end_y)), 3)

        # Draw Freeze Meter UI near player
        bar_width = 40
        bar_height = 6
        bar_x = self.x - bar_width / 2
        bar_y = self.y - self.radius - 12
        fill_width = (self.freeze_meter / self.max_freeze_meter) * bar_width
        
        # Background bar
        pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height))
        # Fill bar (Cyan when freezing, Blue otherwise)
        color = (0, 255, 255) if self.is_freezing else (0, 150, 255)
        pygame.draw.rect(screen, color, (bar_x, bar_y, fill_width, bar_height))
