from pygame.math import Vector2


class PhysicalObject:
    """A physical object with dynamic position, dynamic speed, and constant nonzero mass."""

    def __init__(self, pos: Vector2, speed: Vector2 = Vector2(0, 0), mass: float = 1):
        self.pos = pos
        self.mass = mass
        self.speed = speed

    def update(self, dt: float):
        self.pos += dt * self.speed