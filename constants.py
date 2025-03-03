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

# Enemy Action and Spawn
ENEMY_SPAWN_WEIGHTS = [0.0, 0.0, 0.0, 1.0]
ENEMY_FIRE_RANGE = 1700
ENEMY_VISUAL_RANGE = 5000
ENEMY_ACTION_TIMER = 6
ENEMY_ACTION_WEIGHTS = [0.7, 0.3]

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
ATTACK_RANGE = 150.0  # Optimal firing range
RETREAT_HEALTH = 30.0  # Health threshold to consider retreating
FLANK_DISTANCE = 100.0  # Distance to maintain when flanking
PATROL_RADIUS = 200.0  # Radius of patrol pattern


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
