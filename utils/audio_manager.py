import os
import random
import pygame
from typing import List

from utils import settings


class AudioManager:
    """
    Manages background music and sound effects.
    Encapsulates pygame.mixer logic.
    """

    def __init__(self) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.current_music: str | None = None
        self.master_volume: float = settings.MASTER_VOLUME

        # Load specific sound effects
        self.sfx_player_hit = pygame.mixer.Sound("assets/audio/player_hit.wav")
        self.sfx_ember_pickup = pygame.mixer.Sound("assets/audio/pickup.wav")
        self.sfx_ui_select = pygame.mixer.Sound("assets/audio/ui_click.wav")
        self.sfx_boon_select = pygame.mixer.Sound("assets/audio/milestone.wav")
        self.sfx_game_over = pygame.mixer.Sound(
            "assets/audio/player_death.wav")

        self.sfx_enemy_shatter_list: List[pygame.mixer.Sound] = [
            pygame.mixer.Sound("assets/audio/enemy_death_1.wav"),
            pygame.mixer.Sound("assets/audio/enemy_death_2.wav"),
            pygame.mixer.Sound("assets/audio/enemy_death_3.wav")
        ]

    def play_player_hit(self) -> None:
        self.sfx_player_hit.play()

    def play_ember_pickup(self) -> None:
        self.sfx_ember_pickup.play()

    def play_ui_select(self) -> None:
        self.sfx_ui_select.play()

    def play_boon_select(self) -> None:
        self.sfx_boon_select.play()

    def play_game_over(self) -> None:
        self.sfx_game_over.play()

    def play_enemy_shatter(self) -> None:
        random.choice(self.sfx_enemy_shatter_list).play()

    # --- Background Music Methods (Legacy) ---
    def load_music(self, path: str) -> bool:
        if not os.path.exists(path):
            print(f"AudioManager: Audio file not found at {path}")
            return False

        try:
            pygame.mixer.music.load(path)
            self.current_music = path
            return True
        except pygame.error as e:
            print(f"AudioManager: Failed to load music {path}: {e}")
            self.current_music = None
            return False

    def play_music(self, loop: bool = True) -> None:
        if self.current_music:
            try:
                pygame.mixer.music.set_volume(self.master_volume)
                pygame.mixer.music.play(-1 if loop else 0)
            except pygame.error as e:
                print(f"AudioManager: Failed to play music: {e}")

    def play_random_music(self, paths: list[str], loop: bool = True) -> None:
        if not paths:
            return
        path = random.choice(paths)
        if self.load_music(path):
            self.play_music(loop)

    def stop_music(self) -> None:
        pygame.mixer.music.stop()

    def set_music_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.master_volume)


# Global instance for easy access across scenes
audio_manager = AudioManager()
