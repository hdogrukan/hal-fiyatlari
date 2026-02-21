import requests
from bs4 import BeautifulSoup

def get_hal_prices(date, product_type):
    url = "https://www.ankara.bel.tr/hal-fiyatlari"
    payload = {
        "date": date,
        "type": product_type
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": "PHPSESSID=tbbulrt88lfguadodvl13ft9nk",
        "Origin": "https://www.ankara.bel.tr",
        "Referer": "https://www.ankara.bel.tr/hal-fiyatlari"
    }
    
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code != 200:
        return f"Error: {response.status_code}"
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Debug: Save HTML to check
    with open("response.html", "w") as f:
        f.write(response.text)
        
    table = soup.find('table')
    
    if not table:
        return "No table found"
    
    rows = []
    headers_list = [th.text.strip() for th in table.find_all('th')]
    for tr in table.find_all('tr')[1:]:
        cells = [td.text.strip() for td in tr.find_all('td')]
        if cells:
            rows.append(cells)
    
    return {
        "headers": headers_list,
        "data": rows
    }

if __name__ == "__main__":
    # Test with 18.02.2026
    test_date = "18.02.2026"
    test_type = "vegetable"  # Sebze (site artık string değer bekliyor)
    result = get_hal_prices(test_date, test_type)
    print(result)
