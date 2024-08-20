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
        minx = miny = float("inf")
        maxx = maxy = float("-inf")
        for point in points:
            minx = min(minx, point.x)
            maxx = max(maxx, point.x)
            miny = min(miny, point.y)
            maxy = max(maxy, point.y)

        buffed_tl = Vector2(minx - buff, miny - buff)
        buffed_br = Vector2(maxx + buff, maxy + buff)
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

    def _rectangle_intersects_screen(
        self, top_left: Vector2, bottom_right: Vector2
    ) -> bool:
        """Determines whether the rectangle intersects screen.
        Assumes that top_left.x <= bottom_right.x and top_left.y <= bottom_right.y.
        """
        (width, height) = self.surface.get_size()
        offset = Vector2(width, height) / 2
        own_top_left = self.pos - offset
        own_bottom_right = self.pos + offset
        return (
            own_top_left.x <= bottom_right.x
            and own_bottom_right.x >= top_left.x
            and own_top_left.y >= bottom_right.y
            and own_bottom_right.y <= top_left.y
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
        # TODO: Don't draw if off-screen
        pygame.gfxdraw.aacircle(self.surface, x, y, r, color)
        pygame.gfxdraw.filled_circle(self.surface, x, y, r, color)

    def draw_polygon(self, color: Color, points: list[Vector2]):
        cpoints = [self.world_to_camera(p) for p in points]
        # TODO: Don't draw if off-screen
        pygame.gfxdraw.aapolygon(self.surface, cpoints, color)
        pygame.gfxdraw.filled_polygon(self.surface, cpoints, color)

    def draw_line(self, color: Color, start: Vector2, end: Vector2, width: float):
        # TODO: Don't draw if off-screen
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
        self.draw_polygon(color, points)