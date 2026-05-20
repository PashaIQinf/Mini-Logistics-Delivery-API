from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import schemas, crud, utils
from app.config import settings
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserWithRoleOut, status_code=201)
async def register(user_data: schemas.UserCreateWithRole, db: AsyncSession = Depends(get_db)):
    # Проверка на дубликаты
    if await crud.get_user_by_email(db, user_data.email):
        raise HTTPException(400, "Email уже зарегистрирован")

    try:
        user = await crud.create_user_with_role(db, user_data)
        user.role = user_data.role
        return user
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        await db.rollback()
        raise HTTPException(500, "Ошибка при регистрации")


@router.post("/login", response_model=schemas.Token)
async def login(form_data: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, form_data.email)
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Неверный email или пароль")

    role = await crud.get_user_role(db, user.id)
    token = utils.create_access_token(
        data={"sub": str(user.id), "role": role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer", "role": role}