from fastapi import APIRouter
from typing import Any
from datetime import datetime
import uuid

from app.models import Interaction
from app.core.database import DBSessionDep
from app.core.exceptions import NotFoundException
from app.utils.appUtils import formatAppHistory
from app.utils.authUtils import authenticateToken
from app.agents.chatAgent.chains import chatChain

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=Any)
async def chat_response(
    token: str,
    message: str,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    userId = user.id

    # Api call formatting, request, and reply formatting for app andpoint
    reply = await chatChain(
        db=db,
        userId=userId,
        message=message,
    )
    return reply


@router.get("/history", response_model=Any)
async def chat_history(
    token: str,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    userId = user.id
    firstName = user.first_name

    interactions = await Interaction.find_by_user_id(db=db, user_id=userId)
    if interactions:
        history = await formatAppHistory(interactions=interactions)
        return history
    else:
        greetings = [{
        "id": userId,
        "interacton_id": uuid.uuid4(),
        "createdAt": int(datetime.now().timestamp() * 1000),
        "text": f"Hi there **{firstName}**! Thanks for sharing a bit about your cooking preferences and goals. I'm excited to help you on your culinary journey!",
        "role": "assistant"
    },
    {
        "id": userId,
        "interacton_id": uuid.uuid4(),
        "createdAt": int(datetime.now().timestamp() * 1000),
        "text": "Whether you're looking for easy weeknight meals, want to impress guests with your skills, or have specific health goals in mind, I've got tons of recipes and tips for you.",
        "role": "assistant"  
    },
    {
        "id": userId,
        "interacton_id": uuid.uuid4(),
        "createdAt": int(datetime.now().timestamp() * 1000),
        "text": f"**{firstName}**, What would you like to start with today?",
        "role": "assistant"
    }]
        return {'messages': greetings}
