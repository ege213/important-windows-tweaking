# uzay_istilasi/sprites/projectiles.py
# -*- coding: utf-8 -*-
import pygame
import math
import settings
import assets

class oyuncuMermi(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = assets.load_image("oyuncu_mermi.png", scale=(10, 20), smooth=True)
        if self.image.get_width() == 64 and self.image.get_height() == 64: # Fallback if placeholder loaded
             self.image = pygame.Surface((10, 20)); self.image.fill(settings.BEYAZ)
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.hiz = 14

    def update(self):
        self.rect.y -= self.hiz
        if self.rect.bottom < 0: self.kill()

class uzayliMermi(pygame.sprite.Sprite):
    def __init__(self, x, y, level_no, difficulty_setting):
        super().__init__()
        self.image = assets.load_image("uzayli_mermi.png", scale=(15, 15), smooth=True)
        if self.image.get_width() == 64 and self.image.get_height() == 64: # Fallback
             self.image = pygame.Surface((15, 15)); self.image.fill(settings.TURUNCU)
        self.rect = self.image.get_rect(centerx=x, top=y)

        self.hiz_base = 8 + (level_no // 2)
        self.hiz = self.hiz_base
        self.difficulty = difficulty_setting
        self.apply_difficulty_modifiers()

    def apply_difficulty_modifiers(self):
        if self.difficulty == settings.Difficulty.EASY: self.hiz = max(5, self.hiz_base * 0.8)
        elif self.difficulty == settings.Difficulty.HARD: self.hiz = self.hiz_base * 1.2
        elif self.difficulty == settings.Difficulty.REVENGEANCE: self.hiz = self.hiz_base * 1.5
        else: self.hiz = self.hiz_base

    def update(self):
        self.rect.y += self.hiz
        if self.rect.top > settings.YUKSEKLIK: self.kill()

class BossMermi(pygame.sprite.Sprite):
    def __init__(self, x, y, angle=0, speed=8, beam=False, target_vector=None, duration=None):
        super().__init__()
        self.is_beam = beam
        self.original_image = None
        self.spawn_time = pygame.time.get_ticks()
        self.duration = duration
        self.velocity_x = 0
        self.velocity_y = 0

        if self.is_beam:
            beam_width = 30
            beam_height = settings.YUKSEKLIK
            self.image = assets.load_image("beam.png", scale=(beam_width, beam_height), smooth=True)
            if self.image.get_width() == 64 and self.image.get_height() == 64: # Fallback
                 self.image = pygame.Surface((beam_width, beam_height)); self.image.fill(settings.ACIK_MAVI)
            self.speed = 0
            self.rect = self.image.get_rect(midtop=(x, y))
        elif target_vector:
            self.original_image = assets.load_image("uzayli_mermi.png", scale=(20, 20), smooth=True)
            if self.original_image.get_width() == 64 and self.original_image.get_height() == 64: # Fallback
                 self.original_image = pygame.Surface((20, 20)); self.original_image.fill(settings.TURUNCU)

            dx, dy = target_vector
            distance = math.hypot(dx, dy)
            self.speed = speed
            if distance > 0:
                self.velocity_x = (dx / distance) * self.speed
                self.velocity_y = (dy / distance) * self.speed
            else:
                self.velocity_y = self.speed

            angle_radians = math.atan2(-self.velocity_y, self.velocity_x)
            angle_degrees = math.degrees(angle_radians)
            self.image = pygame.transform.rotate(self.original_image, angle_degrees - 90)
            self.rect = self.image.get_rect(center=(x, y))
        else: # Spread shot
            self.original_image = assets.load_image("uzayli_mermi.png", scale=(20, 20), smooth=True)
            if self.original_image.get_width() == 64 and self.original_image.get_height() == 64: # Fallback
                 self.original_image = pygame.Surface((20, 20)); self.original_image.fill(settings.TURUNCU)

            self.speed = speed
            original_vector = pygame.math.Vector2(0, 1)
            rotated_vector = original_vector.rotate(-angle)
            self.velocity_x = rotated_vector.x * self.speed
            self.velocity_y = rotated_vector.y * self.speed
            angle_degrees = math.degrees(math.atan2(-self.velocity_y, self.velocity_x))
            self.image = pygame.transform.rotate(self.original_image, angle_degrees - 90)
            self.rect = self.image.get_rect(center=(x, y))

        self.precise_x = float(self.rect.centerx)
        self.precise_y = float(self.rect.centery)

    def update(self):
        now = pygame.time.get_ticks()
        if self.is_beam and self.duration is not None and now - self.spawn_time > self.duration:
            self.kill()
            return

        self.precise_x += self.velocity_x
        self.precise_y += self.velocity_y
        self.rect.centerx = round(self.precise_x)
        self.rect.centery = round(self.precise_y)

        if not self.is_beam and (self.rect.bottom < 0 or self.rect.top > settings.YUKSEKLIK or \
                                 self.rect.left > settings.GENISLIK or self.rect.right < 0):
            self.kill()
