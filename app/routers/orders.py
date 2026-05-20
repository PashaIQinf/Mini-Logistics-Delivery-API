from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app import schemas, crud
from app.dependencies import get_current_user, require_role
import uuid

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=schemas.OrderOut, status_code=201)
async def create_order(order: schemas.OrderCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await crud.create_order(db, order, current_user.id)

@router.get("/", response_model=List[schemas.OrderOut])
async def list_orders(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    # Здесь добавить фильтрацию по роли
    return []  # реализовать

@router.get("/{order_id}", response_model=schemas.OrderOut)
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    # реализовать
    pass