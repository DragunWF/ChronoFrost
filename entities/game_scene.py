import pygame
import random
from entities.player import Player
from entities.enemies import TrackerCube, ShotgunCube, NovaCube, Bullet
from utils.math_helpers import get_distance

class GameScene:
    def __init__(self):
        """
        Initialize the core game containers here.
        """
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        self.next_state = None
        
        # Screen dimensions
        self.screen_width = 800
        self.screen_height = 600

    def enter(self):
        """
        Called when starting a new run or returning from the Boons screen.
        Resets player and world state.
        """
        self.next_state = None
        
        # Instantiate Player in the center of the screen
        self.player = Player(self.screen_width / 2, self.screen_height / 2)
        
        # Lists for enemies and bullets
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        
        # Core mechanics variables
        self.time_scale = 1.0
        self.spawn_timer = 0.0
        self.base_spawn_rate = 1.5  # Spawn an enemy every 1.5 seconds (scaled by time_scale)

    def handle_events(self, events):
        """
        Captures single-press actions.
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Placeholder shortcut to test the State Machine
                if event.key == pygame.K_m:
                    self.next_state = "BOONS"
                # Shortcut to "die" and return to menu
                if event.key == pygame.K_ESCAPE:
                    self.next_state = "MENU"
                
                # Toggle Chrono-Freeze
                if event.key == pygame.K_SPACE:
                    if self.player.freeze_meter > 0:
                        self.player.is_freezing = not self.player.is_freezing
            
            # Left Mouse Button to shoot
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    bullet = Bullet(self.player.x, self.player.y, self.player.aim_angle, is_enemy=False)
                    self.player_bullets.append(bullet)

    def update(self, dt):
        """
        Calculates physics, time_scale math, enemy AI, and collisions.
        """
        if self.next_state is not None:
            return self.next_state

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        # 1. Handle Chrono-Freeze State & time_scale
        if self.player.is_freezing and self.player.freeze_meter > 0:
            self.time_scale = 0.15
        else:
            self.time_scale = 1.0
            self.player.is_freezing = False  # Auto-disable if meter runs out

        # 2. Update Player
        self.player.update(dt, keys, mouse_pos)

        # 3. Enemy Spawning Logic (affected by time_scale)
        self.spawn_timer -= dt * self.time_scale
        if self.spawn_timer <= 0:
            self.spawn_timer = self.base_spawn_rate
            self._spawn_enemy()

        # 4. Update Player Bullets
        for bullet in self.player_bullets[:]:
            bullet.update(dt, 1.0) # Player bullets are typically fast, passing 1.0 for responsiveness
            
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
                
            # Check collision: Enemy Bullet vs Player
            dist_to_player = get_distance(bullet.x, bullet.y, self.player.x, self.player.y)
            if dist_to_player < bullet.radius + self.player.radius:
                return "GAME_OVER"

        # 6. Update Enemies & Collision Detection
        for enemy in self.enemies[:]:
            # Enemies now return a list of bullets
            new_bullets = enemy.update(dt, self.time_scale, self.player.x, self.player.y)
            if new_bullets:
                self.enemy_bullets.extend(new_bullets)
            
            # Check collision: Player vs Enemy
            dist_to_player = get_distance(self.player.x, self.player.y, enemy.x, enemy.y)
            if dist_to_player < self.player.radius + (enemy.size / 2):
                return "GAME_OVER"
                
            # Check collision: Player Bullet vs Enemy
            for bullet in self.player_bullets[:]:
                dist_to_bullet = get_distance(bullet.x, bullet.y, enemy.x, enemy.y)
                if dist_to_bullet < bullet.radius + (enemy.size / 2):
                    if bullet in self.player_bullets:
                        self.player_bullets.remove(bullet)
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                    break  # Break out of bullet loop since enemy is destroyed

        return None

    def _spawn_enemy(self):
        """Helper to spawn an enemy slightly off-screen."""
        side = random.choice(['top', 'bottom', 'left', 'right'])
        margin = 50
        
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

    def draw(self, screen):
        """
        Renders the game world.
        """
        # Draw background
        screen.fill((20, 30, 40))
        
        # Draw game entities
        for enemy in self.enemies:
            enemy.draw(screen)
            
        for bullet in self.enemy_bullets:
            bullet.draw(screen)
            
        for bullet in self.player_bullets:
            bullet.draw(screen)
            
        self.player.draw(screen)

        # Draw UI - Top Left Text
        ui_text = "SURVIVAL ARENA - Press 'SPACE' to Freeze"
        if self.player.is_freezing:
            ui_text += " [ACTIVE]"
        text = self.font.render(ui_text, True, (255, 255, 255))
        screen.blit(text, (20, 20))
        
        # Draw UI - Bottom Left Chrono-Freeze Meter
        meter_x = 20
        meter_y = self.screen_height - 40
        meter_width = 200
        meter_height = 20
        
        # Background dark gray rect
        pygame.draw.rect(screen, (50, 50, 50), (meter_x, meter_y, meter_width, meter_height))
        
        # Foreground colored rect
        fill_width = (self.player.freeze_meter / self.player.max_freeze_meter) * meter_width
        fill_color = (0, 255, 255) if self.player.is_freezing else (0, 150, 255)
        if fill_width > 0:
            pygame.draw.rect(screen, fill_color, (meter_x, meter_y, fill_width, meter_height))
            
        # Text label above the meter
        label_text = self.small_font.render("CHRONO-CHARGE", True, (255, 255, 255))
        screen.blit(label_text, (meter_x, meter_y - 25))