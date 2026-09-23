
REQUIRED_KEYS = ["products", "total", "skip", "limit"]

PRODUCT_REQUIRED_FIELDS = [
    "id",
    "title",
    "category",
    "price",
    "stock",
    "sku"
]

def validate_products_payload(payload):
    if not isinstance(payload, dict):
        raise TypeError("Products payload must be a dictionary.")

    missing_keys = []

    for required_key in REQUIRED_KEYS:
        if required_key not in payload:
            missing_keys.append(required_key)

    if missing_keys:
        raise ValueError(
            f"Source schema mismatch. Missing required keys: {missing_keys}"
        )

    if not isinstance(payload["products"], list):
        raise TypeError("'products' must be a list.")

    return True

def validate_product_record(product):
    errors = []

    for required_field in PRODUCT_REQUIRED_FIELDS:
        if required_field not in product:
            errors.append(f"Missing required field: {required_field}")

    if "id" in product and not isinstance(product["id"], int):
        errors.append("id must be an int")

    if "title" in product:
        if not isinstance(product["title"], str):
            errors.append("title must be a string")
        elif not product["title"].strip():
            errors.append("title cannot be empty")

    if "category" in product:
        if not isinstance(product["category"], str):
            errors.append("category must be a string")
        elif not product["category"].strip():
            errors.append("category cannot be empty")

    if "price" in product:
        if not isinstance(product["price"], (int, float)):
            errors.append("price must be numeric")
        elif product["price"] < 0:
            errors.append("price can not be negative")

    if "stock" in product:
        if not isinstance(product["stock"], int):
            errors.append("stock must be an int")
        elif product["stock"] < 0:
            errors.append("stock cannot be negative")

    if "sku" in product:
        if not isinstance(product["sku"], str):
            errors.append("sku must be a string")
        elif not product["sku"].strip():
            errors.append("sku can not be empty")

    return errors


def validate_products_batch(products):
    valid_products = []
    rejected_products = []

    for product in products:
        errors = validate_product_record(product)

        if errors:
            rejected_products.append({
                "product": product,
                "erros": errors
            })

        else:
            valid_products.append(product)

    return valid_products, rejected_products

if __name__ == "__main__":
    valid_products_data = {
        "products": [],
        "total": 0,
        "skip": 0,
        "limit": 0
    }

    result = validate_products_payload(valid_products_data)

    print(result)

    invalid_product = {
        "id": 1,
        "title": "laptop"
    }

    product_errors = validate_product_record(invalid_product)

    print(product_errors)