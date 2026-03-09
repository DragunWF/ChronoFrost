import pygame
from typing import List, Optional

from utils.base_scene import BaseScene
from utils.constants import MAIN_MENU_STATE


class GameOverMenu(BaseScene):
    def __init__(self) -> None:
        self.font: pygame.font.Font = pygame.font.SysFont(None, 64)
        self.small_font: pygame.font.Font = pygame.font.SysFont(None, 32)
        self.next_state: Optional[str] = None

    def enter(self) -> None:
        self.next_state = None

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r or event.key == pygame.K_RETURN:
                    self.next_state = MAIN_MENU_STATE

    def update(self, dt: float) -> Optional[str]:
        return self.next_state

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((50, 10, 10))  # Dark red

        title = self.font.render("FROZEN FOREVER", True, (255, 100, 100))
        prompt = self.small_font.render(
            "Press R to Return to Menu", True, (255, 255, 255))

        screen.blit(title, (screen.get_width() // 2 -
                    title.get_width() // 2, screen.get_height() // 2 - 50))
        screen.blit(prompt, (screen.get_width() // 2 -
                    prompt.get_width() // 2, screen.get_height() // 2 + 50))
