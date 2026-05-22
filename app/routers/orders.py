from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app import schemas, crud, models
from app.dependencies import get_current_user
import uuid

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(order: schemas.OrderCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await crud.create_order(db, order, current_user.id)

@router.get("/", response_model=List[schemas.OrderOut])
async def list_orders(skip: int = 0, limit: int = 100, status: Optional[models.Order_status] = None, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """
       - Админ видит ВСЕ заказы
       - Курьер видит ТОЛЬКО свои (courier_id == current_user.id)
       - Обычный пользователь видит только свои заказы (user_id)
    """
    return await crud.get_orders_with_filters(db, current_user, skip, limit, status)

@router.get("/{order_id}", response_model=schemas.OrderOut)
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    order = await crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(404, "Заказ не найден")

    # Проверка прав: пользователь видит только свои заказы
    if current_user.role == "user" and order.user_id != current_user.id:
        raise HTTPException(403, "Доступ запрещён")
    if current_user.role == "courier" and order.courier_id != current_user.id and order.user_id != current_user.id:
        raise HTTPException(403, "Доступ запрещён")

    return order

@router.patch("/{order_id}/status", response_model=schemas.OrderOut)
async def update_order_status(order_id: uuid.UUID, status_update: schemas.OrderStatusUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await crud.update_order_status(db, order_id, status_update, current_user)