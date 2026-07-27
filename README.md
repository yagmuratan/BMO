# DÜ-ASİSTAN

Düzce Üniversitesi Düzce Meslek Yüksekokulu tanıtım günleri için geliştirilmiş sesli asistan.

Wake word, Faster Whisper, ChatGPT ve OpenAI TTS kullanarak ziyaretçilere bilgi verir.

## Kurulum

Windows'ta bu projeyi Python 3.11 ile calistirman onerilir:

```powershell
py -3.11 -m pip install -r requirements.txt
```

## API anahtari

Kodun icine API anahtari yazmayin. Ortam degiskeni kullanin.

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="sk-..."
py -3.11 main.py
```

macOS/Linux:

```bash
export OPENAI_API_KEY="sk-..."
python main.py
```

## Ses stilini degistirme

Varsayilan TTS modeli stil yonlendirmesi icin `gpt-4o-mini-tts` yapildi.

Istersen PowerShell'de calistirmadan once sesi/stili degistirebilirsin:

```powershell
$env:OPENAI_TTS_MODEL="gpt-4o-mini-tts"
$env:OPENAI_TTS_VOICE="echo"
$env:OPENAI_TTS_STYLE="Speak in Turkish like a warm, friendly and welcoming university representative. Professional yet approachable, polite and respectful."
py -3.11 main.py
```

Desteklenmeyen bir TTS modeli secilirse uygulama stil yonlendirmesini otomatik kaldirip normal TTS ile tekrar dener.

## Bu surumde duzeltilenler

- Hardcoded API anahtari kaldirildi.
- `requirements.txt` UTF-8 olarak duzeltildi.
- Gecersiz/deneysel chat model varsayilani yerine uyumlu model varsayilani kullanildi.
- TTS cikisi MP3 + pygame yerine WAV + sounddevice ile calacak sekilde daha guvenilir hale getirildi.
- TTS sesi Duzce MYO tanitim asistani icin uygun hale getirildi.
- Bilgi bankasi entegre edilerek halusinasyon engeli eklendi.
- TTS dosyasi bos olusursa acik hata mesaji eklendi.
- pygame baslamazsa uygulamanin kapanmamasi saglandi.


## Ses hedefi

Varsayilan ses `echo` olarak ayarlandi. Stil hedefi:

- sicak, misafirperver ve profesyonel ton
- acik ve dogal konusma hizi
- resmi ama samimi uslup
- kisa, akici ve anlasilir cevaplar

PowerShell ornegi:

```powershell
$env:OPENAI_TTS_VOICE="echo"
$env:OPENAI_TTS_SPEED="1.18"
py -3.11 main.py
```
