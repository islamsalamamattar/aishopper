# app/routers/cart.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, List

from app.models import Profile
from app.core.database import DBSessionDep
from app.core.exceptions import NotFoundException

from app.utils.authUtils import authenticateToken


router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=dict)
async def get_cart(token: str, db: DBSessionDep):
    
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    cart = []
    # Check if profile exists
    user_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    if user_profile:
        cart = user_profile.cart
    return {'cart': cart}

@router.post("/add", response_model=dict)
async def add_to_cart(
    token: str,
    new_products: List[dict],
    db: DBSessionDep
):
    
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    cart = []
    # Check if profile exists
    user_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    if user_profile.cart:
        existing_product_ids = {product['asin'] for product in user_profile.cart}
        for new_product in new_products:
            if new_product['asin'] not in existing_product_ids:
                cart = await Profile.add_to_cart(db=db, user_id=user_id, new_product=new_product)
    else:
        for new_product in new_products:
            cart = await Profile.add_to_cart(db=db, user_id=user_id, new_product=new_product)
    return {'cart': cart}

@router.post("/remove", response_model=dict)
async def remove_from_cart(
    token: str,
    old_products: List[dict],
    db: DBSessionDep
):
    
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id
    cart = []
    # Check if profile exists
    user_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    if user_profile:
        for product in old_products:
            cart = await Profile.remove_from_cart(db=db, user_id=user_id, old_product=product)
        
    return {'cart': cart}

@router.post("/move_to_wishlist", response_model=dict)
async def move_to_wishlist(
    token: str,
    products: List[dict],
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    cart = []
    wishlist = []
    user_profile = await Profile.find_by_user_id(db=db, user_id=user_id)
    
    if user_profile:
        for product in products:
            asin = product['asin']
            
            # Remove from cart
            if any(p['asin'] == asin for p in user_profile.cart):
                cart = await Profile.remove_from_cart(db=db, user_id=user_id, old_product=product)

            # Add to wishlist if not already present
            if not any(p['asin'] == asin for p in user_profile.wishlist):
                wishlist = await Profile.add_to_wishlist(db=db, user_id=user_id, new_product=product)

    return {'cart': cart, 'wishlist': wishlist}
