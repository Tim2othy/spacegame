"""Projectiles, shooting through space."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import SMALL_ANGLE, SMALL_ANGULAR_VEL, Mover, Pos, PosVel, RotationState, ThrustState

if TYPE_CHECKING:
    from camera import Camera
    from ship import Ship


# Damage
BULLET_DAMAGE = 16
ROCKET_DAMAGE = 26
MISSILE_DAMAGE = 60
FLARE_DAMAGE = 10
# Thrust
ROCKET_THRUST_COLOR = Color("orange")
ROCKET_HOMING_THRUST = 1257.0
MISSILE_HOMING_THRUST = 2513.0
PROJECTILE_ROTATION_THRUST = 4000.0
# Homing
ROCKET_HOMING_DURATION = 2.0
ROCKET_NONHOMING_DURATION = 2.0
MISSILE_HOMING_DURATION = 20.0

ROCKET_TIMES_HOMES = 3
ROCKET_MIN_SPEED = 500.0

FLARE_COLOR = Color("yellow")

PROJECTILE_LIFETIME = 50.0  # Lifetime in seconds


class Bullet(Mover):
    """A triangular bullet."""

    def __init__(self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, color: Color) -> None:
        """Create a new basic Bullet."""
        super().__init__(relative_to, relative_pos, relative_vel, 1.0)
        self.color = Color(color)
        self.damage = BULLET_DAMAGE
        self.relative_vel = relative_vel
        self.lifetime = PROJECTILE_LIFETIME

    def step(self, dt: float) -> None:
        """Update the bullet's position and decrease its lifetime."""
        super().step(dt)
        self.lifetime -= dt

    def is_expired(self) -> bool:
        """Check if the bullet's lifetime has expired."""
        return self.lifetime <= 0

    def draw(self, camera: Camera, color: Color | None = None) -> None:
        """Draw `self` on `camera`."""
        # QUESTION: You wrote that we violate relativity if we don't use forward = Vec2(1,0), why?
        forward = Vec2(1, 0) if self.relative_vel.length_squared() == 0 else self.relative_vel.normalize()
        camera.draw_polygon(
            color or self.color,
            [Pos(self, 4 * forward), Pos(self, 4 * forward.rotate(150)), Pos(self, 4 * forward.rotate(-150))],
        )


class Rocket(Bullet):
    """A pentagonal bullet, homing on a target-ship."""

    def __init__(
        self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, color: Color, target_ship: Ship
    ) -> None:
        """Create a new rocket targeting `target_ship`."""
        super().__init__(relative_to, relative_pos, relative_vel, color)
        self.target = target_ship
        self.thrust = ROCKET_HOMING_THRUST
        self.rotation_thrust = PROJECTILE_ROTATION_THRUST
        self.homing_timer = 0.0
        self.homing_duration = ROCKET_HOMING_DURATION
        self.nonhoming_duration = ROCKET_NONHOMING_DURATION
        self._cycle_duration = self.homing_duration + self.nonhoming_duration
        self.color = Color(color)
        self.damage = ROCKET_DAMAGE
        self.current_heading = Vec2(0, 0)
        self.ai = ProjectileAI(self)

        self.rotation_state = RotationState.NONE
        self.thrust_state = ThrustState.NONE

    def step(self, dt: float) -> None:
        """Apply homing and physics-logics."""
        self.homing_timer += dt
        delta_target_ship = self.target.pos_relative_to(self)

        current_cycle = int(self.homing_timer / self._cycle_duration)
        time_in_current_cycle = self.homing_timer % self._cycle_duration
        is_homing_phase = time_in_current_cycle <= self.homing_duration

        # Only home if we're in a homing phase and haven't exceeded 3 cycles
        if current_cycle < ROCKET_TIMES_HOMES and is_homing_phase and delta_target_ship != Vec2(0, 0):
            target_ship_direction = delta_target_ship.normalize()

            desired_velocity = target_ship_direction * ROCKET_MIN_SPEED
            force_direction = desired_velocity - self.vel_relative_to(self.target)

            if force_direction != Vec2(0, 0):
                self.my_force = force_direction.normalize() * self.thrust

        self.ai.step(dt)

        self.step_thrust(dt)
        super().step(dt)

    def step_thrust(self, dt: float) -> None:
        """Step physics, control, and `self`'s bullets."""
        if self.rotation_state == RotationState.LEFT:
            self.apply_angular_force(self.rotation_thrust, dt)
        if self.rotation_state == RotationState.RIGHT:
            self.apply_angular_force(-self.rotation_thrust, dt)

        force = self.forward * self.thrust
        if self.thrust_state == ThrustState.FORWARD:
            self.apply_force(force, dt)
        if self.thrust_state == ThrustState.BACKWARD:
            self.apply_force(-force, dt)

    def draw(self, camera: Camera, color: Color | None = None) -> None:
        """Draw `self` to `camera`."""
        draw_color = color or self.color
        forward = self.forward
        left = Vec2(-forward.y, forward.x)
        right = -left
        backward = -forward

        current_cycle = int(self.homing_timer / self._cycle_duration)
        time_in_current_cycle = self.homing_timer % self._cycle_duration
        is_homing_phase = time_in_current_cycle <= self.homing_duration

        if current_cycle < ROCKET_TIMES_HOMES and is_homing_phase:
            # Thrust flame
            camera.draw_polygon(
                draw_color.lerp(ROCKET_THRUST_COLOR, 0.5),
                [
                    Pos(self, 3 * (left + backward)),
                    Pos(self, 4 * (left + 2 * backward)),
                    Pos(self, 4 * (right + 2 * backward)),
                    Pos(self, 3 * (right + backward)),
                ],
            )

        # Missile body
        camera.draw_polygon(
            draw_color,
            [
                Pos(self, 3 * (left + forward)),
                Pos(self, 3 * (left + backward)),
                Pos(self, 3 * (right + backward)),
                Pos(self, 3 * (right + forward)),
                Pos(self, 2 * (3 * forward)),
            ],
        )


class Missile(Rocket):
    """A pentagonal bullet, homing on a target-ship."""

    def __init__(
        self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, color: Color, target_ship: Ship
    ) -> None:
        """Create a new Missile targeting `target_ship`."""
        super().__init__(relative_to, relative_pos, relative_vel, color, target_ship)
        self.homing_thrust = MISSILE_HOMING_THRUST
        self.homing_duration = MISSILE_HOMING_DURATION
        self.damage = MISSILE_DAMAGE

    def draw(self, camera: Camera, color: Color | None = None) -> None:
        """Draw `self` on `camera`."""
        forward = self.forward
        left = Vec2(-forward.y, forward.x)
        right = -left
        backward = -forward

        camera.draw_polygon(
            color or self.color,
            [
                Pos(self, 3 * (left + forward)),
                Pos(self, 5 * (left + 5 * backward)),
                Pos(self, 5 * (right + 5 * backward)),
                Pos(self, 3 * (right + forward)),
                Pos(self, 2 * (8 * forward)),
            ],
        )


class Flare(Bullet):
    """A round bullet, designed to distract other bullets, but also capable of harming enemies."""

    def __init__(self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2) -> None:
        """Create a new flare."""
        super().__init__(relative_to, relative_pos, relative_vel, FLARE_COLOR)
        self.damage = FLARE_DAMAGE

    def draw(self, camera: Camera, color: Color | None = None) -> None:
        """Draw `self` to `camera`."""
        camera.draw_circle(color or self.color, self, 3)


class ProjectileAI:
    """AI for enemy ships."""

    def __init__(self, projectile: Rocket) -> None:
        """Create a new AI controller."""
        self.projectile: Rocket = projectile
        self.current_state: bool = False
        self.action_timer: float = 0.0
        self.delta_target: Vec2 = Vec2(1, 1)
        self.delta_target_vel: Vec2 = Vec2(1, 1)

    def step(self, dt: float) -> None:
        """Transition state and apply appropriate behavior for different enemy types."""
        self.projectile.rotation_state, self.projectile.thrust_state = self._match()

    def _match(self) -> tuple[RotationState, ThrustState]:
        """Match current state to behavior."""
        desired_direction = self.projectile.my_force
        rotation_state = self._calculate_rotation(desired_direction)

        return rotation_state, ThrustState.FORWARD

    def _calculate_rotation(self, desired_direction: Vec2) -> RotationState:
        """Calculate rotation state based on current angle, desired angle, and current angular velocity."""
        current_angle = self.projectile.angle
        angular_velocity = self.projectile.angular_velocity
        desired_angle = math.degrees(math.atan2(desired_direction.y, desired_direction.x))

        angle_diff = (desired_angle - current_angle + 180) % 360 - 180

        # Calculate stopping distance with current angular velocity
        moment_of_inertia = 0.5 * self.projectile.mass * self.projectile.radius**2
        rotation_accel = self.projectile.rotation_thrust / moment_of_inertia
        stopping_distance = (angular_velocity**2) / (2 * rotation_accel) * (1 if angular_velocity >= 0 else -1)

        # Predict where we would stop if we start decelerating now
        stopping_point = (current_angle + stopping_distance) % 360

        # Calculate the angle difference between where we would stop and the desired angle
        stopping_diff = (desired_angle - stopping_point + 180) % 360 - 180

        # If within small angle and velocity is low enough, don't rotate
        if abs(angle_diff) < SMALL_ANGLE and abs(angular_velocity) < SMALL_ANGULAR_VEL:
            return RotationState.NONE

        if angular_velocity > 0:  # Moving counterclockwise
            if stopping_diff > 0:  # We would stop before reaching the desired angle
                return RotationState.LEFT  # Continue accelerating counterclockwise
            # We would stop past the desired angle
            return RotationState.RIGHT  # Start decelerating

        if angular_velocity < 0:  # Moving clockwise
            if stopping_diff < 0:  # We would stop before reaching the desired angle
                return RotationState.RIGHT  # Continue accelerating clockwise
            # We would stop past the desired angle
            return RotationState.LEFT  # Start decelerating

        # If not moving yet, choose direction based on shortest angle
        return RotationState.LEFT if angle_diff > 0 else RotationState.RIGHT
