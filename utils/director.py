class DifficultyDirector:
    def __init__(self) -> None:
        self.level: int = 1
        # The base cooldown for level 1 (after the initial grace period)
        self.base_spawn_cooldown: float = 1
        # The lowest the spawn cooldown can go (caps the max spawn rate)
        self.min_spawn_cooldown: float = 0.2
        self.current_spawn_cooldown: float = self.base_spawn_cooldown

    def increase_level(self) -> None:
        self.level += 1
        # Aggressive multiplier (0.75) so it starts slow but ramps up very quickly after level 1
        calculated_cooldown = self.base_spawn_cooldown * \
            (0.85 ** (self.level - 1))
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

    def get_spawn_cooldown(self, time_alive: float) -> float:
        # Give a slow, 5-second grace period at the beginning of the game
        if self.level == 1 and time_alive < 6.5:
            return 2.5
        # After 5 seconds, instantly snap to the fast ramp-up track
        return self.current_spawn_cooldown
