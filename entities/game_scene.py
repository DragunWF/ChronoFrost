import pygame


class GameScene:
    def __init__(self):
        """
        Initialize the core game containers here.
        This is where you set up your object pools for bullets, enemies, and embers.
        """
        self.font = pygame.font.SysFont(None, 36)
        self.next_state = None

    def enter(self):
        """
        Called when starting a new run or returning from the Boons screen.
        If returning from the Main Menu, use this to completely reset the player's 
        health, score, and clear the screen of enemies.
        """
        self.next_state = None
        # Example: self.player.reset()

    def handle_events(self, events):
        """
        Captures single-press actions like activating the Chrono-Freeze (Spacebar) 
        or clicking the mouse to shoot. 
        (Note: Continuous WASD movement goes in update(), not here).
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Placeholder shortcut to test the State Machine
                if event.key == pygame.K_m:
                    self.next_state = "BOONS"
                # Placeholder shortcut to "die" and return to menu
                if event.key == pygame.K_ESCAPE:
                    self.next_state = "MENU"

    def update(self, dt):
        """
        The heavy lifter. Calculates physics, time_scale math, enemy AI, and collisions.
        Returns "BOONS" if a milestone is hit, or "GAME_OVER" if the player dies.
        """
        # Example: keys = pygame.key.get_pressed()
        # Example: self.player.update(dt, keys)

        if self.next_state is not None:
            return self.next_state
        return None

    def draw(self, screen):
        """
        Renders the game world. 
        Draws the background, enemies, the player, and finally the UI overlay.
        """
        screen.fill((20, 30, 40))  # Slightly lighter background for the arena
        text = self.font.render(
            "SURVIVAL ARENA - Press 'M' for Boons, 'ESC' to Quit", True, (255, 255, 255))
        screen.blit(text, (20, 20))
