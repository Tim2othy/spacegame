from __future__ import annotations

import random


import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2


"""
All the constants, differentiating between test and playmode, and listing the planets .etc are here.
Hopefully this makes main.py more compact and doesn't add any confusion
"""

TEST_MODE = True

SCREEN_SIZE = Vec2(1600, 900)
MINIMAP_SIZE = Vec2(350, 350)
WORLD_SIZE = Vec2(10_000, 10_000) if TEST_MODE else Vec2(30_000, 30_000)
SPAWNPOINT = Vec2(5_000, 5_000) if TEST_MODE else Vec2(20_000, 20_000)


# ship constants
BULLET_SPEED = 1500
GUNBARREL_LENGTH = 3  # relative to radius
GUNBARREL_WIDTH = 0.5  # relative to radius
ENEMY_SHOOT_RANGE = 1900
DAMAGE_INDICATOR_TIME = 0.75  # How long a ship should glow after taking damage

# physics constants
GRAVITATIONAL_CONSTANT = 0.03
SMOL = 1e-3  # Small number to avoid division by zero
BOUNCINESS = 0.97  # 0 <= BOUNCINESS <= 1. Set to 1, collisions cause no damage.
BOUNCE_DAMAGE_THRESHOLD = 1.3e6
# if impulse scalar is smaller than this collisions cause no damage.
BOUNCE_DAMAGE_SCALAR = 6e-4

# Constants only being used here
NUMBER_OF_ASTEROIDS = 40
NUMBER_OF_ENEMIES = 20
ASTEROID_MIN_SIZE = 20
ASTEROID_MAX_SIZE = 80
