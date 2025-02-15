import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from camera import Camera

EPSILON = 1e-8


def test_smoothly_transition_to():
    camera = Camera(Vec2(1, 1), 1, pygame.Surface((2, 2)))

    # Top-left corner of camera is at origin
    assert camera.pos == Vec2(0, 0)

    target_zoom = 2
    target_pos = Vec2(-3, -4)
    dt = 0.15
    transition_time = 0.25

    previous_distance = camera.pos.distance_to(target_pos)
    previous_zoom_difference = abs(camera.zoom - target_zoom)
    for _ in range(25):
        camera.smoothly_transition_to(target_pos, target_zoom, dt, transition_time)
        distance = camera.pos.distance_to(target_pos)
        zoom_difference = abs(camera.zoom - target_zoom)

        # Test we're moving closer to our goal
        assert distance < previous_distance
        assert zoom_difference < previous_zoom_difference
        previous_distance = distance
        previous_zoom_difference = zoom_difference

    # Test we're really close to our target
    assert camera.pos.distance_to(target_pos) < EPSILON
    assert abs(camera.zoom - target_zoom) < EPSILON


def test_smoothly_focus_rectangle():
    camera = Camera(Vec2(1, 1), 1, pygame.Surface((1, 1)))

    rect_topleft = Vec2(-70, -60)
    # Only testing squares here
    size = 123
    camera.smoothly_focus_rect(pygame.Rect(rect_topleft.x, rect_topleft.y, size, size), 1, 1)

    assert camera.pos == rect_topleft
    assert abs(1 - camera.zoom * size) < EPSILON


def test_smoothly_focus_points():
    width, height = 10, 10
    buff = 2
    points_and_colors = [
        (Vec2(5, 5), Color(1, 1, 1)),
        (Vec2(8, 8), Color(2, 2, 2)),
        (Vec2(2, 8), Color(3, 3, 3)),
        (Vec2(8, 2), Color(4, 4, 4)),
        (Vec2(2, 2), Color(5, 5, 5)),
    ]
    camera = Camera(Vec2(width, height) / 2, 1, pygame.Surface((width, height)))

    camera.smoothly_focus_points([p for p, _ in points_and_colors], buff, 1, 1)

    assert camera.pos == Vec2(0, 0)
    assert camera.zoom == 1
