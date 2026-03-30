"""
Тесты для проверки соответствия API OpenAPI схеме.
Эти тесты проверяют, что API соответствует документации.
"""

import pytest
from fastapi import status
import json


@pytest.mark.asyncio()
async def test_openapi_schema_exists(async_client):
    """Проверка, что OpenAPI схема доступна"""
    response = await async_client.get("/openapi.json")
    
    assert response.status_code == status.HTTP_200_OK
    
    schema = response.json()
    
    # Проверяем базовую структуру OpenAPI схемы
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert "components" in schema
    
    # Проверяем версию OpenAPI
    assert schema["openapi"].startswith("3.")


@pytest.mark.asyncio()
async def test_books_endpoints_in_schema(async_client):
    """Проверка, что все эндпоинты книг присутствуют в схеме"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    paths = schema["paths"]
    
    # Проверяем основные эндпоинты книг
    assert "/api/v1/books/" in paths
    assert "/api/v1/books/{book_id}" in paths
    
    # Проверяем методы для /api/v1/books/
    books_path = paths["/api/v1/books/"]
    assert "get" in books_path  # GET /api/v1/books/
    assert "post" in books_path  # POST /api/v1/books/
    
    # Проверяем методы для /api/v1/books/{book_id}
    book_detail_path = paths["/api/v1/books/{book_id}"]
    assert "get" in book_detail_path  # GET /api/v1/books/{book_id}
    assert "put" in book_detail_path  # PUT /api/v1/books/{book_id}
    assert "patch" in book_detail_path  # PATCH /api/v1/books/{book_id}
    assert "delete" in book_detail_path  # DELETE /api/v1/books/{book_id}


@pytest.mark.asyncio()
async def test_sellers_endpoints_in_schema(async_client):
    """Проверка, что все эндпоинты продавцов присутствуют в схеме"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    paths = schema["paths"]
    
    # Проверяем основные эндпоинты продавцов
    assert "/api/v1/seller/" in paths
    assert "/api/v1/seller/{seller_id}" in paths
    
    # Проверяем методы для /api/v1/seller/
    sellers_path = paths["/api/v1/seller/"]
    assert "get" in sellers_path  # GET /api/v1/seller/
    assert "post" in sellers_path  # POST /api/v1/seller/
    
    # Проверяем методы для /api/v1/seller/{seller_id}
    seller_detail_path = paths["/api/v1/seller/{seller_id}"]
    assert "get" in seller_detail_path  # GET /api/v1/seller/{seller_id}
    assert "put" in seller_detail_path  # PUT /api/v1/seller/{seller_id}
    assert "delete" in seller_detail_path  # DELETE /api/v1/seller/{seller_id}


@pytest.mark.asyncio()
async def test_schemas_in_components(async_client):
    """Проверка, что все схемы присутствуют в components"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    
    # Проверяем схемы книг
    assert "IncomingBook" in schemas
    assert "ReturnedBook" in schemas
    assert "ReturnedAllBooks" in schemas
    assert "PatchBook" in schemas
    
    # Проверяем схемы продавцов
    assert "SellerCreate" in schemas
    assert "SellerUpdate" in schemas
    assert "SellerResponse" in schemas
    assert "SellerWithBooksResponse" in schemas
    assert "SellersListResponse" in schemas


@pytest.mark.asyncio()
async def test_book_schema_structure(async_client):
    """Проверка структуры схемы книги"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    returned_book_schema = schema["components"]["schemas"]["ReturnedBook"]
    
    # Проверяем обязательные поля
    properties = returned_book_schema["properties"]
    required_fields = returned_book_schema.get("required", [])
    
    assert "id" in properties
    assert "title" in properties
    assert "author" in properties
    assert "year" in properties
    assert "pages" in properties
    
    # Проверяем, что id обязателен
    assert "id" in required_fields
    
    # Проверяем типы полей
    assert properties["id"]["type"] == "integer"
    assert properties["title"]["type"] == "string"
    assert properties["author"]["type"] == "string"
    assert properties["year"]["type"] == "integer"
    assert properties["pages"]["type"] == "integer"


@pytest.mark.asyncio()
async def test_seller_schema_structure(async_client):
    """Проверка структуры схемы продавца"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    seller_response_schema = schema["components"]["schemas"]["SellerResponse"]
    
    # Проверяем обязательные поля
    properties = seller_response_schema["properties"]
    required_fields = seller_response_schema.get("required", [])
    
    assert "id" in properties
    assert "first_name" in properties
    assert "last_name" in properties
    assert "email" in properties
    
    # Проверяем, что поля обязательны
    for field in ["id", "first_name", "last_name", "email"]:
        assert field in required_fields
    
    # Проверяем типы полей
    assert properties["id"]["type"] == "integer"
    assert properties["first_name"]["type"] == "string"
    assert properties["last_name"]["type"] == "string"
    assert properties["email"]["type"] == "string"
    assert properties["email"]["format"] == "email"  # email формат


@pytest.mark.asyncio()
async def test_seller_with_books_schema_structure(async_client):
    """Проверка структуры схемы продавца с книгами"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    seller_with_books_schema = schema["components"]["schemas"]["SellerWithBooksResponse"]
    
    # Проверяем наличие поля books
    properties = seller_with_books_schema["properties"]
    assert "books" in properties
    
    # Проверяем, что books - это массив ReturnedBook
    books_property = properties["books"]
    assert books_property["type"] == "array"
    
    # Проверяем items ссылается на ReturnedBook
    items = books_property.get("items", {})
    ref = items.get("$ref", "")
    assert "#/components/schemas/ReturnedBook" in ref


@pytest.mark.asyncio()
async def test_api_responses_match_schema(async_client, db_session):
    """Проверка, что реальные ответы API соответствуют схеме"""
    from src.models.books import Book
    from src.models.sellers import Seller
    
    # Тестируем ответ для книг
    book = Book(
        title="Test Book",
        author="Test Author",
        year=2023,
        pages=100
    )
    
    db_session.add(book)
    await db_session.flush()
    
    # GET /api/v1/books/{book_id}
    response = await async_client.get(f"/api/v1/books/{book.id}")
    assert response.status_code == status.HTTP_200_OK
    
    book_data = response.json()
    
    # Проверяем структуру ответа
    assert "id" in book_data
    assert "title" in book_data
    assert "author" in book_data
    assert "year" in book_data
    assert "pages" in book_data
    
    # Проверяем типы данных
    assert isinstance(book_data["id"], int)
    assert isinstance(book_data["title"], str)
    assert isinstance(book_data["author"], str)
    assert isinstance(book_data["year"], int)
    assert isinstance(book_data["pages"], int)


@pytest.mark.asyncio()
async def test_error_responses_in_schema(async_client):
    """Проверка, что ошибки описаны в схеме"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    # Проверяем путь /api/v1/books/{book_id}
    book_detail_path = schema["paths"]["/api/v1/books/{book_id}"]
    
    # Проверяем, что для GET метода описана ошибка 404
    get_operation = book_detail_path["get"]
    responses = get_operation["responses"]
    
    assert "404" in responses
    assert "description" in responses["404"]
    
    # Проверяем, что для DELETE метода описана ошибка 404
    delete_operation = book_detail_path["delete"]
    responses = delete_operation["responses"]
    
    assert "404" in responses
    assert "description" in responses["404"]


@pytest.mark.asyncio()
async def test_request_bodies_match_schema(async_client):
    """Проверка, что тела запросов соответствуют схеме"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    # Проверяем POST /api/v1/books/
    post_books = schema["paths"]["/api/v1/books/"]["post"]
    request_body = post_books.get("requestBody", {})
    
    assert request_body.get("required", False) == True
    
    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema_ref = json_content.get("schema", {}).get("$ref", "")
    
    assert "#/components/schemas/IncomingBook" in schema_ref
    
    # Проверяем POST /api/v1/seller/
    post_seller = schema["paths"]["/api/v1/seller/"]["post"]
    request_body = post_seller.get("requestBody", {})
    
    assert request_body.get("required", False) == True
    
    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema_ref = json_content.get("schema", {}).get("$ref", "")
    
    assert "#/components/schemas/SellerCreate" in schema_ref


@pytest.mark.asyncio()
async def test_query_parameters_in_schema(async_client):
    """Проверка query параметров в схеме (если есть)"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    # В текущей реализации нет query параметров, но проверяем структуру
    # Это пример для будущего расширения
    
    # Проверяем, что paths существуют
    assert "paths" in schema
    
    # Можно добавить проверку, если появятся query параметры
    # Например: assert "parameters" in some_path_schema


@pytest.mark.asyncio()
async def test_api_tags_defined(async_client):
    """Проверка, что теги API определены в схемах операций"""
    response = await async_client.get("/openapi.json")
    schema = response.json()
    
    # Проверяем, что операции имеют правильные теги
    books_operation = schema["paths"]["/api/v1/books/"]["get"]
    assert "tags" in books_operation
    assert "books" in books_operation["tags"]
    
    sellers_operation = schema["paths"]["/api/v1/seller/"]["get"]
    assert "tags" in sellers_operation
    assert "sellers" in sellers_operation["tags"]