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
    EPSILON,
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

    def bounce_off_of_disk(self, disk: Disk) -> float | None:
        """Bounce `self` off of `disk`, iff the two intersect.

        If a bounce occurs, this changes `self.pos` so that it's flush with `disk`,
        and has velocity in the opposite direction.

        Calculates intensity that `self` moved towards `disk` at moment of collision and
        returns calculated impact-damage.

        If the two disks have exactly the same center, they are treated as if they
        were slightly offset from each other, with no guarantee about this behavior's
        stability.

        Args:
        ----
            disk (Disk): Disk to potentially bounce off of

        Returns:
        -------
            float | None: If float, it's `self`'s suffered damage.
                If None, the two didn't intersect.

        """
        if not self.intersects_disk(disk):
            return None

        # Calculate normal vector
        delta = self.pos - disk.pos
        if delta == Vec2(0, 0):
            delta = Vec2(EPSILON, EPSILON)
        delta_magnitude = delta.magnitude()
        delta_normalized = delta / delta_magnitude

        # Move self outside other
        overlap = self.radius + disk.radius - delta_magnitude
        self.pos += delta_normalized * overlap

        self_vel_along_normal = self.vel.dot(delta_normalized)
        impulse_scalar = -(1 + BOUNCINESS) * self_vel_along_normal
        impulse_scalar /= 1 / self.mass + 1 / disk.mass

        self.add_impulse(delta_normalized * impulse_scalar)

        # Return damage.
        # Clamping in case of small impulses allows the ship to land on the planet.
        return max(0, impulse_scalar - BOUNCE_DAMAGE_THRESHOLD) * (1 - BOUNCINESS) * BOUNCE_DAMAGE_SCALAR
