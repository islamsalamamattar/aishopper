from uuid import uuid4
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, func, UUID, JSON, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import Base

class Checkout(Base):
    __tablename__ = "checkouts" 
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    platform = Column(String, nullable=False, default="amazon")
    country = Column(String, nullable=False, default="ae")
    link_type = Column(String, nullable=True)
    products = Column(ARRAY(JSON), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        user_id: UUID,
        platform: str = "amazon",
        country: str = "ae",
        link_type: Optional[str] = None,
        products: Optional[List[dict]] = None,
    ) -> "Checkout":
        new_checkout = cls(
            user_id=user_id,
            platform=platform,
            country=country,
            link_type=link_type,
            products=products,
        )
        db.add(new_checkout)
        await db.commit()
        await db.refresh(new_checkout)
        return new_checkout

    @classmethod
    async def find_by_user_id(cls, db: AsyncSession, user_id: UUID) -> Optional["Checkout"]:
        result = await db.execute(
            select(cls).filter(cls.user_id == user_id, cls.is_deleted == False)
        )
        checkout = result.scalars().all()
        return checkout

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        user_id: UUID,
        platform: Optional[str] = None,
        country: Optional[str] = None,
        link_type: Optional[str] = None,
        products: Optional[List[dict]] = None,
    ) -> Optional["Checkout"]:
        result = await db.execute(
            select(cls).filter(cls.user_id == user_id, cls.is_deleted == False)
        )
        checkout = result.scalars().first()
        if checkout:
            if platform is not None:
                checkout.platform = platform
            if country is not None:
                checkout.country = country
            if link_type is not None:
                checkout.link_type = link_type
            if products is not None:
                checkout.products = products
            await db.commit()
            await db.refresh(checkout)
        return checkout
    
    @classmethod
    async def delete(cls, db: AsyncSession, user_id: UUID) -> Optional["Checkout"]:
        result = await db.execute(
            select(cls).filter(cls.user_id == user_id, cls.is_deleted == False)
        )
        checkout = result.scalars().first()
        if checkout:
            checkout.is_deleted = True
            await db.commit()
            await db.refresh(checkout)
        return checkout
