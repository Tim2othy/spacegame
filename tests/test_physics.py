import math
from math import isclose

import pytest
from pygame import Color, Surface
from pygame.math import Vector2 as Vec2

from camera import Camera
from physics import Disk, MovingObject, PhysicalObject


# Messed-up object-instantiation to bootstrap a reference MovingObject.
# Think thrice before copying this code.
ORIGIN = object.__new__(MovingObject)
ORIGIN._MovingObject__pos = Vec2(0, 0)  # noqa: SLF001
ORIGIN._MovingObject__vel = Vec2(0, 0)  # noqa: SLF001


@pytest.mark.parametrize("relative_pos", [Vec2(10, 5), Vec2(-10, 0), Vec2(10, -20), Vec2(0, 0)])
@pytest.mark.parametrize("relative_vel", [Vec2(10, 5), Vec2(-10, 0), Vec2(10, -20), Vec2(0, 0)])
def test_relativity(relative_pos: Vec2, relative_vel: Vec2) -> None:
    obj = MovingObject(ORIGIN, relative_pos, relative_vel)
    assert obj.pos_relative_to(ORIGIN) == relative_pos
    assert obj.vel_relative_to(ORIGIN) == relative_vel


@pytest.mark.parametrize("relative_pos", [Vec2(10, 5), Vec2(-10, 0), Vec2(10, -20), Vec2(0, 0)])
def test_step(relative_pos: Vec2) -> None:
    obj = MovingObject(ORIGIN, relative_pos, Vec2(1, -1))
    obj.step(0.25)
    assert obj.pos_relative_to(ORIGIN) - relative_pos == Vec2(0.25, -0.25)


def test_gravitational_force() -> None:
    obj = PhysicalObject(ORIGIN, Vec2(), Vec2(), 1)
    small_force = obj.gravitational_force(PhysicalObject(obj, Vec2(1, 2), Vec2(), 1))
    large_force = obj.gravitational_force(PhysicalObject(obj, Vec2(-1, 2), Vec2(), 2))
    double_distance_force = obj.gravitational_force(PhysicalObject(obj, 2 * Vec2(1, 2), Vec2(), 1))
    assert small_force.x > 0
    assert small_force.y > 0
    assert large_force.x < 0
    assert large_force.y > 0
    assert double_distance_force.x > 0
    assert double_distance_force.y > 0
    assert isclose(2, large_force.length() / small_force.length())
    assert isclose(4, small_force.length() / double_distance_force.length())


def test_threedimensional_disk_mass_scaling() -> None:
    radius = 1.23
    disk = Disk(ORIGIN, Vec2(), Vec2(), radius)
    double_size_disk = Disk(disk, Vec2(), Vec2(), radius * 2)

    assert isclose(2**3, double_size_disk.mass / disk.mass), (
        "Scaling the radius by `t` should scale the mass by a factor `t**3`"
    )


def test_disk_drawing() -> None:
    width, height = 50, 50
    color = Color(255, 0, 0)
    black = Color(0, 0, 0)
    camera_center = Vec2(-3, 4)
    camera = Camera(camera_center, 1, Surface((width, height)))
    disk = Disk(ORIGIN, Vec2(1, 0), Vec2(0, 0), radius=10, color=color)
    disk.draw(camera)
    camera.surface.lock()

    good = 0
    bad = 0
    drawn = 0

    for y in range(height):
        for x in range(width):
            pixel = camera.surface.get_at((x, y))
            # Ignore anti-aliasing
            if pixel in (color, black):
                pixel_circle = pixel == color
                worldcoor = Vec2(x, y) + camera_center - Vec2(width, height) / 2
                coordinate_circle = disk._pos.distance_to(worldcoor) < disk.radius

                if pixel_circle:
                    drawn += 1

                if pixel_circle == coordinate_circle:
                    good += 1
                else:
                    bad += 1

    threshold = 0.02
    assert isclose(good, (good + bad), rel_tol=threshold), (
        "The drawn circle should mostly agree with the idealised circle"
    )

    rect_area = width * height
    circle_area = disk.radius**2 * math.pi
    assert isclose(drawn, circle_area, abs_tol=rect_area * threshold), (
        "The area we drew should be close in size to the circle's idealised area"
    )

    camera.surface.unlock()


def test_simple_disk_bounce() -> None:
    disk_a = Disk(ORIGIN, Vec2(), Vec2(), 1)
    disk_b = Disk(disk_a, Vec2(-1, 0), Vec2(1, 0), 1)

    disk_a.bounce_off_of_disk(disk_b)

    assert disk_a.vel_relative_to(ORIGIN).y == 0, "Disk's vertical velocity should be unchanged"
    assert disk_a.vel_relative_to(ORIGIN).x > 0.05, (
        "Disk's horizontal velocity should be increased due to non-elastic bounce"
    )
    assert disk_b.vel_relative_to(disk_a).y == 0, "Disk's vertical velocity should be unchanged"
    assert disk_b.vel_relative_to(disk_a).x < 1 - 0.05, (
        "Disk's horizontal velocity should be reduced due to non-elastic bounce"
    )


def test_disk_bounce() -> None:
    disk_a = Disk(Vec2(0, 0), Vec2(0, 0), radius=1, color=Color(0, 0, 0))
    disk_b = Disk(Vec2(4, 0), Vec2(0, 0), radius=2, color=Color(0, 0, 0))

    assert disk_a.bounce_off_of_disk(disk_b) is None, "Non-intersecting disks shouldn't bounce"

    disk_c = Disk(Vec2(0, 1), Vec2(1, 0), radius=1, color=Color(0, 0, 0))

    bounce_count = 0
    for _ in range(200):
        disk_c.step(0.01)
        disk_b.step(0.01)
        bounce = disk_c.bounce_off_of_disk(disk_b)
        if bounce is not None:
            bounce_count += 1
            assert bounce == 0.0, "Bounce should be clamped to 0 for small-mass disks"

            assert isclose(disk_c.radius + disk_b.radius, disk_c.distance_to(disk_b)), "Disks should be flush"
        else:
            assert not isclose(disk_c.radius + disk_b.radius, disk_c.distance_to(disk_b)), "Disks should not be flush"
        if bounce_count <= 0:
            assert disk_c._vel == Vec2(1, 0)
            assert disk_b._vel == Vec2(0, 0)
        if bounce_count >= 1:
            assert disk_c._vel.x < 0, "Disk should be moving to the left"
            assert disk_c._vel.y > 0, "Disk should be moving up"

        assert disk_b._vel == Vec2(0, 0), "Disk_b should be unaffected"

    assert bounce_count == 1
