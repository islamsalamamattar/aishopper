# app/models/chat_session.py
from uuid import uuid4
from sqlalchemy import Column, String, select, DateTime, Boolean, func, UUID, ForeignKey, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from . import Base


class Chatsession(Base):
    __tablename__ = "chat_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String, nullable=True, default="New Shopping Session")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    is_disabled = Column(Boolean, default=False)
    
    interactions = relationship("Interaction", foreign_keys="Interaction.session_id")
        
    @classmethod
    async def create(cls, db: AsyncSession, **kwargs):
        new_session = cls(**kwargs)
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return new_session
        
    @classmethod
    async def find_by_id(cls, db: AsyncSession, id: UUID):
        query = select(cls).where(cls.id == id)
        result = await db.execute(query)
        return result.scalars().first()
            
    @classmethod
    async def find_by_user_id(cls, db: AsyncSession, user_id: str):
        query = select(cls).where(cls.user_id == user_id).order_by(desc(cls.created_at))
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def delete(cls, db: AsyncSession, phone: str):
        session = await cls.find_by_phone(db, phone)
        if session is None:
            return None
        session.is_disabled = True
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def update_title(cls, db: AsyncSession, session_id: UUID, title: str):
        query = select(cls).where(cls.id == session_id)
        result = await db.execute(query)
        session = result.scalars().first()
        if session:
            session.title = title
            await db.commit()
            await db.refresh(session)
        return session
