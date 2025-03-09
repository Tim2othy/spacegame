"""A collection of celestial objects, forming a Universe."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import Disk, PosVelObj, Particle, PhysicalObject
from profiler import global_profiler
from projectiles import Missile
from ship import BulletEnemy, EnemyConfig, PlayerShip, PlayerConfig

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

    from camera import Camera
    from projectiles import Bullet
    from ship import Ship

from constants import FPS_HISTORY_LENGTH, GRAVITATIONAL_CONSTANT, GRID_COLOR

PLANET_SIZE_MIN = 600
# these are parameters for exponential distributions
PLANET_RADIUS_PARAMETER = 0.02
PLANET_ORBIT_PARAMETER = 0.0002
PLANET_ELLIPSIS_PARAMETER = 0.001


class Star(Disk):
    """A stationary disk."""

    def __init__(self, relative_to: PosVelObj, relative_pos: Vec2, radius: float) -> None:
        """Create a new star."""
        star_color = Color(random.randint(200, 255), random.randint(150, 255), random.randint(0, 150))
        super().__init__(relative_to, relative_pos, Vec2(0, 0), radius, star_color)


@dataclass(kw_only=True)
class PlanetConfig:
    """Configuration for a planet.

    Attributes:
        relative_pos (Vec2): Relative position of the planet
        relative_vel (Vec2): Relative velocity of the planet
        radius (float): Radius of the planet

    """

    relative_pos: Vec2
    relative_vel: Vec2 = field(default_factory=lambda: Vec2(0, 0))
    radius: float


class Planet(Disk):
    """A disk that doesn't exert gravitational force, and isn't stationary."""

    def __init__(self, relative_to: PosVelObj, config: PlanetConfig) -> None:
        """Create a new Planet."""
        color = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        super().__init__(relative_to, config.relative_pos, config.relative_vel, config.radius, color)


type PlanetChunk = tuple[int, int]
type StarChunk = tuple[int, int]


class Universe:
    """A collection of celestial objects, forming a Universe.

    Its width is size.x, its height is size.y.
    Coordinates are implicitly zero-based.
    """

    def __init__(self, star_size: float | None, max_nonstar_size: float) -> None:
        """Create a new universe that can have one star at the center.

        If star_size is None, the universe will have no star, otherwise it will have a star of size star_size.

        Assumes every planet and ship has an axis-aligned-bounding-box
        of size at most max_nonstar_size. For disks, that means their diameter must not
        exceed max_nonstar_size. If violated, collision-detection may ignore large objects.
        A smaller max_nonstar_size speeds up collision-detection, so choose the smallest value
        possible.

        Raises a ValueError if star_size is a float and not strictly positive.

        Args:
            star_size (float | None): The size of the star, must be positive.
            max_nonstar_size: float

        """
        self.max_nonstar_size = max_nonstar_size
        self.__star: PosVelObj | Star = PosVelObj._new_origin_and_only_use_this_if_you_really_know_what_you_are_doing()  # noqa: SLF001
        if star_size is not None:
            if not star_size > 0:
                raise ValueError
            self.__star = Star(self.__star, Vec2(), star_size)

        self._player_ships: list[PlayerShip] = []
        self._enemy_ships: list[BulletEnemy] = []

        def pobj_to_planet_chunk(pobj: PhysicalObject) -> PlanetChunk:
            pos = pobj.pos_relative_to(self.__star) / max_nonstar_size
            return (math.floor(pos.x), math.floor(pos.y))

        self._pobj_to_planet_chunk: Callable[[PhysicalObject], PlanetChunk] = pobj_to_planet_chunk
        self._planet_chunks: dict[PlanetChunk, list[Planet]] = {}

        self._particles: list[Particle] = []

    def add_player(self, ship_config: PlayerConfig, *, relative_to: None | PosVelObj = None) -> PlayerShip:
        """Add a player-ship from its config and return (a reference to) the created ship.

        If relative_to is None, the planet is created relative to the universe's star.
        """
        ship = PlayerShip(relative_to or self.__star, ship_config)
        self._player_ships.append(ship)
        return ship

    def add_enemy(
        self, ship_config: EnemyConfig, ship_type: type[BulletEnemy], *, relative_to: None | PosVelObj = None
    ) -> BulletEnemy:
        """Add an enemy-ship from its config and return (a reference to) the created ship.

        If relative_to is None, the planet is created relative to the universe's star.
        """
        ship = ship_type(relative_to or self.__star, ship_config)
        self._enemy_ships.append(ship)
        return ship

    def add_planet(self, planet_config: PlanetConfig, *, relative_to: None | PosVelObj = None) -> Planet:
        """Add a planet from its config. Returns (a reference to) the created planet.

        If relative_to is None, the planet is created relative to the universe's star.
        Raises a ValueError if the planet's radius exceeds the max_nonstar_size.
        """
        if planet_config.radius * 2 > self.max_nonstar_size:
            raise ValueError
        planet = Planet(relative_to or self.__star, planet_config)
        chunk = self._pobj_to_planet_chunk(planet)
        self._planet_chunks.setdefault(chunk, []).append(planet)
        return planet

    def _nearby_planets(self, pobj: PhysicalObject) -> Iterator[Planet]:
        (x, y) = self._pobj_to_planet_chunk(pobj)
        for i in range(-1, 2):
            for j in range(-1, 2):
                chunk = (x + i, y + j)
                yield from self._planet_chunks.get(chunk, [])

    def apply_gravity_to(self, pobj: PhysicalObject, dt: float) -> None:
        """Affect pobj by `self`'s entire gravity."""
        force_sum = Vec2(0, 0)

        if isinstance(self.__star, Star):
            force_sum += pobj.gravitational_force(self.__star)
        for body in self._nearby_planets(pobj):
            force_sum += pobj.gravitational_force(body)

        pobj.apply_force(force_sum, dt)

    @global_profiler.profile_method
    def apply_gravity(self, dt: float) -> None:
        """Apply gravity to all of `self`'s objects."""
        for pobj in chain(self._player_ships, self._enemy_ships, *self._planet_chunks.values()):
            self.apply_gravity_to(pobj, dt)

    @global_profiler.profile_method
    def apply_bounce(self) -> None:
        """Run all bounce-interactions within `self`."""
        ships: list[Ship] = self._player_ships + self._enemy_ships

        for ix, ship in enumerate(ships):
            # Bounce ships off of each other
            for other_ship in ships[ix + 1 :]:
                if damage := ship.bounce_disks(other_ship) is not None:
                    ship.suffer_damage(damage)
                    other_ship.suffer_damage(damage)
                    self.create_particles_on_disk(ship, other_ship, 25, other_ship.color, 100)
                    self.create_particles_on_disk(other_ship, ship, 25, ship.color, 100)
            for planet in self._nearby_planets(ship):
                if damage := ship.bounce_disks(planet) is not None:
                    ship.suffer_damage(damage)
                    self.create_particles_on_disk(planet, ship, 25, ship.color, 100)
            if isinstance(self.__star, Star) and ship.intersects_disk(self.__star):
                ship.suffer_damage(float("inf"))  # 💀

        # Bounce planets
        for planet in chain(*self._planet_chunks.values()):
            # TODO: Could this be optimised by not checking all pairs of planets?
            for body in self._nearby_planets(planet):
                planet.bounce_disks(body)
            # TODO: This is unrealistic and dumb, but destroying planets that fall into the star
            # isn't fun, either? At any rate, if nobody bounces off of stars anymore, we can probably
            # finally deprecate Disk.bounce_off_of_disk (I hate that method)
            if isinstance(self.__star, Star):
                planet.bounce_off_of_disk(self.__star)

    def create_particles_on_disk(
        self, disk: Disk, projected_pobj: PhysicalObject, n: int, color: Color, blast_vel: float
    ) -> None:
        """Create `n` particles on the disk's surface.

        `projected_pobj._pos` is projected onto `disk`'s surface, with velocity randomly sampled to face
        away from `disk` with max-length `blast_vel` in addition to `disk`'s current velocity.
        Colors are randomly sampled from interpolation
        between `disk.color` and `color`.

        The particles' lifetime is randomly sampled from (0.5, 1.0).

        If pos is exactly on disk's center, nothing happens.
        """
        delta = projected_pobj.pos_relative_to(disk)
        if delta == Vec2(0, 0):
            return
        delta_normalized = delta.normalize()
        projected_relative_to_center = delta_normalized * disk.radius
        for _ in range(n):
            random_lifetime = random.uniform(0.5, 1.0)
            random_angle = random.uniform(-90.0, 90.0)
            random_vel = delta_normalized.rotate(random_angle) * blast_vel * random.random()
            random_color = disk.color.lerp(color, random.random())
            self._particles.append(
                Particle(disk, projected_relative_to_center, random_vel, random_color, random_lifetime)
            )

    def create_particle_cloud(self, source: PhysicalObject, n: int, color: Color, blast_vel: float) -> None:
        """Create `n` particles forming a blast-cloud around pos.

        Particles' velocity are spherically sampled with length between 0 and blast_vel, added
        to `initial_vel`.

        The particles' lifetime is randomly sampled from (1.0, 2.0).
        """
        for _ in range(n):
            random_lifetime = random.uniform(1.0, 2.0)
            random_vel = Vec2()
            random_vel.from_polar((blast_vel * random.random(), random.random() * 360))
            self._particles.append(Particle(source, Vec2(0, 0), random_vel, color, random_lifetime))

    @global_profiler.profile_method
    def collide_bullets(self) -> None:
        """Run bullet-collision checks and damage ships as a result."""

        def projectile_check(projectile: Bullet, ships_it_can_hit: Sequence[Ship]) -> bool:
            """Check for collision and return whether the projectile should stay alive."""
            # TODO: Add lifetime to bullets. The universe being unbounded now, they life forever and
            # will cause eventual lag.

            if isinstance(self.__star, Star) and self.__star.contains_center_of(projectile):
                return False
            for planet in self._nearby_planets(projectile):
                if planet.contains_center_of(projectile):
                    self.create_particles_on_disk(planet, projectile, 5, projectile.color, 250)
                    return False
            for ship in ships_it_can_hit:
                if ship.contains_center_of(projectile):
                    self.create_particle_cloud(ship, 100, ship.color, 150)
                    ship.suffer_damage(projectile.damage)
                    return False
                # TODO: Should we just change `class Bullet(PhysicalObject)` to `class Bullet(Disk)`,
                # i.e. have Bullet inherit from Disk instead of just PhysicalObject? That'd make this whole
                # collision-detection more idiomatic. If we do, we can also change the above calls
                # `Disk.contains_center_of(bullet)` to `Disk.intersects_disk(bullet)`.
                # We should then also change the same call in test_projectiles.py.
                if isinstance(projectile, Missile) and any(
                    other_projectile.distance_squared_to(projectile) < 10**2 for other_projectile in ship.projectiles
                ):
                    return False

            return True

        for player in self._player_ships:
            player.projectiles = [p for p in player.projectiles if projectile_check(p, self._enemy_ships)]

        for enemy in self._enemy_ships:
            enemy.projectiles = [p for p in enemy.projectiles if projectile_check(p, self._player_ships)]

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Run input-logic for player-ships.

        `keys` is typically retreived using `pygame.key.get_pressed()`.
        """
        for player_ship in self._player_ships:
            player_ship.handle_input(keys)

    def move_camera(self, camera: Camera, player_ix: int, dt: float) -> None:
        """Focus the camera on `self.player_ships[player_ix]`."""
        ship = self._player_ships[player_ix]
        camera.smoothly_focus_points([ship._pos, ship._pos + 1.0 * ship._vel], 500, dt)

    @global_profiler.profile_method
    def step(self, dt: float) -> None:
        """Run the universe-logic, also for the object `self` contains."""
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
        """Draw `self`'s parallaxing background on `camera`."""
        # Store random_state. we're about to use random.seed() and want to use "normal" rng later.
        random_state = random.getstate()
        # TODO: Try caching star-chunks to their final on-screen locations.
        # If doing that, also optimise x_chunk_size for performance (via profiling) again.
        camera._surface.lock()
        camera_size = Vec2(camera._surface.get_size())
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

        camera._surface.unlock()
        random.setstate(random_state)

    @global_profiler.profile_method
    def draw(self, camera: Camera) -> None:
        """Draw all of `self` on `camera`."""
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
        """Draw gridlines on `camera`."""
        # TODO: Choose one of these options:
        # 1. Use a grid relative to the camera's position (universe is unbounded now)
        # 2. Use a polar grid centered on self.star, relative to the camera's position
        # 3. Don't use any grid at all (the background-stars will guide your way)
        #
        # I like option 2.    ~lumi-a

        gridline_spacing = 500
        width = 3000
        height = 3000

        for x in range(0, int(width + 1), gridline_spacing):
            camera.draw_vertical_hairline(GRID_COLOR, x, 0, height)

        for y in range(0, int(height + 1), gridline_spacing):
            camera.draw_horizontal_hairline(GRID_COLOR, 0, width, y)

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
