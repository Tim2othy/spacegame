import math

from pygame import Color, Surface
from pygame.math import Vector2 as Vec2
import pytest

from camera import Camera
from physics import Disk, PhysicalObject
from math import isclose


def test_step():
    obj = PhysicalObject(Vec2(0, 0), Vec2(1, -1), 1)
    obj.step(0.25)
    assert obj.pos == Vec2(0.25, -0.25)


def test_gravitational_force():
    obj = PhysicalObject(Vec2(), Vec2(), 1)
    small_force = obj.gravitational_force(PhysicalObject(Vec2(1, 2), Vec2(), 1))
    large_force = obj.gravitational_force(PhysicalObject(Vec2(-1, 2), Vec2(), 2))
    double_distance_force = obj.gravitational_force(PhysicalObject(Vec2(2, 4), Vec2(), 1))
    assert small_force.x > 0
    assert small_force.y > 0
    assert large_force.x < 0
    assert large_force.y > 0
    assert double_distance_force.x > 0
    assert double_distance_force.y > 0
    assert isclose(2, large_force.magnitude() / small_force.magnitude())
    assert isclose(4, small_force.magnitude() / double_distance_force.magnitude())


def test_threedimensional_disk_mass_scaling():
    radius = 1.23
    disk = Disk(Vec2(), Vec2(), radius)
    double_size_disk = Disk(Vec2(), Vec2(), radius * 2)

    assert isclose(2**3, double_size_disk.mass / disk.mass), (
        "Scaling the radius by `t` should scale the mass by a factor `t**3`"
    )


@pytest.mark.parametrize("relative_vel", [Vec2(10, 5), Vec2(10, 0), Vec2(10, -20)])
def test_relative_bounce(relative_vel: Vec2):
    # Bounces should work the same if the disks have the same velocity relative
    # to each other. So if we add an absolute_vel to their velocities, the
    # result shouldn't change.
    bounces: list[tuple[Disk, Disk]] = []

    for absolute_vel in [30 * Vec2(i, j) for i in range(-1, 2) for j in range(-1, 2)]:
        disk_a = Disk(Vec2(0, 0), absolute_vel + relative_vel, 1)
        disk_b = Disk(Vec2(1, 0), absolute_vel, 1)

        relative_vel, disk_a.vel - disk_b.vel
        disk_a.bounce_off_of_disk(disk_b)
        relative_vel, disk_a.vel - disk_b.vel

        assert disk_a.vel.y == (absolute_vel + relative_vel).y, "Disk's vertical velocity should be unchanged"
        assert disk_a.vel.x < (absolute_vel + relative_vel).x - 0.1, (
            "Disk's horizontal velocity should be reduced"
        )
        assert disk_b.vel.y == absolute_vel.y, "Disk's vertical velocity should be unchanged"
        assert disk_b.vel.x == absolute_vel.x, "Disk's horizontal velocity should be unchanged"

        bounces.append((disk_a, disk_b))

    # All the bounces should turn out the same, so compare them to the first bounces
    comparison_a, comparison_b = bounces[0]
    for disk_a, disk_b in bounces[1:]:
        assert isclose(0, (disk_a.pos - disk_b.pos - comparison_a.pos + comparison_b.pos).magnitude()), (
            "Bounce positions should agree relatively"
        )
        assert isclose(0, (disk_a.vel - disk_b.vel - comparison_a.vel + comparison_b.vel).magnitude()), (
            "Bounce velocities should agree relatively"
        )


def test_disk_drawing():
    width, height = 50, 50
    color = Color(255, 0, 0)
    black = Color(0, 0, 0)
    camera_center = Vec2(-3, 4)
    camera = Camera(camera_center, 1, Surface((width, height)))
    disk = Disk(Vec2(1, 0), Vec2(0, 0), radius=10, color=color)
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
                coordinate_circle = disk.pos.distance_to(worldcoor) < disk.radius

                if pixel_circle:
                    drawn += 1

                if pixel_circle == coordinate_circle:
                    good += 1
                else:
                    bad += 1

    threshold = 0.02
    assert good / (good + bad) > 1 - threshold, (
        "The drawn circle should mostly agree with the idealised circle"
    )

    rect_area = width * height
    circle_area = disk.radius**2 * math.pi
    assert abs((circle_area - drawn) / rect_area) < threshold, (
        "The area we drew should be close in size to the circle's idealised area"
    )

    camera.surface.unlock()


def test_disk_bounce():
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

            assert abs(disk_c.radius + disk_b.radius - disk_c.pos.distance_to(disk_b.pos)) < EPSILON, (
                "Disks should be flush"
            )
        else:
            assert abs(disk_c.radius + disk_b.radius - disk_c.pos.distance_to(disk_b.pos)) > EPSILON, (
                "Disks should not be flush"
            )
        if bounce_count <= 0:
            assert disk_c.vel == Vec2(1, 0)
            assert disk_b.vel == Vec2(0, 0)
        if bounce_count >= 1:
            assert disk_c.vel.x < 0, "Disk should be moving to the left"
            assert disk_c.vel.y > 0, "Disk should be moving up"

        assert disk_b.vel == Vec2(0, 0), "Disk_b should be unaffected"

    assert bounce_count == 1
