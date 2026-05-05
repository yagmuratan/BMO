"""
Sesli Asistan - Wake Word + Faster Whisper + ChatGPT + OpenAI TTS
=================================================================
- Surekli mikrofonu dinler
- "GumBot" uyandirma komutunu algiladiginda aktif olur
- Kullanicinin komutunu Faster Whisper ile metne cevirir
- ChatGPT API'ye gonderir
- OpenAI TTS API ile dogal sesli yanit verir
"""

import os
import sys
import tempfile
import time
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
from openai import OpenAI
import pygame


# --- Ayarlar -----------------------------------------------
OPENAI_API_KEY = "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"
WHISPER_MODEL_SIZE = "small"      # tiny, base, small, medium, large-v3
SAMPLE_RATE = 16000               # Whisper 16kHz bekler
LANGUAGE = "tr"                   # Turkce tanima
GPT_MODEL = "gpt-5.4-nano"      # Kullanilacak ChatGPT modeli
TTS_MODEL = "tts-1"              # tts-1 (hizli) veya tts-1-hd (kaliteli)
TTS_VOICE = "nova"               # alloy, echo, fable, onyx, nova, shimmer

# Wake word ayarlari
WAKE_WORD = "hey gambıt"         # Uyandirma komutu (kucuk harf)
WAKE_LISTEN_SECONDS = 3          # Uyandirma icin dinleme parcasi (saniye)
COMMAND_LISTEN_SECONDS = 5        # Komut icin dinleme suresi (saniye)

# Ses esigi - sessizlikte gereksiz islem yapmayi onler
SILENCE_THRESHOLD = 0.008        # Bu seviyenin altindaki ses sessizlik sayilir

# Debug modu - Whisper'in ne duyduklarini gormek icin True yap
DEBUG_MODE = True


def api_anahtarini_kontrol_et():
    """OpenAI API anahtarinin ayarli oldugundan emin ol."""
    global OPENAI_API_KEY
    if not OPENAI_API_KEY:
        OPENAI_API_KEY = input("OpenAI API anahtarinizi girin: ").strip()
        if not OPENAI_API_KEY:
            print("[HATA] API anahtari girilmedi. Cikiliyor...")
            sys.exit(1)


def whisper_modelini_yukle():
    """Faster Whisper modelini yukle."""
    print("[YUKLENIYOR] Whisper modeli yukleniyor ({})...".format(WHISPER_MODEL_SIZE))
    model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    print("[TAMAM] Whisper modeli hazir!")
    return model


def ses_oynatici_baslat():
    """pygame mixer'i ses oynatmak icin baslat."""
    pygame.mixer.init()
    print("[TAMAM] Ses oynatici hazir!")


def onay_sesi_olustur():
    """Uyandirma komutu algilandiginda calacak kisa bir bip sesi olustur."""
    sure = 0.15  # saniye
    frekans = 880  # Hz (A5 notasi)
    t = np.linspace(0, sure, int(SAMPLE_RATE * sure), False)
    # Kisa yumusak bip sesi
    bip = np.sin(2 * np.pi * frekans * t) * 0.5
    # Fade in/out
    fade = int(SAMPLE_RATE * 0.02)
    bip[:fade] *= np.linspace(0, 1, fade)
    bip[-fade:] *= np.linspace(1, 0, fade)
    return bip.astype(np.float32)


def bip_cal():
    """Kisa onay bip sesi cal."""
    bip = onay_sesi_olustur()
    sd.play(bip, SAMPLE_RATE)
    sd.wait()


def ses_kaydet(sure):
    """Mikrofondan ses kaydi al."""
    audio = sd.rec(int(sure * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="float32")
    sd.wait()
    return audio


def ses_seviyesi_kontrol(audio):
    """Ses seviyesinin esik degerinin uzerinde olup olmadigini kontrol et."""
    return np.abs(audio).mean() > SILENCE_THRESHOLD


def hizli_metne_cevir(model, audio):
    """Whisper ile sesi hizlica metne cevir (wake word tespiti icin)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, SAMPLE_RATE)
    tmp.close()

    try:
        segments, _ = model.transcribe(tmp.name, language=LANGUAGE,
                                        beam_size=1,
                                        vad_filter=True)
        metin = " ".join([s.text for s in segments]).strip()
    except Exception:
        metin = ""
    finally:
        os.unlink(tmp.name)

    return metin


def sesi_metne_cevir(model, audio):
    """Faster Whisper ile sesi metne cevir (tam komut icin)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, SAMPLE_RATE)
    tmp.close()

    print("[ISLEM] Ses metne cevriliyor...")
    segments, _ = model.transcribe(tmp.name, language=LANGUAGE,
                                    beam_size=5)

    metin = " ".join([s.text for s in segments]).strip()
    os.unlink(tmp.name)

    if metin:
        print("[METIN] Algilanan: {}".format(metin))
    else:
        print("[UYARI] Ses algilanamadi.")

    return metin


def noktalama_temizle(metin):
    """Metindeki noktalama isaretlerini kaldir (wake word eslesmesi icin)."""
    import re
    return re.sub(r'[.,!?;:\-\'"()\[\]{}]', '', metin)


def wake_word_kontrol(metin):
    """Metinde uyandirma komutu var mi kontrol et.
    
    Regex tabanli esnek eslestirme:
    'hey/he/hei' + 'gam' ile baslayan herhangi bir kelime.
    Whisper 'gamut', 'gamble', 'gambit', 'gammet' vb. yazsa bile yakalar.
    """
    import re
    metin_kucuk = noktalama_temizle(metin.lower().strip())
    # "hey" (veya "he", "hei") + "gam" ile baslayan bir kelime
    pattern = r'\b(hey|he|hei)\s+gam\w*'
    return bool(re.search(pattern, metin_kucuk))


def wake_word_sonrasi_metni_al(metin):
    """Uyandirma komutundan sonraki metni cikar (varsa)."""
    import re
    metin_kucuk = noktalama_temizle(metin.lower())
    # "hey" (veya "he", "hei") + "gam" ile baslayan bir kelime
    pattern = r'\b(hey|he|hei)\s+gam\w*'
    match = re.search(pattern, metin_kucuk)
    if match:
        kalan = metin[match.end():].strip()
        kalan = kalan.lstrip(".,!? ")
        if len(kalan) > 2:
            return kalan
    return ""


def chatgpt_yanit_al(client, mesajlar):
    """ChatGPT'ye mesaj gonder ve yanit al."""
    print("[CHATGPT] Dusunuyor...")
    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=mesajlar,
            max_completion_tokens=500,
            temperature=0.7,
        )
        yanit = response.choices[0].message.content.strip()
        print("[YANIT] ChatGPT: {}".format(yanit))
        return yanit
    except Exception as e:
        print("[HATA] ChatGPT hatasi: {}".format(e))
        return None


def yaniti_seslendir(client, metin):
    """OpenAI TTS API ile metni dogal sesle oku."""
    if not metin:
        return

    print("[SES] Yanit seslendiriliyor...")

    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()

        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=metin,
        )

        response.stream_to_file(tmp_path)

        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.unload()
        os.unlink(tmp_path)

    except Exception as e:
        print("[HATA] TTS hatasi: {}".format(e))
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass


def ana_dongu():
    """Ana uygulama dongusu - wake word ile calisir."""
    print("=" * 55)
    print("   GumBot - Sesli Asistan")
    print("   Uyandirma komutu: \"Hey Gambıt\"")
    print("   Faster Whisper + ChatGPT + OpenAI TTS")
    print("=" * 55)

    # API anahtarini kontrol et
    api_anahtarini_kontrol_et()

    # Bilesenleri baslat
    whisper_model = whisper_modelini_yukle()
    ses_oynatici_baslat()
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    # Konusma gecmisi
    mesajlar = [
        {"role": "system", "content": (
            "Sen popüler çizgi dizi karakteri Gumball Watterson'sın. 12 yaşında, "
            "aşırı enerjik, bazen sakar ama her zaman komik ve laf sokmaya bayılan bir çocuksun.\n\n"
            "- Konuşma tarzın hızlı, heyecanlı ve sarkastik olmalı.\n"
            "- Yanıtların kısa ve öz olsun (maksimum 2-3 cümle), çünkü bir robotun "
            "üzerinden konuşuyorsun ve uzun metinler sıkıcı oluyor.\n"
            "- Darwin'den veya okulda başına gelen saçma olaylardan ufak referanslar verebilirsin.\n\n"
            "Sana gelen ses girişleri gürültülü bir ortamdan geliyor. Eğer sana gelen cümle "
            "anlamsızsa veya içinde yazım hataları varsa, cümlenin gelişinden ne denmek istendiğini "
            "tahmin et. Eğer hiçbir şey anlamadıysan \"Hah? Bu gürültüde seni duymak Elmore "
            "lisesindeki yemekhanede konuşmaya çalışmaktan daha zor! Tekrar söyler misin?\" "
            "gibi Gumball tarzı bir tepki ver.\n\n"
            "Sana söylenen her şeye Gumball kişiliğiyle yanıt ver ve asla bir yapay zeka "
            "olduğunu belli etme."
        )}
    ]

    print("\n[BILGI] \"Hey Gambıt\" diyerek asistani uyandirin.")
    print("[BILGI] Cikis icin Ctrl+C basin.")
    print("-" * 55)
    print("[DINLEME] Uyandirma komutu bekleniyor...\n")

    try:
        while True:
            # --- Adim 1: Kisa ses parcasi kaydet ---
            audio = ses_kaydet(WAKE_LISTEN_SECONDS)

            # Sessizse Whisper'a gonderme (CPU tasarrufu)
            ses_seviyesi = np.abs(audio).mean()
            if ses_seviyesi < SILENCE_THRESHOLD:
                continue

            if DEBUG_MODE:
                print("[DEBUG] Ses seviyesi: {:.4f}".format(ses_seviyesi))

            # --- Adim 2: Hizli transkripsiyon (wake word tespiti) ---
            metin = hizli_metne_cevir(whisper_model, audio)

            if not metin:
                continue

            if DEBUG_MODE:
                print("[DEBUG] Whisper duydu: '{}'".format(metin))

            # --- Adim 3: Wake word var mi kontrol et ---
            if not wake_word_kontrol(metin):
                continue

            # Wake word algilandi!
            print("\n[UYANIK] \"Hey Gambıt\" algilandi!")
            bip_cal()  # Onay sesi

            # Wake word ile birlikte komut da soylenmis olabilir
            ek_metin = wake_word_sonrasi_metni_al(metin)

            if ek_metin:
                # Wake word ile birlikte komut geldi
                komut_metni = ek_metin
                print("[METIN] Komut: {}".format(komut_metni))
            else:
                # Komutu ayri olarak dinle
                print("[MIKROFON] Komutunuzu soyleyin... ({} saniye)".format(COMMAND_LISTEN_SECONDS))
                komut_audio = ses_kaydet(COMMAND_LISTEN_SECONDS)
                komut_metni = sesi_metne_cevir(whisper_model, komut_audio)

                if not komut_metni:
                    print("[DINLEME] Uyandirma komutu bekleniyor...\n")
                    continue

            # --- Adim 4: ChatGPT'ye gonder ---
            mesajlar.append({"role": "user", "content": komut_metni})
            yanit = chatgpt_yanit_al(openai_client, mesajlar)

            if yanit:
                mesajlar.append({"role": "assistant", "content": yanit})
                # --- Adim 5: Sesli yanit ver ---
                yaniti_seslendir(openai_client, yanit)
            else:
                mesajlar.pop()

            print("\n[DINLEME] Uyandirma komutu bekleniyor...\n")

    except KeyboardInterrupt:
        print("\n\n[CIKIS] Hosca kalin!")
        pygame.mixer.quit()
        sys.exit(0)


if __name__ == "__main__":
    ana_dongu()
