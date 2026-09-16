import csv
import io
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


SELECTOR = 'span.price[data-col="info.last_trade.PDrCotVal"]'
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HISTORY_FILE = PROJECT_ROOT / "data" / "history.csv"
TEHRAN = ZoneInfo("Asia/Tehran")
HISTORY_HEADERS = [
    "date", "timestamp", "usd", "gold18", "coin", "ounce", "silver_ounce", "silver_price"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.tgju.org/",
}

PAGES = [
    {"key": "usd", "url": "https://www.tgju.org/profile/price_dollar_rl"},
    {"key": "gold18", "url": "https://www.tgju.org/profile/geram18"},
    {"key": "coin", "url": "https://www.tgju.org/profile/sekee"},
    {"key": "ounce", "url": "https://www.tgju.org/profile/ons"},
    {"key": "silver_ounce", "url": "https://www.tgju.org/profile/silver"},
    {"key": "silver_price", "url": "https://www.tgju.org/profile/silver_999"},
]


def fetch_price(url):
    """Fetch one price from a TGJU profile page."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    price_element = soup.select_one(SELECTOR)
    if price_element is None:
        raise ValueError(f"Price not found for {url}; the selector may have changed")

    raw_price = price_element.get_text(strip=True)
    try:
        return float(raw_price.replace(",", ""))
    except ValueError as error:
        raise ValueError(f"Invalid price {raw_price!r} for {url}") from error


def fetch_latest():
    """Fetch the current price for every configured market."""
    return {page["key"]: fetch_price(page["url"]) for page in PAGES}


def ensure_history_schema(file_path):
    """Upgrade legacy CSV files to UTF-8 and the current header schema."""
    if not file_path.exists():
        return

    raw_data = file_path.read_bytes()
    for encoding in ("utf-8", "cp1256"):
        try:
            contents = raw_data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Unable to decode history file: {file_path}")

    reader = csv.DictReader(io.StringIO(contents))
    if reader.fieldnames == HISTORY_HEADERS and encoding == "utf-8":
        return
    rows = list(reader)

    temporary_file = file_path.with_suffix(".tmp")
    with temporary_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HISTORY_HEADERS)
        writer.writeheader()
        writer.writerows(
            {header: row.get(header, "") for header in HISTORY_HEADERS}
            for row in rows
        )
    temporary_file.replace(file_path)


def already_saved_today(file_path, today):
    """Return whether a row for today already exists anywhere in the CSV."""
    if not file_path.exists():
        return False

    with file_path.open("r", newline="", encoding="utf-8") as file:
        return any(row.get("date") == today for row in csv.DictReader(file))


def save_history(prices):
    """Save one daily market-data snapshot to the project CSV."""
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    ensure_history_schema(HISTORY_FILE)

    now = datetime.now(TEHRAN)
    today = now.strftime("%Y-%m-%d")
    if already_saved_today(HISTORY_FILE, today):
        print("Already saved today")
        return

    file_exists = HISTORY_FILE.exists()
    with HISTORY_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HISTORY_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {"date": today, "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"), **prices}
        )

    print("History saved successfully")


def main():
    prices = fetch_latest()
    print(prices)
    save_history(prices)


if __name__ == "__main__":
    main()
