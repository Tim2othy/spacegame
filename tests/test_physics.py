from pygame.math import Vector2 as Vec2
from pygame import Color

from physics import PhysicalObject, Disk

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
