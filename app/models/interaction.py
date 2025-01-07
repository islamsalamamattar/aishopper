# app/models/interaction.py

from uuid import uuid4
from sqlalchemy import Column, String, select, DateTime, Boolean, func, ForeignKey, UUID, Integer, ARRAY, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from . import Base


class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    prompt = Column(String, nullable=False)
    tool_calls = Column(ARRAY(JSON), nullable=True)
    search_keywords = Column(ARRAY(JSON), nullable=True)
    amazon_products = Column(ARRAY(JSON), nullable=True)
    noon_products = Column(ARRAY(JSON), nullable=True)
    added_to_cart = Column(ARRAY(JSON), nullable=True)
    response = Column(String, nullable=True)
    next = Column(String, nullable=True)
    model = Column(String, nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    is_deleted = Column(Boolean, default=False)

    @classmethod
    async def create(cls, db: AsyncSession, session_id: UUID, prompt: str, response: str, model: str, prompt_tokens: int, completion_tokens: int, total_tokens: int, tool_calls: list[dict], next: str, search_keywords: list[dict], amazon_products: list[dict], noon_products: list[dict], added_to_cart: list[dict]):
        new_interaction = cls(
            session_id=session_id,
            prompt=prompt,
            response=response,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            tool_calls=tool_calls,
            next=next,
            search_keywords=search_keywords,
            amazon_products=amazon_products,
            noon_products=noon_products,
            added_to_cart=added_to_cart,
        )
        db.add(new_interaction)
        await db.commit()
        await db.refresh(new_interaction)
        return new_interaction

    @classmethod
    async def find_by_session_id(cls, db: AsyncSession, session_id: UUID):
        result = await db.execute(select(cls).filter(cls.session_id == session_id).order_by(cls.timestamp))
        interactions = result.scalars().all()
        return interactions

    @classmethod
    async def find_last_n_by_session_id(cls, db: AsyncSession, session_id: UUID, n: int):
        result = await db.execute(
            select(cls)
            .filter_by(session_id=session_id)
            .order_by(cls.timestamp.desc())
            .limit(n)
        )
        return result.scalars().all()

    @classmethod
    async def find_by_id(cls, db: AsyncSession, id: UUID):
        query = select(cls).where(cls.id == id)
        result = await db.execute(query)
        return result.scalars().first()
        
    @classmethod
    async def patch(cls, db: AsyncSession, id: UUID, **kwargs):
        try:
            # Find the interaction by ID
            query = select(cls).where(cls.id == id)
            result = await db.execute(query)
            interaction = result.scalars().first()

            if not interaction:
                raise NoResultFound(f"No interaction found with id: {id}")


            # Update the interaction with the provided kwargs
            for key, value in kwargs.items():
                if hasattr(interaction, key):
                    setattr(interaction, key, value)

            # Commit the changes
            await db.commit()
            await db.refresh(interaction)

            return interaction

        except NoResultFound as e:
            print(f"Error: {str(e)}")
            return None


    @classmethod
    async def tokens_usage(cls, db: AsyncSession, session_id: UUID):
        result = await db.execute(
            select(
                func.sum(cls.prompt_tokens).label("prompt_tokens"),
                func.sum(cls.completion_tokens).label("completion_tokens"),
                func.sum(cls.total_tokens).label("total_tokens")
            ).filter(cls.session_id == session_id)
        )
        row = result.first()
        tokens_usage_dict = {
            'prompt_tokens': row.prompt_tokens or 0,
            'completion_tokens': row.completion_tokens or 0,
            'total_tokens': row.total_tokens or 0
        }
        return tokens_usage_dict
