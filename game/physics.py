"""Shared collision helpers."""
import pygame


def move_with_collision(pos, size, dx, dy, obstacles):
    """Move an axis-aligned entity centered at `pos` by (dx, dy), resolving
    collisions against a list of pygame.Rect obstacles. `pos` is a Vector2 and
    is mutated in place."""
    # Horizontal
    pos.x += dx
    rect = pygame.Rect(int(pos.x - size / 2), int(pos.y - size / 2), size, size)
    for ob in obstacles:
        if rect.colliderect(ob):
            if dx > 0:
                pos.x = ob.left - size / 2
            elif dx < 0:
                pos.x = ob.right + size / 2
            rect = pygame.Rect(int(pos.x - size / 2), int(pos.y - size / 2), size, size)
    # Vertical
    pos.y += dy
    rect = pygame.Rect(int(pos.x - size / 2), int(pos.y - size / 2), size, size)
    for ob in obstacles:
        if rect.colliderect(ob):
            if dy > 0:
                pos.y = ob.top - size / 2
            elif dy < 0:
                pos.y = ob.bottom + size / 2
            rect = pygame.Rect(int(pos.x - size / 2), int(pos.y - size / 2), size, size)
