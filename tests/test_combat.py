import pytest
from pygame.math import Vector2 as Vec2

from ship import (
    _DEFAULT_MATRIX,
    _LOW_HEALTH_AND_PLAYER_VISIBLE_MATRIX,
    _LOW_HEALTH_MATRIX,
    _PLAYER_VISIBLE_MATRIX,
    HEALTH,
    AIState,
    BulletEnemy,
    EnemyConfig,
    MarkovEnemy,
    Matrix,
    MissileEnemy,
    PlayerConfig,
    RocketEnemy,
)
from universe import PlanetConfig, Universe


@pytest.mark.parametrize("enemy_type", [BulletEnemy, RocketEnemy, MissileEnemy, MarkovEnemy])
def test_bullet_paths(monkeypatch: pytest.MonkeyPatch, enemy_type: type[BulletEnemy]) -> None:
    monkeypatch.setattr(Universe, "apply_gravity", lambda _self, _dt: None)
    monkeypatch.setattr(BulletEnemy, "step", lambda _self, _dt: None)

    universe = Universe(1, 100)
    player = universe.add_player(PlayerConfig(relative_pos=Vec2(-500, 0)))
    (enemy_up, enemy_right, enemy_down) = (
        universe.add_enemy(EnemyConfig(relative_pos=vec, target_ship=player), enemy_type, relative_to=player)
        for vec in (Vec2(0, 500), Vec2(1000, 0), Vec2(0, -500))
    )

    _planet = universe.add_planet(PlanetConfig(relative_pos=Vec2(0, 250), radius=1), relative_to=player)

    bullet_up = player.new_bullet(Vec2(0, 50), Vec2(0, 100))
    bullet_right = player.new_bullet(Vec2(50, 0), Vec2(100, 0))
    bullet_down = player.new_bullet(Vec2(0, -50), Vec2(0, -100))

    player.projectiles.extend([bullet_up, bullet_right, bullet_down])

    # Also try shooting the enemy on the right with enemy bullets
    # (hopefully works because enemies can now hit each other)
    # We need an enemy here that's always a BulletEnemy as Rockets and Missiles fly
    # towards the player so won't hit the other Enemy Ships
    enemy_shooter = universe.add_enemy(
        EnemyConfig(relative_pos=Vec2(700, 700), target_ship=player), BulletEnemy, relative_to=player
    )

    enemy_up.projectiles.extend(
        [
            enemy_shooter.new_bullet(enemy_right.pos_relative_to(enemy_shooter) - Vec2(1, 0), Vec2(0.1, 0)),
        ]
    )

    # 10 seconds
    for _ in range(1000):
        universe.step(0.01)

    assert len(player.projectiles) == 0, "All player-bullets should have hit something"
    assert enemy_up.health == HEALTH, "The enemy on the top should be unharmed"
    assert enemy_right.health < HEALTH, "The enemy on the right should have been hit by an enemy bullet"
    assert enemy_down.health < HEALTH, "The enemy on the bottom should be harmed"


@pytest.mark.parametrize(
    "matrix",
    [
        _DEFAULT_MATRIX,
        _LOW_HEALTH_MATRIX,
        _PLAYER_VISIBLE_MATRIX,
        _LOW_HEALTH_AND_PLAYER_VISIBLE_MATRIX,
    ],
)
def test_transition_matrix_sums(matrix: Matrix) -> None:
    """Verify that each row in the transition matrices sums to 1."""
    for from_state, transitions in matrix.items():
        total = sum(transitions.values())
        assert total == 1.0, f"Row for {from_state} does not sum to 1: {total}"


@pytest.mark.parametrize("enemy_type", [BulletEnemy, RocketEnemy, MissileEnemy, MarkovEnemy])
@pytest.mark.parametrize("enemy_starting_pos", [Vec2(0, 600), Vec2(-400, 500)])
def test_enemy_hostility(enemy_type: type[BulletEnemy], enemy_starting_pos: Vec2) -> None:
    """Verify that any enemy will eventually find and hit the player."""
    universe = Universe(None, 100)
    player = universe.add_player(PlayerConfig(relative_pos=Vec2(0, 0)))
    _enemy = universe.add_enemy(EnemyConfig(relative_pos=enemy_starting_pos, target_ship=player), enemy_type)

    starting_health = player.health

    for _ in range(80 * 100):
        universe.step(0.01)
        if player.health < starting_health:
            break

    assert player.health < starting_health, "The player should have been hit by the enemy"


def test_enemy_retreat_behavior() -> None:
    """Test that a MarkovEnemy moves away from player when in retreat mode."""
    universe = Universe(None, 100)
    player = universe.add_player(PlayerConfig(relative_pos=Vec2(0, 0)))
    enemy: MarkovEnemy = universe.add_enemy(EnemyConfig(relative_pos=Vec2(250, 0), target_ship=player), MarkovEnemy)

    # Run simulation for a few seconds
    for _ in range(10):
        distance_squared_0 = player.distance_squared_to(enemy)
        for _ in range(100):
            enemy.ai.current_state = AIState.RETREAT
            universe.step(0.01)

        distance_squared_1 = player.distance_squared_to(enemy)
        assert distance_squared_0 < distance_squared_1, "Enemy should move away from player in retreat mode"


@pytest.mark.parametrize("enemy_vel", [Vec2(0, 0), Vec2(-20, 30), Vec2(40, -10)])
@pytest.mark.parametrize("player_vel", [Vec2(0, 0), Vec2(0, 50), Vec2(-30, 20)])
def test_aim_behaviour(player_vel: Vec2, enemy_vel: Vec2) -> None:
    """Test that a MarkovEnemy will hit a moving player with various relative velocities."""
    universe = Universe(None, 100)
    player = universe.add_player(PlayerConfig(relative_pos=Vec2(0, 0)))
    enemy: MarkovEnemy = universe.add_enemy(EnemyConfig(relative_pos=Vec2(250, 0), target_ship=player), MarkovEnemy)

    player._add_vel(player_vel)
    enemy._add_vel(enemy_vel)

    for _ in range(200):
        enemy.ai.current_state = AIState.AIM
        universe.step(0.01)
    assert player.health != HEALTH, "Enemy should have hit the player"


def test_markov_low_health_search() -> None:
    """Test whether a low health MarkovEnemy eventually finds a distant player."""
    universe = Universe(None, 100)
    player = universe.add_player(PlayerConfig(relative_pos=Vec2(0, 0)))
    enemy: MarkovEnemy = universe.add_enemy(EnemyConfig(relative_pos=Vec2(250, 0), target_ship=player), MarkovEnemy)
    enemy.health -= 20.0
    enemy.ai.current_state = AIState.RETREAT

    for _ in range(50000):
        universe.step(0.01)
        if player.health < HEALTH:
            break

    assert (
        player.health < HEALTH
    ), f"Enemy should have eventually found and damaged player. At the end the distance was {player.distance_to(enemy)}"


def test_search_behaviour() -> None:
    """Test that an enemy moves towards a player when in search mode."""
    universe = Universe(None, 100)
    player = universe.add_player(PlayerConfig(relative_pos=Vec2(0, 0)))
    enemy: MarkovEnemy = universe.add_enemy(EnemyConfig(relative_pos=Vec2(5000, 0), target_ship=player), MarkovEnemy)

    distance_0 = player.distance_to(enemy)

    enemy.ai.action_timer = 60000
    enemy.ai.current_state = AIState.SEARCH
    for _ in range(1000):
        universe.step(0.01)
        if enemy.ai.current_state != AIState.SEARCH:
            pytest.fail("Enemy should be in search mode")
            break

    distance_1 = player.distance_to(enemy)
    assert (
        distance_0 > distance_1 * 2
    ), f"Enemy should move towards player in search mode. But {distance_0} wasn't larger than {distance_1} * 2"


def test_enemy_healing() -> None:
    """Test that an enemy ship will heal when damaged and away from the player."""
    universe = Universe(None, 100)
    player = universe.add_player(PlayerConfig(relative_pos=Vec2(0, 0)))
    enemy = universe.add_enemy(EnemyConfig(relative_pos=Vec2(10000, 10000), target_ship=player), MarkovEnemy)
    starting_health = 5.0
    health_threshold = 11.0
    enemy.health = starting_health

    for _ in range(100 * 65):
        universe.step(0.01)
        if enemy.health > health_threshold:
            break

    assert (
        enemy.health > health_threshold
    ), f"Enemy health is {enemy.health}, but should have increased to at least {health_threshold}."
