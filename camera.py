"""Class for rendering things to a surface, relative to a camera-position.

worldspace == Coordinates in space
surfacespace == Coordinates on the screen
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Color, Rect
from pygame.math import Vector2 as Vec2

from physics import Pos, PosVel
from profiler import global_profiler

if TYPE_CHECKING:
    from collections.abc import Iterable


class Camera(Pos):
    """A camera with dynamic position and zoom, drawing to a fixed Surface."""

    def __init__(self, surface: pygame.Surface, tracking: PosVel) -> None:
        """Construct a new camera, tracking a fixed object."""
        super().__init__(tracking, Vec2(0, 0))
        self._tracking: PosVel = tracking
        self._zoom: float = 2.0

        self._surface: pygame.Surface = surface
        surface_size: tuple[int, int] = surface.get_size()
        self._surface_size: Vec2 = Vec2(*surface_size)
        self._surface_rect: Rect = Rect((0, 0), surface_size)

    def step(self) -> None:
        """Update the camera's position and zoom to track the object it's tracking."""
        self._shift(self._tracking.pos_relative_to(self) - self._surface_size / self._zoom)

    def _rectangle_intersects_surface(self, rect: Rect) -> bool:
        """Return whether a surfacespace-rectangle intersects the camera's surface."""
        # Inflate rect, to take care of edge-cases like zero width or height
        return self._surface_rect.colliderect(rect.inflate(1, 1))

    def _world_to_surface(self, pos: Pos) -> Vec2:
        """Transform a Pos to surfacespace."""
        return pos.pos_relative_to(self) * self._zoom

    @global_profiler.profile_method
    def start_drawing_new_frame(self) -> None:
        """Fill the camera's surface black to prepare for drawing a new frame."""
        self._surface.fill(Color("black"))

    def draw_pixel(self, color: Color, pos: Pos) -> None:
        """Draw a worldspace-pixel at position `pos`."""
        surfacepoint = self._world_to_surface(pos)
        if self._surface_rect.collidepoint(surfacepoint):
            self._surface.set_at((int(surfacepoint.x), int(surfacepoint.y)), color)

    def draw_circle(self, color: Color, center: Pos, radius: float) -> None:
        """Draw a worldspace-circle.

        Args:
            color (Color): Border- and fill-color
            center (Pos): Worldspace-center of the circle
            radius (float): Worldspace-radius of the circle

        """
        surfacespace_center = self._world_to_surface(center)
        surfacespace_radius = radius * self._zoom
        surfacespace_radius_vec = Vec2(surfacespace_radius, surfacespace_radius)

        # soft check for circle-surface-intersection:
        enclosing_rect = Rect(surfacespace_center - surfacespace_radius_vec, 2 * surfacespace_radius_vec)
        if self._rectangle_intersects_surface(enclosing_rect):
            pygame.draw.circle(self._surface, color, surfacespace_center, surfacespace_radius)

    def draw_polygon(self, color: Color, points: Iterable[Pos]) -> None:
        """Draw a filled worldspace-polygon."""
        surfacespace_points = list(map(self._world_to_surface, points))
        # Soft check for point-surface-intersection:
        enclosing_rect = _get_enclosing_rect(surfacespace_points)
        if self._rectangle_intersects_surface(enclosing_rect):
            pygame.draw.polygon(self._surface, color, surfacespace_points)

    def draw_line(self, color: Color, start: Vec2, end: Vec2, thickness: float) -> None:
        """Draw a worldspace-line with a given thickness."""
        screenspace_start, screenspace_end = self._world_to_surface(start), self._world_to_surface(end)
        enclosing_rect = _get_enclosing_rect((screenspace_start, screenspace_end))
        surfacespace_thickness = thickness * self._zoom
        enclosing_rect.inflate_ip(surfacespace_thickness, surfacespace_thickness)
        if self._rectangle_intersects_surface(enclosing_rect):
            pygame.draw.line(self._surface, color, screenspace_start, screenspace_end, int(surfacespace_thickness))

    def draw_hairline(self, color: Color, start: Pos, end: Pos) -> None:
        """Draw a worldspace-line of single-pixel-thickness."""
        screenspace_start = self._world_to_surface(start)
        screenspace_end = self._world_to_surface(end)
        clipped_line = self._surface_rect.clipline(screenspace_start, screenspace_end)
        if clipped_line:
            start, end = clipped_line
            pygame.draw.line(self._surface, color, start, end, 1)

    def draw_text(self, text: str, pos: Vec2 | None, font: pygame.font.Font, color: Color) -> None:
        """Draw text at a surfacespace-position, or centered on the surface if not provided."""
        rendered = font.render(text, antialias=True, color=color)
        pos = pos or (self._surface_size - Vec2(*rendered.get_size())) / 2
        self._surface.blit(rendered, pos)


def _get_enclosing_rect(points: Iterable[Vec2]) -> Rect:
    """Get the smallest rectangle enclosing all points."""
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    for point in points:
        minx = min(minx, point.x)
        maxx = max(maxx, point.x)
        miny = min(miny, point.y)
        maxy = max(maxy, point.y)
    return Rect((minx, miny), (maxx - minx, maxy - miny))
