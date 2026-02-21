# Ankara Hal Fiyatları API Dokümantasyonu

Bu API, Ankara Büyükşehir Belediyesi'nin resmi web sitesinden ([https://www.ankara.bel.tr/hal-fiyatlari](https://www.ankara.bel.tr/hal-fiyatlari)) hal fiyatlarını çekmek için geliştirilmiştir.

## API Uç Noktaları

### 1. Belirli Bir Tarih ve Ürün Türü İçin Fiyatları Getir

`GET /fiyatlar`

Belirli bir tarih ve ürün türü için hal fiyatlarını döndürür.

**Parametreler:**

| Parametre Adı | Tip    | Açıklama                                       | Zorunlu | Varsayılan | Örnek         |
|---------------|--------|------------------------------------------------|---------|------------|---------------|
| `tarih`       | `string` | Fiyatların çekileceği tarih (GG.AA.YYYY formatında) | Evet    | Yok        | `17.02.2026`  |
| `tur`         | `string` | Ürün türü                                     | Hayır   | `2` (Sebze) | `vegetable`   |

**Ürün Türleri:**
- `1` veya `fruit`: Meyve
- `2` veya `vegetable`: Sebze
- `3` veya `imported`: İthal
- `4` veya `fish`: Balık

**Örnek İstek:**

```
GET https://8000-ikwu17x04h95epn0qv4au-0d005bb7.sg1.manus.computer/fiyatlar?tarih=17.02.2026&tur=vegetable
```

**Örnek Yanıt:**

```json
{
  "tarih": "17.02.2026",
  "tur": "2",
  "sonuclar": [
    {
      "urun_adi": "BROKOLİ",
      "urun_turu": "Sebze",
      "birim": "KG",
      "en_dusuk": "30,00",
      "en_yuksek": "40,00",
      "tarih": "17.02.2026"
    },
    {
      "urun_adi": "HAVUÇ",
      "urun_turu": "Sebze",
      "birim": "KG",
      "en_dusuk": "10,00",
      "en_yuksek": "15,00",
      "tarih": "17.02.2026"
    }
  ]
}
```

### 2. Tarih Aralığı ve Ürün Türü İçin Fiyatları Getir

`GET /fiyatlar/aralik`

Belirli bir tarih aralığı ve ürün türü için hal fiyatlarını döndürür. Tarih aralığı en fazla 7 gün olabilir.

**Parametreler:**

| Parametre Adı | Tip    | Açıklama                                       | Zorunlu | Varsayılan | Örnek         |
|---------------|--------|------------------------------------------------|---------|------------|---------------|
| `baslangic`   | `string` | Tarih aralığının başlangıcı (GG.AA.YYYY formatında) | Evet    | Yok        | `10.02.2026`  |
| `bitis`       | `string` | Tarih aralığının bitişi (GG.AA.YYYY formatında)   | Evet    | Yok        | `17.02.2026`  |
| `tur`         | `string` | Ürün türü                                     | Hayır   | `2` (Sebze) | `fruit`       |

**Ürün Türleri:**
- `1` veya `fruit`: Meyve
- `2` veya `vegetable`: Sebze
- `3` veya `imported`: İthal
- `4` veya `fish`: Balık

**Örnek İstek:**

```
GET https://8000-ikwu17x04h95epn0qv4au-0d005bb7.sg1.manus.computer/fiyatlar/aralik?baslangic=10.02.2026&bitis=12.02.2026&tur=fruit
```

**Örnek Yanıt:**

```json
{
  "baslangic": "10.02.2026",
  "bitis": "12.02.2026",
  "tur": "1",
  "toplam_kayit": 4,
  "sonuclar": [
    {
      "urun_adi": "ELMA",
      "urun_turu": "Meyve",
      "birim": "KG",
      "en_dusuk": "10,00",
      "en_yuksek": "15,00",
      "tarih": "10.02.2026"
    },
    {
      "urun_adi": "ARMUT",
      "urun_turu": "Meyve",
      "birim": "KG",
      "en_dusuk": "12,00",
      "en_yuksek": "18,00",
      "tarih": "10.02.2026"
    },
    {
      "urun_adi": "ELMA",
      "urun_turu": "Meyve",
      "birim": "KG",
      "en_dusuk": "10,00",
      "en_yuksek": "15,00",
      "tarih": "11.02.2026"
    },
    {
      "urun_adi": "ARMUT",
      "urun_turu": "Meyve",
      "birim": "KG",
      "en_dusuk": "12,00",
      "en_yuksek": "18,00",
      "tarih": "11.02.2026"
    }
  ]
}
```

## API Erişimi

API'ye aşağıdaki adresten erişebilirsiniz:

[https://8000-ikwu17x04h95epn0qv4au-0d005bb7.sg1.manus.computer](https://8000-ikwu17x04h95epn0qv4au-0d005bb7.sg1.manus.computer)

Swagger UI dokümantasyonuna erişmek için `/docs` yolunu kullanabilirsiniz:

[https://8000-ikwu17x04h95epn0qv4au-0d005bb7.sg1.manus.computer/docs](https://8000-ikwu17x04h95epn0qv4au-0d005bb7.sg1.manus.computer/docs)

Redoc dokümantasyonuna erişmek için `/redoc` yolunu kullanabilirsiniz:

[https://8000-ikwu17x04h95epn0qv4au-0d005bb7.sg1.manus.computer/redoc](https://8000-ikwu17x04h95epn0qv4au-0d005bb7.sg1.manus.computer/redoc)
