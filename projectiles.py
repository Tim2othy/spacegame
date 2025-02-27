"""Projectiles, shooting through space."""

from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from physics import PhysicalObject

if TYPE_CHECKING:
    from ship import Ship

from constants import (
    MISSILE_HOMING_DURATION,
    MISSILE_HOMING_THRUST,
    MISSILE_MIN_SPEED,
    ROCKET_HOMING_DURATION,
    ROCKET_HOMING_THRUST,
    ROCKET_NONHOMING_DURATION,
)


class Bullet(PhysicalObject):
    """A triangular bullet."""

    def __init__(self, pos: Vec2, vel: Vec2, color: Color) -> None:
        """Create a new basic Bullet.

        Args:
            pos (Vec2): Start position
            vel (Vec2): Velocity
            color (Color): Border- and fill-color

        """
        super().__init__(pos, vel, 1.0)
        self.color = Color(color)

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`.

        Args:
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
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            color (Color): Border- and fill-color
            target_ship (Ship): Ship to home in on

        """
        super().__init__(pos, vel, color)
        self.target_ship = target_ship
        self.homing_thrust = ROCKET_HOMING_THRUST * self.mass
        self.homing_timer = 0.0
        self.homing_duration = ROCKET_HOMING_DURATION
        self.nonhoming_duration = ROCKET_NONHOMING_DURATION
        self._total_duration = self.homing_duration + self.nonhoming_duration
        self.color = Color("red")

    def step(self, dt: float) -> None:
        """Apply homing and physics-logic.

        Args:
            dt (float): Passed time

        """
        self.homing_timer = (self.homing_timer + dt) % self._total_duration

        if self.homing_timer <= self.homing_duration:
            # Target the ship
            direction = self.target_ship.pos - self.pos
            if direction == Vec2(0, 0):
                return
            normalized_direction = (self.target_ship.pos - self.pos).normalize()
            force = normalized_direction * self.homing_thrust
            self.apply_force(force, dt)

        super().step(dt)

    def draw(self, camera: Camera) -> None:
        """Draw `self` to `camera`.

        Args:
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
            self.color = Color("red    ")

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


class Missile(Bullet):
    """A pentagonal bullet, homing on a target-ship."""

    def __init__(self, pos: Vec2, vel: Vec2, color: Color, target_ship: "Ship") -> None:
        """Create a new Missile targeting `target_ship`.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            color (Color): Border- and fill-color
            target_ship (Ship): Ship to home in on

        """
        super().__init__(pos, vel, color)
        self.target_ship = target_ship
        self.homing_thrust = MISSILE_HOMING_THRUST * self.mass
        self.homing_timer = 0.0
        self.homing_duration = MISSILE_HOMING_DURATION
        self.color = Color("orange")

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`.

        Args:
            camera (Camera): Camera to draw on

        """
        forward = self.vel.normalize() if self.vel != Vec2(0, 0) else Vec2(1, 0)
        left = Vec2(-forward.y, forward.x)
        right = -left
        backward = -forward

        camera.draw_polygon(
            self.color,
            [
                self.pos + 3 * (left + forward),
                self.pos + 5 * (left + 5 * backward),
                self.pos + 5 * (right + 5 * backward),
                self.pos + 3 * (right + forward),
                self.pos + 2 * (8 * forward),
            ],
        )

    def step(self, dt: float) -> None:
        """Apply homing and physics-logic.

        Args:
            dt (float): Passed time

        """
        self.homing_timer += dt
        delta_target_ship = self.target_ship.pos - self.pos
        if delta_target_ship != Vec2(0, 0) and self.homing_timer <= self.homing_duration:
            target_ship_direction = delta_target_ship.normalize()
            multiplier = max(self.target_ship.vel.magnitude() * 1.1, MISSILE_MIN_SPEED)
            desired_velocity = target_ship_direction * multiplier
            force_direction = desired_velocity - self.vel

            if force_direction == Vec2(0, 0):
                return
            force = force_direction.normalize() * self.homing_thrust
            self.apply_force(force, dt)
        super().step(dt)


class Flair(Bullet):
    """A round bullet, bobbing about."""

    def __init__(self, pos: Vec2, vel: Vec2, color: Color) -> None:
        """Create a new flair.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Velocity
            color (Color): Border- and fill-color

        """
        super().__init__(pos, vel, color)
        self.color = Color("yellow")

    def draw(self, camera: Camera) -> None:
        """Draw `self` to `camera`."""
        camera.draw_circle(self.color,self.pos, 3)
