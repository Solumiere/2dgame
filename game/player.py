"""Player entity: movement, stats, leveling and shooting.

Note: run speed is intentionally CONSTANT and does not increase on level up.
Leveling boosts max HP and a damage bonus only.
"""
import pygame
from . import settings as s
from .physics import move_with_collision
from .inventory import Inventory


class Player:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.size = s.PLAYER_SIZE
        self.speed = s.PLAYER_BASE_SPEED  # constant
        self.max_hp = s.PLAYER_BASE_HP
        self.hp = self.max_hp
        self.damage_bonus = 0
        self.fire_cooldown = 0.0
        self.level = 1
        self.xp = 0
        self.xp_to_next = 5
        self.alive = True
        self.aim = pygame.math.Vector2(1, 0)
        self.inventory = Inventory()

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x - self.size / 2),
                           int(self.pos.y - self.size / 2),
                           self.size, self.size)

    def update_movement(self, dt, obstacles, bounds):
        keys = pygame.key.get_pressed()
        move = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move.x += 1
        if move.length_squared() > 0:
            move = move.normalize()
        move_with_collision(self.pos, self.size,
                            move.x * self.speed * dt,
                            move.y * self.speed * dt,
                            obstacles)
        self.pos.x = max(self.size / 2, min(self.pos.x, bounds[0] - self.size / 2))
        self.pos.y = max(self.size / 2, min(self.pos.y, bounds[1] - self.size / 2))

    def can_fire(self):
        return self.fire_cooldown <= 0

    def reset_fire(self, rate):
        self.fire_cooldown = rate

    def tick_fire(self, dt):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.35) + 3
            self._level_up()

    def _level_up(self):
        # Boost HP and damage only -- NOT speed.
        self.max_hp += 15
        self.hp = min(self.max_hp, self.hp + 40)
        self.damage_bonus += 4

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
