# pyrefly: ignore [missing-import]
import pygame
import threading
import time
import math

class GamboadEyes:
    def __init__(self, width=128, height=128):
        """
        GumBot OLED Goz Simülatörü Sınıfı.
        
        Args:
            width (int): Her bir OLED ekranın genişliği (piksel). Varsayılan 128.
            height (int): Her bir OLED ekranın yüksekliği (piksel). Varsayılan 128.
        """
        self.width = width
        self.height = height
        self.emotion = "normal"
        self.is_talking = False
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Göz kırpma (blink) zamanlayıcısı
        self.last_blink_time = time.time()
        self.blink_duration = 0.15  # Saniye (hızlı bir göz kırpma)
        
        # Ekran boyut katsayıları (128x128 taban alınarak dinamik ölçekleme için)
        self.scale_w = self.width / 128.0
        self.scale_h = self.height / 128.0

    def start(self):
        """Simülasyon penceresini ve arka plan çizim thread'ini başlatır."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[EYES] Göz simülasyonu başlatıldı.")

    def stop(self):
        """Simülasyonu durdurur ve pencereyi kapatır."""
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        print("[EYES] Göz simülasyonu durduruldu.")

    def set_emotion(self, emotion):
        """
        Robotun duygu durumunu değiştirir.
        
        Args:
            emotion (str): 'normal', 'happy', 'sad', 'angry', 'surprised', 'sleepy', 'heart'
        """
        valid_emotions = ["normal", "happy", "sad", "angry", "surprised", "sleepy", "heart"]
        if emotion in valid_emotions:
            with self.lock:
                self.emotion = emotion
            print(f"[EYES] Duygu durumu güncellendi: {emotion}")
        else:
            print(f"[EYES] [UYARI] Geçersiz duygu durumu: {emotion}")

    def start_talking(self):
        """Konuşma animasyonunu başlatır."""
        with self.lock:
            self.is_talking = True
        print("[EYES] Konuşma modu aktif.")

    def stop_talking(self):
        """Konuşma animasyonunu durdurur."""
        with self.lock:
            self.is_talking = False
        print("[EYES] Konuşma modu pasif.")

    def _scale_pts(self, pts):
        """Verilen koordinat çiftlerini dinamik çözünürlüğe göre ölçekler."""
        return [(int(p[0] * self.scale_w), int(p[1] * self.scale_h)) for p in pts]

    def _scale_rect(self, x, y, w, h):
        """Verilen dikdörtgen koordinatlarını çözünürlüğe göre ölçekler."""
        return (int(x * self.scale_w), int(y * self.scale_h), 
                int(w * self.scale_w), int(h * self.scale_h))

    def _scale_circle(self, cx, cy, r):
        """Daire koordinatlarını çözünürlüğe göre ölçekler."""
        center = (int(cx * self.scale_w), int(cy * self.scale_h))
        radius = int(r * ((self.scale_w + self.scale_h) / 2.0))
        return center, radius

    def _run_loop(self):
        """Pygame döngüsünü çalıştıran arka plan thread fonksiyonu."""
        pygame.init()
        pygame.display.set_caption("GumBot OLED Eyes Simulator")
        
        # Simülasyon penceresi boyutları (600x350)
        win_w, win_h = 600, 350
        screen = pygame.display.set_mode((win_w, win_h))
        clock = pygame.time.Clock()
        
        # Fontları yükle
        try:
            font = pygame.font.SysFont("Consolas", 14, bold=True)
            title_font = pygame.font.SysFont("Consolas", 18, bold=True)
        except:
            font = pygame.font.default_font()
            title_font = pygame.font.default_font()
            
        # Tek bir 128x128 (veya self.width x self.height) OLED arabelleği oluştur
        # Gerçek donanımda iki ekran tek SPI hattına (ortak CS) bağlı olduğu için 
        # sadece bu tek arabelleğe çizim yapıp iki OLED'e aynı veriyi göndermiş oluyoruz.
        oled_buffer = pygame.Surface((self.width, self.height))
        
        # Göz çizimi için geçici şeffaf arabellek
        eye_temp_surf = pygame.Surface((self.width, self.height))
        
        while self.running:
            # Event işleme
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
            # Zamanlama parametreleri
            now = time.time()
            with self.lock:
                current_emotion = self.emotion
                speaking = self.is_talking
            
            # --- 1. Göz Kırpma Hesaplaması (Blink) ---
            time_since_blink = now - self.last_blink_time
            if time_since_blink >= 3.0:
                blink_elapsed = time_since_blink - 3.0
                if blink_elapsed < self.blink_duration:
                    progress = blink_elapsed / self.blink_duration
                    # sin(x * pi) ile 0 -> 1 -> 0 pürüzsüz geçiş
                    blink_val = math.sin(progress * math.pi)
                else:
                    blink_val = 0.0
                    self.last_blink_time = now
            else:
                blink_val = 0.0
                
            # --- 2. Konuşma Hareketi Hesaplaması (Squash & Stretch) ---
            if speaking:
                # Göz boyutlarını hafifçe titreştirerek konuşma efekti veriyoruz
                talk_scale_y = 1.0 + 0.12 * math.sin(now * 18.0)
                talk_scale_x = 1.0 + 0.04 * math.cos(now * 14.0)
            else:
                talk_scale_y = 1.0
                talk_scale_x = 1.0
                
            # --- 3. OLED Arabelleğini Temizle (Monokrom Siyah Arka Plan) ---
            oled_buffer.fill((0, 0, 0))
            eye_temp_surf.fill((0, 0, 0))
            eye_temp_surf.set_colorkey((0, 0, 0))
            
            # --- 4. Duygu Durumuna Göre Gözü Geçici Yüzeye Çiz (Beyaz Renk) ---
            white = (255, 255, 255)
            black = (0, 0, 0)
            
            if current_emotion == "normal":
                # Yuvarlak köşeli dik göz şekli
                rect = self._scale_rect(37, 24, 54, 80)
                radius = int(27 * ((self.scale_w + self.scale_h) / 2.0))
                pygame.draw.rect(eye_temp_surf, white, rect, border_radius=radius)
                
            elif current_emotion == "happy":
                # Gülümseyen kavisli göz şekli
                pts = [
                    (30, 75), (40, 55), (52, 45), (64, 42), (76, 45), (88, 55), (98, 75),
                    (88, 65), (76, 57), (64, 55), (52, 57), (40, 65)
                ]
                pygame.draw.polygon(eye_temp_surf, white, self._scale_pts(pts))
                
            elif current_emotion == "sad":
                # Üzgün (dış kenarları aşağı düşmüş) göz şekli
                # Temel gözü çizip üst köşeleri siyah poligonlarla maskeliyoruz
                rect = self._scale_rect(37, 24, 54, 80)
                radius = int(27 * ((self.scale_w + self.scale_h) / 2.0))
                pygame.draw.rect(eye_temp_surf, white, rect, border_radius=radius)
                
                # Sol ve sağ üstten içe doğru eğim maskesi
                pts_left = [(37, 24), (64, 24), (37, 48)]
                pts_right = [(91, 24), (64, 24), (91, 48)]
                pygame.draw.polygon(eye_temp_surf, black, self._scale_pts(pts_left))
                pygame.draw.polygon(eye_temp_surf, black, self._scale_pts(pts_right))
                
            elif current_emotion == "angry":
                # Sinirli (ortası aşağı eğimli) göz şekli
                rect = self._scale_rect(37, 24, 54, 80)
                radius = int(27 * ((self.scale_w + self.scale_h) / 2.0))
                pygame.draw.rect(eye_temp_surf, white, rect, border_radius=radius)
                
                # Ortadan aşağı doğru V şeklinde maskeleme
                pts_cut = [(37, 24), (64, 48), (91, 24), (91, 0), (37, 0)]
                pygame.draw.polygon(eye_temp_surf, black, self._scale_pts(pts_cut))
                
            elif current_emotion == "surprised":
                # Yuvarlak şaşkın göz şekli
                center, radius = self._scale_circle(64, 64, 38)
                pygame.draw.circle(eye_temp_surf, white, center, radius)
                
            elif current_emotion == "sleepy":
                # Yarı kapalı uykulu göz şekli
                rect = self._scale_rect(34, 49, 60, 30)
                radius = int(15 * ((self.scale_w + self.scale_h) / 2.0))
                pygame.draw.rect(eye_temp_surf, white, rect, border_radius=radius)
                
            elif current_emotion == "heart":
                # Kalp şeklinde göz
                c_left, r_left = self._scale_circle(48, 52, 18)
                c_right, r_right = self._scale_circle(80, 52, 18)
                tri_pts = [(30, 56), (98, 56), (64, 96)]
                
                pygame.draw.circle(eye_temp_surf, white, c_left, r_left)
                pygame.draw.circle(eye_temp_surf, white, c_right, r_right)
                pygame.draw.polygon(eye_temp_surf, white, self._scale_pts(tri_pts))

            # --- 5. Ölçekleme, Göz Kırpma ve Konuşma Animasyonunu Uygula ---
            final_scale_x = talk_scale_x
            final_scale_y = talk_scale_y * (1.0 - blink_val)
            
            if final_scale_y > 0.05:
                # Göz açık veya yarı açık: Ölçeklendirip merkeze yerleştir
                new_w = int(self.width * final_scale_x)
                new_h = int(self.height * final_scale_y)
                
                # Boyut 0 olmasın diye min limit koyuyoruz
                new_w = max(1, new_w)
                new_h = max(1, new_h)
                
                scaled_eye = pygame.transform.scale(eye_temp_surf, (new_w, new_h))
                rect = scaled_eye.get_rect(center=(self.width // 2, self.height // 2))
                oled_buffer.blit(scaled_eye, rect)
            else:
                # Tamamen göz kırptığında ince beyaz bir yatay çizgi göster
                line_pts = self._scale_pts([(34, 64), (94, 64)])
                pygame.draw.line(oled_buffer, white, line_pts[0], line_pts[1], max(1, int(6 * self.scale_h)))

            # --- 6. PC Arayüzünü Çiz (Simülatör Görünümü) ---
            screen.fill((18, 18, 20)) # Koyu gri arka plan
            
            # Robot faceplate (yüz plakası)
            pygame.draw.rect(screen, (42, 43, 54), (20, 20, 560, 310), border_radius=40)
            pygame.draw.rect(screen, (70, 72, 88), (20, 20, 560, 310), width=4, border_radius=40)
            
            # OLED ekranların yerleştirileceği bezeller (çerçeveler)
            pygame.draw.rect(screen, (24, 24, 28), (50, 45, 240, 240), border_radius=15)
            pygame.draw.rect(screen, (24, 24, 28), (310, 45, 240, 240), border_radius=15)
            
            # 128x128 boyutundaki tek oled_buffer'ı 220x220 boyutuna genişleterek iki ekrana da blit et
            # Bu işlem iki ekranın fiziksel olarak aynı SPI sinyalini (ortak CS) almasını simüle eder.
            simulated_display_size = (220, 220)
            scaled_display = pygame.transform.scale(oled_buffer, simulated_display_size)
            
            screen.blit(scaled_display, (60, 55))   # Sol Göz Ekranı
            screen.blit(scaled_display, (320, 55))  # Sağ Göz Ekranı
            
            # Metin Etiketleri ve Bilgiler
            title_text = title_font.render("GUMBOT OLED EYES SIMULATOR (SHARED CS)", True, (255, 255, 255))
            screen.blit(title_text, title_text.get_rect(center=(300, 35)))
            
            label_left = font.render("OLED LEFT (CS)", True, (150, 150, 150))
            label_right = font.render("OLED RIGHT (CS)", True, (150, 150, 150))
            screen.blit(label_left, label_left.get_rect(center=(170, 305)))
            screen.blit(label_right, label_right.get_rect(center=(430, 305)))
            
            pygame.display.flip()
            clock.tick(60) # 60 FPS
            
        pygame.quit()
