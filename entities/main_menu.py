# ==========================================
# File: main_menu.py
# ==========================================
import pygame


class MainMenu:
    def __init__(self):
        """
        Initialize persistent menu assets here. 
        Fonts, background surfaces, or UI button coordinates should be created 
        once in __init__ so you aren't recreating them every frame.
        """
        self.font = pygame.font.SysFont(None, 48)
        self.next_state = None

    def enter(self):
        """
        Called automatically by main.py exactly once when switching TO this scene.
        Use this to reset menu animations, play the menu music, or clear old inputs.
        """
        self.next_state = None

    def handle_events(self, events):
        """
        Processes all Pygame events passed from the main loop.
        Handles mouse clicks, hovering, and keyboard navigation.
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Queue up the state switch
                    self.next_state = "PLAYING"

    def update(self, dt):
        """
        Handles any logic that needs to run over time (e.g., drifting background particles).
        MUST return a string to trigger a state switch, or None to stay in this scene.
        """
        if self.next_state is not None:
            return self.next_state
        return None

    def draw(self, screen):
        """
        Renders the menu to the screen. 
        Wipes the previous frame and draws the title and buttons.
        """
        screen.fill((10, 15, 25))  # Dark void background
        text = self.font.render(
            "CHRONOFROST - Press ENTER to Start", True, (100, 200, 255))
        screen.blit(text, (screen.get_width()//2 -
                    text.get_width()//2, screen.get_height()//2))
