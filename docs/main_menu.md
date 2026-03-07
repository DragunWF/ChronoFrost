# ChronoFrost: Main Menu Architecture

## Design Philosophy

The Main Menu serves as the entry point to ChronoFrost. It prioritizes simplicity and immediate access to gameplay. Rendering relies entirely on Pygame's geometric drawing functions and text rendering, avoiding external image assets. The UI will feel responsive through code-driven hover states and transitions.

---

## 1. Core Layout (Main Screen)

The primary screen contains only the essential navigation points, centered on the screen for a clean, minimalist aesthetic.

- **Title Display:** "CHRONOFROST"
  - Rendered in the largest font size.
  - Uses a stark, icy color palette (e.g., Cyan or glowing White) against the dark void background.
- **Button: [ START SEQUENCE ]**
  - Immediately transitions the State Machine from `MENU` to `PLAYING`.
  - Triggers a "FrostNova" screen flash and a sound effect upon clicking to mask the state transition.
- **Button: [ OPTIONS ]**
  - Transitions the menu state to the Options Sub-Menu.
- **Button: [ TERMINATE ]**
  - Cleanly closes the Pygame window and exits the application (`pygame.quit()`, `sys.exit()`).

---

## 2. Options Sub-Menu

A focused configuration screen that gives the player control over the game's audio mix.

- **Master Volume:** \* A horizontal slider or incremental toggle (0% to 100%).
  - Controls the global output volume of the entire game.
- **SFX Volume:** \* A horizontal slider or incremental toggle (0% to 100%).
  - Controls the volume of shooting, shattering, and UI interaction sounds relative to the Master Volume.
- **Button: [ BACK ]**
  - Saves the current audio settings (optionally writing them to a `config.json` file) and returns to the Core Layout.

---

## 3. Visual Flair & Interaction (The "Juice")

To keep the text-based menu from feeling static, the following code-driven effects will run in the `MENU` state:

- **Procedural Background:** Faint, semi-transparent geometric shapes (representing Ice Cubes and Embers) slowly drift upwards in the background, recycling the movement logic from the main game but at a highly reduced speed.
- **Hover States:** When the player's mouse coordinates intersect with a button's rectangle, the button visually reacts.
  - _Example:_ The text color shifts from dull grey to bright white, and geometric brackets `> START <` appear around the text to indicate it is clickable.
