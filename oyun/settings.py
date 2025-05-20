# uzay_istilasi/settings.py
# -*- coding: utf-8 -*-
import pygame

# Pencere boyutu
GENISLIK, YUKSEKLIK = 1920, 1080
INITIAL_DISPLAY_FLAGS = pygame.DOUBLEBUF | pygame.HWSURFACE

# FPS
DEFAULT_FPS = 60

# Colors
BEYAZ = (255, 255, 255)
SIYAH = (0, 0, 0)
KIRMIZI = (255, 0, 0)
YESIL = (0, 255, 0)
MAVI = (0, 0, 255)
PEMBE = (255, 0, 255)
SARI = (255, 255, 0)
TURUNCU = (255, 165, 0)
KOYU_KIRMIZI = (139, 0, 0)
ACIK_MAVI = (173, 216, 230)
YESIL_KOYU = (0, 100, 0)
KOYU_MAVI = (0, 0, 139)
KOYU_GRI = (50, 50, 50)
ENRAGE_OVERLAY_COLOR = (255, 0, 0, 50)

# Game States
class GameState:
    MAIN_MENU = 0
    PLAYING = 1
    PAUSED = 2
    OPTIONS = 3
    GAME_OVER = 4
    LEVEL_TRANSITION = 5
    WIN = 6
    UPGRADES = 7
    BOSS_FIGHT = 8
    BOSS_DEFEATED_CUTSCENE = 9
    BOSS_BARRAGE_CUTSCENE = 10
    HOW_TO_PLAY = 11 # New State

# Difficulty Levels
class Difficulty:
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    INSTA_DEATH = "insta_death"
    REVENGEANCE = "revengeance"

# Asset Paths
ASSET_DIR = "assets"
FONT_PATH = f"{ASSET_DIR}/oyun_font.ttf" # Make sure your font is here
SAVE_FILE = "gamestate.json"

# Max Levels
MAX_LEVELS = 10

# Cheat Code
CHEAT_CODE = "bilisim"

# Particle Colors (Example for explosions)
EXPLOSION_COLORS = [
    (255, 255, 0),    # Yellow
    (255, 165, 0),    # Orange
    (255, 69, 0),     # OrangeRed
    (255, 0, 0),      # Red
    (150, 150, 150)   # Grey for smoke/debris
]
