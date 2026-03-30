"""Это модуль с фикстурами для пайтеста.
Фикстуры - это особые функции, которые не надо импортировать явно.
Сам пайтест подтягивает их по имени из файла conftest.py
"""

import asyncio
from typing import Generator

import httpx
import pytest
import pytest_asyncio
from icecream import ic
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select

from src.configurations.settings import settings
from src.models import books  # noqa
from src.models.base import BaseModel
from src.models.books import Book  # noqa F401
from src.models.sellers import Seller
from src.configurations.security import get_password_hash

# Переопределяем движок для запуска тестов и подключаем его к тестовой базе.
# Это решает проблему с сохранностью данных в основной базе приложения.
# Фикстуры тестов их не зачистят.
# и обеспечивает чистую среду для запуска тестов. В ней не будет лишних записей.
async_test_engine = create_async_engine(
    settings.database_test_url,
    echo=True,
)

# Создаем фабрику сессий для тестового движка.
async_test_session = async_sessionmaker(async_test_engine, expire_on_commit=False, autoflush=False)


# Создаем таблицы в тестовой БД. Предварительно удаляя старые.
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables() -> None:
    """Create tables in DB."""
    async with async_test_engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.drop_all)
        await connection.run_sync(BaseModel.metadata.create_all)


# Создаем продавца с ID=1 для тестов
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_seller():
    """Создает тестового продавца с ID=1 для использования в тестах."""
    async with async_test_engine.connect() as connection:
        async with async_test_session(bind=connection) as session:
            # Проверяем, есть ли уже продавца с ID=1
            existing_seller = await session.get(Seller, 1)
            if not existing_seller:
                # Создаем продавца
                seller = Seller(
                    first_name="Тестовый",
                    last_name="Продавец",
                    email="test@example.com",
                    password=get_password_hash("password123")
                )
                session.add(seller)
                await session.flush()
                
                # Если продавец получил ID не 1, удаляем и пробуем создать снова
                # (в реальности это маловероятно, но на всякий случай)
                if seller.id != 1:
                    await session.delete(seller)
                    await session.flush()
                    # Вставляем с явным ID=1 через execute
                    # Это хак, но для тестов подойдет
                    from sqlalchemy import text
                    await session.execute(
                        text("INSERT INTO sellers_table (id, first_name, last_name, email, password) VALUES (1, :first_name, :last_name, :email, :password)"),
                        {
                            "first_name": "Тестовый",
                            "last_name": "Продавец", 
                            "email": "test@example.com",
                            "password": get_password_hash("password123")
                        }
                    )
                await session.commit()


# Создаем сессию для БД используемую для тестов
@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with async_test_engine.connect() as connection:
        async with connection.begin() as transaction:  # Start a transaction
            async with async_test_session(bind=connection) as session:
                yield session
            await transaction.rollback()  # Rollback the transaction after the test


# Коллбэк для переопределения сессии в приложении
@pytest.fixture(scope="function")
def override_get_async_session(db_session):
    async def _override_get_async_session():
        yield db_session

    return _override_get_async_session


# Мы не можем создать 2 приложения (app) - это приведет к ошибкам.
# Поэтому, на время запуска тестов мы подменяем там зависимость с сессией
@pytest.fixture(scope="function")
def test_app(override_get_async_session):
    from src.configurations.database import get_async_session
    from src.configurations.security import get_current_seller_id, get_current_user
    from src.configurations.security_test import get_current_seller_id as test_get_current_seller_id
    from src.configurations.security_test import get_current_user as test_get_current_user
    from src.main import app

    app.dependency_overrides[get_async_session] = override_get_async_session
    
    # В тестах используем заглушки для авторизации
    app.dependency_overrides[get_current_user] = test_get_current_user
    app.dependency_overrides[get_current_seller_id] = test_get_current_seller_id

    return app


# создаем асинхронного клиента для ручек
@pytest_asyncio.fixture(scope="function")
async def async_client(test_app):
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as test_client:
        yield test_client


# создаем авторизованного клиента для тестирования защищенных эндпоинтов
@pytest_asyncio.fixture(scope="function")
async def auth_client(async_client):
    """Клиент с заголовком Authorization для тестирования защищенных эндпоинтов"""
    # Устанавливаем заголовок (в тестах используется заглушка)
    async_client.headers.update({
        "Authorization": "Bearer test_token"
    })
    yield async_client
    # Очищаем заголовки после теста
    async_client.headers.clear()