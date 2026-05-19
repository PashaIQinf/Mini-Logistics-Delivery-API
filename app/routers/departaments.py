from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import  get_db
from app import  schemas, crud

router = APIRouter(prefix="/departaments", tags=["Departaments"])


@router.get("/", response_model=List[schemas.DepartamentOut] )
async def read_departaments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    departaments = await crud.get_departaments(db, skip=skip, limit=limit)
    return departaments
@router.post("/", response_model=schemas.DepartamentOut )
async def create_departament(departament: schemas.DepartamentCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_departament(db=db,departament=departament)