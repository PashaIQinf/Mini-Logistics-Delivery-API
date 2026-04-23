from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import bcrypt

from . import models, schemas

def get_password_hash(password: str) -> str:
    # Превращаем пароль в байты, генерируем соль и хэшируем
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

# --- РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ---

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.Users).where(models.Users.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: schemas.UserCreate):
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

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Products).offset(skip).limit(limit))
    return result.scalars().all()


async def create_product(db: AsyncSession, product: schemas.ProductCreate):
    data = product.model_dump()
    db_product = models.Products(**data)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


async def create_order(db: AsyncSession, order_data: schemas.OrderCreate, user_id: uuid.UUID):
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
