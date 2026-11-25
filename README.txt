# EduSupport — Faculty IT Helpdesk System

EduSupport — это веб-портал IT-поддержки для студентов и преподавателей факультета. Система позволяет создавать заявки на решение технических проблем в аудиториях и на кафедре, отслеживать их статус и разграничивать права доступа с помощью встроенной системы ролей (Admin, Student, Teacher).

🚀 **Live System URL:** https://edusupport-x4x9.onrender.com
Test#  
Student: login:Student paassword:789456123
Admin: login:Darkhan password: 123
---

## 🏗 Архитектура системы
```text
[ Browser (Client) ] 
       │
       │ HTTPS / REST API
       ▼
[ Render Web Service ] ── (Python 3 / Flask / Gunicorn)
       │
       │ Connection Pooler (Port 6543 / PostgreSQL)
       ▼
[ Supabase Cloud Database ] ── (PostgreSQL: users, tickets)

EduSupport/
├── backend.py            # Основной сервер Flask (маршруты, API, auth, DB-обёртка)
├── requirements.txt      # Зависимости Python (Flask, Gunicorn, psycopg2-binary)
├── README.md             # Документация проекта
├── hub.html              # Личный кабинет (студент / преподаватель / админ)
├── login.html            # Форма входа
├── registration.html     # Форма регистрации
├── forget.html           # Восстановление пароля
├── index2.css            # Стили авторизации и регистрации
├── index3.js             # Логика авторизации
├── hub.css               # Стили личного кабинета
├── hub.js                # Логика работы с API заявок
└── 6266-190550868_medium.mp4 # Фоловое видео для экрана входа

Дата,Версия / Милстоун,Описание этапа
02 Ноября 2026,v0.1 — Idea & Spec,"Определение проблемы (IT Help Desk для Astana IT University), утверждение архитектуры"
08 Ноября 2026,v0.2 — Frontend Prototype,"Макеты страниц входа, регистрации и панели управления на HTML/CSS/JS"
14 Ноября 2026,v0.3 — Local Backend (SQLite),"Разработка backend на Flask, связь с DB Browser SQLite, создание таблиц users и tickets"
20 Ноября 2026,v0.4 — DB Migration,"Перенос структуры данных на облачный PostgreSQL (Supabase), разделение ролей (RBAC)"
23 Ноября 2026,v1.0 — Render Deployment,"Настройка переменных окружения, Gunicorn, HTTPS-деплой на Render и финальное QA-тестирование"

Маршрут,Метод,Описание
/,GET,Перенаправление на /hub или /login
/register,"GET, POST","Регистрация новых пользователей (student, teacher)"
/login,"GET, POST",Вход в систему
/hub,GET,Панель управления и список тикетов
/logout,POST,Выход из сессии
/forgot-password,"GET, POST",Форма восстановления доступа
/api/tickets,GET,"Список тикетов (все для admin, только свои для student/teacher)"
/api/tickets,POST,Создание новой заявки
/api/tickets/<id>/status,POST,Изменение статуса тикета (admin only)
/api/stats,GET,"Статистика заявок (всего, открыто, решено)"
/static/<filename>,GET,"Безопасная раздача CSS, JS и медиафайлов"
