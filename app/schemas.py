import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
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
    price: Decimal = Field(..., gt=0)
    weight: Optional[Decimal] = Field(None, ge=0)

# --- СХЕМЫ ДЛЯ СОЗДАНИЯ (Create) ---

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class CourierCreate(BaseModel):
    user_id: uuid.UUID # Сначала создаем User, потом берем ID для создания Courier
    vehicle_type: Vehicle_type = Vehicle_type.FOOT
    vehicle_number: str = Field(..., max_length=30)

class ProductCreate(ProductBase):
    pass

class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    address_from: str
    address_to: str
    price: Decimal = Field(..., gt=0)
    items: List[OrderItemCreate]

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

    model_config = ConfigDict(from_attributes=True)

class OrderOut(BaseModel):
    id: uuid.UUID
    status: Order_status
    price: Decimal
    address_from: str
    address_to: str
    created_at: datetime
    user_id: uuid.UUID
    courier_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)
