import sys
from eyes import GamboadEyes
from main_voice import SesliAsistan

def main():
    """
    DÜ-ASİSTAN Ana Kontrol Programı.
    Göz simülasyonu ve sesli asistanı tek merkezden yönetir.
    Terminalden girilen komutlara göre göz animasyonları ve sesli asistanı kontrol eder.
    """
    # 1.44 inç OLED çözünürlüğü olan 128x128 ile başlatıyoruz.
    # İleride çözünürlük değişmek istenirse burası güncellenebilir.
    eyes = GamboadEyes(width=128, height=128)
    
    # Simülasyon penceresini arka planda başlat
    eyes.start()

    # Sesli asistan motoru (henüz başlatılmadı)
    asistan = SesliAsistan(eyes=eyes)
    
    # Menüyü yazdır
    print("\n" + "=" * 55)
    print("   DÜ-ASİSTAN - Ana Kontrol Paneli")
    print("=" * 55)
    print("   1 - Normal Göz (normal)")
    print("   2 - Mutlu Göz (happy)")
    print("   3 - Üzgün Göz (sad)")
    print("   4 - Sinirli Göz (angry)")
    print("   5 - Şaşkın Göz (surprised)")
    print("   6 - Uykulu Göz (sleepy)")
    print("   7 - Kalpli Göz (heart)")
    print("   8 - Instagram Önerisi (Test)")
    print("   9 - Sesli Asistanı Uyandır (Manuel)")
    print("   t - Sesli Asistanı Aç / Kapat")
    print("   q - Çıkış")
    print("=" * 55)
    print("   [NOT] 't' ile sesli asistanı başlatınca")
    print("   \"Hey, Merhaba, Selam, Asistan\" diyerek veya '9' tuşuyla asistanı uyandırabilirsiniz.")
    print("=" * 55 + "\n")
    
    try:
        while eyes.running:
            # Kullanıcıdan komut al
            secim = input("Komut girin (1-9, t, q): ").strip().lower()
            
            # Eğer pencere kullanıcı tarafından kapatıldıysa döngüden çık
            if not eyes.running:
                print("[INFO] Simülasyon penceresi kapatılmış. Çıkış yapılıyor...")
                break
                
            if secim == 'q':
                print("[INFO] Çıkış komutu alındı.")
                break
                
            elif secim == '1':
                eyes.set_emotion("normal")
                
            elif secim == '2':
                eyes.set_emotion("happy")
                
            elif secim == '3':
                eyes.set_emotion("sad")
                
            elif secim == '4':
                eyes.set_emotion("angry")
                
            elif secim == '5':
                eyes.set_emotion("surprised")
                
            elif secim == '6':
                eyes.set_emotion("sleepy")
                
            elif secim == '7':
                eyes.set_emotion("heart")
                
            elif secim == '8':
                eyes.set_emotion("instagram_logo", "@duzceuniversite")
                
            elif secim == 't':
                if not asistan.aktif:
                    # Sesli asistanı başlat ve göz konuşma modunu aç
                    asistan.start()
                    eyes.start_talking()
                    eyes.set_emotion("happy")
                else:
                    # Sesli asistanı durdur ve göz konuşma modunu kapat
                    asistan.stop()
                    eyes.stop_talking()
                    eyes.set_emotion("normal")

            elif secim == '9':
                # Manuel uyandırma: sesli asistan çalışıyorsa wake word duymuş gibi tetikle
                asistan.manual_wake()
                    
            else:
                print("[UYARI] Geçersiz komut! Lütfen 1-9, t veya q girin.")
                
    except KeyboardInterrupt:
        print("\n[INFO] Klavye kesmesi algılandı. Çıkılıyor...")
    finally:
        # Sesli asistanı durdur (çalışıyorsa)
        if asistan.aktif:
            asistan.stop()
        # Program sonlanırken pygame ve arka plan thread'ini temizce durdur
        eyes.stop()
        print("[INFO] DÜ-ASİSTAN sonlandırıldı.")
        sys.exit(0)

if __name__ == "__main__":
    main()
