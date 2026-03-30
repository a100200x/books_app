import pytest
from fastapi import status
from icecream import ic
from sqlalchemy import select

from src.models.books import Book
from src.models.sellers import Seller
from src.configurations.security import get_password_hash

API_V1_URL_PREFIX = "/api/v1/books"


# Тест на ручку создающую книгу
@pytest.mark.asyncio()
async def test_create_book(auth_client):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
    }
    response = await auth_client.post(f"{API_V1_URL_PREFIX}/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_book_id = result_data.pop("id", None)
    assert resp_book_id is not None, "Book id not returned from endpoint"

    # В заглушке тестовой авторизации seller_id=1
    # Продавец с ID=1 должен быть создан фикстурой create_test_seller
    assert result_data == {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "pages": 300,
        "year": 2025,
        "seller_id": 1,  # Изменено с None на 1, так как используется auth_client
    }


@pytest.mark.asyncio()
async def test_create_book_with_old_year(auth_client):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 999,
    }
    response = await auth_client.post(f"{API_V1_URL_PREFIX}/", json=data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Тест на ручку получения списка книг
@pytest.mark.asyncio()
async def test_get_books(db_session, async_client):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=104)
    book_2 = Book(author="Lermontov", title="Mziri", year=2021, pages=108)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/")

    assert response.status_code == status.HTTP_200_OK

    assert len(response.json()["books"]) == 2  # Опасный паттерн! Если в БД есть данные, то тест упадет

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2021,
                "id": book.id,
                "pages": 104,
                "seller_id": None,  # Добавлено поле seller_id
            },
            {
                "title": "Mziri",
                "author": "Lermontov",
                "year": 2021,
                "id": book_2.id,
                "pages": 108,
                "seller_id": None,  # Добавлено поле seller_id
            },
        ]
    }


# Тест на ручку получения одной книги
@pytest.mark.asyncio()
async def test_get_single_book(db_session, async_client):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104)
    book_2 = Book(author="Lermontov", title="Mziri", year=1997, pages=104)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/{book.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2001,
        "pages": 104,
        "id": book.id,
        "seller_id": None,  # Добавлено поле seller_id
    }


@pytest.mark.asyncio()
async def test_get_single_book_with_wrong_id(db_session, async_client):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/426548")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# Тест на ручку обновления книги
@pytest.mark.asyncio()
async def test_update_book(db_session, auth_client):
    # Используем продавца с ID=1 (должен быть создан фикстурой)
    # Создаем книгу для этого продавца
    book = Book(
        author="Pushkin", 
        title="Eugeny Onegin", 
        year=2001, 
        pages=104,
        seller_id=1  # Привязываем книгу к продавцу с ID=1
    )

    db_session.add(book)
    await db_session.flush()

    data = {
        "title": "Mziri",
        "author": "Lermontov",
        "pages": 250,
        "year": 2024,
        "id": book.id,
        "seller_id": 1,  # Добавляем seller_id
    }

    response = await auth_client.put(
        f"{API_V1_URL_PREFIX}/{book.id}",
        json=data,
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Book, book.id)
    assert res.title == "Mziri"
    assert res.author == "Lermontov"
    assert res.pages == 250
    assert res.year == 2024
    assert res.id == book.id
    assert res.seller_id == 1


@pytest.mark.asyncio()
async def test_delete_book(db_session, async_client):
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024)

    db_session.add(book)
    await db_session.flush()
    ic(book.id)

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{book.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()
    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 0


@pytest.mark.asyncio()
async def test_delete_book_with_invalid_book_id(db_session, async_client):
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{book.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND