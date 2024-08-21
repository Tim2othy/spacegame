import pygame
import pygame.camera
from pygame.math import Vector2
from camera import Camera
import math

GRAVITATIONAL_CONSTANT = 0.0003


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
        Returns damage to ship.
        """

        if not self.intersects_disk(disk):
            return None

        # When rewriting this: The pygame.math module already has methods for normal-vector
        # calculation.
        # Also use the add_force or add_impulse methods from Physics, do
        # not modify velocity directly

        bounciness = 0.70  # Always between 0 and 1. At 1 collisions cause no damage. I don't think it's necissary to give every disk a bounciness attribute. The game is supposed to be realistic, in real life all objects have a bounciness of 1.0. No! Bad auto suggestion, that's not true, in real life a spaceship just dies if it flies into anything, so bounciness won't play that big of a role.

        # Calculate normal vector
        delta = self.pos - disk.pos
        delta_magnitude = delta.magnitude()
        normal_vector = delta / delta_magnitude
        self_vel_along_normal = self.vel.dot(normal_vector)

        # Check if the objects are moving away from each other
        if self_vel_along_normal > 0:
            return None

        impulse_scalar = -(1 + bounciness) * self_vel_along_normal
        impulse_scalar = impulse_scalar / (1 / self.mass + 1 / disk.mass)
        self.vel += normal_vector * impulse_scalar / self.mass

        # This allows the ship to land on the planet. If impulse is small there is no damage.
        damage = (max(0, impulse_scalar - 1300000)) * (1 - bounciness) * 1e-4
        return damage
