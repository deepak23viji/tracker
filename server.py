from http.server import BaseHTTPRequestHandler, HTTPServer
import json, sqlite3
from urllib.parse import urlparse, parse_qs
from datetime import date

DB = "assignments.db"

# Create DB
conn = sqlite3.connect(DB)
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
conn.close()

class Handler(BaseHTTPRequestHandler):

    def _send(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/assignments":
            qs = parse_qs(parsed.query)
            search = qs.get("search", [""])[0]
            status = qs.get("status", ["All"])[0]

            query = "SELECT * FROM assignments WHERE 1=1"
            params = []

            if status != "All":
                query += " AND status=?"
                params.append(status)

            if search:
                query += " AND (title LIKE ? OR subject LIKE ?)"
                params += [f"%{search}%", f"%{search}%"]

            conn = sqlite3.connect(DB)
            rows = conn.execute(query, params).fetchall()
            conn.close()

            data = [
                dict(id=r[0], title=r[1], subject=r[2],
                     due_date=r[3], status=r[4], priority=r[5])
                for r in rows
            ]
            return self._send(data)

        if parsed.path == "/agent/today":
            today = date.today().isoformat()
            conn = sqlite3.connect(DB)
            rows = conn.execute(
                "SELECT id,title FROM assignments WHERE due_date=? AND status='Pending'",
                (today,)
            ).fetchall()
            conn.close()
            return self._send([{"id": r[0], "title": r[1]} for r in rows])

        self._send({"message": "Backend running"})

    def do_POST(self):
        if self.path == "/assignments":
            length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(length))

            conn = sqlite3.connect(DB)
            conn.execute(
                "INSERT INTO assignments (title, subject, due_date, status, priority) VALUES (?, ?, ?, 'Pending', ?)",
                (data["title"], data["subject"], data["due_date"], data["priority"])
            )
            conn.commit()
            conn.close()
            return self._send({"success": True})

    def do_PUT(self):
        if self.path.startswith("/assignments/") and self.path.endswith("/complete"):
            id = self.path.split("/")[2]
            conn = sqlite3.connect(DB)
            conn.execute("UPDATE assignments SET status='Completed' WHERE id=?", (id,))
            conn.commit()
            conn.close()
            return self._send({"success": True})

    def do_DELETE(self):
        if self.path == "/assignments/completed":
            conn = sqlite3.connect(DB)
            conn.execute("DELETE FROM assignments WHERE status='Completed'")
            conn.commit()
            conn.close()
            return self._send({"success": True})


print("✅ Backend running on http://localhost:3000")
HTTPServer(("localhost", 3000), Handler).serve_forever()
