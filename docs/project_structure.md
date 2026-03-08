# ChronoFrost: Project Structure

## Overview

This document outlines the directory and file architecture for ChronoFrost. The project is structured to separate documentation, core game logic, throwaway testing scripts, and assets, ensuring a clean workspace for rapid game jam development.

## Directory Tree

```txt
ChronoFrost/
├── assets/                 # Game assets (empty by default due to procedural geometry)
│   ├── audio/              # Sound effects and background music (.wav, .ogg)
│   ├── fonts/              # Custom typography (.ttf, .otf)
│   └── sprites/            # Reserved for potential future image assets
├── docs/                   # Centralized project documentation
│   ├── boons.md            # Milestone upgrade logic
│   ├── main_menu.md        # UI and menu architecture
│   ├── powerups.md         # Field drops and active abilities
│   ├── project-structure.md# This file
│   └── requirements.md     # Master blueprint and core mechanics
├── entities/               # Core game objects and behaviors
│   ├── __init__.py
│   ├── player.py           # Player movement, aiming, and Chrono-Charge logic
│   ├── enemies.py          # Ice Cube AI and procedural bullet patterns
│   └── items.py            # Embers, Powerups, and collision logic
├── prototypes/             # Isolated sandbox scripts for testing mechanics
│   ├── throwaway_movement.py
│   └── throwaway_lighting.py
├── GEMINI.md               # Context and constraint directives for the Gemini CLI
├── main.py                 # Application entry point and State Machine manager
├── Pipfile                 # Pipenv dependency definitions
├── Pipfile.lock            # Pipenv deterministic build tree
└── requirements.txt        # Fallback dependency list for standard pip users
```
