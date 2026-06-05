import sys
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pygame
# pyrefly: ignore [missing-import]
from openai import OpenAI

# Modul importlari
import config
from audio_handler import (
    ses_oynatici_baslat, ses_kaydet, bip_cal, ses_seviyesi_kontrol
)
from stt_handler import whisper_modelini_yukle, hizli_metne_cevir, sesi_metne_cevir
from brain_handler import (
    wake_word_kontrol, wake_word_sonrasi_metni_al, chatgpt_yanit_al
)
from tts_handler import yaniti_seslendir

def api_anahtarini_kontrol_et():
    """OpenAI API anahtarinin ayarli oldugundan emin ol."""
    if not config.OPENAI_API_KEY:
        config.OPENAI_API_KEY = input("OpenAI API anahtarinizi girin: ").strip()
        if not config.OPENAI_API_KEY:
            print("[HATA] API anahtari girilmedi. Cikiliyor...")
            sys.exit(1)

def ana_dongu():
    """Ana uygulama dongusu - wake word ile calisir."""
    print("=" * 55)
    print("   GumBot - Sesli Asistan (Modularized)")
    print("   Uyandirma komutu: \"Hey Gambıt\"")
    print("=" * 55)

    # API anahtarini kontrol et
    api_anahtarini_kontrol_et()

    # Bilesenleri baslat
    whisper_model = whisper_modelini_yukle()
    ses_oynatici_baslat()
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    # Konusma gecmisi
    mesajlar = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    print("\n[BILGI] \"Hey Gambıt\" diyerek asistani uyandirin.")
    print("[BILGI] Cikis icin Ctrl+C basin.")
    print("-" * 55)
    print("[DINLEME] Uyandirma komutu bekleniyor...\n")

    is_active = False

    try:
        while True:
            komut_metni = ""

            if not is_active:
                # --- Adim 1: Kisa ses parcasi kaydet (Wake Word Bekleme) ---
                audio = ses_kaydet(config.WAKE_LISTEN_SECONDS)

                # Sessizse Whisper'a gonderme
                if not ses_seviyesi_kontrol(audio):
                    continue

                if config.DEBUG_MODE:
                    print("[DEBUG] Ses seviyesi: {:.4f}".format(np.abs(audio).mean()))

                # --- Adim 2: Hizli transkripsiyon ---
                metin = hizli_metne_cevir(whisper_model, audio)
                if not metin:
                    continue

                if config.DEBUG_MODE:
                    print("[DEBUG] Whisper duydu: '{}'".format(metin))

                # --- Adim 3: Wake word var mi kontrol et ---
                if not wake_word_kontrol(metin):
                    continue

                print("\n[UYANIK] \"Hey Gambıt\" algilandi!")
                is_active = True
                bip_cal()

                komut_metni = wake_word_sonrasi_metni_al(metin)

                if not komut_metni:
                    import random
                    secilen_yanit = random.choice(config.WAKE_RESPONSES)
                    print("\n[GAMBOT] {}".format(secilen_yanit))
                    yaniti_seslendir(openai_client, secilen_yanit)

                    print("[MIKROFON] Komutunuzu soyleyin... ({} saniye)".format(config.COMMAND_LISTEN_SECONDS))
                    komut_audio = ses_kaydet(config.COMMAND_LISTEN_SECONDS)
                    komut_metni = sesi_metne_cevir(whisper_model, komut_audio)
            
            else:
                # --- AKTIF MOD ---
                print("[MIKROFON] Sizi dinliyorum... ({} saniye)".format(config.COMMAND_LISTEN_SECONDS))
                komut_audio = ses_kaydet(config.COMMAND_LISTEN_SECONDS)
                komut_metni = sesi_metne_cevir(whisper_model, komut_audio)

                if not komut_metni:
                    continue

            if komut_metni:
                # --- Adim 4: ChatGPT'ye gonder ---
                mesajlar.append({"role": "user", "content": komut_metni})
                yanit = chatgpt_yanit_al(openai_client, mesajlar)

                if yanit:
                    mesajlar.append({"role": "assistant", "content": yanit})
                    # --- Adim 5: Sesli yanit ver ---
                    yaniti_seslendir(openai_client, yanit)
                else:
                    mesajlar.pop()

                if is_active:
                    print("\n[DINLEME] Sizi dinliyorum... (Yeni komut bekliyor)\n")
                else:
                    print("\n[DINLEME] Uyandirma komutu bekleniyor...\n")

    except KeyboardInterrupt:
        print("\n\n[CIKIS] Hosca kalin!")
        try:
            pygame.mixer.quit()
        except:
            pass
        sys.exit(0)

if __name__ == "__main__":
    ana_dongu()
