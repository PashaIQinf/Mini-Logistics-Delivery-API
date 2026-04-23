from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# 1. URL подключения (для Docker Postgres и асинхронности используем драйвер asyncpg)
DATABASE_URL = "postgresql+asyncpg://admin:pass2005%40P@localhost:5432/mini_logistics"

# 2. Создаем асинхронный движок (Engine)
engine = create_async_engine(DATABASE_URL, echo=True) # echo=True покажет SQL-запросы в терминале

# 3. Фабрика сессий (будем использовать её в FastAPI для каждого запроса)
async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession,  expire_on_commit=False)

# 4. Базовый класс для моделей (в стиле 2.0)
class Base(DeclarativeBase):
    pass