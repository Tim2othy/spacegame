from collections.abc import Sequence
import pygame
import pygame.camera
from pygame.math import Vector2
from camera import Camera
import math

GRAVITATIONAL_CONSTANT = 0.0006

class PhysicalObject:
    """A physical object with dynamic position, dynamic speed, and constant nonzero mass."""

    def __init__(self, pos: Vector2, vel: Vector2, mass: float):
        self.pos = pos
        self.mass = mass
        self.vel = vel
        # TODO: Attribute `vel` was renamed from `speed`. GREP for any remnants of `speed`.

    def step(self, dt: float):
        self.pos += dt * self.vel

    def add_impulse(self, impulse: Vector2):
        self.vel += impulse / self.mass

    def apply_force(self, force: Vector2, dt: float):
        self.add_impulse(force * dt)

    def gravitational_force(self, pobj: "PhysicalObject") -> Vector2:
        """Returns the gravitational force between `self` and `pobj` that affects `self`."""

        # TODO: Here (and everywhere else where we divide by a magnitude) we must
        # check for -- and eliminate -- the case where distance_squared==0.
        delta = pobj.pos - self.pos  # point from `self` to `pobj`
        dist_squared = delta.magnitude_squared()
        force_magnitude = GRAVITATIONAL_CONSTANT * self.mass * pobj.mass / dist_squared
        normalised_delta = delta / math.sqrt(dist_squared)
        force = normalised_delta * force_magnitude

        return force

    def apply_gravitational_forces(
        self, gravity_objects: "Sequence[PhysicalObject]", dt: float
    ):
        force_sum = Vector2(0, 0)
        for pobj in gravity_objects:
            force_sum += self.gravitational_force(pobj)
        self.apply_force(force_sum, dt)

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
        mass = self.radius**3 * math.pi * 4 / 3
        super().__init__(pos, vel, mass)
        self.radius = radius
        self.color = color
        self._radius_squared = radius**2

    def draw(self, camera: Camera):
        center = camera.world_to_camera(self.pos)
        radius = self.radius * camera.zoom
        pygame.draw.circle(camera.surface, self.color, center, radius)

    def intersects_point(self, vec: Vector2) -> bool:
        return vec.magnitude_squared() < self._radius_squared

    def intersects_disk(self, disk: "Disk") -> bool:
        return disk.pos.magnitude_squared() < (self.radius + disk.radius) ** 2

    def bounce_off_of_disk(self, disk: "Disk"):
        """Bounce `self` off of `disk`, if the two intersect."""

        # TODO: The impulse of `disk` should also affect the way
        # that self is reflected.
        # TODO: The pygame.math module already has methods for normal-vector
        # calculation

        if self.intersects_disk(disk):
            # Calculate normal vector
            delta = self.pos - disk.pos
            delta_magnitude = delta.magnitude()
            normal_vector = delta / delta_magnitude
            self_vel_along_normal = self.vel.dot(normal_vector)

            # Do not resolve if velocities are separating
            if self_vel_along_normal > 0:
                return

            # Calculate restitution (bounciness)
            restitution = 1

            # Calculate impulse scalar
            j = -(1 + restitution) * self_vel_along_normal
            j /= 1 / self.mass + 1 / disk.mass

            # Apply impulse
            self.vel += normal_vector * j / self.mass

            # Move self outside other
            overlap = self.radius + disk.radius - delta_magnitude
            self.pos += normal_vector * overlap


class Planet(Disk):
    """A stationary disk."""

    def __init__(
        self,
        pos: Vector2,
        density: float,
        radius: float,
        color: pygame.Color,
    ):
        super().__init__(pos, Vector2(0, 0), density, radius, color)


class Asteroid(Disk):
    """A gray disk that doesn't exert gravitational force."""

    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        density: float,
        radius: float,
    ):
        super().__init__(pos, vel, density, radius, pygame.Color("gray"))

    # TODO: Re-implement that the Asteroids stopped at the world-border.
    # Or should they wrap instead? Should *all* PhysicalObjects wrap?


# TODO: Probably move to some other module.
# Should the celestial bodies be moved somewhere else, too?
class Bullet(PhysicalObject):
    """A triangular bullet."""

    def __init__(self, pos: Vector2, vel: Vector2, color: pygame.Color):
        super().__init__(pos, vel, 1.0)
        self.color = color

    def draw(self, camera: Camera):
        points = [
            camera.world_to_camera(point)
            for point in [
                self.pos + 0.2 * self.vel,
                self.pos + 0.1 * self.vel.rotate(150),
                self.pos + 0.1 * self.vel.rotate(-150),
            ]
        ]
        pygame.draw.polygon(camera.surface, self.color, points)