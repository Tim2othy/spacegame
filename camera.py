import pygame
import pygame.gfxdraw
from pygame.math import Vector2
from pygame import Color


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

    # TODO: Stop the camera at the universe-border?
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
        (enclosing_tl, enclosing_tr) = self._get_enclosing_rect(points)

        buff_offset = Vector2(buff, buff)
        buffed_tl = enclosing_tl - buff_offset
        buffed_br = enclosing_tr + buff_offset
        buffed_size = buffed_br - buffed_tl
        buffed_width = buffed_size.x
        buffed_height = buffed_size.y
        ratio = buffed_width / buffed_height

        surface_width = self.surface.get_width()
        surface_height = self.surface.get_height()
        desired_ratio = surface_width / surface_height

        if ratio > desired_ratio:
            # Increase height
            target_height = buffed_width / desired_ratio
            addy = Vector2(0, (target_height - buffed_height) / 2)
            buffed_tl -= addy
            buffed_br += addy
        else:
            # Increase width
            target_width = buffed_height * desired_ratio
            addy = Vector2((target_width - buffed_width) / 2, 0)
            buffed_tl -= addy
            buffed_br += addy

        new_center = (buffed_tl + buffed_br) / 2
        new_zoom = surface_width / (buffed_br.x - buffed_tl.x)

        self.smoothly_transition_to(new_center, new_zoom, dt, transition_time)

    def _get_enclosing_rect(self, points: list[Vector2]) -> tuple[Vector2, Vector2]:
        """Gets the smallest rectangle enclosing all points
        Returns top-left and bottom-right coordinate of rect.
        """
        minx = miny = float("inf")
        maxx = maxy = float("-inf")
        for point in points:
            minx = min(minx, point.x)
            maxx = max(maxx, point.x)
            miny = min(miny, point.y)
            maxy = max(maxy, point.y)
        return (Vector2(minx, miny), Vector2(maxx, maxy))

    def _rectangle_intersects_screen(
        self, top_left: Vector2, bottom_right: Vector2
    ) -> bool:
        """Determines whether the rectangle intersects screen.
        Assumes that top_left.x <= bottom_right.x and top_left.y <= bottom_right.y.
        """
        (width, height) = self.surface.get_size()
        own_top_left = Vector2(0, 0)
        own_bottom_right = Vector2(width, height)
        return all(
            [
                own_top_left.x <= bottom_right.x,
                top_left.x <= own_bottom_right.x,
                own_top_left.y <= bottom_right.y,
                top_left.y <= own_bottom_right.y,
            ]
        )

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
        offset = Vector2(r, r)
        icenter = Vector2(x, y)
        tl, br = icenter - offset, icenter + offset
        if self._rectangle_intersects_screen(tl, br):
            pygame.gfxdraw.aacircle(self.surface, x, y, r, color)
            pygame.gfxdraw.filled_circle(self.surface, x, y, r, color)

    def draw_polygon(self, color: Color, points: list[Vector2]):
        # Soft check for points-screen-intersection:

        cpoints = [self.world_to_camera(p) for p in points]

        (enclosing_tl, enclosing_br) = self._get_enclosing_rect(cpoints)
        if self._rectangle_intersects_screen(enclosing_tl, enclosing_br):
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
        startx, starty = int(tstart.x), int(tstart.y)
        endx, endy = int(tend.x), int(tend.y)
        tl = Vector2(min(startx, endx), min(starty, endy))
        br = Vector2(max(startx, endx), max(starty, endy))

        if self._rectangle_intersects_screen(tl, br):
            pygame.gfxdraw.line(self.surface, startx, starty, endx, endy, color)

    def draw_rect(self, color: Color, top_left: Vector2, bottom_right: Vector2):
        ttop_left = self.world_to_camera(top_left)
        tbottom_right = self.world_to_camera(bottom_right)
        if self._rectangle_intersects_screen(ttop_left, tbottom_right):
            pygame.gfxdraw.box(
                self.surface, (ttop_left, tbottom_right - ttop_left), color
            )

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