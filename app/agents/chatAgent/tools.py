from typing import List, Dict
from datetime import datetime
import uuid
import json
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import UUID

from app.llms.groqApi import create_chat_completions
from app.models import Interaction

async def llmApiCall(
        systemPrompt: str,
        message: str,
        model: str = "llama3-8b-8192", # "mixtral-8x7b-32768",
        stop: List[str] = ["<SYS>","<</SYS>>", "User:"],
        stream: bool = False,
        temperature: float = 0.7,
        top_p: float = 0.8,
        max_tokens: int = 2000,
):
    # Api call formatting and request
    messages = [
        {'role': "system", 'content': systemPrompt},
        {'role':"user", 'content':message}
    ]

    params = {
        'messages': messages,
        'model': model,
        'stop': stop,
        'stream': stream,
        'temperature': temperature,
        'top_p': top_p,
        'max_tokens': max_tokens,
    }

    response = await create_chat_completions(**params)

    return response

async def saveInteraction(
        db: AsyncSession,
        userId: UUID,
        message: str,
        response: dict,
        
):
    interaction = await Interaction.create(
        db=db,
        user_id=userId,
        prompt=message,
        response=response.choices[0].message.content,
        model='mixtral-8x7b-32768',
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        total_tokens=response.usage.total_tokens
    )

    return interaction

async def formatAppReply(
        response: dict,
        interactionId: str,
):
    reply = {
        "id": uuid.uuid4(),
        "interaction_id": interactionId,
        "createdAt": int(datetime.now().timestamp() * 1000),
        "text": response.choices[0].message.content,
        "type": "text",
        "author": {"id": uuid.uuid4()}
    }

    return reply

async def extractJson(reply: str, db: AsyncSession) -> Dict:
    try:
        # Use regular expression to find the JSON string within the reply
        json_match = re.search(r'{.*}', reply, re.DOTALL)
        if not json_match:
            raise ValueError("JSON string not found in the reply.")
        
        # Extract the JSON string
        json_str = json_match.group(0)

        # Parse the JSON string
        recipe_data = json.loads(json_str)

        return recipe_data

    except json.JSONDecodeError as json_error:
        logging.error(f"JSON decoding error: {json_error}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
