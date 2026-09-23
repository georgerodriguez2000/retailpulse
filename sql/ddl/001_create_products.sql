CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    sku VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    brand VARCHAR(100),
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    rating NUMERIC(3, 2),
    source_updated_at TIMESTAMP,
    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);