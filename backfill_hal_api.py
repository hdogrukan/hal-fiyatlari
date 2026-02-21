#!/usr/bin/env python3
"""Fill missing daily rows in hal_fiyatlari.db using local hal_api module."""

from __future__ import annotations

import argparse
import sqlite3
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import hal_api

TYPE_TO_CATEGORY = {
    "fruit": 1,
    "vegetable": 1,
    "imported": 1,
    "fish": 2,
}


def parse_tr_price(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def ensure_categories(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO categories (id, name) VALUES (?, ?)",
        (1, "MEYVE / SEBZE"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO categories (id, name) VALUES (?, ?)",
        (2, "BALIK"),
    )
    conn.commit()


def load_product_cache(conn: sqlite3.Connection) -> Dict[Tuple[int, str, str], int]:
    cur = conn.execute("SELECT id, category_id, name, unit FROM products")
    return {(row[1], row[2], row[3]): row[0] for row in cur.fetchall()}


def get_or_create_product_id(
    conn: sqlite3.Connection,
    cache: Dict[Tuple[int, str, str], int],
    category_id: int,
    name: str,
    unit: str,
) -> tuple[int, bool]:
    key = (category_id, name, unit)
    if key in cache:
        return cache[key], False

    cur = conn.execute(
        "INSERT INTO products (category_id, name, unit) VALUES (?, ?, ?)",
        (category_id, name, unit),
    )
    product_id = int(cur.lastrowid)
    cache[key] = product_id
    return product_id, True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fill missing hal price days up to today using hal_api."
    )
    parser.add_argument(
        "--db",
        default=str(Path(__file__).resolve().parent / "hal_fiyatlari.db"),
        help="SQLite DB path",
    )
    parser.add_argument(
        "--start",
        default=None,
        help="Start date (YYYY-MM-DD). Default: max(date)+1 in DB.",
    )
    parser.add_argument(
        "--end",
        default=date.today().isoformat(),
        help="End date (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument(
        "--types",
        default="fruit,vegetable,imported,fish",
        help="Comma separated types (fruit,vegetable,imported,fish).",
    )
    parser.add_argument("--retries", type=int, default=3, help="Retry count per fetch.")
    parser.add_argument(
        "--retry-sleep", type=float, default=1.0, help="Base retry sleep seconds."
    )
    parser.add_argument(
        "--sleep", type=float, default=0.35, help="Sleep between days (seconds)."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db).resolve()
    conn = sqlite3.connect(db_path)

    ensure_categories(conn)
    product_cache = load_product_cache(conn)

    cur = conn.execute("SELECT MAX(date) FROM prices")
    max_date_str = cur.fetchone()[0]

    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
    elif max_date_str:
        start_date = date.fromisoformat(max_date_str) + timedelta(days=1)
    else:
        start_date = date.today()

    end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
    if end_date < start_date:
        print(
            f"[INFO] Islem yok. start={start_date.isoformat()} end={end_date.isoformat()}"
        )
        conn.close()
        return 0

    type_slugs: List[str] = []
    for raw in (x.strip() for x in args.types.split(",")):
        if not raw:
            continue
        normalized = hal_api.normalize_type(raw)
        if normalized not in TYPE_TO_CATEGORY:
            raise ValueError(f"Unsupported type for this DB schema: {normalized}")
        type_slugs.append(normalized)

    # Deduplicate but keep input order.
    seen = set()
    unique_types = []
    for type_slug in type_slugs:
        if type_slug not in seen:
            seen.add(type_slug)
            unique_types.append(type_slug)

    print(f"[INFO] DB={db_path}")
    print(
        f"[INFO] max_date={max_date_str} start={start_date.isoformat()} end={end_date.isoformat()} types={','.join(unique_types)}"
    )

    inserted_ops = 0
    new_products = 0
    fetched_days = 0
    empty_days = 0
    error_days = 0

    for day in daterange(start_date, end_date):
        day_iso = day.isoformat()
        day_str = day.strftime("%d.%m.%Y")
        day_rows = 0
        day_has_error = False

        for type_slug in unique_types:
            category_id = TYPE_TO_CATEGORY[type_slug]

            rows = None
            last_error = None
            for attempt in range(1, args.retries + 1):
                try:
                    rows = hal_api.fetch_prices(day_str, type_slug)
                    if rows is None:
                        raise RuntimeError("hal_api returned None")
                    break
                except Exception as exc:  # pragma: no cover - network/runtime path
                    last_error = exc
                    time.sleep(max(0.0, args.retry_sleep * attempt))

            if rows is None:
                day_has_error = True
                print(f"[WARN] {day_iso} [{type_slug}] fetch failed: {last_error}")
                continue

            for row in rows:
                product_name = (row.get("urun_adi") or "").strip()
                unit = (row.get("birim") or "").strip()
                if not product_name or not unit:
                    continue

                product_id, created = get_or_create_product_id(
                    conn,
                    product_cache,
                    category_id,
                    product_name,
                    unit,
                )
                if created:
                    new_products += 1

                conn.execute(
                    """
                    INSERT OR REPLACE INTO prices (product_id, min_price, max_price, date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        parse_tr_price(row.get("en_dusuk")),
                        parse_tr_price(row.get("en_yuksek")),
                        day_iso,
                    ),
                )
                inserted_ops += 1
                day_rows += 1

        conn.commit()

        if day_rows > 0:
            fetched_days += 1
            print(f"[OK] {day_iso} rows={day_rows}")
        elif day_has_error:
            error_days += 1
            print(f"[WARN] {day_iso} no rows due to fetch error")
        else:
            empty_days += 1
            print(f"[INFO] {day_iso} empty")

        time.sleep(max(0.0, args.sleep))

    max_after, distinct_days, total_rows = conn.execute(
        "SELECT MAX(date), COUNT(DISTINCT date), COUNT(*) FROM prices"
    ).fetchone()
    conn.close()

    print("[SUMMARY]")
    print(
        f"insert_ops={inserted_ops} new_products={new_products} fetched_days={fetched_days} empty_days={empty_days} error_days={error_days}"
    )
    print(
        f"max_date={max_after} distinct_days={distinct_days} total_rows={total_rows}"
    )

    return 0 if error_days == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
