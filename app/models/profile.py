from uuid import uuid4
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, func, UUID, JSON, ARRAY, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import Base

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    fav_categories = Column(ARRAY(String), nullable=True)
    cart = Column(ARRAY(JSON), nullable=True)
    wishlist = Column(ARRAY(JSON), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_onboarded = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        user_id: UUID,
        fav_categories: Optional[List[str]] = None,
        cart: Optional[List[dict]] = None,
        wishlist: Optional[List[dict]] = None,
    ):
        new_profile = cls(
            user_id=user_id,
            fav_categories=fav_categories,
            cart=cart,
            wishlist=wishlist,
        )
        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)
        return new_profile

    @classmethod
    async def find_by_user_id(cls, db: AsyncSession, user_id: UUID):
        result = await db.execute(select(cls).filter(cls.user_id == user_id, cls.is_deleted == False))
        profile = result.scalars().first()
        return profile

    @classmethod
    async def update(cls, db: AsyncSession, user_id: UUID, **kwargs):
        result = await db.execute(select(cls).filter(cls.user_id == user_id, cls.is_deleted == False))
        profile = result.scalars().first()
        if profile:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(profile, key, value)
            await db.commit()
            await db.refresh(profile)
        return profile
        
    @classmethod
    async def add_to_cart(cls, db: AsyncSession, user_id: UUID, new_product: dict):
        profile = await cls.find_by_user_id(db, user_id)
        if profile:
            new_cart = profile.cart[:] if profile.cart else []           
            new_cart.append(new_product)
            
            await db.execute(
                update(cls)
                .where(cls.user_id == user_id)
                .values(cart=new_cart)
            )
            await db.commit()
            await db.refresh(profile)
        return profile.cart
        
    @classmethod
    async def remove_from_cart(cls, db: AsyncSession, user_id: UUID, old_product: dict):
        profile = await cls.find_by_user_id(db, user_id)
        if profile:
            cart = profile.cart
            for product in cart:
                if product['asin'] == old_product['asin']:
                    cart.remove(product)
            
            await db.execute(
                update(cls)
                .where(cls.user_id == user_id)
                .values(cart=cart)
            )
            await db.commit()
            await db.refresh(profile)
        return profile.cart

    @classmethod
    async def add_to_wishlist(cls, db: AsyncSession, user_id: UUID, new_product: dict):
        profile = await cls.find_by_user_id(db, user_id)
        if profile:
            new_wishlist = profile.wishlist[:] if profile.wishlist else []           
            new_wishlist.append(new_product)
            
            await db.execute(
                update(cls)
                .where(cls.user_id == user_id)
                .values(wishlist=new_wishlist)
            )
            await db.commit()
            await db.refresh(profile)
        return profile.wishlist
        
    @classmethod
    async def remove_from_wishlist(cls, db: AsyncSession, user_id: UUID, old_product: dict):
        profile = await cls.find_by_user_id(db, user_id)
        if profile:
            wishlist = profile.wishlist
            for product in wishlist:
                if product['asin'] == old_product['asin']:
                    wishlist.remove(product)
            
            await db.execute(
                update(cls)
                .where(cls.user_id == user_id)
                .values(wishlist=wishlist)
            )
            await db.commit()
            await db.refresh(profile)
        return profile.wishlist
    
    @classmethod
    async def update_fav_categories(cls, db: AsyncSession, user_id: UUID, new_fav_categories: List[str]):
        profile = await cls.find_by_user_id(db, user_id)
        if profile:
            profile.fav_categories = new_fav_categories[:]
            await db.commit()
            await db.refresh(profile)
        return profile
   
    @classmethod
    async def delete(cls, db: AsyncSession, user_id: UUID):
        result = await db.execute(select(cls).filter(cls.user_id == user_id, cls.is_deleted == False))
        profile = result.scalars().first()
        if profile:
            profile.is_deleted = True
            await db.commit()
            await db.refresh(profile)
        return profile
       
    @classmethod
    async def onboard(cls, db: AsyncSession, user_id: UUID):
        result = await db.execute(select(cls).filter(cls.user_id == user_id, cls.is_onboarded == False))
        profile = result.scalars().first()
        if profile:
            profile.is_onboarded = True
            await db.commit()
            await db.refresh(profile)
        return profile
