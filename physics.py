import pygame
import pygame.camera
from pygame.math import Vector2
from camera import Camera
import math

GRAVITATIONAL_CONSTANT = 0.5


class PhysicalObject:
    """A physical object with dynamic position, dynamic velocity, and constant nonzero mass."""

    def __init__(self, pos: Vector2, vel: Vector2, mass: float):
        self.pos = pos
        self.mass = mass
        self.vel = vel

    def step(self, dt: float):
        self.pos += dt * self.vel

    def add_impulse(self, impulse: Vector2):
        self.vel += impulse / self.mass

    def apply_force(self, force: Vector2, dt: float):
        self.add_impulse(force * dt)

    def gravitational_force(self, pobj: "PhysicalObject") -> Vector2:
        """Returns the gravitational force between `self` and `pobj` that affects `self`."""

        delta = pobj.pos - self.pos  # point from `self` to `pobj`
        dist_squared = delta.magnitude_squared()
        force_magnitude = GRAVITATIONAL_CONSTANT * self.mass * pobj.mass / dist_squared
        normalised_delta = delta / math.sqrt(dist_squared)
        force = normalised_delta * force_magnitude

        return force

    def draw(self, camera: Camera):
        pass


class Disk(PhysicalObject):
    """A disk-shaped PhysicalObject, with constant radius and dynamic color."""

    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        density: float,
        radius: float,
        color: pygame.Color,
    ):
        mass = radius**3 * math.pi * 4 / 3
        super().__init__(pos, vel, mass)
        self.radius = radius
        self.color = color
        self._radius_squared = radius**2

    def draw(self, camera: Camera):
        camera.draw_circle(self.color, self.pos, self.radius)

    def intersects_point(self, vec: Vector2) -> bool:
        return self.pos.distance_squared_to(vec) < self._radius_squared

    def intersects_disk(self, disk: "Disk") -> bool:
        return self.pos.distance_squared_to(disk.pos) < (self.radius + disk.radius) ** 2

    def bounce_off_of_disk(self, disk: "Disk") -> float | None:
        """
        Bounce `self` off of `disk`, iff the two intersect.
        Returns speed of object at impact, None otherwise.
        """

        if not self.intersects_disk(disk):
            return None

        # When rewriting this: The pygame.math module already has methods for normal-vector
        # calculation.
        # Also use the add_force or add_impulse methods from Physics, do
        # not modify velocity directly

        # Calculate normal vector
        delta = self.pos - disk.pos
        delta_magnitude = delta.magnitude()
        normal_vector = delta / delta_magnitude
        self_vel_along_normal = self.vel.dot(normal_vector)

        # Do not resolve if velocities are separating
        if self_vel_along_normal > 0:
            return None

        # Calculate restitution (bounciness)
        restitution = 0.9

        """
        I think this is working generally correctly:
        - if restitution is 1 then the ship has the same vel after the bounce as before,
        - if it's 0.5 it loses half it's vel, 
        - if it's 2 then vel is doubled by the inpact, etc.
        """

        # Calculate impulse scalar
        impulse_scalar = -(1 + restitution) * self_vel_along_normal
        impulse_scalar = impulse_scalar / (1 / self.mass + 1 / disk.mass)

        self.vel += normal_vector * impulse_scalar / self.mass

        # Move self outside other
        overlap = self.radius + disk.radius - delta_magnitude
        self.pos += normal_vector * overlap
        return self_vel_along_normal