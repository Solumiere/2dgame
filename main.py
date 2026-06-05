"""2D top-down zombie survival game.

Run with:  python main.py
Requires:  pygame  (pip install -r requirements.txt)
"""
import math
import random
import sys

import pygame

from game import settings as s
from game.assets import Sprites
from game.camera import Camera
from game.player import Player
from game.bullet import Bullet
from game.enemy import Enemy
from game.world import World
from game.pickup import Pickup
from game.weapon import WEAPONS, WEAPON_ORDER, AMMO_NAMES

# Drop tables: harder enemies drop more ammo and loot.
DROP_TIERS = {
    "zombie":  {"ammo_chance": 0.25, "ammo": (4, 8),   "loot_chance": 0.12},
    "runner":  {"ammo_chance": 0.30, "ammo": (4, 10),  "loot_chance": 0.12},
    "soldier": {"ammo_chance": 0.65, "ammo": (8, 16),  "loot_chance": 0.30},
    "brute":   {"ammo_chance": 0.55, "ammo": (10, 20), "loot_chance": 0.45},
}
LOOT_DROPS = ["\u0410\u043f\u0442\u0435\u0447\u043a\u0430", "\u0415\u0434\u0430", "\u041c\u043e\u043d\u0435\u0442\u044b"]


class XPOrb:
    def __init__(self, x, y, amount):
        self.pos = pygame.math.Vector2(x, y)
        self.amount = amount
        self.dead = False


def spawn_enemy(player, world, scale):
    angle = random.uniform(0, 2 * math.pi)
    radius = random.uniform(520, 780)
    x = max(40, min(player.pos.x + math.cos(angle) * radius, world.width - 40))
    y = max(40, min(player.pos.y + math.sin(angle) * radius, world.height - 40))
    r = random.random()
    if scale > 1.8 and r < 0.22:
        etype = "soldier"
    elif scale > 2.2 and r < 0.33:
        etype = "brute"
    elif r < 0.30:
        etype = "runner"
    else:
        etype = "zombie"
    hp_scale = 1.0 + (scale - 1.0) * 0.6
    return Enemy(x, y, etype, scale=hp_scale)


def fire_weapon(player, bullets):
    wkey = player.inventory.current_weapon()
    w = WEAPONS[wkey]
    base = math.atan2(player.aim.y, player.aim.x)
    for _ in range(w["pellets"]):
        a = base + math.radians(random.uniform(-w["spread"], w["spread"]))
        d = pygame.math.Vector2(math.cos(a), math.sin(a))
        dmg = w["damage"] + player.damage_bonus
        bullets.append(Bullet(player.pos.x, player.pos.y, d, dmg, speed=w["bullet_speed"]))


def drop_loot(e, elapsed, orbs, pickups):
    diff = min(1.8, 1.0 + elapsed / 110.0)
    orbs.append(XPOrb(e.pos.x, e.pos.y, int((e.xp + elapsed / 30.0) * diff)))
    tier = DROP_TIERS.get(e.etype, DROP_TIERS["zombie"])
    if random.random() < tier["ammo_chance"] * diff:
        atype = random.choice(WEAPON_ORDER[1:])
        amt = int(random.randint(*tier["ammo"]) * diff)
        pickups.append(Pickup(e.pos.x, e.pos.y, "ammo", atype, amt, AMMO_NAMES[atype]))
    if random.random() < tier["loot_chance"] * diff:
        name = random.choice(LOOT_DROPS)
        pickups.append(Pickup(e.pos.x + random.randint(-14, 14),
                              e.pos.y + random.randint(-14, 14), "loot", name, 1, name))


def nearest_car(world, pos, radius):
    best, best_d = None, radius
    for c in world.cars:
        d = (c.pos - pos).length()
        if d < best_d:
            best, best_d = c, d
    return best


def car_exit_spot(car, world):
    for dx, dy in [(car.w / 2 + 34, 0), (-car.w / 2 - 34, 0),
                   (0, car.h / 2 + 34), (0, -car.h / 2 - 34)]:
        p = pygame.math.Vector2(car.pos.x + dx, car.pos.y + dy)
        rect = pygame.Rect(int(p.x - 20), int(p.y - 20), 40, 40)
        if not any(rect.colliderect(o) for o in world.obstacles(exclude_car=car)):
            return p
    return pygame.math.Vector2(car.pos.x, car.pos.y + car.h)


# --------------------------- drawing helpers --------------------------- #

def draw_grass(screen, camera):
    ts = s.TILE_SIZE
    start_x = int(camera.offset.x // ts)
    start_y = int(camera.offset.y // ts)
    for i in range(s.WIDTH // ts + 2):
        for j in range(s.HEIGHT // ts + 2):
            tx, ty = start_x + i, start_y + j
            color = s.GRASS if (tx + ty) % 2 == 0 else s.GRASS_ALT
            screen.fill(color, (int(tx * ts - camera.offset.x),
                                int(ty * ts - camera.offset.y), ts, ts))


def blit_centered(screen, surf, screen_pos):
    rect = surf.get_rect(center=screen_pos)
    screen.blit(surf, rect)


def draw_car(screen, camera, car, font, driving=False):
    if car.base_surf is None:
        surf = pygame.Surface((car.w, car.h), pygame.SRCALPHA)
        pygame.draw.rect(surf, car.color, (0, 0, car.w, car.h), border_radius=9)
        pygame.draw.rect(surf, (20, 20, 25), (0, 0, car.w, car.h), 2, border_radius=9)
        pygame.draw.rect(surf, (150, 190, 215), (car.w * 0.58, car.h * 0.2, car.w * 0.16, car.h * 0.6), border_radius=3)
        pygame.draw.rect(surf, (120, 160, 185), (car.w * 0.28, car.h * 0.22, car.w * 0.12, car.h * 0.56), border_radius=3)
        pygame.draw.rect(surf, (30, 30, 35), (car.w * 0.08, -3, car.w * 0.16, 5), border_radius=2)
        pygame.draw.rect(surf, (30, 30, 35), (car.w * 0.08, car.h - 2, car.w * 0.16, 5), border_radius=2)
        car.base_surf = surf
    rot = pygame.transform.rotate(car.base_surf, -math.degrees(car.heading))
    blit_centered(screen, rot, camera.world_to_screen(car.pos.x, car.pos.y))
    if not driving:
        sx, sy = camera.world_to_screen(car.pos.x, car.pos.y - car.h / 2 - 10)
        col = s.GREEN if car.fuel > 0 else s.RED
        pygame.draw.circle(screen, col, (sx, sy), 4)


def draw_world(screen, camera, world, player, enemies, bullets, ebullets, orbs, pickups, sprites, driving, vehicle):
    draw_grass(screen, camera)
    for car in world.cars:
        if driving and car is vehicle:
            continue
        draw_car(screen, camera, car, None)
    for p in pickups:
        name = "ammo" if p.category == "ammo" else "item"
        blit_centered(screen, sprites.get(name), camera.world_to_screen(p.pos.x, p.pos.y))
    for orb in orbs:
        blit_centered(screen, sprites.get("orb"), camera.world_to_screen(orb.pos.x, orb.pos.y))
    for b in bullets:
        sx, sy = camera.world_to_screen(b.pos.x, b.pos.y)
        pygame.draw.circle(screen, b.color, (sx, sy), b.radius)
    for b in ebullets:
        sx, sy = camera.world_to_screen(b.pos.x, b.pos.y)
        pygame.draw.circle(screen, b.color, (sx, sy), b.radius + 1)
    for e in enemies:
        blit_centered(screen, sprites.get(e.etype), camera.world_to_screen(e.pos.x, e.pos.y))
        if e.hp < e.max_hp:
            sx, sy = camera.world_to_screen(e.pos.x, e.pos.y)
            half = e.size // 2
            ratio = max(0.0, e.hp / e.max_hp)
            pygame.draw.rect(screen, (60, 0, 0), (sx - half, sy - half - 9, e.size, 4))
            pygame.draw.rect(screen, s.RED, (sx - half, sy - half - 9, int(e.size * ratio), 4))
    # Buildings hide their interiors from outside
    for b in world.buildings:
        sx, sy = camera.world_to_screen(b.rect.x, b.rect.y)
        pygame.draw.rect(screen, b.wall_color, (sx, sy, b.rect.w, b.rect.h))
        pygame.draw.rect(screen, b.roof_color, (sx, sy, b.rect.w, b.rect.h), 8)
        dsx, dsy = camera.world_to_screen(b.door_rect.x, b.door_rect.y)
        pygame.draw.rect(screen, (30, 22, 18), (dsx, dsy, b.door_rect.w, b.door_rect.h))
    for t in world.trees:
        blit_centered(screen, sprites.get("tree"), camera.world_to_screen(t.pos.x, t.pos.y - 8))
    if driving:
        draw_car(screen, camera, vehicle, None, driving=True)
    else:
        draw_player(screen, camera, player, sprites)


def draw_player(screen, camera, player, sprites):
    sx, sy = camera.world_to_screen(player.pos.x, player.pos.y)
    angle = -math.degrees(math.atan2(player.aim.y, player.aim.x))
    rot = pygame.transform.rotate(sprites.get("player"), angle)
    blit_centered(screen, rot, (sx, sy))


def draw_interior(screen, camera, interior, player, sprites, font):
    screen.fill(s.DARK)
    ox, oy = camera.offset.x, camera.offset.y
    pygame.draw.rect(screen, s.FLOOR, (int(-ox), int(-oy), interior.width, interior.height))
    for gx in range(0, interior.width, 64):
        pygame.draw.line(screen, (58, 48, 42), (int(gx - ox), int(-oy)), (int(gx - ox), int(interior.height - oy)))
    for gy in range(0, interior.height, 64):
        pygame.draw.line(screen, (58, 48, 42), (int(-ox), int(gy - oy)), (int(interior.width - ox), int(gy - oy)))
    for wall in interior.wall_colliders()[:5]:
        pygame.draw.rect(screen, s.WALL, (int(wall.x - ox), int(wall.y - oy), wall.w, wall.h))
    eg = interior.exit_gap
    pygame.draw.rect(screen, (40, 90, 50), (int(eg.x - ox), int(eg.y - oy), eg.w, eg.h))
    screen.blit(font.render("\u0432\u044b\u0445\u043e\u0434", True, s.WHITE), (int(eg.centerx - ox - 18), int(eg.y - oy - 22)))
    for f in interior.furniture:
        pygame.draw.rect(screen, f.color, (int(f.rect.x - ox), int(f.rect.y - oy), f.rect.w, f.rect.h), border_radius=4)
        pygame.draw.rect(screen, (20, 18, 16), (int(f.rect.x - ox), int(f.rect.y - oy), f.rect.w, f.rect.h), 2, border_radius=4)
        screen.blit(font.render(f.name, True, (230, 225, 215)), (int(f.rect.x - ox), int(f.rect.y - oy - 16)))
    for it in interior.items:
        if it.taken:
            continue
        name = "ammo" if it.category == "ammo" else "item"
        blit_centered(screen, sprites.get(name), (int(it.rect.centerx - ox), int(it.rect.centery - oy)))
        screen.blit(font.render(it.name, True, s.WHITE), (int(it.rect.x - ox - 10), int(it.rect.y - oy - 16)))
    draw_player(screen, camera, player, sprites)


def draw_hud(screen, player, font, elapsed, enemy_count, score, mode):
    bar_w = 260
    pygame.draw.rect(screen, (50, 0, 0), (20, 20, bar_w, 22), border_radius=4)
    pygame.draw.rect(screen, s.RED, (20, 20, int(bar_w * max(0.0, player.hp / player.max_hp)), 22), border_radius=4)
    pygame.draw.rect(screen, s.WHITE, (20, 20, bar_w, 22), 2, border_radius=4)
    screen.blit(font.render(f"HP {int(player.hp)}/{int(player.max_hp)}", True, s.WHITE), (26, 22))
    pygame.draw.rect(screen, (10, 30, 50), (20, 50, bar_w, 14), border_radius=4)
    xp_ratio = player.xp / player.xp_to_next if player.xp_to_next else 0
    pygame.draw.rect(screen, s.BLUE, (20, 50, int(bar_w * xp_ratio), 14), border_radius=4)
    pygame.draw.rect(screen, s.WHITE, (20, 50, bar_w, 14), 1, border_radius=4)
    stats = [f"\u0423\u0440\u043e\u0432\u0435\u043d\u044c: {player.level}",
             f"\u0411\u043e\u043d\u0443\u0441 \u0443\u0440\u043e\u043d\u0430: +{player.damage_bonus}"]
    for i, line in enumerate(stats):
        screen.blit(font.render(line, True, s.WHITE), (20, 72 + i * 20))
    info = [f"\u0421\u0447\u0451\u0442: {score}", f"\u0412\u0440\u0435\u043c\u044f: {int(elapsed)}\u0441", f"\u0412\u0440\u0430\u0433\u043e\u0432: {enemy_count}"]
    for i, line in enumerate(info):
        surf = font.render(line, True, s.WHITE)
        screen.blit(surf, (s.WIDTH - surf.get_width() - 20, 20 + i * 22))
    loot = player.inventory.loot
    screen.blit(font.render(f"\U0001f4b0 {loot.get(chr(1052)+chr(1086)+chr(1085)+chr(1077)+chr(1090)+chr(1099), 0)}  "
                            f"\u0410\u043f\u0442\u0435\u0447\u043a\u0438: {loot.get(chr(1040)+chr(1087)+chr(1090)+chr(1077)+chr(1095)+chr(1082)+chr(1072), 0)}",
                            True, s.YELLOW), (s.WIDTH - 200, 90))


def draw_weapon_bar(screen, inv, font):
    x, y = 20, s.HEIGHT - 40
    for i, wkey in enumerate(inv.weapons):
        w = WEAPONS[wkey]
        sel = (i == inv.current)
        box = pygame.Rect(x, y, 168, 26)
        pygame.draw.rect(screen, (70, 90, 120) if sel else (40, 40, 50), box, border_radius=5)
        pygame.draw.rect(screen, s.WHITE if sel else (90, 90, 100), box, 2, border_radius=5)
        ammo = "\u221e" if w.get("infinite") else str(inv.ammo.get(wkey, 0))
        screen.blit(font.render(f"{i+1}.{w['name']} [{ammo}]", True, s.WHITE), (x + 6, y + 5))
        x += 178


def draw_speedometer(screen, car, font, bigfont):
    cx, cy = s.WIDTH // 2, s.HEIGHT - 70
    panel = pygame.Rect(cx - 110, cy - 30, 220, 70)
    pygame.draw.rect(screen, (20, 20, 28), panel, border_radius=8)
    pygame.draw.rect(screen, s.WHITE, panel, 2, border_radius=8)
    spd = bigfont.render(f"{car.speed_kmh()}", True, s.WHITE)
    screen.blit(spd, (cx - spd.get_width() // 2 - 30, cy - 26))
    screen.blit(font.render("\u043a\u043c/\u0447", True, s.GRAY), (cx + 14, cy - 6))
    fb = pygame.Rect(cx - 100, cy + 18, 200, 12)
    pygame.draw.rect(screen, (50, 40, 0), fb, border_radius=3)
    pygame.draw.rect(screen, s.YELLOW if car.fuel > 0 else s.RED,
                     (fb.x, fb.y, int(fb.w * car.fuel / car.max_fuel), fb.h), border_radius=3)
    if car.fuel <= 0:
        t = font.render("\u041d\u0415\u0422 \u0411\u0415\u041d\u0417\u0418\u041d\u0410", True, s.RED)
        screen.blit(t, (cx - t.get_width() // 2, cy + 16))
    screen.blit(font.render("E \u2014 \u0432\u044b\u0439\u0442\u0438", True, s.WHITE), (cx + 116, cy - 4))


def draw_inventory_panel(screen, inv, font, bigfont):
    panel = pygame.Rect(s.WIDTH // 2 - 220, s.HEIGHT // 2 - 180, 440, 360)
    overlay = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
    overlay.fill((10, 10, 16, 235))
    screen.blit(overlay, panel.topleft)
    pygame.draw.rect(screen, s.WHITE, panel, 2, border_radius=8)
    title = bigfont.render("\u0418\u043d\u0432\u0435\u043d\u0442\u0430\u0440\u044c", True, s.WHITE)
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))
    y = panel.y + 70
    screen.blit(font.render("\u041e\u0440\u0443\u0436\u0438\u0435 \u0438 \u043f\u0430\u0442\u0440\u043e\u043d\u044b:", True, s.YELLOW), (panel.x + 20, y))
    y += 26
    for wkey in inv.weapons:
        w = WEAPONS[wkey]
        ammo = "\u221e" if w.get("infinite") else str(inv.ammo.get(wkey, 0))
        screen.blit(font.render(f"- {w['name']}: {ammo}", True, s.WHITE), (panel.x + 32, y))
        y += 22
    y += 10
    screen.blit(font.render("\u041b\u0443\u0442:", True, s.YELLOW), (panel.x + 20, y))
    y += 26
    for name, count in inv.loot.items():
        screen.blit(font.render(f"- {name}: {count}", True, s.WHITE), (panel.x + 32, y))
        y += 22
    screen.blit(font.render("I \u2014 \u0437\u0430\u043a\u0440\u044b\u0442\u044c", True, s.GRAY),
                (panel.centerx - 40, panel.bottom - 28))


def draw_game_over(screen, bigfont, font, score, elapsed, level):
    overlay = pygame.Surface((s.WIDTH, s.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    title = bigfont.render("\u0418\u0413\u0420\u0410 \u041e\u041a\u041e\u041d\u0427\u0415\u041d\u0410", True, s.RED)
    screen.blit(title, (s.WIDTH // 2 - title.get_width() // 2, s.HEIGHT // 2 - 120))
    lines = [f"\u0421\u0447\u0451\u0442: {score}", f"\u0414\u043e\u0436\u0438\u043b\u0438: {int(elapsed)} \u0441\u0435\u043a",
             f"\u0423\u0440\u043e\u0432\u0435\u043d\u044c: {level}", "",
             "R \u2014 \u0437\u0430\u043d\u043e\u0432\u043e     ESC \u2014 \u0432\u044b\u0445\u043e\u0434"]
    for i, line in enumerate(lines):
        surf = font.render(line, True, s.WHITE)
        screen.blit(surf, (s.WIDTH // 2 - surf.get_width() // 2, s.HEIGHT // 2 - 40 + i * 30))


# ------------------------------ game loop ------------------------------ #

def run_game(screen, clock, sprites, font, bigfont):
    world = World()
    player = Player(0, 0)
    player.pos = world.find_open_spawn()
    camera = Camera(world.width, world.height)
    inv = player.inventory

    bullets, ebullets, enemies, orbs, pickups = [], [], [], [], []
    spawn_timer = 0.0
    elapsed = 0.0
    score = 0

    mode = "world"
    interior = None
    current_building = None
    enter_cooldown = 0.0
    driving = False
    vehicle = None
    show_inv = False

    while True:
        dt = min(clock.tick(s.FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                if event.key == pygame.K_r and not player.alive:
                    return "restart"
                if event.key == pygame.K_i:
                    show_inv = not show_inv
                if pygame.K_1 <= event.key <= pygame.K_9:
                    inv.select(event.key - pygame.K_1)
                if event.key == pygame.K_e and player.alive and mode == "world":
                    if driving:
                        driving = False
                        player.pos = car_exit_spot(vehicle, world)
                        vehicle = None
                        enter_cooldown = 0.3
                    else:
                        car = nearest_car(world, player.pos, s.ENTER_RADIUS)
                        if car is not None:
                            driving = True
                            vehicle = car
            if event.type == pygame.MOUSEWHEEL:
                inv.cycle(-1 if event.y > 0 else 1)

        if player.alive:
            elapsed += dt
            if enter_cooldown > 0:
                enter_cooldown -= dt
            scale = 1.0 + elapsed / 45.0

            if mode == "world":
                car_obstacles = world.obstacles(exclude_car=vehicle) if driving else world.obstacles()
                bounds = world.bounds()
                if driving:
                    keys = pygame.key.get_pressed()
                    accel = pygame.math.Vector2(0, 0)
                    if keys[pygame.K_w] or keys[pygame.K_UP]:
                        accel.y -= 1
                    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                        accel.y += 1
                    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                        accel.x -= 1
                    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                        accel.x += 1
                    vehicle.drive(dt, accel, car_obstacles, bounds)
                    player.pos.update(vehicle.pos)
                else:
                    player.update_movement(dt, car_obstacles, bounds)
                obstacles = car_obstacles
            else:
                obstacles = interior.wall_colliders()
                bounds = interior.bounds()
                player.update_movement(dt, obstacles, bounds)

            # Aim
            mx, my = pygame.mouse.get_pos()
            aim = camera.screen_to_world(mx, my) - player.pos
            if aim.length_squared() > 0:
                player.aim = aim.normalize()

            # Shooting (allowed on foot and while driving)
            player.tick_fire(dt)
            if pygame.mouse.get_pressed()[0] and player.can_fire():
                wkey = inv.current_weapon()
                if inv.has_ammo(wkey):
                    fire_weapon(player, bullets)
                    inv.consume(wkey)
                    player.reset_fire(WEAPONS[wkey]["fire_rate"])
                else:
                    inv.select_pistol()

            for b in bullets:
                b.update(dt, obstacles, bounds)
            bullets = [b for b in bullets if not b.dead]
            for b in ebullets:
                b.update(dt, obstacles, bounds)
            ebullets = [b for b in ebullets if not b.dead]

            hit_rect = vehicle.rect if driving else player.rect

            if mode == "world":
                spawn_timer -= dt
                interval = max(0.35, s.SPAWN_INTERVAL - elapsed / 120.0)
                if spawn_timer <= 0 and len(enemies) < s.MAX_ENEMIES:
                    spawn_timer = interval
                    enemies.append(spawn_enemy(player, world, scale))

                for e in enemies:
                    e.update(dt, player, obstacles, bounds)
                    shoot_dir = e.try_shoot(player)
                    if shoot_dir is not None:
                        ebullets.append(Bullet(e.pos.x, e.pos.y, shoot_dir, e.bullet_damage,
                                               speed=e.bullet_speed, friendly=False, color=s.ORANGE))
                    if e.rect.colliderect(hit_rect):
                        if driving:
                            sp = vehicle.vel.length()
                            if sp > 90:
                                e.take_damage(sp * dt * 0.5 + 6)
                            if e.contact_cd <= 0:
                                player.take_damage(e.damage * 0.4)
                                e.contact_cd = s.ENEMY_CONTACT_COOLDOWN
                        elif e.contact_cd <= 0:
                            player.take_damage(e.damage)
                            e.contact_cd = s.ENEMY_CONTACT_COOLDOWN

                # player bullets vs enemies
                for b in bullets:
                    if b.dead:
                        continue
                    for e in enemies:
                        if not e.dead and b.rect.colliderect(e.rect):
                            e.take_damage(b.damage)
                            b.dead = True
                            if e.dead:
                                score += 10
                                drop_loot(e, elapsed, orbs, pickups)
                            break
                bullets = [b for b in bullets if not b.dead]
                enemies = [e for e in enemies if not e.dead]

                # enemy bullets vs player
                for b in ebullets:
                    if not b.dead and b.rect.colliderect(hit_rect):
                        player.take_damage(b.damage)
                        b.dead = True
                ebullets = [b for b in ebullets if not b.dead]

                # XP orbs magnet + pickup
                for orb in orbs:
                    to_p = player.pos - orb.pos
                    dist = to_p.length()
                    if dist < s.PLAYER_PICKUP_RADIUS:
                        if dist > 1:
                            orb.pos += to_p.normalize() * 340 * dt
                        if dist < 26:
                            player.add_xp(orb.amount)
                            orb.dead = True
                orbs = [o for o in orbs if not o.dead]

                # ground pickups
                for p in pickups:
                    if hit_rect.colliderect(p.rect):
                        if p.category == "ammo":
                            inv.add_ammo(p.key, p.amount)
                        else:
                            inv.add_loot(p.key, p.amount)
                            if p.key == chr(1040)+chr(1087)+chr(1090)+chr(1077)+chr(1095)+chr(1082)+chr(1072):
                                player.hp = min(player.max_hp, player.hp + 35)
                            elif p.key == chr(1045)+chr(1076)+chr(1072):
                                player.hp = min(player.max_hp, player.hp + 15)
                        score += 5
                        p.dead = True
                pickups = [p for p in pickups if not p.dead]

                # enter building (only on foot)
                if enter_cooldown <= 0 and not driving:
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
                # interior: items + exit
                for it in interior.items:
                    if not it.taken and player.rect.colliderect(it.rect):
                        it.taken = True
                        score += 15
                        if it.category == "ammo":
                            inv.add_ammo(it.key, it.amount)
                        else:
                            inv.add_loot(it.key, it.amount)
                            if it.key == chr(1040)+chr(1087)+chr(1090)+chr(1077)+chr(1095)+chr(1082)+chr(1072):
                                player.hp = min(player.max_hp, player.hp + 35)
                            elif it.key == chr(1045)+chr(1076)+chr(1072):
                                player.hp = min(player.max_hp, player.hp + 15)
                if enter_cooldown <= 0 and player.rect.colliderect(interior.exit_trigger):
                    mode = "world"
                    camera.set_bounds(world.width, world.height)
                    player.pos = current_building.outside_spawn()
                    enter_cooldown = 0.5

        camera.follow(player.pos)
        if mode == "world":
            draw_world(screen, camera, world, player, enemies, bullets, ebullets,
                       orbs, pickups, sprites, driving, vehicle)
        else:
            draw_interior(screen, camera, interior, player, sprites, font)
        draw_hud(screen, player, font, elapsed, len(enemies), score, mode)
        draw_weapon_bar(screen, inv, font)
        if driving:
            draw_speedometer(screen, vehicle, font, bigfont)
        elif mode == "world" and player.alive:
            near = nearest_car(world, player.pos, s.ENTER_RADIUS)
            if near is not None:
                tip = font.render("E \u2014 \u0441\u0435\u0441\u0442\u044c \u0432 \u043c\u0430\u0448\u0438\u043d\u0443", True, s.YELLOW)
                sx, sy = camera.world_to_screen(near.pos.x, near.pos.y)
                screen.blit(tip, (sx - tip.get_width() // 2, sy - near.h))
        if show_inv:
            draw_inventory_panel(screen, inv, font, bigfont)
        if not player.alive:
            draw_game_over(screen, bigfont, font, score, elapsed, player.level)
        pygame.display.flip()


def main():
    pygame.init()
    pygame.display.set_caption(s.TITLE)
    screen = pygame.display.set_mode((s.WIDTH, s.HEIGHT))
    clock = pygame.time.Clock()
    sprites = Sprites()
    font = pygame.font.SysFont("consolas", 16)
    bigfont = pygame.font.SysFont("consolas", 40, bold=True)
    while True:
        if run_game(screen, clock, sprites, font, bigfont) == "quit":
            break
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
