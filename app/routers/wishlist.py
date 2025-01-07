# app/routers/wishlist.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, List

from app.models import Profile
from app.core.database import DBSessionDep
from app.core.exceptions import NotFoundException

from app.utils.authUtils import authenticateToken


router = APIRouter(
    prefix="/wishlist",
    tags=["Wishlist"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=dict)
async def get_wishlist(token: str, db: DBSessionDep):
    
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    wishlist = []
    # Check if profile exists
    user_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    if user_profile:
        wishlist = user_profile.wishlist
    return {'wishlist': wishlist}

@router.post("/add", response_model=dict)
async def add_to_wishlist(
    token: str,
    new_products: List[dict],
    db: DBSessionDep
):
    
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    wishlist = []
    # Check if profile exists
    user_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    if user_profile.wishlist:
        existing_product_ids = {product['asin'] for product in user_profile.wishlist}
        for new_product in new_products:
            if new_product['asin'] not in existing_product_ids:
                wishlist = await Profile.add_to_wishlist(db=db, user_id=user_id, new_product=new_product)
    else:
        for new_product in new_products:
            wishlist = await Profile.add_to_wishlist(db=db, user_id=user_id, new_product=new_product)
            
    return {'wishlist': wishlist}

@router.post("/remove", response_model=dict)
async def remove_from_wishlist(
    token: str,
    old_products: List[dict],
    db: DBSessionDep
):
    
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id
    wishlist = []
    # Check if profile exists
    user_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    if user_profile:
        for product in old_products:
            wishlist = await Profile.remove_from_wishlist(db=db, user_id=user_id, old_product=product)
        
    return {'wishlist': wishlist}

@router.post("/move_to_cart", response_model=dict)
async def move_to_cart(
    token: str,
    products: List[dict],
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    wishlist = []
    cart = []
    user_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    
    if user_profile:
        for product in products:
            asin = product['asin']
            
            # Remove from wishlist
            if any(p['asin'] == asin for p in user_profile.wishlist):
                wishlist = await Profile.remove_from_wishlist(db=db, user_id=user_id, old_product=product)

            # Add to cart if not already present
            if not any(p['asin'] == asin for p in user_profile.cart):
                cart = await Profile.add_to_cart(db=db, user_id=user_id, new_product=product)

    return {'wishlist': wishlist, 'cart': cart}
