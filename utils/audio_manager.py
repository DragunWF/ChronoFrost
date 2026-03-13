import pygame
import os
import random
from utils import settings

class AudioManager:
    """
    Manages background music and sound effects.
    Encapsulates pygame.mixer logic.
    """
    def __init__(self):
        self.current_music = None
        self.master_volume = settings.MASTER_VOLUME

    def load_music(self, path: str) -> bool:
        """
        Loads the music file from the given path.
        Returns True if successful, False otherwise.
        """
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
        """
        Plays the currently loaded music.
        """
        if self.current_music:
            try:
                pygame.mixer.music.set_volume(self.master_volume)
                # Loop forever if -1, otherwise play once
                pygame.mixer.music.play(-1 if loop else 0)
            except pygame.error as e:
                print(f"AudioManager: Failed to play music: {e}")

    def play_random_music(self, paths: list[str], loop: bool = True) -> None:
        """
        Loads and plays a random track from the list.
        """
        if not paths:
            return
        path = random.choice(paths)
        if self.load_music(path):
            self.play_music(loop)

    def stop_music(self) -> None:
        """
        Stops the music playback.
        """
        pygame.mixer.music.stop()

    def set_music_volume(self, volume: float) -> None:
        """
        Updates the master volume and current music volume.
        """
        self.master_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.master_volume)

# Global instance for easy access across scenes
audio_manager = AudioManager()
