import sys
import threading
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pygame
# pyrefly: ignore [missing-import]
from openai import OpenAI

# Modul importlari
import config
from audio_handler import (
    ses_cihazlarini_listele, ses_oynatici_baslat, ses_kaydet, bip_cal, ses_seviyesi_kontrol
)
from stt_handler import whisper_modelini_yukle, hizli_metne_cevir, sesi_metne_cevir
from brain_handler import (
    wake_word_kontrol, wake_word_sonrasi_metni_al, chatgpt_yanit_al
)
from tts_handler import yaniti_seslendir


class SesliAsistan:
    """
    DÜ-ASİSTAN sesli asistan motoru.
    Arka plan thread'inde calisarak wake word dinler ve sesli yanit verir.
    main.py'den start()/stop() ile kontrol edilebilir.
    """

    def __init__(self, eyes=None):
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self.eyes = eyes
        self._whisper_model = None
        self._openai_client = None
        self._hazir = False
        self._manual_wake_event = threading.Event()

    @property
    def aktif(self):
        """Asistanin calisip calismadigini dondur."""
        return self._running

    def start(self):
        """Sesli asistani arka planda baslat."""
        with self._lock:
            if self._running:
                print("[DÜ-ASİSTAN] Sesli asistan zaten çalışıyor.")
                return
            self._running = True

        self._thread = threading.Thread(target=self._calistir, daemon=True)
        self._thread.start()
        print("[DÜ-ASİSTAN] Sesli asistan arka planda başlatıldı.")
        print("[DÜ-ASİSTAN] Uyandırma komutu: \"Hey, Merhaba, Selam veya Asistan\"")
        print("[DÜ-ASİSTAN] Terminalde '9' tuşu ile de asistanı uyandırabilirsiniz.")

    def manual_wake(self):
        """Terminaldeki 9 komutu ile asistani disaridan uyandirma."""
        if not self._running:
            print("[UYARI] Sesli asistan çalışmıyor. Önce 't' ile başlatın.")
            return
        self._manual_wake_event.set()
        print("[TETIK] Manuel uyandırma sinyali gönderildi.")

    def stop(self):
        """Sesli asistani durdur."""
        with self._lock:
            if not self._running:
                print("[DÜ-ASİSTAN] Sesli asistan zaten durmuş.")
                return
            self._running = False

        if self._thread:
            self._thread.join(timeout=8.0)
            self._thread = None
        print("[DÜ-ASİSTAN] Sesli asistan durduruldu.")

    def _baslat_bilesenler(self):
        """Whisper modeli, OpenAI client ve ses oynaticiyi hazirla."""
        if self._hazir:
            return True

        try:
            # API anahtarini kontrol et
            if not config.OPENAI_API_KEY:
                print("[HATA] OpenAI API anahtari ayarlanmamis!")
                print("[BILGI] $env:OPENAI_API_KEY='sk-...' ile ayarlayin.")
                return False

            # Ses cihazlarini listele ve USB mikrofonu otomatik bul
            ses_cihazlarini_listele()

            # Whisper modelini yukle
            self._whisper_model = whisper_modelini_yukle()

            # Ses oynaticiyi baslat
            ses_oynatici_baslat()

            # OpenAI client olustur
            self._openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

            self._hazir = True
            return True

        except Exception as e:
            print("[HATA] Bilesen baslatma hatasi: {}".format(e))
            return False

    def _calistir(self):
        """Sesli asistan ana dongusu (arka plan thread'inde calisir)."""
        # Bilesenleri hazirla
        if not self._baslat_bilesenler():
            print("[HATA] Bilesenler baslatilamadi. Sesli asistan durduruluyor.")
            self._running = False
            return

        # Konusma gecmisi
        mesajlar = [{"role": "system", "content": config.SYSTEM_PROMPT}]

        print("\n[BILGI] \"Hey, Merhaba, Selam veya Asistan\" diyerek asistani uyandirin.")
        print("[BILGI] Terminalde '9' tusu ile de asistani uyandirabilirsiniz.")
        print("-" * 55)
        print("[DINLEME] Uyandirma komutu bekleniyor...\n")

        is_active = False

        while self._running:
            try:
                komut_metni = ""

                if not is_active:
                    # --- Manuel uyandırma kontrolü ---
                    if self._manual_wake_event.is_set():
                        self._manual_wake_event.clear()
                        print("\n[UYANIK] Manuel uyandırma komutu alındı! (Tuş 9)")
                        if self.eyes:
                            self.eyes.set_emotion("normal")
                        is_active = True
                        bip_cal()

                        import random
                        secilen_yanit = random.choice(config.WAKE_RESPONSES)
                        print("\n[DÜ-ASİSTAN] {}".format(secilen_yanit))
                        yaniti_seslendir(self._openai_client, secilen_yanit)

                        print("[MIKROFON] Komutunuzu soyleyin... ({} saniye)".format(config.COMMAND_LISTEN_SECONDS))
                        komut_audio = ses_kaydet(config.COMMAND_LISTEN_SECONDS)
                        komut_metni = sesi_metne_cevir(self._whisper_model, komut_audio)
                    else:
                        # --- Adim 1: Kisa ses parcasi kaydet (Wake Word Bekleme) ---
                        print("[BİLGİ] Dinleniyor... Mikrofondan ses bekleniyor")
                        audio = ses_kaydet(config.WAKE_LISTEN_SECONDS)

                        if not self._running:
                            break

                        # Sessizse Whisper'a gonderme
                        if not ses_seviyesi_kontrol(audio):
                            continue

                        if config.DEBUG_MODE:
                            print("[DEBUG] Ses seviyesi: {:.4f}".format(np.abs(audio).mean()))

                        # --- Adim 2: Hizli transkripsiyon ---
                        metin = hizli_metne_cevir(self._whisper_model, audio)
                        if not metin:
                            continue

                        if config.DEBUG_MODE:
                            print("[DEBUG] Whisper duydu: '{}'".format(metin))

                        # --- Adim 3: Wake word var mi kontrol et ---
                        if not wake_word_kontrol(metin):
                            continue

                        print("\n[UYANIK] Uyandırma komutu algilandi!")
                        if self.eyes:
                            self.eyes.set_emotion("normal")
                        is_active = True
                        bip_cal()

                        komut_metni = wake_word_sonrasi_metni_al(metin)

                    if not komut_metni:
                        import random
                        secilen_yanit = random.choice(config.WAKE_RESPONSES)
                        print("\n[DÜ-ASİSTAN] {}".format(secilen_yanit))
                        yaniti_seslendir(self._openai_client, secilen_yanit)

                        print("[MIKROFON] Komutunuzu soyleyin... ({} saniye)".format(config.COMMAND_LISTEN_SECONDS))
                        komut_audio = ses_kaydet(config.COMMAND_LISTEN_SECONDS)
                        komut_metni = sesi_metne_cevir(self._whisper_model, komut_audio)

                else:
                    # --- AKTIF MOD ---
                    print("[MIKROFON] Sizi dinliyorum... ({} saniye)".format(config.COMMAND_LISTEN_SECONDS))
                    komut_audio = ses_kaydet(config.COMMAND_LISTEN_SECONDS)

                    if not self._running:
                        break

                    komut_metni = sesi_metne_cevir(self._whisper_model, komut_audio)

                    if not komut_metni:
                        continue

                if komut_metni:
                    # --- Adim 4: ChatGPT'ye gonder ---
                    mesajlar.append({"role": "user", "content": komut_metni})
                    yanit = chatgpt_yanit_al(self._openai_client, mesajlar)

                    if yanit:
                        mesajlar.append({"role": "assistant", "content": yanit})
                        
                        # --- Ekran Durum Kontrolü (Instagram & Duygu) ---
                        if self.eyes:
                            import re
                            import threading
                            
                            ig_match = re.search(r"@([A-Za-z0-9_.]+)", yanit)
                            sevgi_sozcukleri = ["harika", "süper", "muhteşem", "bayıldım", "mükemmel", "canım", "sevgi", "seviyorum", "mutluluk", "şans"]
                            kalp_yap = any(kelime in yanit.lower() for kelime in sevgi_sozcukleri)
                            
                            if ig_match:
                                self.eyes.set_emotion("instagram_logo", ig_match.group(0))
                            elif kalp_yap:
                                self.eyes.set_emotion("heart")
                                
                        # --- Adim 5: Sesli yanit ver ---
                        yaniti_seslendir(self._openai_client, yanit)
                        
                        # Konuşma bittikten 5 saniye sonra normale dön
                        if self.eyes:
                            def reset_eyes():
                                import time
                                time.sleep(5.0)
                                if self.eyes and self.eyes.emotion in ["instagram_logo", "heart"]:
                                    self.eyes.set_emotion("normal")
                            threading.Thread(target=reset_eyes, daemon=True).start()
                    else:
                        mesajlar.pop()

                    if is_active:
                        print("\n[DINLEME] Sizi dinliyorum... (Yeni komut bekliyor)\n")
                    else:
                        print("\n[DINLEME] Uyandirma komutu bekleniyor...\n")

            except Exception as e:
                if self._running:
                    print("[HATA] Sesli asistan dongusunde hata: {}".format(e))
                    import traceback
                    traceback.print_exc()

        print("[DÜ-ASİSTAN] Sesli asistan dongusu sonlandi.")


# --- Bagimsiz calistirma (main_voice.py direkt calistirilirsa) ---
def ana_dongu():
    """Ana uygulama dongusu - bagimsiz calistirma icin."""
    print("=" * 55)
    print("   DÜ-ASİSTAN - Sesli Asistan")
    print("   Uyandirma komutu: \"Hey, Merhaba, Selam, Asistan\"")
    print("=" * 55)

    asistan = SesliAsistan()
    asistan.start()

    try:
        # Ana thread'i canlı tut
        while asistan.aktif:
            import time
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n[CIKIS] Hosca kalin!")
    finally:
        asistan.stop()
        try:
            pygame.mixer.quit()
        except:
            pass


if __name__ == "__main__":
    ana_dongu()
