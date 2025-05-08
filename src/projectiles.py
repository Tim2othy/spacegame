"""Projectiles, shooting through space."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import Mover, Pos, PosVel, RotationState, ThrustState

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

    DAMAGE = BULLET_DAMAGE

    def __init__(self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, color: Color) -> None:
        """Create a new basic Bullet."""
        super().__init__(relative_to, relative_pos, relative_vel, 1.0)
        self.color = Color(color)
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
        forward = Vec2(1, 0) if self.relative_vel.length_squared() == 0 else self.relative_vel.normalize()
        camera.draw_polygon(
            color or self.color,
            [Pos(self, 4 * forward), Pos(self, 4 * forward.rotate(150)), Pos(self, 4 * forward.rotate(-150))],
        )


class Rocket(Bullet):
    """A pentagonal bullet, homing on a target-ship."""

    THRUST = ROCKET_HOMING_THRUST
    ROTATION_THRUST = PROJECTILE_ROTATION_THRUST
    HOMING_DURATION = ROCKET_HOMING_DURATION
    NONHOMING_DURATION = ROCKET_NONHOMING_DURATION
    DAMAGE = ROCKET_DAMAGE
    CYCLE_DURATION = HOMING_DURATION + NONHOMING_DURATION

    def __init__(
        self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, color: Color, target_ship: Ship
    ) -> None:
        """Create a new rocket targeting `target_ship`."""
        super().__init__(relative_to, relative_pos, relative_vel, color)
        self.target = target_ship
        self.color = Color(color)
        self.ai = ProjectileAI(self)

    def step(self, dt: float) -> None:
        """Apply homing and physics-logics."""
        self.ai.step(dt)
        super().step(dt)

    def draw(self, camera: Camera, color: Color | None = None) -> None:
        """Draw `self` to `camera`."""
        draw_color = color or self.color
        forward = self.forward
        left = Vec2(-forward.y, forward.x)
        right = -left
        backward = -forward

        current_cycle = int(self.ai.action_timer / self.CYCLE_DURATION)
        time_in_current_cycle = self.ai.action_timer % self.CYCLE_DURATION
        is_homing_phase = time_in_current_cycle <= self.HOMING_DURATION

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
    """A pentagonal bullet, homing on target-ship."""

    THRUST = MISSILE_HOMING_THRUST
    HOMING_DURATION = MISSILE_HOMING_DURATION
    DAMAGE = MISSILE_DAMAGE

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

    DAMAGE = FLARE_DAMAGE

    def __init__(self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2) -> None:
        """Create a new flare."""
        super().__init__(relative_to, relative_pos, relative_vel, FLARE_COLOR)

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
        self.action_timer += dt
        delta_target_ship = self.projectile.target.pos_relative_to(self.projectile)

        current_cycle = int(self.action_timer / self.projectile.CYCLE_DURATION)
        time_in_current_cycle = self.action_timer % self.projectile.CYCLE_DURATION
        is_homing_phase = time_in_current_cycle <= self.projectile.HOMING_DURATION

        # Only home if we're in a homing phase and haven't exceeded 3 cycles
        if current_cycle < ROCKET_TIMES_HOMES and is_homing_phase and delta_target_ship != Vec2(0, 0):
            target_ship_direction = delta_target_ship.normalize()

            desired_velocity = target_ship_direction * ROCKET_MIN_SPEED
            force_direction = desired_velocity - self.projectile.vel_relative_to(self.projectile.target)

            if force_direction != Vec2(0, 0):
                self.my_force = force_direction.normalize() * self.projectile.THRUST

        self.projectile.rotation_state, self.projectile.thrust_state = self._match()

    def _match(self) -> tuple[RotationState, ThrustState]:
        """Match current state to behavior."""
        desired_direction = self.my_force
        rotation_state = self.projectile.calculate_rotation(desired_direction)

        return rotation_state, ThrustState.FORWARD
