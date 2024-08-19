import math
import pygame
import pygame.camera
from pygame.math import Vector2
from physics import Disk, PhysicalObject
from ship import Ship, BulletEnemy
from camera import Camera


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
    """
    A collection of celestial objects, forming a Universe.

    Its width is size.x, its height is size.y.
    Coordinates are implicitly zero-based.
    """

    def __init__(
        self,
        size: Vector2,
        planets: list[Planet],
        asteroids: list[Asteroid],
        player_ship: Ship,
        enemy_ships: list[BulletEnemy],
    ):
        self.size = size
        self.planets = planets
        self.asteroids = asteroids
        self.player_ship = player_ship
        self.enemy_ships = enemy_ships

    def apply_gravity_to_obj(self, dt: float, pobj: PhysicalObject):
        force_sum = Vector2(0, 0)
        for body in self.planets:
            force_sum += pobj.gravitational_force(body)
        pobj.apply_force(force_sum, dt)

    def apply_gravity(self, dt: float):
        self.apply_gravity_to_obj(dt, self.player_ship)
        for enemy_ship in self.enemy_ships:
            self.apply_gravity_to_obj(dt, enemy_ship)
        for asteroid in self.asteroids:
            self.apply_gravity_to_obj(dt, asteroid)

    def apply_bounce_to_disk(self, disk: Disk) -> float | None:
        for body in self.asteroids + self.planets:
            bounce = disk.bounce_off_of_disk(body)
            if bounce is not None:
                return bounce
        return None

    def apply_bounce(self):
        ship_bounce = self.apply_bounce_to_disk(self.player_ship)
        if ship_bounce is not None:
            # TODO: Reimplement ship glowing red on impact
            # TODO: Adjust this to taste.
            # Also, should we really cast a sqrt here?
            # Check the bounce_off_of_disk method please,
            # I don't understand its code, but it decides
            # what value to return for the impact-intensity,
            # i.e. the bounce-variable.
            damage = math.sqrt(ship_bounce) / 500
            self.player_ship.health -= damage
        for enemy_ship in self.enemy_ships:
            self.apply_bounce_to_disk(enemy_ship)
        for asteroid in self.asteroids:
            # TODO: This is an *asymmetric* interaction.
            # If two asteroids collide, only one of them will bounce,
            # because when the second tries to bounce, the two will already
            # have been separated from one another
            other_asteroids = list(filter(lambda ast: ast != asteroid, self.asteroids))
            for disk in other_asteroids + self.planets:
                asteroid.bounce_off_of_disk(disk)

    def asteroids_or_planets_intersect_point(self, vec: Vector2):
        return any(
            map(lambda planet: planet.intersects_point(vec), self.planets)
        ) or any(map(lambda asteroid: asteroid.intersects_point(vec), self.asteroids))

    def step(self, dt: float):
        # Call `step` on everything
        self.player_ship.step(dt)
        for projectile in self.player_ship.projectiles:
            projectile.step(dt)
        for ship in self.enemy_ships:
            ship.step(dt)
            for projectile in ship.projectiles:
                projectile.step(dt)
        for asteroid in self.asteroids:
            asteroid.step(dt)

        self.apply_gravity(dt)
        self.apply_bounce()

        # Collide bullets:
        for projectile in self.player_ship.projectiles:
            if self.asteroids_or_planets_intersect_point(
                projectile.pos
            ) or not self.contains_point(projectile.pos):
                self.player_ship.projectiles.remove(projectile)
                continue
            for ship in self.enemy_ships:
                if ship.intersects_point(projectile.pos):
                    self.enemy_ships.remove(ship)
                    self.player_ship.projectiles.remove(projectile)
                    break
        for ship in self.enemy_ships:
            for projectile in ship.projectiles:
                if self.asteroids_or_planets_intersect_point(
                    projectile.pos
                ) or not self.contains_point(projectile.pos):
                    ship.projectiles.remove(projectile)
                    continue
                if self.player_ship.intersects_point(projectile.pos):
                    self.player_ship.health -= 10
                    ship.projectiles.remove(projectile)
                    continue

    def draw(self, camera: Camera):
        for asteroid in self.asteroids:
            asteroid.draw(camera)
        for planet in self.planets:
            planet.draw(camera)
        for ship in self.enemy_ships:
            ship.draw(camera)
            for projectile in ship.projectiles:
                projectile.draw(camera)
        for projectile in self.player_ship.projectiles:
            projectile.draw(camera)
        self.player_ship.draw(camera)

    def contains_point(self, vec: Vector2):
        return 0 <= vec.x <= self.size.x and 0 <= vec.y <= self.size.y

    def clamp_point(self, vec: Vector2):
        return Vector2(max(0, min(self.size.x, vec.x)), max(0, min(self.size.y, vec.y)))