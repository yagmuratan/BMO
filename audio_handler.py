# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import sounddevice as sd
# pyrefly: ignore [missing-import]
import soundfile as sf
# pyrefly: ignore [missing-import]
import pygame
from config import SAMPLE_RATE, SILENCE_THRESHOLD

def ses_oynatici_baslat():
    """Ses oynaticiyi hazirla."""
    try:
        pygame.mixer.init()
        print("[TAMAM] pygame ses oynatici hazir!")
    except Exception as e:
        print("[UYARI] pygame baslatilamadi, sounddevice ile devam edilecek: {}".format(e))

def ses_dosyasi_cal(dosya_yolu):
    """WAV dosyasini varsayilan cikis cihazindan cal."""
    data, samplerate = sf.read(dosya_yolu, dtype="float32")
    sd.play(data, samplerate)
    sd.wait()

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
