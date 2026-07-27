import os
import tempfile
from config import TTS_MODEL, TTS_VOICE, TTS_RESPONSE_FORMAT, TTS_SPEED, TTS_STYLE_INSTRUCTIONS
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

        # gpt-4o-mini-tts gibi stil destekleyen modeller icin instructions ekle
        if "4o" in TTS_MODEL:
            tts_kwargs["instructions"] = TTS_STYLE_INSTRUCTIONS

        try:
            response = client.audio.speech.create(**tts_kwargs)
            response.stream_to_file(tmp_path)
            print("[SES] TTS dosyasi olusturuldu: {} ({} bytes)".format(
                tmp_path, os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
            ))
        except Exception as e:
            print("[HATA] TTS API seslendirme hatasi!")
            print("[HATA] Hata tipi: {}".format(type(e).__name__))
            print("[HATA] Detay: {}".format(e))

            # Stil parametresi desteklenmiyorsa stil olmadan tekrar dene
            if "instructions" in tts_kwargs:
                print("[BILGI] Stil yonlendirmesi kaldiriliyor, tekrar deneniyor...")
                del tts_kwargs["instructions"]
                try:
                    response = client.audio.speech.create(**tts_kwargs)
                    response.stream_to_file(tmp_path)
                    print("[SES] TTS dosyasi (stilsiz) olusturuldu.")
                except Exception as e2:
                    print("[HATA] Stilsiz TTS de basarisiz: {}".format(e2))
                    raise e2
            else:
                raise

        if not os.path.exists(tmp_path):
            raise RuntimeError("TTS dosyasi olusturulamadi: dosya bulunamadi.")

        dosya_boyutu = os.path.getsize(tmp_path)
        if dosya_boyutu == 0:
            raise RuntimeError("TTS dosyasi bos (0 byte). API yaniti bos geldi.")

        print("[SES] Dosya oynatiliyor ({} bytes)...".format(dosya_boyutu))
        ses_dosyasi_cal(tmp_path)
        print("[SES] Yanit basariyla calindi.")

    except Exception as e:
        print("[HATA] TTS/oynatma hatasi!")
        print("[HATA] Hata tipi: {}".format(type(e).__name__))
        print("[HATA] Detay: {}".format(e))
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass
