import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# CONFIGURATION
# ============================================================

SELECTOR = 'span.price[data-col="info.last_trade.PDrCotVal"]'

TEHRAN = ZoneInfo("Asia/Tehran")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "*/*;q=0.8"
    ),
    "Accept-Language": (
        "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7"
    ),
    "Referer": "https://www.tgju.org/",
}


# ============================================================
# TGJU PAGES
# ============================================================

PAGES = [
    {
        "key": "usd",
        "url": "https://www.tgju.org/profile/price_dollar_rl"
    },
    {
        "key": "gold18",
        "url": "https://www.tgju.org/profile/geram18"
    },
    {
        "key": "coin",
        "url": "https://www.tgju.org/profile/sekee"
    },
    {
        "key": "ounce",
        "url": "https://www.tgju.org/profile/ons"
    },
    {
        "key": "silver_ounce",
        "url": "https://www.tgju.org/profile/silver"
    },
    {
        "key": "silver_price",
        "url": "https://www.tgju.org/profile/silver_999"
    }
]


# ============================================================
# FETCH PRICE
# ============================================================

def fetch_price(url):
    """
    دریافت قیمت از یک صفحه TGJU
    """

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15
    )

    if response.status_code != 200:
        raise Exception(
            f"Request failed for {url} -> "
            f"status {response.status_code}"
        )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    price_element = soup.select_one(
        SELECTOR
    )

    if price_element is None:
        raise Exception(
            f"Price not found for {url} "
            f"(selector may have changed)"
        )

    raw_price = price_element.text.strip()

    price = float(
        raw_price.replace(",", "")
    )

    return price


# ============================================================
# FETCH ALL PRICES
# ============================================================

def fetch_latest():
    """
    دریافت آخرین قیمت همه موارد
    """

    prices = {}

    for page in PAGES:

        print(
            f"Fetching {page['key']}..."
        )

        prices[page["key"]] = fetch_price(
            page["url"]
        )

    return prices


# ============================================================
# CHECK TODAY'S DATA
# ============================================================

def already_saved_today(file_path):
    """
    بررسی اینکه امروز به وقت تهران
    قبلاً داده ذخیره شده یا نه
    """

    if not os.path.exists(file_path):
        return False

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        rows = list(
            csv.reader(f)
        )

    if len(rows) <= 1:
        return False

    last_date = rows[-1][0]

    today = datetime.now(
        TEHRAN
    ).strftime(
        "%Y-%m-%d"
    )

    return last_date == today


# ============================================================
# SAVE HISTORY
# ============================================================

def save_history(prices):
    """
    ذخیره داده‌ها در CSV
    """

    os.makedirs(
        "data",
        exist_ok=True
    )

    file_path = "data/history.csv"

    # --------------------------------------------------------
    # Prevent duplicate data on the same Tehran date
    # --------------------------------------------------------

    if already_saved_today(file_path):

        print(
            "Already saved today."
        )

        return

    file_exists = os.path.exists(
        file_path
    )

    # --------------------------------------------------------
    # Current Tehran time
    # --------------------------------------------------------

    now = datetime.now(
        TEHRAN
    )

    # --------------------------------------------------------
    # Write data
    # --------------------------------------------------------

    with open(
        file_path,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        if not file_exists:

            writer.writerow(
                [
                    "date",
                    "timestamp",
                    "usd",
                    "gold18",
                    "coin",
                    "ounce",
                    "silver_ounce",
                    "silver_price"
                ]
            )

        # ----------------------------------------------------
        # Data row
        # ----------------------------------------------------

        writer.writerow(
            [
                now.strftime("%Y-%m-%d"),
                now.strftime("%Y-%m-%d %H:%M:%S"),
                prices["usd"],
                prices["gold18"],
                prices["coin"],
                prices["ounce"],
                prices["silver_ounce"],
                prices["silver_price"]
            ]
        )

    print(
        "History saved successfully."
    )

    print(
        f"Tehran time: "
        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    prices = fetch_latest()

    print(
        "\nLatest prices:"
    )

    for key, value in prices.items():

        print(
            f"{key}: {value}"
        )

    save_history(
        prices
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
