import os
import tempfile
import soundfile as sf
from faster_whisper import WhisperModel
from config import WHISPER_MODEL_SIZE, LANGUAGE, SAMPLE_RATE

def whisper_modelini_yukle():
    """Faster Whisper modelini yukle."""
    print("[YUKLENIYOR] Whisper modeli yukleniyor ({})...".format(WHISPER_MODEL_SIZE))
    model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    print("[TAMAM] Whisper modeli hazir!")
    return model

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
