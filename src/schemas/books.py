from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

__all__ = [
    "PatchBook",
    "IncomingBook",
    "ReturnedBook",
    "ReturnedAllBooks",
]


# Базовый класс "Книги", содержащий поля, которые есть во всех классах-наследниках.
class BaseBook(BaseModel):
    title: str
    author: str
    year: int


# Класс для обработки входных данных для частичного обновления данных о книге
class PatchBook(BaseModel):
    title: str | None = None
    author: str | None = None
    year: int | None = None
    pages: int | None = None
    seller_id: int | None = None


# Класс для валидации входящих данных. Не содержит id так как его присваивает БД.
class IncomingBook(BaseBook):
    pages: int = Field(
        default=100, alias="count_pages"
    )  # Пример использования тонкой настройки полей. Передачи в них метаинформации.
    seller_id: Optional[int] = None

    @field_validator("year")  # Валидатор, проверяет что дата не слишком древняя
    @staticmethod
    def validate_year(val: int):
        if val < 1000:
            raise PydanticCustomError("Validation error", "Year is too old!")

        return val


# Класс, валидирующий исходящие данные. Он уже содержит id
class ReturnedBook(BaseBook):  # {"id": 1, "title": "Clean Code", ....}
    id: int
    pages: int
    seller_id: Optional[int] = None


# Класс для возврата массива объектов "Книга"
class ReturnedAllBooks(BaseModel):
    books: list[ReturnedBook]