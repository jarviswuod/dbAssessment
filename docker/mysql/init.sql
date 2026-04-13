-- Seed data for MySQL test database
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customers (name, email, phone, city, country) VALUES
('Acme Corp', 'contact@acme.com', '+1-555-0101', 'New York', 'USA'),
('Globex Inc', 'info@globex.com', '+1-555-0102', 'Chicago', 'USA'),
('Initech', 'support@initech.com', '+1-555-0103', 'Austin', 'USA'),
('Umbrella Ltd', 'hello@umbrella.co.uk', '+44-20-7946-0958', 'London', 'UK'),
('Wayne Enterprises', 'bruce@wayne.com', '+1-555-0105', 'Gotham', 'USA'),
('Stark Industries', 'tony@stark.com', '+1-555-0106', 'Malibu', 'USA'),
('Oscorp', 'norman@oscorp.com', '+1-555-0107', 'New York', 'USA'),
('LexCorp', 'lex@lexcorp.com', '+1-555-0108', 'Metropolis', 'USA'),
('Cyberdyne', 'info@cyberdyne.com', '+81-3-1234-5678', 'Tokyo', 'Japan'),
('Weyland Corp', 'contact@weyland.com', '+1-555-0110', 'San Francisco', 'USA');

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    quantity INT DEFAULT 1,
    total_amount DECIMAL(12, 2),
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

INSERT INTO orders (customer_id, product_name, quantity, total_amount, status) VALUES
(1, 'Server Rack', 2, 4500.00, 'delivered'),
(2, 'Network Switch', 5, 1250.00, 'shipped'),
(3, 'Firewall Appliance', 1, 2800.00, 'processing'),
(4, 'SSD 1TB', 10, 990.00, 'pending'),
(5, 'UPS System', 3, 1800.00, 'delivered'),
(1, 'CAT6 Cable Box', 20, 600.00, 'shipped'),
(6, 'GPU Server', 1, 12000.00, 'processing'),
(7, 'RAM 64GB Kit', 4, 1200.00, 'delivered'),
(8, 'Cooling System', 2, 3400.00, 'pending'),
(9, 'Blade Server', 1, 8500.00, 'shipped');
