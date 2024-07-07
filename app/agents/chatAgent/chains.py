import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from .tools import llmApiCall, saveInteraction, formatAppReply
from .prompt_templates import chatSystemPromptTemplate
from .prompts import extract_prompt
from app.models import Interaction

async def chatChain(
        db: AsyncSession,
        userId: str,
        message: str,
):
    
    systemPrompt = await chatSystemPromptTemplate(
        userId=userId,
        db=db,
    )
    # Api call formatting and request
    response = await llmApiCall(
        systemPrompt=systemPrompt,
        message=message,
    )
    Interaction = await saveInteraction(
        db=db,
        userId=userId,
        message=message,
        response=response
    )
    reply = await formatAppReply(
        interactionId=Interaction.id,
        response=response
    )

    return reply
