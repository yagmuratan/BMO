# GumBot

Sesli asistan: wake word, Faster Whisper, ChatGPT ve OpenAI TTS.

Bu surumde ses karakteri, belirli bir telifli cizgi film karakterini kopyalamadan, daha simarik, akici, cirtlak ve ergen erkek cocuk/velet cizgi film tarzi bir havaya yaklastirildi.

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
$env:OPENAI_TTS_STYLE="Speak in Turkish like an original energetic cartoon boy sidekick. Fast, cheerful, playful and expressive. Do not imitate any specific copyrighted character or real actor."
py -3.11 main.py
```

Desteklenmeyen bir TTS modeli secilirse uygulama stil yonlendirmesini otomatik kaldirip normal TTS ile tekrar dener.

## Bu surumde duzeltilenler

- Hardcoded API anahtari kaldirildi.
- `requirements.txt` UTF-8 olarak duzeltildi.
- Gecersiz/deneysel chat model varsayilani yerine uyumlu model varsayilani kullanildi.
- TTS cikisi MP3 + pygame yerine WAV + sounddevice ile calacak sekilde daha guvenilir hale getirildi.
- TTS sesi daha enerjik cizgi film tarzi icin yonlendirildi.
- Telifli karakteri birebir taklit etmeden ozgun GumBot kisiligi eklendi.
- TTS dosyasi bos olusursa acik hata mesaji eklendi.
- pygame baslamazsa uygulamanin kapanmamasi saglandi.


## Bu paketteki ses hedefi

Varsayilan ses `echo` olarak ayarlandi. Stil hedefi:

- ergen/kucuk erkek cocuk hissi
- cirtlak ama kadinsi olmayan ton
- simarik, velet, muzip ve hizli konusma
- kisa, akici ve enerjik cevaplar

Daha kalin gelirse `ash` veya `verse` deneyebilirsin. Daha tok gelirse `echo`da kalmak daha iyi olabilir.

PowerShell ornegi:

```powershell
$env:OPENAI_TTS_VOICE="echo"
$env:OPENAI_TTS_SPEED="1.18"
py -3.11 main.py
```
