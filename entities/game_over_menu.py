import pygame
from utils.base_scene import BaseScene


class GameOverMenu(BaseScene):
    def __init__(self) -> None:
        self.next_state: str | None = None

    def enter(self) -> None:
        pass

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        pass

    def update(self, dt: float) -> str | None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        pass
