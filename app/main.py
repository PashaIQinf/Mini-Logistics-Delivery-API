from contextlib import asynccontextmanager
from fastapi import FastAPI

# Импортируем всё наше "лего"
from .database import engine, Base

from app.routers import products, departaments, auth, orders, couriers


# 1. Создаем Lifespan функцию
@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):

    print(f"🚀 Запуск приложения: {fastapi_app.title}")
    # Код здесь выполнится ПРИ СТАРТЕ
    async with engine.begin() as conn:
        # Создаем таблицы, если их нет
        await conn.run_sync(Base.metadata.create_all)

    yield

    print(f"🛑 Остановка приложения: {fastapi_app.title}")
    # Код здесь выполнится ПРИ ОСТАНОВКЕ (например, можно закрыть соединения)
    await engine.dispose()

app = FastAPI(title="Mini-Logistics Delivery API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(departaments.router)
app.include_router(orders.router)
app.include_router(couriers.router)

@app.get("/", tags=["Root/Health"])
async def root():
    return {"message": "Система логистики работает, роутеры подключены!"}


