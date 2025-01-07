from fastapi import APIRouter
from typing import Any
from datetime import datetime
import uuid

from app.models import Interaction, Chatsession
from app.core.database import DBSessionDep
from app.core.exceptions import NotFoundException
from app.utils.appUtils import formatAppHistory, formatAppReply
from app.utils.authUtils import authenticateToken
from app.agents.chatAgent.chains_copy import newMesssageChain, nextNoonSearch, nextTopPicks
from app.agents.chatAgent.search_agent import MessageChain
from app.agents.chatAgent.tools import available_tools
from app.schemas.chat_requests import ChatRequest
from app.schemas.chat_session import NewSessionRequest
from app.utils.scrapers.scrapingfish import noon_search

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)


@router.get("/get_sessions", response_model=Any)
async def get_sessions(
    token: str,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    chat_sessions = await Chatsession.find_by_user_id(db=db, user_id=user_id)

    chat_sessions_json = []
    for session in chat_sessions:
        chat_session = {
            "session_id": session.id,
            "session_title": session.title
        }
        chat_sessions_json.append(chat_session)

    return {'chat_sessions': chat_sessions_json}

@router.post("/new_session", response_model=Any)
async def create_session(
    request: NewSessionRequest,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=request.token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    new_session = await Chatsession.create(db=db, user_id=user_id, title=request.title)
    return {'session_id': new_session.id}


@router.post("/new_message", response_model=Any)
async def chat_response(
    request: ChatRequest,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=request.token)
    if not user:
        raise NotFoundException(detail="User not found")

    interaction = await MessageChain(db, request.session_id, request.message)
    response_formatted = await formatAppReply(interaction)
    
    return {
        'messages': response_formatted,
        'next': True
    }    

@router.get("/next_message", response_model=dict)
async def chat_next(
    token: str,
    interaction_id: str,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id
    country = user.country
    
    interaction = await Interaction.find_by_id(db, interaction_id)
    if not interaction:
        raise NotFoundException(detail="Interaction not found")
    
    if interaction.next == 'noon_search':
        response_unformatted = await nextNoonSearch(
            db,
            country,
            interaction
        )
        response_formatted = await formatAppReply(response_unformatted)
    
        return {
            'messages': response_formatted,
            'next': response_unformatted['next']
        }
        
    if interaction.next == 'top_picks':
        response_unformatted = await nextTopPicks(
            db,
            country,
            interaction
        )
        response_formatted = await formatAppReply(response_unformatted)
    
        return {
            'messages': response_formatted,
            'next': response_unformatted['next']
        }
    else:
        return {'messages': None}


@router.get("/history", response_model=dict)
async def chat_history(
    token: str,
    session_id: str,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id
    first_name = user.first_name

    interactions = await Interaction.find_by_session_id(db=db, session_id=session_id)
    if interactions:
        history = await formatAppHistory(interactions=interactions)
        return history
    else:
        greetings = [
    {
        "id": user_id,
        "type": "text",
        "interacton_id": uuid.uuid4(),
        "createdAt": int(datetime.now().timestamp() * 1000),
        "text": f"Hi **{first_name}**, What would you like to shop for today?",
        "role": "assistant"
    }]
        return {'messages': greetings}
