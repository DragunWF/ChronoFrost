import pygame
import sys

from entities.main_menu import MainMenu
from entities.game_scene import GameScene
from entities.boons_menu import BoonsMenu
from entities.game_over_menu import GameOverMenu

from utils.constants import (
    MAIN_MENU_STATE,
    PLAY_STATE,
    GAME_OVER_STATE,
    BOONS_STATE,
    QUIT_STATE
)

# --- Global Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60


def main():
    """The main entry point and State Machine manager for ChronoFrost."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ChronoFrost")
    clock = pygame.time.Clock()

    # Dictionary holding our instantiated state objects.
    states = {
        MAIN_MENU_STATE: MainMenu(),
        PLAY_STATE: GameScene(),
        BOONS_STATE: BoonsMenu(),
        GAME_OVER_STATE: GameOverMenu()
    }

    current_state = "MENU"

    # Call enter() on the initial state if it exists (useful for resetting variables)
    if hasattr(states[current_state], 'enter'):
        states[current_state].enter()

    running = True
    while running:
        # Delta time in seconds ensures movement is consistent regardless of framerate
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        # Global event handling (Quit)
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # 1. Event Handling (Pass the remaining events to the active scene)
        states[current_state].handle_events(events)

        # 2. Logic Update
        # If the scene's update method returns a string, we trigger a state switch
        next_state = states[current_state].update(dt)

        # State Switching Logic
        if next_state is not None and next_state != current_state:
            if next_state in states:
                prev_state = current_state
                current_state = next_state

                if prev_state == PLAY_STATE and current_state == BOONS_STATE:
                    # PLAY → BOONS: share RunStats with the menu; do NOT reset the game
                    states[BOONS_STATE].open_with_stats(states[PLAY_STATE].run_stats)
                elif prev_state == BOONS_STATE and current_state == PLAY_STATE:
                    # BOONS → PLAY: resume the existing run; do NOT call enter()
                    pass
                else:
                    # All other transitions: call enter() to reset the target scene
                    if hasattr(states[current_state], 'enter'):
                        states[current_state].enter()
            elif next_state == QUIT_STATE:
                # Allow scenes to gracefully exit the game by returning "QUIT"
                running = False

        # 3. Rendering
        states[current_state].draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
