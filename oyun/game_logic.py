# uzay_istilasi/game_logic.py
# -*- coding: utf-8 -*-
import pygame
import random
import os
import settings
import assets
import save_load
from sprites.player import Oyuncu
from sprites.enemies import Uzayli, Boss, Minion # Minion is in enemies
from sprites.effects import Particle # For explosions and thrusters

class Oyun():
    def __init__(self, oyuncu_instance, initial_oyuncu_mermi_grup):
        self.puan = 0
        self.bolum_no = 1
        self.high_score, self.boss_unlocked, self.music_volume, self.sfx_volume, \
        self.difficulty, self.set_fps, self.upgrade_levels = save_load.load_game_state()

        self.game_state = settings.GameState.MAIN_MENU
        self.max_levels = settings.MAX_LEVELS
        self.max_enemy_bullets_on_screen = 10 # Example cap for minion/alien bullets

        self.oyuncu = oyuncu_instance
        self.oyuncu_grup = pygame.sprite.GroupSingle(self.oyuncu)
        self.uzayli_grup = pygame.sprite.Group()
        self.oyuncu_mermi_grup = initial_oyuncu_mermi_grup
        self.uzayli_mermi_grup = pygame.sprite.Group() # For regular alien bullets
        self.boss_grup = pygame.sprite.GroupSingle()
        self.boss_mermi_grup = pygame.sprite.Group() # For Boss & Minion bullets
        self.warning_grup = pygame.sprite.Group()
        self.sword_slash_grup = pygame.sprite.GroupSingle()
        self.minion_grup = pygame.sprite.Group()
        self.particle_grup = pygame.sprite.Group() # For explosions, thrusters
        self.thruster_particle_grup = pygame.sprite.Group() # Specific for player thrusters

        self.is_fullscreen = False
        self.initial_display_flags = settings.INITIAL_DISPLAY_FLAGS

        self.cheat_code_input = ""
        self.cheat_input_active = False

        self.show_boss_unlocked_message = False
        self.boss_unlocked_message_start_time = 0
        self.boss_unlocked_message_duration = 4000

        self.upgrade_costs = {
            "speed": [1000, 2500, 5000, 10000, 18000],
            "fire_rate": [1500, 3000, 6000, 12000, 20000],
            "max_bullets": [2000, 4000, 8000, 15000],
            "lives": [5000], "parry": [7000], "parry_cooldown": [3000, 6000, 10000]
        }
        self.upgrade_max_levels = {k: len(v) for k, v in self.upgrade_costs.items()}
        self.apply_upgrades()

        self.arka_planlar = []
        for i in range(1, min(self.max_levels, 10) + 1): # Load up to 10 backgrounds
            fn_png, fn_jpg = f"arka_plan{i}.png", f"arka_plan{i}.jpg"
            fp_png, fp_jpg = os.path.join(settings.ASSET_DIR, fn_png), os.path.join(settings.ASSET_DIR, fn_jpg)
            actual_fn = fn_png if os.path.exists(fp_png) else (fn_jpg if os.path.exists(fp_jpg) else None)
            if actual_fn:
                self.arka_planlar.append(assets.load_image(actual_fn, scale=(settings.GENISLIK, settings.YUKSEKLIK), convert_alpha=False))
            else: print(f"Uyarı: Arkaplan '{fn_png}' veya '{fn_jpg}' bulunamadı.")
        
        if not self.arka_planlar:
            print("HATA: Hiç arkaplan yüklenemedi! Varsayılan siyah arkaplan kullanılacak.")
            placeholder_bg = pygame.Surface((settings.GENISLIK, settings.YUKSEKLIK)); placeholder_bg.fill(settings.SIYAH)
            self.arka_planlar.append(placeholder_bg)
        while len(self.arka_planlar) < self.max_levels and self.arka_planlar:
            self.arka_planlar.append(self.arka_planlar[-1])

        self.tebrikler_img = assets.load_image("tebrikler.png", scale=(settings.GENISLIK, settings.YUKSEKLIK))
        self.sword_icon = assets.load_image("sword.png", scale=(50, 50), smooth=True)

        self.uzayli_vurus = assets.load_sound("uzayli_vurus.wav")
        self.oyuncu_vurus = assets.load_sound("oyuncu_vurus.wav")
        self.oyuncu_mermi_sesi = assets.load_sound("oyuncu_mermi.wav")
        self.uzayli_mermi_sesi = assets.load_sound("uzayli_mermi.wav")
        self.upgrade_sound = assets.load_sound("oyuncu_vurus.wav")
        self.cant_afford_sound = assets.load_sound("uzayli_vurus.wav")
        self.level_complete_sound = assets.load_sound("oyuncu_mermi.wav")
        self.boss_death_sound = assets.load_sound("oyuncu_vurus.wav") # Replaced by boss's own logic
        self.parry_sound = assets.load_sound("parry.wav") # SwordSlash now handles this
        self.boss_laugh_sound = assets.load_sound("bosslaugh.wav")
        self.summon_sound = assets.load_sound("summon.wav") # Boss uses this
        self.enraged_sound = assets.load_sound("enraged.wav") # Boss uses this
        self.defeat_sound = assets.load_sound("defeat.wav") # Boss uses this

        self.oyuncu.mermi_sesi = self.oyuncu_mermi_sesi
        self.oyuncu.oyun_ref = self

        self.is_enraged_visual = False
        self.enraged_overlay = pygame.Surface((settings.GENISLIK, settings.YUKSEKLIK), pygame.SRCALPHA)
        self.enraged_overlay.fill(settings.ENRAGE_OVERLAY_COLOR)
        self.shake_intensity = 0
        self.shake_duration = 0 
        self.shake_timer = 0

        self.cutscene_start_time = 0
        self.barrage_cutscene_duration = 2000

        self.background_music_path = os.path.join(settings.ASSET_DIR, "arka_plan_sarki.wav")
        try:
            pygame.mixer.music.load(self.background_music_path)
            pygame.mixer.music.play(-1)
        except pygame.error as e: print(f"Arkaplan müziği yüklenemedi: {e}")

        self.apply_volume()
        self.apply_difficulty_settings_to_game()
        self.came_from_state = None
        self.how_to_play_button_rect = None # For UI module
        self.start_button_rect = None
        self.boss_rush_button_rect = None
        self.options_button_rect = None
        self.quit_button_rect = None
        self.how_to_play_scroll_y = 0 # For potential scrolling in how to play
        self.how_to_play_content_height = 0 # Calculated by ui.py

    def stop_all_sounds(self):
        sound_list = [self.uzayli_vurus, self.oyuncu_vurus, self.oyuncu_mermi_sesi, self.uzayli_mermi_sesi,
                      self.upgrade_sound, self.cant_afford_sound, self.level_complete_sound, self.boss_death_sound,
                      self.parry_sound, self.boss_laugh_sound, self.summon_sound, self.enraged_sound, self.defeat_sound]
        if self.boss_grup.sprite:
            sound_list.extend([getattr(self.boss_grup.sprite, snd_attr, None) for snd_attr in 
                               ['hit_sound', 'shoot_sound', 'warning_sound', 'beam_sound', 'summon_sound', 'enraged_sound']])
        for sound in filter(None, sound_list): sound.stop()

    def apply_volume(self):
        pygame.mixer.music.set_volume(self.music_volume)
        sound_list = [self.uzayli_vurus, self.oyuncu_vurus, self.oyuncu_mermi_sesi, self.uzayli_mermi_sesi,
                      self.upgrade_sound, self.cant_afford_sound, self.level_complete_sound, self.boss_death_sound,
                      self.parry_sound, self.boss_laugh_sound, self.summon_sound, self.enraged_sound, self.defeat_sound]
        if self.boss_grup.sprite:
             sound_list.extend([getattr(self.boss_grup.sprite, snd_attr, None) for snd_attr in 
                               ['hit_sound', 'shoot_sound', 'warning_sound', 'beam_sound', 'summon_sound', 'enraged_sound']])
        for minion in self.minion_grup:
            if hasattr(minion, 'minion_mermi_sesi'): sound_list.append(minion.minion_mermi_sesi)
        for sound in filter(None, sound_list): sound.set_volume(self.sfx_volume)

    def apply_difficulty_settings_to_game(self):
        for uzayli_sprite in self.uzayli_grup.sprites():
            uzayli_sprite.difficulty = self.difficulty
            uzayli_sprite.hiz_base = 1 + (self.bolum_no // 2)
            uzayli_sprite.apply_difficulty_modifiers()
        if self.boss_grup.sprite:
            self.boss_grup.sprite.difficulty = self.difficulty
            self.boss_grup.sprite.apply_difficulty_settings()
        for minion_sprite in self.minion_grup.sprites():
            minion_sprite.difficulty = self.difficulty
            minion_sprite.apply_difficulty_modifiers()
        self.apply_upgrades()

    def apply_upgrades(self):
        self.oyuncu.hiz = 8 + self.upgrade_levels["speed"] * 1.5
        self.oyuncu.shoot_delay = max(80, 300 - self.upgrade_levels["fire_rate"] * 35)
        self.oyuncu.max_bullets = 2 + self.upgrade_levels["max_bullets"] * 2
        base_lives = 5 + self.upgrade_levels["lives"]
        self.oyuncu.can = 1 if self.difficulty == settings.Difficulty.INSTA_DEATH else base_lives
        self.oyuncu.has_parry = self.upgrade_levels["parry"] > 0
        self.oyuncu.parry_cooldown = max(1000, 6000 - self.upgrade_levels["parry_cooldown"] * 500)

    def get_upgrade_cost(self, upgrade_name):
        lvl = self.upgrade_levels[upgrade_name]
        max_lvl = self.upgrade_max_levels.get(upgrade_name, 0)
        return self.upgrade_costs[upgrade_name][lvl] if lvl < max_lvl else None

    def purchase_upgrade(self, upgrade_name):
        cost = self.get_upgrade_cost(upgrade_name)
        if cost is None:
            if self.cant_afford_sound: self.cant_afford_sound.play(); return False
        if self.puan >= cost:
            self.puan -= cost; self.upgrade_levels[upgrade_name] += 1
            self.apply_upgrades()
            if self.upgrade_sound: self.upgrade_sound.play(); return True
        else:
            if self.cant_afford_sound: self.cant_afford_sound.play(); return False

    def change_difficulty(self, direction):
        diffs = [settings.Difficulty.EASY, settings.Difficulty.NORMAL, settings.Difficulty.HARD, 
                 settings.Difficulty.INSTA_DEATH, settings.Difficulty.REVENGEANCE]
        try: current_idx = diffs.index(self.difficulty)
        except ValueError: current_idx = 1 
        self.difficulty = diffs[(current_idx + direction) % len(diffs)]
        self.apply_difficulty_settings_to_game()

    def change_fps(self, amount):
        self.set_fps = max(30, min(120, self.set_fps + amount))

    def update_game_logic(self, current_time_delta_ms):
        self.particle_grup.update() # Update all general particles
        self.thruster_particle_grup.update() # Update thruster particles

        if self.game_state == settings.GameState.PLAYING:
            self.oyuncu_grup.update()
            self.oyuncu_mermi_grup.update()
            self.sword_slash_grup.update()
            if self.bolum_no == 5: # Boss Level (Assuming 5 is boss)
                self.boss_grup.update()
                self.minion_grup.update()
                self.boss_mermi_grup.update() # Boss and Minion bullets
                self.warning_grup.update()
            else: # Normal Alien Levels
                self.uzayli_grup.update()
                self.uzayli_mermi_grup.update() # Regular alien bullets
                self.uzayli_konum_degistirme()
            self.temas()
            if self.bolum_no != 5: self.tamamlandi()

        elif self.game_state == settings.GameState.BOSS_BARRAGE_CUTSCENE:
            self.oyuncu_grup.update(); self.oyuncu_mermi_grup.update()
            if pygame.time.get_ticks() - self.cutscene_start_time > self.barrage_cutscene_duration:
                self.oyuncu.is_barraging = False; self.oyuncu_mermi_grup.empty()
                self.boss_grup.empty(); self.minion_grup.empty(); self.warning_grup.empty()
                if self.defeat_sound: self.defeat_sound.stop()
                self._revert_enraged_visuals()
                self.tamamlandi()
                try:
                    pygame.mixer.music.load(self.background_music_path); pygame.mixer.music.play(-1); self.apply_volume()
                except pygame.error as e: print(f"Müzik hatası: {e}")
        
        if self.show_boss_unlocked_message and pygame.time.get_ticks() - self.boss_unlocked_message_start_time > self.boss_unlocked_message_duration:
            self.show_boss_unlocked_message = False
        
        if self.shake_intensity > 0:
            self.shake_timer -= current_time_delta_ms
            if self.shake_timer <= 0: self.shake_intensity = 0

    def cizdir(self, surface):
        shake_x, shake_y = (0,0)
        if self.shake_intensity > 0:
            shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_y = random.randint(-self.shake_intensity, self.shake_intensity)

        bg_to_draw = self.arka_planlar[self.bolum_no - 1] if (self.arka_planlar and 0 < self.bolum_no <= len(self.arka_planlar)) else (self.arka_planlar[0] if self.arka_planlar else None)
        if bg_to_draw: surface.blit(bg_to_draw, (shake_x, shake_y))
        else: 
            temp_sf = pygame.Surface((settings.GENISLIK, settings.YUKSEKLIK)); temp_sf.fill(settings.SIYAH)
            surface.blit(temp_sf, (shake_x, shake_y))

        game_surface = pygame.Surface((settings.GENISLIK, settings.YUKSEKLIK), pygame.SRCALPHA)
        self.oyuncu_grup.draw(game_surface)
        self.thruster_particle_grup.draw(game_surface) # Draw thrusters under bullets
        self.oyuncu_mermi_grup.draw(game_surface)
        self.sword_slash_grup.draw(game_surface)
        
        if self.bolum_no == 5:
            if self.boss_grup.sprite: self.boss_grup.sprite.draw(game_surface) # Boss custom draw for hit flash
            self.minion_grup.draw(game_surface)
            self.boss_mermi_grup.draw(game_surface)
            self.warning_grup.draw(game_surface)
        else:
            self.uzayli_grup.draw(game_surface)
            self.uzayli_mermi_grup.draw(game_surface)
        
        self.particle_grup.draw(game_surface) # Draw general particles (explosions)
        surface.blit(game_surface, (shake_x, shake_y)) # Blit game elements with shake

        if self.boss_grup.sprite and self.bolum_no == 5: # Boss health bar drawn on main surface (no shake)
            self.boss_grup.sprite.draw_health_bar(surface)
            
        if self.is_enraged_visual: surface.blit(self.enraged_overlay, (0,0))
        # HUD and specific screen elements are drawn by ui.py in main.py

    def uzayli_konum_degistirme(self):
        kenara_geldi = any(u.rect.right >= settings.GENISLIK or u.rect.left <= 0 or u.rect.bottom >= settings.YUKSEKLIK - 300 for u in self.uzayli_grup)
        if kenara_geldi:
            for u in self.uzayli_grup:
                u.yon *= -1; u.rect.y += 15 + self.bolum_no
                u.rect.left = max(0, u.rect.left); u.rect.right = min(settings.GENISLIK, u.rect.right)
        for u in self.uzayli_grup:
            u.rect.x += u.yon * u.hiz
            if u.rect.bottom >= settings.YUKSEKLIK - 300: self.oyun_durumu(game_over=True); return

    def temas(self):
        # Player bullets vs Enemies
        if self.bolum_no == 5:
            if self.boss_grup.sprite and self.game_state == settings.GameState.PLAYING:
                hits = pygame.sprite.spritecollide(self.boss_grup.sprite, self.oyuncu_mermi_grup, True)
                if hits: self.boss_grup.sprite.take_damage(50 * len(hits)); self.puan += 25 * len(hits)
            minions_hit = pygame.sprite.groupcollide(self.minion_grup, self.oyuncu_mermi_grup, False, True) # Minion not killed by bullet, bullet killed
            for minion, bullets_hit in minions_hit.items():
                if self.oyuncu_vurus: self.oyuncu_vurus.play()
                self.puan += 50 * len(bullets_hit) # Score for hitting
                # Minions should have take_damage method or simply die
                minion.got_hit() # Visual feedback
                # Add minion health/death logic if desired, for now they are invulnerable to player bullets or die instantly
                # For this example, let's make them die from one hit.
                self.create_explosion(minion.rect.center, 10, settings.ACIK_MAVI, (2,5), (200,400))
                minion.kill()
        else:
            aliens_hit = pygame.sprite.groupcollide(self.uzayli_grup, self.oyuncu_mermi_grup, False, True) # Alien not killed, bullet killed
            for alien, bullets_hit in aliens_hit.items():
                if self.oyuncu_vurus: self.oyuncu_vurus.play()
                self.puan += (100 * self.bolum_no) * len(bullets_hit)
                alien.got_hit() # Visual feedback
                # Add alien health/death logic if desired
                self.create_explosion(alien.rect.center, 15, settings.TURUNCU, (3,7), (300, 600))
                alien.kill() # For simplicity, one hit kill

        # Parry
        if self.sword_slash_grup.sprite and self.game_state == settings.GameState.PLAYING:
            sword = self.sword_slash_grup.sprite
            # Parry uzayli_mermi_grup (regular aliens) AND boss_mermi_grup (boss + minions)
            parried_bullets = pygame.sprite.spritecollide(sword, self.uzayli_mermi_grup, True)
            parried_bullets.extend(pygame.sprite.spritecollide(sword, self.boss_mermi_grup, True))
            if parried_bullets: sword.play_parry_sound()
        
        # Enemy bullets vs Player
        if self.game_state == settings.GameState.PLAYING:
            hits_alien = pygame.sprite.spritecollide(self.oyuncu, self.uzayli_mermi_grup, True)
            hits_boss_minion = pygame.sprite.spritecollide(self.oyuncu, self.boss_mermi_grup, True)
            total_hits = len(hits_alien) + len(hits_boss_minion)
            if total_hits > 0:
                if self.uzayli_vurus: self.uzayli_vurus.play()
                self.oyuncu.can -= total_hits
                self.oyuncu.got_hit() # Trigger player hit flash
                # Trigger screen shake on player hit
                self.shake_intensity = 5
                self.shake_duration = 250 # ms
                self.shake_timer = self.shake_duration
        
        if self.oyuncu.can <= 0 and self.game_state == settings.GameState.PLAYING:
            self.oyun_durumu(game_over=True)

    def check_win_condition(self):
        if self.bolum_no > self.max_levels:
            if self.puan > self.high_score: self.high_score = self.puan
            save_load.save_game_state(self.high_score, self.boss_unlocked, self.music_volume, self.sfx_volume, self.difficulty, self.set_fps, self.upgrade_levels)
            self.game_state = settings.GameState.WIN
            self._revert_enraged_visuals()

    def bolum_setup(self):
        self.uzayli_grup.empty(); self.uzayli_mermi_grup.empty()
        self.boss_grup.empty(); self.boss_mermi_grup.empty()
        self.warning_grup.empty(); self.sword_slash_grup.empty()
        self.minion_grup.empty(); self.particle_grup.empty(); self.thruster_particle_grup.empty()

        if self.bolum_no == 5: # Boss level
            boss = Boss(settings.GENISLIK // 2, 80, self.boss_mermi_grup, self.warning_grup, self.oyuncu, self.minion_grup, self.difficulty, self)
            self.boss_grup.add(boss)
            if boss: boss.current_hp = boss.max_hp; boss.is_enraged = False; boss.is_moving = True
            self._revert_enraged_visuals()
        else:
            rows = min(5, 3 + self.bolum_no // 2); cols = min(10, 7 + self.bolum_no // 2)
            speed = min(1 + self.bolum_no // 2, 6)
            sx = max(50, (settings.GENISLIK - (cols * 64 + (cols-1)*10))//2); sy = 100
            for i in range(cols):
                for j in range(rows):
                    self.uzayli_grup.add(Uzayli(sx+i*74, sy+j*70, speed, self.uzayli_mermi_grup, self.uzayli_mermi_sesi, self.bolum_no, self.difficulty))
        self.apply_difficulty_settings_to_game()
        self.apply_volume() # Ensure boss sounds have correct volume

    def oyun_durumu(self, game_over=False):
        if game_over:
            if self.puan > self.high_score: self.high_score = self.puan
            save_load.save_game_state(self.high_score, self.boss_unlocked, self.music_volume, self.sfx_volume, self.difficulty, self.set_fps, self.upgrade_levels)
            self.game_state = settings.GameState.GAME_OVER
            self._revert_enraged_visuals(); self.stop_all_sounds()
            if self.boss_laugh_sound: pygame.mixer.music.stop(); self.boss_laugh_sound.play()
        
        for grp in [self.uzayli_mermi_grup, self.boss_mermi_grup, self.warning_grup, self.oyuncu_mermi_grup, 
                    self.sword_slash_grup, self.minion_grup, self.particle_grup, self.thruster_particle_grup]: grp.empty()
        self.oyuncu.reset(); self.apply_upgrades()

    def tamamlandi(self):
        cleared = False
        if self.bolum_no == 5: # Boss level logic
            if not self.boss_grup.sprite and self.game_state == settings.GameState.BOSS_BARRAGE_CUTSCENE:
                 cleared = True
                 if not self.boss_unlocked:
                     self.boss_unlocked = True; self.show_boss_unlocked_message = True
                     self.boss_unlocked_message_start_time = pygame.time.get_ticks()
                     save_load.save_game_state(self.high_score, self.boss_unlocked, self.music_volume, self.sfx_volume, self.difficulty, self.set_fps, self.upgrade_levels)
        elif self.bolum_no != 5 and not self.uzayli_grup: cleared = True

        if cleared:
            if self.level_complete_sound: self.level_complete_sound.play()
            self.bolum_no += 1
            self.check_win_condition()
            if self.game_state != settings.GameState.WIN: self.game_state = settings.GameState.UPGRADES

    def oyun_reset(self):
        self.puan = 0; self.bolum_no = 1
        default_upgrades = {"speed": 0, "fire_rate": 0, "max_bullets": 0, "lives": 0, "parry": 0, "parry_cooldown": 0}
        if self.boss_unlocked: # Keep some progress if boss is unlocked
            kept_upgrades = {k: self.upgrade_levels.get(k, 0) for k in ["lives", "parry", "parry_cooldown"]}
            self.upgrade_levels = default_upgrades.copy()
            self.upgrade_levels.update(kept_upgrades)
        else: self.upgrade_levels = default_upgrades.copy()
        
        self.apply_upgrades(); self.oyuncu.reset()
        for grp in [self.uzayli_grup, self.uzayli_mermi_grup, self.oyuncu_mermi_grup, self.boss_grup, 
                    self.boss_mermi_grup, self.warning_grup, self.sword_slash_grup, self.minion_grup, 
                    self.particle_grup, self.thruster_particle_grup]: grp.empty()
        self._revert_enraged_visuals()

    def start_boss_fight(self):
        self.oyun_reset(); self.bolum_no = 5
        self.game_state = settings.GameState.LEVEL_TRANSITION

    def _apply_enraged_visuals(self):
        self.is_enraged_visual = True; self.shake_intensity = 5
        self.shake_duration = 5000; self.shake_timer = self.shake_duration

    def _revert_enraged_visuals(self):
        self.is_enraged_visual = False; self.shake_intensity = 0; self.shake_timer = 0

    def create_explosion(self, center_pos, num_particles=20, base_color=settings.TURUNCU, size_range=(3,7), lifespan_range=(300,700), velocity_scale=3):
        for _ in range(num_particles):
            vel_x = random.uniform(-velocity_scale, velocity_scale)
            vel_y = random.uniform(-velocity_scale, velocity_scale)
            # Create a color variation
            r_offset = random.randint(-40, 40)
            g_offset = random.randint(-40, 40)
            b_offset = random.randint(-40, 40)
            
            # Pick a random color from the EXPLOSION_COLORS list or vary base_color
            # chosen_base_color = random.choice(settings.EXPLOSION_COLORS)
            chosen_base_color = base_color # Use provided base_color

            color = (max(0, min(255, chosen_base_color[0] + r_offset)),
                     max(0, min(255, chosen_base_color[1] + g_offset)),
                     max(0, min(255, chosen_base_color[2] + b_offset)),
                     random.randint(150,255)) # Add alpha
                     
            particle = Particle(center_pos[0], center_pos[1], color, size_range, 
                                ((-velocity_scale, velocity_scale), (-velocity_scale, velocity_scale)), # Pass velocity ranges
                                lifespan_range)
            self.particle_grup.add(particle)

    def create_thruster_particle(self, pos):
        # Simple thruster particle
        size = random.randint(4, 8)
        color = random.choice([(100,100,255,150), (150,150,255,200), (200,200,255,220)]) # Shades of blue/white
        # Particles move straight down from thruster with some spread
        vel_x = random.uniform(-0.5, 0.5)
        vel_y = random.uniform(2, 4) # Moves downwards from player perspective
        lifespan = random.randint(100, 300) # Short lifespan
        
        particle = Particle(pos[0], pos[1], color, (size,size+2), 
                            ((vel_x-0.2, vel_x+0.2), (vel_y-0.5, vel_y+0.5)), # velocity ranges
                            (lifespan-50, lifespan+50))
        self.thruster_particle_grup.add(particle)
