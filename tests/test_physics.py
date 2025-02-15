import math

from pygame import Color, Surface
from pygame.math import Vector2 as Vec2

from camera import Camera
from physics import Disk, PhysicalObject

EPSILON = 1e-8


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
    assert abs(2 - large_force.magnitude() / small_force.magnitude()) < EPSILON
    assert abs(4 - small_force.magnitude() / double_distance_force.magnitude()) < EPSILON


def test_threedimensional_disk_mass_scaling():
    density = 9.87
    radius = 1.23
    disk = Disk(Vec2(), Vec2(), density, radius, Color(0, 0, 0))
    double_density_disk = Disk(Vec2(), Vec2(), density * 2, radius, Color(0, 0, 0))
    double_size_disk = Disk(Vec2(), Vec2(), density, radius * 2, Color(0, 0, 0))

    assert abs(2 - double_density_disk.mass / disk.mass) < EPSILON
    assert abs(2**3 - double_size_disk.mass / disk.mass) < EPSILON


def test_disk_drawing():
    width, height = 50, 50
    color = Color(255, 0, 0)
    black = Color(0, 0, 0)
    camera_center = Vec2(-3, 4)
    camera = Camera(
        camera_center,
        1,
        Surface((width, height)),
    )
    disk = Disk(Vec2(1, 0), Vec2(0, 0), density=1, radius=10, color=color)
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
    # The two circles *mostly* agree
    assert good / (good + bad) > 1 - threshold

    # We did draw roughly the required area
    rect_area = width * height
    circle_area = disk.radius**2 * math.pi
    assert abs((circle_area - drawn) / rect_area) < threshold

    camera.surface.unlock()


def test_disk_bounce():
    disk_a = Disk(Vec2(0, 0), Vec2(0, 0), density=1, radius=1, color=Color(0, 0, 0))
    disk_b = Disk(Vec2(4, 0), Vec2(0, 0), density=1, radius=2, color=Color(0, 0, 0))

    # No bounce for non-intersecting disks
    assert disk_a.bounce_off_of_disk(disk_b) is None

    disk_c = Disk(Vec2(0, 1), Vec2(1, 0), density=1, radius=1, color=Color(0, 0, 0))

    bounce_count = 0
    for _ in range(200):
        disk_c.step(0.01)
        disk_b.step(0.01)
        bounce = disk_c.bounce_off_of_disk(disk_b)
        if bounce is not None:
            bounce_count += 1
            # Because these are small disks, the bounce
            # will be clamped to 0 (capping damage)
            assert bounce == 0.0

            # disk_c is flush with disk_b right now
            assert abs(disk_c.radius + disk_b.radius - disk_c.pos.distance_to(disk_b.pos)) < EPSILON
        else:
            # disk_c is not flush with disk_b
            assert abs(disk_c.radius + disk_b.radius - disk_c.pos.distance_to(disk_b.pos)) > EPSILON
        if bounce_count <= 0:
            assert disk_c.vel == Vec2(1, 0)
            assert disk_b.vel == Vec2(0, 0)
        if bounce_count >= 1:
            # Check rough angle of disk_c bouncing
            assert disk_c.vel.x < 0
            assert disk_c.vel.y > 0

            # Nothing happened to disk_b, I hope?
            assert disk_b.vel == Vec2(0, 0)

    assert bounce_count == 1
