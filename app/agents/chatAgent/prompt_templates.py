from sqlalchemy import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Interaction, User
from .prompts import instructionsPrompt_old

async def chatSystemPromptTemplate(
   userId: UUID,
   db: AsyncSession,
   instructionsPrompt= instructionsPrompt_old,
   num_interactions= 5
):
    user = await User.find_by_id(db=db, id=userId)
    userFirstName = user.first_name
    userProfile = f"User First Name: {userProfile}\n\n"
    profile = f"### USER PROFILE: {userProfile}"
    interactions = await Interaction.find_last_n_by_user_id(db=db, user_id=userId, n=num_interactions)
    history = ""
    if interactions:
        history = "### Chat History:"
        for interaction in interactions:
            response_parts = interaction.response.split("**")
            truncated_responses = [part for part in response_parts if part.strip()]
            truncated_response = '**'.join(truncated_responses[:4])
            history += f'''
[ {interaction.timestamp} ]
[{userFirstName}]: {interaction.prompt}
[assistant]: {truncated_response}
...
'''

    systemPrompt = f'''{instructionsPrompt}


{history}
'''

    return systemPrompt
