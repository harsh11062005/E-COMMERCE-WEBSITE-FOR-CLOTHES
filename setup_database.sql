-- Drop database if exists and create new one
DROP DATABASE IF EXISTS thrifty;
CREATE DATABASE thrifty;
USE thrifty;

-- Create tables with additional fields for authentication and images
CREATE TABLE employees (
    emp_id INT AUTO_INCREMENT PRIMARY KEY,
    emp_name VARCHAR(100) NOT NULL,
    emp_address TEXT,
    emp_no VARCHAR(20) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    email_address VARCHAR(100) UNIQUE,
    phone_number VARCHAR(20) UNIQUE,
    password VARCHAR(100) NOT NULL,
    emp_id INT,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

CREATE TABLE sellers (
    seller_id INT AUTO_INCREMENT PRIMARY KEY,
    seller_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100) NOT NULL,
    emp_id INT,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL,
    image_url VARCHAR(255),
    category VARCHAR(50),
    seller_id INT,
    emp_id INT,
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    emp_id INT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

CREATE TABLE order_details (
    order_id INT,
    product_id INT,
    quantity INT NOT NULL,
    price_at_time DECIMAL(10,2) NOT NULL,
    emp_id INT,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

CREATE TABLE seller_addresses (
    seller_id INT PRIMARY KEY,
    seller_address TEXT NOT NULL,
    seller_no VARCHAR(20) UNIQUE,
    emp_id INT,
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

CREATE TABLE seller_orders (
    seller_order_id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    emp_id INT,
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

CREATE TABLE tracking_details (
    track_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    status VARCHAR(50) NOT NULL,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    emp_id INT,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

-- Insert admin user
INSERT INTO employees (emp_name, emp_address, emp_no, email, password, is_admin)
VALUES ('Admin', 'Admin Address', '1234567890', 'admin@thrifty.com', 'admin123', TRUE);

-- Insert sample sellers
INSERT INTO sellers (seller_name, email, password)
VALUES 
('Fashion Store', 'fashion@store.com', 'fashion123'),
('Trendy Clothes', 'trendy@clothes.com', 'trendy123');

-- Insert sample products
INSERT INTO products (name, description, price, quantity, image_url, category, seller_id)
VALUES
('Classic T-Shirt', 'Comfortable cotton t-shirt in various colors', 19.99, 100, '/static/images/tshirt.jpg', 'Clothing', 1),
('Denim Jeans', 'High-quality denim jeans with perfect fit', 49.99, 50, '/static/images/jeans.jpg', 'Clothing', 1),
('Summer Dress', 'Light and breezy summer dress', 39.99, 30, '/static/images/dress.jpg', 'Clothing', 2),
('Casual Shirt', 'Button-down casual shirt for any occasion', 29.99, 75, '/static/images/shirt.jpg', 'Clothing', 2); 