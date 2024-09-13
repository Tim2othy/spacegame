"""Class for rendering things to a surface, relative to a camera-position.

worldspace == Coordinates in space
screenspace == Coordinates on the screen
"""

from __future__ import annotations

import pygame
import pygame.gfxdraw
from pygame import Color, Rect
from pygame.math import Vector2 as Vec2


class Camera:
    """A camera with dynamic position and zoom, drawing to a fixed Surface."""

    def __init__(self, center: Vec2, zoom: float, surface: pygame.Surface) -> None:
        """Construct a new camera.

        Args:
        ----
            center (Vec2): Worldspace-coordinate at the center of the screen
            zoom (float): Higher = Fewer objects fit on screen,
                zoom==1 corresponds to 1 pixel per unit
            surface (pygame.Surface): Surface to draw on

        """
        self.zoom: float = zoom
        self.surface: pygame.Surface = surface
        # Convert `center` to topleft corner
        self.pos: Vec2 = Vec2(center) - Vec2(surface.get_size()) / (2 * zoom)

    def smoothly_transition_to(
        self,
        new_pos: Vec2,
        new_zoom: float,
        dt: float,
        transition_time: float = 0.25,
    ) -> None:
        """Smoothly transition the camera to a new location.

        Args:
        ----
            new_pos (Vec2): New camera worldspace topleft corner
            new_zoom (float): New zoom-factor
            dt (float): Time-factor (for the smooth operation)
            transition_time (float, optional): After this amount of dt has passed,
                the camera will have fully transitioned. Defaults to 0.25

        """
        dist = self.pos.distance_to(new_pos)
        self.pos.move_towards_ip(new_pos, dist * dt / transition_time)

        # This makes it easier to write, please don't judge me
        zoomy = Vec2(self.zoom, 0)
        new_zoomy = Vec2(new_zoom, 0)
        dist = abs(self.zoom - new_zoom)
        self.zoom = zoomy.move_towards(new_zoomy, dist * dt / transition_time).x

    def smoothly_focus_rect(
        self,
        rect: Rect,
        dt: float,
        transition_time: float = 0.25,
    ) -> None:
        """Smoothly move the camera so that a worldspace-rectangle is
        visible entirely, but not more.

        Args:
        ----
            rect (Rect): Worldspace-rectangle to fit to
            dt (float): Time-factor (for the smooth operation)
            transition_time (float, optional): After this amount of dt has passed,
                the camera will have fully transitioned. Defaults to 0.25

        """
        ratio = rect.width / rect.height
        surface_width = self.surface.get_width()
        surface_height = self.surface.get_height()
        desired_ratio = surface_width / surface_height

        if ratio > desired_ratio:
            # Width dominates, height is too small
            new_zoom = surface_width / rect.width
            new_height = rect.width / desired_ratio
            rect.inflate_ip(0, new_height - rect.height)
        else:
            # Height dominates, width is too small
            new_zoom = surface_height / rect.height
            new_width = rect.height * desired_ratio
            rect.inflate_ip(new_width - rect.width, 0)

        self.smoothly_transition_to(Vec2(rect.topleft), new_zoom, dt, transition_time)

    def smoothly_focus_points(
        self,
        points: list[Vec2],
        buff: float,
        dt: float,
        transition_time: float = 0.25,
    ) -> None:
        """Smoothly focus camera so that a list of worldspace-points is
        visible, with an additional buffer.

        Args:
        ----
            points (list[Vec2]): Worldspace-points to focus on. Hopefully nonempty.
            buff (float): Worldspace-buffer around the points
            dt (float): Time-factor (for the smooth operation)
            transition_time (float, optional): After this amount of dt has passed,
                the camera will have fully transitioned. Defaults to 0.25

        """
        enclosing_rect = _get_enclosing_rect(points)
        buffed_rect = enclosing_rect.inflate(2 * buff, 2 * buff)
        self.smoothly_focus_rect(buffed_rect, dt, transition_time)

    def _rectangle_intersects_screen(self, rect: Rect) -> bool:
        """Determine whether a screenspace-rectangle intersects the camera's screen.

        Args:
        ----
            rect (Rect): Screenspace-rectangle

        Returns:
        -------
            bool: True iff screenspace-rectangle intersects the screen

        """
        own_rect = Rect((0, 0), self.surface.get_size())
        # Inflate rect, to take care of edge-cases like zero width or height
        return own_rect.colliderect(rect.inflate(1, 1))

    def world_to_screen(self, vec: Vec2) -> Vec2:
        """Transform a worldspace-vector to screenspace.

        Args:
        ----
            vec (Vec2): Worldspace-vector

        Returns:
        -------
            Vec2: Screenspace-vector

        """
        return (vec - self.pos) * self.zoom

    def start_drawing_new_frame(self) -> None:
        """Fill the camera's surface blue to prepare for drawing a new frame."""
        self.surface.fill(Color("blue"))

    def draw_circle(self, color: Color, center: Vec2, radius: float) -> None:
        """Draw an anti-aliased worldspace-circle on screen.

        Args:
        ----
            color (Color): Border- and fill-color
            center (Vec2): Worldspace-center of the circle
            radius (float): Worldspace-radius of the circle

        """
        ccenter, cradius = self.world_to_screen(center), radius * self.zoom
        # ??? Why only ints?
        x, y, r = int(ccenter.x), int(ccenter.y), int(cradius)

        # soft check for circle-screen-intersection:
        enclosing_rect = Rect((x - r, y - r), (2 * r, 2 * r))
        if self._rectangle_intersects_screen(enclosing_rect):
            pygame.gfxdraw.aacircle(self.surface, x, y, r, color)
            pygame.gfxdraw.filled_circle(self.surface, x, y, r, color)

    def draw_polygon(self, color: Color, points: list[Vec2]) -> None:
        """Draw an anti-aliased worldspace-polygon on screen.

        Args:
        ----
            color (Color): Border- and fill-color
            points (list[Vec2]): Worldspace-points

        """
        cpoints = [self.world_to_screen(p) for p in points]
        # Soft check for points-screen-intersection:
        enclosing_rect = _get_enclosing_rect(cpoints)
        if self._rectangle_intersects_screen(enclosing_rect):
            pygame.gfxdraw.aapolygon(self.surface, cpoints, color)
            pygame.gfxdraw.filled_polygon(self.surface, cpoints, color)

    def draw_line(self, color: Color, start: Vec2, end: Vec2, thickness: float) -> None:
        """Draw an anti-aliased worldspace-line with a given thickness.

        Args:
        ----
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
        # Need not check whether this is on-screen, as
        # draw_polygon does it for us
        self.draw_polygon(color, points)

    def draw_hairline(self, color: Color, start: Vec2, end: Vec2) -> None:
        """Draw an anti-aliased worldspace-line of single-pixel-thickness.

        Args:
        ----
            color (Color): Line's color
            start (Vec2): Line's start-worldspace-point
            end (Vec2): Line's end-worldspace-point

        """
        tstart, tend = self.world_to_screen(start), self.world_to_screen(end)
        screen_rect = Rect((0, 0), self.surface.get_size())
        clipped_line = screen_rect.clipline(tstart, tend)
        if clipped_line:
            ((x1, y1), (x2, y2)) = clipped_line
            pygame.gfxdraw.line(self.surface, x1, y1, x2, y2, color)

    def draw_vertical_hairline(
        self,
        color: Color,
        x: float,
        starty: float,
        endy: float,
    ) -> None:
        """Draw a vertical worldspace-line of single-pixel-thickness.

        Args:
        ----
            color (Color): Line's Color
            x (float): Line's horizontal position
            starty (float): Line's starting point
            endy (float): Line's ending point

        """
        tstart, tend = (
            self.world_to_screen(Vec2(x, starty)),
            self.world_to_screen(Vec2(x, endy)),
        )
        screen_rect = Rect((0, 0), self.surface.get_size())
        clipped_line = screen_rect.clipline(tstart, tend)
        if clipped_line:
            ((x, y1), (_, y2)) = clipped_line
            pygame.gfxdraw.vline(self.surface, x, y1, y2, color)

    def draw_horizontal_hairline(
        self,
        color: Color,
        startx: float,
        endx: float,
        y: float,
    ) -> None:
        """Draw a horizontal worldspace-line of single-pixel-thickness.

        Args:
        ----
            color (Color): Line's Color
            startx (float): Line's starting point
            endx (float): Line's ending point
            y (float): Line's vertical position

        """
        tstart, tend = (
            self.world_to_screen(Vec2(startx, y)),
            self.world_to_screen(Vec2(endx, y)),
        )
        screen_rect = Rect((0, 0), self.surface.get_size())
        clipped_line = screen_rect.clipline(tstart, tend)
        if clipped_line:
            ((x1, y), (x2, _)) = clipped_line
            pygame.gfxdraw.hline(self.surface, x1, x2, y, color)

    def draw_rect(self, color: Color, rect: Rect) -> None:
        """Draw an anti-aliased worldspace-rectangle.

        Args:
        ----
            color (Color): Border- and fill-color
            rect (Rect): Worldspace rectangle to draw

        """
        ttopleft = self.world_to_screen(Vec2(rect.topleft))
        tbottomright = self.world_to_screen(Vec2(rect.bottomright))
        screen_rect = Rect(ttopleft, tbottomright - ttopleft)
        if self._rectangle_intersects_screen(screen_rect):
            pygame.gfxdraw.box(self.surface, screen_rect, color)

    def draw_text(
        self,
        text: str,
        pos: Vec2 | None,
        font: pygame.font.Font,
        color: Color,
    ) -> None:
        """Draw text on screen at screenspace-position, or centered on screen.

        Args:
        ----
            text (str): Text to render
            pos (Vec2 | None): If Vec2, screenspace-position of text's top-left-corner,
                if None, text will be centered on screen
            font (pygame.font.Font): Font to be used
            color (Color): Text's fill color

        """
        rendered = font.render(text, True, color)
        if pos is None:
            width, height = self.surface.get_size()
            pos = Vec2(
                (width - rendered.get_width()) / 2,
                (height - rendered.get_height()) / 2,
            )
        self.surface.blit(rendered, pos)


def _get_enclosing_rect(points: list[Vec2]) -> Rect:
    """Get the smallest rectangle enclosing all points.

    Args:
    ----
        points (list[Vec2]): Points to enclose

    Returns:
    -------
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
