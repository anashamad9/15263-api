#!/usr/bin/env python3
"""
Fetches the 15263 offers Google Sheet and writes columns B-F to
docs/api/offers.json for static hosting.
"""

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from io import StringIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SHEET_ID = "1jK66XcKOLgQWAhToEhPSpHewOWn1EKIzlVw0hn_a8sY"
GID = "0"
AFFILIATE_ID = "15263"
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "docs", "api", "offers.json"
)

COLUMNS = {
    "offer_name": 1,
    "code": 2,
    "affiliate_id": 3,
    "discount": 4,
    "geo": 5,
}


def fetch_csv() -> list[list[str]]:
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/gviz/tq?tqx=out:csv&gid={GID}&_={time.time_ns()}"
    )
    req = Request(
        url,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        },
    )

    try:
        with urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8-sig")
    except HTTPError as exc:
        if exc.code in (401, 403):
            print(
                "ERROR fetching sheet: Google returned authorization error. "
                "Share the sheet with anyone who has the link as Viewer, "
                "or publish it to the web.",
                file=sys.stderr,
            )
        else:
            print(f"ERROR fetching sheet: HTTP {exc.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as exc:
        print(f"ERROR fetching sheet: {exc}", file=sys.stderr)
        sys.exit(1)

    return list(csv.reader(StringIO(content)))


def cell(row: list[str], key: str) -> str:
    idx = COLUMNS[key]
    return row[idx].strip() if len(row) > idx else ""


def append_text(existing: str, extra: str) -> str:
    if not extra:
        return existing
    if not existing:
        return extra
    if extra in existing:
        return existing
    return f"{existing}\n{extra}"


def parse_rows(rows: list[list[str]]) -> list[dict]:
    data = [row for row in rows[1:] if any(value.strip() for value in row)]
    offers: list[dict] = []
    current: dict | None = None

    for row in data:
        offer_name = cell(row, "offer_name")
        code = cell(row, "code")
        affiliate_id = cell(row, "affiliate_id")
        discount = cell(row, "discount")
        geo = cell(row, "geo")

        if offer_name:
            current = {
                "offer_name": offer_name,
                "code": code,
                "affiliate_id": affiliate_id or AFFILIATE_ID,
                "discount": discount,
                "geo": geo,
            }
            offers.append(current)
            continue

        # Handles sheet rows that visually continue the previous offer.
        if current:
            current["code"] = current["code"] or code
            current["affiliate_id"] = current["affiliate_id"] or affiliate_id or AFFILIATE_ID
            current["discount"] = append_text(current["discount"], discount)
            current["geo"] = append_text(current["geo"], geo)

    return offers


def main():
    print(f"Fetching sheet {SHEET_ID} (gid={GID})")
    rows = fetch_csv()
    print(f"  {len(rows)} rows fetched (including header)")

    offers = parse_rows(rows)
    print(f"  {len(offers)} offers parsed")

    output = {
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "15263 Offers",
        "sheet_id": SHEET_ID,
        "gid": GID,
        "columns": {
            "B": "offer_name",
            "C": "code",
            "D": "affiliate_id",
            "E": "discount",
            "F": "geo",
        },
        "total": len(offers),
        "offers": offers,
    }

    out_path = os.path.normpath(OUTPUT_PATH)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  Written to {out_path}")


if __name__ == "__main__":
    main()
