import pygame
from pygame.math import Vector2
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, G
from ship import Ship

class Planet:
    def __init__(self, x: float, y: float, radius: float, color: pygame.Color):
        self.pos = Vector2(x, y)
        self.radius = radius
        self.color = color

    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        if (
            self.pos[0] - self.radius - camera_pos.x < SCREEN_WIDTH
            and self.pos[0] + self.radius - camera_pos.x > 0
            and self.pos[1] - self.radius - camera_pos.y < SCREEN_HEIGHT
            and self.pos[1] + self.radius - camera_pos.y > 0
        ):
            pygame.draw.circle(
                screen,
                self.color,
                self.pos - camera_pos,
                self.radius,
            )

    def check_collision(self, ship: Ship) -> bool:
        # TODO: Checks like these can almost always be made faster by squaring both sides:
        # Instead of checking:
        #     dist(v,w) < r,
        # it's usually faster to check:
        #     dist_squared(v,w) < r**2,
        # which is equivalent if r is non-negative. This is more performant, because
        # we avoid a costly sqrt-calculation.
        return ship.pos.distance_to(self.pos) < self.radius + ship.radius

    def calculate_gravity(self, ship: Ship) -> Vector2:
        delta = self.pos - ship.pos
        distance_squared = delta.magnitude_squared()
        # TODO: Here (and everywhere else where we divide by a magnitude) we must
        # check for -- and eliminate -- the case where distance_squared==0.
        force_magnitude = (
            G * (4 / 3 * 3.13 * self.radius**3) * ship.mass / distance_squared
        )

        # Normalize the direction
        distance = math.sqrt(distance_squared)
        force = delta * force_magnitude / distance

        return force
