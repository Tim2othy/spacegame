"""Projectiles, shooting through space."""

from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera
from physics import Body, PosVel

if TYPE_CHECKING:
    from ship import Ship

from constants import THRUST_COLOR

# Damage
BULLET_DAMAGE = 16
ROCKET_DAMAGE = 26
MISSILE_DAMAGE = 60
FLARE_DAMAGE = 10
# Thrust
ROCKET_HOMING_THRUST = 300.0
MISSILE_HOMING_THRUST = 600.0
# Homing
ROCKET_HOMING_DURATION = 2.0
ROCKET_NONHOMING_DURATION = 2.0
MISSILE_HOMING_DURATION = 20.0

ROCKET_TIMES_HOMES = 3
ROCKET_MIN_SPEED = 500.0

FLARE_COLOR = Color("yellow")


class Bullet(Body):
    """A triangular bullet."""

    def __init__(self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, color: Color) -> None:
        """Create a new basic Bullet.

        Args:
            pos (Vec2): Start position
            vel (Vec2): Velocity
            color (Color): Border- and fill-color

        """
        super().__init__(relative_to, relative_pos, relative_vel, 1.0)
        self.color = Color(color)
        self.damage = BULLET_DAMAGE

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`.

        Args:
            camera (Camera): Camera to draw on

        """
        forward = self._vel.normalize() if self._vel != Vec2(0, 0) else Vec2(1, 0)
        camera.draw_polygon(
            self.color,
            [
                self._pos + 4 * forward,
                self._pos + 4 * forward.rotate(150),
                self._pos + 4 * forward.rotate(-150),
            ],
        )


class Rocket(Bullet):
    """A pentagonal bullet, homing on a target-ship."""

    def __init__(
        self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, color: Color, target_ship: "Ship"
    ) -> None:
        """Create a new rocket targeting `target_ship`.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            color (Color): Border- and fill-color
            target_ship (Ship): Ship to home in on

        """
        super().__init__(relative_to, relative_pos, relative_vel, color)
        self.target_ship = target_ship
        self.homing_thrust = ROCKET_HOMING_THRUST * self.mass
        self.homing_timer = 0.0
        self.homing_duration = ROCKET_HOMING_DURATION
        self.nonhoming_duration = ROCKET_NONHOMING_DURATION
        self._cycle_duration = self.homing_duration + self.nonhoming_duration
        self.color = Color(color)
        self.damage = ROCKET_DAMAGE

    def step(self, dt: float) -> None:
        """Apply homing and physics-logics.

        Args:
            dt (float): Passed time

        """
        self.homing_timer += dt
        delta_target_ship = self.target_ship.pos_relative_to(self)

        current_cycle = int(self.homing_timer / self._cycle_duration)
        time_in_current_cycle = self.homing_timer % self._cycle_duration
        is_homing_phase = time_in_current_cycle <= self.homing_duration

        # Only home if we're in a homing phase and haven't exceeded 3 cycles
        if current_cycle < ROCKET_TIMES_HOMES and is_homing_phase and delta_target_ship != Vec2(0, 0):
            target_ship_direction = delta_target_ship.normalize()

            desired_velocity = target_ship_direction * ROCKET_MIN_SPEED
            force_direction = desired_velocity - self.vel_relative_to(self.target_ship)

            if force_direction != Vec2(0, 0):
                force = force_direction.normalize() * self.homing_thrust
                self.apply_force(force, dt)
        super().step(dt)

    def draw(self, camera: Camera) -> None:
        """Draw `self` to `camera`.

        Args:
            camera (Camera): Camera to draw on

        """
        forward = self._vel.normalize() if self._vel != Vec2(0, 0) else Vec2(1, 0)
        left = Vec2(-forward.y, forward.x)
        right = -left
        backward = -forward

        current_cycle = int(self.homing_timer / self._cycle_duration)
        time_in_current_cycle = self.homing_timer % self._cycle_duration
        is_homing_phase = time_in_current_cycle <= self.homing_duration

        if current_cycle < ROCKET_TIMES_HOMES and is_homing_phase:
            # Thrust flame
            camera.draw_polygon(
                self.color.lerp(THRUST_COLOR, 0.5),
                [
                    self._pos + 3 * (left + backward),
                    self._pos + 4 * (left + 2 * backward),
                    self._pos + 4 * (right + 2 * backward),
                    self._pos + 3 * (right + backward),
                ],
            )

        # Missile body
        camera.draw_polygon(
            self.color,
            [
                self._pos + 3 * (left + forward),
                self._pos + 3 * (left + backward),
                self._pos + 3 * (right + backward),
                self._pos + 3 * (right + forward),
                self._pos + 2 * (3 * forward),
            ],
        )


class Missile(Rocket):
    """A pentagonal bullet, homing on a target-ship."""

    def __init__(
        self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, color: Color, target_ship: "Ship"
    ) -> None:
        """Create a new Missile targeting `target_ship`.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            color (Color): Border- and fill-color
            target_ship (Ship): Ship to home in on

        """
        super().__init__(relative_to, relative_pos, relative_vel, color, target_ship)
        self.homing_thrust = MISSILE_HOMING_THRUST * self.mass
        self.homing_timer = 0.0
        self.homing_duration = MISSILE_HOMING_DURATION
        self.damage = MISSILE_DAMAGE

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`.

        Args:
            camera (Camera): Camera to draw on

        """
        forward = self._vel.normalize() if self._vel != Vec2(0, 0) else Vec2(1, 0)
        left = Vec2(-forward.y, forward.x)
        right = -left
        backward = -forward

        camera.draw_polygon(
            self.color,
            [
                self._pos + 3 * (left + forward),
                self._pos + 5 * (left + 5 * backward),
                self._pos + 5 * (right + 5 * backward),
                self._pos + 3 * (right + forward),
                self._pos + 2 * (8 * forward),
            ],
        )


class Flare(Bullet):
    """A round bullet, bobbing about."""

    def __init__(self, pos: Vec2, vel: Vec2) -> None:
        """Create a new flare.

        Args:
            pos (Vec2): Initial position
            vel (Vec2): Velocity

        """
        super().__init__(pos, vel, FLARE_COLOR)
        self.damage = FLARE_DAMAGE

    def draw(self, camera: Camera) -> None:
        """Draw `self` to `camera`."""
        # TODO: This is no longer necessary if bullets finally become subclasses of Disk
        camera.draw_circle(self.color, self, 3)
