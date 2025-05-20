# uzay_istilasi/ui.py
# -*- coding: utf-8 -*-
import pygame
import settings
import assets

def render_text(text, font, color, surface, center_x, y, center_y=False, top_left=False):
    # Pygame's font.render_to() is more efficient if you don't need the rect immediately for complex positioning
    if hasattr(font, 'render_to'):
        try:
            text_surf, text_rect = font.render(text, fgcolor=color, size=-1) # Get surface and rect
            if top_left:
                text_rect.topleft = (center_x, y)
            elif center_y:
                text_rect.center = (center_x, y)
            else:
                text_rect.centerx = center_x
                text_rect.top = y
            surface.blit(text_surf, text_rect)
            return text_rect
        except TypeError: # Fallback for older Pygame or different font objects
            pass # Fall through to original method

    # Original method
    text_surface = font.render(text, True, color)
    if top_left:
        text_rect = text_surface.get_rect(topleft=(center_x, y))
    elif center_y:
        text_rect = text_surface.get_rect(center=(center_x, y))
    else:
        text_rect = text_surface.get_rect(centerx=center_x, top=y)
    surface.blit(text_surface, text_rect)
    return text_rect

def draw_main_menu(surface, game_data):
    if game_data.arka_planlar:
        surface.blit(game_data.arka_planlar[0], (0, 0))
    else:
        surface.fill(settings.SIYAH)

    render_text("Uzay İstilası", assets.FONTS["buyuk"], settings.YESIL, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 4 - 40)

    menu_y_start = settings.YUKSEKLIK // 2 - 80
    line_spacing = 65 # Increased spacing slightly
    option_index = 0
    button_font = assets.FONTS["orta"]

    rect_start = render_text("Oyuna Başla (ENTER)", button_font, settings.BEYAZ, surface, settings.GENISLIK // 2, menu_y_start + option_index * line_spacing)
    game_data.start_button_rect = rect_start # For potential mouse interaction
    option_index += 1

    rect_how_to_play = render_text("Nasıl Oynanır? (H)", button_font, settings.BEYAZ, surface, settings.GENISLIK // 2, menu_y_start + option_index * line_spacing)
    game_data.how_to_play_button_rect = rect_how_to_play
    option_index += 1

    if game_data.boss_unlocked:
        rect_boss_rush = render_text("Boss Savaşı (B)", button_font, settings.BEYAZ, surface, settings.GENISLIK // 2, menu_y_start + option_index * line_spacing)
        game_data.boss_rush_button_rect = rect_boss_rush
        option_index += 1
    
    rect_options = render_text("Seçenekler (O)", button_font, settings.BEYAZ, surface, settings.GENISLIK // 2, menu_y_start + option_index * line_spacing)
    game_data.options_button_rect = rect_options
    option_index += 1

    rect_quit = render_text("Çıkış (ESC)", button_font, settings.BEYAZ, surface, settings.GENISLIK // 2, menu_y_start + option_index * line_spacing)
    game_data.quit_button_rect = rect_quit

    if game_data.cheat_input_active:
        render_text(f"Hile Kodu: {game_data.cheat_code_input}_", assets.FONTS["minik"], settings.SARI, surface, settings.GENISLIK // 2, settings.YUKSEKLIK - 90)

    render_text(f"Yüksek Skor: {game_data.high_score}", assets.FONTS["kucuk"], settings.PEMBE, surface, settings.GENISLIK // 2, settings.YUKSEKLIK - 50)
    render_text("Hile için F1 (Ana Menüde)", assets.FONTS["minik"], settings.KOYU_GRI, surface, settings.GENISLIK // 2, settings.YUKSEKLIK - 20)


def draw_how_to_play_screen(surface, game_data, scroll_y=0):
    surface.fill(settings.KOYU_MAVI)
    
    content_x_margin = 60
    content_width = settings.GENISLIK - (2 * content_x_margin)
    
    # Create a temporary surface for all text content if scrolling is desired
    # For now, we'll render directly, assuming it mostly fits or user accepts no scroll.
    # To implement scrolling: render all text to a large off-screen surface, then blit a viewport.
    
    current_y = 40 - scroll_y
    heading_font = assets.FONTS["how_to_play_heading"]
    text_font = assets.FONTS["how_to_play_text"]
    line_spacing_text = 5
    section_spacing = 35
    subsection_spacing = 15
    
    def wrap_text(text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())
        return lines

    def draw_multiline_text(full_text, font, color, x, initial_y, max_w):
        nonlocal current_y # Use the outer current_y if this is a nested helper
        lines = wrap_text(full_text, font, max_w)
        temp_y = initial_y
        for line in lines:
            if temp_y > -font.get_linesize() and temp_y < settings.YUKSEKLIK: # Basic culling
                render_text(line, font, color, surface, x, temp_y, top_left=True)
            temp_y += font.get_linesize() + line_spacing_text
        return temp_y # Return the y position after the last line

    # Title
    title_rect = render_text("Nasıl Oynanır?", assets.FONTS["buyuk"], settings.SARI, surface, settings.GENISLIK // 2, current_y)
    current_y = title_rect.bottom + section_spacing

    # Kontroller
    current_y = draw_multiline_text("Temel Kontroller", heading_font, settings.YESIL, content_x_margin, current_y, content_width)
    current_y = draw_multiline_text(" • Hareket: Sol / Sağ Ok Tuşları", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Ateş Etme: Sol Fare Tuşu (Basılı Tutarak Otomatik Ateş)", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Savuşturma (Parry): Sağ Fare Tuşu (Yükseltme Alındıktan Sonra Aktif)", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Duraklatma: P Tuşu", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Tam Ekran: F11 Tuşu", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y += section_spacing

    # Amaç
    current_y = draw_multiline_text("Oyun Amacı", heading_font, settings.YESIL, content_x_margin, current_y, content_width)
    current_y = draw_multiline_text("Gelen uzaylı dalgalarını ve güçlü bölüm sonu canavarlarını (Boss) yok ederek hayatta kalmak ve en yüksek puanı elde etmektir. Her bölüm sonunda kazandığınız puanlarla geminizi geliştirebilirsiniz.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y += section_spacing

    # Yükseltmeler
    current_y = draw_multiline_text("Yükseltmeler", heading_font, settings.YESIL, content_x_margin, current_y, content_width)
    current_y = draw_multiline_text(" • Hız: Geminizin yatay hareket hızını artırır.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Atış Hızı: Mermilerinizin ne kadar sık ateşleneceğini belirler (Daha düşük 'ms' değeri daha hızlıdır).", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Maks. Mermi: Ekranda aynı anda bulunabilecek mermi sayınızı artırır.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Can Satın Al: Ekstra can hakkı verir ('Insta-Death' zorluğunda etkisiz).", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Kılıç Savuşturma: Düşman mermilerini savuşturma yeteneği kazandırır. Belli bir bekleme süresi vardır.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Savuşturma Cooldown: Savuşturma yeteneğinin bekleme süresini kısaltır.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y += section_spacing

    # Düşmanlar & Boss
    current_y = draw_multiline_text("Düşmanlar ve Boss", heading_font, settings.YESIL, content_x_margin, current_y, content_width)
    current_y = draw_multiline_text(" • Uzaylılar: Farklı hareket ve atış paternlerine sahip temel düşmanlar.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Minyonlar: Boss tarafından çağrılan küçük, destekleyici düşmanlar.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Boss (5. Bölüm): Çok çeşitli ve tehlikeli saldırıları olan güçlü düşman. Saldırıları öncesinde çıkan uyarılara dikkat edin! Canı azaldığında 'Öfke (Enrage)' moduna girerek daha da hızlanır ve tehlikeli olur (ekran kırmızılaşır ve titrer).", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y += subsection_spacing
    current_y = draw_multiline_text("   Boss Saldırıları: Yaylım Ateşi, Işın Saldırısı, Hedefli Atış, Mermi Yağmuru.", text_font, settings.ACIK_MAVI, content_x_margin + 40, current_y, content_width)
    current_y += section_spacing

    # Savuşturma Detay
    current_y = draw_multiline_text("Savuşturma (Parry) Detayları", heading_font, settings.YESIL, content_x_margin, current_y, content_width)
    current_y = draw_multiline_text("Sağ fare tuşu ile kullanılır. Gelen mermileri (Boss'un ışınları dahil) yok eder. Başarılı savuşturma özel bir ses çıkarır. HUD'da sağ üstte kılıç ikonu ile bekleme süresi gösterilir (Yeşil: Hazır, Kırmızı: Beklemede).", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y += section_spacing

    # Zorluk Seviyeleri
    current_y = draw_multiline_text("Zorluk Seviyeleri", heading_font, settings.YESIL, content_x_margin, current_y, content_width)
    current_y = draw_multiline_text(" • Kolay, Normal, Zor: Düşman hızı, saldırganlığı ve Boss'un canı gibi faktörleri etkiler.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Insta-Death: Tek vuruşta ölürsünüz! Zorlu bir meydan okuma.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y = draw_multiline_text(" • Revengeance: En üst düzey zorluk. Düşmanlar çok daha agresif, Boss'un saldırı sıklığı artar ve daha ölümcüldür.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    current_y += section_spacing
    
    # İpuçları
    # current_y = draw_multiline_text("İpuçları", heading_font, settings.YESIL, content_x_margin, current_y, content_width)
    # current_y = draw_multiline_text("• Sürekli hareket ederek düşman ateşinden kaçının. \n• Boss'un saldırı paternlerini ve uyarılarını öğrenin. \n• Yükseltmelerinizi oyun tarzınıza uygun seçin.", text_font, settings.BEYAZ, content_x_margin + 20, current_y, content_width)
    # current_y += section_spacing * 2


    # Return Instruction (ensure it's visible)
    render_text("Ana Menüye Dönmek İçin ESC", assets.FONTS["orta"], settings.SARI, surface, settings.GENISLIK // 2, settings.YUKSEKLIK - 50)

    # Store total height for potential scrolling logic in main.py
    game_data.how_to_play_content_height = current_y + scroll_y # Total height of rendered content


def draw_pause_screen(surface):
    overlay = pygame.Surface((settings.GENISLIK, settings.YUKSEKLIK), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    render_text("DURAKLATILDI", assets.FONTS["buyuk"], settings.KIRMIZI, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 4 - 20)
    render_text("Devam etmek için P", assets.FONTS["orta"], settings.BEYAZ, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 2 - 30)
    render_text("Seçenekler için O", assets.FONTS["orta"], settings.BEYAZ, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 2 + 30)
    render_text("Ana Menü için M", assets.FONTS["orta"], settings.BEYAZ, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 2 + 90)

def draw_options_screen(surface, game_data):
    surface.fill(settings.KOYU_MAVI)
    render_text("SEÇENEKLER", assets.FONTS["buyuk"], settings.BEYAZ, surface, settings.GENISLIK // 2, 50)
    y_pos = 150
    spacing = 70

    render_text("Zorluk:", assets.FONTS["orta"], settings.BEYAZ, surface, settings.GENISLIK // 2, y_pos)
    difficulty_text = f"{game_data.difficulty.upper().replace('_', ' ')}"
    render_text(difficulty_text, assets.FONTS["kucuk"], settings.SARI, surface, settings.GENISLIK // 2, y_pos + 40)
    render_text("Değiştir: <- (Z) / (C) ->", assets.FONTS["minik"], settings.KIRMIZI, surface, settings.GENISLIK // 2, y_pos + 70)
    y_pos += spacing * 2

    render_text("FPS:", assets.FONTS["orta"], settings.BEYAZ, surface, settings.GENISLIK // 2, y_pos)
    render_text(f"{game_data.set_fps}", assets.FONTS["kucuk"], settings.SARI, surface, settings.GENISLIK // 2, y_pos + 40)
    render_text("Değiştir: <- (F) / (G) ->", assets.FONTS["minik"], settings.KIRMIZI, surface, settings.GENISLIK // 2, y_pos + 70)
    y_pos += spacing * 2

    render_text("Müzik Sesi:", assets.FONTS["orta"], settings.BEYAZ, surface, settings.GENISLIK // 2, y_pos)
    render_text(f"{int(game_data.music_volume * 100)}%", assets.FONTS["kucuk"], settings.SARI, surface, settings.GENISLIK // 2, y_pos + 40)
    render_text("Değiştir: <- (Sol Ok) / (Sağ Ok) ->", assets.FONTS["minik"], settings.KIRMIZI, surface, settings.GENISLIK // 2, y_pos + 70)
    y_pos += spacing * 2

    render_text("Efekt Sesi:", assets.FONTS["orta"], settings.BEYAZ, surface, settings.GENISLIK // 2, y_pos)
    render_text(f"{int(game_data.sfx_volume * 100)}%", assets.FONTS["kucuk"], settings.SARI, surface, settings.GENISLIK // 2, y_pos + 40)
    render_text("Değiştir: <- (A) / (D) ->", assets.FONTS["minik"], settings.KIRMIZI, surface, settings.GENISLIK // 2, y_pos + 70)
    y_pos += spacing * 2

    render_text("Tam Ekran (F11)", assets.FONTS["orta"], settings.BEYAZ, surface, settings.GENISLIK // 2, settings.YUKSEKLIK - 150)
    render_text("Geri dönmek için ESC", assets.FONTS["orta"], settings.YESIL, surface, settings.GENISLIK // 2, settings.YUKSEKLIK - 100)

def draw_upgrade_screen(surface, game_data):
    surface.fill((20, 20, 80))
    render_text("BÖLÜM TAMAMLANDI!", assets.FONTS["orta"], settings.YESIL, surface, settings.GENISLIK // 2, 30)
    render_text("YÜKSELTMELER", assets.FONTS["buyuk"], settings.YESIL, surface, settings.GENISLIK // 2, 80)
    render_text(f"Puan: {game_data.puan}", assets.FONTS["orta"], settings.SARI, surface, settings.GENISLIK // 2, 150)

    y_pos = 220 # Adjusted starting y
    spacing = 75 # Adjusted spacing

    options_data = [
        ("speed", f"[1] Hız Sv {game_data.upgrade_levels['speed']}/{game_data.upgrade_max_levels['speed']} (Mevcut: {game_data.oyuncu.hiz:.1f})"),
        ("fire_rate", f"[2] Atış Hızı Sv {game_data.upgrade_levels['fire_rate']}/{game_data.upgrade_max_levels['fire_rate']} ({game_data.oyuncu.shoot_delay}ms)"),
        ("max_bullets", f"[3] Maks. Mermi Sv {game_data.upgrade_levels['max_bullets']}/{game_data.upgrade_max_levels['max_bullets']} ({game_data.oyuncu.max_bullets})"),
        ("lives", f"[4] Can Satın Al Sv {game_data.upgrade_levels['lives']}/{game_data.upgrade_max_levels['lives']} (Mevcut: {'1 (Insta Death)' if game_data.difficulty == settings.Difficulty.INSTA_DEATH else game_data.oyuncu.can})"),
        ("parry", f"[5] Kılıç Savuşturma Sv {game_data.upgrade_levels['parry']}/{game_data.upgrade_max_levels['parry']} (Sağ Tık)"),
        ("parry_cooldown", f"[6] Savuşturma Cooldown Sv {game_data.upgrade_levels['parry_cooldown']}/{game_data.upgrade_max_levels['parry_cooldown']} ({game_data.oyuncu.parry_cooldown / 1000:.1f}s)")
    ]

    for key, text in options_data:
        cost = game_data.get_upgrade_cost(key)
        is_maxed = cost is None
        cost_text = "MAKS SEVİYE" if is_maxed else f"Bedel: {cost}"
        if key == "parry" and game_data.upgrade_levels["parry"] >= game_data.upgrade_max_levels["parry"]:
            cost_text = "SATIN ALINDI"
            
        render_text(text, assets.FONTS["kucuk"], settings.BEYAZ, surface, settings.GENISLIK // 2, y_pos)
        cost_color = settings.KIRMIZI if is_maxed and key != "parry" else (settings.YESIL if key=="parry" and is_maxed else settings.SARI)
        render_text(cost_text, assets.FONTS["minik"], cost_color, surface, settings.GENISLIK // 2, y_pos + 30)
        y_pos += spacing
    
    render_text("Sonraki Bölüme Geçmek İçin ENTER", assets.FONTS["orta"], settings.YESIL, surface, settings.GENISLIK // 2, settings.YUKSEKLIK - 70)

def draw_game_over_screen(surface, game_data):
    surface.fill(settings.SIYAH)
    render_text("OYUN BİTTİ!", assets.FONTS["buyuk"], settings.KIRMIZI, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 3)
    render_text(f"Skorunuz: {game_data.puan}", assets.FONTS["orta"], settings.PEMBE, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 2)
    if game_data.puan > game_data.high_score:
        render_text(f"Yeni Yüksek Skor: {game_data.puan}", assets.FONTS["orta"], settings.YESIL, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 2 + 60)
    else:
        render_text(f"Yüksek Skor: {game_data.high_score}", assets.FONTS["orta"], settings.PEMBE, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 2 + 60)
    render_text("Ana Menü için ENTER", assets.FONTS["orta"], settings.BEYAZ, surface, settings.GENISLIK // 2, settings.YUKSEKLIK * 2 // 3 + 20)

def draw_win_screen(surface, game_data):
    if game_data.tebrikler_img and game_data.tebrikler_img.get_width() > 64 : # Check if not placeholder
        surface.blit(game_data.tebrikler_img, (0,0))
    else:
        surface.fill(settings.YESIL_KOYU)

    render_text(f"Tebrikler! Skorunuz: {game_data.puan}", assets.FONTS["orta"], settings.SIYAH, surface, settings.GENISLIK // 2, 60)
    if game_data.puan > game_data.high_score:
        render_text(f"Yeni Yüksek Skor: {game_data.puan}!", assets.FONTS["kucuk"], settings.YESIL, surface, settings.GENISLIK // 2, 120)
    render_text("Ana Menü için ENTER", assets.FONTS["orta"], settings.SIYAH, surface, settings.GENISLIK // 2, settings.YUKSEKLIK - 80)

def draw_level_transition_screen(surface, game_data):
    surface.fill(settings.SIYAH)
    level_text = f"Bölüm {game_data.bolum_no}"
    if game_data.bolum_no == 5: level_text += " - BOSS!"
    render_text(f"{level_text} Başlıyor...", assets.FONTS["buyuk"], settings.YESIL, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 2 - 50)

def draw_hud(surface, game_data):
    render_text(f"Skor: {game_data.puan}", assets.FONTS["orta"], settings.PEMBE, surface, 15, 10, top_left=True)
    
    level_display_text = f"Bölüm: {game_data.bolum_no}"
    if game_data.bolum_no == 5 and game_data.boss_grup.sprite: level_display_text += " BOSS"
    level_text_width = assets.FONTS["orta"].size(level_display_text)[0]
    render_text(level_display_text, assets.FONTS["orta"], settings.PEMBE, surface, settings.GENISLIK - 15 - level_text_width, 10, top_left=True)

    lives_display_text = f"Can: {'1 (Insta Death)' if game_data.difficulty == settings.Difficulty.INSTA_DEATH else game_data.oyuncu.can}"
    render_text(lives_display_text, assets.FONTS["orta"], settings.KIRMIZI, surface, 15, 60, top_left=True)

    if game_data.oyuncu.has_parry and game_data.sword_icon:
        icon_x = settings.GENISLIK - 75
        icon_y = 65
        icon_rect = game_data.sword_icon.get_rect(topleft=(icon_x, icon_y))
        cooldown_remaining = game_data.oyuncu.get_parry_cooldown_remaining()
        bg_color = settings.YESIL_KOYU if cooldown_remaining == 0 else settings.KOYU_KIRMIZI

        bg_rect_size = 60
        bg_rect = pygame.Rect(icon_x - 5, icon_y - 5, bg_rect_size, bg_rect_size)
        pygame.draw.rect(surface, bg_color, bg_rect, border_radius=5)
        surface.blit(game_data.sword_icon, icon_rect)

        if cooldown_remaining > 0:
            cooldown_seconds_text = f"{cooldown_remaining / 1000:.1f}"
            text_w, text_h = assets.FONTS["minik"].size(cooldown_seconds_text)
            render_text(cooldown_seconds_text, assets.FONTS["minik"], settings.BEYAZ, surface, 
                        icon_rect.centerx - text_w // 2, icon_rect.centery - text_h // 2) # Centered on icon
                        
    if game_data.show_boss_unlocked_message:
        message_text = "Boss Savaşı artık ana menüden erişilebilir!" # Turkish
        message_surface, message_rect = assets.FONTS["kucuk"].render(message_text, fgcolor=settings.BEYAZ)
        
        box_padding = 10
        box_rect = pygame.Rect(0,0, message_rect.width + 2 * box_padding, message_rect.height + 2* box_padding)
        box_rect.center = (settings.GENISLIK // 2, settings.YUKSEKLIK - 60)
        
        pygame.draw.rect(surface, settings.KOYU_MAVI, box_rect, border_radius=5)
        pygame.draw.rect(surface, settings.BEYAZ, box_rect, 2, border_radius=5)
        surface.blit(message_surface, (box_rect.x + box_padding, box_rect.y + box_padding))


def draw_boss_defeated_cutscene_elements(surface):
    now = pygame.time.get_ticks()
    if (now // 500) % 2 == 0:
        render_text("X Tuşuna Bas!", assets.FONTS["buyuk"], settings.SARI, surface, settings.GENISLIK // 2, settings.YUKSEKLIK // 2)
