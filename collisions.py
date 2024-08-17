import pygame
import sys
import math
import random
import time
import numpy as np
from math import atan2, cos, sin, sqrt


from ship import Ship
from bullet import Bullet
from planets import Planet


from calcu import distance, vec_add, vec_scale, sign


def check_bullet_planet_collision(bullet, planets):
    for planet in planets:
        if distance(bullet.pos, planet.pos) < planet.radius:
            return True
    return False

def check_bullet_asteroid_collision(bullet, asteroids):
    for asteroid in asteroids:
        if distance(bullet.pos, asteroid.pos) < asteroid.radius:
            return True
    return False

