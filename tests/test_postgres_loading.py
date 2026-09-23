from src.loading.postgres import (
    get_connection,
    insert_products_batch
)

TEST_PRODUCTS = [
    {
        "id": 900001,
        "sku": "TEST-900001",
        "title": "Integration Test Product 1",
        "category": "test",
        "brand": "RetailPulse",
        "price": 10.50,
        "stock": 5,
        "rating": 4.20
    },
    {
        "id": 900002,
        "sku": "TEST-900002",
        "title": "Integration Test Product 2",
        "category": "test",
        "brand": "RetailPulse",
        "price": 20.50,
        "stock": 8,
        "rating": 4.40
    }
]

def delete_test_products():
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM products
            WHERE product_id IN (900001, 900002);
            """
        )

    connection.commit()
    connection.close()


def test_batch_insert_and_upsert():
    try:
        insert_products_batch(TEST_PRODUCTS)

        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM products
                WHERE product_id IN (900001, 900002);
                """
            )

            count = cursor.fetchone()[0]

        connection.close()

        assert count == 2

        updated_products = TEST_PRODUCTS.copy()

        updated_products[0] = TEST_PRODUCTS[0].copy()
        updated_products[0]["price"] = 99.99

        insert_products_batch(updated_products)

        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT price
                FROM products
                WHERE product_id = 900001;
                """
            )

            updated_price = cursor.fetchone()[0]

        connection.close()

        assert float(updated_price) == 99.99

    finally:
        delete_test_products()

