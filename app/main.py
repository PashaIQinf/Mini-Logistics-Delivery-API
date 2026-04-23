from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Импортируем всё наше "лего"
from .database import engine, Base, async_session_maker
from . import models, schemas, crud


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

app = FastAPI(title="Mini-Logistics Vladivostok API", lifespan=lifespan)


# --- ЗАВИСИМОСТЬ (Dependency Injection) ---
# Эта функция будет создавать сессию для каждого запроса и закрывать её после
async def get_db():
    async with async_session_maker() as session:
        yield session


# --- ПЕРВЫЕ ЭНДПОИНТЫ (Маршруты) ---

@app.post("/users/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Проверяем, нет ли уже юзера с таким email
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    # 2. Создаем нового юзера
    return await crud.create_user(db=db, user=user)


@app.get("/products/", response_model=List[schemas.ProductOut] , tags=["Products"])
async def read_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    products = await crud.get_products(db, skip=skip, limit=limit)
    return products


@app.post("/products/", response_model=schemas.ProductOut, tags=["Products"])
async def create_product(product: schemas.ProductCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_product(db=db, product=product)
