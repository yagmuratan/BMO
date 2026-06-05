import os
import tempfile
from config import TTS_MODEL, TTS_VOICE, TTS_RESPONSE_FORMAT, TTS_SPEED
from audio_handler import ses_dosyasi_cal

def yaniti_seslendir(client, metin):
    """OpenAI TTS API ile metni dogal sesle oku."""
    if not metin:
        return

    print("[SES] Yanit seslendiriliyor...")
    tmp_path = None

    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        tts_kwargs = {
            "model": TTS_MODEL,
            "voice": TTS_VOICE,
            "input": metin[:4096],
            "response_format": TTS_RESPONSE_FORMAT,
            "speed": TTS_SPEED,
        }

        try:
            response = client.audio.speech.create(**tts_kwargs)
            response.stream_to_file(tmp_path)
        except Exception as e:
            print("[HATA] TTS seslendirme hatasi: {}".format(e))
            raise

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise RuntimeError("TTS dosyasi olusmadi veya bos geldi.")

        ses_dosyasi_cal(tmp_path)
        print("[SES] Yanit calindi.")

    except Exception as e:
        print("[HATA] TTS/oynatma hatasi: {}".format(e))
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass
