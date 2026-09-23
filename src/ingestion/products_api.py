## ESTO TRAE LOS DATOS DE LA API


import json
from pathlib import Path
from datetime import datetime

import requests
from src.validation.products_validator import (validate_products_payload, validate_products_batch)
from src.loading.postgres import insert_products_batch
from src.monitoring.pipeline_runs import (start_pipeline_run, finish_pipeline_run )

API_URL = "https://dummyjson.com/products?limit=0"
PRODUCTS_RAW_DIR = Path("data/raw/products")
PRODUCTS_CLEAN_DIR = Path("data/clean/products")
PRODUCTS_REJECTED_DIR = Path("data/rejected/products")
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

def save_clean_products(valid_products):
    PRODUCTS_CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

    clean_file = PRODUCTS_CLEAN_DIR / f"products_clean_{timestamp}.json"

    with clean_file.open("w", encoding="utf-8") as file:
        json.dump(valid_products, file, ensure_ascii=False, indent=4)

    return clean_file

def save_rejected_products(rejected_products):
    PRODUCTS_REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

    rejected_file = (
        PRODUCTS_REJECTED_DIR / f"products_rejected_{timestamp}.json"
    )

    with rejected_file.open("w", encoding="utf-8") as file:
        json.dump(rejected_products, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_id = start_pipeline_run("products_ingestion")

    raw_file = None
    clean_file = None
    rejected_file = None

    rows_extracted = 0
    rows_valid = 0
    rows_rejected = 0
    rows_loaded = 0

    try:
        products_data = fetch_products()

        rows_extracted = len(products_data["products"])

        raw_file = save_raw_products(products_data)

        payload_is_valid = validate_products_payload(products_data)

        if payload_is_valid:
            print("Payload Validation: OK")

        valid_products, rejected_products = validate_products_batch(
            products_data["products"]
        )

        rows_valid = len(valid_products)
        rows_rejected = len(rejected_products)

        clean_file = save_clean_products(valid_products)

        if rejected_products:
            rejected_file = save_rejected_products(rejected_products)

        insert_products_batch(valid_products)

        rows_loaded = len(valid_products)

        finish_pipeline_run(
            run_id=run_id,
            status="SUCCESS",
            rows_extracted=rows_extracted,
            rows_valid=rows_valid,
            rows_rejected=rows_rejected,
            rows_loaded=rows_loaded,
            raw_file=raw_file,
            clean_file=clean_file,
            rejected_file=rejected_file
        )

        print(f"Productos extraidos: {rows_extracted}")
        print(f"Productos validos: {rows_valid}")
        print(f"Productos rechazados: {rows_rejected}")
        print(f"Productos cargados en PostgreSQL: {rows_loaded}")
        print(f"RAW guardado en: {raw_file}")
        print(f"Clean guardado en: {clean_file}")

        if rejected_file:
            print(f"Rejected guardado en: {rejected_file}")

    except Exception as error:
        finish_pipeline_run(
            run_id=run_id,
            status="FAILED",
            rows_extracted=rows_extracted,
            rows_valid=rows_valid,
            rows_rejected=rows_rejected,
            rows_loaded=rows_loaded,
            raw_file=raw_file,
            clean_file=clean_file,
            rejected_file=rejected_file,
            error_message=str(error)
        )

        print(f"Pipeline failed: {error}")

        raise