import pygame
from pygame.math import Vector2 as Vec2

from camera import Camera
from physics import PosVel

EPSILON = 1e-8

ORIGIN = PosVel._new_origin_and_only_use_this_if_you_really_know_what_you_are_doing()
