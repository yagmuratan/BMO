import threading
import time
import math
import os

try:
    from luma.core.interface.serial import spi
    from luma.lcd.device import st7735
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[HATA] luma.lcd veya Pillow yuklu degil!")
    print("[BILGI] Terminalde su komutu calistirin: pip install luma.lcd Pillow")
    import sys
    sys.exit(1)


def draw_scaled_text(draw, image, text, y_position, max_width=120, default_font_size=18):
    """
    Metni verilen Pillow yüzeyine dinamik font ölçeklendirmesiyle ortalayarak çizer.
    """
    font_size = default_font_size
    min_font_size = 8
    font = ImageFont.load_default()
    
    while font_size >= min_font_size:
        try:
            # Raspberry Pi OS uzerinde genellikle DejaVu veya FreeMono bulunur
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("FreeSansBold.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
                break
                
        # Metin genisligini hesapla (Pillow 8+ uyumlu)
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
        except AttributeError:
            text_width, _ = draw.textsize(text, font=font)
            
        if text_width <= max_width:
            break
        font_size -= 1

    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
    except AttributeError:
        text_width, _ = draw.textsize(text, font=font)
        
    x_position = (image.width - text_width) // 2
    draw.text((x_position, y_position), text, font=font, fill="white")


class GamboadEyes:
    def __init__(self, width=128, height=128):
        """
        DÜ-ASİSTAN Donanımsal TFT (ST7735) Göz Sınıfı.
        """
        self.width = width
        self.height = height
        self.emotion = "normal"
        self.instagram_handle = ""
        self.is_talking = False
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Zamanlayıcılar
        self.last_blink_time = time.time()
        self.blink_duration = 0.15 
        
        # Luma.LCD Donanım Başlatma
        try:
            print("[EYES] SPI Arayuzu baslatiliyor...")
            # Kullanicinin verdigi pinler: DC=GPIO 24, RST=GPIO 25
            # port=0, device=0 demek CE0 (GPIO 8) pinini Chip Select olarak kullanir
            self.serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)
            
            # ST7735 cihazi (rotate=1 ile 90 derece saga donduruldu)
            self.device = st7735(self.serial, width=self.width, height=self.height, bgr=False, rotate=1)
            print("[EYES] ST7735 Ekran basariyla baglandi.")
        except Exception as e:
            print(f"[HATA] Ekran baglantisi basarisiz: {e}")
            self.device = None

        # Logo Yukleme (Opsiyonel)
        self.du_logo = None
        if os.path.exists("du_logo.png"):
            try:
                logo_img = Image.open("du_logo.png").convert("RGBA")
                self.du_logo = logo_img.resize((100, 40), Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS)
            except Exception as e:
                print(f"[EYES] Logo yukleme hatasi: {e}")

    def start(self):
        if self.running or self.device is None:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[EYES] Donanimsal goz guncellemesi baslatildi.")

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        # Ekrani temizle
        if self.device:
            black_screen = Image.new("RGB", (self.width, self.height), "black")
            self.device.display(black_screen)
            
        print("[EYES] Goz durduruldu.")

    def set_emotion(self, emotion, ig_handle=""):
        valid_emotions = ["normal", "happy", "sad", "angry", "surprised", "sleepy", "heart", "instagram_logo"]
        if emotion in valid_emotions:
            with self.lock:
                self.emotion = emotion
                self.instagram_handle = ig_handle
            print(f"[EYES] Duygu durumu guncellendi: {emotion}")
        else:
            print(f"[EYES] [UYARI] Gecersiz duygu durumu: {emotion}")

    def start_talking(self):
        with self.lock:
            self.is_talking = True

    def stop_talking(self):
        with self.lock:
            self.is_talking = False

    def _draw_rounded_rect(self, draw, coords, radius, fill):
        """Pillow surumune bagli olmaksizin yuvarlak diktortgen cizimi."""
        try:
            draw.rounded_rectangle(coords, radius=radius, fill=fill)
        except AttributeError:
            # Eski Pillow (8.2 oncesi) icin manuel cizim
            x1, y1, x2, y2 = coords
            draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
            draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)
            draw.pieslice([x1, y1, x1+radius*2, y1+radius*2], 180, 270, fill=fill)
            draw.pieslice([x2-radius*2, y1, x2, y1+radius*2], 270, 360, fill=fill)
            draw.pieslice([x1, y2-radius*2, x1+radius*2, y2], 90, 180, fill=fill)
            draw.pieslice([x2-radius*2, y2-radius*2, x2, y2], 0, 90, fill=fill)

    def _run_loop(self):
        fps = 30
        frame_time = 1.0 / fps

        white = (255, 255, 255)
        black = (0, 0, 0)

        while self.running:
            start_time = time.time()
            now = start_time
            
            with self.lock:
                current_emotion = self.emotion
                speaking = self.is_talking
            
            # 1. Blink (Göz Kırpma)
            time_since_blink = now - self.last_blink_time
            if time_since_blink >= 3.0:
                blink_elapsed = time_since_blink - 3.0
                if blink_elapsed < self.blink_duration:
                    progress = blink_elapsed / self.blink_duration
                    blink_val = math.sin(progress * math.pi)
                else:
                    blink_val = 0.0
                    self.last_blink_time = now
            else:
                blink_val = 0.0
                
            # 2. Konuşma Hareketi (Squash & Stretch)
            if speaking:
                talk_scale_y = 1.0 + 0.12 * math.sin(now * 18.0)
                talk_scale_x = 1.0 + 0.04 * math.cos(now * 14.0)
            else:
                talk_scale_y = 1.0
                talk_scale_x = 1.0

            # Gecici sekil arabellegi (Sadece 1 goz cizimi icin)
            eye_temp = Image.new("RGB", (self.width, self.height), "black")
            draw_eye = ImageDraw.Draw(eye_temp)

            # 3. Sekil Cizimleri
            if current_emotion == "normal":
                self._draw_rounded_rect(draw_eye, [37, 24, 37+54, 24+80], 27, white)
                
            elif current_emotion == "happy":
                pts = [(30, 75), (40, 55), (52, 45), (64, 42), (76, 45), (88, 55), (98, 75),
                       (88, 65), (76, 57), (64, 55), (52, 57), (40, 65)]
                draw_eye.polygon(pts, fill=white)
                
            elif current_emotion == "sad":
                self._draw_rounded_rect(draw_eye, [37, 24, 37+54, 24+80], 27, white)
                draw_eye.polygon([(37, 24), (64, 24), (37, 48)], fill=black)
                draw_eye.polygon([(91, 24), (64, 24), (91, 48)], fill=black)
                
            elif current_emotion == "angry":
                self._draw_rounded_rect(draw_eye, [37, 24, 37+54, 24+80], 27, white)
                draw_eye.polygon([(37, 24), (64, 48), (91, 24), (91, 0), (37, 0)], fill=black)
                
            elif current_emotion == "surprised":
                draw_eye.ellipse([26, 26, 102, 102], fill=white)
                
            elif current_emotion == "sleepy":
                self._draw_rounded_rect(draw_eye, [34, 49, 94, 79], 15, white)
                
            elif current_emotion == "heart":
                draw_eye.ellipse([30, 34, 66, 70], fill=white)
                draw_eye.ellipse([62, 34, 98, 70], fill=white)
                draw_eye.polygon([(30, 56), (98, 56), (64, 96)], fill=white)

            # 4. Olcekleme ve Ana Ekrana Birlestirme
            final_scale_x = talk_scale_x
            final_scale_y = talk_scale_y * (1.0 - blink_val)
            
            main_image = Image.new("RGB", (self.width, self.height), "black")
            main_draw = ImageDraw.Draw(main_image)

            if current_emotion != "instagram_logo":
                if final_scale_y > 0.05:
                    new_w = max(1, int(self.width * final_scale_x))
                    new_h = max(1, int(self.height * final_scale_y))
                    
                    try:
                        resample_mode = Image.Resampling.BILINEAR
                    except AttributeError:
                        resample_mode = Image.BILINEAR
                        
                    scaled_eye = eye_temp.resize((new_w, new_h), resample=resample_mode)
                    
                    x_offset = (self.width - new_w) // 2
                    y_offset = (self.height - new_h) // 2
                    main_image.paste(scaled_eye, (x_offset, y_offset))
                else:
                    main_draw.line([(34, 64), (94, 64)], fill=white, width=6)
            else:
                # Instagram Arayuzu
                if self.du_logo:
                    logo_w, logo_h = self.du_logo.size
                    main_image.paste(self.du_logo, ((self.width - logo_w)//2, 37 - logo_h//2), self.du_logo)
                else:
                    draw_scaled_text(main_draw, main_image, "DUZCE UNI", 27, max_width=120, default_font_size=16)
                    
                draw_scaled_text(main_draw, main_image, "INSTAGRAM:", 75, max_width=120, default_font_size=14)
                
                if self.instagram_handle:
                    draw_scaled_text(main_draw, main_image, self.instagram_handle, 101, max_width=120, default_font_size=16)

            # Ekrana Gonder
            self.device.display(main_image)
            
            # FPS Sabitleyici
            elapsed = time.time() - start_time
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)

if __name__ == "__main__":
    print("Goz testi baslatiliyor...")
    eyes = GamboadEyes()
    eyes.start()
    try:
        while True:
            # Saniyede bir duygu degistir (Test icin)
            for emo in ["normal", "happy", "angry", "surprised", "sleepy", "heart"]:
                eyes.set_emotion(emo)
                time.sleep(2)
                eyes.start_talking()
                time.sleep(2)
                eyes.stop_talking()
            
            eyes.set_emotion("instagram_logo", "@duzceuniversite")
            time.sleep(4)
    except KeyboardInterrupt:
        eyes.stop()
