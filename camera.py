import pygame
import pygame.gfxdraw
from pygame.math import Vector2
from pygame import Color, Rect


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
        self,
        new_pos: Vector2,
        new_zoom: float,
        dt: float,
        transition_time: float = 0.25,
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

    def smoothly_focus_rect(self, rect: Rect, dt: float, transition_time: float = 0.25):
        ratio = rect.width / rect.height
        surface_width = self.surface.get_width()
        surface_height = self.surface.get_height()
        desired_ratio = surface_width / surface_height

        if ratio > desired_ratio:
            # Width dominates
            zoom = surface_width / rect.width
        else:
            # Height dominates
            zoom = surface_height / rect.height

        self.smoothly_transition_to(Vector2(rect.center), zoom, dt, transition_time)

    def smoothly_focus_points(
        self,
        points: list[Vector2],
        buff: float,
        dt: float,
        transition_time: float = 0.25,
    ):
        """Focus camera smoothly on a list of points.

        Args:
            points (list[Vector2]): The points to focus on
            buff (float): The padding around the points
        """
        enclosing_rect = self._get_enclosing_rect(points)
        buffed_rect = enclosing_rect.inflate(2 * buff, 2 * buff)
        self.smoothly_focus_rect(buffed_rect, dt, transition_time)

    def _get_enclosing_rect(self, points: list[Vector2]) -> Rect:
        """Gets the smallest rectangle enclosing all points.
        Returns top-left and bottom-right coordinate of rect.
        """
        minx = miny = float("inf")
        maxx = maxy = float("-inf")
        for point in points:
            minx = min(minx, point.x)
            maxx = max(maxx, point.x)
            miny = min(miny, point.y)
            maxy = max(maxy, point.y)
        return Rect((minx, miny), (maxx - minx, maxy - miny))

    def _rectangle_intersects_screen(self, rect: Rect) -> bool:
        """Determines whether a screenspace-rectangle intersects the screen."""
        own_rect = Rect((0, 0), self.surface.get_size())
        # Inflate rect, to take care of edge-cases like zero width or height
        return own_rect.colliderect(rect.inflate(1, 1))

    def world_to_camera(self, vec: Vector2) -> Vector2:
        """Transforms a worldspace-vector to its position on the camera's screen."""
        width, height = self.surface.get_size()
        center = Vector2(width / 2, height / 2)
        return (vec - self.pos) * self.zoom + center

    def start_drawing_new_frame(self):
        self.surface.fill(Color("black"))

    def draw_circle(self, color: Color, center: Vector2, radius: float):
        ccenter, cradius = self.world_to_camera(center), radius * self.zoom
        # ??? Why only ints?
        x, y, r = int(ccenter.x), int(ccenter.y), int(cradius)

        # soft check for circle-screen-intersection:
        enclosing_rect = Rect((x - r, y - r), (2 * r, 2 * r))
        if self._rectangle_intersects_screen(enclosing_rect):
            pygame.gfxdraw.aacircle(self.surface, x, y, r, color)
            pygame.gfxdraw.filled_circle(self.surface, x, y, r, color)

    def draw_polygon(self, color: Color, points: list[Vector2]):
        # Soft check for points-screen-intersection:

        cpoints = [self.world_to_camera(p) for p in points]

        enclosing_rect = self._get_enclosing_rect(cpoints)
        if self._rectangle_intersects_screen(enclosing_rect):
            pygame.gfxdraw.aapolygon(self.surface, cpoints, color)
            pygame.gfxdraw.filled_polygon(self.surface, cpoints, color)

    def draw_line(self, color: Color, start: Vector2, end: Vector2, width: float):
        delta = end - start
        if delta == Vector2(0, 0):
            return
        orthogonal = Vector2(-delta.y, delta.x).normalize() * width / 2
        points = [
            start + orthogonal,
            end + orthogonal,
            end - orthogonal,
            start - orthogonal,
        ]
        # Need not check whether this is on-screen, as
        # draw_polygon does it for us
        self.draw_polygon(color, points)

    def draw_hairline(self, color: Color, start: Vector2, end: Vector2):
        tstart, tend = self.world_to_camera(start), self.world_to_camera(end)
        screen_rect = Rect((0, 0), self.surface.get_size())
        clipped_line = screen_rect.clipline(tstart, tend)
        if clipped_line:
            ((x1, y1), (x2, y2)) = clipped_line
            pygame.gfxdraw.line(self.surface, x1, y1, x2, y2, color)

    def draw_rect(self, color: Color, rect: Rect):
        ttopleft = self.world_to_camera(Vector2(rect.topleft))
        tbottomright = self.world_to_camera(Vector2(rect.bottomright))
        screen_rect = Rect(ttopleft, tbottomright - ttopleft)
        if self._rectangle_intersects_screen(screen_rect):
            pygame.gfxdraw.box(self.surface, screen_rect, color)

    def draw_text(
        self, text: str, pos: Vector2 | None, font: pygame.font.Font, color: Color
    ):
        """Draw text on screen, at pos `pos`. If `pos` is `None`, centers text."""
        rendered = font.render(text, True, color)
        if pos is None:
            width, height = self.surface.get_size()
            pos = Vector2(
                (width - rendered.get_width()) / 2, (height - rendered.get_height()) / 2
            )
        self.surface.blit(rendered, pos)
