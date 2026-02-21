import argparse
import datetime as dt
import random
import sqlite3
import time
from typing import Dict, Iterable, List, Tuple

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.ankara.bel.tr/hal-fiyatlari"

TYPE_MAP = {
    "1": "fruit",
    "2": "vegetable",
    "3": "imported",
    "4": "fish",
    "meyve": "fruit",
    "sebze": "vegetable",
    "ithal": "imported",
    "balik": "fish",
    "balık": "fish",
    "fruit": "fruit",
    "vegetable": "vegetable",
    "imported": "imported",
    "fish": "fish",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.ankara.bel.tr",
    "Referer": "https://www.ankara.bel.tr/hal-fiyatlari",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def normalize_type(value: str) -> str:
    key = str(value).strip().lower()
    if key in TYPE_MAP:
        return TYPE_MAP[key]
    raise ValueError(
        "Gecersiz urun turu. Kabul edilenler: 1,2,3,4 veya fruit, vegetable, imported, fish."
    )


def parse_price(value: str):
    text = value.strip()
    if not text:
        return None
    # Turkish numeric format: 1.234,56
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def is_cloudflare_block(html: str) -> bool:
    if not html:
        return False
    lowered = html.lower()
    return (
        "attention required" in lowered
        or "cf-error-details" in lowered
        or "cloudflare" in lowered
    )


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_prices(session: requests.Session, date_str: str, type_slug: str, timeout: int) -> List[Dict]:
    # First GET for cookies
    resp = session.get(BASE_URL, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"GET failed: {resp.status_code}")
    if is_cloudflare_block(resp.text):
        raise RuntimeError("Cloudflare block on GET")

    payload = {"date": date_str, "type": type_slug}
    resp = session.post(BASE_URL, data=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"POST failed: {resp.status_code}")
    if is_cloudflare_block(resp.text):
        raise RuntimeError("Cloudflare block on POST")

    if "Kayitli veri bulunamadi" in resp.text or "Kayıtlı veri bulunamadı" in resp.text:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    if not table:
        # Some days may not show data; treat as empty rather than crash.
        return []

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) < 6:
            continue
        rows.append(
            {
                "product_name": cells[0],
                "product_type": cells[1],
                "unit": cells[2],
                "min_price": parse_price(cells[3]),
                "max_price": parse_price(cells[4]),
                "source_date_text": cells[5],
            }
        )
    return rows


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type_code TEXT NOT NULL,
            type_slug TEXT NOT NULL,
            product_name TEXT NOT NULL,
            product_type TEXT,
            unit TEXT,
            min_price REAL,
            max_price REAL,
            source_date_text TEXT,
            fetched_at TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique
        ON prices(date, type_slug, product_name, unit, min_price, max_price);

        CREATE TABLE IF NOT EXISTS fetch_log (
            date TEXT NOT NULL,
            type_slug TEXT NOT NULL,
            status TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            error_message TEXT,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (date, type_slug)
        );
        """
    )
    conn.commit()


def log_fetch(
    conn: sqlite3.Connection,
    date_iso: str,
    type_slug: str,
    status: str,
    row_count: int,
    error_message: str = None,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO fetch_log
        (date, type_slug, status, row_count, error_message, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            date_iso,
            type_slug,
            status,
            row_count,
            error_message,
            dt.datetime.utcnow().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()


def already_fetched(conn: sqlite3.Connection, date_iso: str, type_slug: str) -> bool:
    cur = conn.execute(
        "SELECT status FROM fetch_log WHERE date = ? AND type_slug = ?",
        (date_iso, type_slug),
    )
    row = cur.fetchone()
    return row is not None and row[0] in ("ok", "empty")


def daterange(start: dt.date, end: dt.date) -> Iterable[dt.date]:
    current = start
    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def insert_prices(
    conn: sqlite3.Connection,
    date_iso: str,
    type_code: str,
    type_slug: str,
    rows: List[Dict],
) -> int:
    if not rows:
        return 0
    now = dt.datetime.utcnow().isoformat(timespec="seconds")
    payload: List[Tuple] = []
    for r in rows:
        payload.append(
            (
                date_iso,
                type_code,
                type_slug,
                r["product_name"],
                r.get("product_type"),
                r.get("unit"),
                r.get("min_price"),
                r.get("max_price"),
                r.get("source_date_text"),
                now,
            )
        )
    conn.executemany(
        """
        INSERT OR IGNORE INTO prices
        (date, type_code, type_slug, product_name, product_type, unit, min_price, max_price, source_date_text, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )
    conn.commit()
    return len(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="2024'ten bugune kadar Ankara hal fiyatlarini SQLite DB'ye yaz."
    )
    parser.add_argument("--db", default="hal_prices.sqlite", help="SQLite dosya yolu")
    parser.add_argument("--start", default="2024-01-01", help="Baslangic tarihi (YYYY-MM-DD)")
    parser.add_argument("--end", default=dt.date.today().isoformat(), help="Bitis tarihi (YYYY-MM-DD)")
    parser.add_argument("--types", default="1,2,3,4", help="Urun turleri: 1,2,3,4 veya fruit,vegetable,imported,fish")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout (sn)")
    parser.add_argument("--sleep", type=float, default=1.0, help="Istekler arasi bekleme (sn)")
    parser.add_argument("--jitter", type=float, default=0.5, help="Bekleme jitter (sn)")
    parser.add_argument("--retries", type=int, default=3, help="Basarisiz isteklerde tekrar sayisi")
    parser.add_argument("--skip-existing", action="store_true", help="Basarili gunleri atla")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start_date = dt.datetime.strptime(args.start, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end, "%Y-%m-%d").date()
    if end_date < start_date:
        raise SystemExit("Bitis tarihi baslangic tarihinden once olamaz.")

    type_inputs = [t.strip() for t in args.types.split(",") if t.strip()]
    type_pairs: List[Tuple[str, str]] = []
    for t in type_inputs:
        type_pairs.append((t, normalize_type(t)))

    conn = sqlite3.connect(args.db)
    init_db(conn)

    session = build_session()

    total_rows = 0
    for d in daterange(start_date, end_date):
        date_str = d.strftime("%d.%m.%Y")
        date_iso = d.isoformat()

        for type_code, type_slug in type_pairs:
            if args.skip_existing and already_fetched(conn, date_iso, type_slug):
                continue

            last_error = None
            for attempt in range(1, args.retries + 1):
                try:
                    rows = fetch_prices(session, date_str, type_slug, args.timeout)
                    inserted = insert_prices(conn, date_iso, type_code, type_slug, rows)
                    total_rows += inserted
                    status = "ok" if rows else "empty"
                    log_fetch(conn, date_iso, type_slug, status, len(rows))
                    last_error = None
                    break
                except Exception as exc:
                    last_error = str(exc)
                    if attempt < args.retries:
                        time.sleep(min(10, args.sleep) + attempt)

            if last_error is not None:
                log_fetch(conn, date_iso, type_slug, "error", 0, last_error)

            time.sleep(max(0.0, args.sleep + random.uniform(0, args.jitter)))

    print(f"Tamamlandi. Eklenen satir sayisi: {total_rows}")


if __name__ == "__main__":
    main()
