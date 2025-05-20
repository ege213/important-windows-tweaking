# uzay_istilasi/assets.py
# -*- coding: utf-8 -*-
import pygame
import os
from settings import ASSET_DIR, FONT_PATH, PEMBE, SIYAH

if not pygame.font.get_init():
    pygame.font.init()
if not pygame.mixer.get_init():
    pygame.mixer.init()

def load_image(filename, scale=None, convert_alpha=True, smooth=False):
    """Loads an image, optionally scales it, handles errors."""
    filepath = os.path.join(ASSET_DIR, filename)
    if not os.path.exists(filepath):
        print(f"Uyarı: Resim dosyası '{filepath}' bulunamadı.")
        placeholder = pygame.Surface((64, 64) if scale is None else scale)
        placeholder.fill(PEMBE)
        pygame.draw.rect(placeholder, SIYAH, placeholder.get_rect(), 2)
        return placeholder
    try:
        image = pygame.image.load(filepath)
        if convert_alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()
        if scale:
            if smooth:
                image = pygame.transform.smoothscale(image, scale)
            else:
                image = pygame.transform.scale(image, scale)
        return image
    except pygame.error as e:
        print(f"Hata: Resim dosyası '{filepath}' yüklenemedi: {e}")
        placeholder = pygame.Surface((64, 64) if scale is None else scale)
        placeholder.fill(PEMBE)
        pygame.draw.rect(placeholder, SIYAH, placeholder.get_rect(), 2)
        return placeholder

def load_sound(filename):
    """Loads a sound, handles errors."""
    filepath = os.path.join(ASSET_DIR, filename)
    if not os.path.exists(filepath):
        print(f"Uyarı: Ses dosyası '{filepath}' bulunamadı.")
        return None
    try:
        sound = pygame.mixer.Sound(filepath)
        # print(f"Ses dosyası '{filepath}' başarıyla yüklendi.") # Optional: for debugging
        return sound
    except pygame.error as e:
        print(f"Hata: Ses dosyası '{filepath}' yüklenemedi: {e}")
        return None

def get_fonts():
    try:
        return {
            "buyuk": pygame.font.Font(FONT_PATH, 64),
            "orta": pygame.font.Font(FONT_PATH, 48),
            "kucuk": pygame.font.Font(FONT_PATH, 32),
            "minik": pygame.font.Font(FONT_PATH, 24),
            "how_to_play_text": pygame.font.Font(FONT_PATH, 28), # For How To Play screen text
            "how_to_play_heading": pygame.font.Font(FONT_PATH, 38), # For How To Play screen headings
        }
    except pygame.error as e:
        print(f"Font '{FONT_PATH}' yüklenemedi: {e}. Varsayılan font kullanılacak.")
        return {
            "buyuk": pygame.font.Font(None, 74),
            "orta": pygame.font.Font(None, 58),
            "kucuk": pygame.font.Font(None, 42),
            "minik": pygame.font.Font(None, 32),
            "how_to_play_text": pygame.font.Font(None, 36),
            "how_to_play_heading": pygame.font.Font(None, 48),
        }

FONTS = get_fonts()
