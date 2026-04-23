from sqlalchemy import String, Text, Enum, DateTime, SmallInteger, Integer, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from decimal import Decimal
from app.database import Base

import enum
import uuid
import datetime

#Модели базы данных PostgreSQL, сделанные в SqlAlchemy 2.
class Gender(str, enum.Enum):
    MALE="Мужской"
    FEMALE = "Женский"
    NON="Не указан"
class Users(Base):
    __tablename__ = "users"

    id:Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    first_name: Mapped[str] = mapped_column(String(100),nullable=False)

    last_name: Mapped[str] = mapped_column(String(100),nullable=False)

    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    birth_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    gender: Mapped[Gender] = mapped_column(Enum(Gender), default=Gender.NON, nullable=False)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    phone_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    admins: Mapped[Optional["Admins"]] = relationship(back_populates="user_admin", uselist=False)
    couriers: Mapped[Optional["Couriers"]] = relationship(back_populates="user_courier", uselist=False)
    orders: Mapped[List["Orders"]] = relationship(back_populates="user_orders")
    status_histories: Mapped[List["StatusHistory"]] = relationship(back_populates="user_history")

class Admins(Base):
    __tablename__="admins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))

    user_admin: Mapped["Users"] = relationship(back_populates="admins")

    departament_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departaments.id", onupdate="CASCADE", ondelete="CASCADE"))

    departaments: Mapped["Departaments"] = relationship(back_populates="admins_departament")

    access_level: Mapped[int] = mapped_column(SmallInteger)

class Departaments(Base):
    __tablename__ = "departaments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    code: Mapped[str] = mapped_column(String(3), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    admins_departament: Mapped[List["Admins"]] = relationship(back_populates="departaments")

class Vehicle_type(str, enum.Enum):
    FOOT = "Пеший"
    BICYCLE = "Велосипед"
    SCOOTER = "Самокат"
    CAR = "Автомобиль"
    TRUCK = "Грузовик"

class Couriers(Base):
    __tablename__ = "couriers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))

    user_courier: Mapped["Users"] = relationship(back_populates="couriers")

    vehicle_type: Mapped[Vehicle_type] = mapped_column(Enum(Vehicle_type), default=Vehicle_type.FOOT, nullable=False)

    vehicle_number: Mapped[str] = mapped_column(String(30), nullable=False)

    rating: Mapped[Decimal] = mapped_column(Numeric(3,2), default=5.00, nullable=False)

    balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=0.00, nullable=False)

    orders: Mapped[List["Orders"]] = relationship(back_populates="courier_orders")

class Order_status(str, enum.Enum):
    CREATED = "Создан"
    SEARCHING = "Поиск курьера"
    IN_DELIVERY = "В пути"
    DELIVERED = "Доставлен"
    CANCELLED = "Отменён"
class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))

    user_orders: Mapped["Users"] = relationship(back_populates="orders")

    courier_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("couriers.id", onupdate="CASCADE", ondelete="CASCADE",))

    courier_orders: Mapped["Couriers"] = relationship(back_populates="orders")

    status: Mapped[Order_status] = mapped_column(Enum(Order_status), default=Order_status.CREATED, nullable=False)

    price:Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)

    address_from: Mapped[str] = mapped_column(Text,nullable=False)

    address_to: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order_list: Mapped[List["OrderItems"]] = relationship(back_populates="order_items")

    order_status: Mapped[List["StatusHistory"]] = relationship(back_populates="order_history")

class Products(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    price: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)

    weight: Mapped[Decimal] = mapped_column(Numeric(10,3), nullable=True)

    order_list: Mapped[List["OrderItems"]] = relationship(back_populates="order_products")

class OrderItems(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", onupdate="CASCADE", ondelete="CASCADE"))

    order_items: Mapped["Orders"] = relationship(back_populates="order_list")

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", onupdate="CASCADE", ondelete="CASCADE"))

    order_products: Mapped["Products"] = relationship(back_populates="order_list")

    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

class StatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", onupdate="CASCADE", ondelete="CASCADE"))

    order_history: Mapped["Orders"] = relationship(back_populates="order_status")

    previous_status: Mapped[Optional[Order_status]] = mapped_column(Enum(Order_status), nullable=True)

    new_status: Mapped[Order_status] = mapped_column(Enum(Order_status), nullable=False)

    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    changed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))

    user_history: Mapped["Users"] = relationship(back_populates="status_histories")

    comment: Mapped[str] = mapped_column(Text, nullable=True)