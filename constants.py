"""Constants for the game.

TODO: We should put most of these into their respective modules.
"""

from pygame import Color
from pygame.math import Vector2 as Vec2

SCREEN_SIZE = Vec2(1700, 900)
MINIMAP_SIZE = Vec2(400, 400)
FPS_HISTORY_LENGTH = 180  # how many frames to keep for FPS calculation
MINIMAP_BORDER_COLOR = Color("aquamarine")

# planet constants
PLANET_RADIUS_MU = 6.2
PLANET_RADIUS_SIGMA = 0.2
PLANET_COLORS_SMALL = []
PLANET_COLORS_LARGE = [
    Color("khaki"),
    Color("darkred"),
    Color("royalblue"),
    Color("mediumpurple"),
    Color("darkslategray"),
    Color("darkgreen"),
    Color("crimson"),
    Color("coral"),
    Color("blue"),
    Color("green"),
    Color("yellow"),
    Color("turquoise"),
    Color("deeppink"),
    Color("darkorange"),
    Color("lightblue"),
    Color("plum"),
    Color("slategray"),
    Color("navy"),
]


# Enemy Action and Spawn
ENEMY_SPAWN_WEIGHTS = [0.3, 0.3, 0.2, 0.2]
ENEMY_FIRE_RANGE_SQUARED = 1700**2
ENEMY_VISUAL_RANGE_SQUARED = 2000**2
ENEMY_ACTION_TIMER = 6
ENEMY_ACTION_WEIGHTS = [0.7, 0.3]


PLAYER_COLOR = Color("darkslategray")
PLAYER_2_COLOR = Color("darkred")
THRUST_COLOR = Color("orange")


# Added speed at release
BULLET_RELEASE_SPEED = 700.0
ROCKET_RELEASE_SPEED = 300.0
FLARE_MEAN_RELEASE_SPEED = 140
FLARE_SD_RELEASE_SPEED = 28


# Constants for state transitions
RETREAT_HEALTH = 30.0
DESIRED_APPROACH_SPEED = 500

GRAVITATIONAL_CONSTANT = 0.2
EPSILON = 1e-8

ASTEROIDS_PER_PLANET = 5


GRID_COLOR = Color("darkgreen")


def generate_complementary_color(base_color: Color) -> Color:
    """Generate a complementary bullet color based on a color.

    >>> generate_complementary_color(Color("red"))  # should return cyan
    Color(0, 255, 255, 255)
    >>> generate_complementary_color(Color("white"))  # should return white
    Color(255, 255, 255, 255)
    >>> generate_complementary_color(Color(0, 128, 0))  # dark green, should return violet
    Color(166, 0, 166, 255)
    """
    h, s, v, a = base_color.hsva

    new_h = (h + 180) % 360  # Shift hue by 180° for complementary color
    new_s = min(100, s * 1.2)  # Slightly more saturated
    new_v = min(100, v * 1.3)  # Slightly brighter

    return Color.from_hsva(new_h, new_s, new_v, a)  # type: ignore  # noqa: PGH003
