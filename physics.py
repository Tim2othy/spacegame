import pygame
import pygame.camera
from pygame.math import Vector2
from pygame import draw
from camera import Camera


class PhysicalObject:
    """A physical object with dynamic position, dynamic speed, and constant nonzero mass."""

    def __init__(self, pos: Vector2, speed: Vector2, mass: float):
        self.pos = pos
        self.mass = mass
        self.speed = speed

    def update(self, dt: float):
        self.pos += dt * self.speed

    def add_impulse(self, impulse: Vector2):
        self.speed += impulse / self.mass

    def draw(self, camera: Camera):
        pass


class Disk(PhysicalObject):
    """A disk-shaped PhysicalObject, with constant radius and dynamic color."""

    def __init__(
        self,
        pos: Vector2,
        speed: Vector2,
        mass: float,
        radius: float,
        color: pygame.Color,
    ):
        super().__init__(pos, speed, mass)
        self.radius = radius
        self.color = color

    def draw(self, camera: Camera):
        center = camera.world_to_camera(self.pos)
        radius = self.radius * camera.zoom
        draw.circle(camera.surface, self.color, center, radius)