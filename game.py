"""Flappy Bird clone with a custom avatar image.

Usage:
    python game.py                 # uses avatar.png if present, else a yellow circle
    python game.py path/to/me.png  # use any image as the bird
"""

import random
import sys
from pathlib import Path

import pygame

# --- Config ---
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 0.45
FLAP_STRENGTH = -8
PIPE_WIDTH = 70
PIPE_GAP = 160
PIPE_SPEED = 3
PIPE_INTERVAL_MS = 1500
AVATAR_SIZE = (48, 48)
DEFAULT_AVATAR = Path(__file__).parent / "sigma.png"
# Pilot image for the ship obstacle; falls back to the player's avatar.
SHIP_PILOT = Path(__file__).parent / "enemy.png"
SHIP_CHANCE = 0.30
SHIP_SIZE = (96, 64)
SHIP_PILOT_SIZE = 34
SHIP_SPEED_Y = (2.0, 3.5)
BIG_SHIP_PILOT = Path(__file__).parent / "enemy_2.jpg"
# Chance that a spawned ship is the big variant.
BIG_SHIP_CHANCE = 0.35
BIG_SHIP_SCALE = 2
BIG_SHIP_HP = 3
BIG_SHIP_SPEED = 0.5
HIT_FLASH_FRAMES = 6
LASER_SPEED = 10
LASER_LENGTH = 22
EXPLOSION_FRAMES = 15
BG_SCROLL_SPEED = 0.3

BG_TOP = (25, 14, 8)
BG_BOTTOM = (80, 35, 5)
GRID = (95, 45, 12)
CIRCUIT = (255, 140, 0)
ORANGE = (240, 115, 20)
ORANGE_LIGHT = (255, 170, 70)
ORANGE_DARK = (170, 70, 10)
STEEL = (60, 55, 52)
STEEL_DARK = (30, 28, 26)
RIVET = (200, 200, 205)
HAZARD = (255, 165, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GROUND_HEIGHT = 80
CAP_HEIGHT = 24


def load_avatar(path: Path) -> pygame.Surface:
    """Load and scale the avatar image, or fall back to a drawn circle."""
    if path.is_file():
        image = pygame.image.load(str(path)).convert_alpha()
        return pygame.transform.smoothscale(image, AVATAR_SIZE)
    surface = pygame.Surface(AVATAR_SIZE, pygame.SRCALPHA)
    radius = AVATAR_SIZE[0] // 2
    pygame.draw.circle(surface, (250, 220, 50), (radius, radius), radius)
    pygame.draw.circle(surface, BLACK, (radius + 8, radius - 6), 4)
    return surface


def draw_hazard_stripes(screen: pygame.Surface, rect: pygame.Rect, stripe: int = 12):
    previous_clip = screen.get_clip()
    screen.set_clip(rect.clip(previous_clip))
    screen.fill(HAZARD, rect)
    for x in range(rect.left - rect.height, rect.right, stripe * 2):
        pygame.draw.polygon(
            screen,
            STEEL_DARK,
            [
                (x, rect.bottom),
                (x + stripe, rect.bottom),
                (x + stripe + rect.height, rect.top),
                (x + rect.height, rect.top),
            ],
        )
    screen.set_clip(previous_clip)


def make_background() -> pygame.Surface:
    """Pre-render a dark orange gradient with a circuit-board pattern."""
    surface = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        color = [int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)]
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))

    cell = 40
    for x in range(0, WIDTH, cell):
        pygame.draw.line(surface, GRID, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, cell):
        pygame.draw.line(surface, GRID, (0, y), (WIDTH, y))

    # Fixed seed so the circuit layout is the same every run.
    rng = random.Random(42)
    for _ in range(25):
        x = rng.randrange(0, WIDTH, cell)
        y = rng.randrange(0, HEIGHT - GROUND_HEIGHT, cell)
        dx, dy = rng.choice([(cell, 0), (0, cell), (cell, cell)])
        end = (x + dx * rng.randint(1, 3), y + dy * rng.randint(1, 2))
        # Draw a wrapped copy too so the background tiles seamlessly when scrolling.
        for ox in (0, -WIDTH):
            start_pt, end_pt = (x + ox, y), (end[0] + ox, end[1])
            pygame.draw.line(surface, ORANGE_DARK, start_pt, (end_pt[0], y), 2)
            pygame.draw.line(surface, ORANGE_DARK, (end_pt[0], y), end_pt, 2)
            pygame.draw.circle(surface, CIRCUIT, start_pt, 4)
            pygame.draw.circle(surface, CIRCUIT, end_pt, 3, 1)
    return surface


def make_ship(pilot: pygame.Surface) -> pygame.Surface:
    """Pre-render an orange robotic spaceship with the pilot image in the cockpit."""
    w, h = SHIP_SIZE
    ship = pygame.Surface(SHIP_SIZE, pygame.SRCALPHA)
    cx, dome_y, dome_r = w // 2, 30, 22

    for side in (-1, 1):
        pygame.draw.polygon(ship, ORANGE_DARK, [
            (cx + side * 20, 50), (cx + side * 44, h - 1), (cx + side * 30, 50)])
        pygame.draw.polygon(ship, STEEL_DARK, [
            (cx + side * 20, 50), (cx + side * 44, h - 1), (cx + side * 30, 50)], 2)

    hull = pygame.Rect(4, 30, w - 8, 28)
    pygame.draw.ellipse(ship, ORANGE, hull)
    pygame.draw.ellipse(ship, ORANGE_LIGHT, hull.inflate(-20, -18).move(0, -4))
    draw_hazard_stripes(ship, pygame.Rect(18, 48, w - 36, 5), 5)
    pygame.draw.ellipse(ship, STEEL_DARK, hull, 3)
    for x in (14, w - 14):
        pygame.draw.circle(ship, CIRCUIT, (x, 44), 4)
        pygame.draw.circle(ship, STEEL_DARK, (x, 44), 4, 1)
    for x in range(24, w - 20, 12):
        pygame.draw.circle(ship, RIVET, (x, 54), 2)

    pygame.draw.circle(ship, (45, 30, 20), (cx, dome_y), dome_r)
    pilot = pygame.transform.smoothscale(
        pilot, (SHIP_PILOT_SIZE, SHIP_PILOT_SIZE))
    mask = pygame.Surface(pilot.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(mask, WHITE, (SHIP_PILOT_SIZE // 2,)
                       * 2, SHIP_PILOT_SIZE // 2)
    pilot.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    ship.blit(pilot, pilot.get_rect(center=(cx, dome_y)))
    pygame.draw.circle(ship, ORANGE_LIGHT, (cx, dome_y), dome_r, 3)
    pygame.draw.circle(ship, STEEL_DARK, (cx, dome_y), dome_r + 1, 1)
    pygame.draw.line(ship, STEEL, (cx, dome_y - dome_r), (cx, 1), 2)
    pygame.draw.circle(ship, CIRCUIT, (cx, 3), 3)
    return ship


class Bird:
    def __init__(self, image: pygame.Surface):
        self.image = image
        self.rect = image.get_rect(center=(WIDTH // 4, HEIGHT // 2))
        self.y = float(self.rect.centery)
        self.velocity = 0.0

    def flap(self):
        self.velocity = FLAP_STRENGTH

    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.centery = int(self.y)

    def draw(self, screen: pygame.Surface):
        angle = max(-30, min(30, -self.velocity * 3))
        rotated = pygame.transform.rotate(self.image, angle)
        screen.blit(rotated, rotated.get_rect(center=self.rect.center))

    def hitbox(self) -> pygame.Rect:
        # Slightly smaller than the image so near-misses feel fair.
        return self.rect.inflate(-10, -10)


class PipePair:
    def __init__(self):
        play_height = HEIGHT - GROUND_HEIGHT
        gap_top = random.randint(60, play_height - PIPE_GAP - 60)
        self.top = pygame.Rect(WIDTH, 0, PIPE_WIDTH, gap_top)
        self.bottom = pygame.Rect(
            WIDTH, gap_top + PIPE_GAP, PIPE_WIDTH, play_height - gap_top - PIPE_GAP
        )
        self.scored = False

    @property
    def right(self) -> int:
        return self.top.right

    def update(self):
        self.top.x -= PIPE_SPEED
        self.bottom.x -= PIPE_SPEED

    def off_screen(self) -> bool:
        return self.top.right < 0

    def collides(self, rect: pygame.Rect) -> bool:
        return rect.colliderect(self.top) or rect.colliderect(self.bottom)

    def draw(self, screen: pygame.Surface):
        for rect, cap_y in (
            (self.top, self.top.bottom - CAP_HEIGHT),
            (self.bottom, self.bottom.top),
        ):
            pygame.draw.rect(screen, ORANGE, rect)
            pygame.draw.rect(screen, ORANGE_LIGHT,
                             (rect.x + 8, rect.y, 8, rect.height))
            pygame.draw.rect(screen, ORANGE_DARK,
                             (rect.right - 16, rect.y, 10, rect.height))
            for y in range(rect.top + 20, rect.bottom, 40):
                pygame.draw.line(screen, ORANGE_DARK,
                                 (rect.left, y), (rect.right, y), 2)
                for x in (rect.left + 6, rect.right - 6):
                    pygame.draw.circle(screen, RIVET, (x, y + 8), 3)
            pygame.draw.rect(screen, STEEL_DARK, rect, 3)

            cap = pygame.Rect(rect.x - 4, cap_y, PIPE_WIDTH + 8, CAP_HEIGHT)
            draw_hazard_stripes(screen, cap)
            pygame.draw.rect(screen, STEEL_DARK, cap, 3)


class Ship:
    """Obstacle that scrolls left while bouncing between ceiling and floor."""

    def __init__(self, image: pygame.Surface, scale: int = 1, hp: int = 1,
                 speed: float = 1.0):
        self.image = image
        self.scale = scale
        self.speed = speed
        self.hp = hp
        self.flash = 0
        floor = HEIGHT - GROUND_HEIGHT
        self.rect = image.get_rect(
            left=WIDTH, top=random.randint(0, floor - image.get_height()))
        # Float positions so fractional speeds aren't truncated by Rect ints.
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.vy = random.uniform(*SHIP_SPEED_Y) * \
            random.choice((-1, 1)) * speed
        self.scored = False
        self.frame = 0

    @property
    def right(self) -> int:
        return self.rect.right

    def hit(self) -> bool:
        """Apply one laser hit; return True if the ship is destroyed."""
        self.hp -= 1
        self.flash = HIT_FLASH_FRAMES
        return self.hp <= 0

    def update(self):
        self.frame += 1
        self.flash = max(0, self.flash - 1)
        self.x -= PIPE_SPEED * self.speed
        self.rect.x = int(self.x)
        self.y += self.vy
        floor = HEIGHT - GROUND_HEIGHT
        if self.y <= 0:
            self.y, self.vy = 0, abs(self.vy)
        elif self.y + self.rect.height >= floor:
            self.y, self.vy = floor - self.rect.height, -abs(self.vy)
        self.rect.y = int(self.y)

    def off_screen(self) -> bool:
        return self.rect.right < 0

    def collides(self, rect: pygame.Rect) -> bool:
        return rect.colliderect(self.rect.inflate(-12 * self.scale, -10 * self.scale))

    def draw(self, screen: pygame.Surface):
        # Ship flies left, so the thruster flame trails on the right.
        s = self.scale
        flicker = (10 + (self.frame // 3 % 2) * 6) * s
        x, y = self.rect.right - 6 * s, self.rect.top + 44 * s
        pygame.draw.polygon(screen, HAZARD, [
            (x, y - 7 * s), (x + flicker + 8 * s, y), (x, y + 7 * s)])
        pygame.draw.polygon(screen, WHITE, [
            (x, y - 3 * s), (x + flicker, y), (x, y + 3 * s)])
        image = self.image
        if self.flash:
            image = image.copy()
            image.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(image, self.rect)


class Laser:
    def __init__(self, x: int, y: int):
        self.rect = pygame.Rect(0, 0, LASER_LENGTH, 4)
        self.rect.midleft = (x, y)

    def update(self):
        self.rect.x += LASER_SPEED

    def draw(self, screen: pygame.Surface):
        pygame.draw.line(screen, ORANGE, self.rect.midleft,
                         self.rect.midright, 7)
        pygame.draw.line(screen, ORANGE_LIGHT, self.rect.midleft,
                         self.rect.midright, 3)


class Explosion:
    def __init__(self, center: tuple[int, int]):
        self.center = center
        self.frame = 0

    def update(self):
        self.frame += 1

    def done(self) -> bool:
        return self.frame >= EXPLOSION_FRAMES

    def draw(self, screen: pygame.Surface):
        radius = 10 + self.frame * 3
        pygame.draw.circle(screen, ORANGE, self.center, radius)
        pygame.draw.circle(screen, HAZARD, self.center, radius * 2 // 3)
        pygame.draw.circle(screen, WHITE, self.center, radius // 3)


class Game:
    def __init__(self, avatar_path: Path):
        pygame.init()
        pygame.display.set_caption("Flappy Sigma")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 28)
        self.avatar = load_avatar(avatar_path)
        self.background = make_background()
        self.bg_offset = 0.0
        pilot = load_avatar(
            SHIP_PILOT) if SHIP_PILOT.is_file() else self.avatar
        self.ship_image = make_ship(pilot)
        big_pilot = load_avatar(
            BIG_SHIP_PILOT) if BIG_SHIP_PILOT.is_file() else pilot
        self.big_ship_image = pygame.transform.smoothscale_by(
            make_ship(big_pilot), BIG_SHIP_SCALE)
        self.spawn_event = pygame.USEREVENT + 1
        self.high_score = 0
        self.reset()

    def reset(self):
        self.bird = Bird(self.avatar)
        self.pipes: list[PipePair | Ship] = []
        self.lasers: list[Laser] = []
        self.explosions: list[Explosion] = []
        self.score = 0
        self.state = "ready"  # ready -> playing -> over
        pygame.time.set_timer(self.spawn_event, 0)

    def start(self):
        self.state = "playing"
        pygame.time.set_timer(self.spawn_event, PIPE_INTERVAL_MS)
        self.bird.flap()

    def game_over(self):
        self.state = "over"
        self.high_score = max(self.high_score, self.score)
        pygame.time.set_timer(self.spawn_event, 0)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                pygame.quit()
                sys.exit()
            if event.type == self.spawn_event and self.state == "playing":
                if random.random() < SHIP_CHANCE:
                    if random.random() < BIG_SHIP_CHANCE:
                        self.pipes.append(Ship(
                            self.big_ship_image, BIG_SHIP_SCALE, BIG_SHIP_HP,
                            BIG_SHIP_SPEED))
                    else:
                        self.pipes.append(Ship(self.ship_image))
                else:
                    self.pipes.append(PipePair())
            if (
                event.type == pygame.KEYDOWN
                and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
                and self.state == "playing"
            ):
                self.lasers.append(
                    Laser(self.bird.rect.right, self.bird.rect.centery))
            flap = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or (
                event.type == pygame.MOUSEBUTTONDOWN
            )
            if flap:
                if self.state == "ready":
                    self.start()
                elif self.state == "playing":
                    self.bird.flap()
                else:
                    self.reset()

    def update(self):
        if self.state != "over":
            self.bg_offset = (self.bg_offset + BG_SCROLL_SPEED) % WIDTH
        if self.state != "playing":
            return
        self.bird.update()
        for pipe in self.pipes:
            pipe.update()
            if not pipe.scored and pipe.right < self.bird.rect.left:
                pipe.scored = True
                self.score += 1
        self.pipes = [p for p in self.pipes if not p.off_screen()]

        for laser in self.lasers:
            laser.update()
        for laser in list(self.lasers):
            target = next(
                (p for p in self.pipes if p.collides(laser.rect)), None)
            if target is None:
                continue
            # Pipes absorb lasers; only ships get destroyed.
            self.lasers.remove(laser)
            if isinstance(target, Ship) and target.hit():
                self.pipes.remove(target)
                self.explosions.append(Explosion(target.rect.center))
                if not target.scored:
                    self.score += 1
        self.lasers = [l for l in self.lasers if l.rect.left < WIDTH]

        for explosion in self.explosions:
            explosion.update()
        self.explosions = [e for e in self.explosions if not e.done()]

        hitbox = self.bird.hitbox()
        hit_pipe = any(p.collides(hitbox) for p in self.pipes)
        hit_bounds = hitbox.top < 0 or hitbox.bottom > HEIGHT - GROUND_HEIGHT
        if hit_pipe or hit_bounds:
            self.game_over()

    def draw_text(self, text: str, font: pygame.font.Font, y: int):
        shadow = font.render(text, True, BLACK)
        label = font.render(text, True, WHITE)
        x = WIDTH // 2 - label.get_width() // 2
        self.screen.blit(shadow, (x + 2, y + 2))
        self.screen.blit(label, (x, y))

    def draw(self):
        offset = int(self.bg_offset)
        self.screen.blit(self.background, (-offset, 0))
        self.screen.blit(self.background, (WIDTH - offset, 0))
        for pipe in self.pipes:
            pipe.draw(self.screen)
        for laser in self.lasers:
            laser.draw(self.screen)
        for explosion in self.explosions:
            explosion.draw(self.screen)
        ground = pygame.Rect(0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT)
        pygame.draw.rect(self.screen, STEEL, ground)
        draw_hazard_stripes(self.screen, pygame.Rect(
            0, ground.top, WIDTH, 16), 16)
        for x in range(20, WIDTH, 50):
            pygame.draw.circle(self.screen, RIVET, (x, ground.top + 40), 4)
            pygame.draw.circle(self.screen, STEEL_DARK,
                               (x, ground.top + 40), 4, 1)
        self.bird.draw(self.screen)

        if self.state == "ready":
            self.draw_text("Flappy Sigma", self.font, HEIGHT // 3)
            self.draw_text("Space / click to flap",
                           self.small_font, HEIGHT // 3 + 60)
            self.draw_text("Enter to shoot",
                           self.small_font, HEIGHT // 3 + 90)
        elif self.state == "playing":
            self.draw_text(str(self.score), self.font, 40)
        else:
            self.draw_text("Sigma Over", self.font, HEIGHT // 3)
            self.draw_text(f"Score: {self.score}",
                           self.small_font, HEIGHT // 3 + 60)
            self.draw_text(f"Best: {self.high_score}",
                           self.small_font, HEIGHT // 3 + 90)
            self.draw_text("Space / click to restart",
                           self.small_font, HEIGHT // 3 + 130)

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    avatar = DEFAULT_AVATAR
    Game(avatar).run()
