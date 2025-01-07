# app/models/product.py
from uuid import uuid4
from sqlalchemy import Column, String, select, DateTime, Boolean, func, UUID, ForeignKey, Float, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession

from . import Base


class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    platform = Column(String, nullable=False, default="amazon")
    country = Column(String, nullable=False, default="ae")

    asin = Column(String, nullable=False)
    name = Column(String, nullable=False)
    images = Column(ARRAY(String), nullable=True)
    price_symbol = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    brand = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    product_category = Column(String, nullable=True)
    product_information = Column(String, nullable=True)
    feature_bullets = Column(ARRAY(String), nullable=True)
    customization_options = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    is_disabled = Column(Boolean, default=False)
        
    @classmethod
    async def create(cls, db: AsyncSession, **kwargs):
        new_product = cls(**kwargs)
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        return new_product
        
    @classmethod
    async def find_by_id(cls, db: AsyncSession, id: UUID):
        query = select(cls).where(cls.id == id)
        result = await db.execute(query)
        return result.scalars().first()
            
    @classmethod
    async def find_by_asin(cls, db: AsyncSession, asin: str):
        query = select(cls).where(cls.asin == asin)
        result = await db.execute(query)
        return result.scalars().first()
    
    @classmethod
    async def patch(cls, db: AsyncSession, asin: str, **kwargs):
        # Fetch the product from the database
        product = await cls.find_by_asin(db, asin)
        if product is None:
            return None

        # Update the product's attributes with the provided keyword arguments
        for key, value in kwargs.items():
            setattr(product, key, value)

        await db.commit()
        await db.refresh(product)
        return product
    
    @classmethod
    async def delete(cls, db: AsyncSession, asin: str):
        # Fetch the user from the database
        product = await cls.find_by_asin(db, asin)
        if product is None:
            return None

        # Set is_disabled to True and update the database
        product.is_disabled = True
        await db.commit()
        await db.refresh(product)
        return product
