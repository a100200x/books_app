from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from .books import ReturnedBook  # Явный импорт

__all__ = [
    "SellerCreate",
    "SellerUpdate",
    "SellerResponse",
    "SellerWithBooksResponse",
    "SellersListResponse",
]


# Базовый класс для продавца
class SellerBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=100)


# Класс для создания продавца (регистрация)
class SellerCreate(SellerBase):
    password: str = Field(..., min_length=6, max_length=255)


# Класс для обновления данных продавца
class SellerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=100)


# Класс для ответа с данными продавца (без пароля)
class SellerResponse(SellerBase):
    id: int


# Класс для ответа с данными продавца и его книгами
class SellerWithBooksResponse(SellerResponse):
    books: list[ReturnedBook] = []  # Без кавычек, прямой тип


# Класс для ответа со списком продавцов
class SellersListResponse(BaseModel):
    sellers: list[SellerResponse]