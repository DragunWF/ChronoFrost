import pygame
import sys
import asyncio

from entities.main_menu import MainMenu
from entities.game_scene import GameScene
from entities.boons_menu import BoonsMenu
from entities.game_over_menu import GameOverMenu
from entities.leaderboard_scene import LeaderboardScene

from utils.constants import (
    MAIN_MENU_STATE,
    PLAY_STATE,
    GAME_OVER_STATE,
    BOONS_STATE,
    QUIT_STATE,
    LEADERBOARD_STATE,
)
from utils.audio_manager import audio_manager

# --- Global Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60


async def main():
    """The main entry point and State Machine manager for ChronoFrost."""
    pygame.init()
    pygame.mixer.init() # Initialize audio system
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ChronoFrost")
    clock = pygame.time.Clock()

    # Dictionary holding our instantiated state objects.
    states = {
        MAIN_MENU_STATE:   MainMenu(),
        PLAY_STATE:        GameScene(),
        BOONS_STATE:       BoonsMenu(),
        GAME_OVER_STATE:   GameOverMenu(),
        LEADERBOARD_STATE: LeaderboardScene(),
    }

    current_state = "MENU"

    # Call enter() on the initial state if it exists (useful for resetting variables)
    if hasattr(states[current_state], 'enter'):
        states[current_state].enter()

    running = True
    while running:
        # Yield to browser to prevent freezing (pygbag requirement)
        await asyncio.sleep(0)
        
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

                # Audio transition logic: stop music if leaving GameScene
                if prev_state == PLAY_STATE and current_state != BOONS_STATE:
                    audio_manager.stop_music()

                if prev_state == PLAY_STATE and current_state == BOONS_STATE:
                    # PLAY → BOONS: share RunStats with the menu; do NOT reset the game
                    states[BOONS_STATE].open_with_stats(states[PLAY_STATE].run_stats)
                elif prev_state == BOONS_STATE and current_state == PLAY_STATE:
                    # BOONS → PLAY: resume the existing run; do NOT call enter()
                    # Defensive: clear any stale one-shot transition requested by
                    # GameScene before the menu opened.
                    states[PLAY_STATE].next_state = None
                elif prev_state == PLAY_STATE and current_state == GAME_OVER_STATE:
                    # PLAY → GAME_OVER: capture last rendered frame + pass run stats.
                    # save_data write happens inside enter_with_stats (one write/run).
                    game = states[PLAY_STATE]
                    snapshot  = game.render_surface.copy()
                    player    = getattr(game, "player", None)
                    player_x  = getattr(player, "x", 400.0)
                    player_y  = getattr(player, "y", 300.0)
                    states[GAME_OVER_STATE].enter_with_stats(
                        score             = int(game.score),
                        time_alive        = game.time_alive,
                        enemies_shattered = game.enemies_shattered,
                        boons_acquired    = (
                            len(game.run_stats.selected_boons) +
                            game.powerups_acquired
                        ),
                        player_x = player_x,
                        player_y = player_y,
                        snapshot = snapshot,
                    )
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
    asyncio.run(main())
