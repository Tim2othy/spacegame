"""Class for rendering things to a surface, relative to a camera-position.

worldspace == Coordinates in space
surfacespace == Coordinates on the screen
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame
from pygame import Color, Rect
from pygame.math import Vector2 as Vec2

from physics import Pos, PosVel
from profiler import global_profiler

if TYPE_CHECKING:
    from collections.abc import Iterable


MIN_ZOOM = 0.04
MAX_ZOOM = 0.9  # not really being used yet
DIST_ZOOM_FACTOR = 1.2  # adjusts how quickly to zoom as a function of distance at 1 zoom and dist exactly cancel out
REFERENCE_DIST = 1000  # adjusts minimal zoom as a function of distance, but in an odd way
MAX_CAMERA_SHIFT = 5


def cap_vector_length(vector: Vec2, max_length: float) -> Vec2:
    """Cap a vector to a maximum length while preserving direction."""
    if vector == Vec2(0, 0):
        return Vec2(0, 0)
    return vector * (min(max_length, vector.length()) / vector.length())


class Camera(Pos):
    """A camera with dynamic position and zoom, drawing to a fixed Surface."""

    def __init__(self, surface: pygame.Surface, tracking: PosVel, zoom: float) -> None:
        """Construct a new camera, tracking a fixed object.

        Raises a ValueError if `zoom` is not finite and strictly positive.
        Higher `zoom` = Fewer objects fit on screen,
        `zoom`==1 corresponds to 1 pixel per unit.

        TODO: The effective `zoom` should actually be independent of screen-size.
        """
        super().__init__(tracking, Vec2(0, 0))
        self._tracking: PosVel = tracking
        if not (math.isfinite(zoom) and zoom > 0):
            raise ValueError
        self._base_zoom: float = zoom
        self._zoom: float = zoom
        self.nearest_object: PosVel | None = None

        self._surface: pygame.Surface = surface
        surface_size: tuple[int, int] = surface.get_size()
        self._surface_size: Vec2 = Vec2(*surface_size)
        self._surface_rect: Rect = Rect((0, 0), surface_size)
        self._midpoint = Vec2(0, 0)

    def _update_zoom(self) -> None:
        """Calculate zoom based on distance to nearest object."""
        if self.nearest_object is None:
            new_zoom = 1
        else:
            dist = self._tracking.pos_relative_to(self.nearest_object).length()
            speed = self._tracking.vel_relative_to(self.nearest_object).length()
            average = 0.9 * dist + speed
            # Inverse relationship produces sensible zooming
            new_zoom = DIST_ZOOM_FACTOR * self._base_zoom * (REFERENCE_DIST / (average + 0.5 * REFERENCE_DIST))
            # Prevent tiny zoom values, giant zoom values are prevented by the "+ REFERENCE_DIST" above
            new_zoom = max(MIN_ZOOM, new_zoom)
            self._zoom *= 0.99
            self._zoom += 0.01 * new_zoom

    def _update_midpoint(self) -> None:
        """Update the midpoint that the camera is centered on."""
        if self.nearest_object is None:
            return
        # Get  midpoint between player and nearest object
        new_midpoint = self.nearest_object.pos_relative_to(self._tracking) / 2.0
        difference = new_midpoint - self._midpoint
        # cap size of shift, but make camera shift more the more zoomed out
        max_length_shift = MAX_CAMERA_SHIFT / (1 - MIN_ZOOM) * (MAX_ZOOM - self._zoom)
        midpoint_shift = cap_vector_length(difference, max_length_shift)
        self._midpoint += midpoint_shift

    def step(self) -> None:
        """Update the camera's position and zoom to track the object it's tracking."""
        self._update_zoom()
        self._update_midpoint()
        self._shift(self._tracking.pos_relative_to(self) + self._midpoint - self._surface_size / (2.0 * self._zoom))

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

    def draw_pixel(self, color: Color, transparency: float, pos: Pos) -> None:
        """Draw a worldspace-pixel at position `pos`."""
        surfacepoint = self._world_to_surface(pos)
        if self._surface_rect.collidepoint(surfacepoint):
            position = (int(surfacepoint.x), int(surfacepoint.y))
            old_color = self._surface.get_at(position)
            new_color = old_color.lerp(color, transparency)
            self._surface.set_at(position, new_color)

    def draw_circle(self, color: Color, center: Pos, radius: float, width: int = 0) -> None:
        """Draw a worldspace-circle. Optional `width` arg makes a ring."""
        surfacespace_center = self._world_to_surface(center)
        surfacespace_radius = radius * self._zoom
        surfacespace_radius_vec = Vec2(surfacespace_radius, surfacespace_radius)

        # soft check for circle-surface-intersection:
        enclosing_rect = Rect(surfacespace_center - surfacespace_radius_vec, 2 * surfacespace_radius_vec)
        if self._rectangle_intersects_surface(enclosing_rect):
            pygame.draw.circle(self._surface, color, surfacespace_center, surfacespace_radius, width=width)

    def draw_polygon(self, color: Color, points: Iterable[Pos]) -> None:
        """Draw a filled worldspace-polygon."""
        surfacespace_points = list(map(self._world_to_surface, points))
        # Soft check for point-surface-intersection:
        enclosing_rect = _get_enclosing_rect(surfacespace_points)
        if self._rectangle_intersects_surface(enclosing_rect):
            pygame.draw.polygon(self._surface, color, surfacespace_points)

    def draw_line(self, color: Color, start: Pos, end: Pos, thickness: float) -> None:
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
            clipped_start, clipped_end = clipped_line
            pygame.draw.line(self._surface, color, clipped_start, clipped_end, 1)

    def draw_arrow(self, color: Color, start: Pos, direction: Vec2, size: float) -> None:
        """Draw an arrow pointing in a specific direction."""
        direction = direction.normalize()

        # Calculate dimensions
        shaft_length = size * 0.6
        shaft_width = size * 0.15
        head_width = size * 0.5

        # Create directional vectors
        shaft_vec = direction * shaft_length
        head_vec = direction * size * 1.4
        perp_vec = Vec2(-direction.y, direction.x)

        back_r = Pos(start, perp_vec * shaft_width)
        inside_r = Pos(start, shaft_vec + perp_vec * shaft_width)
        far_r = Pos(start, shaft_vec + perp_vec * head_width)
        tip = Pos(start, head_vec)
        far_l = Pos(start, shaft_vec - perp_vec * head_width)
        inside_l = Pos(start, shaft_vec - perp_vec * shaft_width)
        back_l = Pos(start, -perp_vec * shaft_width)

        # Draw the arrow as a polygon with 7 points
        self.draw_polygon(
            color,
            [back_r, inside_r, far_r, tip, far_l, inside_l, back_l],
        )

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
