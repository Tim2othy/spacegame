"""A collection of celestial objects, forming a Universe."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import Disk, PhysicalObject
from profiler import global_profiler

if TYPE_CHECKING:
    from camera import Camera
    from ship import BulletEnemy, PlayerShip

from constants import (
    ASTEROID_ELLIPSIS_PARAMETER,
    ASTEROID_ORBIT_PARAMETER,
    ASTEROID_RADIUS_PARAMETER,
    ASTEROID_SIZE_MIN,
    FPS_HISTORY_LENGTH,
    GRAVITATIONAL_CONSTANT,
)


class Planet(Disk):
    """A stationary disk."""

    def __init__(
        self,
        pos: Vec2,
        radius: float,
        color: Color,
        density: float = 1,
    ) -> None:
        """Create a new planet.

        Args:
        ----
            pos (Vec2): Fixed position
            radius (float): Radius
            color (Color): Color
            density (float): Density

        """
        super().__init__(
            pos,
            Vec2(0, 0),
            density,
            radius,
            color,
        )


class Asteroid(Disk):
    """A gray disk that doesn't exert gravitational force, and isn't stationary."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        density: float,
        radius: float,
    ) -> None:
        """Create a new Asteroid.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            density (float): Density
            radius (float): Radius

        """
        super().__init__(pos, vel, density, radius, Color("gray"))


class Universe:
    """A collection of celestial objects, forming a Universe.

    Its width is size.x, its height is size.y.
    Coordinates are implicitly zero-based.
    """

    def __init__(
        self,
        size: Vec2,
        planets: list[Planet],
        player_ships: list[PlayerShip],
        enemy_ships: list[BulletEnemy],
        parallax_background_paths: list[str],
    ) -> None:
        """Create a new universe (not in the big-bang way, sadly).

        Args:
        ----
            size (Vec2): Width and height
            planets (list[Planet]): Planets
            asteroids (list[Asteroid]): Asteroids but starts out empty
            player_ships (list[Ship]): List of player-ships
            enemy_ships (list[BulletEnemy]): Enemy fleet
            parallax_background_paths (list[str]): Paths to
                background-images,increasingly far away

        """
        self.size = Vec2(size)
        self._planets = planets
        self.asteroids: list[Asteroid] = []
        self.player_ships = player_ships
        self.enemy_ships = enemy_ships
        self.parallax_backgrounds = [
            pygame.image.load(path).convert_alpha() for path in parallax_background_paths
        ]

    def apply_gravity_to_obj(self, dt: float, pobj: PhysicalObject) -> None:
        """Affect pobj by `self`'s entire gravity.

        Args:
        ----
            dt (float): Passed time
            pobj (PhysicalObject): Object to affect

        """
        force_sum = Vec2(0, 0)
        for body in self._planets:
            force_sum += pobj.gravitational_force(body)
        pobj.apply_force(force_sum, dt)

    def apply_gravity(self, dt: float) -> None:
        """Apply gravity to all of `self`'s objects.

        Args:
        ----
            dt (float): Passed time

        """
        for pobj in self.player_ships + self.enemy_ships + self.asteroids:
            self.apply_gravity_to_obj(dt, pobj)

    def apply_bounce(self) -> None:
        """Run all bounce-interactions within `self`."""
        # Bounce-Hierarchy:
        # player_ships > enemy_ships > asteroids
        # Planets are separate.

        # Bounce player_ships
        for player in self.player_ships:
            # For now, don't bounce player-ships off of other player-ships
            for body in self.enemy_ships + self.asteroids:
                if damage := player.bounce_disks(body) is not None:
                    player.suffer_damage(damage)
            for planet in self._planets:
                if damage := player.bounce_off_of_disk(planet) is not None:
                    player.suffer_damage(damage)

        # Bounce enemy_ships
        for ix, enemy_ship in enumerate(self.enemy_ships):
            # But it *is* fun to bounce enemies off of each other
            for body in self.enemy_ships[ix + 1 :] + self.asteroids:
                # TODO: Once enemies have proper health, they should probably suffer damage, too
                enemy_ship.bounce_disks(body)
            for planet in self._planets:
                # TODO: Once enemies have proper health, they should probably suffer damage, too
                enemy_ship.bounce_off_of_disk(planet)

        # Bounce asteroids
        for ix, asteroid in enumerate(self.asteroids):
            for body in self.asteroids[ix + 1 :]:
                asteroid.bounce_disks(body)
            for planet in self._planets:
                asteroid.bounce_off_of_disk(planet)

    def asteroids_or_planets_intersect_point(self, vec: Vec2) -> bool:
        """Test whether any of `self`'s planets or asteroids intersect `vec`.

        Args:
        ----
            vec (Vec2): Position to test for intersection

        Returns:
        -------
            bool: True iff any intersect

        """
        return any(planet.intersects_point(vec) for planet in self._planets) or any(
            asteroid.intersects_point(vec) for asteroid in self.asteroids
        )

    def collide_bullets(self) -> None:
        """Run bullet-collision checks and damage ships as a result."""

        # TODO: Use memory-hack to make bullet-removal faster, use indices and python's analogue
        # of https://doc.rust-lang.org/std/vec/struct.Vec.html#method.swap_remove
        for player_ship in self.player_ships:
            for projectile in player_ship.projectiles:
                if self.asteroids_or_planets_intersect_point(
                    projectile.pos,
                ) or not self.contains_point(projectile.pos):
                    player_ship.projectiles.remove(projectile)
                    continue
                for enemy_ship in self.enemy_ships:
                    if enemy_ship.intersects_point(projectile.pos):
                        self.enemy_ships.remove(enemy_ship)
                        player_ship.projectiles.remove(projectile)
                        break
        for enemy_ship in self.enemy_ships:
            for projectile in enemy_ship.projectiles:
                if self.asteroids_or_planets_intersect_point(
                    projectile.pos,
                ) or not self.contains_point(projectile.pos):
                    enemy_ship.projectiles.remove(projectile)
                    continue
                for player_ship in self.player_ships:
                    if player_ship.intersects_point(projectile.pos):
                        player_ship.suffer_damage(5)
                        enemy_ship.projectiles.remove(projectile)
                        break

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Run input-logic for player-ships.

        Args:
        ----
            keys (pygame.key.ScancodeWrapper): Pressed keys

        """
        for player_ship in self.player_ships:
            player_ship.handle_input(keys)

    def move_camera(self, camera: Camera, player_ix: int, dt: float) -> None:
        """Move the camera to `self.player_ships[player_ix]`.

        Args:
        ----
            camera (Camera): Camera to move
            player_ix (int): Player to focus on
            dt (float): Passed time

        """
        ship = self.player_ships[player_ix]
        camera.smoothly_focus_points(
            [ship.pos, ship.pos + 1.0 * ship.vel],
            500,
            dt,
        )

    @global_profiler.profile_method
    def step(self, dt: float) -> None:
        """Run the universe-logic, also for the object `self` contains.

        Args:
        ----
            dt (float): Passed time

        """
        # Call `step` on everything
        for ship in self.player_ships + self.enemy_ships:
            ship.step(dt)
        for asteroid in self.asteroids:
            asteroid.step(dt)

        # Physics
        self.apply_gravity(dt)
        self.apply_bounce()
        self.collide_bullets()

    @global_profiler.profile_method
    def draw_background(self, camera: Camera) -> None:
        """Draw `self`'s parallaxing background on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        zoom = camera.zoom
        screenspace_size = camera.surface.get_size()
        camera_pos_x = -camera.pos.x * zoom
        camera_pos_y = -camera.pos.y * zoom
        background_count = len(self.parallax_backgrounds)

        for ix, background in enumerate(self.parallax_backgrounds):
            scaled_background = pygame.transform.smoothscale_by(background, zoom)
            (bg_width, bg_height) = Vec2(background.get_size()) * zoom

            draw_start_x = (camera_pos_x / (background_count - ix + 0.5) % bg_width) - bg_width
            draw_start_y = (camera_pos_y / (background_count - ix + 0.5) % bg_height) - bg_height
            repeat_x = math.ceil(screenspace_size[0] / bg_width) + 2
            repeat_y = math.ceil(screenspace_size[1] / bg_height) + 2

            for i in range(repeat_x):
                for j in range(repeat_y):
                    x = int(draw_start_x + i * bg_width)
                    y = int(draw_start_y + j * bg_height)
                    camera.surface.blit(scaled_background, (x, y))

    @global_profiler.profile_method
    def draw(self, camera: Camera) -> None:
        """Draw all of `self` on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        for pobj in self.asteroids + self._planets + self.enemy_ships + self.player_ships:
            pobj.draw(camera)

    @global_profiler.profile_method
    def draw_text(self, camera: Camera, player_ix: int, fps: float) -> None:
        """Draw "debugging" text on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on
            player_ix (int): Player to display information about
            fps (float): Current fps

        """
        font_size = 32
        font = pygame.font.Font(None, font_size)

        def texty(vertical_offset: int, text: str | None = None) -> int:
            if text is not None:
                camera.draw_text(
                    text,
                    Vec2(10, vertical_offset),
                    font,
                    Color("white"),
                )
            return vertical_offset + font_size

        text_v = 10
        player_ship = self.player_ships[player_ix]
        text_v = texty(text_v, f"{fps:.0f} fps (average over past {FPS_HISTORY_LENGTH} frames)")
        text_v = texty(text_v, f"Fuel: {player_ship.fuel:.0f}")
        text_v = texty(text_v, f"Health: {player_ship.health:.0f}")
        text_v = texty(text_v, f"Ammunition: {player_ship.ammo}")

        enemy_count = len(self.enemy_ships)
        texty(text_v, f"Enemies left: {enemy_count}")

    @global_profiler.profile_method
    def draw_grid(self, camera: Camera) -> None:
        """Draw grid on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        grid_color = Color("darkgreen")
        gridline_spacing = 500
        width = self.size.x
        height = self.size.y

        for x in range(0, int(width + 1), gridline_spacing):
            camera.draw_vertical_hairline(grid_color, x, 0, height)

        for y in range(0, int(height + 1), gridline_spacing):
            camera.draw_horizontal_hairline(grid_color, 0, width, y)

    def contains_point(self, vec: Vec2) -> bool:
        """Test whether `vec` is contained in `self`'s boundaries.

        Args:
        ----
            vec (Vec2): Vec to test for containment

        Returns:
        -------
            bool: True iff `self` contains `vec`

        """
        return 0 <= vec.x <= self.size.x and 0 <= vec.y <= self.size.y

    def clamp_point(self, vec: Vec2) -> Vec2:
        """Return `vec` clamped to be within `self`'s bounds.

        Args:
        ----
            vec (Vec2): Point to clamp into `self`

        Returns:
        -------
            Vec2: The clamped point. Unchanged if it already was in `self`.

        """
        return Vec2(max(0, min(self.size.x, vec.x)), max(0, min(self.size.y, vec.y)))

    def generate_asteroid(self, planet: Planet) -> None:
        """Create an asteroid orbiting a planet.

        Args:
        ----
            planet (Planet): The planet to orbit

        What the random variables do:
        - radius_asteroid - pretty obvious
        - r_a             - shortest distance to planet during orbit
        - r_p             - largest distance to planet during orbit
        - true_anomaly    - where along it's orbit it starts, as in near r_a or near r_p or so
        - orbit_direction - in which direction (in degrees) of the planet it starts
        - asteroid_angle  - does it go clockwise or anticlockwise

        """
        # random variables
        asteroid_radius_lambda = 1 / (ASTEROID_RADIUS_PARAMETER * planet.radius)
        radius_asteroid = ASTEROID_SIZE_MIN + random.expovariate(asteroid_radius_lambda)
        r_p = planet.radius + radius_asteroid + random.expovariate(ASTEROID_ORBIT_PARAMETER)
        r_a = r_p + random.expovariate(ASTEROID_ELLIPSIS_PARAMETER)
        true_anomaly = random.uniform(0, 2 * math.pi)
        orbit_direction = random.uniform(0, 2 * math.pi)
        asteroid_angle = random.choice([90, 270])

        # pos_asteroid
        semi_major_axis = (r_p + r_a) / 2
        eccentricity = (r_a - r_p) / (r_a + r_p)
        r_initial = (semi_major_axis * (1 - eccentricity**2)) / (1 + eccentricity * math.cos(true_anomaly))
        radial_vector = Vec2(1, 0).rotate(math.degrees(true_anomaly + orbit_direction))
        pos_asteroid = planet.pos + radial_vector * r_initial

        # velocity_asteroid
        total_specific_energy = -GRAVITATIONAL_CONSTANT * planet.mass / (2 * semi_major_axis)
        orbital_velocity = (
            2 * (GRAVITATIONAL_CONSTANT * planet.mass / r_initial + total_specific_energy)
        ) ** 0.5
        tangential_vector = radial_vector.rotate(asteroid_angle)
        velocity_asteroid = tangential_vector * orbital_velocity

        self.asteroids.append(
            Asteroid(pos_asteroid, velocity_asteroid, 1, radius_asteroid),
        )
