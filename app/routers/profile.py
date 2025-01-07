# app/routers/profile.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, List

from app.models import Interaction, Chatsession, Profile
from app.schemas.profile import ProfileCreate, ProfileBase, ProfileUpdate
from app.core.database import DBSessionDep
from app.core.exceptions import NotFoundException

from app.utils.authUtils import authenticateToken


router = APIRouter(
    prefix="/account",
    tags=["profile"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=dict)
async def get_profile(token: str, db: DBSessionDep):
    
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    response = {
        "phone": user.phone,
        "name": f"{user.first_name}  {user.last_name}",
        "email": user.email,
        "gender": user.gender,
        "age_group": user.age_group
    }

    # Check if profile exists
    user_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    if user_profile.fav_categories:
        categories = ""
        for category in user_profile.fav_categories:
            if categories == "":
                categories += f"{category}"
            else:
                categories += f"\n{category}"
        response["fav_categories"]= categories
    else:
        response["fav_categories"]= "Not defined"

    return response

@router.get("/onboarded", response_model=Any)
async def is_onboarded(
    token: str,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id
    profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    onboarded = profile.is_onboarded
    return {'is_onboarded': onboarded}


@router.post("/onboard", response_model=Any)
async def onboard(
    token: str,
    fav_categories: List[str],
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id
    profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    await profile.update_fav_categories(db, user_id, fav_categories)
    profile = await profile.onboard(db, user_id)
    return {'fav_categories': fav_categories}


@router.post("/upsert", response_model=Any)
async def upsert_profile(
    profile_data: ProfileCreate,  # Use ProfileCreate for incoming data
    token: str,
    db: DBSessionDep
):
    # Log the incoming data
    print("Received profile_data:", profile_data.dict())
    
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    # Check if profile exists
    existing_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    if existing_profile:
        # Convert incoming data to ProfileUpdate for partial update
        profile_update_data = ProfileUpdate(**profile_data.dict())
        
        # Update existing profile
        updated_profile = await Profile.update(
            db=db,
            user_id=user_id,
            **profile_update_data.dict(exclude_unset=True)
        )
        response = {
            "gender": updated_profile.gender,
            "age_group": updated_profile.age_group,
            "Favorite Categories": updated_profile.fav_categories,

        }
        return response
    else:
        # Create new profile
        new_profile = await Profile.create(
            db=db,
            user_id=user_id,
            **profile_data.dict()
        )
        response = {
            "gender": new_profile.gender,
            "age_group": new_profile.age_group,
            "Favorite Categories": new_profile.fav_categories,

        }
        return response

@router.get("/usage", response_model=Any)
async def get_usage(
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
