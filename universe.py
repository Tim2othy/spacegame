"""If you wish to collect celestial bodies, spaceships, and everything else,
you must first invent the universe."""

import pygame
import pygame.camera
from pygame import Color, Rect
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
        color: Color,
    ):
        """Create a new planet.

        Args:
            pos (Vector2): Fixed position
            density (float): Density
            radius (float): Radius
            color (Color): Color
        """
        super().__init__(pos, Vector2(0, 0), density, radius, color)


class Asteroid(Disk):
    """A gray disk that doesn't exert gravitational force, and isn't stationary."""

    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        density: float,
        radius: float,
    ):
        """Create a new Asteroid.
        Any color you like, as long as it's gray.

        Args:
            pos (Vector2): Initial position
            vel (Vector2): Initial velocity
            density (float): Density
            radius (float): Radius
        """
        super().__init__(pos, vel, density, radius, Color("gray"))


class Area(Rect):
    """A rectangular area that triggers an event for a ship."""

    def __init__(
        self,
        rect: Rect,
        color: Color,
        caption: str,
    ):
        """Create a new area

        Args:
            rect (Rect): Rectangular area
            color (Color): Color
            caption (str): Area's "Name"
        """
        super().__init__(rect)
        self.color = color
        self.caption = caption

    def draw(self, camera: Camera):
        """Draw `self` on `camera`

        Args:
            camera (Camera): Camera to draw on
        """
        camera.draw_rect(self.color, self)

    def event(self, ship: Ship):
        """An event to trigger for a ship entering `self`

        Args:
            ship (Ship): Affected `ship`
        """
        pass


class RefuelArea(Area):
    """Refuel every ship entering this."""

    def __init__(
        self,
        rect: Rect,
    ):
        """Create a RefuelArea

        Args:
            rect (Rect): Rectangular area
        """
        super().__init__(rect, Color("yellow"), "Refuel")

    def event(self, ship: Ship):
        """Refuel `ship`

        Args:
            ship (Ship): Ship to refuel
        """
        ship.fuel = ship.max_fuel


class TrophyArea(Area):
    """Give every ship entering this a trophy."""

    def __init__(self, rect: Rect):
        """Create a TrophyArea

        Args:
            rect (Rect): Rectangular area
        """
        super().__init__(rect, Color("gold"), "Trophy")

    def event(self, ship: Ship):
        """Give `ship` a trophy

        Args:
            ship (Ship): Ship to give a trophy to
        """
        ship.has_trophy = True


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
        areas: list[Area],
        enemy_ships: list[BulletEnemy],
    ):
        """Create a new universe (not in the big-bang way, sadly)

        Args:
            size (Vector2): Width and height
            planets (list[Planet]): Planets
            asteroids (list[Asteroid]): Asteroids
            player_ship (Ship): Player's ship
            areas (list[Area]): Areas
            enemy_ships (list[BulletEnemy]): Enemy fleet
        """
        self.size = size
        self.planets = planets
        self.asteroids = asteroids
        self.player_ship = player_ship
        self.areas = areas
        self.enemy_ships = enemy_ships

    def apply_gravity_to_obj(self, dt: float, pobj: PhysicalObject):
        """Have pobj be affected by `self`'s entire gravity

        Args:
            dt (float): Passed time
            pobj (PhysicalObject): Object to affect
        """
        force_sum = Vector2(0, 0)
        for body in self.planets:
            force_sum += pobj.gravitational_force(body)
        pobj.apply_force(force_sum, dt)

    def apply_gravity(self, dt: float):
        """Apply gravity to all of `self`'s objects

        Args:
            dt (float): Passed time
        """
        self.apply_gravity_to_obj(dt, self.player_ship)
        for enemy_ship in self.enemy_ships:
            self.apply_gravity_to_obj(dt, enemy_ship)
        for asteroid in self.asteroids:
            self.apply_gravity_to_obj(dt, asteroid)

    def apply_bounce_to_disk(self, disk: Disk) -> float | None:
        """Bounce a disk off of each of `self`s objects

        Args:
            disk (Disk): Disk to bounce

        Returns:
            float | None: If float, impact velocity of first bounce.
                If None, no impact occured.
        """
        for body in self.asteroids + self.planets:
            damage = disk.bounce_off_of_disk(body)
            if damage is not None:
                return damage
        return None

    def apply_bounce(self):
        """Run all bounce-interactions within `self`."""
        damage = self.apply_bounce_to_disk(self.player_ship)
        if damage is not None:
            self.player_ship.suffer_damage(damage)
        for enemy_ship in self.enemy_ships:
            self.apply_bounce_to_disk(enemy_ship)
        for asteroid in self.asteroids:
            other_asteroids = [ast for ast in self.asteroids if ast != asteroid]
            for disk in other_asteroids + self.planets:
                asteroid.bounce_off_of_disk(disk)

    def asteroids_or_planets_intersect_point(self, vec: Vector2) -> bool:
        """Test whether any of `self`'s planets or asteroids intersect `vec`

        Args:
            vec (Vector2): Position to test for intersection

        Returns:
            bool: True iff any intersect
        """
        return any(
            map(lambda planet: planet.intersects_point(vec), self.planets)
        ) or any(map(lambda asteroid: asteroid.intersects_point(vec), self.asteroids))

    def step(self, dt: float):
        """Run the universe-logic, also for the object `self` contains.

        Args:
            dt (float): Passed time
        """
        # Call `step` on everything
        self.player_ship.step(dt)
        for ship in self.enemy_ships:
            ship.step(dt)
        for asteroid in self.asteroids:
            asteroid.step(dt)

        # Physics
        self.apply_gravity(dt)
        self.apply_bounce()

        # Areas
        for area in self.areas:
            if area.collidepoint(self.player_ship.pos):
                area.event(self.player_ship)

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
                    self.player_ship.suffer_damage(10)
                    ship.projectiles.remove(projectile)
                    continue

    def draw(self, camera: Camera):
        """Draw all of `self` on `camera`

        Args:
            camera (Camera): Camera to draw on
        """
        self.draw_grid(camera)
        for area in self.areas:
            area.draw(camera)
        for asteroid in self.asteroids:
            asteroid.draw(camera)
        for planet in self.planets:
            planet.draw(camera)
        for ship in self.enemy_ships:
            ship.draw(camera)
        self.player_ship.draw(camera)

    def draw_text(self, camera: Camera):
        """Draw "debugging" text about `self` on `camera`

        Args:
            camera (Camera): Camera to draw on
        """
        font_size = 32
        font = pygame.font.Font(None, font_size)

        self.text_vertical_offset = 10

        def texty(text: str | None = None):
            if text is not None:
                camera.draw_text(
                    text, Vector2(10, self.text_vertical_offset), font, Color("white")
                )
            self.text_vertical_offset += 1.0 * font_size

        ship = self.player_ship
        texty(f"({int(ship.pos.x)}, {int(ship.pos.y)})")
        texty(f"Velocity: ({int(ship.vel.x)}, {int(ship.vel.y)})")
        texty(f"Remaining Fuel: {ship.fuel:.2f}")
        texty(f"Trophy: {"Collected" if ship.has_trophy else "Not collected"}")
        texty(f"Health: {ship.health:.2f}")
        texty(f"Ammunition: {ship.ammo}")
        for area in self.areas:
            texty(f"  Coordinates of {area.caption}: ({area.centerx}, {area.centery})")
        texty(f"{len(ship.projectiles)} projectiles from you")
        enemy_projectile_count = sum(len(e.projectiles) for e in self.enemy_ships)
        texty(f"{enemy_projectile_count} enemy projectiles")

        del self.text_vertical_offset

    def draw_grid(self, camera: Camera):
        """Draw grid on `camera`

        Args:
            camera (Camera): Camera to draw on
        """
        grid_color = Color("darkgreen")
        gridline_spacing = 5000
        width = self.size.x
        height = self.size.y

        for x in range(0, int(width + 1), gridline_spacing):
            camera.draw_hairline(grid_color, Vector2(x, 0), Vector2(x, height))

        for y in range(0, int(height + 1), gridline_spacing):
            camera.draw_hairline(grid_color, Vector2(0, y), Vector2(width, y))

    def contains_point(self, vec: Vector2) -> bool:
        """Test whether `vec` is contained in `self`'s boundaries

        Args:
            vec (Vector2): Vec to test for containment

        Returns:
            bool: True iff `self` contains `vec`
        """
        return 0 <= vec.x <= self.size.x and 0 <= vec.y <= self.size.y

    def clamp_point(self, vec: Vector2) -> Vector2:
        """Return `vec` clamped to be within `self`'s bounds.

        Args:
            vec (Vector2): Point to clamp into `self`

        Returns:
            Vector2: The clamped point. Unchanged if it already was in `self`.
        """
        return Vector2(max(0, min(self.size.x, vec.x)), max(0, min(self.size.y, vec.y)))
