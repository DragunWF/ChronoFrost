import json
import math
import os
import random
from typing import Dict, List, Optional, Tuple

import pygame

from utils.audio_manager import audio_manager
from utils.base_scene import BaseScene
from utils.constants import PLAY_STATE, QUIT_STATE, LEADERBOARD_STATE
from utils.vfx import ScreenFlash
from utils.font_manager import font_manager

# ---------------------------------------------------------------------------
# Color palette — icy dark void aesthetic
# ---------------------------------------------------------------------------
_BG = (8, 12, 22)
_TITLE = (100, 220, 255)
_TITLE_SHADOW = (18, 60, 120)
_SUBTITLE = (42, 72, 102)
_BTN_IDLE = (80, 95, 115)
_BTN_HOVER = (235, 248, 255)
_BORDER_IDLE = (38, 78, 138)
_BORDER_HOVER = (80, 190, 255)
_TRACK_BG = (28, 44, 70)
_TRACK_FILL = (65, 168, 255)
_THUMB = (195, 235, 255)
_LABEL_COLOR = (140, 170, 200)

# config.json lives at the workspace root (one level above entities/)
_CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "config.json")
)


# ---------------------------------------------------------------------------
# Helpers — config persistence
# ---------------------------------------------------------------------------

def _load_config() -> Dict[str, float]:
    defaults: Dict[str, float] = {"master_vol": 1.0, "sfx_vol": 1.0}
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return {
            "master_vol": float(raw.get("master_vol", 1.0)),
            "sfx_vol":    float(raw.get("sfx_vol",    1.0)),
        }
    except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
        return defaults


def _save_config(master_vol: float, sfx_vol: float) -> None:
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump({"master_vol": master_vol,
                      "sfx_vol": sfx_vol}, fh, indent=2)
    except OSError:
        pass  # Non-critical; silently skip on permission errors


# ---------------------------------------------------------------------------
# Background particle (ice cube or ember drifting upward)
# ---------------------------------------------------------------------------

class _BgParticle:
    """Faint geometric shape that drifts upward and wraps at the top edge."""

    __slots__ = ("x", "y", "speed", "half", "alpha", "kind", "angle", "spin")

    def __init__(self, sw: int, sh: int, spread_y: bool = True) -> None:
        self._randomise(sw, sh, spread_y)

    def _randomise(self, sw: int, sh: int, spread_y: bool) -> None:
        self.x = random.uniform(0, sw)
        self.y = random.uniform(
            0, sh) if spread_y else sh + random.uniform(0, 40)
        self.speed = random.uniform(10.0, 32.0)
        self.half = random.uniform(4.0, 13.0)
        self.alpha = random.randint(14, 50)
        self.kind = random.choice(("cube", "ember"))
        self.angle = random.uniform(0.0, 360.0)
        self.spin = random.uniform(-18.0, 18.0)

    def update(self, dt: float, sw: int, sh: int) -> None:
        self.y -= self.speed * dt
        self.angle += self.spin * dt
        if self.y < -(self.half * 3):
            self._randomise(sw, sh, spread_y=False)

    def draw(self, surf: pygame.Surface) -> None:
        h = int(self.half)
        tmp_size = h * 4 + 2
        tmp = pygame.Surface((tmp_size, tmp_size), pygame.SRCALPHA)
        cx = cy = tmp_size // 2

        rad = math.radians(self.angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)

        if self.kind == "cube":
            color = (90, 200, 255, self.alpha)
            # Rotated square outline: 4 corners
            corners = [
                (cos_a * h - sin_a * h,  sin_a * h + cos_a * h),
                (-cos_a * h - sin_a * h, -sin_a * h + cos_a * h),
                (-cos_a * h + sin_a * h, -sin_a * h - cos_a * h),
                (cos_a * h + sin_a * h,  sin_a * h - cos_a * h),
            ]
            pts = [(int(cx + x), int(cy + y)) for x, y in corners]
            pygame.draw.polygon(tmp, color, pts, 1)
        else:
            color = (255, 130, 55, self.alpha)
            # Diamond (unrotated; spin still applies via angle on cube variant)
            pts = [
                (cx,     cy - h),
                (cx + h, cy),
                (cx,     cy + h),
                (cx - h, cy),
            ]
            pygame.draw.polygon(tmp, color, pts, 1)

        surf.blit(tmp, (int(self.x) - cx, int(self.y) - cy))


# ---------------------------------------------------------------------------
# Single button with idle / hover rendering
# ---------------------------------------------------------------------------

class _Button:
    """Draws a labelled rectangular button. Hover state adds `> LABEL <`."""

    def __init__(self, label: str, rect: pygame.Rect) -> None:
        self.label = label
        self.rect = rect

    def hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(mouse_pos)

    def draw(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        is_hovered: bool,
    ) -> None:
        border = _BORDER_HOVER if is_hovered else _BORDER_IDLE
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=4)

        text = f"> {self.label} <" if is_hovered else self.label
        color = _BTN_HOVER if is_hovered else _BTN_IDLE
        surf = font.render(text, True, color)
        screen.blit(
            surf,
            (self.rect.centerx - surf.get_width() // 2,
             self.rect.centery - surf.get_height() // 2),
        )


# ---------------------------------------------------------------------------
# MainMenu scene
# ---------------------------------------------------------------------------

class MainMenu(BaseScene):
    """
    Entry-point scene for ChronoFrost.

    Manages two internal sub-views via ``_view``:
    - ``"main"``    — title + START SEQUENCE / OPTIONS / TERMINATE buttons.
    - ``"options"`` — Master/SFX volume sliders + BACK button.

    The Options sub-view is handled entirely within this class so the state
    machine stays clean (only one MENU state in main.py).
    """

    _PARTICLE_COUNT = 35

    def __init__(self) -> None:
        self.font_title = font_manager.get_font(96)
        self.font_subtitle = font_manager.get_font(26)
        self.font_btn = font_manager.get_font(36)
        self.font_label = font_manager.get_font(28)

        self.next_state: Optional[str] = None
        self._view: str = "main"

        # Audio volumes (0.0 – 1.0)
        cfg = _load_config()
        self._master_vol: float = cfg["master_vol"]
        self._sfx_vol:    float = cfg["sfx_vol"]

        # FrostNova transition flash —— plays before switching to PLAY
        self._flash:        Optional[ScreenFlash] = None
        self._pending_play: bool = False

        # Background particles — initialised with sane defaults; rebuilt in enter()
        self._particles:       List[_BgParticle] = []
        self._sw: int = 800
        self._sh: int = 600

        # Button and slider layout — built lazily in draw() / enter()
        self._main_buttons:    List[_Button] = []
        self._options_buttons: List[_Button] = []
        self._slider_rects:    Dict[str, pygame.Rect] = {}
        self._slider_label_y:  Dict[str, int] = {}
        self._layout_built:    bool = False

        # Slider drag state
        self._dragging_slider: Optional[str] = None  # "master" | "sfx"

    # ------------------------------------------------------------------
    # BaseScene interface
    # ------------------------------------------------------------------

    def enter(self) -> None:
        self.next_state = None
        self._view = "main"
        self._flash = None
        self._pending_play = False
        self._dragging_slider = None

        # Reload config so volume reflects any mid-session saves
        cfg = _load_config()
        self._master_vol = cfg["master_vol"]
        self._sfx_vol = cfg["sfx_vol"]

        # Build layout using the live display surface dimensions
        surf = pygame.display.get_surface()
        sw, sh = surf.get_size() if surf else (800, 600)
        self._build_layout(sw, sh)

        # Seed particles once; keep them alive across re-entries
        if not self._particles:
            self._particles = [
                _BgParticle(sw, sh, spread_y=True)
                for _ in range(self._PARTICLE_COUNT)
            ]

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        # Ignore all input while the FrostNova flash is playing
        if self._pending_play:
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._view == "main":
                    self._handle_main_click(event.pos)
                else:
                    self._handle_options_click(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._dragging_slider = None

            elif event.type == pygame.MOUSEMOTION:
                if self._dragging_slider:
                    self._drag_slider(event.pos)

            elif event.type == pygame.KEYDOWN:
                if self._view == "options":
                    self._handle_options_key(event)

    def update(self, dt: float) -> Optional[str]:
        # Advance background particles
        for p in self._particles:
            p.update(dt, self._sw, self._sh)

        # Advance FrostNova flash; switch to PLAY when it expires
        if self._flash is not None:
            alive = self._flash.update(dt)
            if not alive and self._pending_play:
                self._pending_play = False
                self._flash = None
                return PLAY_STATE

        return self.next_state

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()

        # Rebuild layout if this is the first draw or if window resized
        if not self._layout_built or sw != self._sw or sh != self._sh:
            self._build_layout(sw, sh)
            if not self._particles:
                self._particles = [
                    _BgParticle(sw, sh, spread_y=True)
                    for _ in range(self._PARTICLE_COUNT)
                ]

        # Background void
        screen.fill(_BG)

        # Drifting particles (drawn under everything else)
        for p in self._particles:
            p.draw(screen)

        if self._view == "main":
            self._draw_main(screen, sw, sh)
        else:
            self._draw_options(screen, sw, sh)

        # FrostNova flash overlay (topmost layer)
        if self._flash:
            self._flash.draw(screen)

    # ------------------------------------------------------------------
    # Layout builder
    # ------------------------------------------------------------------

    def _build_layout(self, sw: int, sh: int) -> None:
        self._sw = sw
        self._sh = sh
        cx = sw // 2

        # --- Main view buttons ---
        btn_w, btn_h = 260, 48
        gap = 18
        # Buttons centred below the title
        start_y = sh // 2
        labels = ["START SEQUENCE", "OPTIONS", "RECORDS", "TERMINATE"]
        self._main_buttons = [
            _Button(lbl, pygame.Rect(cx - btn_w // 2,
                    start_y + i * (btn_h + gap), btn_w, btn_h))
            for i, lbl in enumerate(labels)
        ]

        # --- Options view ---
        back_r = pygame.Rect(cx - 80, sh - 100, 160, 44)
        self._options_buttons = [_Button("BACK", back_r)]

        track_w = 320
        slider_x = cx - track_w // 2

        master_track_y = sh // 2 - 10
        sfx_track_y = sh // 2 + 80
        self._slider_rects = {
            "master": pygame.Rect(slider_x, master_track_y, track_w, 8),
            "sfx":    pygame.Rect(slider_x, sfx_track_y,    track_w, 8),
        }
        self._slider_label_y = {
            "master": master_track_y - 34,
            "sfx":    sfx_track_y - 34,
        }

        self._layout_built = True

    # ------------------------------------------------------------------
    # Event sub-handlers
    # ------------------------------------------------------------------

    def _handle_main_click(self, pos: Tuple[int, int]) -> None:
        for i, btn in enumerate(self._main_buttons):
            if btn.hovered(pos):
                audio_manager.play_ui_select()
                if i == 0:   # START SEQUENCE
                    self._flash = ScreenFlash((80, 200, 255), duration=0.45)
                    self._pending_play = True
                elif i == 1:  # OPTIONS
                    self._view = "options"
                elif i == 2:  # RECORDS
                    self.next_state = LEADERBOARD_STATE
                elif i == 3:  # TERMINATE
                    self.next_state = QUIT_STATE
                return

    def _handle_options_click(self, pos: Tuple[int, int]) -> None:
        # BACK button
        for btn in self._options_buttons:
            if btn.hovered(pos):
                audio_manager.play_ui_select()
                _save_config(self._master_vol, self._sfx_vol)
                self._apply_volumes()
                self._view = "main"
                return

        # Slider hit — begin drag
        for key, rect in self._slider_rects.items():
            if rect.inflate(0, 28).collidepoint(pos):
                self._dragging_slider = key
                self._drag_slider(pos)
                return

    def _handle_options_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            _save_config(self._master_vol, self._sfx_vol)
            self._apply_volumes()
            self._view = "main"

    def _drag_slider(self, pos: Tuple[int, int]) -> None:
        key = self._dragging_slider
        if key not in self._slider_rects:
            return
        rect = self._slider_rects[key]
        val = max(0.0, min(1.0, (pos[0] - rect.x) / rect.width))
        if key == "master":
            self._master_vol = val
        else:
            self._sfx_vol = val
        self._apply_volumes()

    def _apply_volumes(self) -> None:
        """Push current volumes into the pygame mixer if it is initialised."""
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self._master_vol)
            # Individual SFX channels will read self._sfx_vol at play-time

    # ------------------------------------------------------------------
    # Draw sub-routines
    # ------------------------------------------------------------------

    def _draw_main(self, screen: pygame.Surface, sw: int, sh: int) -> None:
        cx = sw // 2
        mouse_pos = pygame.mouse.get_pos()

        # Title shadow + title
        title_surf = self.font_title.render("CHRONOFROST", True, _TITLE)
        shadow_surf = self.font_title.render(
            "CHRONOFROST", True, _TITLE_SHADOW)
        title_x = cx - title_surf.get_width() // 2
        title_y = sh // 4
        screen.blit(shadow_surf, (title_x + 3, title_y + 3))
        screen.blit(title_surf,  (title_x,     title_y))

        # Subtitle tagline
        sub = self.font_subtitle.render(
            "A BULLET-HELL EXPERIENCE", True, _SUBTITLE)
        screen.blit(sub, (cx - sub.get_width() // 2,
                    title_y + title_surf.get_height() + 10))

        # Navigation buttons
        for btn in self._main_buttons:
            btn.draw(screen, self.font_btn, btn.hovered(mouse_pos))

    def _draw_options(self, screen: pygame.Surface, sw: int, sh: int) -> None:
        cx = sw // 2
        mouse_pos = pygame.mouse.get_pos()

        # Section title
        title_surf = self.font_title.render("OPTIONS", True, _TITLE)
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, sh // 6))

        # Volume sliders
        self._draw_slider(screen, "master", "MASTER VOLUME", self._master_vol)
        self._draw_slider(screen, "sfx",    "SFX VOLUME",    self._sfx_vol)

        # BACK button
        for btn in self._options_buttons:
            btn.draw(screen, self.font_btn, btn.hovered(mouse_pos))

        # Keyboard hint
        hint = self.font_label.render("ESC  to go back", True, (45, 65, 90))
        screen.blit(hint, (cx - hint.get_width() // 2, self._sh - 52))

    def _draw_slider(
        self,
        screen: pygame.Surface,
        key: str,
        label: str,
        value: float,
    ) -> None:
        rect = self._slider_rects[key]
        label_y = self._slider_label_y[key]
        cx = rect.centerx

        # Label + percentage
        pct_text = f"{label}   {int(value * 100)}%"
        lbl_surf = self.font_label.render(pct_text, True, _LABEL_COLOR)
        screen.blit(lbl_surf, (cx - lbl_surf.get_width() // 2, label_y))

        # Track background
        pygame.draw.rect(screen, _TRACK_BG, rect, border_radius=4)

        # Filled portion
        fill_w = max(0, int(rect.width * value))
        if fill_w:
            fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
            pygame.draw.rect(screen, _TRACK_FILL, fill_rect, border_radius=4)

        # Thumb knob
        thumb_x = rect.x + int(rect.width * value)
        thumb_y = rect.centery
        pygame.draw.circle(screen, _THUMB,        (thumb_x, thumb_y), 9)
        pygame.draw.circle(screen, _BORDER_HOVER, (thumb_x, thumb_y), 9, 2)
