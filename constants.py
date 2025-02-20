"""Constants for the game.

TODO: We should put most of these into their respective modules.
"""

from pygame import Color
from pygame.math import Vector2 as Vec2

SCREEN_SIZE = Vec2(1400, 700)
MINIMAP_SIZE = Vec2(350, 350)
FPS_HISTORY_LENGTH = 180  # how many frames to keep for FPS calculation
MINIMAP_BORDER_COLOR = Color("aquamarine")

# planet constants
PLANET_RADIUS_MU = 6.2
PLANET_RADIUS_SIGMA = 0.2


# ship constants
BULLET_SPEED = 700
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius
DAMAGE_INDICATOR_TIME = 1
"""Time (in seconds) a ship should flash red after taking damage"""
GUN_COOLDOWN_PLAYER = 0.05


# BulletEnemy constants
ENEMY_SHOOT_RANGE = 1700
ENEMY_VISUAL_RANGE = 5000
ENEMY_THRUST_MULTIPLIER = 0.3  # relative to player
ENEMY_ACTION_TIMER = 6
ENEMY_HEALTH = 100  # TODO: Unused, ships die instantly
ENEMY_ACTION_WEIGHTS = [0.7, 0.3]
ENEMY_BULLET_COOLDOWN = 0.1


# RocketEnemy constants
ENEMY_ROCKET_COOLDOWN = 0.2
ROCKET_HOMING_DURATION = 2.0
ROCKET_NONHOMING_DURATION = 2.0
ROCKET_HOMING_THRUST = 1000.0


# MissileEnemy constants
ENEMY_MISSILE_COOLDOWN = 2.0
MISSILE_HOMING_DURATION = 20.0
MISSILE_HOMING_THRUST = 1000.0
MISSILE_PREFERRED_SPEED = 500.0


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
