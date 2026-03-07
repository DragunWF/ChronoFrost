import pygame
import math
import random
import sys

# --- Configuration & Setup ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ChronoFrost - Prototype")
clock = pygame.time.Clock()

# --- Colors ---
C_BG = (10, 15, 25)
C_FROZEN_BG = (15, 30, 50)
C_PLAYER = (100, 200, 255)
C_PLAYER_BULLET = (255, 255, 100)
C_ENEMY = (50, 100, 180)
C_ENEMY_BULLET = (200, 50, 50)
C_EMBER = (255, 150, 50)
C_TEXT = (255, 255, 255)
C_UI_BG = (30, 40, 60)

font_large = pygame.font.SysFont(None, 64)
font_med = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 24)

# --- Game Entities ---


class Player:
    def __init__(self):
        self.x, self.y = WIDTH // 2, HEIGHT // 2
        self.radius = 15
        self.speed = 300.0

        # Combat stats
        self.fire_rate = 0.25  # Seconds between shots
        self.fire_timer = 0.0
        self.bullet_speed = 600.0
        self.pierce = 1  # How many enemies a bullet can hit

        # Chrono stats
        self.freeze_active = False
        self.freeze_meter = 100.0
        self.max_freeze = 100.0
        self.freeze_drain_rate = 20.0

        self.dead = False

    def update(self, dt, keys):
        # Movement (Unaffected by time scale)
        if keys[pygame.K_w]:
            self.y -= self.speed * dt
        if keys[pygame.K_s]:
            self.y += self.speed * dt
        if keys[pygame.K_a]:
            self.x -= self.speed * dt
        if keys[pygame.K_d]:
            self.x += self.speed * dt

        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

        # Timers
        if self.fire_timer > 0:
            self.fire_timer -= dt

        if self.freeze_active:
            self.freeze_meter -= self.freeze_drain_rate * dt
            if self.freeze_meter <= 0:
                self.freeze_meter = 0
                self.freeze_active = False

    def draw(self, surface, mx, my):
        # Draw aim line
        angle = math.atan2(my - self.y, mx - self.x)
        end_x = self.x + math.cos(angle) * 30
        end_y = self.y + math.sin(angle) * 30
        pygame.draw.line(surface, (255, 255, 255),
                         (self.x, self.y), (end_x, end_y), 2)

        # Draw player core
        pygame.draw.circle(surface, C_PLAYER,
                           (int(self.x), int(self.y)), self.radius)
        if self.freeze_active:
            pygame.draw.circle(surface, (150, 255, 255),
                               (int(self.x), int(self.y)), self.radius + 4, 2)


class Bullet:
    def __init__(self, x, y, angle, speed, is_enemy=False, pierce=1):
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = 6 if is_enemy else 4
        self.is_enemy = is_enemy
        self.pierce = pierce
        self.dead = False

    def update(self, dt, time_scale):
        # Player bullets move normal speed, enemy bullets slow down
        active_dt = dt * time_scale if self.is_enemy else dt
        self.x += self.vx * active_dt
        self.y += self.vy * active_dt

        if not (0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT):
            self.dead = True

    def draw(self, surface):
        color = C_ENEMY_BULLET if self.is_enemy else C_PLAYER_BULLET
        pygame.draw.circle(
            surface, color, (int(self.x), int(self.y)), self.radius)


class IceCube:
    def __init__(self):
        # Spawn outside the screen
        spawn_edge = random.choice(['top', 'bottom', 'left', 'right'])
        if spawn_edge == 'top':
            self.x, self.y = random.randint(0, WIDTH), -30
        elif spawn_edge == 'bottom':
            self.x, self.y = random.randint(0, WIDTH), HEIGHT + 30
        elif spawn_edge == 'left':
            self.x, self.y = -30, random.randint(0, HEIGHT)
        else:
            self.x, self.y = WIDTH + 30, random.randint(0, HEIGHT)

        self.size = random.randint(20, 35)
        self.speed = random.uniform(40.0, 90.0)
        self.hp = 2 if self.size > 25 else 1
        self.fire_timer = random.uniform(1.0, 3.0)
        self.dead = False

    def update(self, dt, time_scale, px, py, bullets):
        active_dt = dt * time_scale

        # Move towards player
        angle = math.atan2(py - self.y, px - self.x)
        self.x += math.cos(angle) * self.speed * active_dt
        self.y += math.sin(angle) * self.speed * active_dt

        # Shooting
        self.fire_timer -= active_dt
        if self.fire_timer <= 0:
            self.fire_timer = random.uniform(2.0, 4.0)
            bullets.append(Bullet(self.x, self.y, angle, 200.0, is_enemy=True))

    def draw(self, surface):
        rect = (int(self.x - self.size//2),
                int(self.y - self.size//2), self.size, self.size)
        pygame.draw.rect(surface, C_ENEMY, rect, border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=4)


class Ember:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 6
        self.dead = False

    def draw(self, surface):
        pygame.draw.circle(
            surface, C_EMBER, (int(self.x), int(self.y)), self.radius)


# --- Global State Variables ---
state = "MENU"
player = None
bullets = []
enemies = []
embers = []

score = 0
survival_time = 0.0
next_milestone = 1000

enemy_spawn_timer = 0.0
enemy_spawn_rate = 1.5


def reset_game():
    global player, bullets, enemies, embers, score, survival_time, next_milestone, enemy_spawn_rate
    player = Player()
    bullets.clear()
    enemies.clear()
    embers.clear()
    score = 0
    survival_time = 0.0
    next_milestone = 1000
    enemy_spawn_rate = 1.5


# --- Main Game Loop ---
running = True
while running:
    dt = clock.tick(60) / 1000.0
    mx, my = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if state == "MENU":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                reset_game()
                state = "PLAYING"

        elif state == "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if player.freeze_meter > 10:
                    player.freeze_active = not player.freeze_active

            # Click to shoot
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if player.fire_timer <= 0:
                    player.fire_timer = player.fire_rate
                    angle = math.atan2(my - player.y, mx - player.x)
                    bullets.append(
                        Bullet(player.x, player.y, angle, player.bullet_speed, False, player.pierce))

        elif state == "SHOP":
            # Press 1, 2, or 3 to select an upgrade
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    player.pierce += 1
                    state = "PLAYING"
                elif event.key == pygame.K_2:
                    player.max_freeze += 50
                    player.freeze_meter = player.max_freeze
                    state = "PLAYING"
                elif event.key == pygame.K_3:
                    player.fire_rate = max(0.1, player.fire_rate - 0.05)
                    state = "PLAYING"

        elif state == "GAME_OVER":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                state = "MENU"

    # --- State Logic & Rendering ---
    if state == "MENU":
        screen.fill(C_BG)
        title = font_large.render("CHRONOFROST", True, C_PLAYER)
        prompt = font_med.render("Press ENTER to Start", True, C_TEXT)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2))

    elif state == "PLAYING":
        time_scale = 0.15 if player.freeze_active else 1.0
        keys = pygame.key.get_pressed()

        # 1. Spawning
        survival_time += dt
        enemy_spawn_timer += dt * time_scale
        if enemy_spawn_timer >= enemy_spawn_rate:
            enemies.append(IceCube())
            enemy_spawn_timer = 0.0
            # Gets harder over time
            enemy_spawn_rate = max(0.3, 1.5 - (survival_time * 0.01))

        # 2. Updates
        player.update(dt, keys)

        for b in bullets:
            b.update(dt, time_scale)
        for e in enemies:
            e.update(dt, time_scale, player.x, player.y, bullets)

        # 3. Collisions
        for b in bullets:
            if b.is_enemy:
                if math.hypot(player.x - b.x, player.y - b.y) < player.radius + b.radius:
                    state = "GAME_OVER"
            else:
                for e in enemies:
                    if not e.dead and not b.dead:
                        # Simple rect/circle collision math approximation
                        if abs(b.x - e.x) < e.size//2 + b.radius and abs(b.y - e.y) < e.size//2 + b.radius:
                            e.hp -= 1
                            b.pierce -= 1
                            if b.pierce <= 0:
                                b.dead = True
                            if e.hp <= 0:
                                e.dead = True
                                score += 50
                                if random.random() < 0.4:
                                    embers.append(Ember(e.x, e.y))

        for e in enemies:
            if abs(player.x - e.x) < e.size//2 + player.radius and abs(player.y - e.y) < e.size//2 + player.radius:
                state = "GAME_OVER"

        for em in embers:
            if math.hypot(player.x - em.x, player.y - em.y) < player.radius + em.radius + 20:  # Pickup radius
                em.dead = True
                score += 10
                player.freeze_meter = min(
                    player.max_freeze, player.freeze_meter + 15)

        # 4. Cleanup
        bullets = [b for b in bullets if not b.dead]
        enemies = [e for e in enemies if not e.dead]
        embers = [em for em in embers if not em.dead]

        # 5. Check Shop Milestone
        if score >= next_milestone:
            next_milestone += 1000
            state = "SHOP"

        # 6. Drawing
        screen.fill(C_FROZEN_BG if player.freeze_active else C_BG)

        for em in embers:
            em.draw(screen)
        for e in enemies:
            e.draw(screen)
        for b in bullets:
            b.draw(screen)
        player.draw(screen, mx, my)

        # UI
        score_txt = font_med.render(f"Score: {score}", True, C_TEXT)
        screen.blit(score_txt, (10, 10))

        pygame.draw.rect(screen, (50, 50, 50), (10, HEIGHT - 30, 200, 20))
        if player.freeze_meter > 0:
            ratio = player.freeze_meter / player.max_freeze
            pygame.draw.rect(screen, (100, 255, 255),
                             (10, HEIGHT - 30, 200 * ratio, 20))
        pygame.draw.rect(screen, C_TEXT, (10, HEIGHT - 30, 200, 20), 2)

    elif state == "SHOP":
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        title = font_large.render("MILESTONE REACHED", True, (255, 215, 0))
        opt1 = font_med.render("[1] +1 Bullet Pierce", True, C_TEXT)
        opt2 = font_med.render("[2] +50 Max Chrono Capacity", True, C_TEXT)
        opt3 = font_med.render("[3] Faster Fire Rate", True, C_TEXT)

        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        screen.blit(opt1, (WIDTH//2 - opt1.get_width()//2, 250))
        screen.blit(opt2, (WIDTH//2 - opt2.get_width()//2, 320))
        screen.blit(opt3, (WIDTH//2 - opt3.get_width()//2, 390))

    elif state == "GAME_OVER":
        screen.fill(C_BG)
        go_txt = font_large.render("FROZEN FOREVER", True, (255, 50, 50))
        score_txt = font_med.render(f"Final Score: {score}", True, C_TEXT)
        prompt = font_small.render("Press R to return to Menu", True, C_TEXT)

        screen.blit(go_txt, (WIDTH//2 - go_txt.get_width()//2, HEIGHT//3))
        screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, HEIGHT//2))
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 + 50))

    pygame.display.flip()

pygame.quit()
sys.exit()
