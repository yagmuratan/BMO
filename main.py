"""
Sesli Asistan - Faster Whisper + ChatGPT + TTS
===============================================
- Mikrofondan ses kaydi alir
- Faster Whisper ile metne cevirir
- ChatGPT API'ye gonderir
- Gelen yaniti sesli olarak okur
"""

import os
import sys
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
from openai import OpenAI
import pyttsx3


# --- Ayarlar -----------------------------------------------
OPENAI_API_KEY = "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"
WHISPER_MODEL_SIZE = "base"       # tiny, base, small, medium, large-v3
SAMPLE_RATE = 16000               # Whisper 16kHz bekler
RECORD_SECONDS = 5                # Kayit suresi (saniye)
LANGUAGE = "tr"                   # Turkce tanima
GPT_MODEL = "gpt-5.4-nano"      # Kullanilacak ChatGPT modeli


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


def tts_motorunu_baslat():
    """pyttsx3 TTS motorunu baslat ve ayarla."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)     # Konusma hizi
    engine.setProperty("volume", 1.0)   # Ses seviyesi

    # Turkce ses varsa sec
    voices = engine.getProperty("voices")
    for voice in voices:
        if "turkish" in voice.name.lower() or "tr" in voice.id.lower():
            engine.setProperty("voice", voice.id)
            break

    return engine


def ses_kaydet(sure=RECORD_SECONDS):
    """Mikrofondan ses kaydi al."""
    print("\n[MIKROFON] Konusun... ({} saniye)".format(sure))
    audio = sd.rec(int(sure * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="float32")
    sd.wait()
    print("[TAMAM] Kayit tamamlandi!")
    return audio


def sesi_metne_cevir(model, audio):
    """Faster Whisper ile sesi metne cevir."""
    # Gecici WAV dosyasina kaydet
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, SAMPLE_RATE)
    tmp.close()

    print("[ISLEM] Ses metne cevriliyor...")
    segments, info = model.transcribe(tmp.name, language=LANGUAGE,
                                       beam_size=5)

    metin = " ".join([segment.text for segment in segments]).strip()

    # Gecici dosyayi sil
    os.unlink(tmp.name)

    if metin:
        print("[METIN] Algilanan metin: {}".format(metin))
    else:
        print("[UYARI] Ses algilanamadi.")

    return metin


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


def yaniti_seslendir(engine, metin):
    """Metni sesli olarak oku."""
    if metin:
        print("[SES] Yanit seslendiriliyor...")
        engine.say(metin)
        engine.runAndWait()


def ana_dongu():
    """Ana uygulama dongusu."""
    print("=" * 50)
    print("   Sesli Asistan")
    print("   Faster Whisper + ChatGPT + TTS")
    print("=" * 50)

    # API anahtarini kontrol et
    api_anahtarini_kontrol_et()

    # Bilesenleri baslat
    whisper_model = whisper_modelini_yukle()
    tts_engine = tts_motorunu_baslat()
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    # Konusma gecmisi
    mesajlar = [
        {"role": "system", "content": "Senin ismin Gumbot. Senin karakterin Gumball çizgi filmindeki Gumball gibi davran "
         "Kisa ve oz yanitlar ver."}
    ]

    print("\nKomutlar:")
    print("   ENTER  -> Konusmaya basla")
    print("   'q'    -> Cikis")
    print("   's:N'  -> Kayit suresini N saniye yap (orn: s:10)")
    print("-" * 50)

    kayit_suresi = RECORD_SECONDS

    while True:
        komut = input("\nKonusmak icin ENTER'a basin (q=cikis): ").strip()

        if komut.lower() == "q":
            print("Hosca kalin!")
            break

        if komut.lower().startswith("s:"):
            try:
                kayit_suresi = int(komut.split(":")[1])
                print("[AYAR] Kayit suresi {} saniye olarak ayarlandi.".format(kayit_suresi))
            except ValueError:
                print("[UYARI] Gecersiz sure.")
            continue

        # 1. Ses kaydet
        audio = ses_kaydet(kayit_suresi)

        # 2. Sesi metne cevir
        metin = sesi_metne_cevir(whisper_model, audio)
        if not metin:
            continue

        # 3. ChatGPT'ye gonder
        mesajlar.append({"role": "user", "content": metin})
        yanit = chatgpt_yanit_al(openai_client, mesajlar)

        if yanit:
            mesajlar.append({"role": "assistant", "content": yanit})
            # 4. Yaniti seslendir
            yaniti_seslendir(tts_engine, yanit)
        else:
            # Basarisiz mesaji gecmisten kaldir
            mesajlar.pop()


if __name__ == "__main__":
    ana_dongu()
