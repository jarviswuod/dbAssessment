-- Seed data for ClickHouse test database
CREATE TABLE IF NOT EXISTS testdb.web_analytics (
    event_date Date,
    event_time DateTime,
    user_id UInt32,
    page_url String,
    referrer String,
    browser String,
    country String,
    duration_seconds UInt16
) ENGINE = MergeTree()
ORDER BY (event_date, user_id);

INSERT INTO testdb.web_analytics VALUES
('2024-01-15', '2024-01-15 08:00:00', 1001, '/home', 'https://google.com', 'Chrome', 'USA', 45),
('2024-01-15', '2024-01-15 08:05:00', 1002, '/products', 'https://google.com', 'Firefox', 'UK', 120),
('2024-01-15', '2024-01-15 08:10:00', 1001, '/products/laptop', '/products', 'Chrome', 'USA', 200),
('2024-01-15', '2024-01-15 08:15:00', 1003, '/home', 'direct', 'Safari', 'Canada', 30),
('2024-01-15', '2024-01-15 08:20:00', 1004, '/about', 'https://bing.com', 'Edge', 'Germany', 60),
('2024-01-15', '2024-01-15 08:25:00', 1002, '/cart', '/products', 'Firefox', 'UK', 90),
('2024-01-15', '2024-01-15 08:30:00', 1005, '/home', 'https://twitter.com', 'Chrome', 'Japan', 15),
('2024-01-15', '2024-01-15 08:35:00', 1001, '/checkout', '/cart', 'Chrome', 'USA', 180),
('2024-01-15', '2024-01-15 08:40:00', 1006, '/blog', 'https://reddit.com', 'Firefox', 'France', 240),
('2024-01-15', '2024-01-15 08:45:00', 1003, '/contact', '/about', 'Safari', 'Canada', 55);

CREATE TABLE IF NOT EXISTS testdb.server_metrics (
    timestamp DateTime,
    server_id String,
    cpu_usage Float32,
    memory_usage Float32,
    disk_io_read UInt64,
    disk_io_write UInt64,
    network_in UInt64,
    network_out UInt64
) ENGINE = MergeTree()
ORDER BY (timestamp, server_id);

INSERT INTO testdb.server_metrics VALUES
('2024-01-15 08:00:00', 'srv-001', 45.2, 62.1, 1024000, 512000, 2048000, 1024000),
('2024-01-15 08:00:00', 'srv-002', 78.5, 81.3, 2048000, 1024000, 4096000, 2048000),
('2024-01-15 08:05:00', 'srv-001', 42.8, 61.5, 980000, 490000, 1950000, 980000),
('2024-01-15 08:05:00', 'srv-002', 82.1, 83.7, 2200000, 1100000, 4200000, 2100000),
('2024-01-15 08:10:00', 'srv-001', 55.3, 64.2, 1200000, 600000, 2400000, 1200000),
('2024-01-15 08:10:00', 'srv-002', 71.9, 79.8, 1800000, 900000, 3600000, 1800000),
('2024-01-15 08:15:00', 'srv-001', 38.7, 59.8, 900000, 450000, 1800000, 900000),
('2024-01-15 08:15:00', 'srv-002', 88.4, 86.2, 2500000, 1250000, 5000000, 2500000),
('2024-01-15 08:20:00', 'srv-001', 61.2, 67.3, 1400000, 700000, 2800000, 1400000),
('2024-01-15 08:20:00', 'srv-002', 75.6, 80.1, 1900000, 950000, 3800000, 1900000);
