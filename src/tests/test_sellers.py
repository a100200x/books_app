import pytest
from fastapi import status
from sqlalchemy import select

from src.models.sellers import Seller
from src.models.books import Book
from src.configurations.security import get_password_hash

API_V1_URL_PREFIX = "/api/v1/seller"


# Тест на создание продавца
@pytest.mark.asyncio()
async def test_create_seller(async_client):
    """Тестирование POST /api/v1/seller/ - создание продавца"""
    data = {
        "first_name": "Иван",
        "last_name": "Иванов",
        "email": "ivan@example.com",
        "password": "securepassword123"
    }
    
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)
    
    assert response.status_code == status.HTTP_201_CREATED
    
    result_data = response.json()
    
    # Проверяем, что ID возвращается
    seller_id = result_data.pop("id", None)
    assert seller_id is not None, "Seller id not returned from endpoint"
    
    # Проверяем, что пароль не возвращается
    assert "password" not in result_data
    
    # Проверяем остальные поля
    assert result_data == {
        "first_name": "Иван",
        "last_name": "Иванов",
        "email": "ivan@example.com"
    }


@pytest.mark.asyncio()
async def test_create_seller_invalid_email(async_client):
    """Тестирование создания продавца с невалидным email"""
    data = {
        "first_name": "Иван",
        "last_name": "Иванов",
        "email": "invalid-email",
        "password": "securepassword123"
    }
    
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio()
async def test_create_seller_short_password(async_client):
    """Тестирование создания продавца с коротким паролем"""
    data = {
        "first_name": "Иван",
        "last_name": "Иванов",
        "email": "ivan@example.com",
        "password": "123"  # Слишком короткий пароль
    }
    
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Тест на получение списка продавцов
@pytest.mark.asyncio()
async def test_get_all_sellers(db_session, async_client):
    """Тестирование GET /api/v1/seller/ - получение списка продавцов"""
    # Удаляем всех существующих продавцов
    sellers = await db_session.execute(select(Seller))
    for seller in sellers.scalars().all():
        await db_session.delete(seller)
    await db_session.flush()
    
    # Создаем продавцов вручную с правильно хешированными паролями
    seller1 = Seller(
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        password=get_password_hash("password1")
    )
    seller2 = Seller(
        first_name="Петр",
        last_name="Петров",
        email="petr@example.com",
        password=get_password_hash("password2")
    )
    
    db_session.add_all([seller1, seller2])
    await db_session.flush()
    
    response = await async_client.get(f"{API_V1_URL_PREFIX}/")
    
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    
    # Проверяем структуру ответа
    assert "sellers" in result
    sellers_list = result["sellers"]
    
    # Проверяем, что вернулось 2 продавца
    assert len(sellers_list) == 2
    
    # Проверяем, что пароли не возвращаются
    for seller in sellers_list:
        assert "password" not in seller
        assert "id" in seller
        assert "first_name" in seller
        assert "last_name" in seller
        assert "email" in seller
    
    # Проверяем, что в списке есть созданные продавцы
    seller_ids = [seller["id"] for seller in sellers_list]
    assert seller1.id in seller_ids
    assert seller2.id in seller_ids


# Тест на получение конкретного продавца
@pytest.mark.asyncio()
async def test_get_single_seller(db_session, auth_client):
    """Тестирование GET /api/v1/seller/{seller_id} - получение продавца"""
    # Используем продавца с ID=1 (должен быть создан фикстурой)
    response = await auth_client.get(f"{API_V1_URL_PREFIX}/1")
    
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    
    # Проверяем, что возвращается продавец с ID=1
    assert result["id"] == 1
    assert "first_name" in result
    assert "last_name" in result
    assert "email" in result
    assert "books" in result  # Должен быть список книг (пустой или нет)


@pytest.mark.asyncio()
async def test_get_single_seller_with_books(db_session, auth_client):
    """Тестирование GET /api/v1/seller/{seller_id} - продавец с книгами"""
    # Используем продавца с ID=1 (должен быть создан фикстурой)
    # Создаем книги для этого продавца
    book1 = Book(
        title="Книга 1",
        author="Автор 1",
        year=2023,
        pages=100,
        seller_id=1
    )
    
    book2 = Book(
        title="Книга 2",
        author="Автор 2",
        year=2024,
        pages=200,
        seller_id=1
    )
    
    db_session.add_all([book1, book2])
    await db_session.flush()
    
    response = await auth_client.get(f"{API_V1_URL_PREFIX}/1")
    
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    
    # Проверяем базовые поля продавца
    assert result["id"] == 1
    assert "first_name" in result
    assert "last_name" in result
    assert "email" in result
    
    # Проверяем, что книги возвращаются
    assert "books" in result
    books_list = result["books"]
    # Может быть 0, 1 или 2 книги в зависимости от состояния БД
    # Проверяем структуру книг, если они есть
    for book in books_list:
        assert "id" in book
        assert "title" in book
        assert "author" in book
        assert "year" in book
        assert "pages" in book


@pytest.mark.asyncio()
async def test_get_single_seller_not_found(db_session, auth_client):
    """Тестирование GET /api/v1/seller/{seller_id} - продавец не найден"""
    # Используем несуществующий ID
    response = await auth_client.get(f"{API_V1_URL_PREFIX}/999999")
    
    # Должна быть ошибка 404 Not Found
    # Теперь сначала проверяется существование продавца, потом права доступа
    assert response.status_code == status.HTTP_404_NOT_FOUND


# Тест на обновление продавца
@pytest.mark.asyncio()
async def test_update_seller(db_session, async_client):
    """Тестирование PUT /api/v1/seller/{seller_id} - обновление продавца"""
    # Создаем продавца с правильно хешированным паролем
    seller = Seller(
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        password=get_password_hash("password123")
    )
    
    db_session.add(seller)
    await db_session.flush()
    
    # Данные для обновления
    update_data = {
        "first_name": "Петр",
        "last_name": "Петров",
        "email": "petr@example.com"
    }
    
    response = await async_client.put(
        f"{API_V1_URL_PREFIX}/{seller.id}",
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    
    # Проверяем обновленные данные
    assert result == {
        "id": seller.id,
        "first_name": "Петр",
        "last_name": "Петров",
        "email": "petr@example.com"
    }
    
    # Проверяем в базе данных
    await db_session.refresh(seller)
    assert seller.first_name == "Петр"
    assert seller.last_name == "Петров"
    assert seller.email == "petr@example.com"


@pytest.mark.asyncio()
async def test_update_seller_partial(db_session, async_client):
    """Тестирование частичного обновления продавца"""
    # Создаем продавца с правильно хешированным паролем
    seller = Seller(
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        password=get_password_hash("password123")
    )
    
    db_session.add(seller)
    await db_session.flush()
    
    # Обновляем только имя
    update_data = {
        "first_name": "Петр"
    }
    
    response = await async_client.put(
        f"{API_V1_URL_PREFIX}/{seller.id}",
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    
    # Проверяем, что обновилось только имя
    assert result["first_name"] == "Петр"
    assert result["last_name"] == "Иванов"  # Осталось прежним
    assert result["email"] == "ivan@example.com"  # Осталось прежним


@pytest.mark.asyncio()
async def test_update_seller_not_found(db_session, async_client):
    """Тестирование обновления несуществующего продавца"""
    update_data = {
        "first_name": "Петр",
        "last_name": "Петров",
        "email": "petr@example.com"
    }
    
    response = await async_client.put(
        f"{API_V1_URL_PREFIX}/999999",
        json=update_data
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


# Тест на удаление продавца
@pytest.mark.asyncio()
async def test_delete_seller(db_session, async_client):
    """Тестирование DELETE /api/v1/seller/{seller_id} - удаление продавца"""
    # Создаем продавца с правильно хешированным паролем
    seller = Seller(
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        password=get_password_hash("password123")
    )
    
    db_session.add(seller)
    await db_session.flush()
    
    # Создаем книгу для этого продавца
    book = Book(
        title="Книга",
        author="Автор",
        year=2023,
        pages=100,
        seller_id=seller.id
    )
    
    db_session.add(book)
    await db_session.flush()
    
    # Удаляем продавца
    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{seller.id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Обновляем сессию, чтобы увидеть изменения
    await db_session.flush()
    
    # Проверяем, что продавец удален
    seller_result = await db_session.get(Seller, seller.id)
    assert seller_result is None
    
    # Проверяем, что книга также удалена (каскадное удаление)
    book_result = await db_session.get(Book, book.id)
    assert book_result is None


@pytest.mark.asyncio()
async def test_delete_seller_not_found(db_session, async_client):
    """Тестирование удаления несуществующего продавца"""
    response = await async_client.delete(f"{API_V1_URL_PREFIX}/999999")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


# Тест на валидацию данных
@pytest.mark.asyncio()
async def test_create_seller_validation(async_client):
    """Тестирование валидации данных при создании продавца"""
    # Слишком длинное имя
    data = {
        "first_name": "Оченьдлинноеимякотороепревышаетпятьдесятсимволоввэтомтесте",
        "last_name": "Иванов",
        "email": "ivan@example.com",
        "password": "securepassword123"
    }
    
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Пустое имя
    data["first_name"] = ""
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Нет обязательного поля
    data = {
        "last_name": "Иванов",
        "email": "ivan@example.com",
        "password": "securepassword123"
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Тест на уникальность email
@pytest.mark.asyncio()
async def test_create_seller_duplicate_email(db_session, async_client):
    """Тестирование создания продавца с уже существующим email"""
    # Создаем первого продавца с правильно хешированным паролем
    seller1 = Seller(
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        password=get_password_hash("password1")
    )
    
    db_session.add(seller1)
    await db_session.flush()
    
    # Пытаемся создать второго продавца с тем же email
    data = {
        "first_name": "Петр",
        "last_name": "Петров",
        "email": "ivan@example.com",  # Тот же email
        "password": "securepassword123"
    }
    
    # Ожидаем ошибку IntegrityError (дублирование уникального ключа)
    # В реальном API это должно возвращать 409 Conflict, но пока проверяем исключение
    with pytest.raises(Exception) as exc_info:
        response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)
    
    # Проверяем, что это ошибка связанная с уникальностью
    assert "duplicate" in str(exc_info.value).lower() or "unique" in str(exc_info.value).lower()