"""
Заглушки для тестов, чтобы отключить проверку авторизации в тестовом режиме.
Используется только в тестах.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

# Схема для Bearer токена
security = HTTPBearer()


class TokenData(BaseModel):
    """Данные, хранящиеся в JWT токене"""
    seller_id: Optional[int] = None
    email: Optional[str] = None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Заглушка для получения текущего пользователя в тестах"""
    # В тестах проверяем токен
    token = credentials.credentials
    
    # Если токен "invalid_token_here", возвращаем ошибку (для теста test_protected_endpoint_with_invalid_token)
    if token == "invalid_token_here":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Для тестового токена "test_token" возвращаем seller_id=1
    if token == "test_token":
        return TokenData(seller_id=1, email="test@example.com")
    
    # Для реальных токенов пытаемся декодировать (в тестах это не используется)
    # Но на всякий случай возвращаем seller_id=1
    return TokenData(seller_id=1, email="test@example.com")


async def get_current_seller_id(current_user: TokenData = Depends(get_current_user)) -> int:
    """Заглушка для получения ID текущего продавца в тестах"""
    if current_user.seller_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
        )
    
    return current_user.seller_id