from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ------------------ DATABASE INIT ------------------
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            institution TEXT,
            password TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            filename TEXT,
            user_id INTEGER,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ------------------ HOME (SEARCH) ------------------
@app.route('/', methods=['GET', 'POST'])
def search():
    papers = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM papers WHERE title LIKE ? AND status='Approved'", ('%' + keyword + '%',))
        papers = cur.fetchall()
        conn.close()
    return render_template('search.html', papers=papers)

# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        institution = request.form['institution']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO users(email, institution, password) VALUES (?, ?, ?)",
                    (email, institution, password))
        conn.commit()
        conn.close()

        return redirect('/login')
    return render_template('register.html')

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/upload')
        else:
            return "Invalid Credentials"

    return render_template('login.html')

# ------------------ UPLOAD ------------------
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        file = request.files['file']
        filename = secure_filename(file.filename)

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO papers(title, filename, user_id, status) VALUES (?, ?, ?, 'Pending')",
                    (title, filename, session['user_id']))
        conn.commit()
        conn.close()

        return "Uploaded Successfully. Waiting for Admin Approval."

    return render_template('upload.html')

# ------------------ SERVE UPLOADED FILE ------------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ------------------ ADMIN ------------------
@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM papers WHERE status='Pending'")
    papers = cur.fetchall()
    conn.close()
    return render_template('admin.html', papers=papers)

@app.route('/approve/<int:id>')
def approve(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("UPDATE papers SET status='Approved' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)