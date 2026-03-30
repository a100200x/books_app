from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.configurations.security import (
    Token,
    UserCredentials,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from src.services import SellerService

auth_router = APIRouter(prefix="/token", tags=["auth"])


@auth_router.post("/", response_model=Token)
async def login_for_access_token(
    credentials: UserCredentials,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получение JWT токена по email и паролю.
    
    Принимает JSON:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    seller_service = SellerService(session)
    
    # Аутентифицируем продавца
    seller = await seller_service.authenticate_seller(credentials.email, credentials.password)
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(seller.id), "email": seller.email},
        expires_delta=access_token_expires,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}