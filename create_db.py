"""FruitFresh Database Initialization Script.

Creates the fruits table and populates initial sample data if not present.
"""

import sqlite3


def init_db(db_path: str = "database.db") -> None:
    """Initialize the SQLite database schema and sample seed records.

    Args:
        db_path: Path to the SQLite database file.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Create fruits table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fruits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fruit_name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                stock INTEGER NOT NULL,
                image TEXT
            )
            """
        )

        # Check existing data before inserting seed data
        cursor.execute("SELECT COUNT(*) FROM fruits")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO fruits (fruit_name, price, category, stock, image)
                VALUES
                ('Apple', 120, 'Fresh Fruits', 50, 'apple.jpg'),
                ('Banana', 60, 'Fresh Fruits', 80, 'banana.jpg'),
                ('Mango', 250, 'Seasonal', 25, 'mango.jpg'),
                ('Orange', 140, 'Citrus', 40, 'orange.jpg')
                """
            )
            conn.commit()

        print("[SUCCESS] Fruits table created successfully!")


if __name__ == "__main__":
    init_db()
