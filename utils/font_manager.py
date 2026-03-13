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
        # Apply a global scale factor down because the new font renders larger
        # than the default Pygame system font.
        scaled_size = int(size * 0.8)

        if scaled_size not in self._cache:
            try:
                # Attempt to load the custom font
                if not os.path.exists(self.font_path):
                    raise FileNotFoundError(
                        f"Font file missing at {self.font_path}")
                self._cache[scaled_size] = pygame.font.Font(
                    self.font_path, scaled_size)
            except Exception as e:
                # Safe fallback to avoid game crash
                print(
                    f"FontManager: Failed to load custom font '{self.font_path}' (size {scaled_size}). Error: {e}. Using fallback.")
                self._cache[scaled_size] = pygame.font.SysFont(
                    None, scaled_size)

        return self._cache[scaled_size]


# Global instance for easy access across the project
font_manager = FontManager()
