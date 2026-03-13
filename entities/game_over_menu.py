"""
Game Over scene — shatter transition, typewriter header, run stats, and
persistent high-score integration via systems.save_data.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

from systems import save_data
from utils.audio_manager import audio_manager
from utils.base_scene import BaseScene
from utils.constants import MAIN_MENU_STATE, PLAY_STATE

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_BG_FILL = (5, 8, 14)
_TITLE_CLR = (220, 55, 55)
_DIM_TEXT = (100, 120, 140)
_STAT_KEY = (120, 148, 172)
_STAT_VAL = (220, 235, 255)
_BTN_IDLE = (80, 95, 115)
_BTN_HOV = (235, 248, 255)
_BDR_IDLE = (38, 78, 138)
_BDR_HOV = (80, 190, 255)
_GOLD = (255, 210, 50)


# ---------------------------------------------------------------------------
# Internal particle dataclasses
# ---------------------------------------------------------------------------

@dataclass
class _Shard:
    """A coloured shard that flies out from the player's death position."""
    x:            float
    y:            float
    vx:           float
    vy:           float
    angle:        float   # degrees
    spin:         float   # degrees / second
    size:         float
    color:        Tuple[int, int, int]
    alpha:        float   # 0–255
    lifetime:     float
    max_lifetime: float


@dataclass
class _Ash:
    """Tiny dim rectangle that drifts downward — atmospheric dead-ember effect."""
    x:     float
    y:     float
    vx:    float
    vy:    float
    w:     int
    h:     int
    alpha: int


@dataclass
class _Fountain:
    """Celebratory particle launched upward for new-record moments."""
    x:            float
    y:            float
    vx:           float
    vy:           float
    color:        Tuple[int, int, int]
    lifetime:     float
    max_lifetime: float
    size:         float


# ---------------------------------------------------------------------------
# Button (mirrors main_menu._Button)
# ---------------------------------------------------------------------------

class _Button:
    def __init__(self, label: str, rect: pygame.Rect) -> None:
        self.label = label
        self.rect = rect

    def hovered(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def draw(
        self, screen: pygame.Surface, font: pygame.font.Font, is_hov: bool
    ) -> None:
        border = _BDR_HOV if is_hov else _BDR_IDLE
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=4)
        text = f"> {self.label} <" if is_hov else self.label
        color = _BTN_HOV if is_hov else _BTN_IDLE
        surf = font.render(text, True, color)
        screen.blit(
            surf,
            (self.rect.centerx - surf.get_width() // 2,
             self.rect.centery - surf.get_height() // 2),
        )


# ---------------------------------------------------------------------------
# GameOverMenu
# ---------------------------------------------------------------------------

class GameOverMenu(BaseScene):
    """
    Full-featured Game Over scene.

    The normal entry-point is ``enter_with_stats(...)`` (called from main.py on
    the PLAY → GAME_OVER transition).  The plain ``enter()`` method provides a
    safe fallback that goes directly to the UI phase without saving any stats.
    """

    _ASH_COUNT = 28
    _SHARD_COUNT = 14
    _SHATTER_DUR = 1.6    # seconds of shard animation before typewriter
    _CHAR_DELAY = 0.08   # seconds per typewriter character
    _HEADER = "GAME OVER"

    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont(None, 92)
        self.font_sub = pygame.font.SysFont(None, 34)
        self.font_stat = pygame.font.SysFont(None, 30)
        self.font_btn = pygame.font.SysFont(None, 34)
        self.font_record = pygame.font.SysFont(None, 42)

        self.next_state: Optional[str] = None

        # Run data (populated by enter_with_stats)
        self._score:      int = 0
        self._time_alive: float = 0.0
        self._enemies:    int = 0
        self._boons:      int = 0

        self._is_new_record: bool = False
        self._record_rank:   int = 0

        # Darkened snapshot of the last gameplay frame
        self._bg: Optional[pygame.Surface] = None

        # Particle lists
        self._shards:   List[_Shard] = []
        self._ash:      List[_Ash] = []
        self._fountain: List[_Fountain] = []

        # Phase state machine: "shatter" → "typewriter" → "ui"
        self._phase:       str = "ui"
        self._phase_timer: float = 0.0

        # Typewriter
        self._tw_revealed: int = 0

        # Celebration pulse timer
        self._pulse_t: float = 0.0

        # Layout (built lazily)
        self._buttons:      List[_Button] = []
        self._sw: int = 800
        self._sh: int = 600
        self._layout_built: bool = False

    # -----------------------------------------------------------------------
    # BaseScene interface
    # -----------------------------------------------------------------------

    def enter(self) -> None:
        """
        Fallback reset — skips stats persistence and goes straight to UI.
        Normally ``enter_with_stats()`` is used instead.
        """
        self.next_state = None
        self._score = 0
        self._time_alive = 0.0
        self._enemies = 0
        self._boons = 0
        self._is_new_record = False
        self._record_rank = 0
        self._bg = None
        self._shards = []
        self._fountain = []
        self._pulse_t = 0.0
        self._phase = "ui"
        self._phase_timer = 0.0
        self._tw_revealed = len(self._HEADER)

        surf = pygame.display.get_surface()
        sw, sh = surf.get_size() if surf else (800, 600)
        self._ash = self._make_ash(sw, sh, spread=True)
        self._build_layout(sw, sh)

    def enter_with_stats(
        self,
        score:             int,
        time_alive:        float,
        enemies_shattered: int,
        boons_acquired:    int,
        player_x:          float = 400.0,
        player_y:          float = 300.0,
        snapshot:          Optional[pygame.Surface] = None,
    ) -> None:
        """
        Called by main.py on the PLAY → GAME_OVER transition.
        Persists run data, then starts the shatter animation.
        """
        self.next_state = None

        # Persist immediately — one write per run
        self._is_new_record, self._record_rank = save_data.record_run(
            score, time_alive, enemies_shattered, boons_acquired
        )

        self._score = score
        self._time_alive = time_alive
        self._enemies = enemies_shattered
        self._boons = boons_acquired

        # Build darkened background from the captured game frame
        if snapshot is not None:
            self._bg = snapshot.copy()
            overlay = pygame.Surface(self._bg.get_size())
            overlay.set_alpha(190)
            overlay.fill((5, 8, 18))
            self._bg.blit(overlay, (0, 0))
        else:
            self._bg = None

        surf = pygame.display.get_surface()
        sw, sh = surf.get_size() if surf else (800, 600)

        self._shards = self._make_shards(player_x, player_y)
        self._ash = self._make_ash(sw, sh, spread=True)
        self._fountain = []   # created lazily when "ui" phase begins

        self._phase = "shatter"
        self._phase_timer = 0.0
        self._tw_revealed = 0
        self._pulse_t = 0.0

        self._build_layout(sw, sh)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        if self._phase != "ui":
            # Any input skips the animation
            for event in events:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    self._skip_to_ui()
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self._buttons):
                    if btn.hovered(event.pos):
                        audio_manager.play_ui_select()
                        self.next_state = PLAY_STATE if i == 0 else MAIN_MENU_STATE
                        return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.next_state = PLAY_STATE
                elif event.key in (pygame.K_ESCAPE, pygame.K_m):
                    self.next_state = MAIN_MENU_STATE

    def update(self, dt: float) -> Optional[str]:
        self._phase_timer += dt

        if self._phase == "shatter":
            self._update_shards(dt)
            self._update_ash(dt)
            if self._phase_timer >= self._SHATTER_DUR:
                self._phase = "typewriter"
                self._phase_timer = 0.0

        elif self._phase == "typewriter":
            self._update_ash(dt)
            self._tw_revealed = min(
                int(self._phase_timer / self._CHAR_DELAY),
                len(self._HEADER),
            )
            full_reveal_time = len(self._HEADER) * self._CHAR_DELAY + 0.6
            if self._phase_timer >= full_reveal_time:
                self._enter_ui_phase()

        elif self._phase == "ui":
            self._update_ash(dt)
            self._update_fountain(dt)
            self._pulse_t += dt

        return self.next_state

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        if not self._layout_built or sw != self._sw or sh != self._sh:
            self._build_layout(sw, sh)

        # Darkened last-frame background or solid fill
        if self._bg is not None:
            screen.blit(self._bg, (0, 0))
        else:
            screen.fill(_BG_FILL)

        # Ash is drawn in every phase
        self._draw_ash(screen)

        if self._phase == "shatter":
            self._draw_shards(screen)
        elif self._phase == "typewriter":
            self._draw_typewriter(screen, sw, sh)
        elif self._phase == "ui":
            self._draw_ui(screen, sw, sh)

    # -----------------------------------------------------------------------
    # Phase transitions
    # -----------------------------------------------------------------------

    def _enter_ui_phase(self) -> None:
        self._phase = "ui"
        self._phase_timer = 0.0
        self._tw_revealed = len(self._HEADER)
        # Spawn the celebration fountain now (not during shatter so it stays alive)
        if self._is_new_record:
            surf = pygame.display.get_surface()
            sw, sh = surf.get_size() if surf else (800, 600)
            self._fountain = self._make_fountain(sw, sh)

    def _skip_to_ui(self) -> None:
        self._shards.clear()
        self._enter_ui_phase()

    # -----------------------------------------------------------------------
    # Update helpers
    # -----------------------------------------------------------------------

    def _update_shards(self, dt: float) -> None:
        for s in self._shards:
            s.lifetime -= dt
            if s.lifetime <= 0:
                continue
            frac = max(0.0, s.lifetime / s.max_lifetime)
            s.alpha = 255.0 * frac
            s.x += s.vx * dt
            s.y += s.vy * dt
            s.vy += 120.0 * dt          # gentle gravity
            s.vx *= max(0.0, 1.0 - dt * 1.2)
            s.vy *= max(0.0, 1.0 - dt * 0.9)
            s.angle += s.spin * dt

    def _update_ash(self, dt: float) -> None:
        for a in self._ash:
            a.y += a.vy * dt
            a.x += a.vx * dt
            if a.y > self._sh + 10:
                a.y = -random.randint(0, 20)
                a.x = random.uniform(0, self._sw)

    def _update_fountain(self, dt: float) -> None:
        for f in self._fountain:
            f.lifetime -= dt
            if f.lifetime <= 0:
                continue
            f.x += f.vx * dt
            f.y += f.vy * dt
            f.vy += 220.0 * dt   # gravity pulls them back down

    # -----------------------------------------------------------------------
    # Draw helpers
    # -----------------------------------------------------------------------

    def _draw_shards(self, screen: pygame.Surface) -> None:
        for s in self._shards:
            if s.lifetime <= 0:
                continue
            alpha = max(0, int(s.alpha))
            sz = max(2, int(s.size))
            dim = sz * 4 + 2
            tmp = pygame.Surface((dim, dim), pygame.SRCALPHA)
            cx = cy = dim // 2
            rad = math.radians(s.angle)
            c, si = math.cos(rad), math.sin(rad)
            # Diamond shard
            pts_local = [(0, -sz), (sz // 2, 0), (0, sz // 2), (-sz // 2, 0)]
            pts = [
                (int(cx + px * c - py * si), int(cy + px * si + py * c))
                for px, py in pts_local
            ]
            pygame.draw.polygon(tmp, (*s.color, alpha), pts)
            screen.blit(tmp, (int(s.x) - cx, int(s.y) - cy))

    def _draw_ash(self, screen: pygame.Surface) -> None:
        for a in self._ash:
            tmp = pygame.Surface((a.w, a.h), pygame.SRCALPHA)
            tmp.fill((90, 90, 100, a.alpha))
            screen.blit(tmp, (int(a.x), int(a.y)))

    def _draw_typewriter(self, screen: pygame.Surface, sw: int, sh: int) -> None:
        visible = self._HEADER[:self._tw_revealed]
        surf = self.font_title.render(visible, True, _TITLE_CLR)

        # Blinking cursor
        if int(self._phase_timer * 4) % 2 == 0:
            cur = self.font_title.render("_", True, _TITLE_CLR)
            comb = pygame.Surface(
                (surf.get_width() + cur.get_width(), surf.get_height()),
                pygame.SRCALPHA,
            )
            comb.blit(surf, (0, 0))
            comb.blit(cur, (surf.get_width(), 0))
            surf = comb

        screen.blit(surf, (sw // 2 - surf.get_width() // 2, sh // 4 - 30))

    def _draw_ui(self, screen: pygame.Surface, sw: int, sh: int) -> None:
        cx = sw // 2

        # Fountain behind title
        if self._is_new_record:
            self._draw_fountain(screen)

        # --- Title (pulses gold when new record) ---
        if self._is_new_record:
            p = 0.5 + 0.5 * math.sin(self._pulse_t * 5.0)
            clr = (int(200 + 55 * p), int(140 + 70 * p), int(30 + 30 * p))
        else:
            clr = _TITLE_CLR

        title_surf = self.font_title.render(self._HEADER, True, clr)
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, sh // 6))

        # --- New Record badge ---
        if self._is_new_record:
            bp = 0.5 + 0.5 * math.sin(self._pulse_t * 6.0 + 1.0)
            bclr = (int(255 * bp), int(200 * bp), int(50 * bp))
            badge = self.font_record.render(
                f"** NEW RECORD  --  RANK #{self._record_rank} **",
                True, bclr,
            )
            screen.blit(badge, (cx - badge.get_width() // 2, sh // 6 + 88))

        # --- Stats panel ---
        mins = int(self._time_alive // 60)
        secs = int(self._time_alive % 60)
        rows = [
            ("FINAL SCORE",       f"{self._score:,}"),
            ("TIME SURVIVED",     f"{mins:02d}:{secs:02d}"),
            ("ENEMIES SHATTERED", str(self._enemies)),
            ("UPGRADES ACQUIRED", str(self._boons)),
        ]
        panel_top = sh // 2 - 60
        row_height = 34
        panel_left = cx - 200  # left edge of key column
        # right edge of value column (values right-aligned here)
        panel_right = cx + 200

        # Thin divider above stats
        pygame.draw.line(
            screen, (50, 70, 110),
            (panel_left, panel_top - 14),
            (panel_right, panel_top - 14), 1,
        )
        for i, (key, val) in enumerate(rows):
            y = panel_top + i * row_height
            k_surf = self.font_stat.render(key, True, _STAT_KEY)
            v_surf = self.font_stat.render(val, True, _STAT_VAL)
            screen.blit(k_surf, (panel_left, y))
            # Right-align the value against the panel's right edge
            screen.blit(v_surf, (panel_right - v_surf.get_width(), y))

        # --- Buttons ---
        mp = pygame.mouse.get_pos()
        for btn in self._buttons:
            btn.draw(screen, self.font_btn, btn.hovered(mp))

        # Keyboard hint
        hint = self.font_stat.render(
            "R  reboot   |   ESC  return to menu", True, (45, 65, 90)
        )
        screen.blit(hint, (cx - hint.get_width() // 2, sh - 34))

    def _draw_fountain(self, screen: pygame.Surface) -> None:
        for f in self._fountain:
            if f.lifetime <= 0:
                continue
            frac = f.lifetime / f.max_lifetime
            alpha = max(0, int(frac * 220))
            sz = max(1, int(f.size))
            dim = sz * 2 + 2
            tmp = pygame.Surface((dim, dim), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (*f.color, alpha), (sz + 1, sz + 1), sz)
            screen.blit(tmp, (int(f.x) - sz, int(f.y) - sz))

    # -----------------------------------------------------------------------
    # Factory helpers
    # -----------------------------------------------------------------------

    def _make_shards(self, px: float, py: float) -> List[_Shard]:
        colors = [
            (0, 220, 255), (180, 240, 255), (255, 255, 255), (100, 180, 255)
        ]
        shards = []
        for _ in range(self._SHARD_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(70, 240)
            lt = random.uniform(1.2, self._SHATTER_DUR + 0.5)
            shards.append(_Shard(
                x=px, y=py,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                angle=random.uniform(0, 360),
                spin=random.uniform(-200, 200),
                size=random.uniform(4, 11),
                color=random.choice(colors),
                alpha=255.0,
                lifetime=lt,
                max_lifetime=lt,
            ))
        return shards

    def _make_ash(self, sw: int, sh: int, spread: bool = True) -> List[_Ash]:
        ash = []
        for _ in range(self._ASH_COUNT):
            w = random.randint(2, 5)
            h = random.randint(2, 5)
            ash.append(_Ash(
                x=random.uniform(0, sw),
                y=random.uniform(0, sh) if spread else -random.randint(0, sh),
                vx=random.uniform(-8, 8),
                vy=random.uniform(18, 60),
                w=w, h=h,
                alpha=random.randint(28, 76),
            ))
        return ash

    def _make_fountain(self, sw: int, sh: int) -> List[_Fountain]:
        colors = [
            (255, 210, 50), (0, 220, 255), (255, 255, 255), (255, 100, 200)
        ]
        parts = []
        cx = sw // 2
        for _ in range(60):
            lt = random.uniform(1.0, 2.6)
            parts.append(_Fountain(
                x=cx + random.uniform(-130, 130),
                y=sh + 20,
                vx=random.uniform(-180, 180),
                vy=random.uniform(-640, -180),
                color=random.choice(colors),
                lifetime=lt,
                max_lifetime=lt,
                size=random.uniform(2.0, 5.5),
            ))
        return parts

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------

    def _build_layout(self, sw: int, sh: int) -> None:
        self._sw = sw
        self._sh = sh
        cx = sw // 2

        btn_w = 230
        btn_h = 46
        gap = 28
        y = sh - 120

        self._buttons = [
            _Button(
                "REBOOT SEQUENCE",
                pygame.Rect(cx - btn_w - gap // 2, y, btn_w, btn_h),
            ),
            _Button(
                "RETURN TO UPLINK",
                pygame.Rect(cx + gap // 2, y, btn_w, btn_h),
            ),
        ]
        self._layout_built = True
