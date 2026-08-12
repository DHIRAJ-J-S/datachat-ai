-- E-commerce sample database

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_name TEXT,
    contact_email TEXT
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER,
    supplier_id INTEGER,
    price REAL NOT NULL,
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES categories (id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
);

CREATE TABLE inventory (
    product_id INTEGER PRIMARY KEY,
    quantity INTEGER NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    join_date DATE NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date DATETIME NOT NULL,
    status TEXT NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- Insert sample data
INSERT INTO categories (name, description) VALUES 
('Electronics', 'Gadgets and devices'),
('Clothing', 'Apparel and accessories'),
('Home & Garden', 'Furniture and tools'),
('Sports', 'Athletic equipment'),
('Books', 'Physical and digital books');

INSERT INTO suppliers (name, contact_name, contact_email) VALUES
('TechCorp', 'John Doe', 'john@techcorp.com'),
('FashionInc', 'Jane Smith', 'jane@fashioninc.com'),
('HomeGoods LLC', 'Bob Johnson', 'bob@homegoods.com'),
('Sporty', 'Alice Williams', 'alice@sporty.com'),
('BookWorm', 'Charlie Brown', 'charlie@bookworm.com');

INSERT INTO products (name, category_id, supplier_id, price, description) VALUES
('Smartphone X', 1, 1, 799.99, 'Latest smartphone'),
('Laptop Pro', 1, 1, 1299.99, 'High performance laptop'),
('Wireless Earbuds', 1, 1, 149.99, 'Noise cancelling earbuds'),
('Smart Watch', 1, 1, 199.99, 'Fitness tracking watch'),
('T-Shirt', 2, 2, 19.99, 'Cotton t-shirt'),
('Jeans', 2, 2, 49.99, 'Denim jeans'),
('Sneakers', 2, 2, 89.99, 'Running shoes'),
('Winter Jacket', 2, 2, 129.99, 'Warm winter jacket'),
('Sofa', 3, 3, 499.99, 'Comfortable 3-seater sofa'),
('Coffee Table', 3, 3, 149.99, 'Wooden coffee table'),
('Desk Lamp', 3, 3, 39.99, 'LED desk lamp'),
('Blender', 3, 3, 79.99, 'High speed blender'),
('Tennis Racket', 4, 4, 119.99, 'Professional tennis racket'),
('Yoga Mat', 4, 4, 29.99, 'Non-slip yoga mat'),
('Dumbbells', 4, 4, 49.99, 'Set of 2 dumbbells'),
('Basketball', 4, 4, 24.99, 'Official size basketball'),
('Python Crash Course', 5, 5, 39.99, 'Learn Python programming'),
('Clean Code', 5, 5, 45.99, 'A Handbook of Agile Software Craftsmanship'),
('Design Patterns', 5, 5, 54.99, 'Elements of Reusable Object-Oriented Software'),
('The Pragmatic Programmer', 5, 5, 49.99, 'From Journeyman to Master');

-- Inventory
INSERT INTO inventory (product_id, quantity) SELECT id, ABS(RANDOM() % 100) + 10 FROM products;

-- Generate 50 Customers
WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt WHERE x<50)
INSERT INTO customers (first_name, last_name, email, join_date)
SELECT 
  'FirstName' || x, 
  'LastName' || x, 
  'user' || x || '@example.com',
  date('2024-01-01', '+' || (ABS(RANDOM() % 700)) || ' days')
FROM cnt;

-- Generate 200 Orders
WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt WHERE x<200)
INSERT INTO orders (customer_id, order_date, status, total_amount)
SELECT 
  (ABS(RANDOM() % 50) + 1),
  datetime('2024-01-01', '+' || (ABS(RANDOM() % 700)) || ' days', '+' || (ABS(RANDOM() % 24)) || ' hours'),
  CASE (ABS(RANDOM() % 4))
    WHEN 0 THEN 'Pending'
    WHEN 1 THEN 'Processing'
    WHEN 2 THEN 'Shipped'
    ELSE 'Delivered'
  END,
  (ABS(RANDOM() % 1000) + 10.99)
FROM cnt;

-- Generate Order Items
WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt WHERE x<450)
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT 
  (ABS(RANDOM() % 200) + 1),
  (ABS(RANDOM() % 20) + 1),
  (ABS(RANDOM() % 5) + 1),
  (SELECT price FROM products WHERE id = (ABS(RANDOM() % 20) + 1))
FROM cnt;
