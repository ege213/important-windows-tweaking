# uzay_istilasi/sprites/player.py
# -*- coding: utf-8 -*-
import pygame
import settings
import assets
from sprites.projectiles import oyuncuMermi
from sprites.effects import SwordSlash

class Oyuncu(pygame.sprite.Sprite):
    def __init__(self, oyuncu_mermi_grup):
        super().__init__()
        self.image_original = assets.load_image("uzay_gemi.png", scale=(64, 64), smooth=True)
        self.image = self.image_original
        if self.image.get_width() != 64 or self.image.get_height() != 64: # Check if placeholder was loaded
            self.image_original = pygame.Surface((64,64), pygame.SRCALPHA)
            self.image_original.fill(settings.ACIK_MAVI) # Placeholder color
            pygame.draw.polygon(self.image_original, settings.YESIL, [(32,0), (0,60), (64,60)]) # Simple triangle
            self.image = self.image_original

        self.rect = self.image.get_rect(centerx=settings.GENISLIK // 2, bottom=settings.YUKSEKLIK - 150) # Adjusted y slightly
        self.oyuncu_mermi_grup = oyuncu_mermi_grup
        self.mermi_sesi = None
        self.parry_sound = None # SwordSlash handles its own sound
        self.oyun_ref = None

        self.hiz = 8
        self.shoot_delay = 300
        self.max_bullets = 4
        self.last_shot_time = 0

        self.has_parry = False
        self.parry_cooldown = 6000
        self.last_parry_time = 0

        self.next_shot_side = "left"
        self.is_barraging = False
        self.barrage_fire_rate = 50
        self.can = 5

        self.last_thruster_spawn = 0 # For thruster particles
        self.is_hit_timer = 0 # For hit flash effect
        self.hit_flash_duration = 150 # ms

    def get_parry_cooldown_remaining(self):
        now = pygame.time.get_ticks()
        elapsed_since_last_parry = now - self.last_parry_time
        cooldown_remaining = max(0, self.parry_cooldown - elapsed_since_last_parry)
        return cooldown_remaining

    def update(self):
        if self.is_barraging:
            self.ates()

        # Hit flash effect
        if self.is_hit_timer > 0:
            now = pygame.time.get_ticks()
            if now - self.is_hit_timer < self.hit_flash_duration:
                # Alternate between original and white tint
                if (now // (self.hit_flash_duration // 4)) % 2 == 0:
                    flash_image = self.image_original.copy()
                    flash_image.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGBA_MULT)
                    self.image = flash_image
                else:
                    self.image = self.image_original
            else:
                self.image = self.image_original # Restore original image
                self.is_hit_timer = 0
        else:
             self.image = self.image_original # Ensure it's original if not hit


    def move(self, dx):
        self.rect.x += dx * self.hiz
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(settings.GENISLIK, self.rect.right)

        # Thruster particles (visual only)
        if dx != 0 and self.oyun_ref and hasattr(self.oyun_ref, 'create_thruster_particle'):
            now = pygame.time.get_ticks()
            if now - self.last_thruster_spawn > 30: # Emit thruster particle
                self.oyun_ref.create_thruster_particle(self.rect.midbottom)
                self.last_thruster_spawn = now


    def ates(self):
        now = pygame.time.get_ticks()
        current_fire_rate = self.barrage_fire_rate if self.is_barraging else self.shoot_delay

        if now - self.last_shot_time > current_fire_rate and len(self.oyuncu_mermi_grup) < self.max_bullets:
            bullet_offset_x = self.rect.width // 4 # Adjust for better placement from sides
            
            # Fire from alternating sides, or both if barrage and max_bullets allows
            if self.is_barraging and self.max_bullets >= 2 and len(self.oyuncu_mermi_grup) <= self.max_bullets - 2:
                mermi_left = oyuncuMermi(self.rect.centerx - bullet_offset_x, self.rect.top)
                mermi_right = oyuncuMermi(self.rect.centerx + bullet_offset_x, self.rect.top)
                self.oyuncu_mermi_grup.add(mermi_left, mermi_right)
            elif self.next_shot_side == "left":
                mermi = oyuncuMermi(self.rect.centerx - bullet_offset_x, self.rect.top)
                self.oyuncu_mermi_grup.add(mermi)
                self.next_shot_side = "right"
            else:
                mermi = oyuncuMermi(self.rect.centerx + bullet_offset_x, self.rect.top)
                self.oyuncu_mermi_grup.add(mermi)
                self.next_shot_side = "left"

            if self.mermi_sesi: self.mermi_sesi.play()
            self.last_shot_time = now

    def slash(self, sword_slash_group):
        now = pygame.time.get_ticks()
        if self.has_parry and now - self.last_parry_time > self.parry_cooldown:
            slash_animation = SwordSlash(self.rect.centerx, self.rect.top)
            sword_slash_group.add(slash_animation)
            self.last_parry_time = now
            # Parry sound played by SwordSlash instance itself upon successful parry in game_logic

    def start_barrage(self):
        self.is_barraging = True
        self.last_shot_time = 0

    def reset(self):
        self.rect.centerx = settings.GENISLIK // 2
        self.rect.bottom = settings.YUKSEKLIK - 150
        self.last_shot_time = 0
        self.next_shot_side = "left"
        self.is_barraging = False
        self.image = self.image_original # Reset image on game reset
        self.is_hit_timer = 0

    def got_hit(self):
        self.is_hit_timer = pygame.time.get_ticks()
