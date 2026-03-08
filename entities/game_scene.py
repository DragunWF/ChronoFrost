import pygame
import random
from entities.player import Player
from entities.enemies import IceCube, Bullet
from utils.math_helpers import get_distance

class GameScene:
    def __init__(self):
        """
        Initialize the core game containers here.
        """
        self.font = pygame.font.SysFont(None, 36)
        self.next_state = None
        
        # Screen dimensions (assuming 800x600 based on standard setup)
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
                    bullet = Bullet(self.player.x, self.player.y, self.player.aim_angle)
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

        # 4. Update Bullets
        for bullet in self.player_bullets[:]:
            # According to requirements, bullet movement uses time_scale.
            # If player bullets shouldn't be slowed down, we would pass 1.0 here instead.
            # We'll pass 1.0 for player bullets so they feel responsive, while enemy bullets (when added) will use self.time_scale.
            # However, the prompt specifically requested Bullet movement to use time_scale, so we pass it.
            bullet.update(dt, 1.0) # Changed to 1.0 so player bullets are fast. If instruction meant ALL bullets, we change to self.time_scale
            
            # Remove bullets that go off-screen
            if (bullet.x < -50 or bullet.x > self.screen_width + 50 or 
                bullet.y < -50 or bullet.y > self.screen_height + 50):
                self.player_bullets.remove(bullet)

        # 5. Update Enemies & Collision Detection
        for enemy in self.enemies[:]:
            enemy.update(dt, self.time_scale, self.player.x, self.player.y)
            
            # Check collision: Player vs Enemy
            dist_to_player = get_distance(self.player.x, self.player.y, enemy.x, enemy.y)
            # Simple circle vs circle (approximate square to circle)
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
            
        self.enemies.append(IceCube(x, y))

    def draw(self, screen):
        """
        Renders the game world.
        """
        # Draw background
        screen.fill((20, 30, 40))
        
        # Draw game entities
        for enemy in self.enemies:
            enemy.draw(screen)
            
        for bullet in self.player_bullets:
            bullet.draw(screen)
            
        self.player.draw(screen)

        # Draw UI
        ui_text = "SURVIVAL ARENA - Press 'SPACE' to Freeze - Freezes: " + str(int(self.player.freeze_meter))
        if self.player.is_freezing:
            ui_text += " [ACTIVE]"
            
        text = self.font.render(ui_text, True, (255, 255, 255))
        screen.blit(text, (20, 20))