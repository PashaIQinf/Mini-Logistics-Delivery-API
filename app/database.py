from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# 1. Создаем асинхронный движок (Engine)
if settings.TESTING and settings.TEST_DATABASE_URL:
    DATABASE_URL = settings.TEST_DATABASE_URL
else:
    DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(settings.DATABASE_URL, echo=True) # echo=True покажет SQL-запросы в терминале


# 2. Фабрика сессий (будем использовать её в FastAPI для каждого запроса)
async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession,  expire_on_commit=False)

# 3. Базовый класс для моделей (в стиле 2.0)
class Base(DeclarativeBase):
    pass

# 5. Эта функция будет создавать сессию для каждого запроса и закрывать её после
async def get_db():
    async with async_session_maker() as session:
        yield session 