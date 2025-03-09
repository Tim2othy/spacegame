import pygame
from pygame.math import Vector2 as Vec2

from camera import Camera
from physics import PosVel

EPSILON = 1e-8

ORIGIN = PosVel._new_origin_and_only_use_this_if_you_really_know_what_you_are_doing()


def test_smoothly_focus_rectangle() -> None:
    camera = Camera(Vec2(1, 1), 1, pygame.Surface((1, 1)))

    rect_topleft = Vec2(-70, -60)
    # Only testing squares here
    size = 123
    camera.smoothly_focus_rect(pygame.Rect(rect_topleft.x, rect_topleft.y, size, size), 1, 1)

    assert camera.pos == rect_topleft
    assert abs(1 - camera.zoom * size) < EPSILON


def test_smoothly_focus_points() -> None:
    width, height = 10, 10
    buff = 2
    camera = Camera(Vec2(width, height) / 2, 1, pygame.Surface((width, height)))

    camera.smoothly_focus_points(
        [
            Vec2(5, 5),
            Vec2(8, 8),
            Vec2(2, 8),
            Vec2(8, 2),
            Vec2(2, 2),
        ],
        buff,
        1,
        1,
    )

    assert camera.pos == Vec2(0, 0)
    assert camera.zoom == 1
