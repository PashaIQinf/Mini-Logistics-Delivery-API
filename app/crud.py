from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
import uuid
import bcrypt
from decimal import Decimal
from typing import Optional, List
from  fastapi import  HTTPException, status
from sqlalchemy.orm import joinedload, selectinload

from . import models, schemas
from app.logic.order_fsm import can_transition

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


async def get_products_with_filters(db: AsyncSession, order: schemas.OrderOut, skip: int, limit: int) -> List[models.Products]:
    # Создаем быстрый словарь {product_id: item(объект)} из уже загруженных данных
    items_map = {item.product_id: item for item in order.items}
    product_ids = list(items_map.keys())

    query = select(models.Products).where(models.Products.id.in_(product_ids)).offset(skip).limit(limit)

    query = await db.execute(query)
    products = query.scalars().all()

    for product in products:
        corresponding_item = items_map.get(product.id)
        if corresponding_item:
            product.quantity = corresponding_item.quantity
            product.price_at_purchase = corresponding_item.price_at_purchase

    return products


# --- РАБОТА С ЗАКАЗАМИ ---

async def create_order(db: AsyncSession, order_data: schemas.OrderCreate, user_id: uuid.UUID) -> models.Orders:
    # 1. Проверяем и получаем все товары из БД
    product_ids = [item.product_id for item in order_data.items]
    products_result = await db.execute(select(models.Products).where(models.Products.id.in_(product_ids)))
    products = {str(product.id): product for product in products_result.scalars().all()}

    # Проверяем, все ли товары найдены
    missing_products = [str(pid) for pid in product_ids if str(pid) not in products]
    if missing_products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товары не найдены: {', '.join(missing_products)}"
        )
    # 2. Создаем объект заказа
    new_order = models.Orders(
        user_id=user_id,
        address_from=order_data.address_from,
        address_to=order_data.address_to,
        price=Decimal("0.00"),
        status=models.Order_status.CREATED
    )
    db.add(new_order)
    await db.flush()  # Получаем ID заказа, не закрывая транзакцию

    # 3. Добавляем товары в заказ
    total_price = Decimal("0.00")

    for item in order_data.items:
        product = products[str(item.product_id)]
        # Получаем актуальную цену товара
        price_at_purchase = product.price

        # Сумма для этой позиции
        item_total = price_at_purchase * item.quantity
        total_price += item_total

        db_item = models.OrderItems(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=price_at_purchase
        )
        db.add(db_item)

    # 4. Обновляем общую сумму заказа
    new_order.price = total_price.quantize(Decimal("0.01"))  # округление до копеек

    # 5. Фиксируем всё в БД
    await db.commit()
    await db.refresh(new_order)
    return new_order

#Фильтрация заказов по роли и статусу
async def get_orders_with_filters( db: AsyncSession, current_user, skip: int, limit: int,  status: Optional[models.Order_status] = None) -> List[models.Orders]:

    query = select(models.Orders)

    # Фильтрация по роли
    if current_user.role == "courier":
        query = query.where(models.Orders.courier_id == current_user.id)
    elif current_user.role == "user":
        query = query.where(models.Orders.user_id == current_user.id)
    # admin видит всё — без фильтра

    # Фильтрация по статусу
    if status:
        query = query.where(models.Orders.status == status)

    query = query.options(selectinload(models.Orders.order_list)).offset(skip).limit(limit).order_by(models.Orders.created_at.desc())
    orders   = await db.execute(query)
    result = orders.scalars().all()

    for order in result:
        order.items = order.order_list

    return result

async def get_order_by_id(db: AsyncSession, order_id: uuid.UUID) -> Optional[models.Orders]:
    #Получить заказ по ID
    order = await db.get(models.Orders, order_id, options=[joinedload(models.Orders.order_list)])

    if order:
        order.items = order.order_list

    return order

# --- РАБОТА С СТАТУСОМ, ИСТОРИЕЙ И ПРОДУКТАМИ ЗАКАЗА ---

async def update_order_status(db: AsyncSession, order_id: uuid.UUID, status_update: schemas.OrderStatusUpdate, current_user) -> models.Orders:

    order = await db.get(models.Orders, order_id)
    if not order:
        raise HTTPException(404, "Заказ не найден")

    # 1. Валидация перехода (бизнес-логика)
    if not can_transition(order.status, status_update.new_status):
        raise HTTPException(
            400,
            f"Невозможно перейти из '{order.status.value}' в '{status_update.new_status.value}'"
        )

    # 2. Проверка прав на изменение статуса
    if current_user.role == "courier" and order.courier_id != current_user.id:
        raise HTTPException(403, "Вы не можете менять статус этого заказа")

    # 3. Обновляем статус
    old_status = order.status
    order.status = status_update.new_status

    # 4. Записываем историю
    history = models.StatusHistory(
        order_id=order.id,
        previous_status=old_status,
        new_status=status_update.new_status,
        changed_by=current_user.id,
        comment=status_update.comment
    )
    db.add(history)

    await db.commit()
    await db.refresh(order)
    return order

async def get_status_history_by_id(db: AsyncSession, skip: int, limit: int, order_id: uuid.UUID) ->   List[models.StatusHistory]:
    query = select(models.StatusHistory).where(models.StatusHistory.order_id == order_id)

    query = query.offset(skip).limit(limit).order_by(models.StatusHistory.changed_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


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
