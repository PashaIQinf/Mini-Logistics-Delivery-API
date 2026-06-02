from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import  get_db
from app import  schemas, crud
from app.dependencies import get_current_user

router = APIRouter(prefix="/departaments", tags=["Departaments"])


@router.get("/", response_model=List[schemas.DepartamentOut] )
async def read_departaments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):

    if current_user.role != "admin":
        raise HTTPException(403, "Доступ запрещён")

    departaments = await crud.get_departaments(db, skip=skip, limit=limit)
    return departaments
@router.post("/", response_model=schemas.DepartamentOut )
async def create_departament(departament: schemas.DepartamentCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):

    if current_user.role != "admin":
        raise HTTPException(403, "Доступ запрещён")

    return await crud.create_departament(db=db,departament=departament)