# EduSupport — Flask + SQLite

## Структура проекта

```text
EduSupport/
├── backend.py
├── Final_project.db
├── requirements.txt
├── README.txt
└── frontend/
    ├── login.html
    ├── registration.html
    ├── forget.html
    ├── hub.html
    ├── index2.css
    ├── index3.js
    ├── hub.css
    ├── hub.js
    └── 6266-190550868_medium.mp4
```

Все HTML, CSS, JavaScript и медиафайлы находятся вместе в `frontend/`.
Папок `templates/` и `static/` нет. Flask использует одну и ту же папку
`frontend/` для загрузки Jinja HTML и выдачи ресурсов браузеру.

## Установка и запуск локально

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python backend.py
```

Откройте http://127.0.0.1:5000

## Render

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn backend:app`
- Runtime: Python 3

Задайте в Environment Variables переменную `SECRET_KEY` со случайным длинным значением.
Для постоянного хранения SQLite-файла на Render настройте Persistent Disk и разместите
базу на нём либо используйте PostgreSQL. Без постоянного хранилища SQLite может
сбрасываться при пересоздании экземпляра.

## Основные маршруты

- `/` — перенаправление на кабинет или вход
- `/register` — регистрация
- `/login` — вход
- `/hub` — личный кабинет
- `/logout` — выход
- `/forgot-password` — демонстрационная форма восстановления (письма не отправляются)
- `/api/tickets` — просмотр и создание заявок
- `/api/tickets/<id>/status` — изменение статуса администратором
- `/api/stats` — статистика заявок

Ресурсы frontend отдаются по URL `/frontend/<имя-файла>`.
