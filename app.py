import base64
import os
import sqlite3
from openai import OpenAI
from flask import Flask, render_template, request, jsonify, redirect, session
from flask_bcrypt import Bcrypt
import smile_detector

app = Flask(__name__)
app.secret_key = "mental_health_secret_key"
bcrypt = Bcrypt(app)

# ==============================
# OpenRouter Configuration
# ==============================

openai_client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

# ==============================
# DATABASE SETUP
# ==============================

def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    
    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    
    # Journal table (linked to user)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            note TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

create_tables()

# ==============================
# AUTH ROUTES
# ==============================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                         (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            return "Username already exists!"

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?",
                            (username,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/')
        else:
            return "Invalid Credentials!"

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ==============================
# MAIN PAGES (LOGIN REQUIRED)
# ==============================

@app.route('/')
def home():
    return render_template('index.html', username=session.get('username'))

@app.route('/chatbot')
def chatbot():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('chatbot.html')


@app.route('/journal')
def journal():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('journal.html')


@app.route('/smile')
def smile():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('smile.html')


@app.route('/result')
def result():
    score = request.args.get("score", 0)
    return render_template("result.html", score=score)


# ==============================
# JOURNAL SAVE (PER USER)
# ==============================

@app.route('/save_journal', methods=['POST'])
def save_journal():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    note = request.json['note']

    conn = get_db()
    conn.execute("INSERT INTO journals (user_id, note) VALUES (?, ?)",
                 (session['user_id'], note))
    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})


def get_latest_journal(user_id):
    conn = get_db()
    journal = conn.execute("""
        SELECT note FROM journals 
        WHERE user_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (user_id,)).fetchone()
    conn.close()

    if journal:
        return journal['note']
    return ""


# ==============================
# CHAT ROUTE (CONNECTED TO JOURNAL)
# ==============================

@app.route('/chat', methods=['POST'])
def chat():

    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    user_message = data['message']

    journal_data = get_latest_journal(session['user_id'])

    system_prompt = "You are a helpful, caring mental health assistant."

    if journal_data:
        system_prompt += " The user's recent journal entry: " + journal_data

    response = openai_client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=200
    )

    answer = response.choices[0].message.content

    return jsonify({"response": answer})


# ==============================
# IMAGE SAVE (SMILE SCORE)
# ==============================

@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.json['image']

    image_data = data.split(",")[1]

    with open("static/result.png", "wb") as f:
        f.write(base64.b64decode(image_data))

    return jsonify({"status": "saved"})


# ==============================
# RUN
# ==============================

if __name__ == '__main__':
    app.run(debug=True)