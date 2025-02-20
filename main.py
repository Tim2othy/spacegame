"""Staging-grounds for the game."""

from __future__ import annotations

import asyncio
import platform
import random
import sys
from collections import deque

import pygame
from pygame import Color, Font, Surface
from pygame.math import Vector2 as Vec2

from camera import Camera
from constants import (
    ASTEROIDS_PER_PLANET,
    FPS_HISTORY_LENGTH,
    MINIMAP_BORDER_COLOR,
    MINIMAP_SIZE,
    PLANET_RADIUS_MU,
    PLANET_RADIUS_SIGMA,
    SCREEN_SIZE,
)
from profiler import global_profiler
from ship import BulletEnemy, MissileEnemy, PlayerShip, RocketEnemy, ShipInput
from universe import Planet, Universe

type Options = dict[str, bool]


def universe_from_options(options: Options) -> tuple[Universe, list[PlayerShip]]:
    """Create a universe from `options`.

    Returns a tuple (universe, player_ships)
    """
    num_enemies = 20 if options["small"] else 40
    world_size = 15000 if options["small"] else 30000
    world_size_vec = Vec2(world_size, world_size)

    player_ships: list[PlayerShip] = [
        PlayerShip(
            world_size_vec / 2, Vec2(0, 0), 10, Color("orange"), ShipInput.arrows(), "assets/player_ship.png"
        ),
    ]
    if options["splitscreen"]:
        player_ships.append(
            PlayerShip(
                world_size_vec / 2 + Vec2(50, 0),
                Vec2(0, 0),
                10,
                Color("yellow"),
                ShipInput.wasd(),
                "assets/player_ship.png",
            )
        )
    planets: list[Planet] = (
        [
            Planet(
                Vec2(random.uniform(0, world_size_vec[1]), random.uniform(0, world_size_vec[1])),
                random.lognormvariate(PLANET_RADIUS_MU, PLANET_RADIUS_SIGMA),
                color,
            )
            for color in [
                Color("darkred"),
                Color("green"),
                Color("mediumpurple"),
                Color("darkorange"),
                Color("royalblue"),
                Color("yellow"),
            ]
        ]
        if options["small"]
        else [
            Planet(Vec2(27_000, 29_000), 700, Color("darkred")),
            Planet(Vec2(21_000, 28_000), 800, Color("khaki")),
            Planet(Vec2(2_000, 27_000), 900, Color("royalblue")),
            Planet(Vec2(17_000, 26_000), 900, Color("mediumpurple")),
            Planet(Vec2(14_000, 23_000), 900, Color("darkslategray")),
            Planet(Vec2(17_000, 22_000), 800, Color("darkgreen")),
            Planet(Vec2(13_000, 21_000), 400, Color("crimson")),
            Planet(Vec2(18_000, 19_000), 300, Color("coral")),
            Planet(Vec2(13_000, 17_000), 400, Color("blue")),
            Planet(Vec2(8_000, 16_000), 500, Color("turquoise")),
            Planet(Vec2(25_000, 14_000), 300, Color("deeppink")),
            Planet(Vec2(18_000, 12_000), 900, Color("darkorange")),
            Planet(Vec2(22_000, 4_000), 850, Color("lightblue")),
            Planet(Vec2(14_500, 3_000), 600, Color("plum")),
            Planet(Vec2(28_000, 2_000), 200, Color("slategray")),
            Planet(Vec2(3_000, 1_000), 700, Color("navy")),
        ]
    )

    enemy_ships: list[BulletEnemy] = []
    for _ in range(num_enemies):
        pos = Vec2(random.uniform(0, world_size_vec.x), random.uniform(0, world_size_vec.y))
        enemy_type = random.choices([BulletEnemy, RocketEnemy, MissileEnemy], [0.6, 0.2, 0.2])[0]
        enemy_ships.append(enemy_type(pos, Vec2(0, 0), random.choice(player_ships)))

    universe = Universe(world_size_vec, planets, player_ships, enemy_ships, 100)
    for planet in planets:
        for _ in range(ASTEROIDS_PER_PLANET):
            universe.generate_asteroid(planet)

    return universe, player_ships


async def main() -> None:
    """Run the game."""
    screen_surface = None
    pygame.display.init()
    pygame.font.init()
    font = pygame.font.Font(None, 36)
    options: Options = {"small": False, "splitscreen": False, "invincible": False}

    try:
        pygame.display.set_caption("Space Game")
        screen_surface = pygame.display.set_mode(SCREEN_SIZE)

        while True:
            options = await show_menu(screen_surface, options, font)
            universe, player_ships = universe_from_options(options)

            cameras: list[Camera] = []
            player_count = len(player_ships)
            for player_ix, player in enumerate(player_ships):
                topleft = (player_ix * SCREEN_SIZE.x / player_count, 0)
                size = (SCREEN_SIZE.x / player_count, SCREEN_SIZE.y)
                subsurface = screen_surface.subsurface((topleft, size))
                camera = Camera(player.pos, 1.0, subsurface)
                cameras.append(camera)

            minimap_surface = screen_surface.subsurface(((SCREEN_SIZE.x - MINIMAP_SIZE.x, 0), MINIMAP_SIZE))
            minimap_camera = Camera(universe.size / 2, MINIMAP_SIZE.x / universe.size.x, minimap_surface)

            clock = pygame.time.Clock()

            fps: deque[float] = deque()
            running = True

            while running:
                if any(e.type == pygame.QUIT for e in pygame.event.get()):
                    running = False
                    break

                dt = clock.tick() / 1_000
                fps.append(clock.get_fps())
                if len(fps) > FPS_HISTORY_LENGTH:
                    fps.popleft()

                universe.handle_input(pygame.key.get_pressed())
                universe.step(dt)

                # Draw each camera's view and then blit it into SCREEN_SURFACE
                for player_ix, player_ship in enumerate(player_ships):
                    player_camera = cameras[player_ix]
                    player_camera.start_drawing_new_frame()
                    gameover = (
                        not universe.contains_point(player_ship.pos) or player_ship.health <= 0
                    ) and not options["invincible"]
                    if gameover:
                        gameover_font = pygame.font.Font(None, int(64 / player_count))
                        player_camera.draw_text("GAME OVER", None, gameover_font, Color("red"))
                        topleft = (int(player_ix * SCREEN_SIZE[0] / player_count), 0)
                        pygame.display.flip()
                        await asyncio.sleep(2)
                        running = False
                        break
                    universe.move_camera(player_camera, player_ix, dt)
                    universe.draw_background(player_camera)
                    universe.draw_grid(player_camera)
                    universe.draw(player_camera)
                    universe.draw_text(player_camera, player_ix, sum(fps) / len(fps))
                    topleft = (int(player_ix * SCREEN_SIZE[0] / player_count), 0)

                minimap_camera.start_drawing_new_frame()
                universe.draw(minimap_camera)

                # Draw minimap borders directly on SCREEN_SURFACE if needed
                minimap_camera.draw_vertical_hairline(MINIMAP_BORDER_COLOR, 0, 0, universe.size.y)
                minimap_camera.draw_horizontal_hairline(
                    MINIMAP_BORDER_COLOR, 0, universe.size.x, universe.size.y - 1
                )

                pygame.display.flip()
                await asyncio.sleep(0)

    except Exception as e:
        if screen_surface:
            screen_surface.fill((0, 0, 0))
            error_text = font.render(f"Error: {e!s}", antialias=True, color=Color("White"))
            error_rect = error_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2))
            screen_surface.blit(error_text, error_rect)
            pygame.display.flip()
            await asyncio.sleep(5)
        raise
    finally:
        profiler_stats = global_profiler.stats_to_str()
        print(profiler_stats)  # noqa: T201
        if sys.platform == "emscripten":
            platform.console.log(profiler_stats)

        pygame.quit()
        sys.exit()


async def show_menu(screen: Surface, options: Options, font: Font) -> Options:
    """Display the main menu until player presses Enter.

    Args:
        screen (Surface): To fill and render text on
        options (Options): Current options
        font (Font): Font to use for rendering

    Returns:
        Options: Updated options

    """
    option_selection_ix = 0
    title_text = font.render("Space Game", antialias=True, color=Color("White"))
    start_text = font.render("Press Enter to Start", antialias=True, color=Color("White"))

    def draw_menu() -> None:
        screen.fill(Color("Black"))

        screen.blit(title_text, title_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 6)))

        for i, (name, value) in enumerate(options.items()):
            color = (255, 255, 255) if i == option_selection_ix else (100, 100, 100)
            option_text = font.render(f"{name}: <{'On' if value else 'Off'}>", antialias=True, color=color)
            screen.blit(
                option_text, option_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 3 + i * 50))
            )

        screen.blit(start_text, start_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] * 5 / 6)))
        pygame.display.flip()

    option_names = list(options.keys())
    waiting = True
    while waiting:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
                elif event.key == pygame.K_UP:
                    option_selection_ix = (option_selection_ix - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    option_selection_ix = (option_selection_ix + 1) % len(options)
                elif event.key in {pygame.K_LEFT, pygame.K_RIGHT}:
                    options[option_names[option_selection_ix]] = not options[
                        option_names[option_selection_ix]
                    ]
        await asyncio.sleep(0)

    return options


if __name__ == "__main__":
    asyncio.run(main())
