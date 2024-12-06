"""Staging-grounds for the constans"""

from pygame.math import Vector2 as Vec2

# Switch between the two modes, in test mode you can't die, the world is smaller, etc.
TEST_MODE = True

SCREEN_SIZE = Vec2(1600, 900)
MINIMAP_SIZE = Vec2(350, 350)
WORLD_SIZE = Vec2(10_000, 10_000) if TEST_MODE else Vec2(30_000, 30_000)
SPAWNPOINT = Vec2(5_000, 5_000) if TEST_MODE else Vec2(20_000, 20_000)

# ship constants
BULLET_SPEED = 700
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius
DAMAGE_INDICATOR_TIME = 0.75  # How long a ship should glow after taking damage

GUN_COOLDOWN = 0.2

# BulletEnemy constants
ENEMY_SHOOT_RANGE = 1900
ENEMY_THRUST_MULTIPLIER = 0.2
ENEMY_ACTION_TIMER = 10
ENEMY_HEALTH = 100
ENEMY_ACTION_WEIGHTS = [1, 0, 0]
ENEMY_ROCKET_COOLDOWN = 4

# physics constants
GRAVITATIONAL_CONSTANT = 0.03
SMOL = 1e-3  # Small number to avoid division by zero
BOUNCINESS = 0.97  # 0 <= BOUNCINESS <= 1. Set to 1, collisions cause no damage.
BOUNCE_DAMAGE_THRESHOLD = 1.3e6
# if impulse scalar is smaller than this collisions cause no damage.
BOUNCE_DAMAGE_SCALAR = 6e-4

# Constants for main, where these objects are created
NUMBER_OF_ASTEROIDS = 40
NUMBER_OF_ENEMIES = 20
ASTEROID_MIN_SIZE = 20
ASTEROID_MAX_SIZE = 80
