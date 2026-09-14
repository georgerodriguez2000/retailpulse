import json
from pathlib import Path
from datetime import datetime

import requests


API_URL = "https://dummyjson.com/products?limit=0"
PRODUCTS_RAW_DIR = Path("data/raw/products")
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S" ## Year/month/date - hour/minutes/secs


def fetch_products():
    response = requests.get(API_URL, timeout=30)

    response.raise_for_status()

    data = response.json()

    return data

def save_raw_products(data):
    PRODUCTS_RAW_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

    raw_file = PRODUCTS_RAW_DIR / f"products_{timestamp}.json"

    with raw_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    return raw_file


if __name__ == "__main__":
    products_data = fetch_products()

    raw_file = save_raw_products(products_data) ## created to avoid confusion with the other
    ## raw file that was create above in the other function, lol

    print(f"Productos extraidos: {len(products_data['products'])}")
    print(f"RAW guardado en: {raw_file}")