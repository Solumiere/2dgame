"""Camera that follows a target and clamps to bounds."""
import pygame
from . import settings as s


class Camera:
    def __init__(self, width, height):
        self.offset = pygame.math.Vector2(0, 0)
        self.set_bounds(width, height)

    def set_bounds(self, width, height):
        self.width = width
        self.height = height

    def follow(self, target_pos):
        """Center on target, clamping so we never show beyond the map. If the
        map is smaller than the screen on an axis, center it (negative offset)."""
        if self.width <= s.WIDTH:
            self.offset.x = (self.width - s.WIDTH) / 2
        else:
            self.offset.x = max(0.0, min(target_pos.x - s.WIDTH / 2, self.width - s.WIDTH))
        if self.height <= s.HEIGHT:
            self.offset.y = (self.height - s.HEIGHT) / 2
        else:
            self.offset.y = max(0.0, min(target_pos.y - s.HEIGHT / 2, self.height - s.HEIGHT))

    def world_to_screen(self, x, y):
        return (int(x - self.offset.x), int(y - self.offset.y))

    def screen_to_world(self, x, y):
        return pygame.math.Vector2(x + self.offset.x, y + self.offset.y)
