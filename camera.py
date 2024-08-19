import pygame
from pygame.math import Vector2


class Camera:
    """A camera with dynamic position and zoom, drawing to a fixed Surface."""

    def __init__(self, pos: Vector2, zoom: float, surface: pygame.Surface):
        """
        Args:
            pos (Vector2): Center of the camera-frame.
            zoom (float): Zoom-factor of the camera, higher meaning that fewer same-size objects fit on screen.
            surface (pygame.Surface): The surface to be drawn to.
        """
        self.pos = pos
        self.zoom = zoom
        self.surface = surface

    def world_to_camera(self, vec: Vector2) -> Vector2:
        """Transforms a worldspace-vector to its position on the camera's screen."""
        width, height = self.surface.get_size()
        center = Vector2(width / 2, height / 2)
        return (vec - self.pos) * self.zoom + center

    def start_drawing_new_frame(self):
        self.surface.fill(pygame.Color("black"))
