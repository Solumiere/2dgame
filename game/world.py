"""Procedurally generated outdoor world: buildings, trees and cars.

Cars are drivable. Each car has a max speed and a fuel tank -- some cars spawn
with no fuel and cannot be driven until (conceptually) refueled.
"""
import math
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
        # Only the trunk blocks movement.
        return pygame.Rect(int(self.pos.x - 11), int(self.pos.y - 11), 22, 22)


class Car:
    def __init__(self, x, y):
        w = random.choice([96, 108, 120])
        h = random.choice([48, 54])
        if random.random() < 0.5:
            w, h = h, w  # some cars spawn rotated 90 degrees
        self.w = w
        self.h = h
        self.pos = pygame.math.Vector2(x + w / 2, y + h / 2)
        self.vel = pygame.math.Vector2(0, 0)
        self.heading = 0.0  # radians; 0 = facing +x
        self.color = random.choice([(150, 60, 60), (60, 80, 150), (180, 170, 80),
                                    (80, 80, 95), (170, 170, 175), (70, 130, 90)])
        self.max_speed = random.uniform(300, 460)
        self.has_fuel = random.random() < 0.6
        self.fuel = random.uniform(35, 100) if self.has_fuel else 0.0
        self.max_fuel = 100.0
        self.base_surf = None  # built lazily for rendering

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x - self.w / 2), int(self.pos.y - self.h / 2),
                           self.w, self.h)

    def drive(self, dt, accel, obstacles, bounds):
        """accel: input direction Vector2 (may be zero). Applies fuel limits,
        friction, speed clamp, collisions and bounds."""
        if self.fuel > 0 and accel.length_squared() > 0:
            self.vel += accel.normalize() * s.CAR_ACCEL * dt
        else:
            sp = self.vel.length()
            if sp > 1:
                self.vel.scale_to_length(max(0.0, sp - s.CAR_DECEL * dt))
            else:
                self.vel.update(0, 0)
        sp = self.vel.length()
        if sp > self.max_speed:
            self.vel.scale_to_length(self.max_speed)
        self._move(dt, obstacles)
        self.pos.x = max(self.w / 2, min(self.pos.x, bounds[0] - self.w / 2))
        self.pos.y = max(self.h / 2, min(self.pos.y, bounds[1] - self.h / 2))
        if self.vel.length_squared() > 9:
            self.heading = math.atan2(self.vel.y, self.vel.x)
        self.fuel = max(0.0, self.fuel - self.vel.length() * dt * s.FUEL_BURN)

    def _move(self, dt, obstacles):
        self.pos.x += self.vel.x * dt
        r = self.rect
        for ob in obstacles:
            if r.colliderect(ob):
                if self.vel.x > 0:
                    self.pos.x = ob.left - self.w / 2
                elif self.vel.x < 0:
                    self.pos.x = ob.right + self.w / 2
                self.vel.x = 0
                r = self.rect
        self.pos.y += self.vel.y * dt
        r = self.rect
        for ob in obstacles:
            if r.colliderect(ob):
                if self.vel.y > 0:
                    self.pos.y = ob.top - self.h / 2
                elif self.vel.y < 0:
                    self.pos.y = ob.bottom + self.h / 2
                self.vel.y = 0
                r = self.rect

    def speed_kmh(self):
        return int(self.vel.length() / 3)


class World:
    def __init__(self):
        self.width = s.WORLD_WIDTH
        self.height = s.WORLD_HEIGHT
        self.buildings = []
        self.trees = []
        self.cars = []
        self.generate()

    def generate(self):
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
        for _ in range(s.NUM_TREES):
            x = random.randint(40, self.width - 40)
            y = random.randint(40, self.height - 40)
            if any(b.rect.inflate(60, 60).collidepoint(x, y) for b in self.buildings):
                continue
            self.trees.append(Tree(x, y))
        for _ in range(s.NUM_CARS):
            x = random.randint(60, self.width - 200)
            y = random.randint(60, self.height - 200)
            car = Car(x, y)
            if any(b.rect.inflate(50, 50).colliderect(car.rect) for b in self.buildings):
                continue
            self.cars.append(car)

    def obstacles(self, exclude_car=None):
        obs = [b.rect for b in self.buildings]
        obs += [t.collider for t in self.trees]
        for c in self.cars:
            if c is exclude_car:
                continue
            obs.append(c.rect)
        return obs

    def bounds(self):
        return (self.width, self.height)

    def find_open_spawn(self):
        obs = self.obstacles()
        cx, cy = self.width / 2, self.height / 2
        for _ in range(200):
            test = pygame.Rect(int(cx - 20), int(cy - 20), 40, 40)
            if not any(test.colliderect(o) for o in obs):
                return pygame.math.Vector2(cx, cy)
            cx = random.randint(200, self.width - 200)
            cy = random.randint(200, self.height - 200)
        return pygame.math.Vector2(self.width / 2, self.height / 2)
