# -*- coding: utf-8 -*-
import pygame
import random
import json
import os # To check for file existence
import math # Needed for beam rotation and other calculations

# === Initialization ===
pygame.init()
pygame.mixer.init() # Ensure mixer is initialized

# Pencere boyutu - Increased dimensions for more space
GENISLIK, YUKSEKLIK = 1920, 1080 # Increased height further from your base
# Store initial display flags
initial_display_flags = pygame.DOUBLEBUF | pygame.HWSURFACE
pencere = pygame.display.set_mode((GENISLIK, YUKSEKLIK), initial_display_flags)
pygame.display.set_caption("Uzay İstilası - Boss Seviyesi")

# FPS
DEFAULT_FPS = 60 # Default FPS
# FPS is now a game setting, stored in oyun.set_fps
saat = pygame.time.Clock()

# Colors
BEYAZ = (255, 255, 255)
SIYAH = (0, 0, 0)
KIRMIZI = (255, 0, 0)
YESIL = (0, 255, 0)
MAVI = (0, 0, 255)
PEMBE = (255, 0, 255)
SARI = (255, 255, 0)
TURUNCU = (255, 165, 0) # For warnings
KOYU_KIRMIZI = (139, 0, 0) # For health bar background
ACIK_MAVI = (173, 216, 230) # For boss shield/special effects maybe
YESIL_KOYU = (0, 100, 0) # For usable skill background
KOYU_MAVI = (0, 0, 139) # For message box background
KOYU_GRI = (50, 50, 50) # For drained health bar background
ENRAGE_OVERLAY_COLOR = (255, 0, 0, 50) # Semi-transparent red for enrage effect

# Game States
class GameState:
    MAIN_MENU = 0
    PLAYING = 1
    PAUSED = 2
    OPTIONS = 3
    GAME_OVER = 4
    LEVEL_TRANSITION = 5
    WIN = 6
    UPGRADES = 7 # Now used between levels
    BOSS_FIGHT = 8 # Specific state for boss level if needed for distinct logic
    BOSS_DEFEATED_CUTSCENE = 9 # New state for boss defeat cutscene
    BOSS_BARRAGE_CUTSCENE = 10 # New state for player barrage cutscene

# Difficulty Levels
class Difficulty:
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    INSTA_DEATH = "insta_death"
    REVENGEANCE = "revengeance"

# === Load Assets ===
# Fonts
try:
    oyun_font_buyuk = pygame.font.Font("assets/oyun_font.ttf", 64)
    oyun_font_orta = pygame.font.Font("assets/oyun_font.ttf", 48)
    oyun_font_kucuk = pygame.font.Font("assets/oyun_font.ttf", 32)
    oyun_font_minik = pygame.font.Font("assets/oyun_font.ttf", 24)
except pygame.error as e:
    print(f"Font 'assets/oyun_font.ttf' yüklenemedi: {e}. Varsayılan font kullanılacak.")
    oyun_font_buyuk = pygame.font.Font(None, 74)
    oyun_font_orta = pygame.font.Font(None, 58)
    oyun_font_kucuk = pygame.font.Font(None, 42)
    oyun_font_minik = pygame.font.Font(None, 32)

# Helper function for text rendering
def render_text(text, font, color, surface, center_x, y, center_y=False, top_left=False):
    text_surface = font.render(text, True, color)
    if top_left:
        text_rect = text_surface.get_rect(topleft=(center_x, y))
    elif center_y:
         text_rect = text_surface.get_rect(center=(center_x, y))
    else:
         text_rect = text_surface.get_rect(centerx=center_x, top=y)
    surface.blit(text_surface, text_rect)
    return text_rect

# Asset Loading Helper
def load_image(filename, scale=None, convert_alpha=True, smooth=False):
    """Loads an image, optionally scales it, handles errors."""
    filepath = os.path.join("assets", filename) # Look inside assets folder
    if not os.path.exists(filepath):
        print(f"Uyarı: '{filepath}' bulunamadı.")
        # Return a placeholder surface
        placeholder = pygame.Surface((64, 64) if scale is None else scale)
        placeholder.fill(PEMBE) # Bright color to indicate missing asset
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
        print(f"Hata: '{filepath}' yüklenemedi: {e}")
        placeholder = pygame.Surface((64, 64) if scale is None else scale)
        placeholder.fill(PEMBE)
        pygame.draw.rect(placeholder, SIYAH, placeholder.get_rect(), 2)
        return placeholder

def load_sound(filename):
    """Loads a sound, handles errors."""
    filepath = os.path.join("assets", filename) # Look inside assets folder
    if not os.path.exists(filepath):
        print(f"Uyarı: Ses dosyası '{filepath}' bulunamadı.")
        return None # Return None if sound missing
    try:
        sound = pygame.mixer.Sound(filepath)
        print(f"Ses dosyası '{filepath}' başarıyla yüklendi.") # Debug print
        return sound
    except pygame.error as e:
        print(f"Hata: Ses dosyası '{filepath}' yüklenemedi: {e}")
        return None

# Game State Saving/Loading
def load_game_state():
    """Loads high score, boss unlocked status, and game settings."""
    try:
        with open("gamestate.json", "r") as f:
            data = json.load(f)
            high_score = data.get("high_score", 0)
            boss_unlocked = data.get("boss_unlocked", False)
            # Load settings with defaults
            settings = data.get("settings", {})
            music_volume = settings.get("music_volume", 0.5)
            sfx_volume = settings.get("sfx_volume", 0.5)
            difficulty = settings.get("difficulty", Difficulty.NORMAL)
            set_fps = settings.get("set_fps", DEFAULT_FPS)
            return high_score, boss_unlocked, music_volume, sfx_volume, difficulty, set_fps
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default values if file not found or corrupted
        return 0, False, 0.5, 0.5, Difficulty.NORMAL, DEFAULT_FPS

def save_game_state(high_score, boss_unlocked, music_volume, sfx_volume, difficulty, set_fps):
    """Saves high score, boss unlocked status, and game settings."""
    try:
        with open("gamestate.json", "w") as f:
            settings = {
                "music_volume": music_volume,
                "sfx_volume": sfx_volume,
                "difficulty": difficulty,
                "set_fps": set_fps
            }
            json.dump({"high_score": high_score, "boss_unlocked": boss_unlocked, "settings": settings}, f)
    except IOError as e:
        print(f"Oyun durumu kaydedilemedi: {e}")

# === Classes ===

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, projectile_group, warning_group, player_ref, minion_group_ref, difficulty):
        super().__init__()
        self.image_original = load_image("boss.png") # Load the boss image provided by user
        # Scale the boss image if needed, e.g., make it larger
        boss_width = 200
        boss_height = 150
        self.image = pygame.transform.scale(self.image_original, (boss_width, boss_height))
        self.rect = self.image.get_rect(centerx=x, top=y)

        self.projectile_group = projectile_group
        self.warning_group = warning_group
        self.player = player_ref # Reference to player needed for some attacks
        self.minion_group = minion_group_ref # Reference to the minion group
        self.difficulty = difficulty # Store difficulty

        # Stats - Adjusted by difficulty later
        self.max_hp = 4000
        self.base_speed = 6
        self.base_attack_delay = 1500 # Milliseconds between attacks (initially)
        self.barrage_fire_rate = 80 # Milliseconds between bullets in barrage
        self.barrage_duration = 1000 # Duration of the boss's barrage attack pattern (in ms)

        # Apply difficulty to base stats
        self.apply_difficulty_settings()

        self.current_hp = self.max_hp
        self.speed = self.base_speed
        self.attack_delay = self.base_attack_delay
        self.direction = 1 # 1 for right, -1 for left
        self.is_moving = True # Flag to control movement

        # Attack Patterns Management
        self.attack_timer = pygame.time.get_ticks()
        self.attack_phase = 0 # Different phases can have different attacks/delays
        self.warning_active = False
        self.warning_timer = 0
        self.warning_duration = 600 # Slightly shorter warning duration
        self.current_attack_type = None
        self.attack_target_pos = None # Used for targeted attacks

        # Sounds
        self.hit_sound = load_sound("uzayli_vurus.wav") # Reuse or add specific boss hit sound
        self.shoot_sound = load_sound("uzayli_mermi.wav") # Reuse or add specific boss shoot sound
        self.warning_sound = load_sound("oyuncu_mermi.wav") # Sound for warning appearing
        self.beam_sound = load_sound("beam.wav") # Boss beam sound
        self.summon_sound = load_sound("summon.wav") # Minion summon sound
        self.enraged_sound = load_sound("enraged.wav") # Enraged sound

        # Beam attack specific
        self.is_beaming = False
        self.beam_duration = 1500 # How long the beam lasts
        self.beam_end_time = 0

        # Minion Spawning
        self.minion_spawn_timer = pygame.time.get_ticks()
        self.minion_spawn_delay = 15000 # 15 seconds

        # Enrage State
        self.enrage_threshold = self.max_hp // 2
        self.is_enraged = False
        self.enraged_speed_multiplier = 1.2
        self.enraged_attack_multiplier = 0.5 # Attack delay becomes half (2x speed)

        # Barrage Attack
        self.barrage_end_time = 0
        self.last_barrage_shot = 0

    def apply_difficulty_settings(self):
        """Adjusts boss stats based on difficulty."""
        if self.difficulty == Difficulty.EASY:
            self.max_hp = 3000
            self.base_speed = 4
            self.base_attack_delay = 2000
            self.barrage_fire_rate = 120
            self.minion_spawn_delay = 20000
            self.barrage_duration = 800 # Shorter barrage on easy
        elif self.difficulty == Difficulty.NORMAL:
            self.max_hp = 4000
            self.base_speed = 6
            self.base_attack_delay = 1500
            self.barrage_fire_rate = 80
            self.minion_spawn_delay = 15000
            self.barrage_duration = 1000
        elif self.difficulty == Difficulty.HARD:
            self.max_hp = 5000
            self.base_speed = 8
            self.base_attack_delay = 1000
            self.barrage_fire_rate = 60
            self.minion_spawn_delay = 10000
            self.barrage_duration = 1200 # Longer barrage on hard
        elif self.difficulty == Difficulty.INSTA_DEATH:
             self.max_hp = 4000 # Boss HP is same as normal
             self.base_speed = 6
             self.base_attack_delay = 1500
             self.barrage_fire_rate = 80
             self.minion_spawn_delay = 15000
             self.barrage_duration = 1000
        elif self.difficulty == Difficulty.REVENGEANCE:
            self.max_hp = 6000
            self.base_speed = 10
            self.base_attack_delay = 800
            self.barrage_fire_rate = 40
            self.minion_spawn_delay = 8000
            self.enrage_threshold = self.max_hp * 0.6 # Enrage earlier
            self.enraged_speed_multiplier = 1.5
            self.enraged_attack_multiplier = 0.3
            self.barrage_duration = 1500 # Longest barrage

        # Ensure current speed and attack delay are updated if difficulty changes mid-game (though this shouldn't happen with current flow)
        self.speed = self.base_speed
        self.attack_delay = self.base_attack_delay


    def update(self):
        if self.is_moving: # Only move if allowed
            self._move()
            self._handle_attacks() # Only attack if moving
            self._handle_minion_spawning() # Only spawn minions if moving
        self._check_enrage()
        self._handle_barrage() # Handle firing during barrage (can continue briefly after defeat)

    def _move(self):
        self.rect.x += self.speed * self.direction
        # Bounce off walls
        if self.rect.right > GENISLIK - 20: # Leave some margin
            self.rect.right = GENISLIK - 20
            self.direction = -1
        elif self.rect.left < 20:
            self.rect.left = 20
            self.direction = 1
        # Optional: Add vertical movement patterns later

    def _handle_attacks(self):
        now = pygame.time.get_ticks()

        # Don't prepare new attacks or fire regular attacks during barrage or if not moving (defeated)
        if (self.current_attack_type == 'barrage' and now < self.barrage_end_time) or not self.is_moving:
             return

        # If a warning is active, check if it's time to fire
        if self.warning_active and now > self.warning_timer + self.warning_duration:
            self._execute_attack()
            self.warning_active = False
            # If the executed attack was a beam, the next attack timer starts after the beam ends
            if self.current_attack_type == 'beam':
                 self.beam_end_time = now + self.beam_duration
            elif self.current_attack_type == 'barrage':
                 self.barrage_end_time = now + self.barrage_duration # Corrected: Accessing self.barrage_duration from Boss class
                 self.last_barrage_shot = now # Start barrage firing timer
            else:
                 self.attack_timer = now # Reset timer after firing

        # If no warning is active and attack delay has passed, start a new attack
        # Also check if beam or barrage attack has finished
        elif not self.warning_active and now > self.attack_timer + self.attack_delay and now > self.beam_end_time and now > self.barrage_end_time:
            self._prepare_attack()
            self.warning_timer = now # Start warning timer

    def _prepare_attack(self):
        """Choose attack type, create warning."""
        self.warning_active = True
        # Added 'barrage' to attack choices, adjusted weights based on enrage state and difficulty
        attack_weights = {
            'spread': 3,
            'beam': 2,
            'targeted': 2,
            'barrage': 1 # Lower initial chance for barrage
        }

        if self.is_enraged:
             # More likely to do beam or barrage when enraged
             attack_weights['spread'] = 2
             attack_weights['beam'] = 4
             attack_weights['targeted'] = 3
             attack_weights['barrage'] = 5 # Higher chance for barrage when enraged

        if self.difficulty == Difficulty.EASY:
             attack_weights['spread'] = 4
             attack_weights['beam'] = 1
             attack_weights['targeted'] = 1
             attack_weights['barrage'] = 0 # No barrage on easy

        elif self.difficulty == Difficulty.HARD:
             attack_weights['spread'] = 2
             attack_weights['beam'] = 3
             attack_weights['targeted'] = 3
             attack_weights['barrage'] = 4

        elif self.difficulty == Difficulty.REVENGEANCE:
             attack_weights['spread'] = 1
             attack_weights['beam'] = 5
             attack_weights['targeted'] = 4
             attack_weights['barrage'] = 6


        attack_choice = random.choices(list(attack_weights.keys()), weights=list(attack_weights.values()), k=1)[0]


        if attack_choice == 'spread':
            self.current_attack_type = 'spread'
            # Warning for spread shot (maybe just a sound or flash?)
            if self.warning_sound: self.warning_sound.play()
            # For spread, warning indicator might not be position-specific
            self.attack_target_pos = None # Not needed for spread from boss center

        elif attack_choice == 'beam':
            self.current_attack_type = 'beam'
            # Warning for beam: Show a line/area where beam will fire
            beam_x = self.rect.centerx
            self.attack_target_pos = (beam_x, self.rect.bottom)
            warning = WarningIndicator(beam_x, self.rect.bottom, duration=self.warning_duration, beam_type=True)
            self.warning_group.add(warning)
            if self.warning_sound: self.warning_sound.play()

        elif attack_choice == 'targeted':
             self.current_attack_type = 'targeted'
             # Warning for targeted shot: Show indicator near player's current pos
             target_x = self.player.rect.centerx
             target_y = self.player.rect.centery - 50 # Aim slightly above player
             self.attack_target_pos = (target_x, self.rect.bottom) # Originates from boss
             warning = WarningIndicator(target_x, target_y, duration=self.warning_duration, target_type=True) # Indicate target area
             self.warning_group.add(warning)
             if self.warning_sound: self.warning_sound.play()

        elif attack_choice == 'barrage':
             self.current_attack_type = 'barrage'
             # Warning for barrage: Maybe a distinct sound or visual cue on the boss
             if self.warning_sound: self.warning_sound.play() # Reuse warning sound
             self.attack_target_pos = None # Not position-specific for warning


        # Adjust attack delay for next time (maybe faster as health drops and based on difficulty)
        base_delay = self.base_attack_delay
        if self.is_enraged:
            base_delay *= self.enraged_attack_multiplier

        health_ratio = self.current_hp / self.max_hp
        # Attack delay scales with health ratio
        self.attack_delay = max(300, base_delay * health_ratio + 100) # Minimum 0.3 sec


    def _execute_attack(self):
        """Fire the projectile(s) based on the prepared attack type."""
        if self.current_attack_type == 'spread':
            if self.shoot_sound: self.shoot_sound.play()
            # Fire 5 bullets in a wider spread
            bullet_speed = 9
            if self.difficulty == Difficulty.HARD: bullet_speed = 11
            elif self.difficulty == Difficulty.REVENGEANCE: bullet_speed = 13

            for angle in [-25, -10, 0, 10, 25]: # Wider spread
                mermi = BossMermi(self.rect.centerx, self.rect.bottom, angle=angle, speed=bullet_speed) # Slightly faster bullets
                self.projectile_group.add(mermi)

        elif self.current_attack_type == 'beam':
             if self.beam_sound: self.beam_sound.play()
             # Create a beam projectile
             if self.attack_target_pos:
                 # Beam starts from boss bottom and goes to the bottom of the screen
                 beam = BossMermi(self.attack_target_pos[0], self.rect.bottom, beam=True, duration=self.beam_duration)
                 self.projectile_group.add(beam)

        elif self.current_attack_type == 'targeted':
             if self.shoot_sound: self.shoot_sound.play()
             # Fire a bullet towards the player's position *at the time of warning*
             bullet_speed = 12
             if self.difficulty == Difficulty.HARD: bullet_speed = 14
             elif self.difficulty == Difficulty.REVENGEANCE: bullet_speed = 16

             if self.attack_target_pos:
                  target_x, _ = self.attack_target_pos # We stored target X in prep phase
                  # Calculate vector from boss center to target X (at player height)
                  dx = target_x - self.rect.centerx
                  dy = YUKSEKLIK - self.rect.bottom # Aim downwards towards bottom of screen
                  mermi = BossMermi(self.rect.centerx, self.rect.bottom, target_vector=(dx, dy), speed=bullet_speed) # Faster targeted shots
                  self.projectile_group.add(mermi)

        elif self.current_attack_type == 'barrage':
             # Barrage firing is handled in _handle_barrage during its duration
             pass # No immediate action here, just start the timer

    def _handle_barrage(self):
        """Handles continuous firing during a barrage attack."""
        now = pygame.time.get_ticks()
        if self.current_attack_type == 'barrage' and now < self.barrage_end_time:
            # Fire bullets rapidly during the barrage duration
            if now - self.last_barrage_shot > self.barrage_fire_rate:
                 if self.shoot_sound: self.shoot_sound.play() # Play sound for each bullet
                 # Fire a bullet towards the player's current position
                 target_x = self.player.rect.centerx
                 dx = target_x - self.rect.centerx
                 dy = YUKSEKLIK - self.rect.bottom
                 mermi = BossMermi(self.rect.centerx, self.rect.bottom, target_vector=(dx, dy), speed=10) # Barrage bullets speed
                 self.projectile_group.add(mermi)
                 self.last_barrage_shot = now

    def _handle_minion_spawning(self):
        """Checks if it's time to spawn minions."""
        now = pygame.time.get_ticks()
        # Only spawn minions once after the initial delay and if no minions are currently alive
        if now - self.minion_spawn_timer > self.minion_spawn_delay and len(self.minion_group) == 0 and self.is_moving: # Only spawn if boss is moving
            self._spawn_minions()
            # No need to reset the timer if we only spawn once or based on a different condition later

    def _spawn_minions(self):
        """Spawns a wave of minions."""
        if self.summon_sound: self.summon_sound.play()
        num_minions = 3 # Spawn 3 minions
        minion_spacing = 80 # Horizontal space between minions
        start_x = self.rect.centerx - (num_minions - 1) * minion_spacing // 2

        for i in range(num_minions):
            x_pos = start_x + i * minion_spacing
            y_pos = self.rect.bottom + 10 # Spawn just below the boss
            # Pass the minion group reference and other necessary info
            minion = Minion(x_pos, y_pos, self.speed * 0.8, self, self.minion_group, self.player.oyun_ref.uzayli_mermi_grup, self.player.oyun_ref.uzayli_mermi_sesi, self.player.oyun_ref.bolum_no, self.difficulty) # Pass difficulty to minion
            self.minion_group.add(minion)

    def _check_enrage(self):
        """Checks if the boss should become enraged."""
        if not self.is_enraged and self.current_hp <= self.enrage_threshold:
            self._enrage()

    def _enrage(self):
        """Activates the boss's enraged state."""
        self.is_enraged = True
        print("Boss is enraged! Attempting to play sound.") # Debug print
        if self.enraged_sound:
            self.enraged_sound.play()
            print("Enraged sound played.") # Debug print if sound object exists
        else:
             print("Enraged sound object is None.") # Debug print if sound object is None

        self.speed = self.base_speed * self.enraged_speed_multiplier # Increase movement speed
        # Attack delay multiplier is used in _handle_attacks
        print("Boss is enraged!") # Debugging
        # Trigger the visual effects in the Oyun class
        self.player.oyun_ref._apply_enraged_visuals()


    def take_damage(self, amount):
        self.current_hp -= amount
        if self.hit_sound: self.hit_sound.play()
        # Add visual feedback (flash red?) - see draw method
        self.flash_timer = pygame.time.get_ticks()

        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_moving = False # Stop boss movement
            # Stop enraged sound if it's playing
            if self.is_enraged and self.enraged_sound:
                 self.enraged_sound.stop()
                 print("Enraged sound stopped on boss defeat.") # Debug print

            # Trigger boss defeated cutscene
            if self.player.oyun_ref: # Ensure Oyun reference is available
                 self.player.oyun_ref.game_state = GameState.BOSS_DEFEATED_CUTSCENE
                 self.player.oyun_ref.cutscene_start_time = pygame.time.get_ticks() # Start cutscene timer
                 if self.player.oyun_ref.defeat_sound: self.player.oyun_ref.defeat_sound.play() # Play defeat sound


    def draw_health_bar(self, surface):
        # Bar dimensions and position
        bar_width = GENISLIK * 0.6 # 60% of screen width
        bar_height = 25
        bar_x = (GENISLIK - bar_width) // 2
        bar_y = 15 # Near the top

        # Calculate health ratio
        health_ratio = self.current_hp / self.max_hp
        current_width = bar_width * health_ratio

        # Draw background bar (dark grey for drained health)
        pygame.draw.rect(surface, KOYU_GRI, (bar_x, bar_y, bar_width, bar_height))
        # Draw current health bar (red)
        pygame.draw.rect(surface, KIRMIZI, (bar_x, bar_y, current_width, bar_height))
        # Draw border
        pygame.draw.rect(surface, BEYAZ, (bar_x, bar_y, bar_width, bar_height), 3)
        # Optional: Add text label
        render_text("BOSS", oyun_font_minik, BEYAZ, surface, bar_x - 50, bar_y + bar_height // 2, center_y=True)

    def draw(self, surface):
        # Flash white briefly when hit
        if hasattr(self, 'flash_timer') and pygame.time.get_ticks() < self.flash_timer + 100: # Flash for 100ms
             # Create a white version of the image
             flash_image = self.image.copy()
             flash_image.fill((255, 255, 255, 150), special_flags=pygame.BLEND_RGBA_MULT)
             surface.blit(flash_image, self.rect)
        else:
             surface.blit(self.image, self.rect)

class Minion(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, boss_ref, minion_group_ref, mermi_grup, mermi_sesi, level_no, difficulty):
        super().__init__()
        self.image = load_image("minion.png", scale=(40, 40), smooth=True) # Need a minion image, use smoothscale
        if self.image is None: # Fallback
             self.image = pygame.Surface((40, 40)); self.image.fill(MAVI)

        self.rect = self.image.get_rect(centerx=x, top=y)
        self.speed = speed
        self.boss = boss_ref # Reference to the boss
        self.minion_group = minion_group_ref # Reference to the minion group
        self.mermi_grup = mermi_grup # Group to add minion bullets to
        self.minion_mermi_sesi = mermi_sesi # Reuse alien sound
        self.level_no = level_no # For bullet speed scaling
        self.difficulty = difficulty # Store difficulty

        # Adjust fire rate based on difficulty
        self.fire_rate = random.randint(700, 1300) # Base fire rate
        if self.difficulty == Difficulty.EASY: self.fire_rate = random.randint(1000, 1800)
        elif self.difficulty == Difficulty.HARD: self.fire_rate = random.randint(500, 1000)
        elif self.difficulty == Difficulty.REVENGEANCE: self.fire_rate = random.randint(300, 800)


        self.last_shot_time = pygame.time.get_ticks()
        self.fire_chance = 1 # Lower is more frequent
        self.max_bullets_per_minion = 1 # Max bullets per minion instance

        self.offset_x = self.rect.centerx - self.boss.rect.centerx # Maintain initial horizontal offset

    def update(self):
        # Move horizontally with the boss, maintaining relative position
        if self.boss.alive() and self.boss.is_moving: # Only follow if boss is alive and moving
            self.rect.centerx = self.boss.rect.centerx + self.offset_x
        else:
             # If boss is dead or stopped, minions just fall or die
             self.rect.y += self.speed # Make them fall
             if self.rect.top > YUKSEKLIK: self.kill() # Remove if offscreen


        # Simple firing logic (minions stop firing when boss is defeated)
        now = pygame.time.get_ticks()
        # Count only alien/minion bullets in the uzayli_mermi_grup
        current_minion_bullets = sum(1 for b in self.mermi_grup.sprites() if isinstance(b, uzayliMermi))
        if now - self.last_shot_time > self.fire_rate and current_minion_bullets < self.max_bullets_per_minion * len(self.minion_group) and self.boss.is_moving: # Only fire if boss is moving
             if random.randint(0, 100 * self.fire_chance) == 0:
                 self.ates()
                 self.last_shot_time = now


    def ates(self):
         # Reuse uzayliMermi for minion bullets
        mermi = uzayliMermi(self.rect.centerx, self.rect.bottom, self.level_no, self.difficulty) # Pass level and difficulty for speed
        self.mermi_grup.add(mermi)
        if self.minion_mermi_sesi: self.minion_mermi_sesi.play()


class WarningIndicator(pygame.sprite.Sprite):
    def __init__(self, x, y, duration=750, beam_type=False, target_type=False):
        super().__init__()
        self.image_original = load_image("warning.png") # Load user's warning image
        self.duration = duration
        self.spawn_time = pygame.time.get_ticks()

        if beam_type:
            # Make the warning a tall, thin rectangle for a beam
            warn_height = YUKSEKLIK - y # From boss bottom to screen bottom
            warn_width = 20 # Increased width for beam warning
            self.image = load_image("warning.png", scale=(warn_width, warn_height), smooth=True) # Load and scale directly, use smoothscale
            self.rect = self.image.get_rect(midtop=(x, y))
        elif target_type:
             # Make warning a targeted circle/sprite
             warn_size = 50
             self.image = load_image("warning.png", scale=(warn_size, warn_size), smooth=True) # Load and scale directly, use smoothscale
             self.rect = self.image.get_rect(center=(x, y)) # Center on target coordinates
        else: # Default/Spread - maybe doesn't need indicator? Or flash screen?
             # For now, don't create a sprite for default warnings
             self.kill() # Immediately remove if no specific type
             return

        # Make it semi-transparent or pulse?
        if self.image: # Check if image loaded successfully
            self.image.set_alpha(180) # Semi-transparent


    def update(self):
        now = pygame.time.get_ticks()
        # Optional: Add flashing effect
        elapsed = now - self.spawn_time
        if self.image: # Only try to flash if image exists
            if (elapsed // 100) % 2 == 0: # Faster flash every 100ms
                self.image.set_alpha(220) # More opaque when flashing
            else:
                self.image.set_alpha(100)

        # Remove after duration
        if now > self.spawn_time + self.duration:
            self.kill()

class BossMermi(pygame.sprite.Sprite):
    def __init__(self, x, y, angle=0, speed=8, beam=False, target_vector=None, duration=None):
        super().__init__()
        self.is_beam = beam # Flag to identify beam projectiles
        self.is_homing = False # Ensure homing is off
        self.original_image = None # Store original for potential rotation
        self.spawn_time = pygame.time.get_ticks()
        self.duration = duration # Duration for beam (None for normal bullets)


        if self.is_beam:
            beam_width = 30 # Wider beam
            beam_height = YUKSEKLIK # Beam goes to bottom of screen
            self.image = load_image("beam.png", scale=(beam_width, beam_height), smooth=True) # Load beam image, use smoothscale
            self.speed = 0 # Beam doesn't move
            self.velocity_y = 0
            self.velocity_x = 0
            self.rect = self.image.get_rect(midtop=(x, y)) # Beam starts from top center
        elif target_vector: # Targeted shot
            self.original_image = load_image("uzayli_mermi.png", scale=(20, 20), smooth=True) # Use smoothscale
            if self.original_image is None: # Handle case where image loading failed
                 self.original_image = pygame.Surface((20, 20)); self.original_image.fill(TURUNCU)

            dx = target_vector[0]
            dy = target_vector[1]
            distance = (dx**2 + dy**2)**0.5
            self.speed = speed # Use passed speed
            if distance > 0:
                self.velocity_x = (dx / distance) * self.speed
                self.velocity_y = (dy / distance) * self.speed
            else: # Avoid division by zero if target is exactly at start
                self.velocity_x = 0
                self.velocity_y = self.speed # Default to down

            # Calculate angle for rotation
            # Assuming original image points upwards (0, -1)
            angle_radians = math.atan2(-self.velocity_y, self.velocity_x) # Angle of velocity vector relative to positive x-axis (pygame y is inverted)
            angle_degrees = math.degrees(angle_radians)
            self.image = pygame.transform.rotate(self.original_image, angle_degrees - 90) # Rotate original image

            self.rect = self.image.get_rect(center=(x, y)) # Position based on center
        else: # Spread shot (using angle)
             self.original_image = load_image("uzayli_mermi.png", scale=(20, 20), smooth=True) # Use smoothscale
             if self.original_image is None: # Handle case where image loading failed
                  self.original_image = pygame.Surface((20, 20)); self.original_image.fill(TURUNCU)

             self.speed = speed
             # For spread shot, angle is relative to downward vector (0, 1)
             # Create a vector (0, 1), rotate it by the angle
             original_vector = pygame.math.Vector2(0, 1)
             rotated_vector = original_vector.rotate(-angle) # Negative angle for clockwise rotation
             self.velocity_x = rotated_vector.x * self.speed
             self.velocity_y = rotated_vector.y * self.speed
             # Rotate image based on the final velocity vector
             angle_degrees = math.degrees(math.atan2(-self.velocity_y, self.velocity_x)) # Angle of velocity vector relative to positive x-axis
             self.image = pygame.transform.rotate(self.original_image, angle_degrees - 90)

             self.rect = self.image.get_rect(center=(x, y)) # Position based on center


        self.precise_x = float(self.rect.centerx)
        self.precise_y = float(self.rect.centery)


    def update(self):
        now = pygame.time.get_ticks()
        if self.is_beam and self.duration is not None and now - self.spawn_time > self.duration:
             self.kill() # Remove beam after its duration
             return # Stop further updates for the beam

        self.precise_x += self.velocity_x
        self.precise_y += self.velocity_y
        self.rect.centerx = round(self.precise_x)
        self.rect.centery = round(self.precise_y)

        # Kill if it goes off screen (adjusted for beam)
        if not self.is_beam and (self.rect.bottom < 0 or self.rect.top > YUKSEKLIK or self.rect.left > GENISLIK or self.rect.right < 0):
            self.kill()

# Removed BossHomingMermi class as per user request

class SwordSlash(pygame.sprite.Sprite):
    def __init__(self, centerx, bottom):
        super().__init__()
        # Scaled down sword image
        self.image = load_image("sword.png", scale=(80, 80), smooth=True) # Adjusted scale, use smoothscale
        self.rect = self.image.get_rect(centerx=centerx, bottom=bottom)
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 750 # Increased duration for parry effect (0.75 seconds)
        self.parry_sound = load_sound("parry.wav") # Load parry sound

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > self.duration:
            self.kill() # Remove the slash after its duration

    def play_parry_sound(self):
        if self.parry_sound:
            self.parry_sound.play()


class Oyun():
    def __init__(self, oyuncu, oyuncu_grup, uzayli_grup, oyuncu_mermi_grup, uzayli_mermi_grup):
        # Game state and score
        self.bolum_no = 1
        self.puan = 0

        # Load game state and settings
        self.high_score, self.boss_unlocked, self.music_volume, self.sfx_volume, self.difficulty, self.set_fps = load_game_state()

        self.game_state = GameState.MAIN_MENU
        self.max_levels = 10 # <<< Increased max levels

        # Core game groups
        self.oyuncu = oyuncu
        self.oyuncu_grup = oyuncu_grup
        self.uzayli_grup = uzayli_grup
        self.oyuncu_mermi_grup = oyuncu_mermi_grup
        self.uzayli_mermi_grup = uzayli_mermi_grup
        self.boss_grup = pygame.sprite.GroupSingle() # For the boss
        self.boss_mermi_grup = pygame.sprite.Group() # Boss projectiles
        self.warning_grup = pygame.sprite.Group() # Attack warnings
        self.sword_slash_grup = pygame.sprite.GroupSingle() # For the sword slash animation
        self.minion_grup = pygame.sprite.Group() # Group for boss minions

        # Fullscreen state
        self.is_fullscreen = False
        self.current_display_flags = initial_display_flags # Store initial flags

        # Cheat code input
        self.cheat_code_input = ""
        self.cheat_code = "bilisim" # The actual cheat code
        self.cheat_input_active = False # Flag to control cheat input

        # Boss unlocked message
        self.show_boss_unlocked_message = False
        self.boss_unlocked_message_start_time = 0
        self.boss_unlocked_message_duration = 4000 # 4 seconds

        # --- Upgrade System Attributes ---
        # Added 'parry' skill and cooldown upgrade
        self.upgrade_levels = {"speed": 0, "fire_rate": 0, "max_bullets": 0, "lives": 0, "parry": 0, "parry_cooldown": 0}
        self.upgrade_costs = {
            "speed": [1000, 2500, 5000, 10000, 18000], # Added more levels/costs
            "fire_rate": [1500, 3000, 6000, 12000, 20000],
            "max_bullets": [2000, 4000, 8000, 15000],
            "lives": [5000],
            "parry": [7000], # Cost for the parry skill
            "parry_cooldown": [3000, 6000, 10000] # Costs for parry cooldown reduction
        }
        self.upgrade_max_levels = {k: len(v) for k, v in self.upgrade_costs.items()}
        self.apply_upgrades() # Apply initial upgrades based on loaded state

        # --- Arkaplanlar (Backgrounds) ---
        self.arka_planlar = []
        # Load background images from 1 to max_levels (or up to 10 if fewer levels)
        for i in range(1, min(self.max_levels, 10) + 1): # Try loading up to 10 backgrounds
             filename = f"arka_plan{i}.png"
             # Check for jpg as well, although previous code only explicitly checked for 2.jpg
             if not os.path.exists(os.path.join("assets", filename)):
                 filename = f"arka_plan{i}.jpg"
                 if not os.path.exists(os.path.join("assets", filename)):
                      print(f"Uyarı: 'assets/{filename}' bulunamadı.")
                      continue # Skip if neither found

             img = load_image(filename, scale=(GENISLIK, YUKSEKLIK), convert_alpha=False) # Backgrounds usually don't need alpha
             self.arka_planlar.append(img)

        # Fallback if no backgrounds loaded
        if len(self.arka_planlar) == 0: # Critical error if no backgrounds
             print("HATA: Hiç arkaplan yüklenemedi! Oyun kapatılıyor.")
             pygame.quit(); exit()
        # If fewer backgrounds than max_levels, repeat the last loaded one
        while len(self.arka_planlar) < self.max_levels:
             print(f"Uyarı: {self.max_levels} arkaplan bekleniyor, sadece {len(self.arka_planlar)} bulundu. Son arkaplan tekrarlanacak.")
             self.arka_planlar.append(self.arka_planlar[-1])


        # Tebrikler image
        self.tebrikler = load_image("tebrikler.png", scale=(GENISLIK, YUKSEKLIK))

        # Skill icon for the corner display
        self.sword_icon = load_image("sword.png", scale=(50, 50), smooth=True) # Smaller scale for HUD icon, use smoothscale

        # --- Sesler ---
        self.uzayli_vurus = load_sound("uzayli_vurus.wav")
        self.oyuncu_vurus = load_sound("oyuncu_vurus.wav")
        self.oyuncu_mermi_sesi = load_sound("oyuncu_mermi.wav")
        self.uzayli_mermi_sesi = load_sound("uzayli_mermi.wav")
        self.upgrade_sound = load_sound("oyuncu_vurus.wav") # Reuse a sound
        self.cant_afford_sound = load_sound("uzayli_vurus.wav") # Reuse a sound
        self.level_complete_sound = load_sound("oyuncu_mermi.wav") # Sound for level clear
        self.boss_death_sound = load_sound("oyuncu_vurus.wav") # Reuse or add boss death sound
        self.parry_sound = load_sound("parry.wav") # Load the parry sound
        self.boss_laugh_sound = load_sound("bosslaugh.wav") # Load boss laugh sound
        self.summon_sound = load_sound("summon.wav") # Minion summon sound
        self.enraged_sound = load_sound("enraged.wav") # Enraged sound
        self.defeat_sound = load_sound("defeat.wav") # Load defeat sound
        print(f"Enraged sound loaded: {self.enraged_sound}") # Debug print after loading
        print(f"Defeat sound loaded: {self.defeat_sound}") # Debug print after loading


        # Assign player sound here now that sounds are loaded
        self.oyuncu.mermi_sesi = self.oyuncu_mermi_sesi
        self.oyuncu.parry_sound = self.parry_sound # Assign parry sound to player
        self.oyuncu.oyun_ref = self # Pass reference to Oyun to player

        # Enrage Visual Effects
        self.is_enraged_visual = False
        self.enraged_overlay = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
        self.enraged_overlay.fill(ENRAGE_OVERLAY_COLOR)
        self.shake_intensity = 0
        self.shake_duration = 0
        self.shake_timer = 0

        # Cutscene timers
        self.cutscene_start_time = 0
        self.barrage_cutscene_duration = 2000 # 2 seconds for the barrage cutscene (Renamed for clarity)

        # Background Music
        self.background_music_path = "assets/arka_plan_sarki.wav"
        try:
            pygame.mixer.music.load(self.background_music_path)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Arkaplan müziği yüklenemedi: {e}")

        # Apply initial volume settings
        self.apply_volume()
        print(f"Initial SFX Volume applied: {self.sfx_volume}") # Debug print

        # Apply initial difficulty settings
        self.apply_difficulty_settings()


    def stop_all_sounds(self):
        """Stops all currently playing sound effects."""
        if self.uzayli_vurus: self.uzayli_vurus.stop()
        if self.oyuncu_vurus: self.oyuncu_vurus.stop()
        if self.oyuncu_mermi_sesi: self.oyuncu_mermi_sesi.stop()
        if self.uzayli_mermi_sesi: self.uzayli_mermi_sesi.stop()
        if self.upgrade_sound: self.upgrade_sound.stop()
        if self.cant_afford_sound: self.cant_afford_sound.stop()
        if self.level_complete_sound: self.level_complete_sound.stop()
        if self.boss_death_sound: self.boss_death_sound.stop()
        if self.parry_sound: self.parry_sound.stop()
        if self.boss_laugh_sound: self.boss_laugh_sound.stop()
        if self.summon_sound: self.summon_sound.stop()
        if self.enraged_sound: self.enraged_sound.stop()
        if self.defeat_sound: self.defeat_sound.stop()
        # Stop boss specific sounds if boss exists
        if self.boss_grup.sprite:
             if self.boss_grup.sprite.hit_sound: self.boss_grup.sprite.hit_sound.stop()
             if self.boss_grup.sprite.shoot_sound: self.boss_grup.sprite.shoot_sound.stop()
             if self.boss_grup.sprite.warning_sound: self.boss_grup.sprite.warning_sound.stop()
             if self.boss_grup.sprite.beam_sound: self.boss_grup.sprite.beam_sound.stop()
             if self.boss_grup.sprite.summon_sound: self.boss_grup.sprite.summon_sound.stop()
             if self.boss_grup.sprite.enraged_sound: self.boss_grup.sprite.enraged_sound.stop()


    def apply_volume(self):
        """Applies the current volume settings to music and sound effects."""
        pygame.mixer.music.set_volume(self.music_volume)
        sounds = [self.uzayli_vurus, self.oyuncu_vurus, self.oyuncu_mermi_sesi,
                  self.uzayli_mermi_sesi, self.upgrade_sound, self.cant_afford_sound,
                  self.level_complete_sound, self.boss_death_sound, self.parry_sound,
                  self.boss_laugh_sound, self.summon_sound, self.enraged_sound, self.defeat_sound] # Include new sounds
        # Also apply to sounds within Boss class if they are loaded separately
        if self.boss_grup.sprite:
             boss_sounds = [self.boss_grup.sprite.hit_sound, self.boss_grup.sprite.shoot_sound, self.boss_grup.sprite.warning_sound,
                            self.boss_grup.sprite.beam_sound, self.boss_grup.sprite.summon_sound, self.boss_grup.sprite.enraged_sound] # Include new sounds
             sounds.extend(boss_sounds)

        for sound in sounds:
             if sound: sound.set_volume(self.sfx_volume)

    def apply_difficulty_settings(self):
        """Applies current difficulty settings to game elements."""
        # Player health is handled in reset and apply_upgrades
        # Enemy speed and fire rate are handled when spawning enemies/boss, but let's update existing ones if possible
        for uzayli in self.uzayli_grup.sprites():
             # Re-calculate speed and shoot chance based on new difficulty
             uzayli.hiz = 1 + (self.bolum_no // 2) # Base speed based on level
             if self.difficulty == Difficulty.EASY: uzayli.hiz = max(1, uzayli.hiz * 0.8)
             elif self.difficulty == Difficulty.HARD: uzayli.hiz *= 1.2
             elif self.difficulty == Difficulty.REVENGEANCE: uzayli.hiz *= 1.5

             uzayli.shoot_chance = max(1, 6 - (self.bolum_no // 2)) # Base chance based on level
             if self.difficulty == Difficulty.EASY: uzayli.shoot_chance = max(1, uzayli.shoot_chance * 1.5) # Less frequent
             elif self.difficulty == Difficulty.HARD: uzayli.shoot_chance = max(1, uzayli.shoot_chance * 0.8) # More frequent
             elif self.difficulty == Difficulty.REVENGEANCE: uzayli.shoot_chance = max(1, uzayli.shoot_chance * 0.5) # Much more frequent


        if self.boss_grup.sprite:
             self.boss_grup.sprite.difficulty = self.difficulty # Update boss difficulty
             self.boss_grup.sprite.apply_difficulty_settings() # Re-apply boss specific difficulty settings
             # Update current speed and attack delay based on re-applied settings
             self.boss_grup.sprite.speed = self.boss_grup.sprite.base_speed
             self.boss_grup.sprite.attack_delay = self.boss_grup.sprite.base_attack_delay


        for minion in self.minion_grup.sprites():
             minion.difficulty = self.difficulty # Update minion difficulty
             # Re-calculate fire rate based on new difficulty
             minion.fire_rate = random.randint(700, 1300) # Base fire rate
             if self.difficulty == Difficulty.EASY: minion.fire_rate = random.randint(1000, 1800)
             elif self.difficulty == Difficulty.HARD: minion.fire_rate = random.randint(500, 1000)
             elif self.difficulty == Difficulty.REVENGEANCE: minion.fire_rate = random.randint(300, 800)


        # Player lives are handled in reset and apply_upgrades
        self.apply_upgrades() # Reapply upgrades to ensure lives are correct for Insta Death


    def apply_upgrades(self):
        self.oyuncu.hiz = 8 + self.upgrade_levels["speed"] * 1.5 # Speed increases more
        self.oyuncu.shoot_delay = max(80, 300 - self.upgrade_levels["fire_rate"] * 35) # Faster rate potential
        self.oyuncu.max_bullets = 2 + self.upgrade_levels["max_bullets"] * 2 # Max bullets increases by 2 per upgrade level
        # Lives upgrade directly increases max lives, but overridden by Insta Death
        base_lives = 5 + self.upgrade_levels["lives"]
        if self.difficulty == Difficulty.INSTA_DEATH:
             self.oyuncu.can = 1
        else:
             self.oyuncu.can = base_lives

        self.oyuncu.has_parry = self.upgrade_levels["parry"] > 0 # Player has parry skill if level > 0
        # Parry cooldown reduction: Base cooldown - 0.5 seconds per upgrade level
        self.oyuncu.parry_cooldown = max(1000, 6000 - self.upgrade_levels["parry_cooldown"] * 500) # Minimum 1 second cooldown


    def get_upgrade_cost(self, upgrade_name):
        current_level = self.upgrade_levels[upgrade_name]
        max_level = self.upgrade_max_levels.get(upgrade_name, 0) # Use .get for safety
        if current_level >= max_level: return None
        return self.upgrade_costs[upgrade_name][current_level]

    def purchase_upgrade(self, upgrade_name):
        cost = self.get_upgrade_cost(upgrade_name)
        if cost is None:
            if self.cant_afford_sound: self.cant_afford_sound.play()
            return False
        if self.puan >= cost:
            self.puan -= cost
            self.upgrade_levels[upgrade_name] += 1
            # Apply upgrades that affect player stats immediately
            if upgrade_name in ["speed", "fire_rate", "max_bullets", "parry", "parry_cooldown", "lives"]:
                 self.apply_upgrades()
            if self.upgrade_sound: self.upgrade_sound.play()
            return True
        else:
            if self.cant_afford_sound: self.cant_afford_sound.play()
            return False

    def draw_upgrade_screen(self):
        # Screen shown between levels
        pencere.fill((20, 20, 80))
        render_text("BÖLÜM TAMAMLANDI!", oyun_font_orta, YESIL, pencere, GENISLIK // 2, 30)
        render_text("YÜKSELTMELER", oyun_font_buyuk, YESIL, pencere, GENISLIK // 2, 80)
        render_text(f"Puan: {self.puan}", oyun_font_orta, SARI, pencere, GENISLIK // 2, 150)

        y_pos = 230; spacing = 80 # Reduced spacing slightly
        # Draw upgrade options (same as before)
        # 1. Speed
        level_speed = self.upgrade_levels["speed"]; cost_speed = self.get_upgrade_cost("speed")
        cost_text_speed = f"Bedel: {cost_speed}" if cost_speed is not None else "MAKS SEVİYE"
        render_text(f"[1] Hız Sv {level_speed}/{self.upgrade_max_levels['speed']} ({self.oyuncu.hiz})", oyun_font_kucuk, BEYAZ, pencere, GENISLIK // 2, y_pos)
        render_text(cost_text_speed, oyun_font_minik, SARI if cost_speed is not None else KIRMIZI, pencere, GENISLIK // 2, y_pos + 30) # Adjusted y pos
        y_pos += spacing

        # 2. Fire Rate
        level_fire_rate = self.upgrade_levels["fire_rate"]; cost_fire_rate = self.get_upgrade_cost("fire_rate")
        cost_text_fire_rate = f"Bedel: {cost_fire_rate}" if cost_fire_rate is not None else "MAKS SEVİYE"
        render_text(f"[2] Atış Hızı Sv {level_fire_rate}/{self.upgrade_max_levels['fire_rate']} ({self.oyuncu.shoot_delay}ms)", oyun_font_kucuk, BEYAZ, pencere, GENISLIK // 2, y_pos)
        render_text(cost_text_fire_rate, oyun_font_minik, SARI if cost_fire_rate is not None else KIRMIZI, pencere, GENISLIK // 2, y_pos + 30)
        y_pos += spacing

        # 3. Max Bullets
        level_max_bullets = self.upgrade_levels["max_bullets"]; cost_max_bullets = self.get_upgrade_cost("max_bullets")
        cost_text_max_bullets = f"Bedel: {cost_max_bullets}" if cost_max_bullets is not None else "MAKS SEVİYE"
        render_text(f"[3] Maks Mermi Sv {level_max_bullets}/{self.upgrade_max_levels['max_bullets']} ({self.oyuncu.max_bullets})", oyun_font_kucuk, BEYAZ, pencere, GENISLIK // 2, y_pos)
        render_text(cost_text_max_bullets, oyun_font_minik, SARI if cost_max_bullets is not None else KIRMIZI, pencere, GENISLIK // 2, y_pos + 30)
        y_pos += spacing

        # 4. Buy Life
        level_lives = self.upgrade_levels["lives"]; cost_lives = self.get_upgrade_cost("lives")
        cost_text_lives = f"Bedel: {cost_lives}" if cost_lives is not None else "MAKS SEVİYE"
        # Display current lives based on difficulty
        current_lives_display = self.oyuncu.can if self.difficulty != Difficulty.INSTA_DEATH else "1 (Insta Death)"
        render_text(f"[4] Can Satın Al Sv {level_lives}/{self.upgrade_max_levels['lives']} (Mevcut: {current_lives_display})", oyun_font_kucuk, BEYAZ, pencere, GENISLIK // 2, y_pos)
        render_text(cost_text_lives, oyun_font_minik, SARI if cost_lives is not None else KIRMIZI, pencere, GENISLIK // 2, y_pos + 30)
        y_pos += spacing

        # 5. Parry Skill
        level_parry = self.upgrade_levels["parry"]; cost_parry = self.get_upgrade_cost("parry")
        cost_text_parry = f"Bedel: {cost_parry}" if cost_parry is not None else "SATIN ALINDI" # Changed to indicate purchased
        render_text(f"[5] Kılıç Savuşturma Sv {level_parry}/{self.upgrade_max_levels['parry']} (Sağ Tık)", oyun_font_kucuk, BEYAZ, pencere, GENISLIK // 2, y_pos) # Mention Right Click
        render_text(cost_text_parry, oyun_font_minik, SARI if cost_parry is not None else YESIL, pencere, GENISLIK // 2, y_pos + 30) # Green if purchased
        y_pos += spacing

        # 6. Parry Cooldown Reduction
        level_parry_cooldown = self.upgrade_levels["parry_cooldown"]; cost_parry_cooldown = self.get_upgrade_cost("parry_cooldown")
        cost_text_parry_cooldown = f"Bedel: {cost_parry_cooldown}" if cost_parry_cooldown is not None else "MAKS SEVİYE"
        render_text(f"[6] Savuşturma Cooldown Sv {level_parry_cooldown}/{self.upgrade_max_levels['parry_cooldown']} ({self.oyuncu.parry_cooldown // 1000}s)", oyun_font_kucuk, BEYAZ, pencere, GENISLIK // 2, y_pos)
        render_text(cost_text_parry_cooldown, oyun_font_minik, SARI if cost_parry_cooldown is not None else KIRMIZI, pencere, GENISLIK // 2, y_pos + 30)
        # Display current cooldown next to the upgrade option
        render_text(f"Mevcut Cooldown: {self.oyuncu.parry_cooldown // 1000}s", oyun_font_minik, SARI, pencere, GENISLIK // 2 + 200, y_pos + 30, center_y=True)
        y_pos += spacing


        # Exit instruction
        render_text("Sonraki Bölüme Geçmek İçin ENTER", oyun_font_orta, YESIL, pencere, GENISLIK // 2, YUKSEKLIK - 100)
        pygame.display.flip()

    def handle_upgrade_input(self, event):
         # Input for the between-level upgrade screen
         if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: self.purchase_upgrade("speed")
            elif event.key == pygame.K_2: self.purchase_upgrade("fire_rate")
            elif event.key == pygame.K_3: self.purchase_upgrade("max_bullets")
            elif event.key == pygame.K_4: self.purchase_upgrade("lives") # Lives purchase handled by purchase_upgrade now
            elif event.key == pygame.K_5: self.purchase_upgrade("parry") # Handle parry purchase
            elif event.key == pygame.K_6: self.purchase_upgrade("parry_cooldown") # Handle parry cooldown upgrade
            elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                # Proceed to the next level (or win screen)
                if self.bolum_no > self.max_levels: # Should have already been checked, but double-check
                    self.check_win_condition()
                else:
                    self.game_state = GameState.LEVEL_TRANSITION


    def draw_main_menu(self):
        pencere.blit(self.arka_planlar[0], (0, 0)) # Use first background for menu
        render_text("Uzay İstilası", oyun_font_buyuk, YESIL, pencere, GENISLIK // 2, YUKSEKLIK // 4)

        # Menu options positioning
        menu_y_start = YUKSEKLIK // 2 # Corrected typo here
        line_spacing = 60
        option_index = 0

        render_text("Başlamak için ENTER", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, menu_y_start + option_index * line_spacing)
        option_index += 1

        # Add Boss Rush option if unlocked
        if self.boss_unlocked:
            render_text("Boss Savaşı için B", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, menu_y_start + option_index * line_spacing)
            option_index += 1


        render_text("Seçenekler için O", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, menu_y_start + option_index * line_spacing)
        option_index += 1

        render_text("Çıkmak için ESC", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, menu_y_start + option_index * line_spacing)

        # Cheat code prompt (only shown if cheat input is active)
        if self.cheat_input_active:
            render_text(f"Cheat Code: {self.cheat_code_input}", oyun_font_minik, SARI, pencere, GENISLIK // 2, YUKSEKLIK - 80) # Centered cheat input

        render_text(f"Yüksek Skor: {self.high_score}", oyun_font_kucuk, PEMBE, pencere, GENISLIK // 2, YUKSEKLIK - 50)
        render_text("Cheat için F1", oyun_font_minik, SARI, pencere, GENISLIK // 2, YUKSEKLIK - 20) # Hint for cheat code

        pygame.display.flip()

    def draw_pause_screen(self):
        # Removed upgrade access from here
        overlay = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        pencere.blit(overlay, (0, 0))
        render_text("DURAKLATILDI", oyun_font_buyuk, KIRMIZI, pencere, GENISLIK // 2, YUKSEKLIK // 4 - 20)
        render_text("Devam etmek için P", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, YUKSEKLIK // 2 - 30)
        render_text("Seçenekler için O", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, YUKSEKLIK // 2 + 30)
        render_text("Ana Menü için M", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, YUKSEKLIK // 2 + 90)
        pygame.display.flip()

    def draw_options_screen(self):
        pencere.fill(KOYU_MAVI) # Dark blue background for options
        render_text("SEÇENEKLER", oyun_font_buyuk, BEYAZ, pencere, GENISLIK // 2, 50)
        y_pos = 150
        spacing = 70 # Spacing between options

        # Difficulty Option
        render_text("Zorluk:", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, y_pos)
        difficulty_text = f"{self.difficulty.upper()}"
        render_text(difficulty_text, oyun_font_kucuk, SARI, pencere, GENISLIK // 2, y_pos + 40)
        render_text("<- (Z Tuşu) / (C Tuşu) ->", oyun_font_minik, KIRMIZI, pencere, GENISLIK // 2, y_pos + 70)
        y_pos += spacing * 2 # More space after difficulty

        # FPS Option
        render_text("FPS:", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, y_pos)
        render_text(f"{self.set_fps}", oyun_font_kucuk, SARI, pencere, GENISLIK // 2, y_pos + 40)
        render_text("<- (F Tuşu) / (G Tuşu) ->", oyun_font_minik, KIRMIZI, pencere, GENISLIK // 2, y_pos + 70)
        y_pos += spacing * 2

        # Music Volume
        render_text("Müzik Sesi:", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, y_pos)
        render_text(f"{int(self.music_volume * 100)}%", oyun_font_kucuk, SARI, pencere, GENISLIK // 2, y_pos+40)
        render_text("<- (Sol Ok) / (Sağ Ok) ->", oyun_font_minik, KIRMIZI, pencere, GENISLIK // 2, y_pos+70)
        y_pos += spacing * 2

        # SFX Volume
        render_text("Efekt Sesi:", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, y_pos)
        render_text(f"{int(self.sfx_volume * 100)}%", oyun_font_kucuk, SARI, pencere, GENISLIK // 2, y_pos+40)
        render_text("<- (A Tuşu) / (D Tuşu) ->", oyun_font_minik, KIRMIZI, pencere, GENISLIK // 2, y_pos+70)
        y_pos += spacing * 2


        render_text("Tam Ekran (F11)", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, YUKSEKLIK - 150) # Added fullscreen info
        render_text("Geri dönmek için ESC", oyun_font_orta, YESIL, pencere, GENISLIK // 2, YUKSEKLIK - 100)
        pygame.display.flip()

    def handle_options_input(self, event):
         if event.type == pygame.KEYDOWN:
            # Volume controls
            if event.key == pygame.K_LEFT: self.music_volume = round(max(0.0, self.music_volume - 0.1), 1); self.apply_volume()
            elif event.key == pygame.K_RIGHT: self.music_volume = round(min(1.0, self.music_volume + 0.1), 1); self.apply_volume()
            elif event.key == pygame.K_a: self.sfx_volume = round(max(0.0, self.sfx_volume - 0.1), 1); self.apply_volume()
            elif event.key == pygame.K_d: self.sfx_volume = round(min(1.0, self.sfx_volume + 0.1), 1); self.apply_volume()

            # Difficulty controls
            elif event.key == pygame.K_z: self.change_difficulty(-1) # Cycle difficulty left
            elif event.key == pygame.K_c: self.change_difficulty(1) # Cycle difficulty right

            # FPS controls
            elif event.key == pygame.K_f: self.change_fps(-10) # Decrease FPS by 10
            elif event.key == pygame.K_g: self.change_fps(10) # Increase FPS by 10


            elif event.key == pygame.K_F11: self.toggle_fullscreen() # Handle fullscreen toggle
            elif event.key == pygame.K_ESCAPE:
                 # Save settings before returning
                 save_game_state(self.high_score, self.boss_unlocked, self.music_volume, self.sfx_volume, self.difficulty, self.set_fps)
                 # Return to the state we came from
                 if hasattr(self, 'came_from_state'):
                     self.game_state = self.came_from_state
                     delattr(self, 'came_from_state')
                 else:
                     # Default back to main menu or pause if came_from_state is not set
                     if self.game_state == GameState.OPTIONS: # If we were in options
                          self.game_state = GameState.MAIN_MENU # Go to main menu
                     else: # Otherwise, maybe go back to paused? Depends on flow
                         self.game_state = GameState.PAUSED # Assume pause if not specified

    def change_difficulty(self, direction):
        """Cycles through difficulty levels."""
        difficulties = [Difficulty.EASY, Difficulty.NORMAL, Difficulty.HARD, Difficulty.INSTA_DEATH, Difficulty.REVENGEANCE]
        current_index = difficulties.index(self.difficulty)
        new_index = (current_index + direction) % len(difficulties)
        self.difficulty = difficulties[new_index]
        print(f"Difficulty set to: {self.difficulty}") # Debug print
        self.apply_difficulty_settings() # Apply the new difficulty

    def change_fps(self, amount):
        """Changes the target FPS."""
        self.set_fps = max(30, min(120, self.set_fps + amount)) # Limit FPS between 30 and 120
        print(f"FPS set to: {self.set_fps}") # Debug print


    def draw_game_over_screen(self):
        pencere.fill(SIYAH)
        render_text("OYUN BİTTİ!", oyun_font_buyuk, KIRMIZI, pencere, GENISLIK // 2, YUKSEKLIK // 3)
        render_text(f"Skorunuz: {self.puan}", oyun_font_orta, PEMBE, pencere, GENISLIK // 2, YUKSEKLIK // 2)
        if self.puan > self.high_score:
             render_text(f"Yeni Yüksek Skor: {self.puan}", oyun_font_orta, YESIL, pencere, GENISLIK // 2, YUKSEKLIK // 2 + 60)
        else:
            render_text(f"Yüksek Skor: {self.high_score}", oyun_font_orta, PEMBE, pencere, GENISLIK // 2, YUKSEKLIK // 2 + 60)
        render_text("Ana Menü için ENTER", oyun_font_orta, BEYAZ, pencere, GENISLIK // 2, YUKSEKLIK * 2 // 3 + 20)
        pygame.display.flip()

    def draw_win_screen(self):
        pencere.blit(self.tebrikler, (0, 0))
        render_text(f"Tebrikler! Skorunuz: {self.puan}", oyun_font_orta, SIYAH, pencere, GENISLIK // 2, 50)
        if self.puan > self.high_score:
            render_text(f"Yeni Yüksek Skor: {self.puan}!", oyun_font_kucuk, YESIL, pencere, GENISLIK // 2, 110)
        render_text("Ana Menü için ENTER", oyun_font_orta, SIYAH, pencere, GENISLIK // 2, YUKSEKLIK - 100)
        pygame.display.flip()

    def draw_level_transition_screen(self):
        pencere.fill(SIYAH)
        level_text = f"Bölüm {self.bolum_no}"
        if self.bolum_no == 5: level_text += " - BOSS!"
        render_text(f"{level_text} Başılıyor!", oyun_font_buyuk, YESIL, pencere, GENISLIK // 2, YUKSEKLIK // 2 - 50)
        pygame.display.flip()
        pygame.time.wait(2500) # Slightly longer wait for transitions
        self.game_state = GameState.PLAYING


    def update(self):
        # Update logic based on the current state
        if self.game_state == GameState.PLAYING:
            # Player related updates
            self.oyuncu_grup.update() # Passive updates for player if any
            self.oyuncu_mermi_grup.update()
            self.sword_slash_grup.update() # Update sword slash animation

            # Check if it's the boss level
            if self.bolum_no == 5:
                self.boss_grup.update() # Update boss movement, attacks
                self.minion_grup.update() # Update minions
                self.boss_mermi_grup.update() # Update boss projectiles
                self.warning_grup.update() # Update warnings
                self.temas() # Handle collisions
                # Win condition is now handled by boss death triggering cutscene
            else:
                # Normal alien level logic
                self.uzayli_grup.update() # Alien firing logic
                self.uzayli_mermi_grup.update() # Alien projectiles
                self.uzayli_konum_degistirme() # Alien swarm movement
                self.temas() # Handle collisions
                self.tamamlandi() # Check if aliens cleared

        elif self.game_state == GameState.BOSS_BARRAGE_CUTSCENE:
             # Update player barrage fire
             self.oyuncu_grup.update() # Update player (handles barrage firing)
             self.oyuncu_mermi_grup.update() # Update player bullets

             # Check barrage duration
             now = pygame.time.get_ticks()
             # Corrected: Use barrage_cutscene_duration from Oyun class
             if now - self.cutscene_start_time > self.barrage_cutscene_duration:
                  # End barrage and transition
                  self.oyuncu.is_barraging = False # Stop barrage mode
                  self.oyuncu_mermi_grup.empty() # Clear remaining bullets
                  self.boss_grup.empty() # Remove the boss sprite after barrage
                  self.minion_grup.empty() # Remove any remaining minions
                  self.warning_grup.empty() # Clear warnings
                  if self.defeat_sound: self.defeat_sound.stop() # Stop defeat sound
                  self._revert_enraged_visuals() # Revert red screen and shake
                  self.tamamlandi() # Check win condition (should lead to upgrades/win)
                  # Resume background music
                  try:
                      pygame.mixer.music.load(self.background_music_path)
                      pygame.mixer.music.play(-1)
                      self.apply_volume() # Reapply volume
                  except pygame.error as e:
                       print(f"Arkaplan müziği yüklenemedi: {e}")


        # Update boss unlocked message timer
        if self.show_boss_unlocked_message and pygame.time.get_ticks() - self.boss_unlocked_message_start_time > self.boss_unlocked_message_duration:
            self.show_boss_unlocked_message = False

        # Update screen shake timer
        if self.shake_intensity > 0:
            self.shake_timer -= saat.get_time() # Decrease shake timer by delta time
            if self.shake_timer <= 0:
                self.shake_intensity = 0 # Stop shaking when timer is up
                # Ensure screen position is reset after shake stops
                if self.game_state not in [GameState.BOSS_DEFEATED_CUTSCENE, GameState.BOSS_BARRAGE_CUTSCENE]:
                     pass # No need to adjust screen position here, drawing handles it


    def cizdir(self):
        # Calculate screen shake offset
        shake_offset_x = 0
        shake_offset_y = 0
        if self.shake_intensity > 0:
            shake_offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_offset_y = random.randint(-self.shake_intensity, self.shake_intensity)

        # Draw a random background for the current level from the loaded ones
        if self.bolum_no > 0 and self.bolum_no <= len(self.arka_planlar):
             # Use a consistent background for each level number if available
             bg_index = self.bolum_no - 1
             pencere.blit(self.arka_planlar[bg_index], (shake_offset_x, shake_offset_y))
        elif len(self.arka_planlar) > 0:
             # If level number exceeds loaded backgrounds, use a random one from available
             random_bg_index = random.randint(0, len(self.arka_planlar) - 1)
             pencere.blit(self.arka_planlar[random_bg_index], (shake_offset_x, shake_offset_y))
        else:
             # Fallback if no backgrounds were loaded (shouldn't happen due to check in init)
             pencere.fill(SIYAH) # Or some default color


        # Draw HUD (Score, Level, Lives) - HUD should not shake
        render_text("Skor:" + str(self.puan), oyun_font_orta, PEMBE, pencere, 10, 10, top_left=True)
        level_display = f"Bölüm:{self.bolum_no}"
        if self.bolum_no == 5 and self.boss_grup.sprite: level_display += " BOSS"
        render_text(level_display, oyun_font_orta, PEMBE, pencere, GENISLIK - 10, 10, top_left=True) # Align right using rect later if needed
        # Display lives based on difficulty
        lives_display = str(self.oyuncu.can) if self.difficulty != Difficulty.INSTA_DEATH else "1 (Insta Death)"
        render_text("Can:" + lives_display, oyun_font_orta, KIRMIZI, pencere, 10, 60, top_left=True) # Below score

        # Draw skill icon and cooldown if player has the skill - HUD should not shake
        if self.oyuncu.has_parry:
            icon_x = GENISLIK - 70 # Position in the top right corner
            icon_y = 70
            icon_rect = self.sword_icon.get_rect(topleft=(icon_x, icon_y))

            # Determine background color based on cooldown
            cooldown_remaining = self.oyuncu.get_parry_cooldown_remaining()

            if cooldown_remaining == 0:
                bg_color = YESIL_KOYU # Green when usable
            else:
                bg_color = KIRMIZI # Red when on cooldown

            # Draw background rectangle
            bg_rect = icon_rect.inflate(10, 10) # Slightly larger background
            bg_rect.topleft = (icon_rect.left - 5, icon_rect.top - 5) # Center background behind icon
            pygame.draw.rect(pencere, bg_color, bg_rect)

            # Draw sword icon
            pencere.blit(self.sword_icon, icon_rect)

            # Draw cooldown timer text if on cooldown
            if cooldown_remaining > 0:
                cooldown_seconds = cooldown_remaining // 1000 + 1 # Round up to the nearest second
                render_text(str(cooldown_seconds), oyun_font_minik, BEYAZ, pencere, icon_x + icon_rect.width + 15, icon_y + icon_rect.height // 2, center_y=True)


        # Draw boss unlocked message - HUD should not shake
        if self.show_boss_unlocked_message:
            message_text = "You can now play the boss in the menu."
            message_surface = oyun_font_kucuk.render(message_text, True, BEYAZ)
            message_rect = message_surface.get_rect(topleft=(20, YUKSEKLIK - 50)) # Position in the bottom left
            # Draw a background box
            box_padding = 10
            box_rect = message_rect.inflate(box_padding * 2, box_padding * 2)
            box_rect.topleft = (message_rect.left - box_padding, message_rect.top - box_padding)
            pygame.draw.rect(pencere, KOYU_MAVI, box_rect) # Dark blue background
            pygame.draw.rect(pencere, BEYAZ, box_rect, 2) # White border
            pencere.blit(message_surface, message_rect)


        # Draw Sprites based on level type with shake offset
        # Create a temporary surface to draw game elements onto, then blit with offset
        game_surface = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)

        self.oyuncu_grup.draw(game_surface)
        self.oyuncu_mermi_grup.draw(game_surface)
        self.sword_slash_grup.draw(game_surface) # Draw sword slash animation

        if self.bolum_no == 5:
            # Boss level drawing
            if self.boss_grup.sprite:
                self.boss_grup.sprite.draw(game_surface) # Use custom draw for potential effects
                # Health bar should not shake, draw directly on pencere
                self.boss_grup.sprite.draw_health_bar(pencere)
            self.minion_grup.draw(game_surface) # Draw minions
            self.boss_mermi_grup.draw(game_surface)
            self.warning_grup.draw(game_surface)
        else:
            # Normal alien level drawing
            self.uzayli_grup.draw(game_surface)
            self.uzayli_mermi_grup.draw(game_surface)

        # Blit the game surface onto the main window with shake offset
        pencere.blit(game_surface, (shake_offset_x, shake_offset_y))

        # Draw enrage overlay if active
        if self.is_enraged_visual:
             pencere.blit(self.enraged_overlay, (0, 0))

        # Draw cutscene specific elements
        if self.game_state == GameState.BOSS_DEFEATED_CUTSCENE:
             # Flash "Press X!"
             now = pygame.time.get_ticks()
             # Flash text every 500ms
             if (now // 500) % 2 == 0:
                  render_text("Press X!", oyun_font_buyuk, SARI, pencere, GENISLIK // 2, YUKSEKLIK // 2)


    def uzayli_konum_degistirme(self):
        kenara_gelen_var_mi = False
        for uzayli in self.uzayli_grup.sprites():
             # Adjusted win condition Y to be higher up the screen
             if uzayli.rect.right >= GENISLIK or uzayli.rect.left <= 0 or uzayli.rect.bottom >= YUKSEKLIK - 300: # Check if aliens reached a higher line
                 kenara_gelen_var_mi = True; break
        if kenara_gelen_var_mi:
             for uzayli in self.uzayli_grup.sprites():
                uzayli.yon *= -1
                # Increased step down slightly due to larger window
                uzayli.rect.y += 15 + self.bolum_no # Faster step down later, increased step
                # Keep aliens within horizontal bounds after changing direction
                if uzayli.rect.left < 0: uzayli.rect.left = 0
                if uzayli.rect.right > GENISLIK: uzayli.rect.right = GENISLIK

        # Check player area invasion *after* movement
        for uzayli in self.uzayli_grup.sprites():
            uzayli.rect.x += uzayli.yon * uzayli.hiz
            # Adjusted alien win condition based on new window height
            if uzayli.rect.bottom >= YUKSEKLIK - 300: # Player line is even higher
                self.oyun_durumu(game_over=True) # No return here, let the loop finish


    def temas(self):
        # --- Player Bullets ---
        if self.bolum_no == 5:
            # Player bullets vs Boss (only if boss is alive and not in cutscene)
            if self.boss_grup.sprite and self.game_state == GameState.PLAYING:
                hits = pygame.sprite.spritecollide(self.boss_grup.sprite, self.oyuncu_mermi_grup, True)
                if hits:
                    damage_per_bullet = 50 # How much damage each player bullet does
                    self.boss_grup.sprite.take_damage(damage_per_bullet * len(hits))
                    self.puan += 25 * len(hits) # Score for hitting boss

            # Player bullets vs Minions (only if minions are alive and not in cutscene)
            if self.game_state == GameState.PLAYING or self.game_state == GameState.BOSS_BARRAGE_CUTSCENE: # Allow hitting minions during barrage cutscene
                 minions_hit = pygame.sprite.groupcollide(self.oyuncu_mermi_grup, self.minion_grup, True, True)
                 if minions_hit:
                      if self.oyuncu_vurus: self.oyuncu_vurus.play() # Reuse sound
                      self.puan += 50 * len(minions_hit) # Score for hitting minions


        else:
            # Player bullets vs Aliens
            aliens_hit = pygame.sprite.groupcollide(self.oyuncu_mermi_grup, self.uzayli_grup, True, True)
            if aliens_hit:
                 if self.oyuncu_vurus: self.oyuncu_vurus.play()
                 self.puan += (100 * self.bolum_no) * len(aliens_hit)

        # --- Enemy/Boss/Minion Bullets vs Player ---
        # Check collision with sword slash first (only during PLAYING)
        if self.sword_slash_grup.sprite and self.game_state == GameState.PLAYING:
            # Alien bullets vs Sword Slash
            parried_alien_bullets = pygame.sprite.groupcollide(self.uzayli_mermi_grup, self.sword_slash_grup, True, False) # Remove bullet, keep slash
            if parried_alien_bullets:
                 self.sword_slash_grup.sprite.play_parry_sound() # Play parry sound

            # Boss bullets vs Sword Slash (including beams, excluding homing)
            # Create a temporary group of boss bullets that are NOT homing
            boss_bullets_to_parry = pygame.sprite.Group(*[b for b in self.boss_mermi_grup.sprites() if not getattr(b, 'is_homing', False)])
            parried_boss_bullets = pygame.sprite.groupcollide(boss_bullets_to_parry, self.sword_slash_grup, True, False)
            if parried_boss_bullets:
                 self.sword_slash_grup.sprite.play_parry_sound()

        # Then check collision with player for any remaining enemy bullets (only during PLAYING)
        if self.game_state == GameState.PLAYING:
             # Check alien bullets that were NOT parried
             alien_bullets_not_parried = [b for b in self.uzayli_mermi_grup.sprites()]
             hits_player_alien = pygame.sprite.spritecollide(self.oyuncu, pygame.sprite.Group(*alien_bullets_not_parried), True)

             # Check boss bullets that were NOT parried
             boss_bullets_not_parried = [b for b in self.boss_mermi_grup.sprites()]
             hits_player_boss = pygame.sprite.spritecollide(self.oyuncu, pygame.sprite.Group(*boss_bullets_not_parried), True)


             if hits_player_alien or hits_player_boss:
                 if self.uzayli_vurus: self.uzayli_vurus.play()
                 self.oyuncu.can -= len(hits_player_alien) + len(hits_player_boss) # Reduce health by the total number of bullets that hit


        # --- Warnings vs Player (Optional: Do warnings cause damage?) ---
        # if pygame.sprite.spritecollide(self.oyuncu, self.warning_grup, False): # Set last arg True if collision removes warning
            # print("Hit by warning!") # Damage or effect?

        # Check player death after all collision checks (only during PLAYING)
        if self.oyuncu.can <= 0 and self.game_state == GameState.PLAYING:
            self.oyun_durumu(game_over=True)


    def check_win_condition(self):
        # Called when advancing level number (after barrage cutscene for boss)
        if self.bolum_no > self.max_levels:
             if self.puan > self.high_score:
                 self.high_score = self.puan
             # Save game state when winning
             save_game_state(self.high_score, self.boss_unlocked, self.music_volume, self.sfx_volume, self.difficulty, self.set_fps)
             self.game_state = GameState.WIN
             # Revert enrage visuals on win
             self._revert_enraged_visuals()


    def bolum(self):
        # --- Clear previous level entities ---
        self.uzayli_grup.empty()
        self.uzayli_mermi_grup.empty()
        self.boss_grup.empty() # Clear boss if any
        self.boss_mermi_grup.empty()
        self.warning_grup.empty()
        self.sword_slash_grup.empty() # Clear sword slash animation
        self.minion_grup.empty() # Clear minions

        # --- Spawn entities for the new level ---
        if self.bolum_no == 5:
            # Spawn Boss
            # Pass the minion group reference and current difficulty to the boss
            boss = Boss(GENISLIK // 2, 80, self.boss_mermi_grup, self.warning_grup, self.oyuncu, self.minion_grup, self.difficulty)
            self.boss_grup.add(boss)
            self.apply_volume() # Reapply volume in case boss sounds were loaded
            # Reset enrage state and visuals for the new boss fight
            if self.boss_grup.sprite:
                 self.boss_grup.sprite.is_enraged = False
            self._revert_enraged_visuals() # Ensure visuals are off at start of boss fight

        else:
            # Spawn Aliens (adjust difficulty)
            rows = min(5, 3 + self.bolum_no // 2) # More rows later
            cols = min(10, 7 + self.bolum_no // 2) # More columns later
            alien_speed = min(1 + self.bolum_no // 2, 6) # Faster aliens later
            start_x = max(50, (GENISLIK - (cols * 64 + (cols - 1) * 10)) // 2) # Center formation, ensure space
            # Adjusted starting Y position to be higher
            start_y = 100 # Start aliens higher

            for i in range(cols):
                for j in range(rows):
                    x_pos = start_x + i * 74
                    y_pos = start_y + j * 70
                    # Pass difficulty to aliens
                    uzayli = Uzayli(x_pos, y_pos, alien_speed, self.uzayli_mermi_grup, self.uzayli_mermi_sesi, self.bolum_no, self.difficulty)
                    self.uzayli_grup.add(uzayli)

        # Apply difficulty settings after spawning entities to ensure their stats are correct
        self.apply_difficulty_settings()


    def oyun_durumu(self, game_over=False):
        # Player died or aliens reached bottom
        if game_over:
             if self.puan > self.high_score:
                 self.high_score = self.puan
             # Save game state when game over
             save_game_state(self.high_score, self.boss_unlocked, self.music_volume, self.sfx_volume, self.difficulty, self.set_fps)
             self.game_state = GameState.GAME_OVER
             # Revert enrage visuals on game over
             self._revert_enraged_visuals()
             self.stop_all_sounds() # Stop all sounds on game over

             if self.boss_laugh_sound: # Play boss laugh if player dies
                 # Stop any ongoing music before playing laugh
                 pygame.mixer.music.stop()
                 self.boss_laugh_sound.play()
                 # Wait for laugh to finish before going to game over screen
                 pygame.time.wait(int(self.boss_laugh_sound.get_length() * 1000))
                 # Resume music or play game over music if you have one
                 try:
                     pygame.mixer.music.load(self.background_music_path) # Load main music again
                     pygame.mixer.music.play(-1)
                     self.apply_volume() # Reapply volume
                 except pygame.error as e:
                     print(f"Arkaplan müziği yüklenemedi: {e}")


        # Clear projectiles, reset player
        self.uzayli_mermi_grup.empty()
        self.boss_mermi_grup.empty()
        self.warning_grup.empty()
        self.oyuncu_mermi_grup.empty()
        self.sword_slash_grup.empty() # Clear sword slash
        self.minion_grup.empty() # Clear minions
        self.oyuncu.reset()
        # Reset player's current health based on difficulty after reset
        self.apply_upgrades() # Reapply upgrades to set correct starting health


    def tamamlandi(self):
        # Check if level is complete (aliens cleared or boss defeated after barrage)
        level_cleared = False
        # Boss level completion is now triggered by the barrage cutscene ending
        if self.bolum_no == 5 and not self.boss_grup.sprite:
             level_cleared = True
             # Boss death sound is played in take_damage now

        elif self.bolum_no != 5 and not self.uzayli_grup:
            level_cleared = True

        if level_cleared:
            if self.level_complete_sound: self.level_complete_sound.play()
            self.bolum_no += 1
            # Check win condition *before* going to upgrades/transition
            if self.bolum_no > self.max_levels:
                self.check_win_condition() # This will set state to WIN
            else:
                # Go to Upgrade screen
                self.game_state = GameState.UPGRADES


    def oyun_reset(self):
        # Resets game for new playthrough (except high score and boss unlocked)
        self.puan = 0
        self.bolum_no = 1
        # Reset upgrade levels except lives and parry/cooldown if they are permanent
        # Assuming upgrades are permanent across games if boss is unlocked, otherwise reset all
        if not self.boss_unlocked: # Reset all upgrades if boss is not unlocked yet
             for key in self.upgrade_levels: self.upgrade_levels[key] = 0
        else: # Keep lives and parry and parry_cooldown upgrades if boss is unlocked
             upgrades_to_keep = ["lives", "parry", "parry_cooldown"]
             for key in self.upgrade_levels:
                  if key not in upgrades_to_keep:
                       self.upgrade_levels[key] = 0


        self.apply_upgrades()
        # Reset player's current health, but max health is set by apply_upgrades
        # self.oyuncu.can is set by apply_upgrades now
        self.oyuncu.reset()
        self.uzayli_grup.empty()
        self.uzayli_mermi_grup.empty()
        self.oyuncu_mermi_grup.empty()
        self.boss_grup.empty()
        self.boss_mermi_grup.empty()
        self.warning_grup.empty()
        self.sword_slash_grup.empty() # Clear sword slash
        self.minion_grup.empty() # Clear minions
        # State will be set to LEVEL_TRANSITION from MAIN_MENU

    def start_boss_fight(self):
        """Starts the boss fight directly."""
        self.oyun_reset() # Reset game state like a new game
        self.bolum_no = 5 # Set level directly to boss level
        self.game_state = GameState.LEVEL_TRANSITION # Go to transition screen before boss


    def toggle_fullscreen(self):
        """Toggles between fullscreen and windowed mode."""
        global pencere # Need to access the global window surface
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.current_display_flags = pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
            pencere = pygame.display.set_mode((GENISLIK, YUKSEKLIK), self.current_display_flags)
        else:
            self.current_display_flags = initial_display_flags # Use stored initial flags
            pencere = pygame.display.set_mode((GENISLIK, YUKSEKLIK), self.current_display_flags)

    def _apply_enraged_visuals(self):
        """Applies the enraged visual effects (red overlay and screen shake)."""
        self.is_enraged_visual = True
        self.shake_intensity = 5 # Set shake intensity
        self.shake_duration = 5000 # Shake for 5 seconds initially
        self.shake_timer = self.shake_duration

    def _revert_enraged_visuals(self):
        """Reverts the enraged visual effects."""
        self.is_enraged_visual = False
        self.shake_intensity = 0
        self.shake_timer = 0


class Oyuncu(pygame.sprite.Sprite):
    def __init__(self, oyuncu_mermi_grup, mermi_sesi):
        super().__init__()
        self.image = load_image("uzay_gemi.png", scale=(64, 64), smooth=True) # Use smoothscale
        # Adjusted starting position further due to increased window height
        self.rect = self.image.get_rect(centerx=GENISLIK // 2, bottom=YUKSEKLIK - 200)
        self.oyuncu_mermi_grup = oyuncu_mermi_grup
        self.mermi_sesi = mermi_sesi # Will be assigned by Oyun class
        self.parry_sound = None # Will be assigned by Oyun class
        self.oyun_ref = None # Reference to the Oyun object, assigned after creation

        # Base values (overwritten by upgrades and difficulty)
        self.hiz = 8
        # Adjusted shoot delay for alternate firing
        self.shoot_delay = 300 # Milliseconds between shots (this is now the delay between individual shots)
        self.max_bullets = 4 # Increased max bullets since firing two at once
        self.last_shot_time = 0 # Time of the very last bullet fired

        # Parry skill attributes
        self.has_parry = False
        self.parry_cooldown = 6000 # 6 seconds cooldown for parry (base)
        self.last_parry_time = 0

        # Bullet firing side for alternating shots
        self.next_shot_side = "left" # Which side fires next

        # Barrage mode
        self.is_barraging = False
        self.barrage_fire_rate = 50 # Faster fire rate for barrage

        # Player lives - Initialized by Oyun based on difficulty and upgrades
        self.can = 5


    def get_parry_cooldown_remaining(self):
        """Returns the remaining parry cooldown in milliseconds."""
        now = pygame.time.get_ticks()
        elapsed_since_last_parry = now - self.last_parry_time
        cooldown_remaining = max(0, self.parry_cooldown - elapsed_since_last_parry)
        return cooldown_remaining

    def update(self):
        # Player movement is handled by key presses in the main loop
        # Barrage firing is handled here if in barrage mode
        if self.is_barraging:
             self.ates()


    def move(self, dx):
        self.rect.x += dx * self.hiz
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(GENISLIK, self.rect.right)

    def ates(self):
        now = pygame.time.get_ticks()
        # Determine fire rate based on whether in barrage mode
        current_fire_rate = self.barrage_fire_rate if self.is_barraging else self.shoot_delay

        # Check if enough time has passed since the last individual shot
        if now - self.last_shot_time > current_fire_rate and len(self.oyuncu_mermi_grup) < self.max_bullets:
            bullet_offset = self.rect.width // 2 - 10 # Adjust offset based on ship width

            if self.next_shot_side == "left":
                # Fire from the left side
                mermi = oyuncuMermi(self.rect.centerx - bullet_offset, self.rect.top)
                self.next_shot_side = "right"
            else: # next_shot_side == "right"
                # Fire from the right side
                mermi = oyuncuMermi(self.rect.centerx + bullet_offset, self.rect.top)
                self.next_shot_side = "left" # Switch side for the *next* shot

            self.oyuncu_mermi_grup.add(mermi) # Add the bullet to the group
            if self.mermi_sesi: self.mermi_sesi.play()
            self.last_shot_time = now # Update time of the last individual shot

    def slash(self, sword_slash_group):
        now = pygame.time.get_ticks()
        if self.has_parry and now - self.last_parry_time > self.parry_cooldown:
            # Create a sword slash animation sprite
            slash_animation = SwordSlash(self.rect.centerx, self.rect.top)
            sword_slash_group.add(slash_animation)
            self.last_parry_time = now


    def start_barrage(self):
        """Starts the player's barrage firing mode."""
        self.is_barraging = True
        self.last_shot_time = 0 # Reset timer to allow immediate firing


    def reset(self):
        # Adjusted reset position due to increased window height
        self.rect.centerx = GENISLIK // 2
        self.rect.bottom = YUKSEKLIK - 200
        self.last_shot_time = 0 # Reset shot timer
        self.next_shot_side = "left" # Reset firing side
        self.is_barraging = False # Ensure barrage mode is off
        # Player lives are reset by Oyun.oyun_durumu or Oyun.oyun_reset calling apply_upgrades


class Uzayli(pygame.sprite.Sprite):
    def __init__(self, x, y, hiz, mermi_grup, mermi_sesi, level_no, difficulty):
        super().__init__()
        self.image = load_image("uzayli.png", scale=(64, 64), smooth=True) # Use helper, smoothscale
        self.rect = self.image.get_rect(topleft=(x, y))
        self.yon = 1
        self.hiz = hiz # Base speed from bolum()
        self.mermi_grup = mermi_grup
        self.uzayli_mermi_sesi = mermi_sesi
        self.level_no = level_no
        self.difficulty = difficulty # Store difficulty

        # Firing chance increases with level and depends on difficulty
        self.shoot_chance = max(1, 6 - (self.level_no // 2)) # Base chance
        if self.difficulty == Difficulty.EASY: self.shoot_chance = max(1, self.shoot_chance * 1.5) # Less frequent
        elif self.difficulty == Difficulty.HARD: self.shoot_chance = max(1, self.shoot_chance * 0.8) # More frequent
        elif self.difficulty == Difficulty.REVENGEANCE: self.shoot_chance = max(1, self.shoot_chance * 0.5) # Much more frequent


        self.shoot_max_bullets = 3 + (self.level_no // 3) # More bullets allowed from swarm later


    def update(self):
         # Firing logic
        # Count only alien/minion bullets in the uzayli_mermi_grup
        current_alien_bullets = sum(1 for b in self.mermi_grup.sprites() if isinstance(b, uzayliMermi))
        if random.randint(0, 100 * self.shoot_chance) == 0 and current_alien_bullets < self.shoot_max_bullets:
            self.ates()

    def ates(self):
        mermi = uzayliMermi(self.rect.centerx, self.rect.bottom, self.level_no, self.difficulty) # Pass level and difficulty for bullet speed
        self.mermi_grup.add(mermi)
        if self.uzayli_mermi_sesi: self.uzayli_mermi_sesi.play()


class oyuncuMermi(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Make the bullet image smaller
        self.image = load_image("oyuncu_mermi.png", scale=(10, 20), smooth=True) # Reduced size, use smoothscale
        if self.image is None: # Fallback if loading fails
             self.image = pygame.Surface((10, 20)); self.image.fill(BEYAZ)

        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.hiz = 14 # Slightly faster base speed

    def update(self):
        self.rect.y -= self.hiz
        if self.rect.bottom < 0: self.kill()


class uzayliMermi(pygame.sprite.Sprite):
    def __init__(self, x, y, level_no, difficulty):
        super().__init__()
        self.image = load_image("uzayli_mermi.png", scale=(15, 15), smooth=True) # Slightly smaller alien bullets, use smoothscale
        if self.image is None: # Fallback if loading fails
             self.image = pygame.Surface((15, 15)); self.image.fill(TURUNCU)

        self.rect = self.image.get_rect(centerx=x, top=y)
        self.hiz = 8 + (level_no // 2) # Base speed based on level
        # Adjust speed based on difficulty
        if difficulty == Difficulty.EASY: self.hiz = max(5, self.hiz * 0.8) # Minimum speed 5
        elif difficulty == Difficulty.HARD: self.hiz *= 1.2
        elif difficulty == Difficulty.REVENGEANCE: self.hiz *= 1.5


    def update(self):
        self.rect.y += self.hiz
        if self.rect.top > YUKSEKLIK: self.kill()


# === Gruplar ===
oyuncu_mermi_grup = pygame.sprite.Group()
uzayli_mermi_grup = pygame.sprite.Group()
oyuncu_grup = pygame.sprite.GroupSingle() # Player should be single
uzayli_grup = pygame.sprite.Group()
# sword_slash_grup is now managed within the Oyun class
# minion_grup is now managed within the Oyun class

# === Nesneler ===
oyuncu = Oyuncu(oyuncu_mermi_grup, None)
oyuncu_grup.add(oyuncu)
oyun = Oyun(oyuncu, oyuncu_grup, uzayli_grup, oyuncu_mermi_grup, uzayli_mermi_grup)
# Player sound and Oyun reference assigned inside Oyun.__init__ now

# Flag to ensure bolum() is called only once per transition
called_bolum_in_transition = False

# === Oyun Döngüsü ===
durum = True
while durum:
    events = pygame.event.get()
    for etkinlik in events:
        if etkinlik.type == pygame.QUIT:
            oyun.stop_all_sounds() # Stop all sounds before quitting
            # Save settings on quit
            save_game_state(oyun.high_score, oyun.boss_unlocked, oyun.music_volume, oyun.sfx_volume, oyun.difficulty, oyun.set_fps)
            durum = False
        # Key Down Events
        if etkinlik.type == pygame.KEYDOWN:
            # Global quit/pause handling with ESC
            if etkinlik.key == pygame.K_ESCAPE:
                 if oyun.game_state == GameState.PLAYING:
                      oyun.game_state = GameState.PAUSED # Pause if playing
                 elif oyun.game_state == GameState.PAUSED:
                      # Go back to Main Menu from Pause
                      oyun.game_state = GameState.MAIN_MENU
                      oyun.stop_all_sounds() # Stop sounds when returning to menu
                      try: # Resume music on returning to menu
                          pygame.mixer.music.load(oyun.background_music_path)
                          pygame.mixer.music.play(-1)
                          oyun.apply_volume()
                      except pygame.error as e:
                           print(f"Arkaplan müziği yüklenemedi: {e}")

                 elif oyun.game_state == GameState.OPTIONS:
                      # Save settings before returning
                      save_game_state(oyun.high_score, oyun.boss_unlocked, oyun.music_volume, oyun.sfx_volume, oyun.difficulty, oyun.set_fps)
                      # Return to the state we came from
                      if hasattr(oyun, 'came_from_state'):
                          oyun.game_state = oyun.came_from_state
                          delattr(oyun, 'came_from_state')
                      else:
                          oyun.game_state = GameState.MAIN_MENU # Fallback to Main Menu
                          oyun.stop_all_sounds() # Stop sounds when returning to menu
                          try: # Resume music on returning to menu
                              pygame.mixer.music.load(oyun.background_music_path)
                              pygame.mixer.music.play(-1)
                              oyun.apply_volume()
                          except pygame.error as e:
                               print(f"Arkaplan müziği yüklenemedi: {e}")

                 elif oyun.game_state in [GameState.MAIN_MENU, GameState.GAME_OVER, GameState.WIN]:
                      oyun.stop_all_sounds() # Stop sounds before quitting from these states
                      # Save settings on quitting from these states
                      save_game_state(oyun.high_score, oyun.boss_unlocked, oyun.music_volume, oyun.sfx_volume, oyun.difficulty, oyun.set_fps)
                      durum = False # Quit from Main Menu, Game Over, Win screens

            # Handle F1 for cheat input toggle (only in Main Menu)
            if etkinlik.key == pygame.K_F1 and oyun.game_state == GameState.MAIN_MENU:
                 oyun.cheat_input_active = not oyun.cheat_input_active # Toggle cheat input active state
                 oyun.cheat_code_input = "" # Clear input when toggling


            # Handle fullscreen toggle (F11) globally
            if etkinlik.key == pygame.K_F11:
                 oyun.toggle_fullscreen()

            # State-specific keydowns
            if oyun.game_state == GameState.MAIN_MENU:
                # Cheat code input handling (only if active)
                if oyun.cheat_input_active:
                    if etkinlik.unicode and (etkinlik.unicode.isalpha() or etkinlik.unicode.isdigit()):
                        oyun.cheat_code_input += etkinlik.unicode.lower()
                    elif etkinlik.key == pygame.K_BACKSPACE:
                        oyun.cheat_code_input = oyun.cheat_code_input[:-1]
                    elif etkinlik.key == pygame.K_RETURN:
                        if oyun.cheat_code_input == oyun.cheat_code:
                            oyun.puan += 1000000 # Grant points for cheat code
                            print("Cheat code activated: 1,000,000 points granted!") # Optional feedback in console
                        oyun.cheat_code_input = "" # Clear cheat input after attempt
                        oyun.cheat_input_active = False # Deactivate cheat input after attempt

                # Menu navigation (only if cheat input is NOT active)
                elif not oyun.cheat_input_active:
                     if etkinlik.key == pygame.K_RETURN:
                         oyun.oyun_reset() # Reset game state for a new run
                         oyun.game_state = GameState.LEVEL_TRANSITION # Start the game

                     elif etkinlik.key == pygame.K_o: oyun.came_from_state = GameState.MAIN_MENU; oyun.game_state = GameState.OPTIONS
                     elif etkinlik.key == pygame.K_b and oyun.boss_unlocked: # Start boss fight if B is pressed and unlocked
                          oyun.start_boss_fight()


            elif oyun.game_state == GameState.PLAYING:
                # Handle specific key presses for pause, etc.
                if etkinlik.key == pygame.K_p: oyun.game_state = GameState.PAUSED
                # Removed 'O' access from playing directly

            elif oyun.game_state == GameState.PAUSED:
                 if etkinlik.key == pygame.K_p: oyun.game_state = GameState.PLAYING
                 # Allow access to Options from Pause
                 elif etkinlik.key == pygame.K_o:
                      oyun.came_from_state = GameState.PAUSED # Remember to return to pause
                      oyun.game_state = GameState.OPTIONS
                 elif etkinlik.key == pygame.K_m:
                      oyun.game_state = GameState.MAIN_MENU
                      oyun.stop_all_sounds() # Stop sounds when returning to menu
                      try: # Resume music on returning to menu
                          pygame.mixer.music.load(oyun.background_music_path)
                          pygame.mixer.music.play(-1)
                          oyun.apply_volume()
                      except pygame.error as e:
                           print(f"Arkaplan müziği yüklenemedi: {e}")


            elif oyun.game_state == GameState.UPGRADES:
                oyun.handle_upgrade_input(etkinlik) # Handles 1, 2, 3, 4, 5, 6, ENTER, ESC

            elif oyun.game_state == GameState.OPTIONS:
                oyun.handle_options_input(etkinlik) # Handles volume, difficulty, FPS, and ESC back

            elif oyun.game_state == GameState.GAME_OVER or oyun.game_state == GameState.WIN:
                if etkinlik.key == pygame.K_RETURN:
                     oyun.game_state = GameState.MAIN_MENU
                     oyun.stop_all_sounds() # Stop sounds when returning to menu
                     try: # Resume music on returning to menu
                         pygame.mixer.music.load(oyun.background_music_path)
                         pygame.mixer.music.play(-1)
                         oyun.apply_volume()
                     except pygame.error as e:
                              print(f"Arkaplan müziği yüklenemedi: {e}")


            elif oyun.game_state == GameState.BOSS_DEFEATED_CUTSCENE:
                 if etkinlik.key == pygame.K_x:
                      oyun.game_state = GameState.BOSS_BARRAGE_CUTSCENE
                      oyun.cutscene_start_time = pygame.time.get_ticks() # Start barrage timer
                      oyun.oyuncu.start_barrage() # Start player barrage
                      if oyun.defeat_sound: oyun.defeat_sound.stop() # Stop defeat sound


        # Mouse Button Down Events (for parrying on right click)
        if etkinlik.type == pygame.MOUSEBUTTONDOWN and oyun.game_state == GameState.PLAYING:
            # Right mouse button for parry
            if etkinlik.button == 3:
                oyuncu.slash(oyun.sword_slash_grup)

    # --- Continuous Key Presses (Player Movement and Auto-Fire) ---
    if oyun.game_state == GameState.PLAYING:
        tus = pygame.key.get_pressed()
        move_direction = 0
        if tus[pygame.K_LEFT]: move_direction -= 1
        if tus[pygame.K_RIGHT]: move_direction += 1
        oyuncu.move(move_direction)

        # Auto-fire on left mouse button hold
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]: # Check if left mouse button is held down
            oyuncu.ates()


    # --- Updates ---
    oyun.update() # Updates game logic based on state

    # --- Drawing ---
    pencere.fill(SIYAH)
    if oyun.game_state == GameState.PLAYING:
        oyun.cizdir()
        # Reset the flag when entering PLAYING state
        called_bolum_in_transition = False
    elif oyun.game_state == GameState.PAUSED: oyun.cizdir(); oyun.draw_pause_screen()
    elif oyun.game_state == GameState.UPGRADES: oyun.draw_upgrade_screen()
    elif oyun.game_state == GameState.OPTIONS: oyun.draw_options_screen()
    elif oyun.game_state == GameState.GAME_OVER: oyun.draw_game_over_screen()
    elif oyun.game_state == GameState.LEVEL_TRANSITION:
         oyun.draw_level_transition_screen()
         # Call bolum() only once when entering LEVEL_TRANSITION state
         if not called_bolum_in_transition:
             oyun.bolum() # Spawn entities AFTER transition screen
             # Boss health needs to be full when spawning in bolum()
             if oyun.bolum_no == 5 and oyun.boss_grup.sprite:
                 oyun.boss_grup.sprite.current_hp = oyun.boss_grup.sprite.max_hp
                 oyun.boss_grup.sprite.warning_active = False # Ensure no lingering warnings
                 oyun.warning_grup.empty() # Clear old warnings just in case
                 oyun.boss_grup.sprite.is_moving = True # Ensure boss starts moving
                 oyun.boss_grup.sprite.is_enraged = False # Ensure boss starts not enraged
                 if oyun.boss_grup.sprite.enraged_sound: oyun.boss_grup.sprite.enraged_sound.stop() # Stop sound if it was somehow playing
             called_bolum_in_transition = True # Set the flag after calling bolum()

    elif oyun.game_state == GameState.WIN: oyun.draw_win_screen()
    elif oyun.game_state == GameState.MAIN_MENU:
        oyun.draw_main_menu()
        # Reset the flag when entering MAIN_MENU state
        called_bolum_in_transition = False

    # Draw cutscene specific visuals
    if oyun.game_state in [GameState.BOSS_DEFEATED_CUTSCENE, GameState.BOSS_BARRAGE_CUTSCENE]:
        oyun.cizdir() # Draw the game elements
        if oyun.game_state == GameState.BOSS_DEFEATED_CUTSCENE:
             # Flash "Press X!"
             now = pygame.time.get_ticks()
             if (now // 500) % 2 == 0: # Flash every 500ms
                  render_text("Press X!", oyun_font_buyuk, SARI, pencere, GENISLIK // 2, YUKSEKLIK // 2)


    # --- Display Update ---
    # Only flip if not in a state that handles its own flipping (like transitions)
    # Also flip during LEVEL_TRANSITION and cutscenes to show the screens
    if oyun.game_state not in []: # No states excluded from flipping now
         pygame.display.flip()

    # --- Tick Clock ---
    saat.tick(oyun.set_fps) # Use the configured FPS

pygame.quit()
