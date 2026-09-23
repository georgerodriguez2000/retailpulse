import psycopg
import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():
    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    return connection

def insert_product(product):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO PRODUCTS (
            product_id,
            sku,
            title,
            category,
            brand,
            price,
            stock,
            rating
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
        (
            product["id"],
            product["sku"],
            product["title"],
            product["category"],
            product.get("brand"),
            product["price"],
            product["stock"],
            product.get("rating")
        )
    )

    connection.commit()
    connection.close()


def insert_products_batch(products):
    connection = get_connection()

    with connection.cursor() as cursor:
        for product in products:
            cursor.execute(
            """
            INSERT INTO products (
                product_id,
                sku,
                title,
                category,
                brand,
                price,
                stock,
                rating
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_id)
            DO UPDATE SET
                sku = EXCLUDED.sku,
                title = EXCLUDED.title,
                category = EXCLUDED.category,
                brand = EXCLUDED.brand,
                price = EXCLUDED.price,
                stock = EXCLUDED.stock,
                rating = EXCLUDED.rating,
                loaded_at = CURRENT_TIMESTAMP;
                        """,
            (
                product["id"],
                product["sku"],
                product["title"],
                product["category"],
                product.get("brand"),
                product["price"],
                product["stock"],
                product.get("rating")
            )
        )

    connection.commit()
    connection.close()

if __name__ == "__main__":
    test_products = [
    {
        "id": 999001,
        "sku": "PYTHON-TEST-001",
        "title": "Python Test Product 1",
        "category": "test",
        "brand": "RetailPulse",
        "price": 99.99,
        "stock": 10,
        "rating": 4.50
    },
    {
        "id": 999002,
        "sku": "PYTHON-TEST-002",
        "title": "Python Test Product 2",
        "category": "test",
        "brand": "RetailPulse",
        "price": 35.50,
        "stock": 20,
        "rating": 4.20
    }
]

    insert_products_batch(test_products)

    print("Test batch inserted.")