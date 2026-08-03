"""FruitFresh Flask Web Application.

Provides admin dashboard, fruit management, and REST API endpoints.
"""

import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Security: Load secret key from environment or use secure default
app.secret_key = os.environ.get("SECRET_KEY", "fruitfresh123")

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Admin Auth Credentials (configurable via environment with backward compatibility)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "1234")


def get_db_connection() -> sqlite3.Connection:
    """Create and return a database connection with sqlite3.Row factory.

    Returns:
        sqlite3.Connection: Database connection instance.
    """
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def query_db(
    query: str,
    args: tuple = (),
    one: bool = False,
    commit: bool = False
) -> Optional[Union[List[sqlite3.Row], sqlite3.Row, int]]:
    """Execute a database query safely with resource management.

    Args:
        query: SQL query string.
        args: Query parameter values.
        one: If True, return single row result.
        commit: If True, commit changes to database.

    Returns:
        QueryResult: Single row, list of rows, or None.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        if commit:
            conn.commit()
            return cursor.rowcount
        rv = cursor.fetchall()
        return (rv[0] if rv else None) if one else rv


@app.route("/")
def home() -> str:
    """Render customer homepage with all available fruits."""
    fruits = query_db("SELECT * FROM fruits")
    return render_template("index.html", fruits=fruits)


@app.route("/admin")
def admin() -> str:
    """Render admin dashboard with fruit statistics."""
    total_fruits = query_db("SELECT COUNT(*) FROM fruits", one=True)[0]
    total_stock_row = query_db("SELECT SUM(stock) FROM fruits", one=True)
    total_stock = total_stock_row[0] if total_stock_row and total_stock_row[0] is not None else 0
    total_categories = query_db("SELECT COUNT(DISTINCT category) FROM fruits", one=True)[0]
    low_stock = query_db("SELECT COUNT(*) FROM fruits WHERE stock < 10", one=True)[0]

    return render_template(
        "admin_dashboard.html",
        total_fruits=total_fruits,
        total_stock=total_stock,
        total_categories=total_categories,
        low_stock=low_stock,
    )


@app.route("/login", methods=["GET", "POST"])
def login() -> Union[str, Response]:
    """Handle admin authentication."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

        return "Invalid Username or Password"

    return render_template("login.html")


@app.route("/logout")
def logout() -> Response:
    """Handle admin logout and session invalidation."""
    session.pop("admin", None)
    return redirect("/login")


@app.route("/fruit-list")
def fruit_list() -> str:
    """Render admin fruit inventory list."""
    return render_template("fruit_list.html")


@app.route("/delete-fruit/<int:fruit_id>")
def delete_fruit(fruit_id: int) -> Response:
    """Delete a fruit by ID from the database."""
    query_db("DELETE FROM fruits WHERE id = ?", (fruit_id,), commit=True)
    return redirect("/fruit-list")


@app.route("/edit-fruit/<int:fruit_id>", methods=["GET", "POST"])
def edit_fruit(fruit_id: int) -> Union[str, Response]:
    """Handle editing an existing fruit's details."""
    fruit = query_db("SELECT * FROM fruits WHERE id=?", (fruit_id,), one=True)

    if request.method == "POST":
        fruit_name = " ".join(request.form.get("fruit_name", "").split())
        price = request.form.get("price")
        category = request.form.get("category")
        stock = request.form.get("stock")

        # Check duplicate fruit name (excluding current fruit ID)
        existing = query_db(
            "SELECT * FROM fruits WHERE LOWER(fruit_name)=LOWER(?) AND id != ?",
            (fruit_name, fruit_id),
            one=True,
        )

        if existing:
            return render_template(
                "edit_fruit.html",
                fruit=fruit,
                error="Fruit already exists!",
            )

        image = request.files.get("image")
        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))

            query_db(
                """
                UPDATE fruits
                SET fruit_name=?, price=?, category=?, stock=?, image=?
                WHERE id=?
                """,
                (fruit_name, price, category, stock, filename, fruit_id),
                commit=True,
            )
        else:
            query_db(
                """
                UPDATE fruits
                SET fruit_name=?, price=?, category=?, stock=?
                WHERE id=?
                """,
                (fruit_name, price, category, stock, fruit_id),
                commit=True,
            )

        return redirect("/fruit-list")

    return render_template("edit_fruit.html", fruit=fruit)


@app.route("/add-fruit", methods=["GET", "POST"])
def add_fruit() -> Union[str, Response]:
    """Handle adding a new fruit to the inventory."""
    if request.method == "POST":
        fruit_name = " ".join(request.form.get("fruit_name", "").split())
        price = request.form.get("price")
        category = request.form.get("category")
        stock = request.form.get("stock")
        image = request.files.get("image")

        filename = None
        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))

        # Check duplicate fruit name
        existing = query_db(
            "SELECT * FROM fruits WHERE LOWER(fruit_name) = LOWER(?)",
            (fruit_name,),
            one=True,
        )

        if existing:
            return render_template(
                "add_fruit.html",
                error="Fruit already exists!",
            )

        query_db(
            """
            INSERT INTO fruits (fruit_name, price, category, stock, image)
            VALUES (?, ?, ?, ?, ?)
            """,
            (fruit_name, price, category, stock, filename),
            commit=True,
        )

        return redirect("/fruit-list")

    return render_template("add_fruit.html")


@app.route("/api/fruits", methods=["GET"])
def get_all_fruits() -> Response:
    """REST API endpoint to retrieve all fruits as JSON."""
    fruits = query_db("SELECT * FROM fruits")
    fruits_list = [dict(fruit) for fruit in fruits] if fruits else []
    return jsonify(fruits_list)


@app.route("/api/fruits/<int:fruit_id>", methods=["GET"])
def get_fruit(fruit_id: int) -> Tuple[Response, int]:
    """REST API endpoint to retrieve a single fruit by ID as JSON."""
    fruit = query_db("SELECT * FROM fruits WHERE id = ?", (fruit_id,), one=True)

    if fruit:
        return jsonify(dict(fruit)), 200

    return jsonify({"message": "Fruit not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)