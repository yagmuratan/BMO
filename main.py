import sys
from eyes import GamboadEyes

def main():
    """
    GumBot Göz Simülasyonu Test Programı.
    Terminalden girilen komutlara göre göz animasyonlarını kontrol eder.
    """
    # 1.44 inç OLED çözünürlüğü olan 128x128 ile başlatıyoruz.
    # İleride çözünürlük değişmek istenirse burası güncellenebilir.
    eyes = GamboadEyes(width=128, height=128)
    
    # Simülasyon penceresini arka planda başlat
    eyes.start()
    
    # Menüyü yazdır
    print("\n" + "=" * 55)
    print("   GumBot Göz Simülatörü - Test Arayüzü")
    print("=" * 55)
    print("   1 - Normal Göz (normal)")
    print("   2 - Mutlu Göz (happy)")
    print("   3 - Üzgün Göz (sad)")
    print("   4 - Sinirli Göz (angry)")
    print("   5 - Şaşkın Göz (surprised)")
    print("   6 - Uykulu Göz (sleepy)")
    print("   7 - Kalpli Göz (heart)")
    print("   t - Konuşma Modunu Aç / Kapat")
    print("   q - Çıkış")
    print("=" * 55 + "\n")
    
    talking_state = False
    
    try:
        while eyes.running:
            # Kullanıcıdan komut al
            secim = input("Komut girin (1-7, t, q): ").strip().lower()
            
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
                
            elif secim == 't':
                talking_state = not talking_state
                if talking_state:
                    eyes.start_talking()
                else:
                    eyes.stop_talking()
                    
            else:
                print("[UYARI] Geçersiz komut! Lütfen 1-7, t veya q girin.")
                
    except KeyboardInterrupt:
        print("\n[INFO] Klavye kesmesi algılandı. Çıkılıyor...")
    finally:
        # Program sonlanırken pygame ve arka plan thread'ini temizce durdur
        eyes.stop()
        print("[INFO] GumBot göz simülasyonu sonlandırıldı.")
        sys.exit(0)

if __name__ == "__main__":
    main()
