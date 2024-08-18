# Current Problems

1. Weird if 0 asteroids

    for some reason:

    for _ in range(0):
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, WORLD_HEIGHT)
        radius = random.randint(40, 120)
        asteroids.append(Asteroid(x, y, radius))

    If 0 asteroids are created the planets are invisible, but minimap and collision detection still work.

2. Laggy enemies

    If there are not 0 enemies the game laggs a lot

    find out what change caused this, it used to not be like this

3. thrusters not blue while being used 

# Improve code itself

1. Numpy

    für Vektor-Operationen, anstatt sie selbst zu schreiben, e.g. distance = lambda pos1 pos2: np.linalg.norm(pos1 - pos2) anstatt Deiner selbstgeschreibenen (aber nicht weniger korrekten!) distance-Funktion.

2. Physics Frames

    Es scheint, als würde Deine Physik von der Framerate abhängen. D.h., wenn das Spiel bei mir mit 30fps laufen würde, würde sich mein Schiff auch nur halb so schnell bewegen. Das wäre unerwünschtes Verhalten.


3. Camera Class


4. Minimap class?




5. Noch mehr zu classen machen


6. Klassenmethoden

Schreibe so viel wie möglich als Klassenmethoden auf e.g. der Code, der den Spieler eine Bullet schießen lässt
sollte vielleicht eine Klassenmethode von einer Player- oder Schiff-Klasse sein


7. More files

Teile den Code mehr auf. Anstatt diese #regions zu verwenden, lege für jede Klasse eine eigene .py-Datei an, die Du dann in main.py importierst.


8. Docstrings und/oder Type-Hints vertragen.
    
    High-Level Funktionen (z.b. __init__s von Klassen) könnten gut Docstrings und/oder Type-Hints vertragen.




# Obvious needs

1. Give everything good collision detection and world border detection

2. Collisions more realistic

    make it so that if two things bump into each other the speed of both is used in the calculation and not just the own speed
    look into what the actual physics are




# New features

1. Add images for ship and planets
    take inspiration from the game defender

2. background  
    also defender

3. Add simple sound effects
    also defender

4. Create a main menu
5. Clever homing missile
6. slow scatter shot
7. iron dome
8. space dust that has drag
9. Find out how to get more orbits to happen
10. create test map and real map
11. Asteroid belt



# Future Ideas

1. Add more advanced features (weapons, upgrades, etc.)
2. Implement multiple levels or procedural generation
3. Add more complex game mechanics (missions, story elements)
4. Make Neural net / RL AI that's pretty clever
5. Make it a coop game that two people play at the same time
6. Vielleicht wäre es cool, wenn die Kamera weiter rauszoomt, wenn sich das Schiff schneller bewegt.


