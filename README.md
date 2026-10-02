# Flappy Sigma

A Flappy Bird–style game built with [pygame-ce](https://pyga.me/), with an orange robotic theme, a custom avatar, enemy spaceships and lasers.

## Setup

You need **Python 3.9 or newer**.

1. Open a terminal in the project folder.
2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # macOS / Linux
   .venv\Scripts\activate         # Windows
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   > The game uses `pygame-ce` rather than `pygame`, because the original `pygame` doesn't provide ready-made installs for recent Python versions. The code still uses `import pygame`.

4. Run the game:

   ```bash
   python game.py
   ```

## Controls

| Key | Action |
| --- | --- |
| **Space** / **Mouse click** | Flap (also starts the game and restarts after a game over) |
| **Enter** | Fire a laser |
| **Esc** | Quit |

## How to play

- Flap to keep your avatar in the air and fly through the gaps between pipes.
- Hitting a pipe, an enemy ship, the ceiling or the floor ends the game.
- You score **1 point** for each obstacle you pass or ship you destroy.
- **Enemy ships** sometimes appear in place of pipes. They bounce between the ceiling and the floor.
  - **Small ships** go down in one laser hit.
  - **Big ships** are twice the size, move at half speed and take **3 hits**. They flash white each time you hit them.
- Pipes block lasers, so you can't shoot through them.

## Custom images

Put these files next to `game.py` to customise the game:

| File | Used for | If it's missing |
| --- | --- | --- |
| `sigma.png` | Your avatar | A yellow circle is drawn instead |
| `enemy.png` | The pilot in the small ships | Graham is used |
| `enemy_2.jpg` | The pilot in the big ships | Evil Verne is used |

Square images work best. PNGs with transparent backgrounds look cleanest. The avatar is resized to 48×48, and pilots are cropped to a circle inside the cockpit.

## How it works

Everything is in `game.py`, which is organised into a few classes:

- **`Game`** runs the main loop at 60 frames per second: it handles input, updates everything, then draws everything. It moves between three screens: `ready` → `playing` → `over`. A timer spawns a new obstacle every 1.5 seconds.
- **`Bird`** is the player. Each frame gravity adds to its downward speed, and a flap sets it to a fixed upward speed. The avatar tilts based on its speed.
- **`PipePair`** is a top and bottom pipe with a random gap between them, scrolling left.
- **`Ship`** is an enemy that scrolls left while bouncing off the ceiling and floor. Each ship has health points (`hp`), so big ships can take several hits.
- **`Laser`** and **`Explosion`** handle shooting and the blast when a ship is destroyed.
- **`make_background()`** and **`make_ship()`** draw the circuit-board background and the spaceships once at startup, so they don't have to be redrawn from scratch every frame. The background scrolls slowly and repeats so it looks far away.

Collisions use pygame's rectangle checks (`Rect.colliderect`). The hit areas are slightly smaller than the images, so near misses feel fair.

## Tweaking the game

All the main settings are constants at the top of `game.py`:

| Setting | What it controls |
| --- | --- |
| `GRAVITY`, `FLAP_STRENGTH` | How heavy the avatar feels and how strong a flap is |
| `PIPE_GAP`, `PIPE_SPEED`, `PIPE_INTERVAL_MS` | Pipe gap size, scroll speed and how often obstacles spawn |
| `SHIP_CHANCE` | Chance an obstacle is a ship instead of pipes (`0.30` = 30%) |
| `BIG_SHIP_CHANCE` | Chance a ship is the big variant (`0.35` = 35% of ships) |
| `BIG_SHIP_HP`, `BIG_SHIP_SPEED`, `BIG_SHIP_SCALE` | Big ship health, speed multiplier and size multiplier |
| `LASER_SPEED` | How fast lasers travel |
| `BG_SCROLL_SPEED` | How fast the background scrolls |
