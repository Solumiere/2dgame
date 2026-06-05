"""Procedurally generated outdoor world: buildings, trees and cars."""
import random
import pygame
from . import settings as s
from .building import Building


class Tree:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = random.randint(22, 34)

    @property
    def collider(self):
        # Only the trunk blocks movement, so you can walk under the canopy edge.
        return pygame.Rect(int(self.pos.x - 11), int(self.pos.y - 11), 22, 22)


class Car:
    def __init__(self, x, y):
        w = random.choice([92, 104, 116])
        h = random.choice([46, 52])
        if random.random() < 0.5:
            w, h = h, w  # rotate some cars
        self.rect = pygame.Rect(x, y, w, h)
        self.color = random.choice([(150, 60, 60), (60, 80, 150),
                                    (180, 170, 80), (80, 80, 95), (170, 170, 175)])


class World:
    def __init__(self):
        self.width = s.WORLD_WIDTH
        self.height = s.WORLD_HEIGHT
        self.buildings = []
        self.trees = []
        self.cars = []
        self._obstacles = []
        self.generate()

    def generate(self):
        # Buildings (kept apart from each other)
        attempts = 0
        while len(self.buildings) < s.NUM_BUILDINGS and attempts < 400:
            attempts += 1
            bw = random.randint(260, 430)
            bh = random.randint(220, 360)
            x = random.randint(120, self.width - bw - 120)
            y = random.randint(120, self.height - bh - 120)
            rect = pygame.Rect(x, y, bw, bh)
            if any(rect.inflate(160, 160).colliderect(b.rect) for b in self.buildings):
                continue
            self.buildings.append(Building(rect))
        # Trees
        for _ in range(s.NUM_TREES):
            x = random.randint(40, self.width - 40)
            y = random.randint(40, self.height - 40)
            if any(b.rect.inflate(60, 60).collidepoint(x, y) for b in self.buildings):
                continue
            self.trees.append(Tree(x, y))
        # Cars
        for _ in range(s.NUM_CARS):
            x = random.randint(60, self.width - 160)
            y = random.randint(60, self.height - 160)
            car = Car(x, y)
            if any(b.rect.inflate(50, 50).colliderect(car.rect) for b in self.buildings):
                continue
            self.cars.append(car)
        self._rebuild_obstacles()

    def _rebuild_obstacles(self):
        obs = []
        for b in self.buildings:
            obs.append(b.rect)  # solid block; entry happens via door trigger
        for t in self.trees:
            obs.append(t.collider)
        for c in self.cars:
            obs.append(c.rect)
        self._obstacles = obs

    def obstacles(self):
        return self._obstacles

    def bounds(self):
        return (self.width, self.height)

    def find_open_spawn(self):
        """Return a player start position not stuck inside an obstacle."""
        cx, cy = self.width / 2, self.height / 2
        for _ in range(200):
            test = pygame.Rect(int(cx - 20), int(cy - 20), 40, 40)
            if not any(test.colliderect(o) for o in self._obstacles):
                return pygame.math.Vector2(cx, cy)
            cx = random.randint(200, self.width - 200)
            cy = random.randint(200, self.height - 200)
        return pygame.math.Vector2(self.width / 2, self.height / 2)
