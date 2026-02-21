# Ankara Hal Fiyatları API

Bu proje, Ankara Büyükşehir Belediyesi web sitesinden ([https://www.ankara.bel.tr/hal-fiyatlari](https://www.ankara.bel.tr/hal-fiyatlari)) günlük hal fiyatlarını çekmek için geliştirilmiş bir FastAPI uygulamasıdır.

## Özellikler

- Belirli bir tarih ve ürün türü için hal fiyatlarını getirme.
- Belirli bir tarih aralığı ve ürün türü için hal fiyatlarını getirme (maksimum 7 günlük aralık).

## Kurulum

API'yi yerel ortamınızda çalıştırmak için aşağıdaki adımları izleyin:

1.  **Projeyi Klonlayın (veya Dosyaları İndirin):**

    ```bash
    git clone <proje_deposu_adresi> # Eğer bir git deposu varsa
    # veya hal_api.py, requirements.txt ve README.md dosyalarını indirin.
    ```

2.  **Gerekli Kütüphaneleri Yükleyin:**

    Proje dizinine gidin ve aşağıdaki komutu çalıştırın:

    ```bash
    pip install -r requirements.txt
    ```

    Bu komut, FastAPI, Uvicorn, requests ve BeautifulSoup gibi gerekli Python kütüphanelerini yükleyecektir.

3.  **API'yi Başlatın:**

    Aşağıdaki komutu kullanarak API sunucusunu başlatın:

    ```bash
    uvicorn hal_api:app --host 0.0.0.0 --port 8000
    ```

    API, `http://0.0.0.0:8000` adresinde çalışmaya başlayacaktır.

## Kullanım

API çalışmaya başladıktan sonra, web tarayıcınızdan veya bir API istemcisinden (örneğin Postman, Insomnia) aşağıdaki uç noktalara istek gönderebilirsiniz.

### API Dokümantasyonu

API'nin etkileşimli dokümantasyonuna (Swagger UI) aşağıdaki adresten erişebilirsiniz:

`http://localhost:8000/docs`

Redoc dokümantasyonuna ise aşağıdaki adresten erişebilirsiniz:

`http://localhost:8000/redoc`

### Uç Noktalar

#### 1. Belirli Bir Tarih ve Ürün Türü İçin Fiyatları Getir

-   **Endpoint:** `/fiyatlar`
-   **Metod:** `GET`
-   **Parametreler:**
    -   `tarih`: (Zorunlu) Fiyatların çekileceği tarih. Format: `GG.AA.YYYY` (Örn: `17.02.2026`)
    -   `tur`: (Opsiyonel) Ürün türü. Varsayılan: `2` (Sebze).
        -   `1` veya `fruit`: Meyve
        -   `2` veya `vegetable`: Sebze
        -   `3` veya `imported`: İthal
        -   `4` veya `fish`: Balık

-   **Örnek İstek:**

    ```
    http://localhost:8000/fiyatlar?tarih=17.02.2026&tur=vegetable
    ```

#### 2. Tarih Aralığı ve Ürün Türü İçin Fiyatları Getir

-   **Endpoint:** `/fiyatlar/aralik`
-   **Metod:** `GET`
-   **Parametreler:**
    -   `baslangic`: (Zorunlu) Tarih aralığının başlangıcı. Format: `GG.AA.YYYY` (Örn: `10.02.2026`)
    -   `bitis`: (Zorunlu) Tarih aralığının bitişi. Format: `GG.AA.YYYY` (Örn: `12.02.2026`)
    -   `tur`: (Opsiyonel) Ürün türü. Varsayılan: `2` (Sebze).
        -   `1` veya `fruit`: Meyve
        -   `2` veya `vegetable`: Sebze
        -   `3` veya `imported`: İthal
        -   `4` veya `fish`: Balık

-   **Önemli Not:** Tarih aralığı en fazla 7 gün olabilir.

-   **Örnek İstek:**

    ```
    http://localhost:8000/fiyatlar/aralik?baslangic=10.02.2026&bitis=12.02.2026&tur=fruit
    ```

## Geliştirici Notları

-   API, Ankara Büyükşehir Belediyesi web sitesinden veri çekmektedir. Web sitesinin yapısında meydana gelebilecek değişiklikler API'nin çalışmasını etkileyebilir.
-   Veri çekme işlemi sırasında `PHPSESSID` çerezi kullanılmaktadır. Bu çerez, `requests.Session()` kullanılarak otomatik olarak yönetilmektedir.

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakınız. (Şu an için bir `LICENSE` dosyası bulunmamaktadır, ancak eklenebilir.)
