from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import date

app = Flask(__name__)
CORS(app)

DB = "assignments.db"

def get_db():
    return sqlite3.connect(DB)

# Create table
with get_db() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        subject TEXT,
        due_date TEXT,
        status TEXT,
        priority TEXT
    )
    """)

@app.route("/")
def home():
    return "Backend is working"

# Get assignments
@app.route("/assignments", methods=["GET"])
def get_assignments():
    search = request.args.get("search", "")
    status = request.args.get("status", "All")

    query = "SELECT * FROM assignments WHERE 1=1"
    params = []

    if status != "All":
        query += " AND status=?"
        params.append(status)

    if search:
        query += " AND (title LIKE ? OR subject LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY due_date"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    return jsonify(rows)

# Add assignment
@app.route("/assignments", methods=["POST"])
def add_assignment():
    data = request.json
    with get_db() as conn:
        conn.execute(
            "INSERT INTO assignments (title, subject, due_date, status, priority) VALUES (?, ?, ?, 'Pending', ?)",
            (data["title"], data["subject"], data["due_date"], data["priority"])
        )
    return jsonify({"success": True})

# Mark complete
@app.route("/assignments/<int:id>/complete", methods=["PUT"])
def complete_assignment(id):
    with get_db() as conn:
        conn.execute("UPDATE assignments SET status='Completed' WHERE id=?", (id,))
    return jsonify({"success": True})

# Clear completed
@app.route("/assignments/completed", methods=["DELETE"])
def clear_completed():
    with get_db() as conn:
        conn.execute("DELETE FROM assignments WHERE status='Completed'")
    return jsonify({"success": True})

# Agent – due today
@app.route("/agent/today")
def agent_today():
    today = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title FROM assignments WHERE due_date=? AND status='Pending'",
            (today,)
        ).fetchall()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(port=3000, debug=True)


print("✅ Backend running on http://localhost:3000")
HTTPServer(("localhost", 3000), Handler).serve_forever()