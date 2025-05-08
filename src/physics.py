"""Physical objects, and the interactions between them."""

from __future__ import annotations

import math
from enum import Enum, auto
from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

if TYPE_CHECKING:
    from camera import Camera

SMALL_ANGLE = 5
SMALL_ANGULAR_VEL = 5.0


class ThrustState(Enum):
    """Possible thrust states for the ship."""

    NONE = auto()
    FORWARD = auto()
    BACKWARD = auto()


class RotationState(Enum):
    """Possible rotation states for the ship."""

    NONE = auto()
    LEFT = auto()
    RIGHT = auto()


GRAVITATIONAL_CONSTANT = 0.02

GRAY = Color("gray")


# physics constants
BOUNCINESS = 0.7
"""0 <= BOUNCINESS <= 1. Set to 1, collisions cause no damage."""

BOUNCE_DAMAGE_THRESHOLD = 1.3e6
"""Impulse-scalar gets reduced by this (and clamped from negative to 0) before calculating damage."""

BOUNCE_DAMAGE_SCALAR = 1e-4
"""Bounce-damage is scaled by this amount."""


class Pos:
    """An object with a dynamic position, but no velocity."""

    def __init__(self, relative_to: Pos, relative_pos: Vec2) -> None:
        """Create a new Pos relative to another Pos."""
        self.__pos: Vec2 = relative_to.__pos + relative_pos

    def _shift(self, delta: Vec2) -> None:
        """Shift `self`'s position by `delta`. Don't use this unless you know what you're doing."""
        self.__pos += delta

    def pos_relative_to(self, other: Pos) -> Vec2:
        """Return `self`'s position relative to `other`."""
        return self.__pos - other.__pos

    def distance_squared_to(self, other: Pos) -> float:
        """Return the squared distance between `self` and `other`."""
        return self.pos_relative_to(other).length_squared()

    def distance_to(self, other: Pos) -> float:
        """Return the distance between `self` and `other`."""
        return self.pos_relative_to(other).length()


class PosVel(Pos):
    """An object with dynamic position and dynamic velocity."""

    def __init__(self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2) -> None:
        """Create a new PosVel relative to another PosVel."""
        super().__init__(relative_to, relative_pos)
        self.__vel: Vec2 = relative_to.__vel + relative_vel

    @staticmethod
    def _new_origin_and_only_use_this_if_you_really_know_what_you_are_doing() -> PosVel:
        """Create a new PosVel that can act as an origin to bootstrap other PosVels.

        You probably want to create a universe instead.

        PosVels need to be created relative to other PosVels, so this PosVel
        can act as an ur-object.
        """
        # This is messed up. Think thrice before copying this code.
        origin = object.__new__(PosVel)
        setattr(origin, "_Pos__pos", Vec2(0, 0))  # noqa: B010
        origin.__vel = Vec2(0, 0)  # noqa: SLF001
        return origin

    def step(self, dt: float) -> None:
        """Apply velocity to `self`."""
        self._shift(self.__vel * dt)

    def _add_vel(self, vel: Vec2) -> None:
        """Add `vel` to  `self`'s velocity. Be careful with relativity."""
        self.__vel += vel

    def vel_relative_to(self, other: PosVel) -> Vec2:
        """Return `self`'s velocity relative to `other`."""
        return self.__vel - other.__vel


class Particle(PosVel):
    """A single-pixel particle with a color, velocity, and limited lifetime."""

    def __init__(
        self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, color: Color, lifetime: float
    ) -> None:
        """Create a new Particle."""
        super().__init__(relative_to, relative_pos, relative_vel)
        self._base_color: Color = Color(color)
        self._max_lifetime: float = lifetime
        self._lifetime: float = lifetime

    def step_and_survives(self, dt: float) -> bool:
        """Apply velocity to self and reduce lifetime. Return whether the lifetime has elapsed."""
        self.step(dt)
        self._lifetime -= dt
        return self._lifetime > 0

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`."""
        camera.draw_pixel(self._base_color, max(0, min(1, self._lifetime / self._max_lifetime)), self)


class Disk(PosVel):
    """A disk with dynamic position, dynamic velocity, constant radius and dynamic color."""

    def __init__(
        self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, radius: float, color: Color = GRAY
    ) -> None:
        """Create a new Disk. Mass will be calculated as if it were a sphere, though."""
        super().__init__(relative_to, relative_pos, relative_vel)
        if not (math.isfinite(radius) and radius > 0):
            raise ValueError
        self.radius: float = radius
        self.__radius_squared: float = radius**2
        self.color: Color = Color(color)
        self.mass = radius**3 * math.pi * 4 / 3
        self.angle: float = 0.0
        self.angular_velocity: float = 0.0

    def add_impulse(self, impulse: Vec2) -> None:
        """Add an impulse to `self`."""
        self._add_vel(impulse / self.mass)

    def apply_force(self, force: Vec2, dt: float) -> None:
        """Apply a force to `self`."""
        self.add_impulse(force * dt)

    def add_angular_impulse(self, angular_impulse: float) -> None:
        """Add an angular impulse to `self`."""
        moment_of_inertia = 0.5 * self.mass * self.radius**2
        self.angular_velocity += angular_impulse / moment_of_inertia

    def apply_angular_force(self, force: float, dt: float) -> None:
        """Apply an angular force to `self`."""
        self.add_angular_impulse(force * dt)

    def gravitational_force(self, pobj: Disk) -> Vec2:
        """Calculate gravitational force between `pobj` and `self` affecting `self`."""
        delta = pobj.pos_relative_to(self)
        if delta == Vec2(0, 0):
            return Vec2(0, 0)
        dist_squared = delta.length_squared()
        force_length = GRAVITATIONAL_CONSTANT * self.mass * pobj.mass / dist_squared
        normalised_delta = delta / math.sqrt(dist_squared)
        return normalised_delta * force_length

    def draw(self, camera: Camera, color: Color | None = None) -> None:
        """Draw `self` on `camera` with optional color argument."""
        draw_color = color or self.color
        camera.draw_circle(draw_color, self, self.radius)

    def intersects_disk(self, other: Disk) -> bool:
        """Determine whether `self` intersects `other`.

        a.intersects_disk(b) should always return the same as b.intersects_disk(a),
        barring floating-point rounding-errors.
        """
        return self.distance_squared_to(other) < (self.radius + other.radius) ** 2

    def bounce_disks(self, other: Disk) -> float | None:
        """Bounce two disks off each other if they are overlapping.

        If a bounce occurs, this shifts the two disks' positions so that
        they're exactly flush. This shift respects the difference between
        the two disks' mass.

        Returns the damage the two disks take from the collision, or None if no bounce occured.
        The damage is identical for both disks, i.e. it assumes a heavier disk
        can take more damage.

        If the two disks have exactly the same center, they are treated as if they
        were slightly offset from each other, with no guarantee about this behavior's
        stability.
        """
        delta = other.pos_relative_to(self)
        radii_sum = self.radius + other.radius
        distance_squared = delta.length_squared()

        # Check for intersection
        if distance_squared >= radii_sum**2:
            return None

        # Compute the distance; if 0 (disks on top of each other) choose an arbitrary normal.
        distance = math.sqrt(distance_squared)
        normal = delta / distance if distance_squared > 0 else Vec2(1, 0)

        relative_velocity = other.vel_relative_to(self)
        vel_along_normal = relative_velocity.dot(normal)

        # If the disks are moving apart already, skip the collision response.
        if vel_along_normal > 0:
            return None

        # Compute impulse scalar based on the collision response formula.
        impulse_scalar = -(1 + BOUNCINESS) * vel_along_normal
        impulse_scalar /= 1 / self.mass + 1 / other.mass
        impulse = impulse_scalar * normal

        self.add_impulse(-impulse)
        other.add_impulse(impulse)

        # Position correction: push the disks apart so that they are just touching.
        # Respect the relative mass.
        overlap = radii_sum - distance
        correction = normal * overlap
        if math.isfinite(self.mass):
            self._shift(-correction * (1 - self.mass / (self.mass + other.mass)))
        if math.isfinite(other.mass):
            other._shift(correction * (1 - other.mass / (self.mass + other.mass)))

        # Return damage
        return max(0, impulse_scalar - BOUNCE_DAMAGE_THRESHOLD) * (1 - BOUNCINESS) * BOUNCE_DAMAGE_SCALAR

    def step(self, dt: float) -> None:
        """Apply velocity to `self` and angular velocity to `self`."""
        self.angle += self.angular_velocity * dt
        super().step(dt)


class Mover(Disk):
    """A disk that can apply force to itself and move around."""

    def __init__(
        self, relative_to: PosVel, relative_pos: Vec2, relative_vel: Vec2, radius: float, color: Color = GRAY
    ) -> None:
        """Initialize a Mover, inheriting from Disk."""
        super().__init__(relative_to, relative_pos, relative_vel, radius, color)
        self.forward: Vec2 = Vec2(0, 0)
        self.rotation_state = RotationState.NONE
        self.thrust_state = ThrustState.NONE

    def get_faced_direction(self) -> Vec2:
        """Get `self`'s (normalized) faced direction from its `angle`."""
        direction = Vec2(0, 0)
        direction.from_polar((1, self.angle))
        return direction

    def step(self, dt: float) -> None:
        """Get direction and do moving logic."""
        self.forward = self.get_faced_direction()
        return super().step(dt)
