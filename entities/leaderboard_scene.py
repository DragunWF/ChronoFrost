"""
Leaderboard scene — displays the top-10 scores and lifetime statistics
loaded from save_data.json.  Accessed via the RECORDS button in the main menu.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pygame

from systems import save_data
from utils.base_scene import BaseScene
from utils.constants import MAIN_MENU_STATE

# ---------------------------------------------------------------------------
# Icy colour palette (mirrors main_menu.py)
# ---------------------------------------------------------------------------
_BG = (8, 12, 22)
_TITLE = (100, 220, 255)
_TITLE_SHADOW = (18, 60, 120)
_BORDER = (38, 78, 138)
_ROW_ODD = (12, 20, 38)
_ROW_EVEN = (8, 14, 28)
_RANK_COLOURS = [(255, 210, 50), (195, 195, 210),
                 (180, 115, 55)]  # gold / silver / bronze
_TEXT_MAIN = (200, 220, 240)
_TEXT_DIM = (80, 105, 130)
_BTN_IDLE = (80, 95, 115)
_BTN_HOV = (235, 248, 255)
_BDR_IDLE = (38, 78, 138)
_BDR_HOV = (80, 190, 255)


# ---------------------------------------------------------------------------
# Button (same style as the rest of the UI)
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
# LeaderboardScene
# ---------------------------------------------------------------------------

class LeaderboardScene(BaseScene):
    """Read-only view of the top-10 leaderboard and cumulative lifetime stats."""

    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont(None, 68)
        self.font_col_hdr = pygame.font.SysFont(None, 26)
        self.font_row = pygame.font.SysFont(None, 28)
        self.font_stat = pygame.font.SysFont(None, 26)
        self.font_btn = pygame.font.SysFont(None, 34)

        self.next_state: Optional[str] = None

        self._board:    List[Dict[str, Any]] = []
        self._lifetime: Dict[str, Any] = {}
        self._button:   Optional[_Button] = None

        self._layout_built: bool = False
        self._sw: int = 800
        self._sh: int = 600

    # -----------------------------------------------------------------------
    # BaseScene interface
    # -----------------------------------------------------------------------

    def enter(self) -> None:
        self.next_state = None
        # Reload on every visit so newly completed runs appear immediately
        self._board = save_data.get_leaderboard()
        self._lifetime = save_data.get_lifetime_stats()

        surf = pygame.display.get_surface()
        sw, sh = surf.get_size() if surf else (800, 600)
        self._build_layout(sw, sh)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._button and self._button.hovered(event.pos):
                    self.next_state = MAIN_MENU_STATE
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.next_state = MAIN_MENU_STATE

    def update(self, dt: float) -> Optional[str]:
        return self.next_state

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        if not self._layout_built or sw != self._sw or sh != self._sh:
            self._build_layout(sw, sh)

        screen.fill(_BG)
        cx = sw // 2

        # ---- Title ----
        ty = 28
        shadow_surf = self.font_title.render("RECORDS", True, _TITLE_SHADOW)
        title_surf = self.font_title.render("RECORDS", True, _TITLE)
        tx = cx - title_surf.get_width() // 2
        screen.blit(shadow_surf, (tx + 3, ty + 3))
        screen.blit(title_surf,  (tx, ty))

        # ---- Table geometry ----
        table_top = ty + title_surf.get_height() + 18
        table_x = cx - 260
        table_w = 520
        row_h = 30

        # Column headers
        cols = [("#", 24), ("SCORE", 92), ("DATE", 230), ("TIME", 370)]
        for label, off_x in cols:
            s = self.font_col_hdr.render(label, True, _TEXT_DIM)
            screen.blit(s, (table_x + off_x, table_top))

        pygame.draw.line(
            screen, _BORDER,
            (table_x, table_top + 22),
            (table_x + table_w, table_top + 22), 1,
        )

        # Data rows
        rows_start = table_top + 28
        for i, entry in enumerate(self._board[:10]):
            ry = rows_start + i * row_h
            row_bg = _ROW_ODD if i % 2 == 0 else _ROW_EVEN
            pygame.draw.rect(screen, row_bg, (table_x, ry, table_w, row_h - 2))

            rank_col = _RANK_COLOURS[i] if i < 3 else _TEXT_MAIN
            rank_surf = self.font_row.render(
                str(i + 1),                         True, rank_col)
            score_surf = self.font_row.render(
                f"{entry.get('score', 0):,}",       True, rank_col if i < 3 else _TEXT_MAIN)
            date_surf = self.font_row.render(
                entry.get("date", "—"),             True, _TEXT_DIM)
            time_surf = self.font_row.render(
                entry.get("time", "—"),             True, _TEXT_MAIN)

            screen.blit(rank_surf,  (table_x + 24,  ry + 4))
            screen.blit(score_surf, (table_x + 92,  ry + 4))
            screen.blit(date_surf,  (table_x + 230, ry + 4))
            screen.blit(time_surf,  (table_x + 370, ry + 4))

        if not self._board:
            empty = self.font_col_hdr.render(
                "-- No runs recorded yet --", True, _TEXT_DIM)
            screen.blit(empty, (cx - empty.get_width() // 2, rows_start + 20))

        # ---- Lifetime stats bar ----
        ls_y = rows_start + 10 * row_h + 18
        pygame.draw.line(screen, _BORDER, (table_x, ls_y),
                         (table_x + table_w, ls_y), 1)
        ls_y += 12

        ls = self._lifetime
        total_played = ls.get("total_time_played", 0)
        total_mins = total_played // 60
        stat_texts = [
            f"RUNS: {ls.get('runs_completed', 0)}",
            f"SHATTERED: {ls.get('total_shattered', 0):,}",
            f"TOTAL TIME: {total_mins}m",
        ]
        segment = table_w // len(stat_texts)
        for j, txt in enumerate(stat_texts):
            s = self.font_stat.render(txt, True, _TEXT_DIM)
            screen.blit(s, (table_x + segment * j, ls_y))

        # ---- BACK button ----
        if self._button:
            self._button.draw(screen, self.font_btn,
                              self._button.hovered(pygame.mouse.get_pos()))

        # Keyboard hint
        hint = self.font_stat.render("ESC  to return", True, (38, 60, 88))
        screen.blit(hint, (cx - hint.get_width() // 2, sh - 26))

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------

    def _build_layout(self, sw: int, sh: int) -> None:
        self._sw = sw
        self._sh = sh
        cx = sw // 2
        self._button = _Button(
            "BACK", pygame.Rect(cx - 80, sh - 68, 160, 44)
        )
        self._layout_built = True
