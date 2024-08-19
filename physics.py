import pygame
import pygame.camera
from pygame.math import Vector2
from camera import Camera
import math

GRAVITATIONAL_CONSTANT = 0.0006


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
        center = camera.world_to_camera(self.pos)
        radius = self.radius * camera.zoom
        pygame.draw.circle(camera.surface, self.color, center, radius)

    def intersects_point(self, vec: Vector2) -> bool:
        return (vec - self.pos).magnitude_squared() < self._radius_squared

    def intersects_disk(self, disk: "Disk") -> bool:
        dist = (disk.pos - self.pos).magnitude_squared()
        return dist < (self.radius + disk.radius) ** 2

    def bounce_off_of_disk(self, disk: "Disk") -> float | None:
        """
        Bounce `self` off of `disk`, iff the two intersect.
        Returns severity of the impact if it occurred, None otherwise.
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

            # Do not resolve if velocities are separating
            # TODO: What does this mean? And is `False`
            # the correct return-value here?
            if self_vel_along_normal > 0:
                return None

            # Calculate restitution (bounciness)
            restitution = 1

            # TODO: In the original ship-crash-method,
            # bounciness (don't ask me what that corresponds to, here)
            # was multiplied by 0.5, for sake of energy-loss. This
            # should probably be implemented here, to, but I do not
            # understand this code.

            # Calculate impulse scalar
            j = -(1 + restitution) * self_vel_along_normal
            j /= 1 / self.mass + 1 / disk.mass

            # Apply impulse
            self.vel += normal_vector * j / self.mass

            # Move self outside other
            overlap = self.radius + disk.radius - delta_magnitude
            self.pos += normal_vector * overlap
            return j  # TODO: Is this correct???
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
        points = [
            camera.world_to_camera(point)
            for point in [
                self.pos + 5 * forward,
                self.pos + 2 * forward.rotate(150),
                self.pos + 2 * forward.rotate(-150),
            ]
        ]
        pygame.draw.polygon(camera.surface, self.color, points)


class Rocket(Bullet):
    def __init__(self, pos: Vector2, vel: Vector2, color: pygame.Color):
        super().__init__(pos, vel, color)

    # TODO: Reimplement the below code, once I understand what it does.
    # For now, Rockets are synonymous to Bullets.
    # If re-implementing this, also check all calls to the constructor so that
    # they do what you'd like them to do.
    """
        self.pos = Vector2(x, y)
        self.target_pos = target_pos
        self.speed = Vector2(0, 0)  # Initial speed is zero
        self.last_acceleration_time = time.time()
        self.accelerating = True
        self.color = (255, 0, 0)

    def update(self, ship: Ship):
        current_time = time.time()
        time_since_last_acceleration = current_time - self.last_acceleration_time

        if self.accelerating:
            self.color = (255, 0, 200)  # one color while accelerating
        else:
            self.color = (255, 100, 0)  # different color not accelerating

        # Check if it's time to start accelerating
        if not self.accelerating and time_since_last_acceleration >= 9:
            self.accelerating = True
            self.last_acceleration_time = current_time

        # Check if the acceleration period should end
        elif self.accelerating and time_since_last_acceleration >= 3:
            self.accelerating = False
            self.last_acceleration_time = current_time

        # Update the target position to the ship's current position
        self.target_pos = ship.pos
        dx = self.target_pos[0] - self.pos[0]
        dy = self.target_pos[1] - self.pos[1]
        dist = sqrt(dx**2 + dy**2)

        if dist != 0:  # Avoid division by zero
            # Update speed direction towards the player
            if self.accelerating:
                # Apply additional acceleration in the direction of the player
                self.speed[0] += (dx / dist) * ROCKET_ACCELERATION
                self.speed[1] += (dy / dist) * ROCKET_ACCELERATION

        # Update position based on speed
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        pygame.draw.circle(
            screen,
            self.color,
            self.pos - camera_pos,
            5,
        )
    """
