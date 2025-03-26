"""Constants for the game."""

# TODO: Once all ships adopt MarkovAI, these constanst are probably only needed in one module, so then
# we can inline them there.
ENEMY_FIRE_RANGE_SQUARED = 1700**2
ENEMY_VISUAL_RANGE_SQUARED = 2000**2
ENEMY_ACTION_TIMER = 6


# Added speed at release
BULLET_RELEASE_SPEED = 700.0
ROCKET_RELEASE_SPEED = 300.0
FLARE_MEAN_RELEASE_SPEED = 140
FLARE_SD_RELEASE_SPEED = 28


GRAVITATIONAL_CONSTANT = 0.02
