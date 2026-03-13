import pygame
import os


class FontManager:
    """
    Manages loading and caching of the custom thematic font to prevent
    redundant memory allocation and preserve framerate.
    """

    def __init__(self) -> None:
        pygame.font.init()
        self.font_path: str = "assets/fonts/game_font.ttf"
        self._cache: dict[int, pygame.font.Font] = {}

    def get_font(self, size: int) -> pygame.font.Font:
        """
        Retrieves a font object of the specified size. 
        Loads from disk and caches it if it hasn't been requested before.
        Falls back to a default system font if the custom file is missing.
        """
        if size not in self._cache:
            try:
                # Attempt to load the custom font
                if not os.path.exists(self.font_path):
                    raise FileNotFoundError(
                        f"Font file missing at {self.font_path}")
                self._cache[size] = pygame.font.Font(self.font_path, size)
            except Exception as e:
                # Safe fallback to avoid game crash
                print(
                    f"FontManager: Failed to load custom font '{self.font_path}' (size {size}). Error: {e}. Using fallback.")
                self._cache[size] = pygame.font.SysFont(None, size)

        return self._cache[size]


# Global instance for easy access across the project
font_manager = FontManager()
