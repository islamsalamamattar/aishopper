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
from app.logs.logger import logger

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
    """
    Fetches all chat sessions for the authenticated user.

    Args:
        token: The JWT token for user authentication.
        db: DBSessionDep for database operations.

    Returns:
        A list of chat sessions associated with the user.
    """
    try:
        logger.info("Received request to fetch chat sessions.")

        # JWT Authentication
        logger.debug("Authenticating user token.")
        user = await authenticateToken(db=db, token=token)
        if not user:
            logger.warning(f"Authentication failed for token: {token}")
            raise NotFoundException(detail="User not found")
        
        user_id = user.id
        logger.info(f"User authenticated successfully: user_id={user_id}")

        # Fetch chat sessions
        logger.info(f"Fetching chat sessions for user_id: {user_id}")
        chat_sessions = await Chatsession.find_by_user_id(db=db, user_id=user_id)

        # Format the chat sessions into JSON
        logger.debug(f"Found {len(chat_sessions)} chat sessions for user_id: {user_id}")
        chat_sessions_json = [
            {"session_id": session.id, "session_title": session.title}
            for session in chat_sessions
        ]

        logger.info(f"Successfully fetched and formatted chat sessions for user_id: {user_id}")
        return {'chat_sessions': chat_sessions_json}

    except NotFoundException as e:
        logger.error(f"NotFoundException encountered: {e.detail}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_sessions: {e}", exc_info=True)
        raise


@router.post("/new_session", response_model=Any)
async def create_session(
    request: NewSessionRequest,
    db: DBSessionDep
):
    """
    Creates a new chat session for the authenticated user.

    Args:
        request: Contains the user's JWT token and the title for the new session.
        db: DBSessionDep for database operations.

    Returns:
        The ID of the newly created session.
    """
    try:
        logger.info("Received request to create a new chat session.")

        # JWT Authentication
        logger.debug("Authenticating user token.")
        user = await authenticateToken(db=db, token=request.token)
        if not user:
            logger.warning(f"Authentication failed for token: {request.token}")
            raise NotFoundException(detail="User not found")
        
        user_id = user.id
        logger.info(f"User authenticated successfully: user_id={user_id}")

        # Create a new chat session
        logger.info(f"Creating a new chat session for user_id: {user_id} with title: {request.title}")
        new_session = await Chatsession.create(db=db, user_id=user_id, title=request.title)

        logger.info(f"Successfully created new chat session with session_id: {new_session.id}")
        return {'session_id': new_session.id}

    except NotFoundException as e:
        logger.error(f"NotFoundException encountered: {e.detail}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_session: {e}", exc_info=True)
        raise


@router.post("/new_message", response_model=Any)
async def chat_response(
    request: ChatRequest,
    db: DBSessionDep
):
    """
    Handles the chat response flow including JWT authentication, message processing, 
    and formatting the app reply.

    Args:
        request: ChatRequest containing session_id, token, and user message.
        db: DBSessionDep for database operations.

    Returns:
        A dictionary with the formatted messages and a flag indicating further interaction.
    """
    try:
        logger.info(f"Received chat request for session_id: {request.session_id}")
        
        # JWT Authentication
        logger.debug("Authenticating user token.")
        user = await authenticateToken(db=db, token=request.token)
        if not user:
            logger.warning(f"Authentication failed for token: {request.token}")
            raise NotFoundException(detail="User not found")
        
        logger.info(f"User authenticated successfully: {user.id}")
        
        # Process the message with MessageChain
        logger.info(f"Processing message for session_id: {request.session_id}")
        interaction = await MessageChain(db, request.session_id, request.message)
        logger.debug(f"MessageChain interaction result: {interaction}")
        
        # Format the app reply
        logger.info(f"Formatting app reply for session_id: {request.session_id}")
        response_formatted = await formatAppReply(interaction)
        logger.debug(f"Formatted response: {response_formatted}")
        
        # Return the response
        logger.info(f"Returning response for session_id: {request.session_id}")
        logger.info(f"Response:\n{response_formatted}")
        return {
            'messages': response_formatted,
            'next': True
        }

    except NotFoundException as e:
        logger.error(f"NotFoundException encountered: {e.detail}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat_response: {e}", exc_info=True)
        raise  

@router.get("/next_message", response_model=dict)
async def chat_next(
    token: str,
    interaction_id: str,
    db: DBSessionDep
):
    """
    Handles the 'next' interaction flow for a chat session.

    Args:
        token: The JWT token for user authentication.
        interaction_id: The ID of the interaction to process the next step.
        db: DBSessionDep for database operations.

    Returns:
        A dictionary with the formatted messages and the next interaction state.
    """
    try:
        logger.info(f"Received chat_next request for interaction_id: {interaction_id}")

        # JWT Authentication
        logger.debug("Authenticating user token.")
        user = await authenticateToken(db=db, token=token)
        if not user:
            logger.warning(f"Authentication failed for token: {token}")
            raise NotFoundException(detail="User not found")
        
        user_id = user.id
        country = user.country
        logger.info(f"User authenticated successfully: user_id={user_id}, country={country}")

        # Fetch the interaction
        logger.info(f"Fetching interaction with ID: {interaction_id}")
        interaction = await Interaction.find_by_id(db, interaction_id)
        if not interaction:
            logger.warning(f"No interaction found with ID: {interaction_id}")
            raise NotFoundException(detail="Interaction not found")
        
        # Process 'noon_search' interaction
        if interaction.next == 'noon_search':
            logger.info(f"Processing 'noon_search' for interaction_id: {interaction_id}")
            response_unformatted = await nextNoonSearch(db, country, interaction)
            logger.debug(f"Unformatted response from 'noon_search': {response_unformatted}")

            response_formatted = await formatAppReply(response_unformatted)
            logger.debug(f"Formatted response: {response_formatted}")

            return {
                'messages': response_formatted,
                'next': response_unformatted['next']
            }

        # Process 'top_picks' interaction
        elif interaction.next == 'top_picks':
            logger.info(f"Processing 'top_picks' for interaction_id: {interaction_id}")
            response_unformatted = await nextTopPicks(db, country, interaction)
            logger.debug(f"Unformatted response from 'top_picks': {response_unformatted}")

            response_formatted = await formatAppReply(response_unformatted)
            logger.debug(f"Formatted response: {response_formatted}")

            return {
                'messages': response_formatted,
                'next': response_unformatted['next']
            }

        # Handle unknown or unsupported interaction types
        else:
            logger.warning(f"Unknown interaction type: {interaction.next} for interaction_id: {interaction_id}")
            return {'messages': None}

    except NotFoundException as e:
        logger.error(f"NotFoundException encountered: {e.detail}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat_next: {e}", exc_info=True)
        raise

@router.get("/history", response_model=dict)
async def chat_history(
    token: str,
    session_id: str,
    db: DBSessionDep
):
    """
    Fetches the chat history for a given session.

    Args:
        token: The JWT token for user authentication.
        session_id: The ID of the chat session.
        db: DBSessionDep for database operations.

    Returns:
        A dictionary containing the chat history or a greeting message if no history is found.
    """
    try:
        logger.info(f"Received chat_history request for session_id: {session_id}")

        # JWT Authentication
        logger.debug("Authenticating user token.")
        user = await authenticateToken(db=db, token=token)
        if not user:
            logger.warning(f"Authentication failed for token: {token}")
            raise NotFoundException(detail="User not found")
        
        user_id = user.id
        first_name = user.first_name
        logger.info(f"User authenticated successfully: user_id={user_id}, first_name={first_name}")

        # Fetch interactions for the session
        logger.info(f"Fetching interactions for session_id: {session_id}")
        interactions = await Interaction.find_by_session_id(db=db, session_id=session_id)

        # If interactions exist, format and return the history
        if interactions:
            logger.debug(f"Found {len(interactions)} interactions for session_id: {session_id}")
            history = await formatAppHistory(interactions=interactions)
            logger.info(f"Formatted chat history for session_id: {session_id}")
            return history
        
        # If no interactions are found, return a greeting message
        logger.info(f"No interactions found for session_id: {session_id}. Returning default greeting.")
        greetings = [
            {
                "id": user_id,
                "type": "text",
                "interaction_id": str(uuid.uuid4()),
                "createdAt": int(datetime.now().timestamp() * 1000),
                "text": f"Hi **{first_name}**, What would you like to shop for today?",
                "role": "assistant"
            }
        ]
        return {'messages': greetings}

    except NotFoundException as e:
        logger.error(f"NotFoundException encountered: {e.detail}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat_history: {e}", exc_info=True)
        raise