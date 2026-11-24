# EduSupport — Flask + SQLite (регистрация, вход, IT helpdesk)

## 1. Установка
    py -m venv venv
    venv\Scripts\activate          (macOS/Linux: source venv/bin/activate)
    pip install -r requirements.txt

## 2. Запуск
    python backend.py
Открыть http://127.0.0.1:5000

## 3. Структура проекта
    backend.py          Flask-сервер (все маршруты + работа с SQLite)
    Final_project.db    база данных SQLite (таблицы users и tickets)
    templates/          HTML (Jinja): login, registration, forget, hub
    static/             index2.css, index3.js (вход/регистрация),
                        hub.css, hub.js (кабинет), фоновое видео

## 4. Как это работает
Маршруты:
    GET  /                       -> редирект на /hub или /login
    GET/POST /register           -> добавляет пользователя в таблицу users
    GET/POST /login              -> проверяет хэш пароля, создаёт session
    GET  /hub                    -> кабинет (только после входа)
    POST /logout                 -> очищает session
    GET/POST /forgot-password    -> заглушка восстановления (письма не отправляются)
    GET  /api/tickets            -> заявки из БД (admin видит все, остальные — свои)
    POST /api/tickets            -> создать заявку (запись в таблицу tickets)
    POST /api/tickets/<id>/status-> сменить статус (только admin)
    GET  /api/stats              -> счётчики для главной страницы

База данных:
    users   (id, login, password, role, full_name)
    tickets (id, title, description, status, user_id,
             requester_name, group_name, category, created_at)
Недостающие колонки добавляются автоматически при первом запуске (init_db).

Безопасность:
    - пароли хранятся как хэш Werkzeug; старые пароли «обычным текстом»
      автоматически превращаются в хэш при первом входе
    - SQL-запросы параметризованы (защита от SQL-инъекций)
    - CSRF-токен во всех POST-запросах
    - пользовательский текст экранируется при выводе (защита от XSS)

Тестовые аккаунты из БД (роль admin, видят все заявки и меняют статусы):
    Darkhan1 / z123456!
    Olzhas   / x123456!
Новые пользователи через /register получают роль student или teacher.

Для реального сервера: задать длинный SECRET_KEY и отключить debug
(переменная окружения FLASK_DEBUG=0).
