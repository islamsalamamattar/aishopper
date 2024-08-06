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

        if interaction.displayed_products:
            products = {
                "type": "products",
                "id": uuid.uuid4(),
                "interaction_id": interaction.id,
                "role": "tool",
                "createdAt": createdAt,
                "products": interaction.displayed_products,
            }
            messages.append(products)

        if interaction.displayed_images:
            product_images = {
                "type": "images",
                "id": uuid.uuid4(),
                "interaction_id": interaction.id,
                "role": "tool",
                "createdAt": createdAt,
                "images": interaction.displayed_images,
            }
            messages.append(product_images)

        # Splitting the response by the first occurrence of "\n\n"
        splitted_responses = interaction.response.split("\n\n", 1)
        for splitted_response in splitted_responses:
            response = {
                "type": "text",
                "id": uuid.uuid4(),
                "interaction_id": interaction.id,
                "role": "assistant",
                "createdAt": createdAt,
                "text": splitted_response.strip(),
            }
            messages.append(response)

    return {'messages': messages}


async def formatAppReply(response: dict):
    messages = []
    if response['products']:
        products = {
                    "type": "products",
                    "id": uuid.uuid4(),
                    "interaction_id": response['interactionId'],
                    "role": "tool",
                    "createdAt": int(datetime.now().timestamp() * 1000),
                    "products": response['products'],
                }
        messages.append(products)

    if response['images']:
        product_images = {
                    "type": "images",
                    "id": uuid.uuid4(),
                    "interaction_id": response['interactionId'],
                    "role": "tool",
                    "createdAt": int(datetime.now().timestamp() * 1000),
                    "images": response['images'],
                }
        messages.append(product_images)

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


async def formatAppProfile(
    db: AsyncSession,
    user: User,
):
    userProfile = {
        "firstName": user.first_name,
        "lastName": user.last_name,
        "phone": user.phone,
        "email": user.email,
        "userId": user.id
    }

    profile = await Profile.find_by_user_id(db=db, user_id=user.id)
    
    if profile:
        userProfile["onboarded"] = True

        userProfile["profile"] = f"""- Profile:    {profile.firstName}"""
    else:
        userProfile["onboarded"] = False
        userProfile["profile"] = "Profile not setup"

    return userProfile