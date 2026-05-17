"""Game constants for the fighting game logic server."""

MAX_HP: int = 100
TICK_RATE: int = 30
INVINCIBLE_FRAMES: int = 20
CHIP_DAMAGE: int = 2

DAMAGE_TABLE: dict[str, int] = {
    "punch_left": 10,
    "punch_right": 10,
    "kick": 20,
    "block": 0,
    "idle": 0,
    "jump": 0,
}

ATTACK_ACTIONS: set[str] = {"punch_left", "punch_right", "kick"}
