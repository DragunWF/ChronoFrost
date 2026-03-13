import pygame
from typing import Callable, Tuple

class Button:
    """
    A reusable UI Button for menus and overlays.
    Supports hover detection, text rendering, and callbacks.
    """
    def __init__(
        self,
        text: str,
        rect: pygame.Rect,
        font: pygame.font.Font,
        callback: Callable[[], None],
        base_color: Tuple[int, int, int] = (100, 200, 255),
        hover_color: Tuple[int, int, int] = (255, 255, 255),
        border_color: Tuple[int, int, int] = (50, 150, 255)
    ) -> None:
        self.text = text
        self.rect = rect
        self.font = font
        self.callback = callback
        
        self.base_color = base_color
        self.hover_color = hover_color
        self.border_color = border_color
        
        self.is_hovered = False

    def update(self, mouse_pos: Tuple[int, int]) -> None:
        """Update hover state based on mouse position."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse click events."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.callback()

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button with its current state."""
        # Draw border
        pygame.draw.rect(surface, self.border_color, self.rect, 2, border_radius=5)
        
        # Determine text color and content
        color = self.hover_color if self.is_hovered else self.base_color
        display_text = f"> {self.text} <" if self.is_hovered else self.text
        
        text_surf = self.font.render(display_text, True, color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
