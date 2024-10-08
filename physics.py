"""Physical objects, and the interactions between them."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pygame import Color
from pygame.math import Vector2 as Vec2

if TYPE_CHECKING:
    from camera import Camera

GRAVITATIONAL_CONSTANT = 0.03


class PhysicalObject:
    """A physical object with dynamic position, dynamic velocity,
    and constant nonzero mass.
    """

    def __init__(self, pos: Vec2, vel: Vec2, mass: float) -> None:
        """Create a new PhysicalObject.

        Args:
        ----
            pos (Vec2): Object's position, usually its center
            vel (Vec2): Object's velocity (ignore relativity please)
            mass (float): Object's mass

        """
        self.pos = Vec2(pos)
        self.mass = mass
        self.vel = Vec2(vel)

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
        bullet_color: Color,
    ) -> None:
        """Create a new Disk. Mass will be calculated as if it were a sphere, though.

        Args:
        ----
            pos (Vec2): Disk's center
            vel (Vec2): Disk's velocity
            density (float): Disk's density
            radius (float): Disk's radius
            color (pygame.Color): Disk's color
            bullet_color (pygame.Color): Disk's bullet's color, it has bullets

        """
        mass = radius**3 * math.pi * 4 / 3 * density
        super().__init__(pos, vel, mass)
        self.radius = radius
        self.color = Color(color)
        self.bulletcolor = Color(bullet_color)
        self._radius_squared = radius**2

    def draw(self, camera: Camera) -> None:
        """Draw anti-aliased `self`.

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

        """
        return self.pos.distance_squared_to(vec) < self._radius_squared

    def intersects_disk(self, disk: Disk) -> bool:
        """Determine whether `self` intersects another Disk.

        Args:
        ----
            disk (Disk): Other disk

        Returns:
        -------
            bool: True iff the two disks intersect

        """
        return self.pos.distance_squared_to(disk.pos) < (self.radius + disk.radius) ** 2

    def bounce_off_of_disk(self, disk: Disk) -> float | None:
        """Bounce `self` off of `disk`, iff the two intersect.

        Calculates intensity that `self` moved towards `disk`
        at moment of collision. Returns calculated impact-damage.

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

        # When rewriting this: The pygame.math module already has
        # methods for normal-vector calculation.

        # 0 <= bounciness <= 1.
        # At bounciness == 1.0, collisions cause no damage.
        bounciness = 0.97

        # Calculate normal vector
        delta = self.pos - disk.pos
        delta_magnitude = delta.magnitude()
        normal_vector = delta / delta_magnitude
        self_vel_along_normal = self.vel.dot(normal_vector)

        impulse_scalar = -(1 + bounciness) * self_vel_along_normal
        impulse_scalar /= 1 / self.mass + 1 / disk.mass
        self.add_impulse(normal_vector * impulse_scalar)

        # This allows the ship to land on the planet.
        # If impulse is small there is no damage
        damage = (max(0, impulse_scalar - 1300000)) * (1 - bounciness) * 6e-4

        # Move self outside other
        overlap = self.radius + disk.radius - delta_magnitude
        self.pos += normal_vector * overlap

        return damage
