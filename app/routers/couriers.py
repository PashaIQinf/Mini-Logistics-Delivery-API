from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app import schemas, crud
from app.dependencies import get_current_user
import uuid

router = APIRouter(prefix="/couriers", tags=["Couriers"])

@router.get("/", response_model=List[schemas.CourierOut])
async def list_couriers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):

    if current_user.role != "admin":
        raise HTTPException(403, "Доступ запрещён")

    return await crud.get_couriers(db, skip, limit)


@router.get("/me/orders", response_model=List[schemas.OrderOut])
async def my_active_orders(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user) ):
    # Получить мои активные заказы (статус: in_delivery)
    if current_user.role != "courier":
        raise HTTPException(403, "Только для курьеров")

    courier = await crud.get_courier_by_user_id(db, current_user.id)

    return await crud.get_courier_active_orders(db, courier)


@router.post("/orders/{order_id}/accept", response_model=schemas.OrderOut)
async def accept_order( order_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Взять заказ в работу.
    Требования:
    - Статус заказа: SEARCHING
    - Курьер ещё не назначен (courier_id is None)
    После: статус → IN_DELIVERY, courier_id = текущий курьер
    """
    if current_user.role != "courier":
        raise HTTPException(403, "Только для курьеров")

    courier = await crud.get_courier_by_user_id(db, current_user.id)

    return await crud.accept_order_by_courier(db, order_id, courier)