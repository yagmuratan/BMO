import re
from config import GPT_MODEL

def noktalama_temizle(metin):
    """Metindeki noktalama isaretlerini kaldir (wake word eslesmesi icin)."""
    return re.sub(r'[.,!?;:\-_\'"()\[\]{}]', '', metin)

def wake_word_kontrol(metin):
    """Metinde uyandirma komutu var mi kontrol et."""
    metin_kucuk = noktalama_temizle(metin.lower().strip())
    # "hey asistan", "asistan", "hey", "merhaba", "selam" gibi komutlari algilar
    pattern = r'\b(?:hey\s+asistan|hey|merhaba|selam|asistan)\b'
    return bool(re.search(pattern, metin_kucuk))

def wake_word_sonrasi_metni_al(metin):
    """Uyandirma komutundan sonraki metni cikar (varsa)."""
    metin_kucuk = noktalama_temizle(metin.lower())
    pattern = r'\b(?:hey\s+asistan|hey|merhaba|selam|asistan)\b'
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
            max_tokens=500,
            temperature=0.7,
        )
        yanit = (response.choices[0].message.content or "").strip()
        if not yanit:
            print("[HATA] ChatGPT bos yanit dondu.")
            return None
        print("[YANIT] ChatGPT: {}".format(yanit))
        return yanit
    except Exception as e:
        print("[HATA] ChatGPT hatasi: {}".format(e))
        return None
