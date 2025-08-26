Bu program videolardan ses dosyalarını alıp yazı formatına çevirir sonra da özetini çıkarır

MAC de kullanmak için:
1. Automator’u Aç

Spotlight (⌘ + Space) → Automator yaz → aç.

“Yeni Belge” seç → Application (Uygulama) seç.

2. Çalıştırılacak Script’i Ekle

Sol üstte arama kısmına “Run Shell Script” yaz.

Run Shell Script öğesini sürükleyip sağdaki boş alana bırak.

3. Script İçeriğini Yaz

Oraya şunu yapıştır (senin dosyan speechrecog.py ile aynı klasördeyse):

cd "$(dirname "$0")"
python3 speechrecog.py

4. Uygulama Olarak Kaydet

Dosya → Kaydet → örneğin SpeechRecog.app ismini ver.

Masaüstüne ya da Uygulamalar klasörüne kaydedebilirsin.

5. Çift Tıkla Çalıştır 🎉

Artık .app dosyasına çift tıklayınca terminal açılmadan direkt çalışır.