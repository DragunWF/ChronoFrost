import pygame
import math
import random
from typing import List, Optional, Dict, Any

from utils.base_scene import BaseScene
from utils.constants import PLAY_STATE
from systems.boons import BOON_POOL
from systems.run_stats import RunStats

# ----- Card layout -------------------------------------------------------
_CARD_W = 210
_CARD_H = 270
_CARD_PAD = 20
_CARD_TOP = 150
# -------------------------------------------------------------------------


class BoonsMenu(BaseScene):
    """
    Paused upgrade selection overlay shown at score milestones.
    The game world is drawn first (by GameScene), then this overlay is drawn
    on top — keeping the scene frozen behind the UI.

    Enter via open_with_stats() rather than enter() so the run is not reset.
    """

    def __init__(self) -> None:
        self.font_title: pygame.font.Font = pygame.font.SysFont(None, 52)
        self.font_name: pygame.font.Font = pygame.font.SysFont(None, 30)
        self.font_desc: pygame.font.Font = pygame.font.SysFont(None, 22)
        self.font_hint: pygame.font.Font = pygame.font.SysFont(None, 20)

        self.run_stats: Optional[RunStats] = None
        self.cards: List[Dict[str, Any]] = []
        self.selected_idx: int = 0        # keyboard/gamepad cursor
        self.hovered_idx: Optional[int] = None   # mouse hover index
        self.next_state: Optional[str] = None

        # Cached card rects updated every draw() for mouse hit-testing
        self._card_rects: List[pygame.Rect] = []

    def open_with_stats(self, run_stats: RunStats) -> None:
        """
        Called by main.py when PLAY → BOONS transition occurs.
        Picks 3 random non-duplicate boons from the pool and resets nav state.
        """
        self.run_stats = run_stats
        self.next_state = None
        self.selected_idx = 0
        self.hovered_idx = None

        available = [b for b in BOON_POOL if b["name"] not in run_stats.selected_boons]
        count = min(3, len(available))
        self.cards = random.sample(available, count) if count > 0 else []

    def enter(self) -> None:
        """Kept for BaseScene interface compliance; open_with_stats() handles real setup."""
        pass

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected_idx = (self.selected_idx - 1) % max(1, len(self.cards))
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected_idx = (self.selected_idx + 1) % max(1, len(self.cards))
                elif event.key == pygame.K_RETURN:
                    self._select(self.selected_idx)
                elif event.key == pygame.K_1 and len(self.cards) >= 1:
                    self._select(0)
                elif event.key == pygame.K_2 and len(self.cards) >= 2:
                    self._select(1)
                elif event.key == pygame.K_3 and len(self.cards) >= 3:
                    self._select(2)

            elif event.type == pygame.MOUSEMOTION:
                self.hovered_idx = None
                for i, rect in enumerate(self._card_rects):
                    if rect.collidepoint(event.pos):
                        self.hovered_idx = i
                        self.selected_idx = i  # sync keyboard cursor to mouse position
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(self._card_rects):
                    if rect.collidepoint(event.pos):
                        self._select(i)
                        break

    def _select(self, idx: int) -> None:
        """Apply the chosen boon, record it, and return to the game."""
        if not self.cards or idx >= len(self.cards):
            return
        card = self.cards[idx]
        card["apply_fn"](self.run_stats)
        self.run_stats.selected_boons.append(card["name"])
        self.next_state = PLAY_STATE

    def update(self, dt: float) -> Optional[str]:
        return self.next_state

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()

        # Semi-transparent dark overlay — paused game scene stays visible behind it
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 185))
        screen.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_title.render("TEMPORAL AUGMENTS", True, (255, 215, 0))
        screen.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, 60))

        sub_surf = self.font_hint.render(
            "Choose one upgrade to apply permanently", True, (180, 180, 200)
        )
        screen.blit(sub_surf, (sw // 2 - sub_surf.get_width() // 2, 112))

        # Card row — centred
        total_w = len(self.cards) * _CARD_W + (len(self.cards) - 1) * _CARD_PAD
        row_left = sw // 2 - total_w // 2

        self._card_rects = []
        for i, card in enumerate(self.cards):
            rect = pygame.Rect(
                row_left + i * (_CARD_W + _CARD_PAD), _CARD_TOP, _CARD_W, _CARD_H
            )
            self._card_rects.append(rect)
            self._draw_card(screen, rect, card, selected=(i == self.selected_idx))

        # Bottom keyboard hint
        hint = self.font_hint.render(
            "← → to navigate   ENTER to select   (1 / 2 / 3)",
            True,
            (120, 120, 140),
        )
        screen.blit(hint, (sw // 2 - hint.get_width() // 2, sh - 36))

    # -----------------------------------------------------------------------
    # Card rendering helpers
    # -----------------------------------------------------------------------

    def _draw_card(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        card: Dict[str, Any],
        selected: bool,
    ) -> None:
        is_combat = card["category"] == "COMBAT"
        accent = (220, 80, 80) if is_combat else (80, 200, 220)
        bg_col = (35, 15, 15) if is_combat else (10, 22, 38)
        border_col = accent if selected else (60, 60, 80)
        border_w = 3 if selected else 1

        # Card background
        pygame.draw.rect(screen, bg_col, rect, border_radius=10)
        pygame.draw.rect(screen, border_col, rect, border_w, border_radius=10)

        # Selection glow
        if selected:
            glow = pygame.Surface((rect.w + 16, rect.h + 16), pygame.SRCALPHA)
            pygame.draw.rect(
                glow, (*accent, 40), (0, 0, rect.w + 16, rect.h + 16), border_radius=14
            )
            screen.blit(glow, (rect.x - 8, rect.y - 8))

        cx = rect.centerx
        icon_y = rect.y + 58

        # Icon
        self._draw_boon_icon(screen, cx, icon_y, card["name"], accent)

        # Category label
        cat_surf = self.font_hint.render(card["category"], True, accent)
        screen.blit(cat_surf, (cx - cat_surf.get_width() // 2, icon_y + 42))

        # Boon name
        name_surf = self.font_name.render(card["name"], True, (235, 235, 235))
        screen.blit(name_surf, (cx - name_surf.get_width() // 2, icon_y + 62))

        # Description (newline-split)
        for j, line in enumerate(card["description"].split("\n")):
            d_surf = self.font_desc.render(line, True, (160, 160, 180))
            screen.blit(d_surf, (cx - d_surf.get_width() // 2, icon_y + 96 + j * 22))

        # Keyboard shortcut badge
        key_num = self.cards.index(card) + 1
        badge_col = accent if selected else (100, 100, 120)
        badge = self.font_hint.render(f"[{key_num}]", True, badge_col)
        screen.blit(badge, (rect.x + 8, rect.bottom - 24))

    def _draw_boon_icon(
        self, screen: pygame.Surface, cx: int, cy: int, name: str, color: tuple
    ) -> None:
        """Draw a unique pygame.draw icon for each boon at (cx, cy)."""
        r = 24

        if name == "PierceShot":
            # Horizontal arrow (bullet passing through)
            for offset in (-6, 0, 6):
                pygame.draw.line(screen, color, (cx - r, cy + offset), (cx + r - 8, cy + offset), 2)
            pts = [(cx + r - 8, cy - 10), (cx + r + 4, cy), (cx + r - 8, cy + 10)]
            pygame.draw.polygon(screen, color, pts)

        elif name == "RapidFire":
            # Three vertical bars of increasing height
            for i, h in enumerate([14, 20, 26]):
                bx = cx - 14 + i * 14
                pygame.draw.rect(screen, color, (bx - 4, cy - h // 2, 8, h), border_radius=3)

        elif name == "SpreadShot":
            # Fan of 3 lines diverging upward
            for angle_deg in (-30, 0, 30):
                ang = math.radians(angle_deg - 90)
                ex = cx + math.cos(ang) * r
                ey = cy + math.sin(ang) * r
                pygame.draw.line(screen, color, (cx, cy + 10), (int(ex), int(ey)), 2)

        elif name == "HeavyCaliber":
            # Thick bullet silhouette
            pygame.draw.circle(screen, color, (cx, cy - 8), 9)
            pygame.draw.rect(screen, color, (cx - 9, cy - 8, 18, 20), border_radius=2)

        elif name == "DeepFreeze":
            # Snowflake: 6 spokes with tip dots
            for i in range(6):
                ang = math.radians(i * 60)
                ex = cx + math.cos(ang) * r
                ey = cy + math.sin(ang) * r
                pygame.draw.line(screen, color, (cx, cy), (int(ex), int(ey)), 2)
                pygame.draw.circle(screen, color, (int(ex), int(ey)), 3)

        elif name == "EmberMagnet":
            # Horseshoe magnet arc
            pygame.draw.arc(
                screen, color,
                (cx - r, cy - r, r * 2, r * 2),
                math.radians(0), math.radians(180), 3,
            )
            pygame.draw.line(screen, color, (cx - r, cy), (cx - r, cy + 14), 3)
            pygame.draw.line(screen, color, (cx + r, cy), (cx + r, cy + 14), 3)

        elif name == "KineticPlating":
            # Shield outline with centre line
            pts = [
                (cx, cy - r), (cx + r, cy - r // 2),
                (cx + r, cy + r // 3), (cx, cy + r),
                (cx - r, cy + r // 3), (cx - r, cy - r // 2),
            ]
            pygame.draw.polygon(screen, color, pts, 2)
            pygame.draw.line(screen, color, (cx, cy - 10), (cx, cy + 10), 2)

        elif name == "Overclock":
            # Clock face with forward-pointing hour hand
            pygame.draw.circle(screen, color, (cx, cy), r, 2)
            pygame.draw.line(screen, color, (cx, cy), (cx, cy - r + 4), 2)
            pygame.draw.line(screen, color, (cx, cy), (cx + r - 6, cy - 8), 2)
            # Small forward chevron
            pygame.draw.line(screen, color, (cx + r - 6, cy - 8), (cx + r - 2, cy - 2), 2)

        else:
            pygame.draw.circle(screen, color, (cx, cy), r, 2)

