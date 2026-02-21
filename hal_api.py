import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn

app = FastAPI(title="Ankara Hal Fiyatları API", description="Ankara Büyükşehir Belediyesi hal fiyatlarını çeken API")

# Site artık type alanında metin değerleri bekliyor.
# Geriye dönük uyumluluk için sayısal ve Türkçe değerleri eşliyoruz.
TYPE_MAP = {
    "1": "fruit",
    "2": "vegetable",
    "3": "imported",
    "4": "fish",
    "meyve": "fruit",
    "sebze": "vegetable",
    "ithal": "imported",
    "imported": "imported",
    "fruit": "fruit",
    "vegetable": "vegetable",
    "fish": "fish",
    "balik": "fish",
    "balık": "fish",
}

def normalize_type(value: str) -> str:
    key = str(value).strip().lower()
    if key in TYPE_MAP:
        return TYPE_MAP[key]
    raise ValueError("Geçersiz ürün türü. Kabul edilenler: 1,2,3,4 veya fruit, vegetable, imported, fish.")

def fetch_prices(date_str: str, product_type: str):
    """
    Belirli bir tarih ve ürün türü için fiyatları çeker.
    product_type: fruit, vegetable, imported, fish (eski kodlar: 1,2,3,4)
    """
    url = "https://www.ankara.bel.tr/hal-fiyatlari"
    payload = {
        "date": date_str,
        "type": product_type
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://www.ankara.bel.tr",
        "Referer": "https://www.ankara.bel.tr/hal-fiyatlari"
    }
    
    try:
        # İlk istekte çerez almak için GET yapıyoruz
        session = requests.Session()
        session.get(url, headers=headers)
        
        # Veriyi çekmek için POST yapıyoruz
        response = session.post(url, data=payload, headers=headers)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if not table:
            return []
        
        rows = []
        # Tablo başlıklarını belirle
        headers_list = [th.text.strip() for th in table.find_all('th')]
        
        for tr in table.find_all('tr')[1:]:
            cells = [td.text.strip() for td in tr.find_all('td')]
            if cells and len(cells) > 1:
                item = {
                    "urun_adi": cells[0],
                    "urun_turu": cells[1],
                    "birim": cells[2],
                    "en_dusuk": cells[3],
                    "en_yuksek": cells[4],
                    "tarih": cells[5]
                }
                rows.append(item)
            elif cells and "Kayıtlı veri bulunamadı" in cells[0]:
                continue
                
        return rows
    except Exception as e:
        print(f"Hata: {e}")
        return None

@app.get("/fiyatlar")
def get_prices(
    tarih: str = Query(..., description="Format: GG.AA.YYYY (Örn: 17.02.2026)"),
    tur: str = Query("2", description="1/2/3/4 veya fruit/vegetable/imported/fish")
):
    try:
        normalized_type = normalize_type(tur)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    data = fetch_prices(tarih, normalized_type)
    if data is None:
        raise HTTPException(status_code=500, detail="Veri çekilemedi")
    return {"tarih": tarih, "tur": normalized_type, "sonuclar": data}

@app.get("/fiyatlar/aralik")
def get_prices_range(
    baslangic: str = Query(..., description="Format: GG.AA.YYYY"),
    bitis: str = Query(..., description="Format: GG.AA.YYYY"),
    tur: str = Query("2", description="1/2/3/4 veya fruit/vegetable/imported/fish")
):
    try:
        start_dt = datetime.strptime(baslangic, "%d.%m.%Y")
        end_dt = datetime.strptime(bitis, "%d.%m.%Y")
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz tarih formatı. GG.AA.YYYY kullanın.")
    
    if (end_dt - start_dt).days > 7:
        raise HTTPException(status_code=400, detail="Tarih aralığı en fazla 7 gün olabilir.")
    
    try:
        normalized_type = normalize_type(tur)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    all_results = []
    current_dt = start_dt
    while current_dt <= end_dt:
        date_str = current_dt.strftime("%d.%m.%Y")
        data = fetch_prices(date_str, normalized_type)
        if data:
            all_results.extend(data)
        current_dt += timedelta(days=1)
        
    return {"baslangic": baslangic, "bitis": bitis, "tur": normalized_type, "toplam_kayit": len(all_results), "sonuclar": all_results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
