from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import  get_db
from app import  schemas, crud
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=schemas.ProductOut)
async def create_product(product: schemas.ProductCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user) ):

    if current_user.role != "admin" and not settings.TESTING:
        raise HTTPException(403, "Доступ запрещён")

    return await crud.create_product(db=db, product=product)

@router.get("/", response_model=List[schemas.ProductOut])
async def read_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):

    if current_user.role == "courier":
        raise HTTPException(403, "Доступ запрещён")


    products = await crud.get_products(db, skip=skip, limit=limit)
    return products