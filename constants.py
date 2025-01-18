"""Staging-grounds for the constans"""

from pygame.math import Vector2 as Vec2

# Switch between the modes, in test mode you can't die, the world is smaller, etc.
SMALL_MODE = True
MULTI_MODE = False
ORBIT_MODE = True
INVINCIBLE_MODE = False

SCREEN_SIZE = Vec2(1400, 700)
MINIMAP_SIZE = Vec2(350, 350)
WORLD_SIZE = Vec2(10_000, 10_000) if SMALL_MODE else Vec2(30_000, 30_000)
SPAWNPOINT = WORLD_SIZE / 2

# ship constants
BULLET_SPEED = 700
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius
DAMAGE_INDICATOR_TIME = 1  # How long a ship should glow after taking damage
GUN_COOLDOWN = 0.05  #  for the player only

# BulletEnemy constants
ENEMY_SHOOT_RANGE = 1700
ENEMY_VISUAL_RANGE = 5000
ENEMY_THRUST_MULTIPLIER = 0.3
ENEMY_ACTION_TIMER = 6
ENEMY_HEALTH = 100  # ???
ENEMY_ACTION_WEIGHTS = [0.7, 0.3]
ENEMY_BULLET_COOLDOWN = 0.1

# RocketEnemy constants
ENEMY_ROCKET_COOLDOWN = 0.2
ROCKET_HOMING_DURATION = 3
ROCKET_NONHOMING_DURATION = 5
ROCKET_HOMING_THRUST = 200

# MissileEnemy constants
ENEMY_MISSILE_COOLDOWN = 2
MISSILE_HOMING_DURATION = 20
MISSILE_HOMING_THRUST = 300
MISSILE_PREFERRED_SPEED = 300

# physics constants
GRAVITATIONAL_CONSTANT = 0.1
SMOL = 1e-3  # Small number to avoid division by zero
BOUNCINESS = 0.92  # 0 <= BOUNCINESS <= 1. Set to 1, collisions cause no damage.
BOUNCE_DAMAGE_THRESHOLD = 1.3e6
# if impulse scalar is smaller than this collisions cause no damage.
BOUNCE_DAMAGE_SCALAR = 6e-4

# Asteroid related constants
ASTS_PER_PLANET = 15
AST_MIN_SIZE = 20
AST_RADIUS_PARAM = 0.05
AST_ORBIT_PARAM = 0.0037
AST_ORBIT_MAX_ELIPSIS_LENGTH = 9000

# Number of enemies in the game
NUMBER_OF_ENEMIES = 8 if SMALL_MODE else 20
