# uzay_istilasi/main.py
# -*- coding: utf-8 -*-
import pygame
import settings
import assets
import ui
import save_load
from game_logic import Oyun
from sprites.player import Oyuncu

pygame.init()
pygame.mixer.init()
# It's good practice to initialize pygame.freetype if using it for assets.FONTS.render_to
if hasattr(pygame, 'freetype'):
    pygame.freetype.init()


pencere = pygame.display.set_mode((settings.GENISLIK, settings.YUKSEKLIK), settings.INITIAL_DISPLAY_FLAGS)
pygame.display.set_caption("Uzay İstilası Gelişmiş")
saat = pygame.time.Clock()

oyuncu_mermi_grup = pygame.sprite.Group()
oyuncu_sprite = Oyuncu(oyuncu_mermi_grup)
oyun_manager = Oyun(oyuncu_sprite, oyuncu_mermi_grup)

called_bolum_setup_in_transition = False
level_transition_timer = 0
LEVEL_TRANSITION_DURATION = 2500 # Milliseconds

durum = True
while durum:
    dt_ms = saat.get_time() 
    events = pygame.event.get()

    for etkinlik in events:
        if etkinlik.type == pygame.QUIT:
            oyun_manager.stop_all_sounds()
            save_load.save_game_state(oyun_manager.high_score, oyun_manager.boss_unlocked,
                                      oyun_manager.music_volume, oyun_manager.sfx_volume,
                                      oyun_manager.difficulty, oyun_manager.set_fps,
                                      oyun_manager.upgrade_levels)
            durum = False

        # --- MOUSE BUTTON DOWN for Menus (Optional) ---
        if etkinlik.type == pygame.MOUSEBUTTONDOWN and etkinlik.button == 1: # Left Click
            if oyun_manager.game_state == settings.GameState.MAIN_MENU:
                mouse_pos = etkinlik.pos
                if oyun_manager.start_button_rect and oyun_manager.start_button_rect.collidepoint(mouse_pos):
                    oyun_manager.oyun_reset(); oyun_manager.game_state = settings.GameState.LEVEL_TRANSITION
                    called_bolum_setup_in_transition = False; level_transition_timer = pygame.time.get_ticks()
                elif oyun_manager.how_to_play_button_rect and oyun_manager.how_to_play_button_rect.collidepoint(mouse_pos):
                    oyun_manager.came_from_state = settings.GameState.MAIN_MENU
                    oyun_manager.game_state = settings.GameState.HOW_TO_PLAY
                    oyun_manager.how_to_play_scroll_y = 0 # Reset scroll
                elif oyun_manager.options_button_rect and oyun_manager.options_button_rect.collidepoint(mouse_pos):
                    oyun_manager.came_from_state = settings.GameState.MAIN_MENU
                    oyun_manager.game_state = settings.GameState.OPTIONS
                elif oyun_manager.boss_unlocked and oyun_manager.boss_rush_button_rect and oyun_manager.boss_rush_button_rect.collidepoint(mouse_pos):
                    oyun_manager.start_boss_fight()
                    called_bolum_setup_in_transition = False; level_transition_timer = pygame.time.get_ticks()
                elif oyun_manager.quit_button_rect and oyun_manager.quit_button_rect.collidepoint(mouse_pos):
                     oyun_manager.stop_all_sounds(); save_load.save_game_state(oyun_manager.high_score, oyun_manager.boss_unlocked, oyun_manager.music_volume, oyun_manager.sfx_volume, oyun_manager.difficulty, oyun_manager.set_fps, oyun_manager.upgrade_levels); durum = False


        # --- MOUSE WHEEL for How To Play Scroll ---
        if etkinlik.type == pygame.MOUSEWHEEL and oyun_manager.game_state == settings.GameState.HOW_TO_PLAY:
            oyun_manager.how_to_play_scroll_y -= etkinlik.y * 30 # etkinlik.y is usually 1 or -1
            # Clamp scroll_y
            max_scroll = max(0, oyun_manager.how_to_play_content_height - settings.YUKSEKLIK + 100) # +100 for some bottom margin
            oyun_manager.how_to_play_scroll_y = max(0, min(oyun_manager.how_to_play_scroll_y, max_scroll))


        if etkinlik.type == pygame.KEYDOWN:
            if etkinlik.key == pygame.K_ESCAPE:
                if oyun_manager.game_state == settings.GameState.PLAYING: oyun_manager.game_state = settings.GameState.PAUSED
                elif oyun_manager.game_state == settings.GameState.PAUSED:
                    oyun_manager.game_state = settings.GameState.MAIN_MENU; oyun_manager.stop_all_sounds()
                    try: pygame.mixer.music.load(oyun_manager.background_music_path); pygame.mixer.music.play(-1); oyun_manager.apply_volume()
                    except pygame.error: pass
                elif oyun_manager.game_state == settings.GameState.OPTIONS:
                    save_load.save_game_state(oyun_manager.high_score, oyun_manager.boss_unlocked, oyun_manager.music_volume, oyun_manager.sfx_volume, oyun_manager.difficulty, oyun_manager.set_fps, oyun_manager.upgrade_levels)
                    oyun_manager.game_state = oyun_manager.came_from_state or settings.GameState.MAIN_MENU
                    oyun_manager.came_from_state = None
                elif oyun_manager.game_state == settings.GameState.HOW_TO_PLAY:
                    oyun_manager.game_state = oyun_manager.came_from_state or settings.GameState.MAIN_MENU
                    oyun_manager.came_from_state = None
                elif oyun_manager.game_state in [settings.GameState.MAIN_MENU, settings.GameState.GAME_OVER, settings.GameState.WIN]:
                    oyun_manager.stop_all_sounds(); save_load.save_game_state(oyun_manager.high_score, oyun_manager.boss_unlocked, oyun_manager.music_volume, oyun_manager.sfx_volume, oyun_manager.difficulty, oyun_manager.set_fps, oyun_manager.upgrade_levels); durum = False

            if etkinlik.key == pygame.K_F1 and oyun_manager.game_state == settings.GameState.MAIN_MENU:
                oyun_manager.cheat_input_active = not oyun_manager.cheat_input_active; oyun_manager.cheat_code_input = ""
            if etkinlik.key == pygame.K_F11:
                oyun_manager.is_fullscreen = not oyun_manager.is_fullscreen
                flags = pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE if oyun_manager.is_fullscreen else settings.INITIAL_DISPLAY_FLAGS
                pencere = pygame.display.set_mode((settings.GENISLIK, settings.YUKSEKLIK), flags)

            if oyun_manager.game_state == settings.GameState.MAIN_MENU:
                if oyun_manager.cheat_input_active:
                    if etkinlik.unicode.isalnum(): oyun_manager.cheat_code_input += etkinlik.unicode.lower()
                    elif etkinlik.key == pygame.K_BACKSPACE: oyun_manager.cheat_code_input = oyun_manager.cheat_code_input[:-1]
                    elif etkinlik.key == pygame.K_RETURN:
                        if oyun_manager.cheat_code_input == settings.CHEAT_CODE: oyun_manager.puan += 1000000
                        oyun_manager.cheat_code_input = ""; oyun_manager.cheat_input_active = False
                else:
                    if etkinlik.key == pygame.K_RETURN:
                        oyun_manager.oyun_reset(); oyun_manager.game_state = settings.GameState.LEVEL_TRANSITION
                        called_bolum_setup_in_transition = False; level_transition_timer = pygame.time.get_ticks()
                    elif etkinlik.key == pygame.K_h:
                        oyun_manager.came_from_state = settings.GameState.MAIN_MENU; oyun_manager.game_state = settings.GameState.HOW_TO_PLAY; oyun_manager.how_to_play_scroll_y = 0
                    elif etkinlik.key == pygame.K_o:
                        oyun_manager.came_from_state = settings.GameState.MAIN_MENU; oyun_manager.game_state = settings.GameState.OPTIONS
                    elif etkinlik.key == pygame.K_b and oyun_manager.boss_unlocked:
                        oyun_manager.start_boss_fight()
                        called_bolum_setup_in_transition = False; level_transition_timer = pygame.time.get_ticks()
            
            elif oyun_manager.game_state == settings.GameState.PLAYING:
                if etkinlik.key == pygame.K_p: oyun_manager.game_state = settings.GameState.PAUSED
            
            elif oyun_manager.game_state == settings.GameState.PAUSED:
                if etkinlik.key == pygame.K_p: oyun_manager.game_state = settings.GameState.PLAYING
                elif etkinlik.key == pygame.K_o: oyun_manager.came_from_state = settings.GameState.PAUSED; oyun_manager.game_state = settings.GameState.OPTIONS
                elif etkinlik.key == pygame.K_m:
                    oyun_manager.game_state = settings.GameState.MAIN_MENU; oyun_manager.stop_all_sounds()
                    try: pygame.mixer.music.load(oyun_manager.background_music_path); pygame.mixer.music.play(-1); oyun_manager.apply_volume()
                    except pygame.error: pass
            
            elif oyun_manager.game_state == settings.GameState.UPGRADES:
                if etkinlik.key == pygame.K_1: oyun_manager.purchase_upgrade("speed")
                elif etkinlik.key == pygame.K_2: oyun_manager.purchase_upgrade("fire_rate")
                elif etkinlik.key == pygame.K_3: oyun_manager.purchase_upgrade("max_bullets")
                elif etkinlik.key == pygame.K_4: oyun_manager.purchase_upgrade("lives")
                elif etkinlik.key == pygame.K_5: oyun_manager.purchase_upgrade("parry")
                elif etkinlik.key == pygame.K_6: oyun_manager.purchase_upgrade("parry_cooldown")
                elif etkinlik.key == pygame.K_RETURN or etkinlik.key == pygame.K_ESCAPE:
                    if oyun_manager.bolum_no > oyun_manager.max_levels: oyun_manager.check_win_condition()
                    else: 
                        oyun_manager.game_state = settings.GameState.LEVEL_TRANSITION
                        called_bolum_setup_in_transition = False; level_transition_timer = pygame.time.get_ticks()

            elif oyun_manager.game_state == settings.GameState.OPTIONS:
                if etkinlik.key == pygame.K_LEFT: oyun_manager.music_volume = round(max(0.0, oyun_manager.music_volume - 0.1), 1); oyun_manager.apply_volume()
                elif etkinlik.key == pygame.K_RIGHT: oyun_manager.music_volume = round(min(1.0, oyun_manager.music_volume + 0.1), 1); oyun_manager.apply_volume()
                elif etkinlik.key == pygame.K_a: oyun_manager.sfx_volume = round(max(0.0, oyun_manager.sfx_volume - 0.1), 1); oyun_manager.apply_volume()
                elif etkinlik.key == pygame.K_d: oyun_manager.sfx_volume = round(min(1.0, oyun_manager.sfx_volume + 0.1), 1); oyun_manager.apply_volume()
                elif etkinlik.key == pygame.K_z: oyun_manager.change_difficulty(-1)
                elif etkinlik.key == pygame.K_c: oyun_manager.change_difficulty(1)
                elif etkinlik.key == pygame.K_f: oyun_manager.change_fps(-10)
                elif etkinlik.key == pygame.K_g: oyun_manager.change_fps(10)

            elif oyun_manager.game_state in [settings.GameState.GAME_OVER, settings.GameState.WIN]:
                if etkinlik.key == pygame.K_RETURN:
                    oyun_manager.game_state = settings.GameState.MAIN_MENU; oyun_manager.stop_all_sounds()
                    try: pygame.mixer.music.load(oyun_manager.background_music_path); pygame.mixer.music.play(-1); oyun_manager.apply_volume()
                    except pygame.error: pass
            
            elif oyun_manager.game_state == settings.GameState.BOSS_DEFEATED_CUTSCENE:
                if etkinlik.key == pygame.K_x:
                    oyun_manager.game_state = settings.GameState.BOSS_BARRAGE_CUTSCENE
                    oyun_manager.cutscene_start_time = pygame.time.get_ticks()
                    oyun_manager.oyuncu.start_barrage()
                    if oyun_manager.defeat_sound: oyun_manager.defeat_sound.stop()

        # Mouse Button Down for player parry
        if etkinlik.type == pygame.MOUSEBUTTONDOWN and oyun_manager.game_state == settings.GameState.PLAYING:
            if etkinlik.button == 3: oyun_manager.oyuncu.slash(oyun_manager.sword_slash_grup)

    if oyun_manager.game_state == settings.GameState.PLAYING:
        keys = pygame.key.get_pressed()
        move_dir = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
        oyun_manager.oyuncu.move(move_dir)
        if pygame.mouse.get_pressed()[0]: oyun_manager.oyuncu.ates()

    oyun_manager.update_game_logic(dt_ms)
    pencere.fill(settings.SIYAH)

    if oyun_manager.game_state == settings.GameState.PLAYING:
        oyun_manager.cizdir(pencere); ui.draw_hud(pencere, oyun_manager)
    elif oyun_manager.game_state == settings.GameState.PAUSED:
        oyun_manager.cizdir(pencere); ui.draw_pause_screen(pencere)
    elif oyun_manager.game_state == settings.GameState.UPGRADES:
        ui.draw_upgrade_screen(pencere, oyun_manager)
    elif oyun_manager.game_state == settings.GameState.OPTIONS:
        ui.draw_options_screen(pencere, oyun_manager)
    elif oyun_manager.game_state == settings.GameState.GAME_OVER:
        ui.draw_game_over_screen(pencere, oyun_manager)
    elif oyun_manager.game_state == settings.GameState.WIN:
        ui.draw_win_screen(pencere, oyun_manager)
    elif oyun_manager.game_state == settings.GameState.MAIN_MENU:
        ui.draw_main_menu(pencere, oyun_manager)
    elif oyun_manager.game_state == settings.GameState.HOW_TO_PLAY:
        ui.draw_how_to_play_screen(pencere, oyun_manager, oyun_manager.how_to_play_scroll_y)
    elif oyun_manager.game_state == settings.GameState.LEVEL_TRANSITION:
        ui.draw_level_transition_screen(pencere, oyun_manager)
        if not called_bolum_setup_in_transition:
            oyun_manager.bolum_setup()
            if oyun_manager.bolum_no == 5 and oyun_manager.boss_grup.sprite: # Boss specific resets
                 oyun_manager.boss_grup.sprite.current_hp = oyun_manager.boss_grup.sprite.max_hp
                 oyun_manager.boss_grup.sprite.warning_active = False; oyun_manager.warning_grup.empty()
                 oyun_manager.boss_grup.sprite.is_moving = True; oyun_manager.boss_grup.sprite.is_enraged = False
                 if oyun_manager.boss_grup.sprite.enraged_sound: oyun_manager.boss_grup.sprite.enraged_sound.stop()
            called_bolum_setup_in_transition = True
            level_transition_timer = pygame.time.get_ticks() # Start timer for transition display
        
        if pygame.time.get_ticks() - level_transition_timer > LEVEL_TRANSITION_DURATION:
            oyun_manager.game_state = settings.GameState.PLAYING
            
    if oyun_manager.game_state in [settings.GameState.BOSS_DEFEATED_CUTSCENE, settings.GameState.BOSS_BARRAGE_CUTSCENE]:
        oyun_manager.cizdir(pencere); ui.draw_hud(pencere, oyun_manager)
        if oyun_manager.game_state == settings.GameState.BOSS_DEFEATED_CUTSCENE:
            ui.draw_boss_defeated_cutscene_elements(pencere)

    pygame.display.flip()
    saat.tick(oyun_manager.set_fps)

pygame.quit()
