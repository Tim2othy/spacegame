from pygame.math import Vector2
from pygame import Color
from camera import Camera
from physics import PhysicalObject
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ship import Ship


class Bullet(PhysicalObject):
    """A triangular bullet."""

    def __init__(self, pos: Vector2, vel: Vector2, color: Color):
        super().__init__(pos, vel, 1.0)
        self.color = color

    def draw(self, camera: Camera):
        forward = self.vel.normalize() if self.vel != Vector2(0, 0) else Vector2(1, 0)
        camera.draw_polygon(
            self.color,
            [
                self.pos + 5 * forward,
                self.pos + 2 * forward.rotate(150),
                self.pos + 2 * forward.rotate(-150),
            ],
        )


class Rocket(Bullet):
    def __init__(self, pos: Vector2, vel: Vector2, color: Color, target_ship: "Ship"):
        super().__init__(pos, vel, color)
        self.target_ship = target_ship
        self.vel /= 4
        self.homing_thrust = 1000 * self.mass
        self.homing_timer = 0
        self.homing_duration = 1
        self.nonhoming_duration = 3
        self._total_duration = self.homing_duration + self.nonhoming_duration

    def step(self, dt: float):
        self.homing_timer = (self.homing_timer + dt) % self._total_duration

        if self.homing_timer <= self.homing_duration:
            # Target the ship
            dir = self.target_ship.pos - self.pos
            if dir != Vector2(0, 0):
                dir.normalize_ip()
                self.apply_force(dir * self.homing_thrust, dt)

        super().step(dt)

    def draw(self, camera: Camera):
        forward = self.vel.normalize() if self.vel != Vector2(0, 0) else Vector2(1, 0)
        left = Vector2(-forward.y, forward.x)
        right = -left
        backward = -forward

        # Spooky homing body
        if self.homing_timer <= self.homing_duration:
            camera.draw_polygon(
                self.color.lerp(Color("blue"), 0.5),
                [
                    self.pos + 4 * (left + forward),
                    self.pos + 4 * (left + backward),
                    self.pos + 4 * (right + backward),
                    self.pos + 4 * (right + forward),
                ],
            )

        # Missile body
        camera.draw_polygon(
            self.color,
            [
                self.pos + 3 * (left + forward),
                self.pos + 3 * (left + backward),
                self.pos + 3 * (right + backward),
                self.pos + 3 * (right + forward),
                self.pos + 2 * (3 * forward),
            ],
        )