"""Sprite graphics for the game.

Sprites are generated procedurally with pygame so the game ships with real
\"pictures\" (Surfaces) out of the box. If a matching PNG exists in an
`assets/` folder next to the project, it is loaded instead -- so you can drop
in your own art (e.g. assets/player.png) without changing code.

Must be created AFTER pygame.display.set_mode().
"""
import math
import os
import pygame
from . import settings as s

ASSET_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


class Sprites:
    def __init__(self):
        self.cache = {}
        self._build()

    def get(self, name):
        return self.cache.get(name)

    # ---- helpers ----
    def _surf(self, w, h):
        return pygame.Surface((w, h), pygame.SRCALPHA)

    def _maybe_load(self, name, size):
        path = os.path.join(ASSET_DIR, name + ".png")
        if os.path.isfile(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, size)
            except Exception:
                return None
        return None

    def _build(self):
        self.cache["player"] = self._maybe_load("player", (40, 40)) or self._player()
        self.cache["zombie"] = self._maybe_load("zombie", (30, 30)) or self._zombie((96, 150, 84), 30)
        self.cache["runner"] = self._maybe_load("runner", (26, 26)) or self._zombie((180, 150, 70), 26)
        self.cache["brute"] = self._maybe_load("brute", (46, 46)) or self._zombie((150, 80, 80), 46)
        self.cache["soldier"] = self._maybe_load("soldier", (32, 32)) or self._soldier()
        self.cache["tree"] = self._maybe_load("tree", (74, 74)) or self._tree()
        self.cache["item"] = self._maybe_load("item", (22, 22)) or self._item()
        self.cache["ammo"] = self._maybe_load("ammo", (22, 22)) or self._ammo()
        self.cache["orb"] = self._maybe_load("orb", (14, 14)) or self._orb()

    # ---- makers ----
    def _player(self):
        size = 40
        surf = self._surf(size, size)
        c = size // 2
        pygame.draw.circle(surf, (40, 60, 90), (c - 3, c), 14)
        pygame.draw.circle(surf, s.BLUE, (c, c), 13)
        pygame.draw.circle(surf, (20, 30, 45), (c, c), 13, 2)
        pygame.draw.circle(surf, (225, 200, 170), (c + 3, c), 6)
        pygame.draw.rect(surf, (45, 45, 50), (c + 8, c - 3, 15, 6), border_radius=2)
        return surf

    def _zombie(self, color, size):
        surf = self._surf(size, size)
        c = size // 2
        dark = tuple(max(0, x - 45) for x in color)
        pygame.draw.circle(surf, color, (c, c), c - 2)
        pygame.draw.circle(surf, dark, (c, c), c - 2, 2)
        pygame.draw.circle(surf, (40, 70, 40), (c - 5, c + 3), 3)
        pygame.draw.circle(surf, (20, 20, 20), (c - 4, c - 3), 2)
        pygame.draw.circle(surf, (20, 20, 20), (c + 4, c - 3), 2)
        return surf

    def _soldier(self):
        size = 32
        surf = self._surf(size, size)
        c = size // 2
        pygame.draw.circle(surf, (115, 130, 158), (c, c), c - 3)
        pygame.draw.circle(surf, (40, 55, 75), (c, c), c - 3, 2)
        pygame.draw.arc(surf, (60, 75, 55), (c - 10, c - 12, 20, 18), 0, math.pi, 5)
        pygame.draw.rect(surf, (35, 35, 40), (c + 4, c - 2, 17, 4))
        return surf

    def _tree(self):
        size = 74
        surf = self._surf(size, size)
        c = size // 2
        pygame.draw.rect(surf, s.TREE_TRUNK, (c - 5, c + 6, 10, 24), border_radius=2)
        pygame.draw.circle(surf, (38, 88, 44), (c, c), 24)
        pygame.draw.circle(surf, s.TREE_LEAF, (c, c - 2), 21)
        pygame.draw.circle(surf, (72, 132, 74), (c - 7, c - 9), 11)
        return surf

    def _item(self):
        surf = self._surf(22, 22)
        pygame.draw.rect(surf, (90, 200, 95), (2, 2, 18, 18), border_radius=4)
        pygame.draw.rect(surf, (30, 90, 35), (2, 2, 18, 18), 2, border_radius=4)
        pygame.draw.rect(surf, (240, 255, 240), (6, 6, 5, 5))
        return surf

    def _ammo(self):
        surf = self._surf(22, 22)
        pygame.draw.rect(surf, (180, 140, 60), (2, 5, 18, 13), border_radius=3)
        pygame.draw.rect(surf, (120, 90, 40), (2, 5, 18, 13), 2, border_radius=3)
        for i in range(3):
            pygame.draw.rect(surf, (235, 215, 130), (5 + i * 5, 2, 3, 7))
        return surf

    def _orb(self):
        surf = self._surf(14, 14)
        pygame.draw.circle(surf, s.YELLOW, (7, 7), 6)
        pygame.draw.circle(surf, (255, 255, 210), (7, 7), 3)
        return surf
