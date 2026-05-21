from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud
from app.config import settings
import uuid

# Используется HTTPBearer вместо OAuth2PasswordBearer,
# чтобы сохранить JSON-формат для /auth/login (удобнее для фронтенда и тестов).
# Для сервера с требованиями OAuth2 можно заменить на OAuth2PasswordBearer.
security = HTTPBearer()


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    token = token.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await crud.get_user_by_id(db, uuid.UUID(user_id))
    if user is None:
        raise credentials_exception

    # Добавляем роль к объекту
    user.role = await crud.get_user_role(db, user.id)
    return user


def require_role(*roles: str):
    #Проверка роли: @require_role("admin", "courier")

    async def checker(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется роль: {', '.join(roles)}"
            )
        return current_user

    return checker