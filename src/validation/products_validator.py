REQUIRED_KEYS = ["products", "total", "skip", "limit"]

def validate_products_payload(products_data):
    if not isinstance(products_data, dict):
        raise TypeError("Products payload must be a dictionary.")

    for required_key in REQUIRED_KEYS:
        if required_key not in products_data:
            raise KeyError(f"Missing required key: {required_key}")

    if not isinstance(products_data["products"], list):
        raise TypeError("'products' must be a list.")

    return True

if __name__ == "__main__":
    invalid_products_data = {
        "products": "this is a test",
        "total": 0,
        "skip": 0,
        "limit": 0
    }

    result = validate_products_payload(invalid_products_data)

    print(result)