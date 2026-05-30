import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from .models import Gender, Vehicle_type, Order_status

# --- БАЗОВЫЕ СХЕМЫ (Shared) ---

class UserBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    middle_name: Optional[str] = None
    birth_date: datetime
    gender: Gender = Gender.NON
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    email: EmailStr

class ProductBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    weight: Optional[Decimal] = Field(None, ge=0)
class DepartamentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=3, pattern=r"\b[A-ZА-ЯЁ]+\b")
    is_active: bool

# --- СХЕМЫ ДЛЯ СОЗДАНИЯ (Create) ---


class CourierCreate(BaseModel):
    user_id: uuid.UUID # Сначала создаем User, потом берем ID для создания Courier
    vehicle_type: Vehicle_type = Vehicle_type.FOOT
    vehicle_number: str = Field(..., max_length=30)

class ProductCreate(ProductBase):
    price: Decimal = Field(..., gt=0)

class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(..., ge=1)

class OrderCreate(BaseModel):
    address_from: str = Field(...,  min_length=5, max_length=255)
    address_to: str = Field(...,  min_length=5, max_length=255)
    items: List[OrderItemCreate] = Field(..., min_length=1)

class DepartamentCreate(DepartamentBase):
    pass

class UserCreateWithRole(UserBase):
    #Регистрация с выбором роли
    password: str = Field(..., min_length=8)
    role: Literal["admin", "courier", "user"]

    # Поля для админа (опциональные)
    department_id: Optional[uuid.UUID] = None
    access_level: Optional[int] = Field(default=1, ge=1, le=5)

    # Поля для курьера (опциональные)
    vehicle_type: Optional[Vehicle_type] = None
    vehicle_number: Optional[str] = Field(None, max_length=30)

# --- СХЕМЫ ДЛЯ ВЫВОДА (Out / Read) ---

class UserOut(UserBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class CourierOut(CourierCreate):
    id: uuid.UUID
    vehicle_type: Vehicle_type
    vehicle_number: str
    rating: Decimal
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)

class ProductOut(ProductBase):
    id: uuid.UUID
    price: Decimal = Field(..., gt=0)

    model_config = ConfigDict(from_attributes=True)


class OrderItemOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    price_at_purchase: Decimal

    model_config = ConfigDict(from_attributes=True)

class OrderProductOut(ProductBase):
    id: uuid.UUID
    quantity: int
    price_at_purchase: Decimal

    model_config = ConfigDict(from_attributes=True)

class OrderOut(BaseModel):
    id: uuid.UUID
    status: Order_status
    price: Decimal
    address_from: str
    address_to: str
    created_at: datetime
    user_id: uuid.UUID
    courier_id: Optional[uuid.UUID] = None
    items: List[OrderItemOut] = []

    model_config = ConfigDict(from_attributes=True)
class DepartamentOut(DepartamentBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class UserWithRoleOut(UserOut):
    #Ответ с информацией о роли
    role: Optional[str] = None

# Схема для обновления статуса заказа.
class OrderStatusUpdate(BaseModel):
    new_status: Order_status
    comment: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True, extra="forbid"  )

# История изменения статуса заказ
class StatusHistoryOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    previous_status: Order_status
    new_status: Order_status
    changed_by: Optional[uuid.UUID] = None
    changed_at: datetime
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Расширенный ответ заказа с историей статусов
class OrderOutWithHistory(OrderOut):
    status_history: List[StatusHistoryOut] = []

    model_config = ConfigDict(from_attributes=True)

# --- СХЕМЫ ДЛЯ АВТОРИЗАЦИИ ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Optional[str] = None




