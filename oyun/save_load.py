# uzay_istilasi/save_load.py
# -*- coding: utf-8 -*-
import json
from settings import SAVE_FILE, Difficulty, DEFAULT_FPS

def load_game_state():
    """Loads high score, boss unlocked status, and game settings."""
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            high_score = data.get("high_score", 0)
            boss_unlocked = data.get("boss_unlocked", False)
            settings_data = data.get("settings", {})
            music_volume = settings_data.get("music_volume", 0.5)
            sfx_volume = settings_data.get("sfx_volume", 0.5)
            difficulty = settings_data.get("difficulty", Difficulty.NORMAL)
            set_fps = settings_data.get("set_fps", DEFAULT_FPS)
            default_upgrades = {"speed": 0, "fire_rate": 0, "max_bullets": 0, "lives": 0, "parry": 0, "parry_cooldown": 0}
            loaded_upgrades = data.get("upgrade_levels", default_upgrades.copy()) # Use copy
            upgrade_levels = default_upgrades.copy() # Start with defaults
            upgrade_levels.update(loaded_upgrades) # Override with loaded values

            return high_score, boss_unlocked, music_volume, sfx_volume, difficulty, set_fps, upgrade_levels
    except (FileNotFoundError, json.JSONDecodeError):
        default_upgrades = {"speed": 0, "fire_rate": 0, "max_bullets": 0, "lives": 0, "parry": 0, "parry_cooldown": 0}
        return 0, False, 0.5, 0.5, Difficulty.NORMAL, DEFAULT_FPS, default_upgrades.copy()

def save_game_state(high_score, boss_unlocked, music_volume, sfx_volume, difficulty, set_fps, upgrade_levels):
    """Saves high score, boss unlocked status, game settings, and upgrade levels."""
    try:
        with open(SAVE_FILE, "w") as f:
            settings_data = {
                "music_volume": music_volume,
                "sfx_volume": sfx_volume,
                "difficulty": difficulty,
                "set_fps": set_fps
            }
            game_data = {
                "high_score": high_score,
                "boss_unlocked": boss_unlocked,
                "settings": settings_data,
                "upgrade_levels": upgrade_levels
            }
            json.dump(game_data, f, indent=4) # Added indent for readability
    except IOError as e:
        print(f"Oyun durumu kaydedilemedi: {e}")
