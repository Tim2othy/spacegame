"""Class for rendering things to a surface, relative to a camera-position.

worldspace == Coordinates in space
surfacespace == Coordinates on the screen
"""

from __future__ import annotations

import pygame
from pygame import Color, Rect
from pygame.math import Vector2 as Vec2

from physics import Pos, PosVel
from profiler import global_profiler


class Camera(Pos):
    """A camera with dynamic position and zoom, drawing to a fixed Surface."""

    def __init__(self, surface: pygame.Surface, tracking: PosVel, buff: float) -> None:
        """Construct a new camera, tracking a fixed object."""
        super().__init__(tracking, Vec2(0, 0))
        self._buff: float = buff
        self._tracking: PosVel = tracking
        self._zoom: float = 2.0

        self._surface: pygame.Surface = surface
        surface_size: tuple[int, int] = surface.get_size()
        self._surface_size: Vec2 = Vec2(*surface_size)
        self._surface_rect: Rect = Rect((0, 0), surface_size)

    def step(self) -> None:
        """Update the camera's position and zoom to track the object it's tracking."""
        self._shift(self._tracking.pos_relative_to(self))

    def _rectangle_intersects_surface(self, rect: Rect) -> bool:
        """Return whether a surfacespace-rectangle intersects the camera's surface."""
        # Inflate rect, to take care of edge-cases like zero width or height
        return self._surface_rect.colliderect(rect.inflate(1, 1))

    def _world_to_surface(self, pos: Pos) -> Vec2:
        """Transform a Pos to surfacespace."""
        return pos.pos_relative_to(self) * self.zoom

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

    def draw_polygon(self, color: Color, points: list[Pos]) -> None:
        """Draw a filled polygon."""
        cpoints = [self._world_to_surface(p) for p in points]
        # Soft check for point-surface-intersection:
        enclosing_rect = _get_enclosing_rect(cpoints)
        if self._rectangle_intersects_surface(enclosing_rect):
            pygame.draw.polygon(self._surface, color, cpoints)

    def draw_line(self, color: Color, start: Vec2, end: Vec2, thickness: float) -> None:
        """Draw a worldspace-line with a given thickness.

        Args:
            color (Color): Border- and fill-color
            start (Vec2): Line's start-worldspace-point
            end (Vec2): Line's end-worldspace-point
            thickness (float): Line's worldspace-thickness

        """
        delta = end - start
        if delta == Vec2(0, 0):
            return
        orthogonal = Vec2(-delta.y, delta.x).normalize() * thickness / 2
        points = [
            start + orthogonal,
            end + orthogonal,
            end - orthogonal,
            start - orthogonal,
        ]
        # Need not check whether this is on-surface, as
        # draw_polygon does it for us
        self.draw_polygon(color, points)

    def draw_hairline(self, color: Color, start: Vec2, end: Vec2) -> None:
        """Draw a worldspace-line of single-pixel-thickness.

        Args:
            color (Color): Line's color
            start (Vec2): Line's start-worldspace-point
            end (Vec2): Line's end-worldspace-point

        """
        tstart, tend = self._world_to_surface(start), self._world_to_surface(end)
        surface_rect = Rect((0, 0), self._surface.get_size())
        clipped_line = surface_rect.clipline(tstart, tend)
        if clipped_line:
            ((x1, y1), (x2, y2)) = clipped_line
            pygame.draw.line(self._surface, color, (x1, y1), (x2, y2))

    def draw_vertical_hairline(self, color: Color, x: float, starty: float, endy: float) -> None:
        """Draw a vertical worldspace-line of single-pixel-thickness.

        Args:
            color (Color): Line's Color
            x (float): Line's horizontal position
            starty (float): Line's starting point
            endy (float): Line's ending point

        """
        tstart, tend = (self._world_to_surface(Vec2(x, starty)), self._world_to_surface(Vec2(x, endy)))
        surface_rect = Rect((0, 0), self._surface.get_size())
        clipped_line = surface_rect.clipline(tstart, tend)
        if clipped_line:
            ((x, y1), (_, y2)) = clipped_line
            pygame.draw.line(self._surface, color, (x, y1), (x, y2))

    def draw_horizontal_hairline(self, color: Color, startx: float, endx: float, y: float) -> None:
        """Draw a horizontal worldspace-line of single-pixel-thickness.

        Args:
            color (Color): Line's Color
            startx (float): Line's starting point
            endx (float): Line's ending point
            y (float): Line's vertical position

        """
        tstart, tend = (self._world_to_surface(Vec2(startx, y)), self._world_to_surface(Vec2(endx, y)))
        surface_rect = Rect((0, 0), self._surface.get_size())
        clipped_line = surface_rect.clipline(tstart, tend)
        if clipped_line:
            ((x1, y), (x2, _)) = clipped_line
            pygame.draw.line(self._surface, color, (x1, y), (x2, y))

    def draw_text(self, text: str, pos: Vec2 | None, font: pygame.font.Font, color: Color) -> None:
        """Draw text at a surfacespace-position, or centered on the surface if not provided."""
        rendered = font.render(text, antialias=True, color=color)
        if pos is None:
            width, height = self._surface.get_size()
            pos = Vec2((width - rendered.get_width()) / 2, (height - rendered.get_height()) / 2)
        self._surface.blit(rendered, pos)


def _get_enclosing_rect(points: list[Vec2]) -> Rect:
    """Get the smallest rectangle enclosing all points.

    Args:
        points (list[Vec2]): Points to enclose

    Returns:
        Rect: Rectangle fitting all points snugly

    """
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    for point in points:
        minx = min(minx, point.x)
        maxx = max(maxx, point.x)
        miny = min(miny, point.y)
        maxy = max(maxy, point.y)
    return Rect((minx, miny), (maxx - minx, maxy - miny))
