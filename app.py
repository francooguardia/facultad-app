from flask import Flask, request, jsonify, send_from_directory
import psycopg2

app = Flask(__name__)

DB_URL = "postgresql://postgres:4cfW3XZmCNqIQi4f@db.powotolytlsxhtecbmbq.supabase.co:5432/postgres"

def get_db():
    return psycopg2.connect(DB_URL)

# -------- CREAR USUARIO (TEMPORAL) --------

@app.route("/create_user")
def create_user():
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        ("admin", "1234")
    )

    db.commit()
    cur.close()
    db.close()

    return "usuario creado"


# -------- LOGIN --------

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT id FROM users WHERE username=%s AND password=%s",
        (data["username"], data["password"])
    )

    user = cur.fetchone()

    cur.close()
    db.close()

    if user:
        return {"user_id": user[0]}
    else:
        return {"error": "error"}, 401


# -------- EVENTS --------

@app.route("/add_event", methods=["POST"])
def add_event():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO events (user_id, title, date) VALUES (%s, %s, %s)",
        (data["user_id"], data["title"], data["date"])
    )

    db.commit()
    cur.close()
    db.close()

    return {"status": "ok"}


# 👉 ESTE ES EL QUE TE FALTABA
@app.route("/events/<int:user_id>")
def get_events(user_id):
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT id, title, date FROM events WHERE user_id=%s",
        (user_id,)
    )

    events = cur.fetchall()

    cur.close()
    db.close()

    return jsonify(events)


# -------- NOTES --------

@app.route("/save_note", methods=["POST"])
def save_note():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO notes (user_id, date, content)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, date)
        DO UPDATE SET content = EXCLUDED.content
    """, (data["user_id"], data["date"], data["content"]))

    db.commit()
    cur.close()
    db.close()

    return {"status": "saved"}


@app.route("/note/<int:user_id>/<date>")
def get_note(user_id, date):
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT content FROM notes WHERE user_id=%s AND date=%s",
        (user_id, date)
    )

    note = cur.fetchone()

    cur.close()
    db.close()

    return jsonify(note if note else [""])


# -------- FRONT --------

@app.route("/")
def home():
    return send_from_directory("static", "index.html")


# 🔥 IMPORTANTE (para usar en celular)
if __name__ == "__main__":
    app.run()