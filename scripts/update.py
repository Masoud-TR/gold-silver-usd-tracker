import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime


SELECTOR = 'span.price[data-col="info.last_trade.PDrCotVal"]'


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
    }
]


def fetch_price(url):
    """
    دریافت قیمت از یک صفحه TGJU
    """

    response = requests.get(url)

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    price_element = soup.select_one(SELECTOR)

    if price_element is None:
        raise Exception("Price not found")

    raw_price = price_element.text.strip()

    price = float(
        raw_price.replace(",", "")
    )

    return price



def fetch_latest():
    """
    دریافت آخرین قیمت همه موارد
    """

    prices = {}

    for page in PAGES:
        prices[page["key"]] = fetch_price(
            page["url"]
        )

    return prices



def already_saved_today(file_path):
    """
    بررسی اینکه امروز قبلاً داده ذخیره شده یا نه
    """

    if not os.path.exists(file_path):
        return False


    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        rows = list(csv.reader(f))


    if len(rows) <= 1:
        return False


    last_date = rows[-1][0]

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    return last_date == today



def save_history(prices):
    """
    ذخیره داده‌ها در CSV
    """

    os.makedirs(
        "data",
        exist_ok=True
    )


    file_path = "data/history.csv"


    if already_saved_today(file_path):

        print("Already saved today")

        return



    file_exists = os.path.exists(
        file_path
    )


    with open(
        file_path,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:


        writer = csv.writer(f)


        if not file_exists:

            writer.writerow(
                [
                    "date",
                    "timestamp",
                    "usd",
                    "gold18",
                    "coin",
                    "ounce"
                ]
            )


        now = datetime.now()


        writer.writerow(
            [
                now.strftime("%Y-%m-%d"),
                int(now.timestamp()),
                prices["usd"],
                prices["gold18"],
                prices["coin"],
                prices["ounce"]
            ]
        )


    print("History saved successfully")



def main():

    prices = fetch_latest()


    print(prices)


    save_history(prices)



if __name__ == "__main__":

    main()