import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, flash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'Final_project.db')

app = Flask(__name__)
app.secret_key = 'edusupport_secret_key_render'

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>EduSupport - Вход</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e1e1e; padding: 30px; border-radius: 10px; width: 320px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); text-align: center; }
        input, select, button { width: 100%; padding: 10px; margin: 8px 0; border-radius: 5px; border: 1px solid #333; box-sizing: border-box; }
        button { background: #007bff; color: white; font-weight: bold; cursor: pointer; border: none; }
        a { color: #00d2ff; text-decoration: none; font-size: 14px; }
        .flash { color: #ff4d4d; font-size: 14px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>EduSupport Login</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}{% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}{% endif %}
        {% endwith %}
        <form method="POST">
            <input type="text" name="login" placeholder="Логин" required>
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>
        <p><a href="/registration">Регистрация</a> | <a href="/forget">Забыли пароль?</a></p>
    </div>
</body>
</html>
'''

REGISTRATION_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>EduSupport - Регистрация</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e1e1e; padding: 30px; border-radius: 10px; width: 320px; text-align: center; }
        input, select, button { width: 100%; padding: 10px; margin: 8px 0; border-radius: 5px; border: 1px solid #333; box-sizing: border-box; }
        button { background: #28a745; color: white; font-weight: bold; cursor: pointer; border: none; }
        a { color: #00d2ff; text-decoration: none; font-size: 14px; }
        .flash { color: #ff4d4d; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Регистрация</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}{% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}{% endif %}
        {% endwith %}
        <form method="POST">
            <input type="text" name="login" placeholder="Логин" required>
            <input type="password" name="password" placeholder="Пароль" required>
            <select name="role">
                <option value="student">Студент</option>
                <option value="teacher">Преподаватель</option>
                <option value="admin">Администратор</option>
            </select>
            <button type="submit">Зарегистрироваться</button>
        </form>
        <p><a href="/login">Уже есть аккаунт? Войти</a></p>
    </div>
</body>
</html>
'''

HUB_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>EduSupport - Панель управления</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: #fff; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e1e1e; padding: 15px 20px; border-radius: 8px; }
        a.btn { background: #dc3545; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; }
        .content { margin-top: 30px; background: #1e1e1e; padding: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>EduSupport Hub</h2>
        <div>Пользователь: <b>{{ login }}</b> (Роль: {{ role }}) | <a href="/logout" class="btn">Выйти</a></div>
    </div>
    <div class="content">
        <h3>Добро пожаловать в систему IT Help Desk!</h3>
        <p>Вы успешно вошли в систему EduSupport.</p>
    </div>
</body>
</html>
'''

FORGET_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>EduSupport - Восстановление</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e1e1e; padding: 30px; border-radius: 10px; width: 320px; text-align: center; }
        a { color: #00d2ff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Восстановление пароля</h2>
        <p>Обратитесь к администратору системы.</p>
        <p><a href="/login">Назад к входу</a></p>
    </div>
</body>
</html>
'''

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
            return render_template_string(LOGIN_HTML)
            
    return render_template_string(LOGIN_HTML)

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
            return render_template_string(REGISTRATION_HTML)
            
    return render_template_string(REGISTRATION_HTML)

@app.route('/forget')
def forget():
    return render_template_string(FORGET_HTML)

@app.route('/hub')
def hub():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template_string(HUB_HTML, login=session.get('login'), role=session.get('role'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
