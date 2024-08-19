import pygame
import pygame.camera
from pygame.math import Vector2
from physics import Disk
from ship import Ship, BulletEnemy


class Planet(Disk):
    """A stationary disk."""

    def __init__(
        self,
        pos: Vector2,
        density: float,
        radius: float,
        color: pygame.Color,
    ):
        super().__init__(pos, Vector2(0, 0), density, radius, color)


class Asteroid(Disk):
    """A gray disk that doesn't exert gravitational force."""

    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        density: float,
        radius: float,
    ):
        super().__init__(pos, vel, density, radius, pygame.Color("gray"))

    # TODO: Re-implement that the Asteroids stopped at the world-border.
    # Or should they wrap instead? Should *all* PhysicalObjects wrap?


class Universe:
    """A collection of celestial objects, forming a Universe."""

    def __init__(
        self,
        planets: list[Planet],
        asteroids: list[Asteroid],
        player_ship: Ship,
        enemy_ships: list[BulletEnemy],
    ):
        self.planets = planets
        self.asteroids = asteroids
        self.player_ship = Ship
        self.enemy_ships = BulletEnemy
