"""Enemy entities: melee zombies and ranged soldiers."""
import random
import pygame
from .physics import move_with_collision

# type -> stats. `ranged` enemies keep distance and shoot bullets.
ENEMY_TYPES = {
    "zombie":  {"color": (96, 150, 84),  "hp": 42,  "speed": 82,  "damage": 12, "xp": 2, "size": 28},
    "runner":  {"color": (180, 150, 70), "hp": 26,  "speed": 158, "damage": 8,  "xp": 3, "size": 26},
    "brute":   {"color": (150, 80, 80),  "hp": 130, "speed": 54,  "damage": 26, "xp": 7, "size": 44},
    "soldier": {"color": (115, 130, 158), "hp": 58, "speed": 78,  "damage": 6,  "xp": 5, "size": 30,
                 "ranged": True, "range": 360, "shoot_cd": 1.4, "bullet_damage": 11, "bullet_speed": 540},
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
        self.ranged = data.get("ranged", False)
        self.range = data.get("range", 0)
        self.shoot_cd = data.get("shoot_cd", 1.0)
        self.bullet_damage = data.get("bullet_damage", 0)
        self.bullet_speed = data.get("bullet_speed", 520)
        self.shoot_timer = random.uniform(0.4, self.shoot_cd)
        self.dead = False
        self.contact_cd = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x - self.size / 2),
                           int(self.pos.y - self.size / 2),
                           self.size, self.size)

    def update(self, dt, target, obstacles, bounds):
        to_t = target.pos - self.pos
        dist = to_t.length()
        direction = pygame.math.Vector2(0, 0)
        if self.ranged:
            # Approach until in range, then hold; back off if too close.
            if dist > self.range * 0.85 and dist > 1:
                direction = to_t.normalize()
            elif dist < self.range * 0.5 and dist > 1:
                direction = -to_t.normalize()
        else:
            if dist > 1:
                direction = to_t.normalize()
        move_with_collision(self.pos, self.size,
                            direction.x * self.speed * dt,
                            direction.y * self.speed * dt,
                            obstacles)
        self.pos.x = max(self.size / 2, min(self.pos.x, bounds[0] - self.size / 2))
        self.pos.y = max(self.size / 2, min(self.pos.y, bounds[1] - self.size / 2))
        if self.contact_cd > 0:
            self.contact_cd -= dt
        if self.shoot_timer > 0:
            self.shoot_timer -= dt

    def try_shoot(self, target):
        """Return a normalized direction Vector2 if the enemy fires this frame."""
        if not self.ranged or self.shoot_timer > 0:
            return None
        to_t = target.pos - self.pos
        if to_t.length_squared() > 0 and to_t.length() <= self.range:
            self.shoot_timer = self.shoot_cd
            return to_t.normalize()
        return None

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.dead = True
