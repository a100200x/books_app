__all__ = ["SellerService"]

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.security import verify_password, get_password_hash
from src.models.sellers import Seller
from src.schemas.books import ReturnedBook
from src.schemas.sellers import SellerCreate, SellerUpdate, SellerResponse, SellerWithBooksResponse


class SellerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_seller(self, seller_data: SellerCreate) -> Seller:
        """Создание нового продавца"""
        # Хешируем пароль перед сохранением
        hashed_password = get_password_hash(seller_data.password)
        
        new_seller = Seller(
            first_name=seller_data.first_name,
            last_name=seller_data.last_name,
            email=seller_data.email,
            password=hashed_password,
        )
        
        self.session.add(new_seller)
        await self.session.flush()
        
        return new_seller

    async def authenticate_seller(self, email: str, password: str) -> Seller | None:
        """Аутентификация продавца по email и паролю"""
        query = select(Seller).where(Seller.email == email)
        result = await self.session.execute(query)
        seller = result.scalar_one_or_none()
        
        if seller is None:
            return None
        
        # Проверяем пароль
        if not verify_password(password, seller.password):
            return None
        
        return seller

    async def get_all_sellers(self) -> list[Seller]:
        """Получение всех продавцов"""
        query = select(Seller)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_seller_by_id(self, seller_id: int) -> Seller | None:
        """Получение продавца по ID"""
        return await self.session.get(Seller, seller_id)

    async def get_seller_with_books(self, seller_id: int) -> Seller | None:
        """Получение продавца с его книгами"""
        query = select(Seller).where(Seller.id == seller_id)
        result = await self.session.execute(query)
        seller = result.scalar_one_or_none()
        
        # Загружаем книги продавца
        if seller:
            await self.session.refresh(seller, ["books"])
        
        return seller

    async def update_seller(self, seller_id: int, seller_data: SellerUpdate) -> Seller | None:
        """Обновление данных продавца"""
        seller = await self.session.get(Seller, seller_id)
        
        if seller:
            if seller_data.first_name is not None:
                seller.first_name = seller_data.first_name
            if seller_data.last_name is not None:
                seller.last_name = seller_data.last_name
            if seller_data.email is not None:
                seller.email = seller_data.email
            
            await self.session.flush()
        
        return seller

    async def delete_seller(self, seller_id: int) -> bool:
        """Удаление продавца и всех его книг (каскадное удаление)"""
        seller = await self.session.get(Seller, seller_id)
        
        if seller:
            await self.session.delete(seller)
            return True
        
        return False

    @staticmethod
    def seller_to_response(seller: Seller) -> SellerResponse:
        """Преобразование модели Seller в ответ без пароля"""
        return SellerResponse(
            id=seller.id,
            first_name=seller.first_name,
            last_name=seller.last_name,
            email=seller.email,
        )

    @staticmethod
    def seller_with_books_to_response(seller: Seller) -> SellerWithBooksResponse:
        """Преобразование модели Seller с книгами в ответ"""
        books_response = []
        for book in seller.books:
            books_response.append(
                ReturnedBook(
                    id=book.id,
                    title=book.title,
                    author=book.author,
                    year=book.year,
                    pages=book.pages,
                    seller_id=book.seller_id,
                )
            )
        
        return SellerWithBooksResponse(
            id=seller.id,
            first_name=seller.first_name,
            last_name=seller.last_name,
            email=seller.email,
            books=books_response,
        )