import pytest

from src.validation.products_validator import (
    validate_products_payload,
    validate_product_record
)

def test_valid_products_payload():
    valid_payload = {
        "products": [],
        "total": 0,
        "skip": 0,
        "limit": 0
    }

    result = validate_products_payload(valid_payload)

    assert result is True


def test_payload_missing_required_keys():
    invalid_payload = {
        "products": []
    }

    with pytest.raises(ValueError):
        validate_products_payload(invalid_payload)


def test_product_record_collects_multiple_errors():
    invalid_product = {
        "id": "ABC",
        "title": "  ",
        "category": 123,
        "price": -50,
        "stock": -3,
        "sku": ""
    }

    errors = validate_product_record(invalid_product)

    assert len(errors) == 6


def test_valid_product_record_has_no_errors():
    valid_product = {
        "id": 1,
        "title": "Laptop",
        "category": "electronics",
        "price": 999.99,
        "stock": 10,
        "sku": "LAPTOP-001"
    }

    errors = validate_product_record(valid_product)

    assert errors == []