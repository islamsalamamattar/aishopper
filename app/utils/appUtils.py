import uuid
from datetime import datetime

from app.models import User, Interaction, Profile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict


async def formatAppHistory(interactions: List[Interaction]) -> Dict:
    createdAt = int(datetime.now().timestamp() * 1000)
    messages = []

    for interaction in interactions:
        prompt = {
            "id": uuid.uuid4(),
            "interaction_id": interaction.id,
            "role": "user",
            "createdAt": createdAt,
            "text": interaction.prompt,
        }
        messages.append(prompt)

        # Splitting the response by the first occurrence of "\n\n"
        splitted_responses = interaction.response.split("\n\n", 1)
        for splitted_response in splitted_responses:
            response = {
                "id": uuid.uuid4(),
                "interaction_id": interaction.id,
                "role": "assistant",
                "createdAt": createdAt,
                "text": splitted_response.strip(),  # Removing leading/trailing whitespaces
            }
            messages.append(response)

    return {'messages': messages}


async def formatAppReply(
        interactionId: str,
        response: dict,
):
    reply = {
        "id": uuid.uuid4(),
        "interaction_id": interactionId,
        "role": "assistant",
        "createdAt": int(datetime.now().timestamp() * 1000),
        "text": response.choices[0].message.content
    }

    return reply


async def formatAppProfile(
    db: AsyncSession,
    user: User,
):
    userProfile = {
        "firstName": user.firstName,
        "lastName": user.lastName,
        "imageUrl": user.imageUrl,
        "phone": user.phone,
        "email": user.email,
        "userId": user.id
    }

    profile = await Profile.find_by_user_id(db=db, user_id=user.id)
    
    if profile:
        userProfile["Onboarded"] = True

        userProfile["dietary_profile"] = f"""- Cooking for:    {profile.num_people_per_meal}"""
    else:
        userProfile["Onboarded"] = False
        userProfile["dietary_profile"] = "Cooking Profile not setup"

    return userProfile