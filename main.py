"""2D top-down zombie survival game.

Run with:  python main.py
Requires:  pygame  (pip install -r requirements.txt)
"""
import math
import random
import sys

import pygame

from game import settings as s
from game.camera import Camera
from game.player import Player
from game.bullet import Bullet
from game.enemy import Enemy
from game.world import World


class XPOrb:
    def __init__(self, x, y, amount):
        self.pos = pygame.math.Vector2(x, y)
        self.amount = amount
        self.dead = False


def spawn_enemy(player, world, scale):
    angle = random.uniform(0, 2 * math.pi)
    radius = random.uniform(520, 780)
    x = player.pos.x + math.cos(angle) * radius
    y = player.pos.y + math.sin(angle) * radius
    x = max(40, min(x, world.width - 40))
    y = max(40, min(y, world.height - 40))
    r = random.random()
    if scale > 2.2 and r < 0.18:
        etype = "brute"
    elif r < 0.32:
        etype = "runner"
    else:
        etype = "zombie"
    hp_scale = 1.0 + (scale - 1.0) * 0.6
    return Enemy(x, y, etype, scale=hp_scale)


# --------------------------- drawing helpers --------------------------- #

def draw_grass(screen, camera):
    ts = s.TILE_SIZE
    start_x = int(camera.offset.x // ts)
    start_y = int(camera.offset.y // ts)
    cols = s.WIDTH // ts + 2
    rows = s.HEIGHT // ts + 2
    for i in range(cols):
        for j in range(rows):
            tx = start_x + i
            ty = start_y + j
            color = s.GRASS if (tx + ty) % 2 == 0 else s.GRASS_ALT
            sx = int(tx * ts - camera.offset.x)
            sy = int(ty * ts - camera.offset.y)
            screen.fill(color, (sx, sy, ts, ts))


def draw_world(screen, camera, world, player, enemies, bullets, orbs):
    draw_grass(screen, camera)
    # Cars
    for car in world.cars:
        sx, sy = camera.world_to_screen(car.rect.x, car.rect.y)
        pygame.draw.rect(screen, car.color, (sx, sy, car.rect.w, car.rect.h), border_radius=6)
        pygame.draw.rect(screen, (30, 30, 35), (sx, sy, car.rect.w, car.rect.h), 2, border_radius=6)
        # windshield strip
        pygame.draw.rect(screen, (160, 200, 220),
                         (sx + car.rect.w * 0.28, sy + car.rect.h * 0.28,
                          car.rect.w * 0.44, car.rect.h * 0.44), border_radius=4)
    # XP orbs
    for orb in orbs:
        sx, sy = camera.world_to_screen(orb.pos.x, orb.pos.y)
        pygame.draw.circle(screen, s.YELLOW, (sx, sy), 6)
        pygame.draw.circle(screen, (255, 255, 200), (sx, sy), 3)
    # Bullets
    for b in bullets:
        sx, sy = camera.world_to_screen(b.pos.x, b.pos.y)
        pygame.draw.circle(screen, s.WHITE, (sx, sy), b.radius)
    # Enemies
    for e in enemies:
        draw_creature(screen, camera, e)
    # Buildings (drawn above ground entities so interiors are hidden from outside)
    for b in world.buildings:
        sx, sy = camera.world_to_screen(b.rect.x, b.rect.y)
        pygame.draw.rect(screen, b.wall_color, (sx, sy, b.rect.w, b.rect.h))
        pygame.draw.rect(screen, b.roof_color, (sx, sy, b.rect.w, b.rect.h), 8)
        # Door
        dsx, dsy = camera.world_to_screen(b.door_rect.x, b.door_rect.y)
        pygame.draw.rect(screen, (30, 22, 18), (dsx, dsy, b.door_rect.w, b.door_rect.h))
        label = pygame.font.SysFont("consolas", 14).render("\u0432\u0445\u043e\u0434", True, s.WHITE)
        screen.blit(label, (dsx - 6, dsy + b.door_rect.h + 2))
    # Trees (drawn last so canopies overlap nicely)
    for t in world.trees:
        sx, sy = camera.world_to_screen(t.pos.x, t.pos.y)
        pygame.draw.circle(screen, s.TREE_TRUNK, (sx, sy), 7)
        pygame.draw.circle(screen, s.TREE_LEAF, (sx, sy - 4), t.radius)
        pygame.draw.circle(screen, (58, 116, 64), (sx - t.radius // 3, sy - 8), t.radius // 2)
    # Player
    draw_player(screen, camera, player)


def draw_creature(screen, camera, e):
    sx, sy = camera.world_to_screen(e.pos.x, e.pos.y)
    half = e.size // 2
    pygame.draw.rect(screen, e.color, (sx - half, sy - half, e.size, e.size), border_radius=5)
    pygame.draw.rect(screen, (20, 30, 20), (sx - half, sy - half, e.size, e.size), 2, border_radius=5)
    # HP bar
    if e.hp < e.max_hp:
        ratio = max(0.0, e.hp / e.max_hp)
        pygame.draw.rect(screen, (60, 0, 0), (sx - half, sy - half - 8, e.size, 4))
        pygame.draw.rect(screen, s.RED, (sx - half, sy - half - 8, int(e.size * ratio), 4))


def draw_player(screen, camera, player):
    sx, sy = camera.world_to_screen(player.pos.x, player.pos.y)
    half = player.size // 2
    pygame.draw.rect(screen, s.BLUE, (sx - half, sy - half, player.size, player.size), border_radius=6)
    pygame.draw.rect(screen, s.WHITE, (sx - half, sy - half, player.size, player.size), 2, border_radius=6)
    # Gun barrel pointing toward aim
    aim = player.aim
    end = (int(sx + aim.x * (half + 14)), int(sy + aim.y * (half + 14)))
    pygame.draw.line(screen, (220, 220, 220), (sx, sy), end, 4)


def draw_interior(screen, camera, interior, player, font):
    screen.fill(s.DARK)  # everything outside is hidden
    ox, oy = camera.offset.x, camera.offset.y
    # Floor
    pygame.draw.rect(screen, s.FLOOR, (int(-ox), int(-oy), interior.width, interior.height))
    # Floor tiling for depth
    step = 64
    for gx in range(0, interior.width, step):
        pygame.draw.line(screen, (58, 48, 42), (int(gx - ox), int(-oy)),
                         (int(gx - ox), int(interior.height - oy)), 1)
    for gy in range(0, interior.height, step):
        pygame.draw.line(screen, (58, 48, 42), (int(-ox), int(gy - oy)),
                         (int(interior.width - ox), int(gy - oy)), 1)
    # Walls
    for wall in interior.wall_colliders()[:5]:
        pygame.draw.rect(screen, s.WALL, (int(wall.x - ox), int(wall.y - oy), wall.w, wall.h))
    # Exit marker
    eg = interior.exit_gap
    pygame.draw.rect(screen, (40, 90, 50), (int(eg.x - ox), int(eg.y - oy), eg.w, eg.h))
    exit_label = font.render("\u0432\u044b\u0445\u043e\u0434", True, s.WHITE)
    screen.blit(exit_label, (int(eg.centerx - ox - 18), int(eg.y - oy - 22)))
    # Furniture
    for f in interior.furniture:
        pygame.draw.rect(screen, f.color, (int(f.rect.x - ox), int(f.rect.y - oy), f.rect.w, f.rect.h), border_radius=4)
        pygame.draw.rect(screen, (20, 18, 16), (int(f.rect.x - ox), int(f.rect.y - oy), f.rect.w, f.rect.h), 2, border_radius=4)
        name = font.render(f.name, True, (230, 225, 215))
        screen.blit(name, (int(f.rect.x - ox), int(f.rect.y - oy - 16)))
    # Items
    for it in interior.items:
        if it.taken:
            continue
        r = it.rect
        pygame.draw.rect(screen, s.GREEN, (int(r.x - ox), int(r.y - oy), r.w, r.h), border_radius=3)
        name = font.render(it.name, True, s.WHITE)
        screen.blit(name, (int(r.x - ox - 6), int(r.y - oy - 16)))
    draw_player(screen, camera, player)


def draw_hud(screen, player, font, bigfont, elapsed, enemy_count, score, mode):
    # Health bar
    bar_w = 260
    pygame.draw.rect(screen, (50, 0, 0), (20, 20, bar_w, 22), border_radius=4)
    hp_ratio = max(0.0, player.hp / player.max_hp)
    pygame.draw.rect(screen, s.RED, (20, 20, int(bar_w * hp_ratio), 22), border_radius=4)
    pygame.draw.rect(screen, s.WHITE, (20, 20, bar_w, 22), 2, border_radius=4)
    screen.blit(font.render(f"HP {int(player.hp)}/{int(player.max_hp)}", True, s.WHITE), (26, 22))
    # XP bar
    pygame.draw.rect(screen, (10, 30, 50), (20, 50, bar_w, 14), border_radius=4)
    xp_ratio = player.xp / player.xp_to_next if player.xp_to_next else 0
    pygame.draw.rect(screen, s.BLUE, (20, 50, int(bar_w * xp_ratio), 14), border_radius=4)
    pygame.draw.rect(screen, s.WHITE, (20, 50, bar_w, 14), 1, border_radius=4)
    # Stats text
    stats = [
        f"\u0423\u0440\u043e\u0432\u0435\u043d\u044c: {player.level}",
        f"\u0423\u0440\u043e\u043d: {int(player.damage)}",
        f"\u0421\u043a\u043e\u0440\u043e\u0441\u0442\u044c: {int(player.speed)}",
        f"\u0421\u043a\u043e\u0440\u043e\u0441\u0442\u0440\u0435\u043b: {1/player.fire_rate:.1f}/\u0441",
    ]
    for i, line in enumerate(stats):
        screen.blit(font.render(line, True, s.WHITE), (20, 74 + i * 20))
    # Right side info
    info = [
        f"\u0421\u0447\u0451\u0442: {score}",
        f"\u0412\u0440\u0435\u043c\u044f: {int(elapsed)}\u0441",
        f"\u0412\u0440\u0430\u0433\u043e\u0432: {enemy_count}",
    ]
    for i, line in enumerate(info):
        surf = font.render(line, True, s.WHITE)
        screen.blit(surf, (s.WIDTH - surf.get_width() - 20, 20 + i * 22))
    if mode == "interior":
        tip = font.render("\u0412\u044b \u0432\u043d\u0443\u0442\u0440\u0438 \u0437\u0434\u0430\u043d\u0438\u044f \u2014 \u0438\u0434\u0438\u0442\u0435 \u043a \u0432\u044b\u0445\u043e\u0434\u0443, \u0447\u0442\u043e\u0431\u044b \u0432\u044b\u0439\u0442\u0438", True, s.YELLOW)
        screen.blit(tip, (s.WIDTH // 2 - tip.get_width() // 2, s.HEIGHT - 36))


def draw_game_over(screen, bigfont, font, score, elapsed, level):
    overlay = pygame.Surface((s.WIDTH, s.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    title = bigfont.render("\u0418\u0413\u0420\u0410 \u041e\u041a\u041e\u041d\u0427\u0415\u041d\u0410", True, s.RED)
    screen.blit(title, (s.WIDTH // 2 - title.get_width() // 2, s.HEIGHT // 2 - 120))
    lines = [
        f"\u0421\u0447\u0451\u0442: {score}",
        f"\u0414\u043e\u0436\u0438\u043b\u0438: {int(elapsed)} \u0441\u0435\u043a",
        f"\u0423\u0440\u043e\u0432\u0435\u043d\u044c: {level}",
        "",
        "R \u2014 \u0438\u0433\u0440\u0430\u0442\u044c \u0441\u043d\u043e\u0432\u0430     ESC \u2014 \u0432\u044b\u0445\u043e\u0434",
    ]
    for i, line in enumerate(lines):
        surf = font.render(line, True, s.WHITE)
        screen.blit(surf, (s.WIDTH // 2 - surf.get_width() // 2, s.HEIGHT // 2 - 40 + i * 30))


# ------------------------------ game loop ------------------------------ #

def run_game(screen, clock, font, bigfont):
    world = World()
    player = Player(0, 0)
    player.pos = world.find_open_spawn()
    camera = Camera(world.width, world.height)

    bullets = []
    enemies = []
    orbs = []
    spawn_timer = 0.0
    elapsed = 0.0
    score = 0

    mode = "world"
    interior = None
    current_building = None
    enter_cooldown = 0.0

    while True:
        dt = clock.tick(s.FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                if event.key == pygame.K_r and not player.alive:
                    return "restart"

        if player.alive:
            elapsed += dt
            if enter_cooldown > 0:
                enter_cooldown -= dt

            # Determine current context
            if mode == "world":
                obstacles = world.obstacles()
                bounds = world.bounds()
            else:
                obstacles = interior.wall_colliders()
                bounds = interior.bounds()

            # Movement
            player.update_movement(dt, obstacles, bounds)

            # Aim toward mouse
            mx, my = pygame.mouse.get_pos()
            world_mouse = camera.screen_to_world(mx, my)
            aim = world_mouse - player.pos
            if aim.length_squared() > 0:
                player.aim = aim.normalize()

            # Shooting
            player.tick_fire(dt)
            if pygame.mouse.get_pressed()[0] and player.can_fire():
                bullets.append(Bullet(player.pos.x, player.pos.y, player.aim, player.damage))
                player.reset_fire()

            # Update bullets
            for b in bullets:
                b.update(dt, obstacles, bounds)
            bullets = [b for b in bullets if not b.dead]

            if mode == "world":
                # Spawn enemies over time, scaling difficulty
                scale = 1.0 + elapsed / 45.0
                spawn_timer -= dt
                interval = max(0.35, s.SPAWN_INTERVAL - elapsed / 120.0)
                if spawn_timer <= 0 and len(enemies) < s.MAX_ENEMIES:
                    spawn_timer = interval
                    enemies.append(spawn_enemy(player, world, scale))

                # Update enemies
                for e in enemies:
                    e.update(dt, player, obstacles, bounds)
                    if e.rect.colliderect(player.rect) and e.contact_cd <= 0:
                        player.take_damage(e.damage)
                        e.contact_cd = s.ENEMY_CONTACT_COOLDOWN

                # Bullet vs enemy collisions
                for b in bullets:
                    if b.dead:
                        continue
                    for e in enemies:
                        if not e.dead and b.rect.colliderect(e.rect):
                            e.take_damage(b.damage)
                            b.dead = True
                            if e.dead:
                                score += 10
                                orbs.append(XPOrb(e.pos.x, e.pos.y, e.xp))
                            break
                bullets = [b for b in bullets if not b.dead]
                enemies = [e for e in enemies if not e.dead]

                # XP orbs magnet + pickup
                for orb in orbs:
                    to_player = player.pos - orb.pos
                    dist = to_player.length()
                    if dist < s.PLAYER_PICKUP_RADIUS:
                        if dist > 1:
                            orb.pos += to_player.normalize() * 320 * dt
                        if dist < 24:
                            player.add_xp(orb.amount)
                            orb.dead = True
                orbs = [o for o in orbs if not o.dead]

                # Enter a building?
                if enter_cooldown <= 0:
                    for b in world.buildings:
                        if player.rect.colliderect(b.door_trigger):
                            current_building = b
                            interior = b.interior
                            mode = "interior"
                            camera.set_bounds(interior.width, interior.height)
                            player.pos = interior.spawn_point()
                            enter_cooldown = 0.5
                            break
            else:
                # Interior: pick up items, check for exit
                for it in interior.items:
                    if not it.taken and player.rect.colliderect(it.rect):
                        it.taken = True
                        score += 25
                        if it.name == "\u0410\u043f\u0442\u0435\u0447\u043a\u0430":
                            player.hp = min(player.max_hp, player.hp + 35)
                        elif it.name == "\u0415\u0434\u0430":
                            player.hp = min(player.max_hp, player.hp + 15)
                if enter_cooldown <= 0 and player.rect.colliderect(interior.exit_trigger):
                    mode = "world"
                    camera.set_bounds(world.width, world.height)
                    player.pos = current_building.outside_spawn()
                    enter_cooldown = 0.5

        # Camera + render
        camera.follow(player.pos)
        if mode == "world":
            draw_world(screen, camera, world, player, enemies, bullets, orbs)
        else:
            draw_interior(screen, camera, interior, player, font)
        draw_hud(screen, player, font, bigfont, elapsed, len(enemies), score, mode)
        if not player.alive:
            draw_game_over(screen, bigfont, font, score, elapsed, player.level)
        pygame.display.flip()


def main():
    pygame.init()
    pygame.display.set_caption(s.TITLE)
    screen = pygame.display.set_mode((s.WIDTH, s.HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)
    bigfont = pygame.font.SysFont("consolas", 52, bold=True)

    while True:
        result = run_game(screen, clock, font, bigfont)
        if result == "quit":
            break
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
