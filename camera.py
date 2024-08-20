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

    def smoothly_transition_to(
        self, new_pos: Vector2, new_zoom: float, dt: float, transition_time: float
    ):
        """Smoothly transition the camera view to a new pos and zoom.

        transition_speed (float): After this amount of time has passed, the camera will have fully
        transitioned to the new location.
        """

        dist = self.pos.distance_to(new_pos)
        self.pos.move_towards_ip(new_pos, dist * dt / transition_time)

        # This makes it easier to write, please don't judge me
        zoomy = Vector2(self.zoom, 0)
        new_zoomy = Vector2(new_zoom, 0)
        dist = abs(self.zoom - new_zoom)
        self.zoom = zoomy.move_towards(new_zoomy, dist * dt / transition_time).x

    def world_to_camera(self, vec: Vector2) -> Vector2:
        """Transforms a worldspace-vector to its position on the camera's screen."""
        width, height = self.surface.get_size()
        center = Vector2(width / 2, height / 2)
        return (vec - self.pos) * self.zoom + center

    def start_drawing_new_frame(self):
        self.surface.fill(pygame.Color("black"))
