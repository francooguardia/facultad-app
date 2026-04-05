from flask import Flask, request, jsonify, send_from_directory
import psycopg2
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# 🔥 DB desde Render
DB_URL = os.environ.get("DB_URL")

def get_db():
    return psycopg2.connect(DB_URL)


# -------- REGISTER --------

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        if not data:
            return {"error": "No data received"}, 400

        username = data.get("username")
        password = data.get("password")
        email = data.get("email")

        if not username or not password:
            return {"error": "Faltan datos"}, 400

        db = get_db()
        cur = db.cursor()

        # 🚫 evitar usuarios duplicados
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            return {"error": "Usuario ya existe"}, 400

        cur.execute(
            "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
            (username, password, email)
        )

        db.commit()

        # 📧 enviar mail (opcional)
        try:
            email_user = os.environ.get("EMAIL_USER")
            email_pass = os.environ.get("EMAIL_PASS")

            if email_user and email_pass and email:
                msg = MIMEText(f"""
Hola {username} 👋

Tu cuenta en Facultad Franco fue creada correctamente 🚀

¡Éxitos en tu cursada! 📚
                """)

                msg["Subject"] = "Registro exitoso"
                msg["From"] = email_user
                msg["To"] = email

                server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
                server.login(email_user, email_pass)
                server.send_message(msg)
                server.quit()

        except Exception as e:
            print("⚠️ Error enviando mail:", e)

        cur.close()
        db.close()

        return {"status": "registered"}

    except Exception as e:
        return {"error": str(e)}, 500


# -------- LOGIN --------

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT id FROM users WHERE LOWER(username)=LOWER(%s) AND password=%s",
            (username, password)
        )

        user = cur.fetchone()

        cur.close()
        db.close()

        if user:
            return {"user_id": user[0]}
        else:
            return {"error": "Credenciales incorrectas"}, 401

    except Exception as e:
        return {"error": str(e)}, 500


# -------- EVENTS --------

@app.route("/add_event", methods=["POST"])
def add_event():
    try:
        data = request.get_json()

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

    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/events/<int:user_id>")
def get_events(user_id):
    try:
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

    except Exception as e:
        return {"error": str(e)}, 500


# -------- NOTES --------

@app.route("/save_note", methods=["POST"])
def save_note():
    try:
        data = request.get_json()

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

    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/note/<int:user_id>/<date>")
def get_note(user_id, date):
    try:
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

    except Exception as e:
        return {"error": str(e)}, 500


# -------- FRONT --------

@app.route("/")
def home():
    return send_from_directory("static", "index.html")


# 🔥 PARA RENDER
if __name__ == "__main__":
    app.run()