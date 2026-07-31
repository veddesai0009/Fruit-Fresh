
from flask import Flask, render_template, request, redirect, jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename
def get_db_connection():
    conn = sqlite3.connect("database.db")
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = "fruitfresh123"

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fruits")
    fruits = cursor.fetchall()

    conn.close()

    return render_template("index.html", fruits=fruits)


@app.route("/admin")
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Fruits
    cursor.execute("SELECT COUNT(*) FROM fruits")
    total_fruits = cursor.fetchone()[0]

    # Total Stock
    cursor.execute("SELECT SUM(stock) FROM fruits")
    total_stock = cursor.fetchone()[0]

    # Total Categories
    cursor.execute("SELECT COUNT(DISTINCT category) FROM fruits")
    total_categories = cursor.fetchone()[0]

    # Low Stock (less than 10)
    cursor.execute("SELECT COUNT(*) FROM fruits WHERE stock < 10")
    low_stock = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_fruits=total_fruits,
        total_stock=total_stock,
        total_categories=total_categories,
        low_stock=low_stock
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["admin"] = True
            return redirect("/admin")

        return "Invalid Username or Password"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")


@app.route("/fruit-list")
def fruit_list():
    return render_template("fruit_list.html")
    
@app.route("/delete-fruit/<int:id>")
def delete_fruit(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM fruits WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/fruit-list")


@app.route("/edit-fruit/<int:id>", methods=["GET", "POST"])
def edit_fruit(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fruits WHERE id=?", (id,))
    fruit = cursor.fetchone()

    if request.method == "POST":
        fruit_name = " ".join(request.form["fruit_name"].split())
        price = request.form["price"]
        category = request.form["category"]
        stock = request.form["stock"]

        # Check duplicate fruit name (excluding this fruit's own id)
        cursor.execute("""
            SELECT * FROM fruits
            WHERE LOWER(fruit_name)=LOWER(?)
            AND id != ?
        """, (fruit_name, id))

        existing = cursor.fetchone()

        if existing:
            conn.close()
            return render_template(
                "edit_fruit.html",
                fruit=fruit,
                error="Fruit already exists!"
            )

        # Handle image upload only if a new file was actually chosen
        image = request.files.get("image")
        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))

            cursor.execute("""
                UPDATE fruits
                SET fruit_name=?, price=?, category=?, stock=?, image=?
                WHERE id=?
            """, (fruit_name, price, category, stock, filename, id))
        else:
            cursor.execute("""
                UPDATE fruits
                SET fruit_name=?, price=?, category=?, stock=?
                WHERE id=?
            """, (fruit_name, price, category, stock, id))

        conn.commit()
        conn.close()

        return redirect("/fruit-list")

    conn.close()

    return render_template("edit_fruit.html", fruit=fruit)


@app.route("/add-fruit", methods=["GET", "POST"])
def add_fruit():
    if request.method == "POST":
        fruit_name = " ".join(request.form["fruit_name"].split())
        price = request.form["price"]
        category = request.form["category"]
        stock = request.form["stock"]
        image = request.files.get("image")

        filename = None
        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check duplicate fruit
        cursor.execute(
            "SELECT * FROM fruits WHERE LOWER(fruit_name) = LOWER(?)",
            (fruit_name,)
        )

        existing = cursor.fetchone()

        if existing:
            conn.close()
            return render_template(
                "add_fruit.html",
                error="Fruit already exists!"
            )

        # Insert new fruit
        cursor.execute("""
            INSERT INTO fruits (fruit_name, price, category, stock, image)
            VALUES (?, ?, ?, ?, ?)
        """, (fruit_name, price, category, stock, filename))

        conn.commit()
        conn.close()

        return redirect("/fruit-list")

    return render_template("add_fruit.html")

@app.route("/api/fruits", methods=["GET"])
def get_all_fruits():

    # Use the same database as the rest of your project
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fruits")
    fruits = cursor.fetchall()

    conn.close()

    fruits_list = []

    for fruit in fruits:
        fruits_list.append(dict(fruit))

    return jsonify(fruits_list)
@app.route("/api/fruits/<int:id>", methods=["GET"])
def get_fruit(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fruits WHERE id = ?", (id,))
    fruit = cursor.fetchone()

    conn.close()

    if fruit:
        return jsonify(dict(fruit))
    else:
        return jsonify({"message": "Fruit not found"}), 404
@app.route("/api/fruits/<int:id>", methods=["GET"])

def get_single_fruit(id):

    conn = get_db_connection()
    cursor = conn.cursor() 

    cursor.execute("SELECT * FROM fruits WHERE id = ?", (id,))
    fruit = cursor.fetchone()

    conn.close()

    if fruit is None:
        return jsonify({"message": "Fruit not found"}), 404

    return jsonify(dict(fruit))

if __name__ == "__main__":
    app.run(debug=True)