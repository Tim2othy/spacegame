"""Staging-grounds for the constans"""

from pygame.math import Vector2 as Vec2

SCREEN_SIZE = Vec2(1400, 700)
MINIMAP_SIZE = Vec2(350, 350)

# planet constants
PLANET_RADIUS_MU = 6.2
PLANET_RADIUS_SIGMA = 0.2

# ship constants
BULLET_SPEED = 700
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius
DAMAGE_INDICATOR_TIME = 1  # How long a ship should glow after taking damage
GUN_COOLDOWN = 0.05  #  for the player only

# BulletEnemy constants
ENEMY_SHOOT_RANGE = 1700
ENEMY_VISUAL_RANGE = 5000
ENEMY_THRUST_MULTIPLIER = 0.3  # relative to player
ENEMY_ACTION_TIMER = 6
ENEMY_HEALTH = 100  # ???
ENEMY_ACTION_WEIGHTS = [0.7, 0.3]
ENEMY_BULLET_COOLDOWN = 0.1

# RocketEnemy constants
ENEMY_ROCKET_COOLDOWN = 0.2
ROCKET_HOMING_DURATION = 3.0
ROCKET_NONHOMING_DURATION = 5.0
ROCKET_HOMING_THRUST = 200.0

# MissileEnemy constants
ENEMY_MISSILE_COOLDOWN = 2.0
MISSILE_HOMING_DURATION = 20.0
MISSILE_HOMING_THRUST = 100.0
MISSILE_PREFERRED_SPEED = 500.0

# physics constants
GRAVITATIONAL_CONSTANT = 0.2
SMOL = 1e-3  # Small number to avoid division by zero
BOUNCINESS = 0.7  # 0 <= BOUNCINESS <= 1. Set to 1, collisions cause no damage.
BOUNCE_DAMAGE_THRESHOLD = 1.3e6
# if impulse scalar is smaller than this collisions cause no damage.
BOUNCE_DAMAGE_SCALAR = 1e-4

# Asteroid related constants
ASTS_PER_PLANET = 5
AST_MIN_SIZE = 20
# these are parameters for exponential distributions
AST_RADIUS_PARAM = 0.05  # of the radii
AST_ORBIT_PARAM = 0.0004  # orbit sizes
AST_ELLIPSIS_PARAM = 0.0001  # and orbit ellipticities
