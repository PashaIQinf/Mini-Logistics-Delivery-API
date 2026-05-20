from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
import uuid
import bcrypt
from decimal import Decimal
from typing import Optional, List

from . import models, schemas

def get_password_hash(password: str) -> str:
    # Превращаем пароль в байты, генерируем соль и хэшируем
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

# --- РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ---

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.Users]:
    result = await db.execute(select(models.Users).where(models.Users.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.Users:
    # 1. Хэшируем пароль
    hashed_pass = get_password_hash(user.password)

    # 2. Создаем модель SQLAlchemy (превращаем данные из схемы в данные для базы)
    db_user = models.Users(
        email=user.email,
        hashed_password=hashed_pass,
        first_name=user.first_name,
        last_name=user.last_name,
        middle_name=user.middle_name,
        phone_number=user.phone_number,
        gender=user.gender,
        birth_date=user.birth_date
    )

    # 3. Добавляем в сессию и сохраняем
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)  # Чтобы получить ID, созданный базой
    return db_user


# --- РАБОТА С ТОВАРАМИ ---

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Products]:
    result = await db.execute(select(models.Products).offset(skip).limit(limit))
    return result.scalars().all()


async def create_product(db: AsyncSession, product: schemas.ProductCreate) -> models.Products:
    data = product.model_dump()
    db_product = models.Products(**data)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


async def create_order(db: AsyncSession, order_data: schemas.OrderCreate, user_id: uuid.UUID) -> models.Orders:
    # 1. Создаем объект заказа
    new_order = models.Orders(
        user_id=user_id,
        address_from=order_data.address_from,
        address_to=order_data.address_to,
        price=order_data.price,
        status=models.Order_status.CREATED
    )
    db.add(new_order)
    await db.flush()  # Получаем ID заказа, не закрывая транзакцию

    # 2. Добавляем товары в заказ
    for item in order_data.items:
        # Получаем актуальную цену товара из базы
        res = await db.execute(select(models.Products).where(models.Products.id == item.product_id))
        product = res.scalar_one()

        db_item = models.OrderItems(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=product.price  # Фиксируем цену на момент покупки!
        )
        db.add(db_item)

    await db.commit()
    await db.refresh(new_order)
    return new_order

# --- РАБОТА С ДЕПАРТАМЕНТАМИ    ---
async def create_departament(db:AsyncSession, departament: schemas.DepartamentCreate) -> models.Departaments:
    data = departament.model_dump()
    db_departament = models.Departaments(**data)
    db.add(db_departament)
    await db.commit()
    await db.refresh(db_departament)
    return db_departament

async def get_departaments(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Departaments]:
    result = await db.execute(select(models.Departaments).offset(skip).limit(limit))
    return result.scalars().all()


# --- РАБОТА C АВТОРИЗАЦИЕЙ И РОЛЯМИ ---

async def create_user_with_role(db: AsyncSession, user_data: schemas.UserCreateWithRole) -> models.Users:
    # 1. Создаём базового пользователя
    hashed_pass = get_password_hash(user_data.password)

    db_user = models.Users(
        email=user_data.email,
        hashed_password=hashed_pass,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        middle_name=user_data.middle_name,
        phone_number=user_data.phone_number,
        gender=user_data.gender,
        birth_date=user_data.birth_date
    )

    db.add(db_user)
    await db.flush()  # Получаем user.id до commit

    # 2. Создаём профиль роли
    if user_data.role == "admin":
        db_admin = models.Admins(
            user_id=db_user.id,
            departament_id=user_data.department_id,
            access_level=user_data.access_level
        )
        db.add(db_admin)

    elif user_data.role == "courier":
        if not user_data.vehicle_type or not user_data.vehicle_number:
            raise ValueError("Для курьера обязательны vehicle_type и vehicle_number")

        db_courier = models.Couriers(
            user_id=db_user.id,
            vehicle_type=user_data.vehicle_type,
            vehicle_number=user_data.vehicle_number,
            rating=Decimal("5.00"),
            balance=Decimal("0.00")
        )
        db.add(db_courier)

    # 3. Фиксируем всё в БД
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_role(db: AsyncSession, user_id: uuid.UUID) -> Optional[str]:
    # Определяет роль пользователя по ID
    user = await db.scalar(select(models.Users.id).where(models.Users.id == user_id))
    if not user:
        return None

    # Проверяем наличие связанных профилей
    admin_result = await db.scalar(select(models.Admins.id).where(models.Admins.user_id == user_id))
    if admin_result:  # связь Users.admins → Admins
        return "admin"

    courier_result = await db.scalar(select(models.Couriers.id).where(models.Couriers.user_id == user_id))
    if courier_result:  # связь Users.couriers → Couriers
        return "courier"
    return "user"


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[models.Users]:
    #Получить пользователя по ID
    return await db.get(models.Users, user_id)
