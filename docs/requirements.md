# ChronoFrost - Game Requirements

## Project Overview

A 2D top-down roguelite survival/bullet-hell game built entirely in Pygame using primitive shapes and procedural geometry (no external image assets). The theme is "Frozen," executed through a core time-manipulation mechanic.

## Core Mechanics

- **Player Movement:** WASD keys for fluid, 2D vector-based movement.
- **Player Combat:** Mouse cursor to aim, Left-Click to shoot (or auto-fire towards the mouse).
- **Chrono-Freeze (Theme):** Pressing `SPACE` drastically slows down time (enemy movement, bullet speed, spawn rates) but drains a "Chrono-Charge" meter.
- **Scoring System:** Score constantly increases based on survival time. Bonus score is awarded for shooting down enemies.

## Entities & Enemies

- **The Player:** A simple geometric shape with a designated "front" to show aim direction.
- **Ice Cubes (Enemies):** Geometric shapes that spawn at the screen edges and move toward the player.
- **Enemy Attacks:** Ice Cubes periodically fire bullets in procedural patterns (rings, spirals, aimed shots).
- **Energy Drops:** Destroyed Ice Cubes drop "Chrono-Energy" embers that the player must collect to refuel their Chrono-Freeze meter.
- **Powerups:** Rare drops from enemies that grant temporary buffs (e.g., Thermal Shield, Flash-Step dash, Screen-clearing Supernova).
  - Refer to [`powerups.md`](./powerups.md) for more details.

## Progression & Loop

- **Milestone Boons (Upgrades):** Reaching specific score milestones pauses the game and opens an upgrade screen.
  - Refer to [`boons.md`](./boons.md) for more details.
- **Boons:** The player chooses one of three random buffs (e.g., +1 Pierce, Faster Fire Rate, Larger Freeze Meter).
  - Refer to [`boons.md`](./boons.md) for more details.
- **Escalating Difficulty:** As time progresses, enemy spawn rates, bullet speed, and enemy health gradually increase.

## Architecture & Game States

- **Main Menu State:** Title screen with a "Start Game" option.
  - Refer to [`main_menu.md`](./main_menu.md) for more details.
- **Playing State:** The core survival loop.
- **Boon State:** The paused boons screen where the player can upgrade in each milestone.
- **Game Over State:** Displays final score and a prompt to restart.
