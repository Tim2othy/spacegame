"""Staging-grounds for the game."""

from __future__ import annotations

import asyncio
import platform
import sys
from dataclasses import fields
from typing import TYPE_CHECKING

import pygame
from pygame import Color, Surface
from pygame.font import Font

from camera import Camera
from profiler import global_profiler
from universe import Universe, UniverseOptions

if TYPE_CHECKING:
    from ship import PlayerShip

SCREEN_SIZE = pygame.math.Vector2(1700, 1000)
MINIMAP_SIZE = pygame.math.Vector2(200, 200)


async def get_font_screen_surface() -> tuple[Surface, Font]:
    """Initialize pygame and create basic game objects."""
    screen_surface = None
    pygame.display.init()
    pygame.font.init()
    font = Font(None, 36)
    pygame.display.set_caption("Space Game")
    screen_surface = pygame.display.set_mode(SCREEN_SIZE)
    return screen_surface, font


async def init_game() -> tuple[Universe, list[tuple[PlayerShip, Camera]], Camera, int]:
    """Return values needed to start the game."""
    options = UniverseOptions()
    screen_surface, font = await get_font_screen_surface()

    options = await show_menu(screen_surface, options, font)
    universe, player_ships = Universe.from_options(options)

    players_and_cameras: list[tuple[PlayerShip, Camera]] = []
    player_count = len(player_ships)
    for player_ix, player in enumerate(player_ships):
        topleft = (player_ix * SCREEN_SIZE.x / player_count, 0)
        size = (SCREEN_SIZE.x / player_count, SCREEN_SIZE.y)
        subsurface = screen_surface.subsurface((topleft, size))
        camera = Camera(subsurface, player, 1.0 / 2.0)
        players_and_cameras.append((player, camera))

    minimap_surface = screen_surface.subsurface(((SCREEN_SIZE.x - MINIMAP_SIZE.x, 0), MINIMAP_SIZE))
    minimap_camera = Camera(minimap_surface, player_ships[0], 0.01)

    return universe, players_and_cameras, minimap_camera, player_count


async def main() -> None:
    """Run the game."""
    keep_playing = True

    while keep_playing:
        clock = pygame.time.Clock()

        universe, players_and_cameras, minimap_camera, player_count = await init_game()
        running = True

        while running:
            if any(e.type == pygame.QUIT for e in pygame.event.get()):
                running = False
                keep_playing = False
                break

            dt = clock.tick() / 1_000

            # Draw each camera's view
            for player, camera in players_and_cameras:
                camera.start_drawing_new_frame()
                if player.health <= 0:
                    gameover_font = Font(None, int(64 / player_count))
                    camera.draw_text("GAME OVER", None, gameover_font, Color("red"))
                    pygame.display.flip()
                    await asyncio.sleep(2)
                    running = False
                    break
                camera.nearest_object = universe.find_nearest_object_to(player)
                camera.step()
                minimap_camera.step()
                universe.draw(camera)
                universe.draw_text(camera, player, clock.get_fps())

            universe.handle_input(pygame.key.get_pressed())
            universe.step(dt)

            minimap_camera.start_drawing_new_frame()
            universe.draw(minimap_camera)
            pygame.display.flip()
            await asyncio.sleep(0)

    profiler_stats = global_profiler.stats_to_str()
    print(profiler_stats)  # noqa: T201
    if sys.platform == "emscripten":
        platform.console.log(profiler_stats)

    pygame.quit()
    sys.exit()


async def show_menu(screen: Surface, options: UniverseOptions, font: Font) -> UniverseOptions:
    """Display the main menu until player presses Enter, and return updated options."""
    option_selection_ix = 0
    title_text = font.render("Space Game", antialias=True, color=Color("White"))
    start_text = font.render("Press Enter to Start", antialias=True, color=Color("White"))

    option_fields = list(fields(options))

    def draw_menu() -> None:
        screen.fill(Color("Black"))

        screen.blit(title_text, title_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 6)))

        for i, field in enumerate(option_fields):
            color = (255, 255, 255) if i == option_selection_ix else (100, 100, 100)
            option_text = font.render(
                f"{field.name}: <{'On' if getattr(options, field.name) else 'Off'}>", antialias=True, color=color
            )
            screen.blit(option_text, option_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 3 + i * 50)))

        screen.blit(start_text, start_text.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] * 5 / 6)))
        pygame.display.flip()

    while True:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return options
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    direction = -1 if event.key == pygame.K_UP else 1
                    option_selection_ix = (option_selection_ix + direction) % len(option_fields)
                elif event.key in {pygame.K_LEFT, pygame.K_RIGHT}:
                    field = option_fields[option_selection_ix]
                    # TODO: Since we already have a `field: Field`, is there something more
                    # idiomatic than setattr, getattr?
                    setattr(options, field.name, not getattr(options, field.name))
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
