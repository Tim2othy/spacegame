![Screenshot of a 2D space-videogame](./banner.png)

Fun small game we're making. Give us feedback, or just play the game.

You can play the game in the web [here](https://tim2othy.github.io/spacegame/build/web) or locally by following the instructions below.

## How to Play
- If there is one player, move with arrow keys, shoot with return.
- If there are two players:
    - Player 1 moves with arrow keys, shoots with return,
    - Player 2 moves with WASD, shoots with space.

In `constants.py` you can control the size of the map (`SMALL_MODE`), whether there are one or two players (`MULTI_MODE`), if there is just one or multiple planets (`ORBIT_MODE`), and whether one can die (`INVINCIBLE_MODE`).


## Building
Requires [uv](https://docs.astral.sh/uv/). Running the game locally (automatically installs python and dependencies):
```sh
uv run main.py
```