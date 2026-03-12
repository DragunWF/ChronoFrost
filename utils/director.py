class DifficultyDirector:
    def __init__(self) -> None:
        self.level: int = 1
        # Lowered base cooldown from 2.0 to 1.0 to start with more enemies
        self.base_spawn_cooldown: float = 1.0
        # The lowest the spawn cooldown can go (caps the max spawn rate)
        self.min_spawn_cooldown: float = 0.2
        self.current_spawn_cooldown: float = self.base_spawn_cooldown

    def increase_level(self) -> None:
        self.level += 1
        # Modify the multiplier here (e.g., 0.8) to adjust how fast the difficulty ramps up.
        # Lower values make the spawn cooldown decrease faster, increasing difficulty quicker.
        calculated_cooldown = self.base_spawn_cooldown * \
            (0.8 ** (self.level - 1))
        # Cap the spawn cooldown so it never goes below min_spawn_cooldown
        self.current_spawn_cooldown = max(
            self.min_spawn_cooldown, calculated_cooldown)

    def get_spawn_weights(self) -> list[int]:
        if self.level <= 2:
            return [85, 10, 5]
        elif self.level <= 4:
            return [60, 25, 15]
        else:
            return [40, 30, 30]

    def get_ember_multiplier(self) -> float:
        return max(0.5, 1.0 - 0.05 * (self.level - 1))

    def get_spawn_cooldown(self) -> float:
        return self.current_spawn_cooldown
