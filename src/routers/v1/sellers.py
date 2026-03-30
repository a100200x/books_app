from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.configurations.security import get_current_seller_id
from src.schemas.sellers import (
    SellerCreate,
    SellerUpdate,
    SellerResponse,
    SellerWithBooksResponse,
    SellersListResponse,
)
from src.services import SellerService

sellers_router = APIRouter(prefix="/seller", tags=["sellers"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


@sellers_router.post("/", response_model=SellerResponse, status_code=status.HTTP_201_CREATED)
async def create_seller(seller: SellerCreate, session: DBSession):
    """Регистрация нового продавца"""
    new_seller = await SellerService(session).create_seller(seller)
    return SellerService.seller_to_response(new_seller)


@sellers_router.get("/", response_model=SellersListResponse)
async def get_all_sellers(session: DBSession):
    """Получение списка всех продавцов (без паролей)"""
    sellers = await SellerService(session).get_all_sellers()
    sellers_response = [SellerService.seller_to_response(seller) for seller in sellers]
    return {"sellers": sellers_response}


@sellers_router.get("/{seller_id}", response_model=SellerWithBooksResponse)
async def get_seller(
    seller_id: int,
    session: DBSession,
    current_seller_id: int = Depends(get_current_seller_id),
):
    """Получение данных о конкретном продавце с его книгами"""
    # Сначала получаем продавца
    seller = await SellerService(session).get_seller_with_books(seller_id)
    
    # Если продавец не найден, возвращаем 404
    if seller is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    
    return SellerService.seller_with_books_to_response(seller)


@sellers_router.put("/{seller_id}", response_model=SellerResponse)
async def update_seller(seller_id: int, seller_data: SellerUpdate, session: DBSession):
    """Обновление данных о продавце (без обновления пароля и книг)"""
    updated_seller = await SellerService(session).update_seller(seller_id, seller_data)
    
    if updated_seller is not None:
        return SellerService.seller_to_response(updated_seller)
    
    return Response(status_code=status.HTTP_404_NOT_FOUND)


@sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: DBSession):
    """Удаление продавца и всех его книг"""
    deleted = await SellerService(session).delete_seller(seller_id)
    
    if not deleted:
        return Response(status_code=status.HTTP_404_NOT_FOUND)