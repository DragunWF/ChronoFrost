# ChronoFrost: Powerups & Upgrades Documentation

This document outlines the various buffs and enhancements the player can acquire during a run. The system is split into two categories: **Field Drops** (temporary powerups that spawn during gameplay) and **Milestone Upgrades** (permanent stat boosts purchased in the Shop).

---

## 1. Field Drops (Active Powerups)

Field drops appear randomly when destroying Ice Cubes. They must be picked up by the player to activate and provide immediate, situational advantages to survive bullet-hell waves.

- **Thermal Shield (Gold)**
  - **Effect:** Grants a glowing protective aura around the player. Absorbs exactly one instance of bullet or collision damage.
  - **Feedback:** When broken, the shield shatters with a localized screen-shake and a sharp glass-breaking visual effect, granting 0.5 seconds of invincibility.
- **Flash-Step (Magenta)**
  - **Effect:** Grants a single-use, high-speed dash (activated via `SHIFT`).
  - **Utility:** During the dash, the player has i-frames (invincibility frames) and can pass safely through dense walls of enemy bullets or through enemies themselves without taking damage.

- **Supernova (White)**
  - **Effect:** Acts as a "Smart Bomb." Upon pickup, it instantly emits a massive white shockwave across the entire screen.
  - **Utility:** Vaporizes all active enemy projectiles on the screen and pushes all surviving enemies back toward the edges, giving the player vital breathing room.

- **Chrono-Surge (Cyan)**
  - **Effect:** Instantly refills the Chrono-Freeze meter to 100% capacity.
  - **Utility:** Allows for back-to-back uses of time dilation during overwhelming waves without needing to aggressively hunt for Embers.

---

## 2. Milestone Upgrades (The Shop)

When the player reaches specific score thresholds (e.g., 1000, 2000, 3000 points), the game pauses and the Upgrade Shop appears. The player selects one of three random permanent enhancements.

### Combat Upgrades

- **+1 Pierce:** Player bullets now pass through the first enemy they hit, dealing damage to a second enemy behind them. Can be stacked multiple times for crowd control.
- **Rapid Fire:** Decreases the weapon's cooldown timer (e.g., from 0.25s to 0.20s), allowing the player to shoot significantly faster.
- **Spread Shot:** Adds additional projectiles to each shot (e.g., transitioning from a single straight shot to a 3-way spread), drastically increasing hit probability.
- **Heavy Caliber:** Increases the physical size and damage of player bullets, allowing them to destroy larger Ice Cubes in fewer hits, but slightly reduces bullet travel speed.

### Utility & Survival Upgrades

- **Deep Freeze (Capacity):** Increases the maximum capacity of the Chrono-Freeze meter by +50. Allows the time-slow effect to be maintained for much longer durations.
- **Ember Magnet:** Increases the pickup radius for Thermal Embers and Powerups, meaning the player doesn't have to risk flying as close to enemy clusters to refuel.
- **Kinetic Plating:** Increases the player's starting max lives by +1.
- **Overclock (Ember Efficiency):** Every Thermal Ember collected restores 20% more energy to the Chrono-Freeze meter.
