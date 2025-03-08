"""Physical objects, and the interactions between them."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

if TYPE_CHECKING:
    from camera import Camera

from constants import GRAVITATIONAL_CONSTANT

BLACK = Color("black")
GRAY = Color("gray")


# physics constants
BOUNCINESS = 0.7
"""0 <= BOUNCINESS <= 1. Set to 1, collisions cause no damage."""

BOUNCE_DAMAGE_THRESHOLD = 1.3e6
"""Impulse-scalar gets reduced by this (and clamped from negative to 0) before calculating damage."""

BOUNCE_DAMAGE_SCALAR = 1e-4
"""Bounce-damage is scaled by this amount."""


class MovingObject:
    """An object with dynamic position and dynamic velocity."""

    def __init__(self, relative_to: MovingObject, relative_pos: Vec2, relative_vel: Vec2) -> None:
        """Create a new MovingObject relative to another MovingObject."""
        self.__pos: Vec2 = relative_to.__pos + relative_pos
        self.__vel: Vec2 = relative_to.__vel + relative_vel

    def step(self, dt: float) -> None:
        """Apply velocity to `self`."""
        self.__pos += dt * self.__vel

    def add_vel(self, vel: Vec2) -> None:
        """Add `vel` to  `self`'s velocity. Be careful with relativity."""
        self.__vel += vel

    def pos_relative_to(self, other: MovingObject) -> Vec2:
        """Return `self`'s position relative to `other`.

        >>> a = MovingObject(Vec2(2, 3), Vec2())
        >>> b = MovingObject(Vec2(1, 1), Vec2())
        >>> a.pos_relative_to(b)
        Vector2(1, 2)
        """
        return self.__pos - other.__pos

    def vel_relative_to(self, other: MovingObject) -> Vec2:
        """Return `self`'s velocity relative to `other`.

        >>> a = MovingObject(Vec2(), Vec2(2, 3))
        >>> b = MovingObject(Vec2(), Vec2(1, 1))
        >>> a.vel_relative_to(b)
        Vector2(1, 2)
        """
        return self.__vel - other.__vel

    def distance_squared_to(self, other: MovingObject) -> float:
        """Return the squared distance between `self` and `other`."""
        return self.pos_relative_to(other).length_squared()

    def distance_to(self, other: MovingObject) -> float:
        """Return the distance between `self` and `other`."""
        return self.pos_relative_to(other).length()


class Particle(MovingObject):
    """A single-pixel particle with a color, velocity, and limited lifetime."""

    def __init__(
        self, relative_to: MovingObject, relative_pos: Vec2, relative_vel: Vec2, color: Color, lifetime: float
    ) -> None:
        """Create a new Particle."""
        super().__init__(relative_to, relative_pos, relative_vel)
        self._base_color: Color = Color(color)
        self._max_lifetime: float = lifetime
        self._lifetime: float = lifetime

    def step(self, dt: float) -> bool:
        """Apply velocity to self and reduce lifetime. Return whether the lifetime has elapsed."""
        super().step(dt)
        self._lifetime -= dt
        return self._lifetime > 0

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`."""
        color = BLACK.lerp(self._base_color, max(0, min(1, self._lifetime / self._max_lifetime)))
        camera.draw_pixel(color, self._pos)


class PhysicalObject(MovingObject):
    """A physical object with dynamic position, dynamic velocity, and dynamic strictly positive mass."""

    def __init__(self, relative_to: MovingObject, relative_pos: Vec2, relative_vel: Vec2, mass: float) -> None:
        """Create a new PhysicalObject. Raises a ValueError if the mass is not strictly positive.

        >>> PhysicalObject(Vec2(), Vec2(), 1).mass
        1
        >>> PhysicalObject(Vec2(), Vec2(), -1).mass
        Traceback (most recent call last):
            ...
        ValueError

        """
        super().__init__(relative_to, relative_pos, relative_vel)
        if not mass > 0:
            raise ValueError
        self.mass: float = mass

    def add_impulse(self, impulse: Vec2) -> None:
        """Add an impulse to `self`."""
        self.add_vel(impulse / self.mass)

    def apply_force(self, force: Vec2, dt: float) -> None:
        """Apply a force to `self`."""
        self.add_impulse(force * dt)

    def gravitational_force(self, pobj: PhysicalObject) -> Vec2:
        """Calculate gravitational force between `pobj` and `self` affecting `self`."""
        delta = pobj.pos_relative_to(self)
        if delta == Vec2(0, 0):
            return Vec2(0, 0)
        dist_squared = delta.length_squared()
        force_length = GRAVITATIONAL_CONSTANT * self.mass * pobj.mass / dist_squared
        normalised_delta = delta / math.sqrt(dist_squared)
        return normalised_delta * force_length

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`. Implemented by subclasses."""


class Disk(PhysicalObject):
    """A disk-shaped PhysicalObject, with constant radius and dynamic color."""

    def __init__(
        self, relative_to: MovingObject, relative_pos: Vec2, relative_vel: Vec2, radius: float, color: Color = GRAY
    ) -> None:
        """Create a new Disk. Mass will be calculated as if it were a sphere, though."""
        mass = radius**3 * math.pi * 4 / 3
        super().__init__(relative_to, relative_pos, relative_vel, mass)
        self.radius: float = radius
        self.__radius_squared: float = radius**2
        self.color: Color = Color(color)

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`."""
        camera.draw_circle(self.color, self._pos, self.radius)

    def contains_center_of(self, mobj: MovingObject) -> bool:
        """Determine whether the center of `mobj` is in `self`.

        >>> disk = Disk(Vec2(0,0), Vec2(), radius=2, color=Color(0, 0, 0))
        >>> disk.contains_center_of(MovingObject(Vec2(0, 0), Vec2()))
        True
        >>> disk.contains_center_of(MovingObject(Vec2(1, -1), Vec2()))
        True
        >>> disk.contains_center_of(MovingObject(Vec2(2, 1), Vec2()))
        False

        """
        return self.distance_squared_to(mobj) < self.__radius_squared

    def intersects_disk(self, other: Disk) -> bool:
        """Determine whether `self` intersects `other`.

        a.intersects_disk(b) should always return the same as b.intersects_disk(a),
        barring floating-point rounding-errors.

        >>> disk_a = Disk(Vec2(0,0), Vec2(), radius=2, color=Color(0, 0, 0))
        >>> disk_b = Disk(Vec2(2,1), Vec2(), radius=1, color=Color(0, 0, 0))
        >>> disk_a.intersects_disk(disk_b) or disk_b.intersects_disk(disk_a)
        True
        >>> disk_c = Disk(Vec2(3,1), Vec2(), radius=0.5, color=Color(0, 0, 0))
        >>> disk_a.intersects_disk(disk_c) or disk_c.intersects_disk(disk_a)
        False
        >>> disk_b.intersects_disk(disk_c) and disk_c.intersects_disk(disk_b)
        True

        """
        return self.distance_squared_to(other) < (self.radius + other.radius) ** 2

    def bounce_disks(self, other: Disk) -> float | None:
        """Bounce two disks off each other if they are overlapping.

        If a bounce occurs, this shifts the two disks' positions so that
        they're exactly flush. This shift respects the difference between
        the two disks' mass.

        Returns the damage the two disks take from the collision.
        The damage is identical for both disks, i.e. it assumes a heavier disk
        can take more damage.

        If the two disks have exactly the same center, they are treated as if they
        were slightly offset from each other, with no guarantee about this behavior's
        stability.

        Returns:
            float | None: If float, impact velocity of bounce. None if no bounce occurred.

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
            self._pos -= correction * (1 - self.mass / (self.mass + other.mass))
        if math.isfinite(other.mass):
            other._pos += correction * (1 - other.mass / (self.mass + other.mass))  # noqa: SLF001

        # Return damage
        return max(0, impulse_scalar - BOUNCE_DAMAGE_THRESHOLD) * (1 - BOUNCINESS) * BOUNCE_DAMAGE_SCALAR

    def bounce_off_of_disk(self, other: Disk) -> float | None:
        """Bounce self disks off of `disk` if they are overlapping.

        If a bounce occurs, this shifts self's positions so that
        they're exactly flush.

        Returns the damage self takes from the collision.

        If the two disks have exactly the same center, they are treated as if they
        were slightly offset from each other, with no guarantee about this behavior's
        stability.

        Returns:
            float | None: If float, impact velocity of bounce. None if no bounce occurred.

        """
        # HACK: Treat the static disk as if it had infinite mass
        old_mass, other.mass = other.mass, float("inf")
        bounce = self.bounce_disks(other)
        other.mass = old_mass
        return bounce
