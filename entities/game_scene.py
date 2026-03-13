import pygame
import random
import math
from typing import List, Optional

from entities.player import Player
from entities.enemies import TrackerCube, ShotgunCube, NovaCube, Bullet, BaseEnemy
from entities.items import Powerup, SPAWN_CHANCE, POWERUP_TYPES
from utils.math_helpers import get_distance
from utils.base_scene import BaseScene
from utils.constants import BOONS_STATE, GAME_OVER_STATE, MAIN_MENU_STATE
from utils.vfx import TextPop, ScreenFlash, VFXManager
from systems.run_stats import RunStats
from utils.audio_manager import audio_manager

# Fixed score milestones that trigger the Boons menu.
# After 8000 each subsequent threshold rises by +3000.
_MILESTONES = [1000, 2500, 5000, 8000]


class GameScene(BaseScene):
    def __init__(self) -> None:
        """
        Initialize the core game containers here.
        """
        self.font: pygame.font.Font = pygame.font.SysFont(None, 36)
        self.small_font: pygame.font.Font = pygame.font.SysFont(None, 24)
        self.pop_font: pygame.font.Font = pygame.font.SysFont(None, 26)
        self.next_state: Optional[str] = None

        # Screen dimensions
        self.screen_width: int = 800
        self.screen_height: int = 600

        self.vfx: VFXManager = VFXManager()
        self.render_surface: pygame.Surface = pygame.Surface((self.screen_width, self.screen_height))

        self.player: Player
        self.enemies: List[BaseEnemy] = []
        self.player_bullets: List[Bullet] = []
        self.enemy_bullets: List[Bullet] = []
        self.powerups: List[Powerup] = []
        self.text_pops: List[TextPop] = []
        self.screen_flash: Optional[ScreenFlash] = None

        self.time_scale: float = 1.0
        self.spawn_timer: float = 0.0
        self.base_spawn_rate: float = 1.5

        # Fire rate: base 200ms cooldown, gated per click
        self.base_fire_cooldown: float = 0.2
        self.fire_timer: float = 0.0

        # Scoring
        self.score: int = 0
        self.time_alive: float = 0.0
        self.enemies_shattered: int = 0
        self.powerups_acquired: int = 0
        self.ui_font: pygame.font.Font = pygame.font.SysFont(None, 36)

        # Load background image (ice map)
        self.background_image = pygame.image.load("assets/background/ice-map.png").convert()

        # Upgrade state shared with Player and BoonsMenu
        self.run_stats: RunStats = RunStats()

        # Index into _MILESTONES (or beyond) for the next upgrade trigger
        self.next_milestone_idx: int = 0

    def enter(self) -> None:
        """
        Called when starting a NEW run (not when resuming from the Boons screen).
        Resets player and world state completely.
        """
        self.next_state = None

        # Audio integration: Randomly select between the two available tracks
        audio_manager.play_random_music([
            "assets/audio/audio1.mp3",
            "assets/audio/audio2.mp3"
        ], loop=True)

        # Fresh run stats every new game

        self.run_stats = RunStats()
        self.next_milestone_idx = 0

        # Instantiate Player in the center of the screen, sharing RunStats
        self.player = Player(self.screen_width / 2, self.screen_height / 2, self.run_stats)

        # Reset VFX Manager
        self.vfx = VFXManager()

        # Lists for enemies, bullets, pickups, and VFX
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.text_pops = []
        self.screen_flash = None

        # Core mechanics variables
        self.time_scale = 1.0
        self.spawn_timer = 0.0
        self.base_spawn_rate = 1.5
        self.fire_timer = 0.0

        # Scoring reset
        self.score = 0
        self.time_alive = 0.0
        self.enemies_shattered = 0
        self.powerups_acquired = 0

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        """
        Captures single-press actions.
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Shortcut to "die" and return to menu
                if event.key == pygame.K_ESCAPE:
                    self.next_state = MAIN_MENU_STATE

                # Toggle Chrono-Freeze
                if event.key == pygame.K_SPACE:
                    if getattr(self, 'player', None) and self.player.freeze_meter > 0:
                        was_freezing = self.player.is_freezing
                        self.player.is_freezing = not self.player.is_freezing
                        if not was_freezing and self.player.is_freezing:
                            self.vfx.trigger_shockwave((self.player.x, self.player.y))

            # Left Mouse Button to shoot — gated by fire_timer cooldown
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if getattr(self, 'player', None) and self.fire_timer <= 0:
                        for bullet in self._create_player_bullets():
                            self.player_bullets.append(bullet)
                        self.fire_timer = self._effective_fire_cooldown()

    def update(self, dt: float) -> Optional[str]:
        """
        Calculates physics, time_scale math, enemy AI, and collisions.
        """
        if self.next_state is not None:
            return self.next_state

        if not getattr(self, 'player', None):
            return None

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Count down fire cooldown each frame
        self.fire_timer = max(0.0, self.fire_timer - dt)

        # Update survival time
        self.time_alive += dt
        # Passive score gain
        self.score += 1 * dt

        # --- Milestone check: trigger Boons menu at score thresholds ---
        if self.next_milestone_idx < len(_MILESTONES):
            next_threshold = _MILESTONES[self.next_milestone_idx]
        else:
            # After the fixed list: +3000 per subsequent milestone
            next_threshold = 8000 + 3000 * (self.next_milestone_idx - len(_MILESTONES) + 1)
        if int(self.score) >= next_threshold:
            self.next_milestone_idx += 1
            # Do not persist this transition in self.next_state; otherwise
            # resuming from Boons will immediately re-enter the menu.
            return BOONS_STATE

        # 1. Handle Chrono-Freeze State & time_scale
        if self.player.is_freezing and self.player.freeze_meter > 0:
            self.time_scale = 0.15
        else:
            self.time_scale = 1.0
            self.player.is_freezing = False  # Auto-disable if meter runs out

        # 2. Update Player
        self.player.update(dt, keys, mouse_pos)

        # Handle KineticPlating proc: cut active fire cooldown by 1s
        if self.player.kinetic_proc:
            self.fire_timer = max(0.0, self.fire_timer - 1.0)
            self.player.kinetic_proc = False
            self.text_pops.append(
                TextPop("KINETIC!", self.player.x, self.player.y - 40, (200, 200, 255))
            )

        # 3. Enemy Spawning Logic (affected by time_scale)
        self.spawn_timer -= dt * self.time_scale
        if self.spawn_timer <= 0:
            self.spawn_timer = self.base_spawn_rate
            self._spawn_enemy()

        # 4. Update Player Bullets
        for bullet in self.player_bullets[:]:
            # Player bullets are typically fast, passing 1.0 for responsiveness
            bullet.update(dt, 1.0)

            # Remove bullets that go off-screen
            if (bullet.x < -50 or bullet.x > self.screen_width + 50 or
                    bullet.y < -50 or bullet.y > self.screen_height + 50):
                self.player_bullets.remove(bullet)

        # 5. Update Enemy Bullets
        for bullet in self.enemy_bullets[:]:
            bullet.update(dt, self.time_scale)

            # Remove bullets that go off-screen
            if (bullet.x < -50 or bullet.x > self.screen_width + 50 or
                    bullet.y < -50 or bullet.y > self.screen_height + 50):
                self.enemy_bullets.remove(bullet)
                continue

            # Check collision: Enemy Bullet vs Player
            dist_to_player = get_distance(
                bullet.x, bullet.y, self.player.x, self.player.y)
            if dist_to_player < bullet.radius + self.player.radius:
                self.player.take_damage(1)
                self.vfx.add_shake(15.0)
                self.vfx.spawn_player_leak(self.player.x, self.player.y, (0, 255, 255))
                self.vfx.spawn_bullet_sparks(bullet.x, bullet.y, math.cos(bullet.angle), math.sin(bullet.angle))
                self.enemy_bullets.remove(bullet)
                if self.player.hp <= 0:
                    self.next_state = GAME_OVER_STATE

        # 6. Update Enemies & Collision Detection
        for enemy in self.enemies[:]:
            # Enemies now return a list of bullets
            new_bullets = enemy.update(
                dt, self.time_scale, self.player.x, self.player.y)
            if new_bullets:
                self.enemy_bullets.extend(new_bullets)

            if enemy.is_dead:
                self.vfx.spawn_enemy_shatter(enemy.x, enemy.y, enemy.color)
                self.vfx.spawn_score_popup(enemy.x, enemy.y, 50)
                self.enemies.remove(enemy)
                self.score += 50
                self.enemies_shattered += 1
                # Random chance to drop a Field Drop at the kill position
                if random.random() < SPAWN_CHANCE:
                    self.powerups.append(
                        Powerup(enemy.x, enemy.y, random.choice(POWERUP_TYPES))
                    )
                continue

            # Check collision: Player vs Enemy (body contact)
            dist_to_player = get_distance(
                self.player.x, self.player.y, enemy.x, enemy.y)
            if dist_to_player < self.player.radius + (enemy.size / 2) and not enemy.is_imploding:
                self.player.take_damage(1)
                self.vfx.add_shake(15.0)
                self.vfx.spawn_player_leak(self.player.x, self.player.y, (0, 255, 255))
                enemy.hp = 0  # Trigger implosion
                if self.player.hp <= 0:
                    self.next_state = GAME_OVER_STATE
                continue

            # Check collision: Player Bullet vs Enemy
            if not enemy.is_imploding:
                for p_bullet in self.player_bullets[:]:
                    dist_to_bullet = get_distance(
                        p_bullet.x, p_bullet.y, enemy.x, enemy.y)
                    if dist_to_bullet < p_bullet.radius + (enemy.size / 2):
                        self.vfx.spawn_bullet_sparks(p_bullet.x, p_bullet.y, math.cos(p_bullet.angle), math.sin(p_bullet.angle))
                        # Apply bullet damage to the enemy
                        enemy.hp -= p_bullet.damage
                        # PierceShot: consume one pierce charge rather than destroying bullet
                        if p_bullet.pierce_count > 0:
                            p_bullet.pierce_count -= 1
                        elif p_bullet in self.player_bullets:
                            self.player_bullets.remove(p_bullet)
                        break  # This bullet handled

        # 7. Update and check Powerup pickups
        for pw in self.powerups[:]:
            pw.update(dt)
            dist = get_distance(pw.x, pw.y, self.player.x, self.player.y)
            if dist < self.player.radius + pw.pickup_radius:
                self._apply_powerup(pw)
                self.vfx.spawn_pickup_ring(pw.x, pw.y, (255, 255, 255))
                self.powerups.remove(pw)

        # 8. Advance floating text labels (remove expired ones)
        self.text_pops = [tp for tp in self.text_pops if tp.update(dt)]

        # 9. Advance screen flash
        if self.screen_flash is not None:
            if not self.screen_flash.update(dt):
                self.screen_flash = None
                
        self.vfx.update(dt, self.time_scale)

        return None

    def _spawn_enemy(self) -> None:
        """Helper to spawn an enemy slightly off-screen."""
        side = random.choice(['top', 'bottom', 'left', 'right'])
        margin = 50
        x: float = 0.0
        y: float = 0.0

        if side == 'top':
            x = random.randint(0, self.screen_width)
            y = -margin
        elif side == 'bottom':
            x = random.randint(0, self.screen_width)
            y = self.screen_height + margin
        elif side == 'left':
            x = -margin
            y = random.randint(0, self.screen_height)
        else:
            x = self.screen_width + margin
            y = random.randint(0, self.screen_height)

        enemy_class = random.choices(
            [TrackerCube, ShotgunCube, NovaCube],
            weights=[60, 30, 10],
            k=1
        )[0]

        self.enemies.append(enemy_class(x, y))

    # -----------------------------------------------------------------------
    # Bullet creation helpers
    # -----------------------------------------------------------------------

    def _effective_fire_cooldown(self) -> float:
        """Seconds between shots, factoring in RapidFire and HeavyCaliber boons."""
        mult = self.run_stats.fire_cooldown_mult
        if self.run_stats.heavy_caliber:
            mult *= 1.3  # HeavyCaliber slows fire rate by 30%
        return max(0.08, self.base_fire_cooldown * mult)

    def _create_player_bullets(self) -> List[Bullet]:
        """Return a list of 1 or 3 Bullet objects depending on SpreadShot boon."""
        px, py = self.player.x, self.player.y
        base_angle = self.player.aim_angle
        damage = 2 if self.run_stats.heavy_caliber else 1
        pierce = self.run_stats.pierce_count
        angles = [base_angle]
        if self.run_stats.spread_shot:
            spread = math.radians(15)
            angles = [base_angle - spread, base_angle, base_angle + spread]
        return [
            Bullet(px, py, a, is_enemy=False, damage=damage, pierce_count=pierce)
            for a in angles
        ]

    # -----------------------------------------------------------------------
    # Powerup application
    # -----------------------------------------------------------------------

    def _apply_powerup(self, pw: Powerup) -> None:
        """Apply a picked-up Field Drop's effect and queue a feedback text pop."""
        self.powerups_acquired += 1
        px, py = self.player.x, self.player.y
        if pw.type == "ThermalShield":
            self.player.shield_active = True
            self.text_pops.append(TextPop("SHIELD ACTIVE", px, py - 30, (0, 200, 255)))

        elif pw.type == "FlashStep":
            self.player.flash_step_charges += 1
            self.text_pops.append(TextPop("FLASH STEP!", px, py - 30, (255, 210, 50)))

        elif pw.type == "Supernova":
            # Clear every enemy bullet currently on screen
            self.enemy_bullets.clear()
            # Apply radial knockback: push all enemies away from the player
            for enemy in self.enemies:
                ang = math.atan2(enemy.y - self.player.y, enemy.x - self.player.x)
                enemy.knockback_vel[0] = math.cos(ang) * 1200.0
                enemy.knockback_vel[1] = math.sin(ang) * 1200.0
            self.screen_flash = ScreenFlash((255, 150, 50), 0.35)
            self.text_pops.append(TextPop("SUPERNOVA!", px, py - 30, (255, 130, 30)))

        elif pw.type == "ChronoSurge":
            # Fully restore the Chrono-Freeze meter
            self.player.freeze_meter = self.player.max_freeze_meter
            self.text_pops.append(TextPop("SURGE!", px, py - 30, (100, 255, 200)))

    def draw(self, screen: pygame.Surface) -> None:
        """
        Renders the game world.
        """
        # Draw background image, scaled to fit if needed
        bg = self.background_image
        if bg.get_width() != self.screen_width or bg.get_height() != self.screen_height:
            bg = pygame.transform.smoothscale(bg, (self.screen_width, self.screen_height))
        self.render_surface.blit(bg, (0, 0))

        # Draw game entities
        for enemy in self.enemies:
            enemy.draw(self.render_surface)

        for e_bullet in self.enemy_bullets:
            e_bullet.draw(self.render_surface)

        for p_bullet in self.player_bullets:
            p_bullet.draw(self.render_surface)

        # Draw powerups
        for pw in self.powerups:
            pw.draw(self.render_surface)

        if getattr(self, 'player', None):
            mouse_pos = pygame.mouse.get_pos()
            self.player.draw(self.render_surface, mouse_pos)

            # Draw UI - Top Middle Freeze Text
            freeze_text = "Press 'SPACE' to Freeze Time!"
            if self.player.is_freezing:
                freeze_text += " Time Freeze: [ACTIVE]"
            freeze_surface = self.font.render(
                freeze_text, True, (255, 255, 255))
            freeze_rect = freeze_surface.get_rect(
                center=(self.screen_width / 2, 50))  # Below score text
            self.render_surface.blit(freeze_surface, freeze_rect)

            # Draw UI - Bottom Left Chrono-Freeze Meter
            meter_x = 20
            meter_y = self.screen_height - 40
            meter_width = 200
            meter_height = 20

            # Background dark gray rect
            pygame.draw.rect(self.render_surface, (50, 50, 50),
                             (meter_x, meter_y, meter_width, meter_height))

            # Foreground colored rect
            fill_width = (self.player.freeze_meter /
                          self.player.max_freeze_meter) * meter_width
            fill_color = (0, 255, 255) if self.player.is_freezing else (
                0, 150, 255)
            if fill_width > 0:
                pygame.draw.rect(self.render_surface, fill_color,
                                 (meter_x, meter_y, fill_width, meter_height))

            # Text label above the meter
            label_text = self.small_font.render(
                "CHRONO-CHARGE", True, (255, 255, 255))
            self.render_surface.blit(label_text, (meter_x, meter_y - 25))

            # Draw UI - Bottom Right Health Bar
            hp_meter_width = 200
            hp_meter_height = 20
            hp_meter_x = self.screen_width - hp_meter_width - 20
            hp_meter_y = self.screen_height - 40

            # Background dark gray rect
            pygame.draw.rect(self.render_surface, (50, 50, 50),
                             (hp_meter_x, hp_meter_y, hp_meter_width, hp_meter_height))

            # Foreground green rect
            hp_fill_width = (self.player.hp /
                             self.player.max_hp) * hp_meter_width
            if hp_fill_width > 0:
                pygame.draw.rect(self.render_surface, (0, 255, 0),
                                 (hp_meter_x, hp_meter_y, hp_fill_width, hp_meter_height))

            # Text label above the health bar
            hp_label = self.small_font.render(
                "HULL INTEGRITY", True, (255, 255, 255))
            self.render_surface.blit(hp_label, (hp_meter_x, hp_meter_y - 25))

            # Draw UI - Score
            score_text = self.ui_font.render(
                f"SCORE: {int(self.score)}", True, (255, 255, 255))
            score_rect = score_text.get_rect(
                center=(self.screen_width / 2, 20))
            self.render_surface.blit(score_text, score_rect)

            # Draw floating text labels (pickups, KineticPlating, etc.)
            for tp in self.text_pops:
                tp.draw(self.render_surface, self.pop_font)

            self.vfx.draw_particles(self.render_surface)

            self.vfx.draw_freeze_overlay(self.render_surface, self.player.is_freezing, (self.player.x, self.player.y))

        # Screen flash overlay drawn last so it covers everything
        if self.screen_flash is not None:
            self.screen_flash.draw(self.render_surface)

        screen.fill((0, 0, 0))
        screen.blit(self.render_surface, self.vfx.get_shake_offset())
