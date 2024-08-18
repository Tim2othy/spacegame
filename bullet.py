import pygame
from pygame.math import Vector2
import math
from enemy_info import BULLET_SPEED

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ship import Ship

class Bullet:
    def __init__(self, x: float, y: float, angle: float, ship: Ship):
        self.pos = Vector2(x, y)
        bullet_speed = BULLET_SPEED + math.sqrt(ship.speed[0] ** 2 + ship.speed[1] ** 2)
        self.speed = Vector2(
            bullet_speed * math.cos(angle) + ship.speed[0] + ship.speed[0],
            bullet_speed * math.sin(angle) + ship.speed[1] + ship.speed[1],
        )

    def update(self):
        # TODO: This must depend on ∆t
        self.pos += self.speed

    def draw(self, screen: pygame.Surface, camera_pos: Vector2):
        pygame.draw.circle(
            screen,
            (255, 255, 0),
            self.pos - camera_pos,
            3,
        )
