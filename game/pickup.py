"""Ground pickups dropped by enemies or found in the world."""
import pygame


class Pickup:
    SIZE = 22

    def __init__(self, x, y, category, key, amount, name):
        self.pos = pygame.math.Vector2(x, y)
        self.category = category   # "ammo" or "loot"
        self.key = key             # ammo type or loot name
        self.amount = amount
        self.name = name
        self.dead = False

    @property
    def rect(self):
        h = self.SIZE
        return pygame.Rect(int(self.pos.x - h / 2), int(self.pos.y - h / 2), h, h)
