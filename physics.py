"""Physical objects, and the interactions between them."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

if TYPE_CHECKING:
    from camera import Camera

from constants import (
    BOUNCE_DAMAGE_SCALAR,
    BOUNCE_DAMAGE_THRESHOLD,
    BOUNCINESS,
    GRAVITATIONAL_CONSTANT,
)


class PhysicalObject:
    """A physical object with dynamic position, dynamic velocity, and constant strictly positive mass."""

    def __init__(self, pos: Vec2, vel: Vec2, mass: float) -> None:
        """Create a new PhysicalObject.

        Raises a ValueError if the mass is not strictly positive.

        Args:
        ----
            pos (Vec2): Object's position, usually its center
            vel (Vec2): Object's velocity (ignore relativity please)
            mass (float): Object's mass. Must be strictly positive.

        >>> PhysicalObject(Vec2(), Vec2(), 1).mass
        1
        >>> PhysicalObject(Vec2(), Vec2(), -1).mass
        Traceback (most recent call last):
            ...
        ValueError

        """
        self.pos = Vec2(pos)
        self.vel = Vec2(vel)
        if mass <= 0:
            raise ValueError
        self.mass = mass

    def step(self, dt: float) -> None:
        """Apply its velocity to `self`.

        Args:
        ----
            dt (float): Passed time

        """
        self.pos += dt * self.vel

    def add_impulse(self, impulse: Vec2) -> None:
        """Add an impulse to `self`.

        Args:
        ----
            impulse (Vec2): Impulse to apply

        """
        self.vel += impulse / self.mass

    def apply_force(self, force: Vec2, dt: float) -> None:
        """Apply a force to `self`.

        Args:
        ----
            force (Vec2): Force to apply
            dt (float): Passed time

        """
        self.add_impulse(force * dt)

    def gravitational_force(self, pobj: PhysicalObject) -> Vec2:
        """Calculate gravitational force between `pobj` and `self` affecting `self`.

        Args:
        ----
            pobj (PhysicalObject): Other PhysicalObject to gravitate towards

        Returns:
        -------
            Vec2: Resulting force to apply to `self`

        """
        delta = pobj.pos - self.pos  # point from `self` to `pobj`
        if delta == Vec2(0, 0):
            return Vec2(0, 0)
        dist_squared = delta.magnitude_squared()
        force_magnitude = GRAVITATIONAL_CONSTANT * self.mass * pobj.mass / dist_squared
        normalised_delta = delta / math.sqrt(dist_squared)
        return normalised_delta * force_magnitude

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`. Implemented by subclasses.

        Args:
        ----
            camera (Camera): Camera to draw on

        """


class Disk(PhysicalObject):
    """A disk-shaped PhysicalObject, with constant radius and dynamic color."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        density: float,
        radius: float,
        color: Color,
    ) -> None:
        """Create a new Disk. Mass will be calculated as if it were a sphere, though.

        Args:
        ----
            pos (Vec2): Disk's center
            vel (Vec2): Disk's velocity
            density (float): Disk's density
            radius (float): Disk's radius
            color (pygame.Color): Disk's color

        """
        mass = radius**3 * math.pi * 4 / 3 * density
        super().__init__(pos, vel, mass)
        self.radius = radius
        self.color = Color(color)
        self._radius_squared = radius**2

    def draw(self, camera: Camera) -> None:
        """Draw `self`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        camera.draw_circle(self.color, self.pos, self.radius)

    def intersects_point(self, vec: Vec2) -> bool:
        """Determine whether `vec` is in `self`.

        Args:
        ----
            vec (Vec2): Vector to test for intersection

        Returns:
        -------
            bool: True iff `vec` is in `self`

        >>> disk = Disk(Vec2(0,0), Vec2(), density=1, radius=2, color=Color(0, 0, 0))
        >>> disk.intersects_point(Vec2(0, 0))
        True
        >>> disk.intersects_point(Vec2(1, -1))
        True
        >>> disk.intersects_point(Vec2(2, 1))
        False

        """
        return self.pos.distance_squared_to(vec) < self._radius_squared

    def intersects_disk(self, disk: Disk) -> bool:
        """Determine whether `self` intersects another Disk.

        a.intersects_disk(b) should always return the same as b.intersects_disk(a),
        barring floating-point rounding-errors.

        Args:
        ----
            disk (Disk): Other disk

        Returns:
        -------
            bool: True iff the two disks intersect

        >>> disk_a = Disk(Vec2(0,0), Vec2(), density=1, radius=2, color=Color(0, 0, 0))
        >>> disk_b = Disk(Vec2(2,1), Vec2(), density=1, radius=1, color=Color(0, 0, 0))
        >>> disk_a.intersects_disk(disk_b) or disk_b.intersects_disk(disk_a)
        True
        >>> disk_c = Disk(Vec2(3,1), Vec2(), density=1, radius=0.5, color=Color(0, 0, 0))
        >>> disk_a.intersects_disk(disk_c) or disk_c.intersects_disk(disk_a)
        False
        >>> disk_b.intersects_disk(disk_c) and disk_c.intersects_disk(disk_b)
        True


        """
        return self.pos.distance_squared_to(disk.pos) < (self.radius + disk.radius) ** 2

    def bounce_disks(self, disk: Disk) -> float | None:
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

        Parameters
        ----------
            disk (Disk): The other disk to try bouncing off of.

        Returns
        -------
            float | None: If float, impact velocity of bounce. None if no bounce occurred.

        """
        delta = disk.pos - self.pos
        radii_sum = self.radius + disk.radius
        distance_squared = delta.magnitude_squared()

        # Check for intersection
        if distance_squared >= radii_sum**2:
            return None

        # Compute the distance; if 0 (disks on top of each other) choose an arbitrary normal.
        distance = math.sqrt(distance_squared)
        normal = delta / distance if distance_squared > 0 else Vec2(1, 0)

        relative_velocity = disk.vel - self.vel
        vel_along_normal = relative_velocity.dot(normal)

        # If the disks are moving apart already, skip the collision response.
        if vel_along_normal > 0:
            return None

        # Compute impulse scalar based on the collision response formula.
        impulse_scalar = -(1 + BOUNCINESS) * vel_along_normal
        impulse_scalar /= 1 / self.mass + 1 / disk.mass
        impulse = impulse_scalar * normal

        self.add_impulse(-impulse)
        disk.add_impulse(impulse)

        # Position correction: push the disks apart so that they are just touching.
        # Respect the relative mass.
        overlap = radii_sum - distance
        correction = normal * overlap
        if math.isfinite(self.mass):
            self.pos -= correction * (1 - self.mass / (self.mass + disk.mass))
        if math.isfinite(disk.mass):
            disk.pos += correction * (1 - disk.mass / (self.mass + disk.mass))

        # Return damage
        return max(0, impulse_scalar - BOUNCE_DAMAGE_THRESHOLD) * (1 - BOUNCINESS) * BOUNCE_DAMAGE_SCALAR

    def bounce_off_of_disk(self, disk: Disk) -> float | None:
        """Bounce self disks off of `disk` if they are overlapping.

        If a bounce occurs, this shifts self's positions so that
        they're exactly flush.

        Returns the damage self takes from the collision.

        If the two disks have exactly the same center, they are treated as if they
        were slightly offset from each other, with no guarantee about this behavior's
        stability.

        Parameters
        ----------
            disk (Disk): The other disk to try bouncing off of.

        Returns
        -------
            float | None: If float, impact velocity of bounce. None if no bounce occurred.

        """
        # HACK: Treat the static disk as if it had infinite mass
        old_mass, disk.mass = disk.mass, float("inf")
        bounce = self.bounce_disks(disk)
        disk.mass = old_mass
        return bounce
