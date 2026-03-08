import pygame


class BoonsMenu:
    def __init__(self):
        """
        Initializes the draft screen. Sets up card dimensions and fonts.
        """
        self.font = pygame.font.SysFont(None, 36)
        self.next_state = None

    def enter(self):
        """
        Called exactly when the player hits a score milestone.
        This is where you will randomize the 3 cards presented to the player 
        so they are different every time this menu opens.
        """
        self.next_state = None
        # Example: self.current_cards = self.get_three_random_augments()

    def handle_events(self, events):
        """
        Handles the player clicking on one of the 3 upgrade cards.
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Placeholders for selecting a card
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    # Apply the upgrade to the player here, then return to the game
                    self.next_state = "PLAYING"

    def update(self, dt):
        """
        Handles any visual hover effects on the cards.
        Returns "PLAYING" once an upgrade is selected to unpause the game.
        """
        if self.next_state is not None:
            return self.next_state
        return None

    def draw(self, screen):
        """
        Renders the 3 draft cards over the game.
        Tip: Don't fill the screen with a solid color here. If you draw a semi-transparent 
        black rectangle instead, you can see the paused game behind the menu!
        """
        # A simple background to prove the scene loaded
        screen.fill((50, 20, 50))

        title = self.font.render(
            "TEMPORAL AUGMENTS DRAFT", True, (255, 215, 0))
        prompt = self.font.render(
            "Press 1, 2, or 3 to select a Boon and return", True, (255, 255, 255))

        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 100))
        screen.blit(prompt, (screen.get_width() //
                    2 - prompt.get_width()//2, 300))
