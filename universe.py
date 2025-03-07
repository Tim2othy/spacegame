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
from ship import MissileEnemy, Ship

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from camera import Camera
    from projectiles import Bullet
    from ship import BulletEnemy, PlayerShip

from constants import FPS_HISTORY_LENGTH, GRAVITATIONAL_CONSTANT, GRID_COLOR

PLANET_SIZE_MIN = 600
# these are parameters for exponential distributions
PLANET_RADIUS_PARAMETER = 0.02
PLANET_ORBIT_PARAMETER = 0.0002
PLANET_ELLIPSIS_PARAMETER = 0.001


class Star(Disk):
    """A stationary disk."""

    def __init__(self, pos: Vec2, radius: float) -> None:
        """Create a new star.

        Args:
            pos (Vec2): Fixed position
            radius (float): Radius

        """
        color = Color(random.randint(200, 255), random.randint(150, 255), random.randint(0, 150))
        super().__init__(pos, Vec2(0, 0), radius, color)


class Planet(Disk):
    """A disk that doesn't exert gravitational force, and isn't stationary."""

    def __init__(self, pos: Vec2, vel: Vec2, radius: float) -> None:
        """Create a new Planet.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            radius (float): Radius

        """
        color = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        super().__init__(pos, vel, radius, color)


type PlanetChunk = tuple[int, int]
type StarChunk = tuple[int, int]


class Universe:
    """A collection of celestial objects, forming a Universe.

    Its width is size.x, its height is size.y.
    Coordinates are implicitly zero-based.
    """

    def __init__(
        self,
        size: Vec2,
        stars: list[Star],
        player_ships: list[PlayerShip],
        enemy_ships: list[BulletEnemy],
        max_nonstar_size: float,
    ) -> None:
        """Create a new universe.

        Assumes stars are immutable.

        Assumes every planet and ship has an axis-aligned-bounding-box
        of size at most max_nonstar_size. For disks, that means their diameter must not
        exceed max_nonstar_size. If violated, collision-detection may ignore large objects.
        A smaller max_nonstar_size speeds up collision-detection, so choose the smallest value
        possible.

        Raises a ValueError if any player-ship or enemy-ship is larger than max_nonstar_size.

        Args:
            size (Vec2): Width and height
            stars (list[Star]): Stars
            player_ships (list[Ship]): List of player-ships
            enemy_ships (list[BulletEnemy]): Enemy fleet
            max_nonstar_size: float

        """
        self.size = Vec2(size)
        self.max_nonstar_size = max_nonstar_size

        if any(2 * ship.radius > max_nonstar_size for ship in player_ships) or any(
            2 * ship.radius > max_nonstar_size for ship in enemy_ships
        ):
            raise ValueError

        self._player_ships = player_ships
        self._enemy_ships = enemy_ships

        self._pobj_to_planet_chunk: Callable[[PhysicalObject], PlanetChunk] = lambda pobj: (
            math.floor(pobj._pos.x / max_nonstar_size),  # TODO: Private member access
            math.floor(pobj._pos.y / max_nonstar_size),
        )
        self._planet_chunks: dict[PlanetChunk, list[Planet]] = {}

        star_chunk_size = max(500, 2 * max([p.radius for p in stars], default=0))
        self._pobj_to_star_chunk: Callable[[PhysicalObject], PlanetChunk] = lambda pobj: (
            math.floor(pobj._pos.x / star_chunk_size),  # TODO: Private member access
            math.floor(pobj._pos.y / star_chunk_size),
        )
        self._star_chunks: dict[StarChunk, list[Star]] = {}
        for star in stars:
            chunk = self._pobj_to_star_chunk(star)
            self._star_chunks.setdefault(chunk, []).append(star)
        self.stars = stars

        self._particles: list[Particle] = []

    def add_planet(self, *args: Planet) -> None:
        """Add planets to the universe.

        Raises a ValueError if the planet's size exceeds the universe's max_nonstar_size.

        TODO: We could also check if the planet's size exceeds max_nonstar_size, and if it does,
        update max_nonstar_size and rebuild the chunks. Would be slow, but should hopefully happen
        rarely, would provide a better API (callers need not settle on a size limit upfront), and
        wouldn't cause runtime-exceptions.
        """
        for planet in args:
            if planet.radius * 2 > self.max_nonstar_size:
                raise ValueError
            chunk = self._pobj_to_planet_chunk(planet)
            self._planet_chunks.setdefault(chunk, []).append(planet)

    def _nearby_stars(self, pobj: PhysicalObject) -> Iterator[Star]:
        (x, y) = self._pobj_to_star_chunk(pobj)
        for i in range(-1, 2):
            for j in range(-1, 2):
                chunk = (x + i, y + j)
                yield from self._star_chunks.get(chunk, [])

    def _nearby_planets(self, pobj: PhysicalObject) -> Iterator[Planet]:
        (x, y) = self._pobj_to_planet_chunk(pobj)
        for i in range(-1, 2):
            for j in range(-1, 2):
                chunk = (x + i, y + j)
                yield from self._planet_chunks.get(chunk, [])

    def apply_gravity_to_obj(self, dt: float, pobj: PhysicalObject) -> None:
        """Affect pobj by `self`'s entire gravity.

        Args:
            dt (float): Passed time
            pobj (PhysicalObject): Object to affect

        """
        force_sum = Vec2(0, 0)
        # We can assume only one Star exists
        for body in self.stars:
            force_sum += pobj.gravitational_force(body)

        for body in self._nearby_planets(pobj):
            force_sum += pobj.gravitational_force(body)
        pobj.apply_force(force_sum, dt)

    @global_profiler.profile_method
    def apply_gravity(self, dt: float) -> None:
        """Apply gravity to all of `self`'s objects.

        Args:
            dt (float): Passed time

        """
        for pobj in chain(self._player_ships, self._enemy_ships, *self._planet_chunks.values()):
            self.apply_gravity_to_obj(dt, pobj)

    @global_profiler.profile_method
    def apply_bounce(self) -> None:
        """Run all bounce-interactions within `self`."""
        # Bounce-Hierarchy:
        # player_ships > enemy_ships > planets
        # Stars are separate.

        # Bounce player_ships
        for player in self._player_ships:
            # For now, don't bounce player-ships off of other player-ships
            for body in chain(self._enemy_ships, self._nearby_planets(player)):
                if damage := player.bounce_disks(body) is not None:
                    player.suffer_damage(damage)
                    self.create_particles_on_disk(body, player, 25, player.color, 100)
            for star in self._nearby_stars(player):
                if damage := player.bounce_off_of_disk(star) is not None:
                    player.suffer_damage(damage)
                    self.create_particles_on_disk(star, player, 25, player.color, 100)

        # Bounce enemy_ships
        for ix, enemy_ship in enumerate(self._enemy_ships):
            # But it *is* fun to bounce enemies off of each other
            for body in chain(self._enemy_ships[ix + 1 :], self._nearby_planets(enemy_ship)):
                if damage := enemy_ship.bounce_disks(body) is not None:
                    enemy_ship.suffer_damage(damage)
                enemy_ship.bounce_disks(body)
            for star in self._nearby_stars(enemy_ship):
                if damage := enemy_ship.bounce_off_of_disk(star) is not None:
                    enemy_ship.suffer_damage(damage)
                enemy_ship.bounce_off_of_disk(star)

        # Bounce planets
        for planet in chain(*self._planet_chunks.values()):
            for body in self._nearby_planets(planet):
                planet.bounce_disks(body)
            for star in self._nearby_stars(planet):
                planet.bounce_off_of_disk(star)

    def create_particles_on_disk(
        self, disk: Disk, projected_pobj: PhysicalObject, n: int, color: Color, blast_vel: float, lifetime: float = 1.0
    ) -> None:
        """Create `n` particles on the disk's surface.

        `projected_pobj._pos` is projected onto `disk`'s surface, with velocity randomly sampled to face
        away from `disk` with max-length `blast_vel` in addition to `disk`'s current velocity.
        Colors are randomly sampled from interpolation
        between `disk.color` and `color`.

        The particles' lifetime is randomly sampled from (lifetime/2, lifetime).

        If pos is exactly on disk's center, nothing happens.
        """
        delta = projected_pobj.pos_relative_to(disk)
        if delta == Vec2(0, 0):
            return
        delta_normalized = delta.normalize()
        projected = disk._pos + delta_normalized * disk.radius
        for _ in range(n):
            random_angle = random.uniform(-90.0, 90.0)
            random_vel = disk._vel + delta_normalized.rotate(random_angle) * blast_vel * random.random()
            random_color = disk.color.lerp(color, random.random())
            random_lifetime = random.uniform(lifetime / 2.0, lifetime)
            self._particles.append(Particle(projected, random_vel, random_color, random_lifetime))

    def create_particle_cloud(
        self, source: PhysicalObject, n: int, color: Color, blast_vel: float, lifetime: float = 1.0
    ) -> None:
        """Create `n` particles forming a blast-cloud around pos.

        Particles' velocity are spherically sampled with length between 0 and blast_vel, added
        to `initial_vel`.

        The particles' lifetime is randomly sampled from (lifetime/2, lifetime).
        """
        for _ in range(n):
            random_vel = Vec2()
            random_vel.from_polar((blast_vel * random.random(), random.random() * 360))
            vel = source._vel + random_vel
            random_lifetime = random.uniform(lifetime / 2, lifetime)
            self._particles.append(Particle(source._pos, vel, color, random_lifetime))

    @global_profiler.profile_method
    def collide_bullets(self) -> None:
        """Run bullet-collision checks and damage ships as a result."""

        def projectile_check(projectile: Bullet, target_ships: list[Ship], is_player_projectile: bool) -> bool:
            """Check for collision and return whether the projectile should stay alive.

            Args:
                projectile (Bullet): The projectile to check
                target_ships (list): Ships that can be hit by this projectile
                is_player_projectile (bool): Whether this is a player's projectile

            Returns:
                bool: True if the projectile should stay alive, False otherwise

            """
            if not self.cointains_center_of(projectile):
                return False
            for disk in chain(self._nearby_planets(projectile), self._nearby_stars(projectile)):
                if disk.contains_center_of(projectile):
                    self.create_particles_on_disk(disk, projectile, 5, projectile.color, 250)
                    return False
            for ship in target_ships:
                if ship.contains_center_of(projectile):
                    self.create_particle_cloud(ship, 100, ship.color, 150, 2)
                    ship.suffer_damage(projectile.damage)
                    if ship.health <= 0:
                        self.create_particle_cloud(ship, 300, ship.color, 200, 8)
                        if is_player_projectile:
                            self._enemy_ships.remove(
                                ship
                            )  # TODO: We should probably do _enemy_ships.remove(ship) somewhere else, not
                            # sure where though. Then we could also remove the boolean positional argument.
                    return False
                if isinstance(ship, MissileEnemy):
                    for enemy_projectile in ship.projectiles[:]:
                        # TODO: Should we just change `class Bullet(PhysicalObject)` to `class Bullet(Disk)`,
                        # i.e. have Bullet inherit from Disk instead of just PhysicalObject? That'd make this whole
                        # collision-detection more idiomatic. If we do, we can also change the above calls
                        # `Disk.contains_center_of(bullet)` to `Disk.intersects_disk(bullet)`.
                        # We should then also change the same call in test_projectiles.py.
                        collision_distance_squared = 10**2
                        if projectile.distance_squared_to(enemy_projectile) < collision_distance_squared:
                            ship.projectiles.remove(enemy_projectile)
                            return False

            return True

        for player in self._player_ships:
            player.projectiles = [p for p in player.projectiles if projectile_check(p, self._enemy_ships, True)]

        for enemy in self._enemy_ships:
            enemy.projectiles = [p for p in enemy.projectiles if projectile_check(p, self._player_ships, False)]

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
        camera.smoothly_focus_points([ship._pos, ship._pos + 1.0 * ship._vel], 500, dt)

    @global_profiler.profile_method
    def step(self, dt: float) -> None:
        """Run the universe-logic, also for the object `self` contains.

        Args:
            dt (float): Passed time

        """
        # Ship
        for ship in chain(self._player_ships, self._enemy_ships):
            ship.step(dt)

        # Planets
        new_planet_chunks: dict[PlanetChunk, list[Planet]] = {}
        for planets in self._planet_chunks.values():
            for planet in planets:
                planet.step(dt)
                new_chunk = self._pobj_to_planet_chunk(planet)
                new_planet_chunks.setdefault(new_chunk, []).append(planet)
        self._planet_chunks = new_planet_chunks

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
        # Store random_state. we're about to use random.seed() and want to use "normal" rng later.
        random_state = random.getstate()
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
        - The ━heavy━line━ (at worldspace_z = 1 * z_chunk_size) is the plane containing
          the player-ship, stars and planets
        - Here, z_chunk_min=2 and z_chunk_max=4.
        - The rectangular grid comprises the chunks. Each rectangle thus has height z_chunk_size,
          and width x_chunk_size.
        - The ░shaded░ rectangles are exactly the chunks that stars will be generated in.

        Given a fixed z, let's figure out how to generate all shaded chunks of that z-layer, i.e.
        all shaded chunks between z*z_chunk_size and (z+1)*z_chunk_size.
        For this, it suffices to figure out the x-position of where the camera's periphery (denoted
        by the two diagonal lines) crosses the (z+1)*z_chunk_size line, and round to the nearest chunk.

        For this, it suffices to know the points X1, X2 where the camera's periphery crosses the
        1*z_chunk_size line (so the plane containing the ship, stars, planet), because then
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
        random.setstate(random_state)

    @global_profiler.profile_method
    def draw(self, camera: Camera) -> None:
        """Draw all of `self` on `camera`.

        Args:
            camera (Camera): Camera to draw on

        """
        for pobj in chain(
            *self._planet_chunks.values(), *self._star_chunks.values(), self._enemy_ships, self._player_ships
        ):
            pobj.draw(camera)

        for particle in self._particles:
            particle.draw(camera)

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
        gridline_spacing = 500
        width = self.size.x
        height = self.size.y

        for x in range(0, int(width + 1), gridline_spacing):
            camera.draw_vertical_hairline(GRID_COLOR, x, 0, height)

        for y in range(0, int(height + 1), gridline_spacing):
            camera.draw_horizontal_hairline(GRID_COLOR, 0, width, y)

    def cointains_center_of(self, pobj: PhysicalObject) -> bool:
        """Test whether `vec` is contained in `self`'s boundaries.

        Args:
            vec (Vec2): Vec to test for containment

        Returns:
            bool: True iff `self` contains `vec`

        """
        return 0 <= pobj._pos.x <= self.size.x and 0 <= pobj._pos.y <= self.size.y

    def generate_planet(self, star: Star) -> None:
        """Create an planet orbiting a star.

        Args:
            star (Star): The star to orbit

        What the random variables do:
        - radius_planet - pretty obvious
        - r_a             - shortest distance to star during orbit
        - r_p             - largest distance to star during orbit
        - true_anomaly    - where along it's orbit it starts, as in near r_a or near r_p or so
        - orbit_direction - in which direction (in degrees) of the star it starts
        - planet_angle  - does it go clockwise or anticlockwise

        """
        # random variables
        planet_radius_lambda = 1 / (PLANET_RADIUS_PARAMETER * star.radius)
        radius_planet = min(PLANET_SIZE_MIN + random.expovariate(planet_radius_lambda), self.max_nonstar_size / 2)
        r_p = star.radius + radius_planet + random.expovariate(PLANET_ORBIT_PARAMETER)
        r_a = r_p + random.expovariate(PLANET_ELLIPSIS_PARAMETER)
        true_anomaly = random.uniform(0, 2 * math.pi)
        orbit_direction = random.uniform(0, 2 * math.pi)
        planet_angle = random.choice([90, 270])

        # pos_planet
        semi_major_axis = (r_p + r_a) / 2
        eccentricity = (r_a - r_p) / (r_a + r_p)
        r_initial = (semi_major_axis * (1 - eccentricity**2)) / (1 + eccentricity * math.cos(true_anomaly))
        radial_vector = Vec2(1, 0).rotate(math.degrees(true_anomaly + orbit_direction))
        pos_planet = star._pos + radial_vector * r_initial

        # velocity_planet
        total_specific_energy = -GRAVITATIONAL_CONSTANT * star.mass / (2 * semi_major_axis)
        orbital_velocity = (2 * (GRAVITATIONAL_CONSTANT * star.mass / r_initial + total_specific_energy)) ** 0.5
        tangential_vector = radial_vector.rotate(planet_angle)
        vel_planet = tangential_vector * orbital_velocity

        self.add_planet(Planet(pos_planet, vel_planet, radius_planet))
