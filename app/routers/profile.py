# app/routers/profile.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Any

from app.models import Profile, Interaction, Chatsession
from app.schemas.profile import ProfileCreate, ProfileBase, ProfileUpdate
from app.core.database import DBSessionDep
from app.core.exceptions import NotFoundException

from app.utils.appUtils import formatAppProfile
from app.utils.authUtils import authenticateToken


router = APIRouter(
    prefix="/api/aishopper/account",
    tags=["profile"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=dict)
async def get_profile(token: str, db: DBSessionDep):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")

    profile = await formatAppProfile(db=db, user=user)
    return profile


@router.post("/upsert", response_model=ProfileCreate)
async def upsert_profile(
    profile_data: ProfileBase,
    token: str,
    db: DBSessionDep
):
    # Log the incoming data
    print("Received profile_data:", profile_data.dict())
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    userId = user.id

    # Check if profile exists
    existing_profile = await Profile.find_by_user_id(db=db, user_id=userId)
    if existing_profile:
        # Update profile
        updated_profile = await Profile.update(
            db=db,
            user_id=userId,
            category=profile_data.category,
            relation=profile_data.relation,
            age=profile_data.age,
            weight=profile_data.weight,
            height=profile_data.height ,
            chest_shape=profile_data.chest_shape,
            abdomen_shape=profile_data.abdomen_shape,
            hip_shape=profile_data.hip_shape,
            fitting=profile_data.fitting,
            bra_sizing=profile_data.bra_sizing,
            bra_underband=profile_data.bra_underband,
            bra_cup=profile_data.bra_cup
        )
        return updated_profile
    else:
        # Create new profile
        new_profile = await Profile.create(
            db=db,
            user_id=userId,
            category=profile_data.category,
            relation=profile_data.relation,
            age=profile_data.age,
            weight=profile_data.weight,
            height=profile_data.height ,
            chest_shape=profile_data.chest_shape,
            abdomen_shape=profile_data.abdomen_shape,
            hip_shape=profile_data.hip_shape,
            fitting=profile_data.fitting,
            bra_sizing=profile_data.bra_sizing,
            bra_underband=profile_data.bra_underband,
            bra_cup=profile_data.bra_cup
        )
        return new_profile


@router.get("/usage", response_model=Any)
async def chat_history(
    token: str,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id
    chat_sessions = await Chatsession.find_by_user_id(db=db, user_id=user_id)
    _prompt_tokens = 0
    _completion_tokens = 0
    for session in chat_sessions:
        # Save token usage
        tokens_usage = await Interaction.tokens_usage(db=db, session_id=session.id)
        _prompt_tokens += tokens_usage['prompt_tokens']
        _completion_tokens += tokens_usage['completion_tokens']

    _total_tokens = _prompt_tokens + _completion_tokens
    usage = {
        'prompt_tokens': _prompt_tokens,
        'completion_tokens': _completion_tokens,
        'total_tokens': _total_tokens
    }
    return usage
