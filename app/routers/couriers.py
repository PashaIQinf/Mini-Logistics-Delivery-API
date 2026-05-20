from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app import schemas

router = APIRouter(prefix="/couriers", tags=["Couriers"])

@router.get("/", response_model=List[schemas.CourierOut])
async def list_couriers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # реализовать в crud.py
    return []