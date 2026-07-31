import sqlite3

# Connect to database
conn = sqlite3.connect("database.db")

# Create cursor
cursor = conn.cursor()

# Create fruits table
cursor.execute("""
CREATE TABLE IF NOT EXISTS fruits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fruit_name TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    stock INTEGER NOT NULL,
    image TEXT
)
""")
cursor.execute("""
INSERT INTO fruits (fruit_name, price, category, stock, image)
VALUES
('Apple', 120, 'Fresh Fruits', 50, 'apple.jpg'),
('Banana', 60, 'Fresh Fruits', 80, 'banana.jpg'),
('Mango', 250, 'Seasonal', 25, 'mango.jpg'),
('Orange', 140, 'Citrus', 40, 'orange.jpg')
""")


# Save changes
conn.commit()

# Close database
conn.close()

print("✅ Fruits table created successfully!") 

 
