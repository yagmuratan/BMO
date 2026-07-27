# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import sounddevice as sd
# pyrefly: ignore [missing-import]
import soundfile as sf
# pyrefly: ignore [missing-import]
import pygame
from config import SAMPLE_RATE, SILENCE_THRESHOLD

# Otomatik bulunan USB mikrofon index'i (None ise varsayilan cihaz kullanilir)
_USB_MIC_INDEX = None


def ses_cihazlarini_listele():
    """Sistemdeki tum ses giris/cikis cihazlarini konsola bas ve USB mikrofon index'ini bul."""
    global _USB_MIC_INDEX
    
    print("\n" + "=" * 60)
    print("   SES CİHAZLARI LİSTESİ")
    print("=" * 60)
    
    cihazlar = sd.query_devices()
    usb_bulundu = False
    
    print("\n--- GİRİŞ CİHAZLARI (Mikrofonlar) ---")
    for i, cihaz in enumerate(cihazlar):
        if cihaz["max_input_channels"] > 0:
            isaret = ""
            if "usb" in cihaz["name"].lower() and not usb_bulundu:
                isaret = "  <== USB MİKROFON (OTOMATİK SEÇİLDİ)"
                _USB_MIC_INDEX = i
                usb_bulundu = True
            print("  [{}] {} ({}ch, {}Hz){}".format(
                i, cihaz["name"], cihaz["max_input_channels"],
                int(cihaz["default_samplerate"]), isaret
            ))
    
    print("\n--- ÇIKIŞ CİHAZLARI (Hoparlörler) ---")
    for i, cihaz in enumerate(cihazlar):
        if cihaz["max_output_channels"] > 0:
            print("  [{}] {} ({}ch, {}Hz)".format(
                i, cihaz["name"], cihaz["max_output_channels"],
                int(cihaz["default_samplerate"])
            ))
    
    print("\n" + "-" * 60)
    if _USB_MIC_INDEX is not None:
        print("[TAMAM] USB Mikrofon bulundu: Index={}, Ad='{}'".format(
            _USB_MIC_INDEX, cihazlar[_USB_MIC_INDEX]["name"]
        ))
    else:
        varsayilan = sd.default.device[0]
        print("[BILGI] USB mikrofon bulunamadi. Varsayilan giris cihazi kullanilacak (Index={})".format(
            varsayilan
        ))
    print("-" * 60 + "\n")
    
    return _USB_MIC_INDEX


def ses_oynatici_baslat():
    """Ses oynaticiyi hazirla."""
    try:
        pygame.mixer.init()
        print("[TAMAM] pygame ses oynatici hazir!")
    except Exception as e:
        print("[UYARI] pygame baslatilamadi, sounddevice ile devam edilecek: {}".format(e))

def ses_dosyasi_cal(dosya_yolu):
    """Ses dosyasini belirli bir hoparlor indeksine gondererek cal."""
    try:
        import os
        if not os.path.exists(dosya_yolu) or os.path.getsize(dosya_yolu) == 0:
            return
        
        data, samplerate = sf.read(dosya_yolu, dtype="float32")
        hedef_hoparlor_index = 5  # Speakers (Realtek)
        
        sd.play(data, samplerate=samplerate, device=hedef_hoparlor_index)
        sd.wait()
        print("[SES] Yanit basariyla calindi.")
    except Exception as e:
        print(f"[HATA] Ses calinamadi: {e}")
        
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
    """Mikrofondan ses kaydi al. USB mikrofon varsa onu kullanir."""
    audio = sd.rec(int(sure * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="float32", device=_USB_MIC_INDEX)
    sd.wait()
    return audio

def ses_seviyesi_kontrol(audio):
    """Ses seviyesinin esik degerinin uzerinde olup olmadigini kontrol et."""
    return np.abs(audio).mean() > SILENCE_THRESHOLD
