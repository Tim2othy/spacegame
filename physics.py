import pygame
import pygame.camera
from pygame.math import Vector2
from camera import Camera
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ship import Ship

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

        # TODO: Here (and everywhere else where we divide by a magnitude) we must
        # check for -- and eliminate -- the case where distance_squared==0.
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
        Returns severity of the impact if it occurred, None otherwise.
        is currently using restitution to calc damadge, shoud be changed,
        probably bu using vel along normal vector of ship
        """

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
            print(f"self_vel_along_normal: {self_vel_along_normal}")

            # Do not resolve if velocities are separating
            # TODO: What does this mean? And is `False`
            # the correct return-value here?
            if self_vel_along_normal > 0:
                return None

            # Calculate restitution (bounciness)
            restitution = 10000000

            # TODO: In the original ship-crash-method,
            # bounciness (don't ask me what that corresponds to, here)
            # was multiplied by 0.5, for sake of energy-loss. This
            # should probably be implemented here, to, but I do not
            # understand this code.

            """I think this is working the way it did before, if restitution is 1 then you have the
            same vel after the bounce as before, if it's 0.5 you lose half your vel, 
            if it's > 1 then you gain vel in proportion to restitution
            """

            # Calculate impulse scalar
            impulse_scalar_questionmark = (
                -(1 + restitution) * self_vel_along_normal
            )  # what used to be called j is the impulse_scalar right?

            print(f"impulse_scalar_questionmark: {impulse_scalar_questionmark}")

            impulse_scalar_questionmark = impulse_scalar_questionmark / (
                1 / self.mass + 1 / disk.mass
            )

            print(f"impulse_scalar_questionmark: {impulse_scalar_questionmark}")

            # Apply impulse
            self.vel += normal_vector * impulse_scalar_questionmark / self.mass

            # Move self outside other
            overlap = self.radius + disk.radius - delta_magnitude
            self.pos += normal_vector * overlap
            return (
                impulse_scalar_questionmark,
                self_vel_along_normal,
            )  # TODO: Is this correct???, i think so, it mostly makes sense
        else:
            return None


# TODO: Probably move to some other module.
# Should the celestial bodies be moved somewhere else, too?
class Bullet(PhysicalObject):
    """A triangular bullet."""

    def __init__(self, pos: Vector2, vel: Vector2, color: pygame.Color):
        super().__init__(pos, vel, 1.0)
        self.color = color

    def draw(self, camera: Camera):
        forward = self.vel.normalize() if self.vel != Vector2(0, 0) else Vector2(1, 0)
        camera.draw_polygon(
            self.color,
            [
                self.pos + 5 * forward,
                self.pos + 2 * forward.rotate(150),
                self.pos + 2 * forward.rotate(-150),
            ],
        )


class Rocket(Bullet):
    def __init__(
        self, pos: Vector2, vel: Vector2, color: pygame.Color, target_ship: "Ship"
    ):
        super().__init__(pos, vel, color)
        self.target_ship = target_ship
        self.vel /= 4
        self.homing_thrust = 1000 * self.mass
        self.homing_timer = 0
        self.homing_duration = 1
        self.nonhoming_duration = 3
        self._total_duration = self.homing_duration + self.nonhoming_duration

    def step(self, dt: float):
        self.homing_timer = (self.homing_timer + dt) % self._total_duration

        if self.homing_timer <= self.homing_duration:
            # Target the ship
            dir = self.target_ship.pos - self.pos
            if dir != Vector2(0, 0):
                dir.normalize_ip()
                self.apply_force(dir * self.homing_thrust, dt)

        super().step(dt)

    def draw(self, camera: Camera):
        forward = self.vel.normalize() if self.vel != Vector2(0, 0) else Vector2(1, 0)
        left = Vector2(-forward.y, forward.x)
        right = -left
        backward = -forward

        # Spooky homing body
        if self.homing_timer <= self.homing_duration:
            camera.draw_polygon(
                self.color.lerp(pygame.Color("blue"), 0.5),
                [
                    self.pos + 4 * (left + forward),
                    self.pos + 4 * (left + backward),
                    self.pos + 4 * (right + backward),
                    self.pos + 4 * (right + forward),
                ],
            )

        # Missile body
        camera.draw_polygon(
            self.color,
            [
                self.pos + 3 * (left + forward),
                self.pos + 3 * (left + backward),
                self.pos + 3 * (right + backward),
                self.pos + 3 * (right + forward),
                self.pos + 2 * (3 * forward),
            ],
        )
