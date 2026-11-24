import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'Final_project.db')

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

app.secret_key = 'edusupport_secret_key_render'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE login = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (login, password, role) VALUES ('admin', 'admin123', 'admin')")
        
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('hub'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login')
        password_input = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login = ? AND password = ?', 
                            (login_input, password_input)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['login'] = user['login']
            session['role'] = user['role']
            return redirect(url_for('hub'))
        else:
            flash('Неверный логин или пароль')
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        login_input = request.form.get('login')
        password_input = request.form.get('password')
        role_input = request.form.get('role', 'student')
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)',
                         (login_input, password_input, role_input))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Пользователь с таким логином уже существует')
            return render_template('registration.html')
            
    return render_template('registration.html')

@app.route('/forget', methods=['GET', 'POST'])
def forget():
    return render_template('forget.html')

@app.route('/hub')
def hub():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM tickets').fetchall()
    conn.close()
    
    return render_template('hub.html', login=session.get('login'), role=session.get('role'), tickets=tickets)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
