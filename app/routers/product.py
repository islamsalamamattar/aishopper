# app/routers/wishlist.py
from fastapi import APIRouter, Path
from typing import Any, List


from app.models import Product, Profile
from app.core.database import DBSessionDep
from app.core.exceptions import NotFoundException

from app.utils.authUtils import authenticateToken
from app.utils.scrapers.scrapingfish import amazon_products_details, noon_products_details


router = APIRouter(
    prefix="/product",
    tags=["Product"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{platform}/{country}/{asin}", response_model=dict)
async def get_product(
    token: str,
    db: DBSessionDep,
    platform: str = Path(..., description="The platform"),
    country: str = Path(..., description="The platform country"),
    asin: str = Path(..., description="The ASIN of the product")
    ):
    
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    
    if platform == "amazon":
        product = await amazon_products_details(db, asin, country)
    if platform == "noon":
        product = await noon_products_details(db, asin, country)
    return product
