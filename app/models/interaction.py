# app/models/interaction.py
from uuid import uuid4
from sqlalchemy import Column, String, select, DateTime, Boolean, func, ForeignKey, UUID, Integer, desc
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    prompt = Column(String, nullable=False)
    response = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    @classmethod
    async def create(cls, db: AsyncSession, user_id: UUID, prompt: str, response: str,  model: str, prompt_tokens: int, completion_tokens:int, total_tokens: int):
        new_interaction = cls(
            user_id=user_id,
            prompt=prompt,
            response=response,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
        db.add(new_interaction)
        await db.commit()
        await db.refresh(new_interaction)
        return new_interaction

    @classmethod
    async def find_by_user_id(cls, db: AsyncSession, user_id: UUID):
        result = await db.execute(select(cls).filter(cls.user_id == user_id).order_by(cls.timestamp))
        interactions = result.scalars().all()
        return interactions
    
    @classmethod
    async def find_by_id(cls, db: AsyncSession, id: UUID):
        query = select(cls).where(cls.id == id)
        result = await db.execute(query)
        return result.scalars().first()
    
    @classmethod
    async def find_last_n_by_user_id(cls, db: AsyncSession, user_id: UUID, n: int):
        result = await db.execute(
            select(Interaction)
            .filter_by(user_id=user_id)
            .order_by(Interaction.timestamp.desc())
            .limit(n)
        )
        return result.scalars().all()
    
    @classmethod
    async def tokens_usage(cls, db: AsyncSession, user_id: UUID):
        result = await db.execute(
            select(
                func.sum(cls.prompt_tokens).label("prompt_tokens"),
                func.sum(cls.completion_tokens).label("completion_tokens"),
                func.sum(cls.total_tokens).label("total_tokens")
            ).filter(cls.user_id == user_id)
        )
        row = result.first()
        tokens_usage_dict = {
            'prompt_tokens': row.prompt_tokens or 0,
            'completion_tokens': row.completion_tokens or 0,
            'total_tokens': row.total_tokens or 0
        }
        return tokens_usage_dict