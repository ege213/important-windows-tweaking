# uzay_istilasi/sprites/enemies.py
# -*- coding: utf-8 -*-
import pygame
import random
import math
import settings
import assets
from sprites.projectiles import uzayliMermi, BossMermi
from sprites.effects import WarningIndicator, Particle # Particle for boss explosion

class Uzayli(pygame.sprite.Sprite):
    def __init__(self, x, y, hiz, mermi_grup, mermi_sesi, level_no, difficulty):
        super().__init__()
        self.image_original = assets.load_image("uzayli.png", scale=(64, 64), smooth=True)
        self.image = self.image_original
        if self.image.get_width() != 64 or self.image.get_height() != 64: # Placeholder check
            self.image_original = pygame.Surface((64,64), pygame.SRCALPHA); self.image_original.fill(settings.MAVI)
            self.image = self.image_original

        self.rect = self.image.get_rect(topleft=(x, y))
        self.yon = 1
        self.hiz_base = hiz 
        self.hiz = hiz    
        self.mermi_grup = mermi_grup
        self.uzayli_mermi_sesi = mermi_sesi
        self.level_no = level_no
        self.difficulty = difficulty

        self.shoot_chance_base = max(1, 6 - (self.level_no // 2))
        self.shoot_chance = self.shoot_chance_base
        self.apply_difficulty_modifiers() 

        self.shoot_max_bullets = 3 + (self.level_no // 3)
        self.hit_flash_timer = 0
        self.hit_flash_duration = 100

    def apply_difficulty_modifiers(self):
        if self.difficulty == settings.Difficulty.EASY: self.hiz = max(1, self.hiz_base * 0.8)
        elif self.difficulty == settings.Difficulty.HARD: self.hiz = self.hiz_base * 1.2
        elif self.difficulty == settings.Difficulty.REVENGEANCE: self.hiz = self.hiz_base * 1.5
        else: self.hiz = self.hiz_base

        if self.difficulty == settings.Difficulty.EASY: self.shoot_chance = max(1, int(self.shoot_chance_base * 1.5))
        elif self.difficulty == settings.Difficulty.HARD: self.shoot_chance = max(1, int(self.shoot_chance_base * 0.8))
        elif self.difficulty == settings.Difficulty.REVENGEANCE: self.shoot_chance = max(1, int(self.shoot_chance_base * 0.5))
        else: self.shoot_chance = self.shoot_chance_base


    def update(self):
        # Hit flash
        if self.hit_flash_timer > 0:
            now = pygame.time.get_ticks()
            if now - self.hit_flash_timer < self.hit_flash_duration:
                if (now // (self.hit_flash_duration // 4)) % 2 == 0:
                    flash_image = self.image_original.copy()
                    flash_image.fill((255,255,255,100), special_flags=pygame.BLEND_RGBA_MULT)
                    self.image = flash_image
                else:
                    self.image = self.image_original
            else:
                self.image = self.image_original
                self.hit_flash_timer = 0
        else:
            self.image = self.image_original


        current_alien_bullets = sum(1 for b in self.mermi_grup.sprites() if isinstance(b, uzayliMermi))
        if random.randint(0, 100 * self.shoot_chance) == 0 and current_alien_bullets < self.shoot_max_bullets:
            self.ates()

    def ates(self):
        mermi = uzayliMermi(self.rect.centerx, self.rect.bottom, self.level_no, self.difficulty)
        self.mermi_grup.add(mermi)
        if self.uzayli_mermi_sesi: self.uzayli_mermi_sesi.play()

    def got_hit(self):
        self.hit_flash_timer = pygame.time.get_ticks()


class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, projectile_group, warning_group, player_ref, minion_group_ref, difficulty_setting, oyun_ref):
        super().__init__()
        self.image_original = assets.load_image("boss.png", scale=(200,150), smooth=True)
        self.image = self.image_original
        if self.image.get_width() != 200: # Placeholder check
            self.image_original = pygame.Surface((200,150), pygame.SRCALPHA); self.image_original.fill(settings.KOYU_KIRMIZI)
            self.image = self.image_original

        self.rect = self.image.get_rect(centerx=x, top=y)

        self.projectile_group = projectile_group
        self.warning_group = warning_group
        self.player = player_ref
        self.minion_group = minion_group_ref
        self.difficulty = difficulty_setting
        self.oyun_ref = oyun_ref

        self.is_enraged = False
        self.enraged_speed_multiplier = 1.2
        self.enraged_attack_multiplier = 0.5

        self.max_hp = 4000
        self.base_speed = 6
        self.base_attack_delay = 1500
        self.barrage_fire_rate = 80
        self.barrage_duration = 1000
        self.minion_spawn_delay = 15000
        
        self.apply_difficulty_settings() 

        self.current_hp = self.max_hp
        self.speed = self.base_speed
        self.attack_delay = self.base_attack_delay

        self.direction = 1
        self.is_moving = True
        self.attack_timer = pygame.time.get_ticks()
        self.attack_phase = 0
        self.warning_active = False
        self.warning_timer = 0
        self.warning_duration = 600
        self.current_attack_type = None
        self.attack_target_pos = None

        self.hit_sound = assets.load_sound("uzayli_vurus.wav") 
        self.shoot_sound = assets.load_sound("uzayli_mermi.wav") 
        self.warning_sound = assets.load_sound("oyuncu_mermi.wav") 
        self.beam_sound = assets.load_sound("beam.wav")
        self.summon_sound = assets.load_sound("summon.wav")
        self.enraged_sound = assets.load_sound("enraged.wav")

        self.beam_duration = 1500 
        self.beam_end_time = 0

        self.minion_spawn_timer = pygame.time.get_ticks()
        self.barrage_end_time = 0
        self.last_barrage_shot = 0
        self.hit_flash_timer = 0 
        self.hit_flash_duration = 100


    def apply_difficulty_settings(self):
        default_enrage_speed_mult = 1.2
        default_enrage_attack_mult = 0.5
        self.enraged_speed_multiplier = default_enrage_speed_mult
        self.enraged_attack_multiplier = default_enrage_attack_mult

        if self.difficulty == settings.Difficulty.EASY:
            self.max_hp = 3000; self.base_speed = 4; self.base_attack_delay = 2000
            self.barrage_fire_rate = 120; self.minion_spawn_delay = 20000; self.barrage_duration = 800
        elif self.difficulty == settings.Difficulty.NORMAL:
            self.max_hp = 4000; self.base_speed = 6; self.base_attack_delay = 1500
            self.barrage_fire_rate = 80; self.minion_spawn_delay = 15000; self.barrage_duration = 1000
        elif self.difficulty == settings.Difficulty.HARD:
            self.max_hp = 5000; self.base_speed = 8; self.base_attack_delay = 1000
            self.barrage_fire_rate = 60; self.minion_spawn_delay = 10000; self.barrage_duration = 1200
        elif self.difficulty == settings.Difficulty.INSTA_DEATH:
            self.max_hp = 4000; self.base_speed = 6; self.base_attack_delay = 1500
            self.barrage_fire_rate = 80; self.minion_spawn_delay = 15000; self.barrage_duration = 1000
        elif self.difficulty == settings.Difficulty.REVENGEANCE:
            self.max_hp = 6000; self.base_speed = 10; self.base_attack_delay = 800
            self.barrage_fire_rate = 40; self.minion_spawn_delay = 8000; self.barrage_duration = 1500
            self.enraged_speed_multiplier = 1.5
            self.enraged_attack_multiplier = 0.3
        
        if self.is_enraged:
            self.speed = self.base_speed * self.enraged_speed_multiplier
        else:
            self.speed = self.base_speed
        
        if self.difficulty == settings.Difficulty.REVENGEANCE:
            self.enrage_threshold = self.max_hp * 0.6
        else:
            self.enrage_threshold = self.max_hp // 2
    
    def update(self):
        if self.hit_flash_timer > 0:
            now = pygame.time.get_ticks()
            if now - self.hit_flash_timer < self.hit_flash_duration:
                if (now // (self.hit_flash_duration // 4)) % 2 == 0: 
                    flash_image = self.image_original.copy()
                    flash_image.fill((255,255,255,120), special_flags=pygame.BLEND_RGBA_MULT) 
                    self.image = flash_image
                else:
                    self.image = self.image_original
            else:
                self.image = self.image_original
                self.hit_flash_timer = 0
        else:
            self.image = self.image_original 

        if self.is_moving:
            self._move()
            self._handle_attacks()
            self._handle_minion_spawning()
        self._check_enrage()
        self._handle_barrage()

    def _move(self):
        self.rect.x += self.speed * self.direction
        if self.rect.right > settings.GENISLIK - 20:
            self.rect.right = settings.GENISLIK - 20; self.direction = -1
        elif self.rect.left < 20:
            self.rect.left = 20; self.direction = 1

    def _handle_attacks(self):
        now = pygame.time.get_ticks()
        if (self.current_attack_type == 'barrage' and now < self.barrage_end_time) or not self.is_moving:
            return

        if self.warning_active and now > self.warning_timer + self.warning_duration:
            self._execute_attack()
            self.warning_active = False
            if self.current_attack_type == 'beam': self.beam_end_time = now + self.beam_duration
            elif self.current_attack_type == 'barrage':
                self.barrage_end_time = now + self.barrage_duration; self.last_barrage_shot = now
            else: self.attack_timer = now
        elif not self.warning_active and now > self.attack_timer + self.attack_delay and \
             now > self.beam_end_time and now > self.barrage_end_time:
            self._prepare_attack()
            self.warning_timer = now

    def _prepare_attack(self):
        self.warning_active = True
        attack_weights = {'spread': 3, 'beam': 2, 'targeted': 2, 'barrage': 1}
        if self.is_enraged: attack_weights = {'spread': 2, 'beam': 4, 'targeted': 3, 'barrage': 5}

        if self.difficulty == settings.Difficulty.EASY: attack_weights = {'spread': 4, 'beam': 1, 'targeted': 1, 'barrage': 0}
        elif self.difficulty == settings.Difficulty.HARD: attack_weights = {'spread': 2, 'beam': 3, 'targeted': 3, 'barrage': 4}
        elif self.difficulty == settings.Difficulty.REVENGEANCE: attack_weights = {'spread': 1, 'beam': 5, 'targeted': 4, 'barrage': 6}
        
        possible_attacks = {k: v for k, v in attack_weights.items() if v > 0}
        self.current_attack_type = random.choices(list(possible_attacks.keys()), weights=list(possible_attacks.values()), k=1)[0] if possible_attacks else 'spread'

        if self.warning_sound: self.warning_sound.play()
        if self.current_attack_type == 'beam':
            beam_x = self.rect.centerx; self.attack_target_pos = (beam_x, self.rect.bottom)
            self.warning_group.add(WarningIndicator(beam_x, self.rect.bottom, duration=self.warning_duration, beam_type=True))
        elif self.current_attack_type == 'targeted':
            target_x = self.player.rect.centerx; target_y = self.player.rect.centery - 50
            self.attack_target_pos = (target_x, self.rect.bottom)
            self.warning_group.add(WarningIndicator(target_x, target_y, duration=self.warning_duration, target_type=True))
        else: self.attack_target_pos = None 

        current_base_attack_delay = self.base_attack_delay 
        if self.is_enraged: current_base_attack_delay *= self.enraged_attack_multiplier
        health_ratio = self.current_hp / self.max_hp if self.max_hp > 0 else 0
        self.attack_delay = max(300, current_base_attack_delay * health_ratio + 100)

    def _execute_attack(self):
        s_spd, t_spd = (9,12) 
        if self.difficulty == settings.Difficulty.HARD: s_spd, t_spd = (11,14)
        elif self.difficulty == settings.Difficulty.REVENGEANCE: s_spd, t_spd = (13,16)

        if self.shoot_sound and self.current_attack_type != 'beam': self.shoot_sound.play()
        if self.current_attack_type == 'spread':
            for angle in [-25, -10, 0, 10, 25]:
                self.projectile_group.add(BossMermi(self.rect.centerx, self.rect.bottom, angle=angle, speed=s_spd))
        elif self.current_attack_type == 'beam':
            if self.beam_sound: self.beam_sound.play()
            if self.attack_target_pos:
                self.projectile_group.add(BossMermi(self.attack_target_pos[0], self.rect.bottom, beam=True, duration=self.beam_duration))
        elif self.current_attack_type == 'targeted' and self.attack_target_pos:
            dx = self.attack_target_pos[0] - self.rect.centerx; dy = settings.YUKSEKLIK - self.rect.bottom
            self.projectile_group.add(BossMermi(self.rect.centerx, self.rect.bottom, target_vector=(dx, dy), speed=t_spd))

    def _handle_barrage(self):
        now = pygame.time.get_ticks()
        if self.current_attack_type == 'barrage' and now < self.barrage_end_time and self.is_moving: 
            if now - self.last_barrage_shot > self.barrage_fire_rate:
                if self.shoot_sound: self.shoot_sound.play()
                dx = self.player.rect.centerx - self.rect.centerx; dy = settings.YUKSEKLIK - self.rect.bottom
                self.projectile_group.add(BossMermi(self.rect.centerx, self.rect.bottom, target_vector=(dx, dy), speed=10))
                self.last_barrage_shot = now

    def _handle_minion_spawning(self):
        now = pygame.time.get_ticks()
        if now - self.minion_spawn_timer > self.minion_spawn_delay and not self.minion_group and self.is_moving:
            self._spawn_minions(); self.minion_spawn_timer = now 

    def _spawn_minions(self):
        if self.summon_sound: self.summon_sound.play()
        num_minions = 3; spacing = 80
        start_x = self.rect.centerx - (num_minions - 1) * spacing // 2
        for i in range(num_minions):
            minion = Minion(start_x + i * spacing, self.rect.bottom + 10, self.speed * 0.8, self, 
                            self.minion_group, self.oyun_ref.boss_mermi_grup, # Minions add to boss_mermi_grup
                            self.oyun_ref.uzayli_mermi_sesi, # Can reuse alien mermi sesi
                            self.oyun_ref.bolum_no, self.difficulty)
            self.minion_group.add(minion)

    def _check_enrage(self):
        if not self.is_enraged and self.current_hp <= self.enrage_threshold: self._enrage()

    def _enrage(self):
        self.is_enraged = True
        if self.enraged_sound: self.enraged_sound.play()
        self.speed = self.base_speed * self.enraged_speed_multiplier
        if self.oyun_ref: self.oyun_ref._apply_enraged_visuals()

    def take_damage(self, amount):
        if not self.is_moving: return 
        self.current_hp -= amount
        self.got_hit() 
        if self.hit_sound: self.hit_sound.play()
        
        if self.current_hp <= 0:
            self.current_hp = 0; self.is_moving = False
            if self.is_enraged and self.enraged_sound: self.enraged_sound.stop()
            if self.oyun_ref: 
                self.oyun_ref.create_explosion(self.rect.center, num_particles=100, 
                                               size_range=(5,15), base_color=settings.EXPLOSION_COLORS,
                                               lifespan_range=(800, 1500), velocity_scale=5)
                self.oyun_ref.create_explosion(self.rect.center, num_particles=50,
                                               size_range=(10,25), base_color=settings.SARI,
                                               lifespan_range=(1000, 1800), velocity_scale=4)

                self.oyun_ref.game_state = settings.GameState.BOSS_DEFEATED_CUTSCENE
                self.oyun_ref.cutscene_start_time = pygame.time.get_ticks()
                if self.oyun_ref.defeat_sound: self.oyun_ref.defeat_sound.play()

    def got_hit(self):
        self.hit_flash_timer = pygame.time.get_ticks()

    def draw_health_bar(self, surface):
        bar_w = settings.GENISLIK*0.6; bar_h = 25
        bar_x = (settings.GENISLIK-bar_w)//2; bar_y = 15
        ratio = self.current_hp / self.max_hp if self.max_hp > 0 else 0
        curr_w = bar_w * ratio
        pygame.draw.rect(surface, settings.KOYU_GRI, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, settings.KIRMIZI, (bar_x, bar_y, curr_w, bar_h))
        pygame.draw.rect(surface, settings.BEYAZ, (bar_x, bar_y, bar_w, bar_h), 3)
        
        if "minik" in assets.FONTS: 
            # --- CHANGE IS HERE ---
            font_minik = assets.FONTS["minik"]
            text_surface = font_minik.render("BOSS", True, settings.BEYAZ)
            text_rect = text_surface.get_rect(center=(bar_x - 35, bar_y + bar_h // 2)) # Adjusted x for text
            surface.blit(text_surface, text_rect)
            # --- END CHANGE ---


class Minion(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, boss_ref, minion_group_ref, mermi_grup, mermi_sesi, level_no, difficulty_setting):
        super().__init__()
        self.image_original = assets.load_image("minion.png", scale=(40, 40), smooth=True)
        self.image = self.image_original
        if self.image.get_width() != 40: 
            self.image_original = pygame.Surface((40,40), pygame.SRCALPHA); self.image_original.fill(settings.ACIK_MAVI)
            self.image = self.image_original

        self.rect = self.image.get_rect(centerx=x, top=y)
        self.speed = speed; self.boss = boss_ref; self.minion_group = minion_group_ref
        self.mermi_grup = mermi_grup; self.minion_mermi_sesi = mermi_sesi
        self.level_no = level_no; self.difficulty = difficulty_setting

        self.fire_rate_base_min, self.fire_rate_base_max = 700, 1300
        self.fire_rate = random.randint(self.fire_rate_base_min, self.fire_rate_base_max)
        self.apply_difficulty_modifiers()

        self.last_shot_time = pygame.time.get_ticks()
        self.max_bullets_on_screen_from_this_minion = 1 
        self.offset_x = self.rect.centerx - self.boss.rect.centerx
        self.hit_flash_timer = 0
        self.hit_flash_duration = 100

    def apply_difficulty_modifiers(self):
        min_r, max_r = self.fire_rate_base_min, self.fire_rate_base_max
        if self.difficulty == settings.Difficulty.EASY: min_r, max_r = 1000, 1800
        elif self.difficulty == settings.Difficulty.HARD: min_r, max_r = 500, 1000
        elif self.difficulty == settings.Difficulty.REVENGEANCE: min_r, max_r = 300, 800
        self.fire_rate = random.randint(min_r, max_r)

    def update(self):
        if self.hit_flash_timer > 0:
            now = pygame.time.get_ticks()
            if now - self.hit_flash_timer < self.hit_flash_duration:
                if (now // (self.hit_flash_duration // 4)) % 2 == 0:
                    flash_image = self.image_original.copy()
                    flash_image.fill((255,255,255,100), special_flags=pygame.BLEND_RGBA_MULT)
                    self.image = flash_image
                else:
                    self.image = self.image_original
            else:
                self.image = self.image_original
                self.hit_flash_timer = 0
        else:
            self.image = self.image_original

        if self.boss.alive() and self.boss.is_moving:
            self.rect.centerx = self.boss.rect.centerx + self.offset_x
        else:
            self.rect.y += self.speed 
            if self.rect.top > settings.YUKSEKLIK: self.kill()
