SELECT
    COUNT(*) AS total_products,
    COUNT(DISTINCT category) AS total_categories,
    ROUND(AVG(price), 2) AS average_price,
    SUM(stock) AS total_stock
FROM products;

SELECT
    category,
    COUNT(*) AS product_count,
    ROUND(AVG(price), 2) AS average_price,
    SUM(stock) AS total_stock
FROM products
GROUP BY category
ORDER BY product_count DESC;


SELECT
    product_id,
    sku,
    title,
    category,
    price,
    stock,
    price * stock AS inventory_value
FROM products
ORDER BY inventory_value DESC
LIMIT 10;

SELECT
    category,
    ROUND(SUM(price * stock), 2) AS inventory_value
FROM products
GROUP BY category
ORDER BY inventory_value DESC;