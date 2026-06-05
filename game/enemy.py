"""Enemy entities: zombies and other creatures that chase the player."""
import pygame
from . import settings as s
from .physics import move_with_collision

# type -> stats
ENEMY_TYPES = {
    "zombie": {"color": (96, 150, 84), "hp": 42, "speed": 82, "damage": 12, "xp": 2, "size": 26},
    "runner": {"color": (180, 150, 70), "hp": 26, "speed": 158, "damage": 8, "xp": 3, "size": 22},
    "brute":  {"color": (150, 80, 80), "hp": 130, "speed": 54, "damage": 26, "xp": 7, "size": 40},
}


class Enemy:
    def __init__(self, x, y, etype, scale=1.0):
        data = ENEMY_TYPES[etype]
        self.etype = etype
        self.pos = pygame.math.Vector2(x, y)
        self.max_hp = data["hp"] * scale
        self.hp = self.max_hp
        self.speed = data["speed"]
        self.damage = data["damage"]
        self.xp = data["xp"]
        self.size = data["size"]
        self.color = data["color"]
        self.dead = False
        self.contact_cd = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x - self.size / 2),
                           int(self.pos.y - self.size / 2),
                           self.size, self.size)

    def update(self, dt, target, obstacles, bounds):
        direction = target.pos - self.pos
        if direction.length_squared() > 1:
            direction = direction.normalize()
        else:
            direction = pygame.math.Vector2(0, 0)
        move_with_collision(self.pos, self.size,
                            direction.x * self.speed * dt,
                            direction.y * self.speed * dt,
                            obstacles)
        self.pos.x = max(self.size / 2, min(self.pos.x, bounds[0] - self.size / 2))
        self.pos.y = max(self.size / 2, min(self.pos.y, bounds[1] - self.size / 2))
        if self.contact_cd > 0:
            self.contact_cd -= dt

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.dead = True
