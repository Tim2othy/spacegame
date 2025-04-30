SpaceGame Technical Documentation

# Overview
SpaceGame is a 2D space simulation game featuring planets, stars, ships, and physics-based interactions including gravity and collisions.
The game tries to obey the laws of relativity. For a spaceship flying through space the notion of an "absolute speed" shouldn't make any sense. And nowhere in the game
should relativity be violated.



The files are:
- camera: does camera stuff
    - contains Camera class, does camera stuff
- constants: most constants are where they are needed, but some are in this file
- enemy_ai: does more complicated enemy AI stuff
    - contains MarkovAI class
- main: runs game, handles menu and game loop
- physics: has basic classes
    - contains main classes, Pos, PosVel, Particle, Body, Disk
- profiler: does profiling stuff, not so important for docs
- projectiles:
    - contains Bullet, Rocket, Missile Flare classes
- ship:
    - contains ShipConfig, Ship, ShipInput, PlayerShip, EnemyConfig, BulletEnemy, RocketEnemy, MissileEnemy, MarkovEnemy classes
- universe: all the celestial bodies and bullet-planet, planet-planet etc. interactions are handled here
    - contains Star, PlanetConfig, Planet, UniverseOptions, Universe classes


# What the files do

## universe.py
Core simulation module containing celestial bodies and physics.


### Star
*Extends: Disk*
- **Purpose**: Represents a stationary celestial body
- **Key Properties**:
  - Position (x, y)
  - Radius
  - Color

### PlanetConfig
*Dataclass*
- **Purpose**: Configuration settings for planet creation
- **Attributes**:
  - `relative_pos`: Initial position relative to reference point
  - `relative_vel`: Initial velocity vector
  - `radius`: Size of the planet

### Planet
*Extends: Disk*
- **Purpose**: Represents a movable planet affected by physics
- **Key Properties**:
  - Position (x, y)
  - Velocity vector
  - Radius
  - Mass (derived from radius)

### UniverseOptions
*Dataclass*
- **Purpose**: Configuration for universe generation
- **Notable Settings**:
  - Dimensions
  - Physics constants
  - Generation parameters

### Universe
*Core simulation class*
- **Purpose**: Manages all game elements and their interactions
- **Key Methods**:
  - `add_player(player)`: Adds a player ship to the universe
  - `add_enemy(enemy)`: Adds an enemy ship to the universe
  - `add_planet(planet)`: Adds a planet to the universe
  - `_nearby_planets(position, radius)`: Returns planets within specified radius
  - `apply_gravity_to(object)`: Applies gravitational forces to an object
  - `apply_gravity()`: Applies gravity to all objects in the universe
  - `apply_bounce()`: Handles collision physics
  - `create_particles_on_disk(disk, count)`: Creates particle effects on a disk
  - `create_particle_cloud(position, count)`: Creates a cloud of particles
  - `collide_bullets()`: Handles bullet collision detection and effects
  - `handle_input(input_state)`: Processes user input
  - `step(dt)`: Advances simulation by time step
  - `draw_background()`: Renders the background
  - `draw()`: Renders all game objects
  - `draw_text(text, position)`: Renders text at position
  - `draw_grid()`: Renders coordinate grid
  - `generate_planet(config)`: Creates a planet from configuration
  - `from_options(options)`: Factory method to create universe from options

## ship.py
Module for player and enemy ship functionality.


### ShipConfig
- **Purpose**: Configuration settings for ship creation
- **Notable Attributes**:
  - Ship size
  - Speed characteristics
  - Weapon settings
  - Visual properties

### Ship
*Extends: Disk*
- **Purpose**: Base class for player and enemy vessels
- **Key Properties**:
  - Position and velocity
  - Health and shield status
  - Weapon systems
- **Key Methods**:
  - `thrust(direction, power)`: Move the ship
  - `rotate(angle)`: Change ship orientation
  - `fire_weapon()`: Attack action
  - `take_damage(amount)`: Handle incoming damage
  - `update(dt)`: Update ship state




### ShipInput

### EnemyConfig

### BulletEnemy

### RocketEnemy

### MissileEnemy

### MarkovEnemy

## camera.py
Module handling viewport and coordinate transformations.


### Camera
*Extends: Pos*
- **Purpose**: Controls the view into the game world
- **Key Properties**:
  - `_tracking`: Object camera follows
  - `_zoom`: Scale factor for rendering
  - `_surface`: Pygame surface to draw on
  - `_surface_size`: Dimensions of rendering area
  - `_surface_rect`: Rectangle defining render boundaries
- **Key Methods**:
  - `step()`: Update camera position to follow tracked object
  - `_rectangle_intersects_surface(rect)`: Check if an area is visible
  - `_world_to_surface(pos)`: Convert world coordinates to screen coordinates
  - `start_drawing_new_frame()`: Clear screen for new render
  - `draw_pixel(color, transparency, pos)`: Draw single pixel with alpha
  - `draw_circle(color, center, radius)`: Draw filled circle
  - `draw_polygon(color, points)`: Draw filled polygon
  - `draw_line(color, start, end, thickness)`: Draw line with width
  - `draw_hairline(color, start, end)`: Draw single-pixel width line
  - `draw_text(text, pos, font, color)`: Render text

### Helper Functions
- `_get_enclosing_rect(points)`: Calculate bounding box for set of points

## main.py
Entry point for the game with initialization and main loop.


### main()
- **Purpose**: Initialize and run the game
- **Key Operations**:
  - Initialize Pygame systems
  - Show menu and get game options
  - Create universe with planets and players
  - Set up cameras for each player
  - Run main game loop processing input, physics, and rendering
  - Handle game-over condition
  - Clean up and exit

### show_menu(screen, options, font)
- **Purpose**: Display and handle the main menu
- **Key Operations**:
  - Render menu title and options
  - Handle keyboard navigation
  - Toggle option values
  - Return updated options when player presses Enter


## physics.py
Module implementing the core physics engine and base classes for physical objects.

### Pos
- **Purpose**: Represents an object with a position in 2D space
- **Key Properties**:
  - `__pos`: Vector representing (x, y) position (private)
- **Key Methods**:
  - `_shift(delta)`: Move position by a vector
  - `pos_relative_to(other)`: Calculate position relative to another object
  - `distance_squared_to(other)`: Calculate squared distance (optimization)
  - `distance_to(other)`: Calculate distance to another position

### PosVel
*Extends: Pos*
- **Purpose**: Represents an object with both position and velocity
- **Key Properties**:
  - `__vel`: Velocity vector (private)
- **Key Methods**:
  - `step(dt)`: Update position based on velocity and time step
  - `_add_vel(vel)`: Add to current velocity
  - `vel_relative_to(other)`: Calculate velocity relative to another object
  - `_new_origin_and_only_use_this_if_you_really_know_what_you_are_doing()`: Static method to create origin point

### Particle
*Extends: PosVel*
- **Purpose**: Visual effects for explosions, thrusters, etc.
- **Key Properties**:
  - `_base_color`: Particle color
  - `_lifetime`: Remaining display time
  - `_max_lifetime`: Total display time
- **Key Methods**:
  - `step_and_survives(dt)`: Update and check if particle is still active
  - `draw(camera)`: Render particle with fading transparency

### Body
*Extends: PosVel*
- **Purpose**: Represents a physical body with mass and forces
- **Key Properties**:
  - `mass`: Object's mass, affects gravitational interactions
- **Key Methods**:
  - `add_impulse(impulse)`: Add instantaneous force effect
  - `apply_force(force, dt)`: Apply continuous force over time
  - `gravitational_force(other)`: Calculate gravitational pull from another body
  - `draw(camera)`: Abstract method implemented by subclasses

### Disk
*Extends: Body*
- **Purpose**: Represents a circular object with collision properties
- **Key Properties**:
  - `radius`: Size of the disk
  - `__radius_squared`: Cached square of radius for optimization
  - `color`: Display color
- **Key Methods**:
  - `draw(camera)`: Render disk as circle
  - `intersects_disk(other)`: Detect collision with another disk
  - `bounce_disks(other)`: Handle collision physics between two disks
  - `bounce_off_of_disk(other)`: Specialized collision for static objects


# Important relations


## Class Hierarchies

- **Pos**: Base class for objects with position
    - **Camera**: Manages viewport and rendering
    - **PosVel**: Extends Pos with velocity
        - **Particle**: Extends PosVel for visual effects
        - **Body**: Extends PosVel with mass and forces
            - **Bullet**: What Ships shoot
                - **Flare**: Slow moving Bullet with specific behavior
                - **Rocket**: Type of Bullet with specific behavior
                    - **Missile**: Another type of Bullet with different behavior
            - **Disk**: Extends Body with circular shape and radius
                - **Star**: Stationary celestial body
                - **Planet**: Movable celestial body
                - **Ship**: Base class for ships
                    - **PlayerShip**: Player-controlled ship
                    - **BulletEnemy**: AI-controlled ship
                        - **RocketEnemy**: Enemy ship that fires rockets
                        - **MissileEnemy**: Enemy ship that fires missiles
                        - **MarkovEnemy**: Advanced enemy AI using Markov chains




## Key Interactions
- **Universe** here gravity, bounces, bullet interactions and more are handled
- **Ship** creates **Bullet** objects when firing
- **Planet** objects exert gravitational forces on **Ship** and other **Planet** objects
