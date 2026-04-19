from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import time

# EMAIL
import smtplib
import imaplib
import poplib
import email
from email.mime.text import MIMEText
from email import parser

app = Flask(__name__)
CORS(app)

# ---------------- DB CONNECTION ----------------
conn = None
for i in range(10):
    try:
        conn = psycopg2.connect(
            host="pg-todo",
            database="todo_db",
            user="postgres",
            password="postgres"
        )
        print("Connected to DB")
        break
    except psycopg2.OperationalError:
        print("DB not ready...")
        time.sleep(2)

if conn is None:
    exit(1)

cur = conn.cursor()

# ---------------- TASKS CRUD ----------------
@app.route("/tasks", methods=["GET"])
def get_tasks():
    cur.execute("SELECT * FROM tasks ORDER BY id ASC")
    tasks = cur.fetchall()
    return jsonify([{"id": t[0], "title": t[1]} for t in tasks])


@app.route("/tasks/<int:id>", methods=["GET"])
def get_task(id):
    cur.execute("SELECT * FROM tasks WHERE id=%s", (id,))
    task = cur.fetchone()
    if task:
        return jsonify({"id": task[0], "title": task[1]})
    return jsonify({"error": "Not found"}), 404


@app.route("/tasks", methods=["POST"])
def create_task():
    title = request.json.get("title")
    cur.execute("INSERT INTO tasks (title) VALUES (%s) RETURNING id", (title,))
    task_id = cur.fetchone()[0]
    conn.commit()
    return jsonify({"id": task_id, "title": title})


@app.route("/tasks/<int:id>", methods=["PUT"])
def update_task(id):
    title = request.json.get("title")
    cur.execute("UPDATE tasks SET title=%s WHERE id=%s", (title, id))
    conn.commit()
    return jsonify({"id": id, "title": title})


@app.route("/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):
    cur.execute("DELETE FROM tasks WHERE id=%s", (id,))
    conn.commit()
    return jsonify({"message": "deleted"})


# ---------------- SEND EMAIL WITH PROTOCOL SELECTION ----------------
@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.json

    to_email = data["to"]
    subject = data["subject"]
    message = data["message"]
    protocol = data["protocol"]   # smtp / imap / pop3

    # создаём письмо
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = "your_email@gmail.com"
    msg["To"] = to_email

    try:
        # ---------------- SMTP (реальная отправка) ----------------
        if protocol == "smtp":
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login("123@gmail.com", "123")
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
            server.quit()

            return jsonify({"status": "sent via SMTP"})

        # ---------------- IMAP (демо режим) ----------------
        elif protocol == "imap":
            # IMAP не используется для отправки — имитация
            return jsonify({
                "status": "IMAP selected",
                "note": "IMAP is used for reading emails, simulated sending only"
            })

        # ---------------- POP3 (демо режим) ----------------
        elif protocol == "pop3":
            return jsonify({
                "status": "POP3 selected",
                "note": "POP3 is used for retrieving emails, simulated sending only"
            })

        else:
            return jsonify({"error": "Invalid protocol"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
