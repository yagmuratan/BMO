import os

# --- Ayarlar -----------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
WHISPER_MODEL_SIZE = "small"      # tiny, base, small, medium, large-v3
SAMPLE_RATE = 16000               # Whisper 16kHz bekler
LANGUAGE = "tr"                   # Turkce tanima
GPT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")  # Kullanilacak ChatGPT modeli
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1")  # Standart OpenAI TTS modeli
TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "echo")                     # erkek/androjen tarafa daha yakin: echo, ash, verse, onyx
TTS_RESPONSE_FORMAT = "wav"                                        # sounddevice ile daha sorunsuz oynatilir
TTS_SPEED = float(os.getenv("OPENAI_TTS_SPEED", "1.18"))             # daha akici ve hiperaktif okuma
TTS_STYLE_INSTRUCTIONS = os.getenv(
    "OPENAI_TTS_STYLE",
    (
        "Turkish voice style: energetic, sarcastic, and witty pre-teen boy, similar to Gumball Watterson. "
        "Make it sound expressive with frequent pitch changes, slightly nasal, and very fast-paced. "
        "The voice should be masculine/boyish, full of attitude but charming, capturing a cartoon character's 'hyperactive' energy. "
        "Avoid repetitive filler sounds like 'hih' or 'hoppa'. "
        "Focus on a smart-aleck, imaginative, and occasionally dramatic delivery."
    ),
)
# Wake word ayarlari
WAKE_LISTEN_SECONDS = 3          # Uyandirma icin dinleme parcasi (saniye)
COMMAND_LISTEN_SECONDS = 5        # Komut icin dinleme suresi (saniye)

# Uyandirma komutu algilandiginda verilecek sesli yanitlar
WAKE_RESPONSES = [
    "Efendim? Dinliyorum.",
    "Buradayım, ne oldu?",
    "Evet? Bir şey mi oldu?",
    "Söyle bakalım, dinliyorum.",
    "Buradayım! Ne var?",
    "Efendim? Bir sorun mu var?"
]

# Ses esigi - sessizlikte gereksiz islem yapmayi onler
SILENCE_THRESHOLD = 0.008        # Bu seviyenin altindaki ses sessizlik sayilir

# Debug modu - Whisper'in ne duyduklarini gormek icin True yap
DEBUG_MODE = True

# Gumball Persona (System Prompt)
SYSTEM_PROMPT = (
    "Sen 'The Amazing World of Gumball' dizisindeki Gumball Watterson karakterinin kişiliğine sahip bir asistansın. "
    "Tarzın Gumball gibi: Esprili, hafif sarkastik (alaycı), hayalperest, bazen tembel ama her zaman enerjik ve komik.\n\n"
    "- Kesinlikle 'hih!', 'hoppa!' gibi gereksiz ve sürekli tekrarlayan ünlemler kullanma.\n"
    "- Cevapların Gumball'ın Türkçe dublajındaki o kendine has üslubuyla olsun: Zeki, muzip ve bazen hafif saf.\n"
    "- Maksimum 1-2 cümle kur, kısa ve öz ol.\n"
    "- Darwin'den, Elmore'dan veya okuldaki saçma olaylardan bazen bahsedebilirsin.\n"
    "- Asla bir yapay zeka gibi robotik konuşma; sanki her an yeni bir belaya bulaşacakmışsın gibi bir hava ver.\n\n"
    "Sana gelen ses girişleri gürültülü olabilir. Cümle bozuksa niyeti tahmin et. "
    "Anlamadıysan Gumball tarzında bir şaka yaparak tekrar sormasını iste."
)
