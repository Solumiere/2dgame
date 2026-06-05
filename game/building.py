"""Buildings with enterable, randomly-generated interiors.

Interior loot includes supplies (health/food/coins) and weapon ammo. Picking
up ammo for a weapon you don't own unlocks that weapon.
"""
import random
import pygame
from .weapon import AMMO_NAMES, WEAPON_ORDER


class Furniture:
    def __init__(self, rect, color, name):
        self.rect = rect
        self.color = color
        self.name = name


class Item:
    """A pickup placed inside a building.
    category: \"loot\" or \"ammo\"; key: loot name or ammo type."""
    def __init__(self, rect, category, key, amount, name):
        self.rect = rect
        self.category = category
        self.key = key
        self.amount = amount
        self.name = name
        self.taken = False


FURNITURE_KINDS = [
    ((120, 90, 60), "\u0421\u0442\u043e\u043b", (80, 130), (50, 75)),
    ((92, 92, 115), "\u041a\u0440\u043e\u0432\u0430\u0442\u044c", (90, 150), (130, 170)),
    ((100, 100, 100), "\u0428\u043a\u0430\u0444", (60, 95), (40, 60)),
    ((125, 110, 80), "\u0421\u0442\u0443\u043b", (32, 44), (32, 44)),
    ((72, 112, 122), "\u041f\u043e\u043b\u043a\u0430", (110, 150), (24, 32)),
    ((140, 120, 95), "\u0422\u0443\u043c\u0431\u0430", (55, 80), (45, 60)),
]

LOOT_DROPS = ["\u0410\u043f\u0442\u0435\u0447\u043a\u0430", "\u0415\u0434\u0430", "\u041c\u043e\u043d\u0435\u0442\u044b", "\u041a\u043b\u044e\u0447"]


class Interior:
    WALL = 26
    DOOR_W = 64

    def __init__(self, bw, bh):
        self.width = max(700, int(bw * 1.9))
        self.height = max(560, int(bh * 1.9))
        self.furniture = []
        self.items = []
        gap_x = self.width // 2 - self.DOOR_W // 2
        self.exit_gap = pygame.Rect(gap_x, self.height - self.WALL, self.DOOR_W, self.WALL)
        self.exit_trigger = pygame.Rect(gap_x, self.height - self.WALL - 6, self.DOOR_W, self.WALL + 6)
        self.generate()

    def generate(self):
        w = self.WALL
        attempts = 0
        target = random.randint(6, 10)
        while len(self.furniture) < target and attempts < 120:
            attempts += 1
            color, name, wr, hr = random.choice(FURNITURE_KINDS)
            fw = random.randint(*wr)
            fh = random.randint(*hr)
            x = random.randint(w + 12, self.width - w - fw - 12)
            y = random.randint(w + 12, self.height - w - fh - 12)
            rect = pygame.Rect(x, y, fw, fh)
            if rect.colliderect(self.exit_gap.inflate(120, 120)):
                continue
            if any(rect.colliderect(f.rect.inflate(24, 24)) for f in self.furniture):
                continue
            self.furniture.append(Furniture(rect, color, name))
        # Loot: mix of supplies and weapon ammo
        for _ in range(random.randint(3, 6)):
            x = random.randint(w + 20, self.width - w - 20)
            y = random.randint(w + 20, self.height - w - 40)
            rect = pygame.Rect(x - 11, y - 11, 22, 22)
            if any(rect.colliderect(f.rect) for f in self.furniture):
                continue
            if rect.colliderect(self.exit_gap.inflate(60, 60)):
                continue
            if random.random() < 0.5:
                atype = random.choice(WEAPON_ORDER[1:])  # smg/shotgun/rifle ammo
                amount = random.randint(8, 20)
                self.items.append(Item(rect, "ammo", atype, amount, AMMO_NAMES[atype]))
            else:
                name = random.choice(LOOT_DROPS)
                self.items.append(Item(rect, "loot", name, 1, name))

    def wall_colliders(self):
        w = self.WALL
        half = self.width // 2
        colliders = [
            pygame.Rect(0, 0, self.width, w),
            pygame.Rect(0, 0, w, self.height),
            pygame.Rect(self.width - w, 0, w, self.height),
            pygame.Rect(0, self.height - w, half - self.DOOR_W // 2, w),
            pygame.Rect(half + self.DOOR_W // 2, self.height - w,
                        self.width - (half + self.DOOR_W // 2), w),
        ]
        colliders.extend(f.rect for f in self.furniture)
        return colliders

    def bounds(self):
        return (self.width, self.height)

    def spawn_point(self):
        return pygame.math.Vector2(self.width // 2, self.height - self.WALL - 40)


class Building:
    def __init__(self, rect):
        self.rect = rect
        self.wall_color = random.choice([(96, 76, 64), (84, 80, 92), (74, 86, 78)])
        self.roof_color = random.choice([(62, 46, 40), (56, 52, 64), (50, 60, 54)])
        door_w = 56
        dx = rect.centerx - door_w // 2
        self.door_rect = pygame.Rect(dx, rect.bottom - 10, door_w, 18)
        self.door_trigger = pygame.Rect(dx, rect.bottom, door_w, 26)
        self._interior = None

    @property
    def interior(self):
        if self._interior is None:
            self._interior = Interior(self.rect.width, self.rect.height)
        return self._interior

    def outside_spawn(self):
        return pygame.math.Vector2(self.door_trigger.centerx, self.door_trigger.bottom + 28)
