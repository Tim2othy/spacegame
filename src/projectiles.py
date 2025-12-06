"""Projectiles, shooting through space."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import BasicAI, Mover, Pos, PosVel, ThrustState

if TYPE_CHECKING:
    from camera import Camera
    from ship import Ship

# Damage
BULLET_DAMAGE = 16
ROCKET_DAMAGE = 18
MISSILE_DAMAGE = 24
FLARE_DAMAGE = 6
# Thrust
ROCKET_THRUST_COLOR = Color("orange")
ROCKET_HOMING_THRUST = 1400.0
MISSILE_HOMING_THRUST = 2600.0
PROJECTILE_ROTATION_THRUST = 4000.0
# Homing
ROCKET_HOMING_DURATION = 2.0
ROCKET_NONHOMING_DURATION = 2.0
MISSILE_HOMING_DURATION = 30.0

ROCKET_TIMES_HOMES = 3

FLARE_COLOR = Color("yellow")

PROJECTILE_LIFETIME = 40.0  # Lifetime in seconds


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

        # Convert decreasing timer to the equivalent increasing timer logic
        total_duration = ROCKET_TIMES_HOMES * self.CYCLE_DURATION
        elapsed_time = total_duration - self.ai.action_timer

        current_cycle = int(elapsed_time / self.CYCLE_DURATION)
        time_in_current_cycle = elapsed_time % self.CYCLE_DURATION
        is_homing_phase = time_in_current_cycle <= self.HOMING_DURATION

        if current_cycle < ROCKET_TIMES_HOMES and is_homing_phase:
            # Thrust flame
            camera.draw_polygon(
                ROCKET_THRUST_COLOR,
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
        camera.draw_circle(color or self.color, self, 5)


class ProjectileAI(BasicAI):
    """AI for enemy ships with a countdown timer instead of a count-up timer."""

    def __init__(self, projectile: Rocket) -> None:
        """Create a new AI controller."""
        super().__init__()
        self.projectile: Rocket = projectile

        # Initialize with total homing time
        total_cycle_time = ROCKET_TIMES_HOMES * projectile.CYCLE_DURATION
        self.action_timer = total_cycle_time

    def step(self, dt: float) -> None:
        """Apply homing behavior based on a decreasing timer."""
        # Decrease timer instead of increasing it
        self.action_timer -= dt

        self.delta_target = self.projectile.target.pos_relative_to(self.projectile)
        self.delta_target_vel = self.projectile.target.vel_relative_to(self.projectile)

        # Determine which cycle we're in and position within that cycle
        total_duration = ROCKET_TIMES_HOMES * self.projectile.CYCLE_DURATION
        elapsed_time = total_duration - self.action_timer

        # Calculate the same values as in the original version
        current_cycle = int(elapsed_time / self.projectile.CYCLE_DURATION)
        time_in_current_cycle = elapsed_time % self.projectile.CYCLE_DURATION
        is_homing_phase = time_in_current_cycle <= self.projectile.HOMING_DURATION

        # Logic remains the same as original
        if current_cycle < ROCKET_TIMES_HOMES and is_homing_phase and self.delta_target != Vec2(0, 0):
            self._execute_ram()

        self.projectile.rotation_state = self.projectile.calculate_rotation(self.desired_direction)
        self.projectile.thrust_state = ThrustState.FORWARD
