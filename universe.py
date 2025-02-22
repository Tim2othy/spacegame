"""A collection of celestial objects, forming a Universe."""

from __future__ import annotations

import math
import random
from itertools import chain
from typing import TYPE_CHECKING

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import Disk, Particle, PhysicalObject
from profiler import global_profiler

if TYPE_CHECKING:
    from collections.abc import Iterator

    from camera import Camera
    from projectiles import Bullet
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

    def __init__(self, pos: Vec2, radius: float, color: Color, density: float = 1) -> None:
        """Create a new planet.

        Args:
            pos (Vec2): Fixed position
            radius (float): Radius
            color (Color): Color
            density (float): Density

        """
        super().__init__(pos, Vec2(0, 0), radius, color, density)


class Asteroid(Disk):
    """A gray disk that doesn't exert gravitational force, and isn't stationary."""

    def __init__(self, pos: Vec2, vel: Vec2, radius: float, density: float = 1) -> None:
        """Create a new Asteroid.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            radius (float): Radius
            density (float): Density

        """
        super().__init__(pos, vel, radius, Color(32, 32, 32), density)


type AsteroidChunk = tuple[int, int]
type PlanetChunk = tuple[int, int]


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
        max_nonplanet_size: float,
    ) -> None:
        """Create a new universe.

        Assumes planets are immutable.

        Assumes every asteroid and ship has an axis-aligned-bounding-box
        of size at most max_nonplanet_size. For disks, that means their diameter must not
        exceed max_nonplanet_size. If violated, collision-detection may ignore large objects.
        A smaller max_nonplanet_size speeds up collision-detection, so choose the smallest value
        possible.

        Raises a ValueError if any player-ship or enemy-ship is larger than max_nonplanet_size.

        Args:
            size (Vec2): Width and height
            planets (list[Planet]): Planets
            player_ships (list[Ship]): List of player-ships
            enemy_ships (list[BulletEnemy]): Enemy fleet
            max_nonplanet_size: float

        """
        self.size = Vec2(size)
        self.max_nonplanet_size = max_nonplanet_size

        if any(2 * ship.radius > max_nonplanet_size for ship in player_ships) or any(
            2 * ship.radius > max_nonplanet_size for ship in enemy_ships
        ):
            raise ValueError

        self._player_ships = player_ships
        self._enemy_ships = enemy_ships

        self._vec_to_asteroid_chunk = lambda vec: (
            math.floor(vec.x / max_nonplanet_size),
            math.floor(vec.y / max_nonplanet_size),
        )
        self._asteroid_chunks: dict[AsteroidChunk, list[Asteroid]] = {}

        planet_chunk_size = max(500, 2 * max([p.radius for p in planets], default=0))
        self._vec_to_planet_chunk = lambda vec: (
            math.floor(vec.x / planet_chunk_size),
            math.floor(vec.y / planet_chunk_size),
        )
        self._planet_chunks: dict[PlanetChunk, list[Planet]] = {}
        for planet in planets:
            chunk = self._vec_to_planet_chunk(planet.pos)
            self._planet_chunks.setdefault(chunk, []).append(planet)

        self._particles: list[Particle] = []

    def add_asteroids(self, *args: Asteroid) -> None:
        """Add asteroids to the universe.

        Raises a ValueError if the asteroid's size exceeds the universe's max_nonplanet_size.

        TODO: We could also check if the asteroid's size exceeds max_nonplanet_size, and if it does,
        update max_nonplanet_size and rebuild the chunks. Would be slow, but should hopefully happen
        rarely, would provide a better API (callers need not settle on a size limit upfront), and
        wouldn't cause runtime-exceptions.
        """
        for asteroid in args:
            if asteroid.radius * 2 > self.max_nonplanet_size:
                raise ValueError
            chunk = self._vec_to_asteroid_chunk(asteroid.pos)
            self._asteroid_chunks.setdefault(chunk, []).append(asteroid)

    def _nearby_planets(self, vec: Vec2) -> Iterator[Planet]:
        (x, y) = self._vec_to_planet_chunk(vec)
        for i in range(-1, 2):
            for j in range(-1, 2):
                chunk = (x + i, y + j)
                yield from self._planet_chunks.get(chunk, [])

    def _nearby_asteroids(self, vec: Vec2) -> Iterator[Asteroid]:
        (x, y) = self._vec_to_asteroid_chunk(vec)
        for i in range(-1, 2):
            for j in range(-1, 2):
                chunk = (x + i, y + j)
                yield from self._asteroid_chunks.get(chunk, [])

    def apply_gravity_to_obj(self, dt: float, pobj: PhysicalObject) -> None:
        """Affect pobj by `self`'s entire gravity.

        Args:
            dt (float): Passed time
            pobj (PhysicalObject): Object to affect

        """
        force_sum = Vec2(0, 0)
        for body in self._nearby_planets(pobj.pos):
            force_sum += pobj.gravitational_force(body)
        pobj.apply_force(force_sum, dt)

    @global_profiler.profile_method
    def apply_gravity(self, dt: float) -> None:
        """Apply gravity to all of `self`'s objects.

        Args:
            dt (float): Passed time

        """
        for pobj in chain(self._player_ships, self._enemy_ships, *self._asteroid_chunks.values()):
            self.apply_gravity_to_obj(dt, pobj)

    @global_profiler.profile_method
    def apply_bounce(self) -> None:
        """Run all bounce-interactions within `self`."""
        # Bounce-Hierarchy:
        # player_ships > enemy_ships > asteroids
        # Planets are separate.

        # Bounce player_ships
        for player in self._player_ships:
            # For now, don't bounce player-ships off of other player-ships
            for body in chain(self._enemy_ships, self._nearby_asteroids(player.pos)):
                if damage := player.bounce_disks(body) is not None:
                    player.suffer_damage(damage)
            for planet in self._nearby_planets(player.pos):
                if damage := player.bounce_off_of_disk(planet) is not None:
                    player.suffer_damage(damage)

        # Bounce enemy_ships
        for ix, enemy_ship in enumerate(self._enemy_ships):
            # But it *is* fun to bounce enemies off of each other
            for body in chain(self._enemy_ships[ix + 1 :], self._nearby_asteroids(enemy_ship.pos)):
                # TODO: Once enemies have proper health, they should probably suffer damage, too
                enemy_ship.bounce_disks(body)
            for planet in self._nearby_planets(enemy_ship.pos):
                # TODO: Once enemies have proper health, they should probably suffer damage, too
                enemy_ship.bounce_off_of_disk(planet)

        # Bounce asteroids
        for asteroid in chain(*self._asteroid_chunks.values()):
            for body in self._nearby_asteroids(asteroid.pos):
                asteroid.bounce_disks(body)
            for planet in self._nearby_planets(asteroid.pos):
                asteroid.bounce_off_of_disk(planet)

    def asteroids_or_planets_intersect_point(self, vec: Vec2) -> bool:
        """Test whether any of `self`'s planets or asteroids intersect `vec`.

        Args:
            vec (Vec2): Position to test for intersection

        Returns:
            bool: True iff any intersect

        """
        return any(body.intersects_point(vec) for body in self._nearby_asteroids(vec)) or any(
            body.intersects_point(vec) for body in self._nearby_planets(vec)
        )

    @global_profiler.profile_method
    def collide_bullets(self) -> None:
        """Run bullet-collision checks and damage ships as a result."""

        def player_projectile_check(projectile: Bullet) -> bool:
            """Run bullet-logic and return whether it should stay alive."""
            if not self.contains_point(projectile.pos):
                return False
            if self.asteroids_or_planets_intersect_point(projectile.pos):
                return False
            for enemy in self._enemy_ships:
                if enemy.intersects_point(projectile.pos):
                    self._enemy_ships.remove(enemy)
                    return False
            return True

        # TODO: Once enemies can take damage, collapse player_projectile_check and
        # enemy_projectile_check into a single function taking as an argument the list
        # of enemy-ships.
        def enemy_projectile_check(projectile: Bullet) -> bool:
            """Run bullet-logic and return whether it should stay alive."""
            if not self.contains_point(projectile.pos):
                return False
            if self.asteroids_or_planets_intersect_point(projectile.pos):
                return False
            for player in self._player_ships:
                if player.intersects_point(projectile.pos):
                    player.suffer_damage(5)
                    return False
            return True

        for player in self._player_ships:
            player.projectiles = [p for p in player.projectiles if player_projectile_check(p)]

        for enemy in self._enemy_ships:
            enemy.projectiles = [p for p in enemy.projectiles if enemy_projectile_check(p)]

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Run input-logic for player-ships.

        Args:
            keys (pygame.key.ScancodeWrapper): Pressed keys

        """
        for player_ship in self._player_ships:
            player_ship.handle_input(keys)

    def move_camera(self, camera: Camera, player_ix: int, dt: float) -> None:
        """Move the camera to `self.player_ships[player_ix]`.

        Args:
            camera (Camera): Camera to move
            player_ix (int): Player to focus on
            dt (float): Passed time

        """
        ship = self._player_ships[player_ix]
        camera.smoothly_focus_points([ship.pos, ship.pos + 1.0 * ship.vel], 500, dt)

    @global_profiler.profile_method
    def step(self, dt: float) -> None:
        """Run the universe-logic, also for the object `self` contains.

        Args:
            dt (float): Passed time

        """
        # Ship
        for ship in chain(self._player_ships, self._enemy_ships):
            ship.step(dt)

        # Asteroids
        new_asteroid_chunks: dict[AsteroidChunk, list[Asteroid]] = {}
        for asteroids in self._asteroid_chunks.values():
            for asteroid in asteroids:
                asteroid.step(dt)
                new_chunk = self._vec_to_asteroid_chunk(asteroid.pos)
                new_asteroid_chunks.setdefault(new_chunk, []).append(asteroid)
        self._asteroid_chunks = new_asteroid_chunks

        self._particles = [p for p in self._particles if p.step(dt)]

        # Physics
        self.apply_gravity(dt)
        self.apply_bounce()
        self.collide_bullets()

    @global_profiler.profile_method
    def draw_background(self, camera: Camera) -> None:
        """Draw `self`'s parallaxing background on `camera`.

        Args:
            camera (Camera): Camera to draw on

        """
        # TODO: Try caching star-chunks to their final on-screen locations.
        # If doing that, also optimise x_chunk_size for performance (via profiling) again.
        camera.surface.lock()
        camera_size = Vec2(camera.surface.get_size())
        x_chunk_size = 3500  # This value is profiling-optimised for non-cached star-chunks.
        y_chunk_size = x_chunk_size * camera_size.y / camera_size.x
        z_chunk_size = 1000
        z_chunk_min = 1  # star-depths are in [z_chunk_min*z_chunk_size, z_chunk_max*z_chunk_size)
        z_chunk_max = 5

        r"""
        In worldspace, we can imagine it like this (the y-dimension is not visible here):

                        camera                  worldspace_z = 0 * z_chunk_size
                          ╱╲
                         ╱  ╲
                        ╱    ╲
        ━━┯━━━━┯━━━━┯━━╱━┯p━━━╲━━━━┯━━━━┯━━━━┯━ worldspace_z = 1 * z_chunk_size
          │    │    │ ╱  │    │╲   │    │    │
          │    │    │╱   │    │ ╲  │    │    │
        ──┼────┼────╱────┼────┼──╲─┼────┼────┼─ worldspace_z = 2 * z_chunk_size
          │    │░░░╱│░░░░│░░░░│░░░╲│░░░░│    │
          │    │░░╱░│░░░░│░░░░│░░░░╲░░░░│    │
        ──┼────┼─╱──┼────┼────┼────┼╲───┼────┼─ worldspace_z = 3 * z_chunk_size
          │░░░░│╱░░░│░░░░│░░░░│░░░░│░╲░░│    │
          │░░░░╱░░░░│░░░░│░░░░│░░░░│░░╲░│    │
        ──┼───╱┼────┼────┼────┼────┼───╲┼────┼─ worldspace_z = 4 * z_chunk_size
          │  ╱ │    │    │    │    │    ╲    │


        (As this is a 2D-game, the z-dimension does not actually exist in worldspace, but
        it's helpful to imagine it)

        - p is the player-ship
        - The ━heavy━line━ (at z = 1 * z_chunk_size) is the plane containing the player-ship,
          planets andasteroids
        - Here, z_chunk_min=2 and z_chunk_max=4.
        - The rectangular grid comprises the chunks. Each rectangle thus has height z_chunk_size,
          and width x_chunk_size.
        - The ░shaded░ rectangles are exactly the chunks that stars will be generated in.

        Given a fixed z, let's figure out how to generate all shaded chunks of that z-layer, i.e.
        all shaded chunks between z*z_chunk_size and (z+1)*z_chunk_size.
        For this, it suffices to figure out the x-position of where the camera's periphery (denoted
        by the two diagonal lines) crosses the (z+1)*z_chunk_size line, and round to the nearest chunk.

        For this, it suffices to know the points X1, X2 where the camera's periphery crosses the
        1*z_chunk_size line (so the plane containing the ship, planets, asteroid), because then
        the x-coordinates X1', X2' of the crossing-points with the (z+1)*z_chunk_size line are simply:
            X1' = camera_worldspace_center.x - (camera_worldspace_center.x - X1) * (z+1)
                = (z+1)*X1 - z*camera_worldspace_center.x
            X2' = camera_worldspace_center.x + (X2 - camera_worldspace_center.x) * (z+1)
                = (z+1)*X2 - z*camera_worldspace_center.x
        by the basic proportionality theorem.

        Figuring out X1, X2 is easy, though: They are simply the left and right
        worldspace-coordinates of the screen-edges.
        """  # noqa: RUF001

        # Topleft, bottomright
        camera_topleft_worldspace = camera.pos
        camera_bottomright_worldspace = camera.pos + camera_size / camera.zoom
        camera_center_worldspace = camera.pos + camera_size / (2 * camera.zoom)

        # Threshold for sampling poisson-stars. This is e^(-λ), where λ is the expected value of the
        # poisson-distribution. The poisson-distribution will determine the number of stars in one chunk,
        # so λ should be proportional to the volume of a chunk:
        poisson_threshold = math.exp(-1e-9 * x_chunk_size * y_chunk_size * z_chunk_size)

        # Iterate z-chunks back to front, so that stars in the front are drawn over stars in the back
        for z in range(z_chunk_max - 1, z_chunk_min - 1, -1):
            # Calculate X1', X2'
            x1 = (z + 1) * camera_topleft_worldspace.x - z * camera_center_worldspace.x
            x2 = (z + 1) * camera_bottomright_worldspace.x - z * camera_center_worldspace.x
            # Transfer them to chunks by dividing by x_chunk_size and rounding down.
            # We round down both because this only denotes the left edge of the chunk. The
            # Chunk will extend for one x_chunk_size further rightwards, and thus also include X2'.
            xstart = math.floor(x1 / x_chunk_size)
            xend = math.floor(x2 / x_chunk_size)
            # The +1 in the range is because python's range-ends are exclusive.
            for x in range(xstart, xend + 1):
                # Same calculations for y
                y1 = (z + 1) * camera_topleft_worldspace.y - z * camera_center_worldspace.y
                y2 = (z + 1) * camera_bottomright_worldspace.y - z * camera_center_worldspace.y
                # Transfer them to chunks by dividing by x_chunk_size and rounding down.
                # We round down both because this only denotes the left edge of the chunk. The
                # Chunk will extend for one x_chunk_size further rightwards, and thus also include X2'.
                ystart = math.floor(y1 / y_chunk_size)
                yend = math.floor(y2 / y_chunk_size)
                for y in range(ystart, yend + 1):
                    # Set the seed so that stars are always in the same positions for a given chunk
                    random.seed(z + x * z_chunk_max + y * 1_000 * z_chunk_max)

                    star_depths: list[float] = []
                    # Number of stars follows a poisson-distribution
                    p = random.random()
                    while p > poisson_threshold:
                        p *= random.random()
                        star_depths.append((z + random.random()) * z_chunk_size)

                    for star_depth in star_depths:
                        star_worldspace_xy_unparallax = Vec2(
                            (x + random.random()) * x_chunk_size, (y + random.random()) * y_chunk_size
                        )

                        """
                        For the parallax:

                                        camera                  worldspace_z = 0 * z_chunk_size
                                          ╱╲
                                         ╱  ╲
                                        ╱    ╲
                        ━━┯━━━━┯━━━━┯━━╱┅┅┅┅┅┅╲━━━━┯━━━━┯━━━━┯━ worldspace_z = 1 * z_chunk_size
                          │    │    │ ╱  │    │╲   │    │    │
                          │    │    │╱   │    │ ╲  │    │    │
                        ──┼────┼────╱────┼────┼──╲─┼────┼────┼─
                          │    │   ╱│    │    │   ╲│    │    │
                          │    │  ╱ │    │    │    ╲    │    │
                        ──┼────┼─╱──┼────┼────┼────┼╲───┼────┼─
                          │    │╱   │    │    │    │ ╲  │    │
                          │    ╱════╪════╪════╪════╪══╲ │    │  star_depth
                        ──┼───╱┼────┼────┼────┼────┼───╲┼────┼─
                          │  ╱ │    │    │    │    │    ╲    │


                        If you consider the set of all possible stars at depth = star_depth (this set is
                        the ═doubly═struck═line═), we want those stars to be visible on screen, i.e. we
                        want that set to be mapped to the ┅dashed┅line┅. We can do that by shrinking it
                        by the factor star_depth/z_chunk_size (again by the proportionality theorem),
                        while fixing its center at the camera-center. So the if the star's unparallaxed
                        worldspace-position is X, then its parallaxed worldspace-position is:
                            X' = (X - camera_center_worldspace.x) / (z_chunk_size/star_depth)
                                  + camera_center_worldspace.x
                        """  # noqa: RUF001

                        star_depth_inverse = z_chunk_size / star_depth
                        parallax_scaling_factor = Vec2(star_depth_inverse, star_depth_inverse)
                        star_worldspace_xy = (
                            star_worldspace_xy_unparallax - camera_center_worldspace
                        ).elementwise() * parallax_scaling_factor + camera_center_worldspace
                        color = int(200 * (1 - star_depth / (z_chunk_max * z_chunk_size)))

                        camera.draw_pixel(Color(color, color, color), star_worldspace_xy)

        camera.surface.unlock()

    @global_profiler.profile_method
    def draw(self, camera: Camera) -> None:
        """Draw all of `self` on `camera`.

        Args:
            camera (Camera): Camera to draw on

        """
        for pobj in chain(
            *self._asteroid_chunks.values(),
            *self._planet_chunks.values(),
            self._enemy_ships,
            self._player_ships,
        ):
            pobj.draw(camera)

    @global_profiler.profile_method
    def draw_text(self, camera: Camera, player_ix: int, fps: float) -> None:
        """Draw "debugging" text on `camera`.

        Args:
            camera (Camera): Camera to draw on
            player_ix (int): Player to display information about
            fps (float): Current fps

        """
        font_size = 32
        font = pygame.font.Font(None, font_size)

        def texty(vertical_offset: int, text: str | None = None) -> int:
            if text is not None:
                camera.draw_text(text, Vec2(10, vertical_offset), font, Color("white"))
            return vertical_offset + font_size

        text_v = 10
        player_ship = self._player_ships[player_ix]
        text_v = texty(text_v, f"{fps:.0f} fps (average over past {FPS_HISTORY_LENGTH} frames)")
        text_v = texty(text_v, f"Health: {player_ship.health:.0f}")

        enemy_count = len(self._enemy_ships)
        texty(text_v, f"Enemies left: {enemy_count}")

    @global_profiler.profile_method
    def draw_grid(self, camera: Camera) -> None:
        """Draw grid on `camera`.

        Args:
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
            vec (Vec2): Vec to test for containment

        Returns:
            bool: True iff `self` contains `vec`

        """
        return 0 <= vec.x <= self.size.x and 0 <= vec.y <= self.size.y

    def generate_asteroid(self, planet: Planet) -> None:
        """Create an asteroid orbiting a planet.

        Args:
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
        radius_asteroid = min(
            ASTEROID_SIZE_MIN + random.expovariate(asteroid_radius_lambda), self.max_nonplanet_size / 2
        )
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

        self.add_asteroids(Asteroid(pos_asteroid, velocity_asteroid, 1, radius_asteroid))
