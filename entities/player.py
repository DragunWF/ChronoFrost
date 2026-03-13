import pygame
import math
from typing import Tuple, Optional
from utils.math_helpers import get_angle
from systems.run_stats import RunStats
from utils.audio_manager import audio_manager
from utils.font_manager import font_manager


class Player:
    def __init__(self, x: float, y: float, run_stats: Optional[RunStats] = None) -> None:
        self.x: float = x
        self.y: float = y
        self.radius: int = 15
        self.speed: int = 300
        self.max_hp: int = 3
        self.hp: int = 3
        self.freeze_meter: float = 100.0
        self.max_freeze_meter: float = 100.0
        self.freeze_drain_rate: float = 25.0  # Drains full meter in 4 seconds
        self.freeze_recovery_rate: float = 10.0  # Recovers full meter in 10 seconds
        self.is_freezing: bool = False
        self.aim_angle: float = 0.0

        # Upgrade state — provided by GameScene; falls back to a default instance
        self.run_stats: RunStats = run_stats if run_stats is not None else RunStats()

        # ThermalShield: absorbs the next 1 damage instance and grants i-frames
        self.shield_active: bool = False

        # FlashStep: each stack = one SHIFT dash available
        self.flash_step_charges: int = 0
        self.is_dashing: bool = False
        self.dash_timer: float = 0.0
        self.dash_vel: Tuple[float, float] = (0.0, 0.0)

        # I-frame timer: while > 0 all incoming damage is ignored
        self.invincible_timer: float = 0.0

        # Set to True by take_damage() when KineticPlating fires; game_scene reads
        # and resets this flag to apply the cooldown cut
        self.kinetic_proc: bool = False

        # Rising-edge detection for SHIFT so one press = one dash (not held)
        self._prev_shift: bool = False

        # --- Sprite Asset Loading ---
        # 8-directional wizard sprites
        self.wizard_sprites = self._load_wizard_sprites()

    def _load_wizard_sprites(self):
        # Loads 8 directional sprites from assets/sprites
        directions = [
            ("N", "topwizard.png"),
            ("NE", "toprightwizard.png"),
            ("E", "rightwizard.png"),
            ("SE", "rightdownwizard.png"),
            ("S", "downwizard.png"),
            ("SW", "downleftwizard.png"),
            ("W", "leftwizard.png"),
            ("NW", "topleftwizard.png")
        ]
        sprites = {}
        for dir_key, filename in directions:
            path = f"assets/sprites/{filename}"
            sprites[dir_key] = pygame.image.load(path).convert_alpha()
        return sprites

    @staticmethod
    def _angle_to_direction(angle: float) -> str:
        # Map angle (degrees) to 8 directions
        # 0 = E, 90 = N, 180 = W, -90 = S
        dirs = ["E", "NE", "N", "NW", "W", "SW", "S", "SE"]
        # Angle: atan2(-dy, dx) (mouse relative to player)
        # Convert to [0, 360)
        a = angle % 360
        # Each sector is 45 degrees
        idx = int(((a + 22.5) % 360) // 45)
        return dirs[idx]

    def take_damage(self, amount: int = 1) -> None:
        # I-frames: ignore all damage while timer is running
        if self.invincible_timer > 0:
            return
        # ThermalShield: absorb the hit, grant 1.5s i-frames instead of taking damage
        if self.shield_active:
            self.shield_active = False
            self.invincible_timer = 1.5
            audio_manager.play_shield_absorb()
            return
        # KineticPlating: count the hit; every 5th hit signals a cooldown cut
        if self.run_stats.kinetic_plating_stacks > 0:
            self.run_stats.kinetic_hits_since_proc += 1
            if self.run_stats.kinetic_hits_since_proc >= 5:
                self.run_stats.kinetic_hits_since_proc = 0
                self.kinetic_proc = True

        audio_manager.play_player_hit()
        self.hp = max(0, self.hp - amount)

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper, mouse_pos: Tuple[int, int]) -> None:
        # Recalculate max freeze capacity (may grow via DeepFreeze boon)
        self.max_freeze_meter = 100.0 + 25.0 * self.run_stats.deep_freeze_stacks

        # Count down i-frames
        self.invincible_timer = max(0.0, self.invincible_timer - dt)

        # --- FlashStep dash (SHIFT, rising-edge) ---
        shift_down = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        if shift_down and not self._prev_shift and self.flash_step_charges > 0 and not self.is_dashing:
            # Direction: WASD input first; fall back to aim angle when idle
            ddx = float(int(keys[pygame.K_d]) - int(keys[pygame.K_a]))
            ddy = float(int(keys[pygame.K_s]) - int(keys[pygame.K_w]))
            if ddx == 0.0 and ddy == 0.0:
                ddx = math.cos(self.aim_angle)
                ddy = math.sin(self.aim_angle)
            else:
                length = math.hypot(ddx, ddy)
                ddx /= length
                ddy /= length
            dash_speed = 600.0
            self.dash_vel = (ddx * dash_speed, ddy * dash_speed)
            self.dash_timer = 0.15
            self.is_dashing = True
            # Grant i-frames for the full dash duration
            self.invincible_timer = max(self.invincible_timer, 0.20)
            self.flash_step_charges -= 1
        self._prev_shift = shift_down

        # --- Movement ---
        if self.is_dashing:
            # During dash: apply dash velocity, ignore WASD
            self.x += self.dash_vel[0] * dt
            self.y += self.dash_vel[1] * dt
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.dash_timer = 0.0
        else:
            # 1. WASD Movement (unaffected by time_scale)
            dx: float = 0.0
            dy: float = 0.0
            if keys[pygame.K_w]:
                dy -= 1.0
            if keys[pygame.K_s]:
                dy += 1.0
            if keys[pygame.K_a]:
                dx -= 1.0
            if keys[pygame.K_d]:
                dx += 1.0

            if dx != 0.0 or dy != 0.0:
                # Normalize vector to prevent faster diagonal movement
                length = math.hypot(dx, dy)
                dx /= length
                dy /= length

            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt

        # 2. Update Chrono-Freeze meter
        # Overclock boon reduces drain rate by 15% per stack (capped at 5 stacks)
        effective_drain = self.freeze_drain_rate * (
            1.0 - 0.15 * min(self.run_stats.overclock_stacks, 5)
        )
        if self.is_freezing:
            self.freeze_meter -= effective_drain * dt
            if self.freeze_meter <= 0.0:
                self.freeze_meter = 0.0
                self.is_freezing = False
        else:
            self.freeze_meter += self.freeze_recovery_rate * dt
            if self.freeze_meter > self.max_freeze_meter:
                self.freeze_meter = self.max_freeze_meter

        # 3. Update Aiming Angle
        self.aim_angle = get_angle(self.x, self.y, float(
            mouse_pos[0]), float(mouse_pos[1]))

    def draw(self, screen: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        # I-frame flicker: skip every other draw call while invincible from dashing
        if self.invincible_timer > 0 and self.is_dashing:
            if int(self.invincible_timer * 12) % 2 == 0:
                return

        # --- Sprite Rendering ---
        # Compute direction based on mouse position
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        angle = math.degrees(math.atan2(-dy, dx))
        direction = self._angle_to_direction(angle)
        sprite = self.wizard_sprites.get(direction)
        if sprite:
            rect = sprite.get_rect(center=(self.x, self.y))
            screen.blit(sprite, rect)
        else:
            # Fallback: draw circle if sprite missing
            pygame.draw.circle(screen, (0, 255, 100),
                               (int(self.x), int(self.y)), self.radius)

        # Freeze Meter UI near player
        bar_width = 40
        bar_height = 6
        bar_x = self.x - bar_width / 2
        bar_y = self.y - self.radius - 12
        fill_width = (self.freeze_meter / self.max_freeze_meter) * bar_width

        pygame.draw.rect(screen, (80, 80, 80),
                         (bar_x, bar_y, bar_width, bar_height))
        color = (0, 255, 255) if self.is_freezing else (0, 150, 255)
        pygame.draw.rect(screen, color, (bar_x, bar_y, fill_width, bar_height))

        # --- HUD: ThermalShield indicator ---
        if self.shield_active:
            pygame.draw.circle(screen, (0, 220, 255), (int(
                self.x), int(self.y)), self.radius + 5, 2)

        # --- HUD: FlashStep charge counter ---
        if self.flash_step_charges > 0:
            cx, cy = int(self.x), int(self.y) + self.radius + 10
            size = 5
            pts = [(cx, cy - size), (cx + size, cy),
                   (cx, cy + size), (cx - size, cy)]
            pygame.draw.polygon(screen, (255, 210, 50), pts)
            if self.flash_step_charges > 1:
                font = font_manager.get_font(20)
                count_surf = font.render(
                    str(self.flash_step_charges), True, (255, 210, 50))
                screen.blit(count_surf, (cx + size + 2, cy -
                            count_surf.get_height() // 2))
