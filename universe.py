"""If you wish to collect celestial bodies, spaceships, and
everything else, you must first invent the universe.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Color, Rect
from pygame.math import Vector2 as Vec2

from physics import Disk, PhysicalObject

if TYPE_CHECKING:
    from camera import Camera
    from ship import BulletEnemy, PlayerShip, Ship


class Planet(Disk):
    """A stationary disk."""

    def __init__(
        self,
        pos: Vec2,
        density: float,
        radius: float,
        color: Color,
        bullet_color: Color,
    ) -> None:
        """Create a new planet.

        Args:
        ----
            pos (Vec2): Fixed position
            density (float): Density
            radius (float): Radius
            color (Color): Color

        """
        super().__init__(pos, Vec2(0, 0), density, radius, color, bullet_color)


class Asteroid(Disk):
    """A gray disk that doesn't exert gravitational force, and isn't stationary."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        density: float,
        radius: float,
        bullet_color: Color,
    ) -> None:
        """Create a new Asteroid.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            density (float): Density
            radius (float): Radius

        """
        super().__init__(pos, vel, density, radius, Color("gray"), bullet_color)


class Area(Rect):
    """A rectangular area that triggers an event for a ship."""

    def __init__(
        self,
        rect: Rect,
        color: Color,
        caption: str,
    ) -> None:
        """Create a new area.

        Args:
        ----
            rect (Rect): Rectangular area
            color (Color): Color
            caption (str): Area's "Name"

        """
        super().__init__(rect)
        self.color = color
        self.caption = caption

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        camera.draw_rect(self.color, self)

    def event(self, ship: Ship) -> None:
        """Trigger event for a ship entering `self`.

        Args:
        ----
            ship (Ship): Affected `ship`

        """


class RefuelArea(Area):
    """Refuel every ship entering this."""

    def __init__(
        self,
        rect: Rect,
    ) -> None:
        """Create a RefuelArea.

        Args:
        ----
            rect (Rect): Rectangular area

        """
        super().__init__(rect, Color("yellow"), "Refuel")

    def event(self, ship: Ship) -> None:
        """Refuel `ship`.

        Args:
        ----
            ship (Ship): Ship to refuel

        """
        ship.fuel = ship.max_fuel


class TrophyArea(Area):
    """Give every ship entering this a trophy."""

    def __init__(self, rect: Rect) -> None:
        """Create a TrophyArea.

        Args:
        ----
            rect (Rect): Rectangular area

        """
        super().__init__(rect, Color("gold"), "Trophy")

    def event(self, ship: Ship) -> None:
        """Give `ship` a trophy.

        Args:
        ----
            ship (Ship): Ship to give a trophy to

        """
        ship.has_trophy = True


class Universe:
    """A collection of celestial objects, forming a Universe.

    Its width is size.x, its height is size.y.
    Coordinates are implicitly zero-based.
    """

    def __init__(
        self,
        size: Vec2,
        planets: list[Planet],
        asteroids: list[Asteroid],
        player_ships: list[PlayerShip],
        areas: list[Area],
        enemy_ships: list[BulletEnemy],
    ) -> None:
        """Create a new universe (not in the big-bang way, sadly).

        Args:
        ----
            size (Vec2): Width and height
            planets (list[Planet]): Planets
            asteroids (list[Asteroid]): Asteroids
            player_ships (list[Ship]): List of player-ships
            areas (list[Area]): Areas
            enemy_ships (list[BulletEnemy]): Enemy fleet

        """
        self.size = Vec2(size)
        self.planets = planets
        self.asteroids = asteroids
        self.player_ships = player_ships
        self.areas = areas
        self.enemy_ships = enemy_ships

    def apply_gravity_to_obj(self, dt: float, pobj: PhysicalObject) -> None:
        """Affect pobj by `self`'s entire gravity.

        Args:
        ----
            dt (float): Passed time
            pobj (PhysicalObject): Object to affect

        """
        force_sum = Vec2(0, 0)
        for body in self.planets:
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

    def apply_bounce_to_disk(self, disk: Disk) -> float | None:
        """Bounce a disk off of each of `self`s objects.

        Args:
        ----
            disk (Disk): Disk to bounce

        Returns:
        -------
            float | None: If float, impact velocity of first bounce.
                If None, no impact occured.

        """
        for body in self.asteroids + self.planets:
            damage = disk.bounce_off_of_disk(body)
            if damage is not None:
                return damage
        return None

    def apply_bounce(self) -> None:
        """Run all bounce-interactions within `self`."""
        for player_ship in self.player_ships:
            damage = self.apply_bounce_to_disk(player_ship)
            if damage is not None:
                player_ship.suffer_damage(damage)
        for enemy_ship in self.enemy_ships:
            self.apply_bounce_to_disk(enemy_ship)
        for asteroid in self.asteroids:
            other_asteroids = [ast for ast in self.asteroids if ast != asteroid]
            for disk in other_asteroids + self.planets:
                asteroid.bounce_off_of_disk(disk)

    def asteroids_or_planets_intersect_point(self, vec: Vec2) -> bool:
        """Test whether any of `self`'s planets or asteroids intersect `vec`.

        Args:
        ----
            vec (Vec2): Position to test for intersection

        Returns:
        -------
            bool: True iff any intersect

        """
        return any(planet.intersects_point(vec) for planet in self.planets) or any(
            asteroid.intersects_point(vec) for asteroid in self.asteroids
        )

    def collide_bullets(self) -> None:
        """Run bullet-collision checks and damage ships as a result."""
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
                        player_ship.suffer_damage(10)
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

        # Areas
        for area in self.areas:
            for player_ship in self.player_ships:
                if area.collidepoint(player_ship.pos):
                    area.event(player_ship)

        self.collide_bullets()

    def draw(self, camera: Camera) -> None:
        """Draw all of `self` on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        for pobj in (
            self.areas
            + self.asteroids
            + self.planets
            + self.enemy_ships
            + self.player_ships
        ):
            pobj.draw(camera)

    def draw_text(self, camera: Camera, player_ix: int) -> None:
        """Draw "debugging" text on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on
            player_ix (int): Player to display information about

        """
        font_size = 32
        font = pygame.font.Font(None, font_size)

        self.text_vertical_offset = 10

        def texty(text: str | None = None) -> None:
            if text is not None:
                camera.draw_text(
                    text, Vec2(10, self.text_vertical_offset), font, Color("white"),
                )
            self.text_vertical_offset += 1.0 * font_size

        player_ship = self.player_ships[player_ix]
        texty(f"({int(player_ship.pos.x)}, {int(player_ship.pos.y)})")
        texty(f"Velocity: ({int(player_ship.vel.x)}, {int(player_ship.vel.y)})")
        texty(f"Remaining Fuel: {player_ship.fuel:.2f}")
        texty(f"Trophy: {"Collected" if player_ship.has_trophy else "Not collected"}")
        texty(f"Health: {player_ship.health:.2f}")
        texty(f"Ammunition: {player_ship.ammo}")
        for area in self.areas:
            texty(f"  Coordinates of {area.caption}: ({area.centerx}, {area.centery})")
        player_projectile_count = sum(len(p.projectiles) for p in self.player_ships)
        enemy_projectile_count = sum(len(e.projectiles) for e in self.enemy_ships)
        texty(f"{player_projectile_count} player projectiles")
        texty(f"{enemy_projectile_count} enemy projectiles")

        enemy_count = len(self.enemy_ships)
        texty(f"Enemies left: {enemy_count}")

        del self.text_vertical_offset

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
