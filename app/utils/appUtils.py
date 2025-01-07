import uuid
from datetime import datetime

from app.models import User, Interaction, Product
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict




async def formatAppHistory(interactions: List[Interaction]) -> Dict:
    createdAt = int(datetime.now().timestamp() * 1000)
    messages = []

    for interaction in interactions:
        prompt = {
            "type": "text",
            "id": uuid.uuid4(),
            "interaction_id": interaction.id,
            "role": "user",
            "createdAt": createdAt,
            "text": interaction.prompt,
        }
        messages.append(prompt)
        
        if interaction.amazon_products:
            products = {
                "type": "amazonProducts",
                "id": uuid.uuid4(),
                "interaction_id": interaction.id,
                "role": "assistant",
                "createdAt": createdAt,
                "products": interaction.amazon_products,
            }
            messages.append(products)

        if interaction.noon_products:
            products = {
                "type": "noonProducts",
                "id": uuid.uuid4(),
                "interaction_id": interaction.id,
                "role": "assistant",
                "createdAt": createdAt,
                "products": interaction.noon_products,
            }
            messages.append(products)
            
        if interaction.response:
            response = {
                "type": "text",
                "id": uuid.uuid4(),
                "interaction_id": interaction.id,
                "role": "assistant",
                "createdAt": createdAt,
                "text": interaction.response.strip(),
            }
            messages.append(response)
            
    return {'messages': messages}

async def formatAppReply(response: dict):
    messages = []

    if response['amazonProducts']:
        products = {
                    "type": "amazonProducts",
                    "id": uuid.uuid4(),
                    "interaction_id": response['interactionId'],
                    "role": "assistant",
                    "createdAt": int(datetime.now().timestamp() * 1000),
                    "products": response['amazonProducts'],
                }
        messages.append(products)

    if response['noonProducts']:
        products = {
                    "type": "noonProducts",
                    "id": uuid.uuid4(),
                    "interaction_id": response['interactionId'],
                    "role": "assistant",
                    "createdAt": int(datetime.now().timestamp() * 1000),
                    "products": response['noonProducts'],
                }
        messages.append(products)
    
    if response['message']:
        message = {
            "type": "text",
            "id": uuid.uuid4(),
            "interaction_id": response['interactionId'],
            "role": "assistant",
            "createdAt": int(datetime.now().timestamp() * 1000),
            "text": response['message']
        }
        messages.append(message)
        
    return messages

