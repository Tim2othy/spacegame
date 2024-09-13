"""If you wish to collect celestial bodies, spaceships, and
everything else, you must first invent the universe.
"""

from __future__ import annotations

import math
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
    ) -> None:
        """Create a new planet.

        Args:
        ----
            pos (Vec2): Fixed position
            density (float): Density
            radius (float): Radius
            color (Color): Color

        """
        super().__init__(pos, Vec2(0, 0), density, radius, color)


class Universe:
    """A collection of celestial objects, forming a Universe.

    Its width is size.x, its height is size.y.
    Coordinates are implicitly zero-based.
    """

    def __init__(
        self,
        size: Vec2,
        island: list[Planet],
        player: list[PlayerShip],
        enemy: list[BulletEnemy],
    ) -> None:
        """Create a new universe (not in the big-bang way, sadly).

        Args:
        ----
            size (Vec2): Width and height
            island (list[Planet]): island
            player (list[Ship]): List of player-ships
            enemy (list[BulletEnemy]): Enemy fleet


        """
        self.size = Vec2(size)
        self.island = island
        self.player = player
        self.enemy = enemy

    def collide_bullets(self) -> None:
        """Run bullet-collision checks and damage ships as a result."""
        for player_ship in self.player:
            for projectile in player_ship.projectiles:
                if not self.contains_point(projectile.pos):
                    player_ship.projectiles.remove(projectile)
                    continue
                for enemy_ship in self.enemy:
                    if enemy_ship.intersects_point(projectile.pos):
                        self.enemy.remove(enemy_ship)
                        player_ship.projectiles.remove(projectile)
                        break
        for enemy_ship in self.enemy:
            for projectile in enemy_ship.projectiles:
                if not self.contains_point(projectile.pos):
                    enemy_ship.projectiles.remove(projectile)
                    continue
                for player_ship in self.player:
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
        for player_ship in self.player:
            player_ship.handle_input(keys)

    def move_camera(self, camera: Camera, player_ix: int, dt: float) -> None:
        """Move the camera to `self.player[player_ix]`.

        Args:
        ----
            camera (Camera): Camera to move
            player_ix (int): Player to focus on
            dt (float): Passed time

        """
        ship = self.player[player_ix]
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
        for ship in self.player + self.enemy:
            ship.step(dt)

        # Physics

        self.collide_bullets()

    def draw(self, camera: Camera) -> None:
        """Draw all of `self` on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        for pobj in self.island + self.enemy + self.player:
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
                    text,
                    Vec2(10, self.text_vertical_offset),
                    font,
                    Color("white"),
                )
            self.text_vertical_offset += 1.0 * font_size

        player_ship = self.player[player_ix]
        # texty(f"({int(player_ship.pos.x)}, {int(player_ship.pos.y)})")
        # texty(f"Velocity: ({int(player_ship.vel.x)}, {int(player_ship.vel.y)})")
        # texty(f"Fuel: {player_ship.fuel:.2f}")
        texty(f"Health: {player_ship.health:.2f}")
        texty(f"Ammunition: {player_ship.ammo}")

        # player_projectile_count = sum(len(p.projectiles) for p in self.player)
        # enemy_projectile_count = sum(len(e.projectiles) for e in self.enemy)
        # texty(f"{player_projectile_count} player projectiles")
        # texty(f"{enemy_projectile_count} enemy projectiles")

        # enemy_count = len(self.enemy)
        # texty(f"Enemies left: {enemy_count}")

        del self.text_vertical_offset

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
