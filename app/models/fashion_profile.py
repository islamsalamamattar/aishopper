# app/models/profile.py
from uuid import uuid4
from typing import List
from sqlalchemy import Column, String, Integer, ARRAY, DateTime, ForeignKey, Boolean, func, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import Base

class FashionProfile(Base):
    __tablename__ = "fashion_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False) # Male | Female | Kids
    relation = Column(String, nullable=True) # Self | Spouse | Child | Parent | Friend
    age = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    chest_shape = Column(String, nullable=True)
    abdomen_shape = Column(String, nullable=True)
    hip_shape = Column(String, nullable=True)
    fitting = Column(String, nullable=True)
    bra_sizing = Column(String, nullable=True) # European,Korean | American,English | French,Spanish | Italian
    bra_underband = Column(Integer, nullable=True) #  60 > 125 | 28 > 54 | 75 > 140 | 0 > 12
    bra_cup = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        user_id: UUID,
        category: str,
        relation: str,
        age: int,
        weight: int,
        height: int,
        chest_shape: str,
        abdomen_shape: str,
        hip_shape: str,
        fitting: str,
        bra_sizing: str,
        bra_underband: int,
        bra_cup: str
    ):
        new_profile = cls(
            user_id=user_id,
            category=category,
            relation=relation,
            age=age,
            weight=weight,
            height=height,
            chest_shape=chest_shape,
            abdomen_shape=abdomen_shape,
            hip_shape=hip_shape,
            fitting=fitting,
            bra_sizing=bra_sizing,
            bra_underband=bra_underband,
            bra_cup=bra_cup,
        )
        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)
        return new_profile

    @classmethod
    async def find_by_user_id(cls, db: AsyncSession, user_id: UUID):
        result = await db.execute(select(cls).filter(cls.user_id == user_id))
        profile = result.scalars().first()
        return profile

    @classmethod
    async def update(cls, db: AsyncSession, user_id: UUID, **kwargs):
        result = await db.execute(select(cls).filter(cls.user_id == user_id))
        profile = result.scalars().first()
        if profile:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(profile, key, value)
            await db.commit()
            await db.refresh(profile)
        return profile
