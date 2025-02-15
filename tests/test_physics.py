from pygame.math import Vector2 as Vec2

from physics import PhysicalObject


def test_step():
    obj = PhysicalObject(Vec2(0, 0), Vec2(1, -1), 1)
    obj.step(0.25)
    assert obj.pos == Vec2(0.25, -0.25)

def test_
