"""Projectiles. Used by the player (friendly) and by ranged enemies."""
import pygame
from . import settings as s


class Bullet:
    def __init__(self, x, y, direction, damage, speed=720, friendly=True, color=None):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = direction * speed
        self.damage = damage
        self.life = s.BULLET_LIFETIME
        self.radius = s.BULLET_RADIUS
        self.friendly = friendly
        self.color = color or (s.WHITE if friendly else s.ORANGE)
        self.dead = False

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x - self.radius), int(self.pos.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def update(self, dt, obstacles, bounds):
        self.pos += self.vel * dt
        self.life -= dt
        if self.life <= 0:
            self.dead = True
            return
        if self.pos.x < 0 or self.pos.y < 0 or self.pos.x > bounds[0] or self.pos.y > bounds[1]:
            self.dead = True
            return
        r = self.rect
        for ob in obstacles:
            if r.colliderect(ob):
                self.dead = True
                return
