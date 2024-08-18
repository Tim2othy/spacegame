import pygame
from pygame.math import Vector2
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    GRID_SIZE,
    GRID_COLOR,
)


def draw_grid(screen: pygame.Surface, camera_pos: Vector2):
    # Vertical lines
    for x in range(0, WORLD_WIDTH, GRID_SIZE):
        pygame.draw.line(
            screen, GRID_COLOR, (x - camera_pos.x, 0), (x - camera_pos.x, SCREEN_HEIGHT)
        )

    # Horizontal lines
    for y in range(0, WORLD_HEIGHT, GRID_SIZE):
        pygame.draw.line(
            screen, GRID_COLOR, (0, y - camera_pos.y), (SCREEN_WIDTH, y - camera_pos.y)
        )
