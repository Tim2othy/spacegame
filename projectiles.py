"""Projectiles, shooting through space."""

from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from physics import PhysicalObject

if TYPE_CHECKING:
    from ship import Ship


class Bullet(PhysicalObject):
    """A triangular bullet."""

    def __init__(self, pos: Vec2, vel: Vec2, color: Color) -> None:
        """Create a new basic Bullet.

        Args:
        ----
            pos (Vec2): Start position
            vel (Vec2): Velocity
            color (Color): Border- and fill-color

        """
        super().__init__(pos, vel, 1.0)
        self.color = Color(color)

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        forward = self.vel.normalize() if self.vel != Vec2(0, 0) else Vec2(1, 0)
        camera.draw_polygon(
            self.color,
            [
                self.pos + 4 * forward,
                self.pos + 4 * forward.rotate(150),
                self.pos + 4 * forward.rotate(-150),
            ],
        )


class Rocket(Bullet):
    """A pentagonal bullet, homing on a target-ship."""

    def __init__(self, pos: Vec2, vel: Vec2, color: Color, target_ship: "Ship") -> None:
        """Create a new rocket targeting `target_ship`.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            color (Color): Border- and fill-color
            target_ship (Ship): Ship to home in on

        """
        super().__init__(pos, vel, color)
        self.target_ship = target_ship
        self.vel *= 0  # Sholud have the velocity of the shooting ship but nothing else.
        self.homing_thrust = 200 * self.mass
        self.homing_timer = 0
        self.homing_duration = 3
        self.nonhoming_duration = 9
        self._total_duration = self.homing_duration + self.nonhoming_duration
        self.color = Color("red")

    def step(self, dt: float) -> None:
        """Apply homing and physics-logic.

        Args:
        ----
            dt (float): Passed time

        """
        self.homing_timer = (self.homing_timer + dt) % self._total_duration

        if self.homing_timer <= self.homing_duration:
            # Target the ship
            direction = self.target_ship.pos - self.pos
            if direction != Vec2(0, 0):
                direction.normalize_ip()
                self.apply_force(direction * self.homing_thrust, dt)

        super().step(dt)

    def draw(self, camera: Camera) -> None:
        """Draw `self` to `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        forward = self.vel.normalize() if self.vel != Vec2(0, 0) else Vec2(1, 0)
        left = Vec2(-forward.y, forward.x)
        right = -left
        backward = -forward

        # Spooky homing body
        if self.homing_timer <= self.homing_duration:
            self.color = Color("purple")
            camera.draw_polygon(
                self.color.lerp(Color("blue"), 0.5),
                [
                    self.pos + 4 * (left + forward),
                    self.pos + 4 * (left + backward),
                    self.pos + 4 * (right + backward),
                    self.pos + 4 * (right + forward),
                ],
            )
        else:
            self.color = Color("darkblue    ")

        # Missile body
        camera.draw_polygon(
            self.color,
            [
                self.pos + 3 * (left + forward),
                self.pos + 3 * (left + backward),
                self.pos + 3 * (right + backward),
                self.pos + 3 * (right + forward),
                self.pos + 2 * (3 * forward),
            ],
        )
