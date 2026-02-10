import sqlite3
import os

def create_sample_db():
    """Create sample SQLite database with sales data and related tables."""
    conn = None
    try:
        # Remove existing database if it exists
        if os.path.exists("sales.db"):
            os.remove("sales.db")
            
        conn = sqlite3.connect("sales.db")
        c = conn.cursor()

        # Create regions table
        c.execute('''CREATE TABLE regions (
                        region_id INTEGER PRIMARY KEY,
                        region_name TEXT UNIQUE
                    )''')

        # Create products table
        c.execute('''CREATE TABLE products (
                        product_id INTEGER PRIMARY KEY,
                        product_name TEXT UNIQUE,
                        price REAL
                    )''')

        # Create customers table
        c.execute('''CREATE TABLE customers (
                        customer_id INTEGER PRIMARY KEY,
                        customer_name TEXT UNIQUE,
                        region_id INTEGER,
                        FOREIGN KEY(region_id) REFERENCES regions(region_id)
                    )''')

        # Create salespersons table
        c.execute('''CREATE TABLE salespersons (
                        salesperson_id INTEGER PRIMARY KEY,
                        customer_name TEXT UNIQUE,
                        region_id INTEGER,
                        FOREIGN KEY(region_id) REFERENCES regions(region_id)
                    )''')

        # Create sales table
        c.execute('''CREATE TABLE sales (
                        sale_id INTEGER PRIMARY KEY,
                        region_id INTEGER,
                        product_id INTEGER,
                        customer_id INTEGER,
                        salesperson_id INTEGER,
                        amount REAL,
                        date TEXT,
                        FOREIGN KEY(region_id) REFERENCES regions(region_id),
                        FOREIGN KEY(product_id) REFERENCES products(product_id),
                        FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
                        FOREIGN KEY(salesperson_id) REFERENCES salespersons(salesperson_id)
                    )''')

        # Insert sample data
        regions = [
            (1, 'North'),
            (2, 'South'),
            (3, 'East'),
            (4, 'West')
        ]
        c.executemany("INSERT INTO regions (region_id, region_name) VALUES (?, ?)", regions)

        products = [
            (1, 'Widget', 25.0),
            (2, 'Gadget', 40.0),
            (3, 'Thingamajig', 15.0)
        ]
        c.executemany("INSERT INTO products (product_id, product_name, price) VALUES (?, ?, ?)", products)

        customers = [
            (1, 'Alice', 1),
            (2, 'Bob', 2),
            (3, 'Charlie', 3),
            (4, 'Diana', 4)
        ]
        c.executemany("INSERT INTO customers (customer_id, customer_name, region_id) VALUES (?, ?, ?)", customers)

        salespersons = [
            (1, 'Eve', 1),
            (2, 'Frank', 2),
            (3, 'Grace', 3),
            (4, 'Heidi', 4)
        ]
        c.executemany("INSERT INTO salespersons (salesperson_id, salesperson_name, region_id) VALUES (?, ?, ?)", salespersons)

        sales = [
            (1, 1, 1, 1, 1, 1000.50, '2023-10-01'),
            (2, 2, 2, 2, 2, 850.00, '2023-10-02'),
            (3, 3, 3, 3, 3, 920.75, '2023-10-03'),
            (4, 4, 1, 4, 4, 760.00, '2023-10-04'),
            (5, 1, 2, 1, 1, 500.00, '2023-10-05')
        ]
        c.executemany("""
            INSERT INTO sales (sale_id, region_id, product_id, customer_id, salesperson_id, amount, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sales)

        conn.commit()
        print("Database created successfully with sample data!")
        
        # Verify data was inserted
        c.execute("SELECT COUNT(*) FROM sales")
        sales_count = c.fetchone()[0]
        print(f"Inserted {sales_count} sales records")
        
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_sample_db()