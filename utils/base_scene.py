import pygame
from abc import ABC, abstractmethod
from typing import Optional, List


class BaseScene(ABC):
    """
    The abstract contract for all scenes in ChronoFrost.
    Any class inheriting from this MUST implement the abstract methods below,
    or Python will raise a TypeError upon instantiation.
    """

    def __init__(self) -> None:
        # Every scene needs to track its next state target
        self.next_state: Optional[str] = None

    @abstractmethod
    def enter(self) -> None:
        """
        Called exactly once when the State Machine transitions TO this scene.
        Use this to reset variables, clear old inputs, or trigger scene transitions.
        """
        pass

    @abstractmethod
    def handle_events(self, events: List[pygame.event.Event]) -> None:
        """
        Processes all Pygame events (keystrokes, mouse clicks, window quits) 
        passed down from the main game loop.
        """
        pass

    @abstractmethod
    def update(self, dt: float) -> Optional[str]:
        """
        Handles time-based logic, physics, timers, and AI.

        Returns:
            str: The exact dictionary key of the target state (e.g., "PLAYING").
            None: If the state machine should remain in the current scene.
        """
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """
        Renders the scene's visual elements to the main Pygame display surface.
        """
        pass
