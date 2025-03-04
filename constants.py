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


# ship constants
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius
HEALTH = 100
DAMAGE_INDICATOR_TIME = 1
"""Time (in seconds) a ship should flash red after taking damage"""
NUM_FLARES = 40
SD_FLARE_ANGLE = 25
FLARE_COLOR = Color("yellow")

# Enemy Action and Spawn
ENEMY_SPAWN_WEIGHTS = [0.3, 0.3, 0.2, 0.2]
ENEMY_FIRE_RANGE = 1700
ENEMY_VISUAL_RANGE = 5000
ENEMY_ACTION_TIMER = 6
ENEMY_ACTION_WEIGHTS = [0.7, 0.3]


GRAY = Color("gray")
PLAYER_COLOR = Color("green")
BULLET_ENEMY_COLOR = Color("lightblue")
ROCKET_ENEMY_COLOR = Color("purple")
MISSILE_ENEMY_COLOR = Color("lime")
MARKOV_ENEMY_COLOR = Color("red")


# Added speed at release
BULLET_RELEASE_SPEED = 700.0
ROCKET_RELEASE_SPEED = 300.0
FLARE_MEAN_RELEASE_SPEED = 140
FLARE_SD_RELEASE_SPEED = 28
# Damage
BULLET_DAMAGE = 16
ROCKET_DAMAGE = 26
MISSILE_DAMAGE = 60
FLAIR_DAMAGE = 10
# Rate of fire
BULLET_ROF = 0.08
ROCKET_ROF = 0.5
MISSILE_ROF = 3.0
FLARE_ROF = 5.0
# Thrust
ROCKET_HOMING_THRUST = 300.0
MISSILE_HOMING_THRUST = 600.0
# Homing
ROCKET_HOMING_DURATION = 2.0
ROCKET_NONHOMING_DURATION = 2.0
MISSILE_HOMING_DURATION = 20.0

ROCKET_TIMES_HOMES = 3
ROCKET_MIN_SPEED = 500.0

# Constants for state transitions
RETREAT_HEALTH = 30.0
ENEMY_ACCELERATE_LESS = 500
DESIRED_APPROACH_SPEED = 500

# physics constants
GRAVITATIONAL_CONSTANT = 0.2
EPSILON = 1e-8
BOUNCINESS = 0.7
"""0 <= BOUNCINESS <= 1. Set to 1, collisions cause no damage."""

BOUNCE_DAMAGE_THRESHOLD = 1.3e6
"""Impulse-scalar gets reduced by this (and clamped from negative to 0) before calculating damage."""

BOUNCE_DAMAGE_SCALAR = 1e-4
"""Bounce-damage is scaled by this amount."""


# Asteroid related constants
ASTEROIDS_PER_PLANET = 5
ASTEROID_SIZE_MIN = 20
# these are parameters for exponential distributions
ASTEROID_RADIUS_PARAMETER = 0.05  # of the radii
ASTEROID_ORBIT_PARAMETER = 0.0004  # orbit sizes
ASTEROID_ELLIPSIS_PARAMETER = 0.0001  # and orbit ellipticities

GRID_COLOR = Color("darkgreen")

GRID_COLOR = Color("darkgreen")


def generate_complementary_color(base_color: Color) -> Color:
    """Generate a complementary bullet color based on a color."""
    # Convert RGB to HSV
    r, g, b = base_color.r / 255.0, base_color.g / 255.0, base_color.b / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    delta = max_val - min_val

    # Calculate hue
    if delta == 0:
        h = 0  # Grayscale
    elif max_val == r:
        h = ((g - b) / delta) % 6
    elif max_val == g:
        h = (b - r) / delta + 2
    else:  # max_val == b
        h = (r - g) / delta + 4

    h = (h * 60) % 360

    # Calculate saturation
    s = 0 if max_val == 0 else delta / max_val

    # Calculate value
    v = max_val

    # For bullet color:
    # 1. Shift hue by 180° for complementary color
    # 2. Increase brightness for better visibility
    new_h = (h + 180) % 360
    new_s = min(1.0, s * 1.2)  # Slightly more saturated
    new_v = min(1.0, v * 1.3)  # Slightly brighter

    # Convert back to RGB
    h_i = int(new_h / 60)
    f = new_h / 60 - h_i
    p = new_v * (1 - new_s)
    q = new_v * (1 - f * new_s)
    t = new_v * (1 - (1 - f) * new_s)

    if h_i == 0:
        r, g, b = new_v, t, p
    elif h_i == 1:
        r, g, b = q, new_v, p
    elif h_i == 2:
        r, g, b = p, new_v, t
    elif h_i == 3:
        r, g, b = p, q, new_v
    elif h_i == 4:
        r, g, b = t, p, new_v
    else:
        r, g, b = new_v, p, q

    return Color(int(r * 255), int(g * 255), int(b * 255))
