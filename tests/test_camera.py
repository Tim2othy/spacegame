import pygame
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
