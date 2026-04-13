-- Seed data for PostgreSQL test database
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    department VARCHAR(100),
    salary NUMERIC(12, 2),
    hire_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO employees (first_name, last_name, email, department, salary, hire_date, is_active) VALUES
('Alice', 'Johnson', 'alice.johnson@example.com', 'Engineering', 95000.00, '2020-03-15', TRUE),
('Bob', 'Smith', 'bob.smith@example.com', 'Marketing', 72000.00, '2019-07-22', TRUE),
('Charlie', 'Brown', 'charlie.brown@example.com', 'Engineering', 88000.00, '2021-01-10', TRUE),
('Diana', 'Prince', 'diana.prince@example.com', 'HR', 68000.00, '2018-11-05', TRUE),
('Edward', 'Norton', 'edward.norton@example.com', 'Finance', 91000.00, '2020-06-18', FALSE),
('Fiona', 'Apple', 'fiona.apple@example.com', 'Engineering', 102000.00, '2017-09-30', TRUE),
('George', 'Lucas', 'george.lucas@example.com', 'Marketing', 76000.00, '2022-02-14', TRUE),
('Hannah', 'Montana', 'hannah.montana@example.com', 'HR', 64000.00, '2021-08-25', TRUE),
('Ivan', 'Drago', 'ivan.drago@example.com', 'Finance', 87000.00, '2019-12-01', TRUE),
('Julia', 'Roberts', 'julia.roberts@example.com', 'Engineering', 99000.00, '2020-04-20', TRUE);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price NUMERIC(10, 2),
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO products (name, category, price, stock_quantity) VALUES
('Laptop Pro 15', 'Electronics', 1299.99, 45),
('Wireless Mouse', 'Electronics', 29.99, 200),
('Office Chair', 'Furniture', 449.00, 30),
('Standing Desk', 'Furniture', 699.00, 15),
('USB-C Hub', 'Electronics', 59.99, 120),
('Monitor 27"', 'Electronics', 399.99, 60),
('Keyboard Mechanical', 'Electronics', 89.99, 80),
('Desk Lamp', 'Furniture', 34.99, 150),
('Webcam HD', 'Electronics', 79.99, 90),
('Headset Wireless', 'Electronics', 149.99, 70);
