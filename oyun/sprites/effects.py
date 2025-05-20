# uzay_istilasi/sprites/effects.py
# -*- coding: utf-8 -*-
import pygame
import random
import settings
import assets

class SwordSlash(pygame.sprite.Sprite):
    def __init__(self, centerx, bottom):
        super().__init__()
        self.image = assets.load_image("sword.png", scale=(80, 80), smooth=True)
        self.rect = self.image.get_rect(centerx=centerx, bottom=bottom)
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 750
        self.parry_sound = assets.load_sound("parry.wav")

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > self.duration:
            self.kill()

    def play_parry_sound(self):
        if self.parry_sound:
            self.parry_sound.play()

class WarningIndicator(pygame.sprite.Sprite):
    def __init__(self, x, y, duration=750, beam_type=False, target_type=False):
        super().__init__()
        self.duration = duration
        self.spawn_time = pygame.time.get_ticks()
        self.image = None

        if beam_type:
            warn_height = settings.YUKSEKLIK - y
            warn_width = 20
            self.image = assets.load_image("warning.png", scale=(warn_width, warn_height), smooth=True)
            if self.image:
                self.rect = self.image.get_rect(midtop=(x, y))
        elif target_type:
            warn_size = 50
            self.image = assets.load_image("warning.png", scale=(warn_size, warn_size), smooth=True)
            if self.image:
                self.rect = self.image.get_rect(center=(x, y))
        else:
            self.kill()
            return

        if self.image:
            self.image.set_alpha(180)

    def update(self):
        if not hasattr(self, 'image') or not self.image: # Ensure image exists
            self.kill()
            return

        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if (elapsed // 100) % 2 == 0:
            self.image.set_alpha(220)
        else:
            self.image.set_alpha(100)

        if now > self.spawn_time + self.duration:
            self.kill()

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, size_range, velocity_range, lifespan_range):
        super().__init__()
        self.size = random.randint(size_range[0], size_range[1])
        self.image = pygame.Surface([self.size, self.size], pygame.SRCALPHA) # Use SRCALPHA for per-pixel alpha
        
        # Draw a circle for a smoother particle, or keep square
        pygame.draw.circle(self.image, color, (self.size // 2, self.size // 2), self.size // 2)
        # self.image.fill(color) # If you prefer squares
        
        self.rect = self.image.get_rect(center=(x, y))
        
        self.velocity_x = random.uniform(velocity_range[0][0], velocity_range[0][1])
        self.velocity_y = random.uniform(velocity_range[1][0], velocity_range[1][1])
        
        self.lifespan = random.randint(lifespan_range[0], lifespan_range[1])
        self.spawn_time = pygame.time.get_ticks()
        self.initial_alpha = color[3] if len(color) == 4 else 255 # Handle RGBA or RGB

    def update(self):
        now = pygame.time.get_ticks()
        age = now - self.spawn_time

        if age > self.lifespan:
            self.kill()
            return

        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y

        # Fade out effect
        current_alpha = self.initial_alpha * (1 - (age / self.lifespan))
        self.image.set_alpha(max(0, int(current_alpha)))

        # Optional: Add gravity or other forces
        # self.velocity_y += 0.1 # Example gravity
