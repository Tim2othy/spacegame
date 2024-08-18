import numpy as np


def distance(v, w):
    return np.linalg.norm(v - w)


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
