class DifficultyDirector:
    def __init__(self) -> None:
        self.level: int = 1
        self.base_spawn_cooldown: float = 2.0
        self.current_spawn_cooldown: float = self.base_spawn_cooldown

    def increase_level(self) -> None:
        self.level += 1
        self.current_spawn_cooldown = self.base_spawn_cooldown * (0.9 ** (self.level - 1))

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
