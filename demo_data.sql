INSERT INTO categories(name) VALUES ('Electronics'), ('Books'), ('Home');
INSERT INTO products(category_id, sku, name, price, stock) VALUES
(1, 'SKU-001', 'USB-C Cable', 5.99, 100),
(1, 'SKU-002', 'Wireless Mouse', 19.50, 50),
(2, 'SKU-003', 'Clean Code (book)', 29.99, 20),
(3, 'SKU-004', 'Coffee Mug', 9.99, 200);
INSERT INTO customers(email, full_name, phone) VALUES
('ivan@example.com', 'Ivan Ivanov', '+79001234567'),
('anna@example.com', 'Anna Petrova', '+79007654321');
WITH o AS (
  INSERT INTO orders(customer_id, status) VALUES (1, 'processing') RETURNING id
)
INSERT INTO order_items(order_id, product_id, quantity, unit_price)
SELECT o.id, p.id, 2, p.price FROM o, products p WHERE p.sku = 'SKU-002';