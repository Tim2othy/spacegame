"""A collection of celestial objects, forming a Universe."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING, TypeVar

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import GRAVITATIONAL_CONSTANT, Disk, Particle, Pos, PosVel
from profiler import global_profiler
from projectiles import Missile, Rocket
from ship import BulletEnemy, EnemyConfig, MissileEnemy, PlayerConfig, PlayerShip, RocketEnemy, ShipInputTank, ShipInputAbsolute

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

    from camera import Camera
    from projectiles import Bullet
    from ship import Ship

MU_PLANET_RADIUS = 5.7
SIGMA_PLANET_RADIUS = 0.24
ORBIT_CORRELATION_FACTOR = 0.05
GRID_COLOR = Color("darkgreen")
GRID_RADIAL_SPACING = 2000
ANGULAR_SPACING = int(360 / 72)
MAX_RADIUS = 60000


class Star(Disk):
    """A stationary disk."""

    def __init__(self, relative_to: PosVel, relative_pos: Vec2, radius: float) -> None:
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

    def __init__(self, relative_to: PosVel, config: PlanetConfig) -> None:
        """Create a new Planet."""
        color = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        super().__init__(relative_to, config.relative_pos, config.relative_vel, config.radius, color)


type PlanetChunk = tuple[int, int]


@dataclass
class UniverseOptions:
    """Options for creating pre-made universes.

    Attributes:
        small (bool): Whether the universe should be small
        splitscreen (bool): Whether there should be one or two players
        invincible (bool): Whether players should be invincible

    """

    small: bool = False
    splitscreen: bool = False
    invincible: bool = False
    use_dvorak: bool = True
    use_tank_controls: bool = True


T = TypeVar("T", bound=BulletEnemy)


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

        If star_size is not None, raises a ValueError if it isn't finite and strictly positive.
        """
        self.max_nonstar_size = max_nonstar_size
        self.__star: PosVel | Star = PosVel._new_origin_and_only_use_this_if_you_really_know_what_you_are_doing()
        if star_size is not None:
            if not (math.isfinite(star_size) and star_size > 0):
                raise ValueError
            self.__star = Star(self.__star, Vec2(0, 0), star_size)

        self._player_ships: list[PlayerShip] = []
        self._enemy_ships: list[BulletEnemy] = []

        def pobj_to_planet_chunk(pos: Pos) -> PlanetChunk:
            pos_in_universe = pos.pos_relative_to(self.__star) / max_nonstar_size
            return (math.floor(pos_in_universe.x), math.floor(pos_in_universe.y))

        self._pobj_to_planet_chunk: Callable[[Pos], PlanetChunk] = pobj_to_planet_chunk
        self._planet_chunks: dict[PlanetChunk, list[Planet]] = {}

        self._particles: list[Particle] = []

    @staticmethod
    def from_options(options: UniverseOptions) -> tuple[Universe, list[PlayerShip]]:
        """Create a universe from `options`."""
        star_size = 25 if options.small else 1400
        num_enemies = 0 if options.small else 20
        num_planets = 0 if options.small else 10
        planet_size_parameter = 4.0 if options.small else MU_PLANET_RADIUS

        # (This is a class-variable)
        ShipInput = ShipInputTank if options.use_tank_controls else ShipInputAbsolute

        universe = Universe(star_size, 1000)
        player_input = ShipInput.dvorak() if options.use_dvorak else ShipInput.arrows()
        player_pos = Vec2(star_size + 100, star_size + 100)
        player_ships = [universe.add_player(PlayerConfig(relative_pos=player_pos, ship_input=player_input))]

        if options.splitscreen:
            second_config = PlayerConfig(relative_pos=Vec2(100, 0), ship_input=ShipInput.wasd())
            # TODO: fix color for second player color=Color("darkred")
            second_player = universe.add_player(second_config, relative_to=player_ships[0])
            player_ships.append(second_player)

        if options.invincible:
            for player in player_ships:
                player.health = float("inf")

        if options.small:
            for enemy in [BulletEnemy, RocketEnemy, MissileEnemy]:
                random_angle = random.uniform(0, 360)
                vec = Vec2(0, 0)
                vec.from_polar((1000, random_angle))

                targeting = random.choice(player_ships)
                universe.add_enemy(EnemyConfig(relative_pos=vec, target_ship=targeting), enemy)

        else:
            for _ in range(num_enemies):
                random_radius = random.uniform(star_size * 3 + 100, star_size * 7 + 100)
                random_angle = random.uniform(0, 360)
                vec = Vec2(0, 0)
                vec.from_polar((random_radius, random_angle))

                spawn_weights = [0.4, 0.3, 0.3]
                enemy_type = random.choices([BulletEnemy, RocketEnemy, MissileEnemy], spawn_weights)[0]
                targeting = random.choice(player_ships)

                universe.add_enemy(EnemyConfig(relative_pos=vec, target_ship=targeting), enemy_type)

        universe.add_planets(num_planets, planet_size_parameter)

        return universe, player_ships

    def add_player(self, ship_config: PlayerConfig, *, relative_to: None | PosVel = None) -> PlayerShip:
        """Add a player-ship from its config and return (a reference to) the created ship.

        If relative_to is None, the planet is created relative to the universe's star.
        """
        ship = PlayerShip(relative_to or self.__star, ship_config)
        self._player_ships.append(ship)
        return ship

    def add_enemy(self, ship_config: EnemyConfig, ship_type: type[T], *, relative_to: None | PosVel = None) -> T:
        """Add an enemy-ship from its config and return (a reference to) the created ship.

        If relative_to is None, the planet is created relative to the universe's star.
        """
        ship = ship_type(relative_to or self.__star, ship_config)
        self._enemy_ships.append(ship)
        return ship

    def add_planet(self, planet_config: PlanetConfig, *, relative_to: None | PosVel = None) -> Planet:
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

    def add_planets(self, num_planets: int, planet_size_parameter: float) -> list[Planet]:
        """Create a num_planets orbiting a Disk, defaulting to the universe's star. With orbits that won't intersect."""
        """
        What the random variables do:
        - semi_major_axis - Choose by multiplying the current minimum by a uniformly distributed factor.
        - radius_planet   - follows a lognormal distribution.
        - eccentricity    - how non round orbit is - drawn from a beta distribution
        - true_anomaly    - where along it's orbit it starts, as in near r_a or near r_p or so
        - orbit_direction - in which direction (in degrees) of the star it starts
        - planet_angle  - does it go clockwise or anticlockwise

        The method:
        1. Starts with a minimum semi-major axis (just beyond the star).
        2. For each planet, picks a new semi-major axis by multiplying the previous orbit
            by a random factor (ensuring increasing distance).
        3. Samples a low eccentricity from a beta distribution.
        4. Determines the planet's radius from a lognormal distribution whose mean is slightly
            shifted with the orbit distance.
        5. Calculates the orbit geometry and initial position/velocity.
        6. Updates the minimum allowed semi-major axis for the next planet.
        """

        if not isinstance(self.__star, Star):
            return []
        disk = self.__star
        planets = []
        current_min_a = disk.radius * 2

        for _ in range(num_planets):
            # random variables
            semi_major_axis = current_min_a * random.uniform(1.0, 1.25)
            mu = planet_size_parameter + ORBIT_CORRELATION_FACTOR * math.log(semi_major_axis)
            radius_planet = min(random.lognormvariate(mu, SIGMA_PLANET_RADIUS), self.max_nonstar_size / 2)
            eccentricity = random.betavariate(1, 15)
            true_anomaly = random.uniform(0, 2 * math.pi)
            orbit_direction = random.uniform(0, 2 * math.pi)
            planet_angle = random.choice([90, 270])

            # pos_planet
            r_initial = (semi_major_axis * (1 - eccentricity**2)) / (1 + eccentricity * math.cos(true_anomaly))
            radial_vector = Vec2(1, 0).rotate(math.degrees(true_anomaly + orbit_direction))
            pos_planet = radial_vector * r_initial

            # velocity_planet
            total_specific_energy = -GRAVITATIONAL_CONSTANT * disk.mass / (2 * semi_major_axis)
            orbital_velocity = (2 * (GRAVITATIONAL_CONSTANT * disk.mass / r_initial + total_specific_energy)) ** 0.5
            tangential_vector = radial_vector.rotate(planet_angle)
            vel_planet = tangential_vector * orbital_velocity

            planets.append(
                self.add_planet(
                    PlanetConfig(relative_pos=pos_planet, relative_vel=vel_planet, radius=radius_planet),
                    relative_to=disk,
                )
            )
            r_a = semi_major_axis * (1 + eccentricity)
            # Update current_min_a to just beyond this planet's apastron to avoid overlapping orbits:.
            current_min_a = r_a + radius_planet
        return planets

    def _nearby_planets(self, pos: Pos) -> Iterator[Planet]:
        (x, y) = self._pobj_to_planet_chunk(pos)
        for i in range(-1, 2):
            for j in range(-1, 2):
                chunk = (x + i, y + j)
                yield from self._planet_chunks.get(chunk, [])

    def find_nearest_object_to(self, pos: Pos) -> PosVel | None:
        """Find the nearest object (planet, enemy ship, or star) to the given position."""
        min_dist = float("inf")
        nearest = None

        for item in chain(self._nearby_planets(pos), self._enemy_ships):
            dist = item.distance_squared_to(pos)
            if dist < min_dist:
                min_dist = dist
                nearest = item
        if isinstance(self.__star, Star):
            dist = self.__star.distance_squared_to(pos)
            if dist < min_dist:
                min_dist = dist
                nearest = self.__star

        return nearest

    def apply_gravity_to(self, pobj: Disk, dt: float) -> None:
        """Affect pobj by `self`'s entire gravity."""
        force_sum = Vec2(0, 0)

        if isinstance(self.__star, Star):
            force_sum += pobj.gravitational_force(self.__star)
        for disk in self._nearby_planets(pobj):
            force_sum += pobj.gravitational_force(disk)

        pobj.apply_force(force_sum, dt)

    @global_profiler.profile_method
    def apply_gravity(self, dt: float) -> None:
        """Apply gravity to all of `self`'s objects."""
        for pobj in chain(self._player_ships, self._enemy_ships, *self._planet_chunks.values()):
            self.apply_gravity_to(pobj, dt)

    @global_profiler.profile_method
    def apply_bounce(self) -> None:
        """Run all bounce-interactions within `self`."""
        ships: Sequence[Ship] = [*self._player_ships, *self._enemy_ships]

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
                ship.suffer_damage(1e100)  # 💀

        # Bounce planets
        for planet in chain(*self._planet_chunks.values()):
            # TODO: Could this be optimised by not checking all pairs of planets?
            for disk in self._nearby_planets(planet):
                planet.bounce_disks(disk)
            if isinstance(self.__star, Star):
                planet.bounce_disks(self.__star)

    @global_profiler.profile_method
    def collide_bullets(self) -> None:
        """Run bullet-collision checks and damage ships as a result."""

        def projectile_check(projectile: Bullet) -> bool:
            """Check for collision and return whether the projectile should stay alive."""
            if projectile.is_expired() or (isinstance(self.__star, Star) and self.__star.intersects_disk(projectile)):
                return False
            for planet in self._nearby_planets(projectile):
                if planet.intersects_disk(projectile):
                    self.create_particles_on_disk(planet, projectile, 5, projectile.color, 250)
                    return False
            for ship in chain(self._player_ships, self._enemy_ships):
                if ship.intersects_disk(projectile):
                    self.create_particle_cloud(ship, 100, ship.color, 150)
                    ship.suffer_damage(projectile.DAMAGE)
                    return False
                if (isinstance(projectile, Missile | Rocket)) and any(
                    other_projectile.distance_squared_to(projectile) < 10**2
                    for other_projectile in ship.projectiles
                    if other_projectile is not projectile
                ):
                    self.create_particle_cloud(projectile, 50, projectile.color, 200)
                    return False

            return True

        for ship in chain(self._player_ships, self._enemy_ships):
            ship.projectiles = [p for p in ship.projectiles if projectile_check(p)]

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Run input-logic for player-ships.

        `keys` is typically retreived using `pygame.key.get_pressed()`.
        """
        for player_ship in self._player_ships:
            player_ship.handle_input(keys)

    @global_profiler.profile_method
    def step(self, dt: float) -> None:
        """Run the universe-logic, also for the object `self` contains."""
        # Ship
        for player_ship in self._player_ships:
            player_ship.update_closest_enemy(self._enemy_ships)
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

        self._particles = [p for p in self._particles if p.step_and_survives(dt)]

        # Physics
        self.apply_gravity(dt)
        self.apply_bounce()
        self.collide_bullets()
        self._enemy_ships = [ship for ship in self._enemy_ships if ship.health > 0]

    def create_particles_on_disk(self, disk: Disk, projected_from: Pos, n: int, color: Color, blast_vel: float) -> None:
        """Create `n` particles on the disk's surface.

        `projected_from` is projected onto `disk`'s surface, with velocity randomly sampled to face
        away from `disk` with max-length `blast_vel` in addition to `disk`'s current velocity.
        Colors are randomly sampled from interpolation
        between `disk.color` and `color`.

        The particles' lifetime is randomly sampled from (0.5, 1.0).

        If pos is exactly on disk's center, nothing happens.
        """
        delta = projected_from.pos_relative_to(disk)
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

    def create_particle_cloud(self, source: PosVel, n: int, color: Color, blast_vel: float) -> None:
        """Create `n` particles forming a blast-cloud around pos.

        Particles' velocity are spherically sampled with length between 0 and blast_vel, added
        to `initial_vel`.

        The particles' lifetime is randomly sampled from (1.0, 2.0).
        """
        angle = random.random() * 360
        for _ in range(n):
            random_lifetime = random.lognormvariate(1.5, 0.2)
            random_vel = Vec2(0, 0)
            random_vel.from_polar(
                (blast_vel * random.lognormvariate(0.3, 0.4), angle + random.normalvariate(0.0, 50.0))
            )
            self._particles.append(Particle(source, Vec2(0, 0), random_vel, color, random_lifetime))

    @global_profiler.profile_method
    def draw_background(self, camera: Camera) -> None:
        """Draw `self`'s parallaxing background on `camera`."""
        # TODO: Update this with respect to relativity.
        return
        # Store random_state. we're about to use random.seed() and want to use "normal" rng later.
        random_state = random.getstate()
        # TODO: Try caching star-chunks to their final on-screen locations.  # noqa: FIX002
        # If doing that, also optimise x_chunk_size for performance (via profiling) again.
        camera._surface.lock()  # noqa: SLF001
        camera_size = Vec2(camera._surface.get_size())  # noqa: SLF001
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

        camera._surface.unlock()  # noqa: SLF001
        random.setstate(random_state)

    @global_profiler.profile_method
    def draw_text(self, camera: Camera, player: PlayerShip, fps: float) -> None:
        """Draw "debugging" text on `camera`."""
        font_size = 32
        font = pygame.font.Font(None, font_size)

        def texty(vertical_offset: int, text: str | None = None) -> int:
            if text is not None:
                camera.draw_text(text, Vec2(10, vertical_offset), font, Color("white"))
            return vertical_offset + font_size

        text_v = 10
        text_v = texty(text_v, f"{fps:.0f} fps")
        text_v = texty(text_v, f"Health: {player.health:.0f}")
        if player.max_repair_health - player.health > 1:
            text_v = texty(text_v, f"Repairable Damage: {player.max_repair_health - player.health:.0f}")
        text_v = texty(text_v, f"Fuel: {player.fuel:.0f}")
        """
        Useful for debugging purposes:
        if player.closest_enemy:
            direction = player.closest_enemy.pos_relative_to(player)
            text_v = texty(
                text_v, f"Closest Enemy at: {direction[0]:.0f},{direction[1]:.0f} distance is {direction.length():.0f}"
            )
            text_v = texty(text_v, f"Enemy State: {player.closest_enemy.ai.current_state}")
            text_v = texty(text_v, f"Enemy Health: {player.closest_enemy.health:.0f}")
            text_v = texty(text_v, f"Enemy Low Health: {player.closest_enemy.ai.low_health}")
        """
        enemy_count = len(self._enemy_ships)
        text_v = texty(text_v, f"Enemies left: {enemy_count}")

    @global_profiler.profile_method
    def draw_grid(self, camera: Camera) -> None:
        """Draw a polar grid centered on the star."""
        center = self.__star

        for r in range(GRID_RADIAL_SPACING, MAX_RADIUS + 1, GRID_RADIAL_SPACING):
            camera.draw_circle(GRID_COLOR, center, r, 2)

        for angle in range(0, 360, ANGULAR_SPACING * 2):
            end_vector = Vec2(0, -1).rotate(angle) * MAX_RADIUS
            camera.draw_line(GRID_COLOR, Pos(center, -end_vector), Pos(center, end_vector), 2)

    @global_profiler.profile_method
    def draw(self, camera: Camera, *, minimap: bool = False) -> None:
        """Draw all of `self` on `camera`."""
        if not minimap:
            self.draw_background(camera)
            self.draw_grid(camera)

        for obj in chain(*self._planet_chunks.values(), self._enemy_ships, self._player_ships):
            obj.draw(camera)

        if isinstance(self.__star, Star):
            self.__star.draw(camera)

        if not minimap:
            for particle in self._particles:
                particle.draw(camera)
