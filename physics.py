"""Physical objects, and the interactions between them."""

from __future__ import annotations

import math
import pygame
import pygame.camera
from pygame.math import Vector2 as Vec2
from camera import Camera

GRAVITATIONAL_CONSTANT = 0.003


class PhysicalObject:
    """A physical object with dynamic position, dynamic velocity, and constant nonzero mass."""

    def __init__(self, pos: Vec2, vel: Vec2, mass: float):
        """Create a new PhysicalObject.

        Args:
        ----
            pos (Vec2): Object's position, usually its center
            vel (Vec2): Object's velocity (ignore relativity please)
            mass (float): Object's mass

        """
        self.pos = pos
        self.mass = mass
        self.vel = vel

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

    def gravitational_force(self, pobj: "PhysicalObject") -> Vec2:
        """Calculate gravitational force between `pobj` and `self` that
        affects `self`.

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
        force = normalised_delta * force_magnitude

        return force

    def draw(self, camera: Camera) -> None:
        """Draws `self` on `camera`.
        Implemented by subclasses.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        pass


class Disk(PhysicalObject):
    """A disk-shaped PhysicalObject, with constant radius and dynamic color."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        density: float,
        radius: float,
        color: pygame.Color,
    ):
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
        self.color = color
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

    def intersects_disk(self, disk: "Disk") -> bool:
        """Determine whether `self` intersects another Disk.

        Args:
        ----
            disk (Disk): Other disk

        Returns:
        -------
            bool: True iff the two disks intersect

        """
        return self.pos.distance_squared_to(disk.pos) < (self.radius + disk.radius) ** 2

    def bounce_off_of_disk(self, disk: "Disk") -> float | None:
        """Bounce `self` off of `disk`, iff the two intersect.
            Calculates intensity with `self` is moving towards `disk`
            at moment of collision. Then strength of bounce and damage.

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

        # When rewriting this: The pygame.math module already has methods for normal-vector
        # calculation.
        # Also use the add_force or add_impulse methods from Physics, do
        # not modify velocity directly

        bounciness = 0.70
        """
        bounciness: float between 0 and 1. 
        At 1 collisions cause no damage.
        """
        """Calculate normal vector"""
        delta = self.pos - disk.pos
        delta_magnitude = delta.magnitude()
        normal_vector = delta / delta_magnitude
        self_vel_along_normal = self.vel.dot(normal_vector)

        impulse_scalar = -(1 + bounciness) * self_vel_along_normal
        impulse_scalar = impulse_scalar / (1 / self.mass + 1 / disk.mass)
        self.vel += normal_vector * impulse_scalar / self.mass

        """This allows the ship to land on the planet. If impulse is small there is no damage"""
        damage = (max(0, impulse_scalar - 1300000)) * (1 - bounciness) * 1e-4
        return damage
