# ChronoFrost

A 2D top-down roguelite survival/bullet-hell game built entirely in Pygame. Relying strictly on primitive geometric shapes and fluid procedural patterns, _ChronoFrost_ tasks the player with surviving relentless waves of Ice Cubes by mastering the art of time manipulation.

## 🚀 Features Overview

- **Chrono-Freeze:** Drastically slow down time to weave through impossible bullet patterns.
- **Aggressive Economy:** Time manipulation drains your Chrono-Charge. Refuel it by destroying enemies and diving into danger to collect their Thermal Embers.
- **Milestone Augments:** Reaching score thresholds pauses the game, allowing you to draft permanent upgrades to customize your build.
- **Procedural Bullet Hell:** Enemies utilize trigonometry to fire expanding rings, double-spirals, and sweeping arcs that scale in difficulty the longer you survive.

## 📸 Screenshots

> _(Add your screenshots here!)_

## 📖 Documentation

For a deep dive into the mechanics, architecture, and feature sets, check out the project documentation located in the `docs/` directory:

- [**Game Requirements (`requirements.md`)**](./docs/requirements.md) - The master blueprint, detailing the core loop, scoring, entity behavior, and the state machine architecture.
- [**Project Structure** (`project_structure.md`)](./docs/project_structure.md) - The structure of directories and files in the project.
- [**Main Menu (`main_menu.md`)**](./docs/main_menu.md) - UI design philosophy, options/audio configurations, and procedural visual flair.
- [**Powerups (`powerups.md`)**](./docs/powerups.md) - Details on active "Field Drops" like the Thermal Shield, Flash-Step, and Supernova.
- [**Milestone Boons (`boons.md`)**](./docs/boons.md) - The complete list of offensive, defensive, and temporal permanent upgrades available during the draft phase.

## 🛠️ Setup & Installation

This project uses `pipenv` for dependency management to ensure a clean, isolated environment.

### Prerequisites

- Python 3.10+
- [Pipenv](https://pipenv.pypa.io/en/latest/) installed (`pip install pipenv`)

### Installation Steps

1. **Clone the repository:**

   ```bash
   git clone [https://github.com/yourusername/ChronoFrost.git](https://github.com/yourusername/ChronoFrost.git)
   cd ChronoFrost
   ```

2. **Install dependencies:**
   This will create a virtual environment and install Pygame (or pygame-ce) as specified in the Pipfile.

```bash
pipenv install
```

3. Run the game:
   Launch the game loop through the Pipenv shell.

```bash
pipenv run python main.py
```
