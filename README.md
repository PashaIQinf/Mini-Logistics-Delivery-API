## Mini-Logistics-Delivery-API
*REST API для службы доставки (в разработке)*

**Стек:** FastAPI • SQLAlchemy (Async) • PostgreSQL • Alembic • Docker • Pydantic v2

**Реализовано:**
1. Архитектура приложения (Router/Service/DAO слои)
2. Асинхронное подключение к PostgreSQL
3. Система миграций БД через Alembic
4. JWT-аутентификация и хэширование паролей (bcrypt)
5. Валидация данных через Pydantic 2
6. Docker-compose для быстрого деплоя базы данных

*Цель проекта:* отработка паттернов асинхронной архитектуры и лучших практик FastAPI.
# Быстрый старт
1) "git clone https://github.com/PashaIQinf/Mini-Logistics-Delivery-API.git"
2) перейти в папку проекта и сделать "docker-compose up --build" для базы данных
3) "uvicorn app.main:app --reload" для запуска Mini-Logistics-Delivery-API

**API доступно на http://localhost:8000, docs: http://localhost:8000/docs**
